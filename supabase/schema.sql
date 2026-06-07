-- ============================================================
-- OptimityFX — Supabase Database Schema
-- Run this in: Supabase Dashboard > SQL Editor > New Query
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- PROFILES (extends auth.users)
-- ============================================================
CREATE TABLE IF NOT EXISTS profiles (
  id              UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email           TEXT,
  full_name       TEXT,
  avatar_url      TEXT,
  role            TEXT DEFAULT 'customer' CHECK (role IN ('customer','team','admin','super_admin')),
  wallet_credits  INTEGER DEFAULT 0,
  login_streak    INTEGER DEFAULT 0,
  last_login_date DATE,
  total_logins    INTEGER DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', '')
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- PRODUCTS (digital downloads)
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
  id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name           TEXT NOT NULL,
  slug           TEXT UNIQUE NOT NULL,
  description    TEXT,
  short_desc     TEXT,
  price          NUMERIC(10,2) NOT NULL,
  sale_price     NUMERIC(10,2),
  category       TEXT CHECK (category IN ('lut','preset','template','bundle','other')),
  thumbnail_url  TEXT,
  file_url       TEXT,
  is_active      BOOLEAN DEFAULT TRUE,
  download_count INTEGER DEFAULT 0,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- COURSES
-- ============================================================
CREATE TABLE IF NOT EXISTS courses (
  id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title          TEXT NOT NULL,
  slug           TEXT UNIQUE NOT NULL,
  description    TEXT,
  thumbnail_url  TEXT,
  price          NUMERIC(10,2) NOT NULL,
  sale_price     NUMERIC(10,2),
  is_live        BOOLEAN DEFAULT FALSE,
  live_url       TEXT,
  live_schedule  JSONB,
  instructor     TEXT,
  level          TEXT DEFAULT 'beginner' CHECK (level IN ('beginner','intermediate','advanced')),
  is_active      BOOLEAN DEFAULT TRUE,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS modules (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  course_id   UUID REFERENCES courses(id) ON DELETE CASCADE NOT NULL,
  title       TEXT NOT NULL,
  order_index INTEGER NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lessons (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  module_id    UUID REFERENCES modules(id) ON DELETE CASCADE NOT NULL,
  title        TEXT NOT NULL,
  video_url    TEXT,
  description  TEXT,
  duration_mins INTEGER,
  order_index  INTEGER NOT NULL,
  is_preview   BOOLEAN DEFAULT FALSE,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ORDERS & PURCHASES
-- ============================================================
CREATE TABLE IF NOT EXISTS coupons (
  id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  code           TEXT UNIQUE NOT NULL,
  discount_type  TEXT NOT NULL CHECK (discount_type IN ('percent','flat')),
  discount_value NUMERIC(10,2) NOT NULL,
  min_order      NUMERIC(10,2) DEFAULT 0,
  max_uses       INTEGER,
  used_count     INTEGER DEFAULT 0,
  expires_at     TIMESTAMPTZ,
  is_active      BOOLEAN DEFAULT TRUE,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
  id                    UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id               UUID REFERENCES auth.users(id),
  total                 NUMERIC(10,2) NOT NULL,
  discount              NUMERIC(10,2) DEFAULT 0,
  credits_used          INTEGER DEFAULT 0,
  coupon_id             UUID REFERENCES coupons(id),
  status                TEXT DEFAULT 'pending' CHECK (status IN ('pending','paid','failed','refunded')),
  razorpay_order_id     TEXT,
  razorpay_payment_id   TEXT,
  notes                 TEXT,
  created_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  order_id   UUID REFERENCES orders(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id),
  course_id  UUID REFERENCES courses(id),
  price      NUMERIC(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS purchases (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id      UUID REFERENCES auth.users(id),
  product_id   UUID REFERENCES products(id),
  order_id     UUID REFERENCES orders(id),
  purchased_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, product_id)
);

CREATE TABLE IF NOT EXISTS coupon_usage (
  id        UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  coupon_id UUID REFERENCES coupons(id),
  user_id   UUID REFERENCES auth.users(id),
  order_id  UUID REFERENCES orders(id),
  used_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ENROLLMENTS & LESSON PROGRESS
-- ============================================================
CREATE TABLE IF NOT EXISTS enrollments (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id      UUID REFERENCES auth.users(id),
  course_id    UUID REFERENCES courses(id),
  order_id     UUID REFERENCES orders(id),
  enrolled_at  TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  UNIQUE(user_id, course_id)
);

CREATE TABLE IF NOT EXISTS lesson_progress (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id      UUID REFERENCES auth.users(id),
  lesson_id    UUID REFERENCES lessons(id),
  completed_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, lesson_id)
);

-- ============================================================
-- QUIZZES & CERTIFICATES
-- ============================================================
CREATE TABLE IF NOT EXISTS quizzes (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  course_id  UUID REFERENCES courses(id) ON DELETE CASCADE,
  module_id  UUID REFERENCES modules(id),
  title      TEXT NOT NULL,
  pass_score INTEGER DEFAULT 70,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS questions (
  id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  quiz_id        UUID REFERENCES quizzes(id) ON DELETE CASCADE,
  question_text  TEXT NOT NULL,
  image_url      TEXT,
  options        JSONB NOT NULL,
  correct_option TEXT NOT NULL,
  order_index    INTEGER,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
  id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id         UUID REFERENCES auth.users(id),
  quiz_id         UUID REFERENCES quizzes(id),
  score           INTEGER NOT NULL,
  total_questions INTEGER,
  correct_answers INTEGER,
  passed          BOOLEAN NOT NULL,
  answers         JSONB,
  completed_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS certificates (
  id                 UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id            UUID REFERENCES auth.users(id),
  course_id          UUID REFERENCES courses(id),
  quiz_attempt_id    UUID REFERENCES quiz_attempts(id),
  certificate_number TEXT UNIQUE DEFAULT 'OFX-' || UPPER(SUBSTR(gen_random_uuid()::TEXT, 1, 8)),
  issued_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- WALLET & DAILY REWARDS
-- ============================================================
CREATE TABLE IF NOT EXISTS login_rewards (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       UUID REFERENCES auth.users(id),
  date          DATE NOT NULL,
  credits_earned INTEGER NOT NULL,
  streak_day    INTEGER NOT NULL,
  UNIQUE(user_id, date)
);

CREATE TABLE IF NOT EXISTS wallet_transactions (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     UUID REFERENCES auth.users(id),
  type        TEXT NOT NULL CHECK (type IN ('earned','spent')),
  amount      INTEGER NOT NULL,
  description TEXT,
  ref_id      UUID,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TEAM PORTAL
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
  id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title           TEXT NOT NULL,
  description     TEXT,
  client_name     TEXT,
  client_email    TEXT,
  client_phone    TEXT,
  client_company  TEXT,
  status          TEXT DEFAULT 'pending' CHECK (status IN ('pending','active','completed','on_hold')),
  priority        TEXT DEFAULT 'medium'  CHECK (priority IN ('low','medium','high','urgent')),
  deadline        DATE,
  budget          NUMERIC(10,2),
  created_by      UUID REFERENCES auth.users(id),
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS project_members (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  user_id    UUID REFERENCES auth.users(id),
  role       TEXT DEFAULT 'member' CHECK (role IN ('lead','member')),
  joined_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(project_id, user_id)
);

CREATE TABLE IF NOT EXISTS tasks (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id  UUID REFERENCES projects(id) ON DELETE CASCADE,
  assigned_to UUID REFERENCES auth.users(id),
  title       TEXT NOT NULL,
  description TEXT,
  status      TEXT DEFAULT 'todo' CHECK (status IN ('todo','in_progress','review','done')),
  priority    TEXT DEFAULT 'medium' CHECK (priority IN ('low','medium','high','urgent')),
  due_date    DATE,
  created_by  UUID REFERENCES auth.users(id),
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS time_logs (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id      UUID REFERENCES auth.users(id),
  project_id   UUID REFERENCES projects(id),
  task_id      UUID REFERENCES tasks(id),
  start_time   TIMESTAMPTZ,
  end_time     TIMESTAMPTZ,
  duration_mins INTEGER,
  notes        TEXT,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS screenshots (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id      UUID REFERENCES auth.users(id),
  project_id   UUID REFERENCES projects(id),
  time_log_id  UUID REFERENCES time_logs(id),
  storage_path TEXT NOT NULL,
  file_size    INTEGER,
  notes        TEXT,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE profiles          ENABLE ROW LEVEL SECURITY;
ALTER TABLE products          ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses           ENABLE ROW LEVEL SECURITY;
ALTER TABLE modules           ENABLE ROW LEVEL SECURITY;
ALTER TABLE lessons           ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders            ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items       ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases         ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrollments       ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_progress   ENABLE ROW LEVEL SECURITY;
ALTER TABLE quizzes           ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions         ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts     ENABLE ROW LEVEL SECURITY;
ALTER TABLE certificates      ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_rewards     ENABLE ROW LEVEL SECURITY;
ALTER TABLE wallet_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE coupons           ENABLE ROW LEVEL SECURITY;
ALTER TABLE coupon_usage      ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects          ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_members   ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks             ENABLE ROW LEVEL SECURITY;
ALTER TABLE time_logs         ENABLE ROW LEVEL SECURITY;
ALTER TABLE screenshots       ENABLE ROW LEVEL SECURITY;

-- Profiles: own row
CREATE POLICY "Users can view own profile"   ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- Admins can see all profiles
CREATE POLICY "Admins view all profiles" ON profiles FOR SELECT
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin','super_admin')));

-- Products & courses: public read, admin write
CREATE POLICY "Anyone can view active products" ON products FOR SELECT USING (is_active = true);
CREATE POLICY "Admins manage products"          ON products FOR ALL
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin','super_admin')));

CREATE POLICY "Anyone can view active courses" ON courses FOR SELECT USING (is_active = true);
CREATE POLICY "Admins manage courses"          ON courses FOR ALL
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin','super_admin')));

CREATE POLICY "Anyone can view modules"  ON modules  FOR SELECT USING (true);
CREATE POLICY "Anyone can view lessons"  ON lessons  FOR SELECT USING (true);
CREATE POLICY "Admins manage modules"    ON modules  FOR ALL
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin','super_admin')));
CREATE POLICY "Admins manage lessons"    ON lessons  FOR ALL
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin','super_admin')));

-- Orders: own orders
CREATE POLICY "Users view own orders"    ON orders      FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own orders"  ON orders      FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users view own items"     ON order_items FOR SELECT
  USING (EXISTS (SELECT 1 FROM orders WHERE id = order_items.order_id AND user_id = auth.uid()));
CREATE POLICY "Users insert own items"   ON order_items FOR INSERT WITH CHECK (
  EXISTS (SELECT 1 FROM orders WHERE id = order_items.order_id AND user_id = auth.uid()));

-- Purchases
CREATE POLICY "Users view own purchases"   ON purchases FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own purchases" ON purchases FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Enrollments
CREATE POLICY "Users view own enrollments"   ON enrollments FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own enrollments" ON enrollments FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Lesson progress
CREATE POLICY "Users manage own progress" ON lesson_progress FOR ALL USING (auth.uid() = user_id);

-- Quizzes & questions: enrolled users can read
CREATE POLICY "Anyone can view quizzes"   ON quizzes   FOR SELECT USING (true);
CREATE POLICY "Anyone can view questions" ON questions FOR SELECT USING (true);

-- Quiz attempts
CREATE POLICY "Users manage own attempts"    ON quiz_attempts  FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users view own certificates"  ON certificates   FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own certificates"ON certificates   FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Rewards & wallet
CREATE POLICY "Users manage own rewards"      ON login_rewards       FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users manage own transactions" ON wallet_transactions  FOR ALL USING (auth.uid() = user_id);

-- Coupons: any logged-in user can read active coupons (to validate)
CREATE POLICY "Logged-in users can read coupons" ON coupons FOR SELECT
  USING (auth.uid() IS NOT NULL AND is_active = true);
CREATE POLICY "Admins manage coupons" ON coupons FOR ALL
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin','super_admin')));
CREATE POLICY "Users insert coupon usage" ON coupon_usage FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Admins update coupon usage" ON coupons FOR UPDATE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin','super_admin')));
-- Allow logged-in users to increment used_count (for coupon application)
CREATE POLICY "Users can update coupon count" ON coupons FOR UPDATE USING (auth.uid() IS NOT NULL);

-- Team portal: team + admin roles only
CREATE POLICY "Team can view projects" ON projects FOR SELECT
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('team','admin','super_admin')));
CREATE POLICY "Team can manage projects" ON projects FOR ALL
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('team','admin','super_admin')));

CREATE POLICY "Team can view members"  ON project_members FOR SELECT
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('team','admin','super_admin')));
CREATE POLICY "Admins manage members"  ON project_members FOR ALL
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin','super_admin')));

CREATE POLICY "Team can view tasks"    ON tasks FOR SELECT
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('team','admin','super_admin')));
CREATE POLICY "Team can manage tasks"  ON tasks FOR ALL
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('team','admin','super_admin')));

CREATE POLICY "Team can manage time"   ON time_logs FOR ALL
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('team','admin','super_admin')));

CREATE POLICY "Team can view screenshots"   ON screenshots FOR SELECT
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('team','admin','super_admin')));
CREATE POLICY "Team can upload screenshots" ON screenshots FOR INSERT
  WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Admins can delete screenshots" ON screenshots FOR DELETE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin','super_admin')));

-- ============================================================
-- SAMPLE DATA (optional — remove in production)
-- ============================================================

-- Sample coupon
INSERT INTO coupons (code, discount_type, discount_value, min_order, max_uses, is_active)
VALUES ('LAUNCH25', 'percent', 25, 0, 100, true)
ON CONFLICT (code) DO NOTHING;

-- Set a user as super_admin (replace with your actual user UUID after registering)
-- UPDATE profiles SET role = 'super_admin' WHERE email = 'optimityfx.studio@gmail.com';

-- ============================================================
-- STORAGE BUCKET (run separately in Supabase Dashboard > Storage)
-- ============================================================
-- 1. Go to Storage > New Bucket
-- 2. Name: screenshots
-- 3. Make it PUBLIC (so images can be viewed via URL)
-- 4. Max file size: 5MB
-- 5. Allowed MIME types: image/png, image/jpeg, image/webp

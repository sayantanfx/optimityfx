-- ============================================================
-- OptimityFX — Editor screening applications (the /opening form)
-- Run ONCE in: Supabase Dashboard > SQL Editor > New Query > Run
-- Then view/screen candidates in: Table Editor > applications
-- (sort by visible_chance to rank them).
-- ============================================================

CREATE TABLE IF NOT EXISTS public.applications (
  id                       UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at               TIMESTAMPTZ DEFAULT NOW(),
  visible_chance           TEXT,   -- candidate-facing hiring %
  name                     TEXT,
  sex                      TEXT,
  age                      TEXT,
  phone                    TEXT,
  email                    TEXT,
  experience_yrs           TEXT,
  expected_salary_bracket  TEXT,
  internet                 TEXT,
  youtube                  TEXT,
  self_rating_avg          TEXT,
  confidence_flag          TEXT,
  skill_check              TEXT,   -- REAL blind MCQ score (recruiter only)
  portfolio                TEXT,
  test_edit                TEXT,
  why                      TEXT,
  requirement              TEXT,
  start_when               TEXT,
  video_sw                 JSONB,
  photo_sw                 JSONB,
  design                   JSONB,
  style                    JSONB,
  tech                     JSONB,
  sound                    JSONB,
  ai_image                 JSONB,
  ai_video                 JSONB,
  self_rating              JSONB,
  skill_check_detail       JSONB,
  raw                      JSONB    -- full submission, just in case
);

-- Lock it down: the public form may INSERT, but the public/anon API key
-- can NEVER read rows back (candidates can't see each other's data).
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anyone can apply" ON public.applications;
CREATE POLICY "anyone can apply" ON public.applications
  FOR INSERT TO anon, authenticated WITH CHECK (true);

-- No SELECT policy on purpose → no reads via the API key.
-- You read/sort/export in the Supabase Table Editor (service role, bypasses RLS).
-- If you later want admins to read it inside the site, add:
--   CREATE POLICY "admins read applications" ON public.applications
--     FOR SELECT USING (user_role(auth.uid()) IN ('admin','super_admin'));

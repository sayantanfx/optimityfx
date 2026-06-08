/* ============================================================
   POST /api/admin/create-user
   Lets an authenticated admin/super_admin create a team account
   (username + password, no email verification). Runs server-side
   only — uses the Supabase service-role key, which must never be
   exposed to the browser.
   Body: { username, password, fullName, role }
   ============================================================ */
const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL    = process.env.SUPABASE_URL;
const SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const ANON_KEY        = process.env.SUPABASE_ANON_KEY;

const USERNAME_DOMAIN = 'team.optimityfx.local';
const ALLOWED_ROLES   = ['team', 'admin', 'super_admin'];

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }
  if (!SUPABASE_URL || !SERVICE_ROLE_KEY || !ANON_KEY) {
    res.status(500).json({ error: 'Server missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY / SUPABASE_ANON_KEY env vars.' });
    return;
  }

  const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  if (!token) {
    res.status(401).json({ error: 'Missing auth token.' });
    return;
  }

  // Verify the caller's identity and role using their own session token.
  const anon = createClient(SUPABASE_URL, ANON_KEY);
  const { data: { user }, error: userErr } = await anon.auth.getUser(token);
  if (userErr || !user) {
    res.status(401).json({ error: 'Invalid session.' });
    return;
  }

  const { data: callerProfile } = await anon
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .maybeSingle();

  if (!callerProfile || !['admin', 'super_admin'].includes(callerProfile.role)) {
    res.status(403).json({ error: 'Admin access required.' });
    return;
  }

  const { username, password, fullName, role } = req.body || {};
  if (!username || !password || !ALLOWED_ROLES.includes(role)) {
    res.status(400).json({ error: 'username, password, and a valid role (team/admin/super_admin) are required.' });
    return;
  }
  if (role === 'super_admin' && callerProfile.role !== 'super_admin') {
    res.status(403).json({ error: 'Only a super admin can create another super admin.' });
    return;
  }
  if (String(password).length < 6) {
    res.status(400).json({ error: 'Password must be at least 6 characters.' });
    return;
  }

  const cleanUsername = String(username).trim().toLowerCase().replace(/[^a-z0-9._-]/g, '');
  if (cleanUsername.length < 3) {
    res.status(400).json({ error: 'Username must be at least 3 characters (letters, numbers, . _ - only).' });
    return;
  }
  const syntheticEmail = `${cleanUsername}@${USERNAME_DOMAIN}`;

  // Service-role client — bypasses RLS, only used here on the server.
  const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
    auth: { autoRefreshToken: false, persistSession: false },
  });

  const { data: created, error: createErr } = await admin.auth.admin.createUser({
    email: syntheticEmail,
    password,
    email_confirm: true, // skip email verification — internal accounts only
    user_metadata: { full_name: fullName || cleanUsername, username: cleanUsername },
  });
  if (createErr) {
    const msg = /already.*registered|already exists/i.test(createErr.message)
      ? `Username "${cleanUsername}" is already taken.`
      : createErr.message;
    res.status(400).json({ error: msg });
    return;
  }

  // Upsert (not update) — some Supabase projects don't fire the
  // on_auth_user_created trigger for admin-created users, which would
  // leave no profile row for `.update()` to match. Upsert guarantees
  // the row exists either way.
  await admin.from('profiles').upsert({
    id: created.user.id,
    role,
    full_name: fullName || cleanUsername,
    email: syntheticEmail,
  }, { onConflict: 'id' });

  res.status(200).json({ ok: true, id: created.user.id, username: cleanUsername, role });
};

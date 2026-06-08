/* ============================================================
   One-time setup: creates the initial super_admin and team
   accounts directly via the Supabase service-role API (no
   email verification — internal accounts only).

   Run locally (never commit your service-role key):
     SUPABASE_URL=https://xxxx.supabase.co \
     SUPABASE_SERVICE_ROLE_KEY=eyJ... \
     node scripts/seed-admin-users.mjs

   Get the service-role key from: Supabase dashboard >
   Project Settings > API > service_role (secret).
   ============================================================ */
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const DOMAIN = 'team.optimityfx.local';

if (!SUPABASE_URL || !SERVICE_ROLE_KEY) {
  console.error('Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars first.');
  process.exit(1);
}

const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false },
});

const ACCOUNTS = [
  { username: 'superadmin', password: 'Well@2314', fullName: 'Super Admin', role: 'super_admin' },
  { username: 'team',       password: '1111',      fullName: 'Team Member', role: 'team' },
];

for (const acc of ACCOUNTS) {
  const email = `${acc.username}@${DOMAIN}`;
  const { data, error } = await admin.auth.admin.createUser({
    email,
    password: acc.password,
    email_confirm: true,
    user_metadata: { full_name: acc.fullName, username: acc.username },
  });

  if (error) {
    console.error(`✗ ${acc.username}: ${error.message}`);
    continue;
  }

  await admin.from('profiles').update({
    role: acc.role,
    full_name: acc.fullName,
    email,
  }).eq('id', data.user.id);

  console.log(`✓ Created ${acc.username} (${acc.role}) — login with username "${acc.username}"`);
}

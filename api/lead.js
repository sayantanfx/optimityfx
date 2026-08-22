/**
 * POST /api/lead  — progressive lead capture for the NextGen AI Artists funnel.
 *
 * Two-phase, exactly like the funnel we reverse-engineered:
 *   1) modal opens  -> { status:"form_started", source }            => creates a row, returns { id }
 *   2) form submit  -> { id, status:"registered", name,email,phone } => updates that same row
 *
 * Storage: Airtable (no SDK needed — plain REST). Set these env vars in Vercel:
 *   AIRTABLE_TOKEN     Personal access token (scope: data.records:read + write)
 *   AIRTABLE_BASE_ID   e.g. appXXXXXXXXXXXXXX
 *   AIRTABLE_TABLE     table name, e.g. "Leads"   (defaults to "Leads")
 *
 * Airtable "Leads" table fields (create these columns):
 *   Name (text) · Email (text) · Phone (text) · Status (single select: form_started/registered)
 *   Source (text) · Created (created-time, automatic) · UserAgent (text)
 *
 * Want Supabase/Google Sheets instead? Swap the two helper calls at the bottom.
 */

const AIRTABLE_TOKEN = process.env.AIRTABLE_TOKEN;
const BASE_ID = process.env.AIRTABLE_BASE_ID;
const TABLE = encodeURIComponent(process.env.AIRTABLE_TABLE || "Leads");
const AT_URL = `https://api.airtable.com/v0/${BASE_ID}/${TABLE}`;

function json(res, code, body) {
  res.status(code).setHeader("Content-Type", "application/json");
  res.end(JSON.stringify(body));
}

async function readBody(req) {
  if (req.body && typeof req.body === "object") return req.body; // Vercel already parsed
  const chunks = [];
  for await (const c of req) chunks.push(c);
  const raw = Buffer.concat(chunks).toString("utf8") || "{}";
  try { return JSON.parse(raw); } catch { return {}; }
}

async function atCreate(fields) {
  const r = await fetch(AT_URL, {
    method: "POST",
    headers: { Authorization: `Bearer ${AIRTABLE_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ fields, typecast: true }),
  });
  if (!r.ok) throw new Error(`airtable create ${r.status}: ${await r.text()}`);
  return (await r.json()).id;
}

async function atUpdate(id, fields) {
  const r = await fetch(`${AT_URL}/${id}`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${AIRTABLE_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ fields, typecast: true }),
  });
  if (!r.ok) throw new Error(`airtable update ${r.status}: ${await r.text()}`);
  return (await r.json()).id;
}

export default async function handler(req, res) {
  // CORS (safe to keep; same-origin in prod)
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return json(res, 405, { error: "method_not_allowed" });

  if (!AIRTABLE_TOKEN || !BASE_ID) {
    // Fail soft: never block the user's registration just because storage isn't wired yet.
    return json(res, 200, { id: null, saved: false, note: "storage_not_configured" });
  }

  const b = await readBody(req);
  const status = (b.status === "registered") ? "registered" : "form_started";

  // Build the field set. Only overwrite name/email/phone when provided.
  const fields = { Status: status };
  if (b.source) fields.Source = String(b.source).slice(0, 60);
  if (b.name) fields.Name = String(b.name).slice(0, 120);
  if (b.email) fields.Email = String(b.email).slice(0, 160);
  if (b.phone) fields.Phone = String(b.phone).replace(/\D/g, "").slice(0, 15);
  const ua = req.headers["user-agent"];
  if (ua) fields.UserAgent = String(ua).slice(0, 250);

  try {
    let id = b.id;
    if (id) {
      await atUpdate(id, fields);
    } else {
      id = await atCreate(fields);
    }
    return json(res, 200, { id, saved: true });
  } catch (err) {
    // Log for observability, but still let the client proceed to the group.
    console.error("lead save failed:", err.message);
    return json(res, 200, { id: b.id || null, saved: false });
  }
}

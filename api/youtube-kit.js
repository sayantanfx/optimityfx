/* ============================================================
   POST /api/youtube-kit
   Generates SEO-friendly YouTube metadata from a pasted video
   script: 10 title options, a description, and comma-separated
   tags under 500 characters.

   Provider is chosen by which env var is set in Vercel
   (Project → Settings → Environment Variables):
     GEMINI_API_KEY     → Google Gemini Flash (free tier)
     ANTHROPIC_API_KEY  → Claude Haiku (paid, used if no Gemini key)
   Keys stay server-side and must never be committed to this repo.

   Body: { script, focusKeyword? }
   Returns: { titles: string[], description: string, tags: string }
   ============================================================ */
const Anthropic = require('@anthropic-ai/sdk');

const MAX_SCRIPT_CHARS = 30000;
const MAX_TAGS_CHARS = 500;

const SYSTEM_PROMPT = `You are an expert YouTube SEO strategist who has grown multiple channels past 1M subscribers. You write metadata that ranks in YouTube search AND earns clicks from browse/suggested feeds.

Rules for TITLES (return exactly 10):
- Under 70 characters each; front-load the main keyword in the first 40 characters.
- Mix styles across the 10: how-to, curiosity gap, listicle, bold claim, question, negative angle ("stop doing X"), result-driven ("I did X for 30 days").
- Never clickbait that the script can't deliver on. No ALL-CAPS words except 1 max per title. No quotes around titles.
- Match the language of the script.

Rules for DESCRIPTION:
- 150-250 words. The first 2 lines must hook and contain the main keyword — they show above the fold in search.
- Then a short paragraph summarizing the value of the video (what the viewer will learn/see), naturally weaving in 3-5 secondary keywords from the script.
- End with a call-to-action line (subscribe/comment) and 3-5 relevant hashtags on the final line.
- Do not invent links, timestamps, social handles, or facts not present in the script.
- Match the language of the script.

Rules for TAGS:
- Comma-separated, no "#" symbols, lowercase except proper nouns.
- Order: main keyword first, then long-tail variations, then broader category tags.
- STRICT LIMIT: the entire tags string must be UNDER 500 characters. Aim for 400-480.`;

function buildUserPrompt(script, focusKeyword) {
  let prompt = '';
  if (focusKeyword) {
    prompt += `Main focus keyword to optimize for: "${focusKeyword}"\n\n`;
  }
  prompt += `Here is the full video script. Generate the YouTube metadata for it:\n\n<script>\n${script}\n</script>`;
  return prompt;
}

/* Trim a comma-separated tag string to the limit at a tag boundary. */
function clampTags(tags) {
  let t = String(tags || '').replace(/#/g, '').trim();
  if (t.length <= MAX_TAGS_CHARS) return t;
  t = t.slice(0, MAX_TAGS_CHARS);
  const lastComma = t.lastIndexOf(',');
  return (lastComma > 0 ? t.slice(0, lastComma) : t).trim();
}

function normalizeResult(data) {
  return {
    titles: (data.titles || []).slice(0, 10).map((t) => String(t).trim()).filter(Boolean),
    description: String(data.description || '').trim(),
    tags: clampTags(data.tags),
  };
}

/* Small helper so provider errors surface as clean HTTP responses. */
class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

/* ---------------- Google Gemini (free tier) ---------------- */
const GEMINI_MODEL = 'gemini-flash-latest';

const GEMINI_SCHEMA = {
  type: 'OBJECT',
  properties: {
    titles: { type: 'ARRAY', items: { type: 'STRING' }, description: 'Exactly 10 SEO-friendly YouTube title options' },
    description: { type: 'STRING', description: 'Full YouTube video description' },
    tags: { type: 'STRING', description: 'Comma-separated YouTube tags, under 500 characters total' },
  },
  required: ['titles', 'description', 'tags'],
};

async function generateWithGemini(script, focusKeyword) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-goog-api-key': process.env.GEMINI_API_KEY,
    },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
      contents: [{ parts: [{ text: buildUserPrompt(script, focusKeyword) }] }],
      generationConfig: {
        responseMimeType: 'application/json',
        responseSchema: GEMINI_SCHEMA,
      },
    }),
  });

  if (res.status === 429) {
    throw new HttpError(429, 'Free AI quota hit for now — wait a minute and try again.');
  }
  if (res.status === 400 || res.status === 401 || res.status === 403) {
    throw new HttpError(500, 'The Gemini API key configured on the server is invalid or expired.');
  }
  if (!res.ok) {
    throw new HttpError(502, `AI service error (${res.status}). Try again shortly.`);
  }

  const body = await res.json();
  const candidate = body.candidates && body.candidates[0];
  if (!candidate || !candidate.content || !candidate.content.parts) {
    if (body.promptFeedback && body.promptFeedback.blockReason) {
      throw new HttpError(422, 'The AI declined to process this script. Please review the content and try again.');
    }
    throw new HttpError(502, 'The AI returned an empty response. Try again shortly.');
  }
  // Join text parts, skipping "thought" summary parts if present.
  const text = candidate.content.parts
    .filter((p) => typeof p.text === 'string' && !p.thought)
    .map((p) => p.text)
    .join('');
  return JSON.parse(text);
}

/* ---------------- Anthropic Claude (paid) ---------------- */
const CLAUDE_SCHEMA = {
  type: 'object',
  properties: {
    titles: { type: 'array', items: { type: 'string' }, description: 'Exactly 10 SEO-friendly YouTube title options' },
    description: { type: 'string', description: 'Full YouTube video description' },
    tags: { type: 'string', description: 'Comma-separated YouTube tags, under 500 characters total' },
  },
  required: ['titles', 'description', 'tags'],
  additionalProperties: false,
};

async function generateWithClaude(script, focusKeyword) {
  const client = new Anthropic();
  let response;
  try {
    response = await client.messages.create({
      model: 'claude-haiku-4-5',
      max_tokens: 3000,
      system: SYSTEM_PROMPT,
      messages: [{ role: 'user', content: buildUserPrompt(script, focusKeyword) }],
      output_config: { format: { type: 'json_schema', schema: CLAUDE_SCHEMA } },
    });
  } catch (err) {
    if (err instanceof Anthropic.AuthenticationError) {
      throw new HttpError(500, 'The Anthropic API key configured on the server is invalid.');
    }
    if (err instanceof Anthropic.RateLimitError) {
      throw new HttpError(429, 'Rate limited — wait a minute and try again.');
    }
    if (err instanceof Anthropic.APIConnectionError) {
      throw new HttpError(502, 'Could not reach the AI service. Try again shortly.');
    }
    if (err instanceof Anthropic.APIError) {
      throw new HttpError(502, `AI service error (${err.status || 'unknown'}). Try again shortly.`);
    }
    throw err;
  }

  if (response.stop_reason === 'refusal') {
    throw new HttpError(422, 'The AI declined to process this script. Please review the content and try again.');
  }
  if (response.stop_reason === 'max_tokens') {
    throw new HttpError(502, 'The response was cut short. Try a shorter script.');
  }
  const textBlock = response.content.find((b) => b.type === 'text');
  return JSON.parse(textBlock.text);
}

/* ---------------- handler ---------------- */
module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');

  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const { script, focusKeyword } = req.body || {};
  const cleanScript = typeof script === 'string' ? script.trim() : '';
  if (cleanScript.length < 100) {
    res.status(400).json({ error: 'Please paste a script of at least 100 characters.' });
    return;
  }
  if (cleanScript.length > MAX_SCRIPT_CHARS) {
    res.status(400).json({ error: `Script is too long (max ${MAX_SCRIPT_CHARS.toLocaleString()} characters). Trim it and try again.` });
    return;
  }
  const cleanKeyword =
    typeof focusKeyword === 'string' ? focusKeyword.trim().slice(0, 120) : '';

  if (!process.env.GEMINI_API_KEY && !process.env.ANTHROPIC_API_KEY) {
    res.status(500).json({
      error: 'Server has no AI key configured. Add GEMINI_API_KEY (free) or ANTHROPIC_API_KEY in Vercel → Project → Settings → Environment Variables, then redeploy.',
    });
    return;
  }

  try {
    const data = process.env.GEMINI_API_KEY
      ? await generateWithGemini(cleanScript, cleanKeyword)
      : await generateWithClaude(cleanScript, cleanKeyword);
    res.status(200).json(normalizeResult(data));
  } catch (err) {
    if (err instanceof HttpError) {
      res.status(err.status).json({ error: err.message });
    } else if (err instanceof SyntaxError) {
      res.status(502).json({ error: 'The AI returned malformed data. Try again.' });
    } else {
      console.error('youtube-kit unexpected error:', err);
      res.status(500).json({ error: 'Unexpected server error. Try again shortly.' });
    }
  }
};

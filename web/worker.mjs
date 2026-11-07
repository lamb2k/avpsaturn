// Private AvP test site: everything except sign-in and licence pages needs a session. Image parts come from a private R2 bucket.
const encoder = new TextEncoder();
const SESSION = "avp_test_session", SESSION_SECONDS = 8 * 60 * 60, GUESSES_PER_MINUTE = 10;
const OPEN = new Set(["/signin.html", "/signin.css", "/signin.mjs", "/style.css", "/licenses.html", "/LICENSE-GPL-2.0.txt", "/LICENSE-GPL-3.0.txt", "/yabause-web.patch", "/build-core.sh"]);
const guesses = new Map();

const b64 = bytes => btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const unb64 = v => { try { return Uint8Array.from(atob(v.replace(/-/g, "+").replace(/_/g, "/") + "="), c => c.charCodeAt(0)); } catch { return null; } };
const hmacKey = secret => crypto.subtle.importKey("raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
const sessionKey = env => hmacKey(`session:${env.TEST_USERNAME}:${env.TEST_PASSWORD}`);

function secure(response) {
  const h = new Headers(response.headers);
  h.set("Cache-Control", "private, no-store");
  h.set("X-Content-Type-Options", "nosniff");
  h.set("Referrer-Policy", "no-referrer");
  h.set("Cross-Origin-Resource-Policy", "same-origin");
  // EmulatorJS loads its core from blob scripts and sets inline styles.
  h.set("Content-Security-Policy", "default-src 'self'; script-src 'self' 'wasm-unsafe-eval' blob:; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; media-src 'self' blob:; connect-src 'self' blob: data:; worker-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'");
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers: h });
}
const reply = (text, status, headers = {}) => secure(new Response(text, { status, headers }));

async function sessionValid(request, env) {
  const cookies = request.headers.get("Cookie") ?? "";
  if (cookies.length > 2048) return false;
  const field = cookies.split(";").map(x => x.trim()).find(x => x.startsWith(SESSION + "="));
  const m = field && /^(1\.([0-9]{1,12})\.[A-Za-z0-9_-]{32})\.([A-Za-z0-9_-]{43})$/.exec(field.slice(SESSION.length + 1));
  if (!m) return false;
  const expires = Number(m[2]), now = Math.floor(Date.now() / 1000);
  if (expires <= now || expires > now + SESSION_SECONDS) return false;
  const signature = unb64(m[3]);
  return !!signature && crypto.subtle.verify("HMAC", await sessionKey(env), signature, encoder.encode(m[1]));
}
async function newSession(env) {
  const payload = `1.${Math.floor(Date.now() / 1000) + SESSION_SECONDS}.${b64(crypto.getRandomValues(new Uint8Array(24)))}`;
  const signature = new Uint8Array(await crypto.subtle.sign("HMAC", await sessionKey(env), encoder.encode(payload)));
  return `${SESSION}=${payload}.${b64(signature)}; Path=/; HttpOnly; SameSite=Strict; Secure; Max-Age=${SESSION_SECONDS}`;
}
// Constant-time compare through HMAC verify.
async function matches(provided, expected) {
  const key = await hmacKey(expected);
  return crypto.subtle.verify("HMAC", key, await crypto.subtle.sign("HMAC", key, encoder.encode(expected)), encoder.encode(provided));
}
function guessRow(request, now = Date.now()) {
  const key = request.headers.get("CF-Connecting-IP") ?? "local";
  let row = guesses.get(key);
  if (!row || now - row.start >= 60000) {
    if (guesses.size > 4096) guesses.clear();
    row = { start: now, count: 0 }; guesses.set(key, row);
  }
  return { key, row };
}

async function signIn(request, env, url) {
  if (request.headers.get("Origin") !== url.origin) return reply("Origin refused", 403);
  const { key, row } = guessRow(request);
  if (row.count >= GUESSES_PER_MINUTE) return reply("Too many sign-in attempts. Try again in a minute.", 429, { "Retry-After": "60" });
  if (!request.headers.get("Content-Type")?.toLowerCase().startsWith("application/json")) return reply("Invalid request", 400);
  const text = await request.text();
  if (text.length > 1024) return reply("Invalid request", 400);
  let body; try { body = JSON.parse(text); } catch { return reply("Invalid request", 400); }
  if (typeof body?.username !== "string" || typeof body?.password !== "string") return reply("Invalid request", 400);
  if (!await matches(`${body.username}:${body.password}`, `${env.TEST_USERNAME}:${env.TEST_PASSWORD}`)) {
    row.count++;
    if (env.SIGNIN_LIMIT && !(await env.SIGNIN_LIMIT.limit({ key })).success) row.count = GUESSES_PER_MINUTE;
    return reply("Sign-in failed", 401);
  }
  return reply("Signed in", 200, { "Set-Cookie": await newSession(env) });
}

async function file(request, env, url) {
  const key = url.pathname.slice("/files/".length);
  if (!/^[A-Za-z0-9._-]+$/.test(key) || key.includes("..")) return reply("Not found", 404);
  const object = request.method === "HEAD" ? await env.TEST_FILES.head(key) : await env.TEST_FILES.get(key);
  if (!object) return reply("Not found", 404);
  return secure(new Response(request.method === "HEAD" ? null : object.body, { headers: {
    "Content-Type": key.endsWith(".json") ? "application/json" : "application/octet-stream",
    "Content-Length": String(object.size), "ETag": object.httpEtag } }));
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (typeof env.TEST_USERNAME !== "string" || typeof env.TEST_PASSWORD !== "string" || env.TEST_PASSWORD.length < 16) return reply("Tester access not configured", 503);
    if (url.pathname === "/signin" && request.method === "POST") return signIn(request, env, url);
    if (!["GET", "HEAD"].includes(request.method)) return reply("Method not allowed", 405, { Allow: "GET, HEAD" });
    const asset = pathname => { const u = new URL(request.url); u.pathname = pathname; return env.ASSETS.fetch(new Request(u, { method: request.method })); };
    if (url.pathname === "/signin") return secure(await asset("/signin.html"));
    if (OPEN.has(url.pathname)) return secure(await asset(url.pathname));
    if (!await sessionValid(request, env)) {
      if (url.pathname === "/" && request.headers.get("Accept")?.includes("text/html")) return reply("", 302, { Location: "/signin" });
      return reply("Tester login required", 401);
    }
    if (url.pathname.startsWith("/files/")) return file(request, env, url);
    return secure(await asset(url.pathname));
  }
};

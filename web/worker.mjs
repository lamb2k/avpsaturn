// Open AvP test site (owner: "Open is fine"). Page and core come from assets; image parts from R2. Parts are named by content, so browsers and the edge may keep them.
const FILES_PER_MINUTE = 120;
const rows = new Map();
const types = { json: "application/json" };

function allowed(request, now = Date.now()) {
  const key = request.headers.get("CF-Connecting-IP") ?? "local";
  let row = rows.get(key);
  if (!row || now - row.start >= 60000) {
    if (rows.size > 4096) rows.clear();
    row = { start: now, count: 0 }; rows.set(key, row);
  }
  return ++row.count <= FILES_PER_MINUTE;
}

async function file(request, env, url) {
  const key = url.pathname.slice("/files/".length);
  if (!/^[A-Za-z0-9._-]+$/.test(key)) return new Response("Not found", { status: 404 });
  if (!allowed(request)) return new Response("Too many requests", { status: 429, headers: { "Retry-After": "60" } });
  const object = request.method === "HEAD" ? await env.TEST_FILES.head(key) : await env.TEST_FILES.get(key);
  if (!object) return new Response("Not found", { status: 404 });
  const isBuild = key === "build.json";
  return new Response(request.method === "HEAD" ? null : object.body, { headers: {
    "Content-Type": types[key.split(".").pop()] ?? "application/octet-stream",
    "Content-Length": String(object.size), "ETag": object.httpEtag,
    "Cache-Control": isBuild ? "no-cache" : "public, max-age=31536000, immutable" } });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!["GET", "HEAD"].includes(request.method)) return new Response("Method not allowed", { status: 405, headers: { Allow: "GET, HEAD" } });
    if (url.pathname.startsWith("/files/")) return file(request, env, url);
    return env.ASSETS.fetch(request);
  }
};

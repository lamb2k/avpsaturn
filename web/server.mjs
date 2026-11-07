// Local test server, 127.0.0.1 only. args: --image DIR (holds build.json and the image) --runtime DIR (EmulatorJS data with the core) [--port N]
import http from "node:http"; import fs from "node:fs"; import path from "node:path"; import { fileURLToPath } from "node:url";
const arg = n => { const i = process.argv.indexOf(`--${n}`); return i < 0 ? undefined : process.argv[i + 1]; };
const image = arg("image"), runtime = arg("runtime");
if (!image || !runtime) { console.error("usage: server.mjs --image DIR --runtime DIR [--port N]"); process.exit(2); }
const pub = path.join(path.dirname(fileURLToPath(import.meta.url)), "public");
const roots = [["/files/", image], ["/runtime/", runtime], ["/", pub]];
const types = { ".html":"text/html", ".js":"text/javascript", ".mjs":"text/javascript", ".css":"text/css", ".json":"application/json", ".wasm":"application/wasm" };
const server = http.createServer((q, a) => {
  let u; try { u = decodeURIComponent(new URL(q.url, "http://x").pathname); } catch { a.writeHead(400); return a.end(); }
  if (u === "/") u = "/index.html";
  const [prefix, root] = roots.find(([p]) => u.startsWith(p));
  const f = path.resolve(root, u.slice(prefix.length));
  if (!f.startsWith(path.resolve(root) + path.sep) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { a.writeHead(404); return a.end(); }
  const n = fs.statSync(f).size;
  a.setHeader("Content-Type", types[path.extname(f)] || "application/octet-stream");
  a.setHeader("Accept-Ranges", "bytes"); a.setHeader("Cache-Control", "no-store");
  const m = /bytes=(\d+)-(\d*)/.exec(q.headers.range || "");
  if (m) {
    const s = +m[1], e = m[2] ? +m[2] : n - 1;
    a.writeHead(206, { "Content-Range": `bytes ${s}-${e}/${n}`, "Content-Length": e - s + 1 });
    return q.method === "HEAD" ? a.end() : fs.createReadStream(f, { start: s, end: e }).pipe(a);
  }
  a.setHeader("Content-Length", n); a.writeHead(200);
  return q.method === "HEAD" ? a.end() : fs.createReadStream(f).pipe(a);
});
server.listen(+(arg("port") ?? 0), "127.0.0.1", () => console.log(`http://127.0.0.1:${server.address().port}/`));

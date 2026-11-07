// Headless Edge against a local server: load, Play, title, coin, start, select, Round 1, Reset, and a second load from the cache. Stills and a receipt in OUT.
// Keys go only to this browser's own page over DevTools. Stops only its own children.
// usage: node live-test.mjs OUT (live site)
import { writeFile, readFile, mkdir, mkdtemp } from "node:fs/promises"; import { spawn } from "node:child_process"; import path from "node:path"; import { fileURLToPath } from "node:url";
const [out] = process.argv.slice(2);
if (!out) { console.error("usage: live-test.mjs OUT"); process.exit(2); }
await mkdir(out, { recursive: true });
const profile = await mkdtemp(path.join(out, "profile-"));
const here = path.dirname(fileURLToPath(import.meta.url));
const base = "https://avp.retronetplay.com/"; const srv = { kill() {} };
const br = spawn("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", ["--headless=new", "--disable-sync", "--disable-extensions", "--no-first-run", "--use-angle=d3d11", "--autoplay-policy=no-user-gesture-required", "--disable-background-timer-throttling", "--disable-renderer-backgrounding", "--window-size=900,1000", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const R = { base, steps: [], errors: [], stills: [] };
const save = () => writeFile(path.join(out, "receipt.json"), JSON.stringify(R, null, 1));
const stop = c => { br.kill(); srv.kill(); process.exit(c); };
setTimeout(async () => { R.hardStop = true; await save(); stop(2); }, 240000);
let port; for (let n = 0; n < 150; n++) { try { port = (await readFile(path.join(profile, "DevToolsActivePort"), "utf8")).split("\n")[0]; break; } catch { await sleep(100); } }
const t = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(x => x.type === "page");
const ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener("open", r, { once: true }));
let id = 0; const pend = new Map(); const T0 = Date.now(), S = () => +((Date.now() - T0) / 1000).toFixed(1);
ws.addEventListener("message", e => { const v = JSON.parse(e.data); if (v.id && pend.has(v.id)) { const p = pend.get(v.id); pend.delete(v.id); v.error ? p.reject(Error(v.error.message)) : p.resolve(v.result); return; }
  if (v.method === "Runtime.exceptionThrown") R.errors.push([S(), (v.params.exceptionDetails.exception?.description || v.params.exceptionDetails.text).slice(0, 400)]); });
const call = (m, p = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method: m, params: p })); });
const ev = async x => { const r = await call("Runtime.evaluate", { expression: x, returnByValue: true, awaitPromise: true, userGesture: true }); if (r.exceptionDetails) throw Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text); return r.result.value; };
const still = async l => { const s = await call("Page.captureScreenshot", { format: "png" }); await writeFile(path.join(out, `${l}.png`), Buffer.from(s.data, "base64")); R.stills.push(l); };
const step = async (l, x = {}) => { R.steps.push({ l, s: S(), status: await ev("document.getElementById('status').textContent"), ...x }); await save(); };
const until = async (x, ms) => { const end = Date.now() + ms; while (Date.now() < end) { if (await ev(x).catch(() => false)) return true; await sleep(200); } return false; };
const KEYS = { coin: ["5", "Digit5", 53], start: ["Enter", "Enter", 13], gun: ["c", "KeyC", 67], attack: ["z", "KeyZ", 90], right: ["ArrowRight", "ArrowRight", 39] };
const key = async (name, hold = 120) => { const [k, code, vk] = KEYS[name]; const a = { key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk };
  await call("Input.dispatchKeyEvent", { type: "keyDown", ...a }); await sleep(hold); await call("Input.dispatchKeyEvent", { type: "keyUp", ...a }); };
const guest = () => ev(`(()=>{const M=EJS_emulator.gameManager.Module,p=M._web_peek8;if(!p)return null;const r=a=>((p(a)<<24)|(p(a+1)<<16)|(p(a+2)<<8)|p(a+3))>>>0;if(!window.__d)for(let a=0x060c0000;a<0x060fff00;a+=4)if(r(a)===0x53415452){window.__d=a;break}const d=window.__d;if(!d)return null;const b=d+0x74;return{vb:r(d+8),fatal:r(d+28),att:p(b+0x81b0),cred:p(b+0x818c),sec:p(b+0xd182),hp:(p(b+0x83c0)<<8)|p(b+0x83c1)}})()`).catch(() => null);
const untilGuest = async (f, ms) => { const end = Date.now() + ms; while (Date.now() < end) { const g = await guest(); if (g && f(g)) return g; await sleep(300); } return null; };
const clickPlay = async () => { const r = await ev("(()=>{const r=document.getElementById('play').getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()");
  for (const type of ["mousePressed", "mouseReleased"]) await call("Input.dispatchMouseEvent", { type, button: "left", clickCount: 1, x: r.x, y: r.y }); };
let code = 1;
try {
  for (const d of ["Page", "Runtime"]) await call(`${d}.enable`);
  await call("Emulation.setFocusEmulationEnabled", { enabled: true });
  await call("Page.navigate", { url: base });
  if (!await until("document.getElementById('play')?.disabled===false", 90000)) throw Error("not ready: " + await ev("document.getElementById('status').textContent"));
  R.firstLoad = await ev("window.avpLoad"); R.resources = await ev("performance.getEntriesByType('resource').filter(e=>e.name.includes('/files/')).map(e=>[e.name.split('/').pop(),Math.round(e.duration),e.transferSize])"); await step("ready"); await still("01-ready");
  await clickPlay();
  if (!await until("window.avpLoad.running>0", 30000)) throw Error("no game start");
  R.running = await ev("window.avpLoad"); await step("running");
  if (!await untilGuest(g => g.vb > 300, 60000)) throw Error("guest did not start");
  await still("02-title");
  if (!await untilGuest(g => g.vb > 1250, 40000)) throw Error("attract stalled");
  await ev("window.__k=[];for(const t of ['keydown','keyup'])document.addEventListener(t,e=>window.__k.push([t,e.keyCode,e.target.tagName,EJS_emulator.settingsMenu.style.display,EJS_emulator.isPopupOpen(),EJS_emulator.getSettingValue('keyboardInput'),EJS_emulator.started]),true);const o=EJS_emulator.gameManager.simulateInput.bind(EJS_emulator.gameManager);EJS_emulator.gameManager.simulateInput=(a,b,c)=>{window.__k.push(['sim',a,b,c]);o(a,b,c)};1");
  let c = null; for (let n = 0; n < 4 && !c; n++) { await key("coin"); c = await untilGuest(g => g.cred > 0, 2000); } R.keylog = await ev("JSON.stringify(window.__k)"); R.g0 = await guest(); await step("coin", { guest: c });
  if (!c) throw Error("coin key had no effect");
  await sleep(400); await key("start"); await sleep(3000); await still("03-select"); await step("start", { guest: await guest() });
  for (let n = 0; n < 8; n++) { await key("gun"); await sleep(1000); const g = await guest(); if (g?.sec) break; }
  const r1 = await untilGuest(g => g.sec >= 1 && g.hp > 0, 40000); await step("round1", { guest: r1 });
  if (!r1) { await key("start"); throw Error("no Round 1"); }
  const fr = () => ev("EJS_emulator.gameManager.getFrameNum()"); const f0 = await fr(), g0 = await guest(), t0 = Date.now();
  const hold = key("right", 30000); for (let n = 0; n < 12; n++) { await sleep(2000); await key("attack"); } await hold; await still("04-round1");
  const secs = (Date.now() - t0) / 1000, g1 = await guest(); R.round1 = { secs, fps: (await fr() - f0) / secs, vbPerSec: (g1.vb - g0.vb) / secs, hp: g1.hp, sec: g1.sec };
  const before = await guest(); await step("played", { guest: before });
  if (before.fatal) throw Error("guest fatal " + before.fatal);
  await ev("document.getElementById('reset').click()"); const after = await untilGuest(g => g.vb > 200, 40000) ; await sleep(0); await step("reset", { guest: after, before: before.vb }); await still("05-after-reset");
  R.resetOk = !!after && after.vb < before.vb;
  await call("Page.reload");
  await sleep(500);
  if (!await until("document.getElementById('play')?.disabled===false", 40000)) throw Error("second load not ready");
  R.secondLoad = await ev("window.avpLoad"); R.resources2 = await ev("performance.getEntriesByType('resource').filter(e=>e.name.includes('/files/')).map(e=>[e.name.split('/').pop(),Math.round(e.duration),e.transferSize])"); await step("second-load");
  code = R.resetOk && R.secondLoad.fromCache ? 0 : 1;
  R.result = code ? "partial" : "pass";
} catch (e) { R.result = "fail: " + e.message; await still("fail").catch(() => {}); }
await save(); console.log(R.result); stop(code);

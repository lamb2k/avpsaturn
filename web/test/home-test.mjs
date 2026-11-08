// Headless Edge against a local server: load, Play, title, coin, start, select, Round 1, Reset, and a second load from the cache. Stills and a receipt in OUT.
// Keys go only to this browser's own page over DevTools. Stops only its own children.
// usage: node edge-test.mjs OUT IMAGE_DIR RUNTIME_DIR
import { writeFile, readFile, mkdir, mkdtemp } from "node:fs/promises"; import { spawn } from "node:child_process"; import path from "node:path"; import { fileURLToPath } from "node:url";
const [out, image, runtime] = process.argv.slice(2);
if (!runtime) { console.error("usage: edge-test.mjs OUT IMAGE_DIR RUNTIME_DIR"); process.exit(2); }
await mkdir(out, { recursive: true });
const profile = await mkdtemp(path.join(out, "profile-"));
const here = path.dirname(fileURLToPath(import.meta.url));
const srv = spawn(process.execPath, [path.join(here, "..", "server.mjs"), "--image", image, "--runtime", runtime], { stdio: ["ignore", "pipe", "inherit"] });
const base = await new Promise(r => srv.stdout.once("data", d => r(String(d).trim())));
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
const KEYS = { coin: ["5", "Digit5", 53], start: ["Enter", "Enter", 13], gun: ["c", "KeyC", 67], attack: ["z", "KeyZ", 90], right: ["ArrowRight", "ArrowRight", 39], down: ["ArrowDown", "ArrowDown", 40], p2start: ["2", "Digit2", 50], p2gun: ["e", "KeyE", 69], p2left: ["f", "KeyF", 70], p2attack: ["q", "KeyQ", 81] };
const key = async (name, hold = 120) => { const [k, code, vk] = KEYS[name]; const a = { key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk };
  await call("Input.dispatchKeyEvent", { type: "keyDown", ...a }); await sleep(hold); await call("Input.dispatchKeyEvent", { type: "keyUp", ...a }); };
const guest = () => ev(`(()=>{const M=EJS_emulator.gameManager.Module,p=M._web_peek8;if(!p)return null;const r=a=>((p(a)<<24)|(p(a+1)<<16)|(p(a+2)<<8)|p(a+3))>>>0;if(!window.__d)for(let a=0x060c0000;a<0x060fff00;a+=4)if(r(a)===0x53415452){window.__d=a;break}const d=window.__d;if(!d)return null;const b=d+${process.env.RAMB_OFF||"0x84"};return{vb:r(d+8),fatal:r(d+28),att:p(b+0x81b0),cred:p(b+0x818c),sec:p(b+0xd182),hp:(p(b+0x83c0)<<8)|p(b+0x83c1),mode:p(b+0x8001),stage:p(b+0x81e9)}})()`).catch(() => null);
const untilGuest = async (f, ms) => { const end = Date.now() + ms; while (Date.now() < end) { const g = await guest(); if (g && f(g)) return g; await sleep(300); } return null; };
const clickPlay = async () => { const r = await ev("(()=>{const r=document.getElementById('play').getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()");
  for (const type of ["mousePressed", "mouseReleased"]) await call("Input.dispatchMouseEvent", { type, button: "left", clickCount: 1, x: r.x, y: r.y }); };
let code = 1;
try {
  for (const d of ["Page", "Runtime"]) await call(`${d}.enable`);
  await call("Emulation.setFocusEmulationEnabled", { enabled: true });
  await call("Page.navigate", { url: base });
  if (!await until("document.getElementById('play')?.disabled===false", 90000)) throw Error("not ready: " + await ev("document.getElementById('status').textContent"));
  R.firstLoad = await ev("window.avpLoad"); await step("ready"); await still("01-ready");
  await clickPlay();
  if (!await until("window.avpLoad.running>0", 30000)) throw Error("no game start");
  R.running = await ev("window.avpLoad"); await step("running");
  if (!await untilGuest(g => g.vb > 300, 60000)) throw Error("guest did not start");
  await still("02-title");
  // Home build: no coin. The title menu shows about 150 vblanks after the title; Start confirms START GAME.
  if (!await untilGuest(g => g.vb > 900, 60000)) throw Error("attract stalled");
  await still("03-home-menu"); await step("home-menu", { guest: await guest() });
  if (process.env.DUEL) {
    // DUEL is the third title item: Down twice, Start. Player 2 uses its own keys.
    await key("down"); await sleep(300); await key("down"); await sleep(300); await still("03b-duel-selected"); await key("start");
    R.duel = [];
    for (let n = 0; n < 12; n++) {
      await sleep(2000);
      const d = await guest(); d.hp2 = await ev(`(()=>{const p=EJS_emulator.gameManager.Module._web_peek8,b=window.__d+${process.env.RAMB_OFF||"0x84"};return (p(b+0x84c0)<<8)|p(b+0x84c1)})()`); R.duel.push(d);
      await still(`d-${String(n).padStart(2, "0")}`);
      if (n < 6) { await key(n % 2 ? "gun" : "start"); await key(n % 2 ? "p2gun" : "p2start"); }
      else { await Promise.all([key("right", 800), key("p2left", 800)]); await key("attack"); await key("p2attack"); }
    }
    await step("duel", { guest: await guest() }); await save(); stop(0);
  }
  let g = null;
  for (let n = 0; n < 20 && !(g = await untilGuest(x => x.att === 0 && x.mode === 2 && x.hp > 0, 1500)); n++) { await key(n % 2 ? "gun" : "start"); }
  await step("in-play", { guest: g });
  if (!g) throw Error("START GAME did not reach play");
  const hold = key("right", 3000); await sleep(1000); await key("attack"); await hold; await still("04-stage");
  await key("start"); await sleep(1500); await still("05-pause"); const p1 = await guest(); await sleep(1000); const p2 = await guest();
  R.cdda = await ev("(()=>{const M=EJS_emulator.gameManager.Module;return [M._web_pc(8),M._web_pc(9)]})()");
  R.pause = { hpSame: p1.hp === p2.hp, vb: [p1.vb, p2.vb] };
  await key("start"); await sleep(1500); await still("06-resumed"); await step("resumed", { guest: await guest() });
  if (process.env.BOSS) {
    // BOSS RUSH is the last title item: quit to title, Up wraps to it, Start opens it.
    await key("start"); await sleep(1200); await call("Input.dispatchKeyEvent", { type: "keyDown", key: "ArrowDown", code: "ArrowDown", windowsVirtualKeyCode: 40 }); await sleep(120); await call("Input.dispatchKeyEvent", { type: "keyUp", key: "ArrowDown", code: "ArrowDown", windowsVirtualKeyCode: 40 });
    await key("start"); await sleep(3000); await untilGuest(g => g.vb > 950 && g.mode === 4, 60000); await still("08-title-again");
    for (const k of ["ArrowUp"]) { await call("Input.dispatchKeyEvent", { type: "keyDown", key: k, code: k, windowsVirtualKeyCode: 38 }); await sleep(120); await call("Input.dispatchKeyEvent", { type: "keyUp", key: k, code: k, windowsVirtualKeyCode: 38 }); }
    await sleep(500); await still("09-boss-rush-selected"); await key("start");
    R.boss = [];
    for (let n = 0; n < 8; n++) { await sleep(2500); R.boss.push(await guest()); await still(`10-boss-${n}`); if (n === 2 || n === 4) await key("start"); }
  }
  const before = await guest(); await step("played", { guest: before });
  if (before.fatal) throw Error("guest fatal " + before.fatal);
  await ev("document.getElementById('reset').click()"); const after = await untilGuest(g => g.vb > 200, 40000) ; await sleep(0); await step("reset", { guest: after, before: before.vb }); await still("07-after-reset");
  R.resetOk = !!after && after.vb < before.vb;
  await call("Page.reload");
  await sleep(500);
  if (!await until("document.getElementById('play')?.disabled===false", 40000)) throw Error("second load not ready");
  R.secondLoad = await ev("window.avpLoad"); await step("second-load");
  code = R.resetOk && R.secondLoad.fromCache ? 0 : 1;
  R.result = code ? "partial" : "pass";
} catch (e) { R.result = "fail: " + e.message; await still("fail").catch(() => {}); }
await save(); console.log(R.result); stop(code);

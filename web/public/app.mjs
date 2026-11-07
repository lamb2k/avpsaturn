// Page flow: read build.json, get the image (verified cache or download with progress), verify the core, then boot on Play.
import { CORE, OPTIONS, CONTROLS } from "/runtime-config.mjs";
const $ = id => document.getElementById(id);
const status = t => { $("status").textContent = t; };
const progress = fraction => {
  $("progress").style.width = `${(fraction * 100).toFixed(1)}%`;
  document.querySelector(".bar").setAttribute("aria-valuenow", String(Math.round(fraction * 100)));
};
const mib = n => `${(n / 1048576).toFixed(0)} MiB`;
const hex = buf => [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
const sha256 = async buf => hex(await crypto.subtle.digest("SHA-256", buf));
const timing = window.avpLoad = { started: performance.now() };

function idb(mode, run) {
  return new Promise((resolve, reject) => {
    const open = indexedDB.open("avp-test-image", 1);
    open.onupgradeneeded = () => open.result.createObjectStore("images");
    open.onerror = () => reject(open.error);
    open.onsuccess = () => {
      const db = open.result, tx = db.transaction("images", mode), req = run(tx.objectStore("images"));
      tx.oncomplete = () => { db.close(); resolve(req?.result); };
      tx.onerror = tx.onabort = () => { db.close(); reject(tx.error); };
    };
  });
}
const cacheGet = hash => idb("readonly", s => s.get(hash)).catch(() => undefined);
const cachePut = (hash, blob) => idb("readwrite", s => { s.clear(); return s.put(blob, hash); }).catch(() => undefined);

async function download(image) {
  const res = await fetch(image.path);
  if (!res.ok) throw new Error(`Image download failed: HTTP ${res.status}`);
  const reader = res.body.getReader(), bytes = new Uint8Array(image.bytes);
  let at = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    if (at + value.length > image.bytes) throw new Error("Image is larger than build.json says");
    bytes.set(value, at); at += value.length;
    progress(at / image.bytes);
    status(`Downloading game ${mib(at)} of ${mib(image.bytes)}`);
  }
  if (at !== image.bytes) throw new Error("Image is smaller than build.json says");
  return bytes;
}

async function prepare() {
  const res = await fetch("/files/build.json", { cache: "no-store" });
  if (!res.ok) throw new Error("No build is published");
  const build = await res.json();
  if (build.status !== "ready") throw new Error("This build is not ready");
  $("build").textContent = `Build ${build.build}, image ${build.image.sha256.slice(0, 12)}, ${mib(build.image.bytes)}`;
  const coreRes = await fetch(`/runtime/${CORE.file}`);
  if (!coreRes.ok || await sha256(await coreRes.arrayBuffer()) !== CORE.sha256) throw new Error("Emulator core does not match its pin");
  let blob = await cacheGet(build.image.sha256);
  timing.fromCache = !!blob;
  if (blob) {
    if (blob.size !== build.image.bytes) { blob = null; timing.fromCache = false; }
    else progress(1);
  }
  if (!blob) {
    const bytes = await download(build.image);
    status("Checking game data");
    if (await sha256(bytes) !== build.image.sha256) throw new Error("Game data failed its check");
    blob = new Blob([bytes]);
    status("Saving game for next time");
    await cachePut(build.image.sha256, blob);
  }
  timing.ready = performance.now();
  const name = build.image.path.split("/").pop();
  return new File([blob], name);
}

function boot(file) {
  Object.assign(window, {
    EJS_player: "#game", EJS_core: "yabause", EJS_gameUrl: file, EJS_gameName: "avp-saturn",
    EJS_pathtodata: "/runtime/", EJS_startOnLoaded: true, EJS_DEBUG_XX: true, EJS_disableDatabases: true,
    EJS_disableLocalStorage: true, EJS_defaultOptions: OPTIONS, EJS_defaultControls: CONTROLS,
    EJS_Buttons: { netplay: false, cheat: false, saveState: false, loadState: false, saveSavFiles: false, loadSavFiles: false, gamepad: true, quickSave: false, quickLoad: false, screenRecord: false },
    EJS_onGameStart: () => {
      timing.running = performance.now();
      status("Running");
      $("reset").disabled = false;
      // Keys work wherever focus is on the page, not only on the emulator's own element.
      const emu = window.EJS_emulator;
      for (const type of ["keydown", "keyup"]) document.addEventListener(type, e => { if (!emu.elements.parent.contains(e.target)) emu.keyChange(e); });
    }
  });
  const s = document.createElement("script");
  s.src = "/runtime/loader.js";
  document.body.append(s);
}

try {
  const file = await prepare();
  status(`Ready${timing.fromCache ? " (saved copy)" : ""}. Press Play.`);
  const play = $("play");
  play.disabled = false;
  play.onclick = () => {
    play.disabled = true;
    status("Starting the emulator");
    boot(file);
  };
  $("reset").onclick = () => { window.EJS_emulator?.gameManager?.restart(); status("Running (reset)"); };
} catch (error) {
  status(error.message);
}

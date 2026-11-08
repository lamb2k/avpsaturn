// Hash-pinned core. A rebuilt core changes this pin on purpose; see core/README.md. The game image is not pinned here: it comes from /files/build.json.
export const CORE = {
  file: "cores/yabause-legacy-wasm.data",   // EmulatorJS asks for the legacy name without WebGL 2
  sha256: "88a8d8b343a1875a30d698cebe2b7cb3e78d85cc3f058570dc7af62691f6ba4a"
};
export const OPTIONS = {
  yabause_addon_cartridge: "4M_ram",
  yabause_force_hle_bios: "enabled",
  yabause_frameskip: "disabled"
};
const key = (value, value2) => ({ value, value2 });
// Index is the libretro pad button; the core maps Y to Saturn X, B to A, A to B, R to C.
export const CONTROLS = {
  0: { 0: key("z", "BUTTON_1"), 1: key("5", "SELECT"), 2: {}, 3: key("enter", "START"),
       4: key("up arrow", "DPAD_UP"), 5: key("down arrow", "DPAD_DOWN"), 6: key("left arrow", "DPAD_LEFT"), 7: key("right arrow", "DPAD_RIGHT"),
       8: key("x", "BUTTON_2"), 9: {}, 10: {}, 11: key("c", "BUTTON_3") },
  // Player 2 (the home duel): keyboard keys below, or a second gamepad.
  1: { 0: key("q", "BUTTON_1"), 1: {}, 2: {}, 3: key("2", "START"),
       4: key("t", "DPAD_UP"), 5: key("g", "DPAD_DOWN"), 6: key("f", "DPAD_LEFT"), 7: key("h", "DPAD_RIGHT"),
       8: key("w", "BUTTON_2"), 9: {}, 10: {}, 11: key("e", "BUTTON_3") },
  2: {}, 3: {}
};

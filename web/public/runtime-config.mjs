// Hash-pinned core. A rebuilt core changes this pin on purpose; see core/README.md. The game image is not pinned here: it comes from /files/build.json.
export const CORE = {
  file: "cores/yabause-legacy-wasm.data",   // EmulatorJS asks for the legacy name without WebGL 2
  sha256: "c5e05626039d29f7a5300dbb954a6455447e947715af19686122b2744a675eef"
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
  1: {}, 2: {}, 3: {}
};

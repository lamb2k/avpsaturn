
// ---- lane perf-hw 2026-11-12: MODELLED hardware cost + profiler. HW_MODEL=1: cache line fills, cache-through reads and writes are charged by region; HW_PROF=1: PC histogram and access census.
#include <unordered_map>
#include <vector>
#include <map>
#include <algorithm>
namespace hwp {
static unsigned Gi(const char *n, unsigned d) { const char *e = std::getenv(n); return e ? (unsigned)std::strtoul(e, nullptr, 0) : d; }
struct Cfg { unsigned prof, model, hfill, hsingle, hwrite, lwlong, cartbeat, vdp2, vdp1, vdp1r, other, wbuf; };
static const Cfg C = { Gi("HW_PROF",0), Gi("HW_MODEL",0), Gi("HW_HFILL",7), Gi("HW_HSINGLE",7), Gi("HW_HWRITE",4), Gi("HW_LWLONG",14), Gi("HW_CARTBEAT",6), Gi("HW_VDP2",40), Gi("HW_VDP1",45), Gi("HW_VDP1R",29), Gi("HW_OTHER",8), Gi("HW_WBUF",1) };
enum { R_HW, R_LW, R_CART, R_VDP2, R_VDP1, R_OTHER, R_N };
enum { K_IFILL, K_DFILL, K_THRU, K_WRITE, K_WSTALL, K_N };
static inline int Reg(uint32 a) { a &= 0x1FFFFFFF; if (a >= 0x06000000u) return R_HW; if (a >= 0x00200000u && a < 0x00300000u) return R_LW; if (a >= 0x02000000u && a < 0x05000000u) return R_CART; if (a >= 0x05E00000u && a < 0x05FC0000u) return R_VDP2; if (a >= 0x05C00000u && a < 0x05D80000u) return R_VDP1; return R_OTHER; }
// cost of one bus access (cache-through read or write) in SH-2 clocks, bytes 1/2/4
static inline unsigned Single(uint32 a, int bytes, bool wr) {
    switch (Reg(a)) {
    case R_HW: return wr ? C.hwrite : C.hsingle;
    case R_LW: return bytes == 4 ? C.lwlong : (C.lwlong + 1) / 2;
    case R_CART: return bytes == 4 ? 2 * C.cartbeat : C.cartbeat;
    case R_VDP2: return C.vdp2;
    case R_VDP1: return ((a & 0x1FFFFFFF) >= 0x05D00000u) ? C.vdp1r : C.vdp1;
    default: return C.other;
    }
}
static inline unsigned Fill(uint32 a) {   // 16 byte cache line
    switch (Reg(a)) {
    case R_HW: return C.hfill;
    case R_LW: return 4 * C.lwlong;
    case R_CART: return 8 * C.cartbeat;
    default: return 4 * Single(a, 4, false);
    }
}
struct St { uint64 clk = 0, wb = 0; uint32 pen = 0; };
static St S[2];
struct Ac { uint64 cyc[K_N][R_N] = {}; uint64 cnt[K_N][R_N] = {}; uint64 insn = 0, total = 0; };
static Ac A[4];
static int Ph = 0;   // master phase: 0 tasks, 1 vblank irq, 2 idle (set by the write taps in GsProbe)
static inline int V(int cpu) { return cpu ? 1 : (Ph == 1 ? 2 : Ph == 2 ? 3 : 0); }
static const int NV = 4;
static std::vector<uint32> hExec[4][3], hPen[4][3];
static std::unordered_map<uint32, uint64> dFill[4], dThru[4], dWrite[4], iFill[4];
static unsigned resetVb = 0;
static inline bool InitHist() { static bool done = false; if (!done) { done = true; for (int c = 0; c < 4; c++) { hExec[c][0].assign(0x80000, 0); hPen[c][0].assign(0x80000, 0); hExec[c][1].assign(0x80000, 0); hPen[c][1].assign(0x80000, 0); hExec[c][2].assign(0x200000, 0); hPen[c][2].assign(0x200000, 0); } } return true; }
static inline void RecPc(int cpu0, uint32 pc, uint64 c, uint32 pen) {
    int cpu = V(cpu0);
    uint32 a = pc & 0x1FFFFFFF; int r = -1; uint32 i = 0;
    if (a >= 0x06000000u) { r = 0; i = (a & 0xFFFFF) >> 1; }
    else if (a >= 0x00200000u && a < 0x00300000u) { r = 1; i = (a & 0xFFFFF) >> 1; }
    else if (a >= 0x02400000u && a < 0x02800000u) { r = 2; i = (a - 0x02400000u) >> 1; }
    A[cpu].insn++; A[cpu].total += c;
    if (r < 0) return;
    hExec[cpu][r][i]++; hPen[cpu][r][i] += pen;
}
static inline void Stall(int cpu, int k, uint32 a, uint32 cost) {
    St &s = S[cpu]; Ac &x = A[V(cpu)]; int r = Reg(a);
    s.pen += cost; x.cyc[k][r] += cost; x.cnt[k][r]++;
}
static inline unsigned WbWait(int cpu, uint32 a) {
    St &s = S[cpu]; Ac &x = A[V(cpu)];
    uint64 now = s.clk + s.pen; unsigned wait = s.wb > now ? (unsigned)(s.wb - now) : 0;
    if (wait) { s.pen += wait; x.cyc[K_WSTALL][Reg(a)] += wait; x.cnt[K_WSTALL][Reg(a)]++; }
    return wait;
}
static inline void OnFill(int cpu, bool instr, uint32 a) {
    Ac &x = A[V(cpu)];
    if (C.model) WbWait(cpu, a);
    if (C.prof) { if (instr) iFill[V(cpu)][(a & 0x1FFFFFFF) >> 4]++; else dFill[V(cpu)][(a & 0x1FFFFFFF) >> 4]++; }
    if (C.model) Stall(cpu, instr ? K_IFILL : K_DFILL, a, Fill(a)); else x.cnt[instr ? K_IFILL : K_DFILL][Reg(a)]++;
}
static inline void OnThru(int cpu, uint32 a, int bytes) {
    Ac &x = A[V(cpu)];
    if (C.model) WbWait(cpu, a);
    if (C.prof) dThru[V(cpu)][(a & 0x1FFFFFFF) >> 6]++;
    if (C.model) Stall(cpu, K_THRU, a, Single(a, bytes, false)); else x.cnt[K_THRU][Reg(a)]++;
}
static inline void OnWrite(int cpu, uint32 a, int bytes) {
    St &s = S[cpu]; Ac &x = A[V(cpu)];
    unsigned wait = C.model ? WbWait(cpu, a) : 0;
    if (C.prof) dWrite[V(cpu)][(a & 0x1FFFFFFF) >> 6]++;
    x.cnt[K_WRITE][Reg(a)]++;
    if (C.model) { uint64 now = s.clk + s.pen; unsigned w = Single(a, bytes, true); x.cyc[K_WRITE][Reg(a)] += w; if (C.wbuf) s.wb = now + w; else s.pen += w; (void)wait; }
}
static void Reset() { for (int c = 0; c < 4; c++) { A[c] = Ac(); for (int r = 0; r < 3; r++) { std::fill(hExec[c][r].begin(), hExec[c][r].end(), 0); std::fill(hPen[c][r].begin(), hPen[c][r].end(), 0); } dFill[c].clear(); dThru[c].clear(); dWrite[c].clear(); iFill[c].clear(); } }
static void Dump(const char *name, unsigned vb) {
    char fn[256]; std::snprintf(fn, sizeof fn, "E:/AvP/learning/lane-perf-hw/ymir_hw/hwprof_%s.txt", name);
    std::FILE *f = std::fopen(fn, "w"); if (!f) return;
    std::fprintf(f, "WINDOW vb %u .. %u\n", resetVb, vb);
    static const char *kn[K_N] = {"ifill", "dfill", "thru", "write", "wstall"}; static const char *rn[R_N] = {"hw", "lw", "cart", "vdp2", "vdp1", "other"};
    static const uint32 base[3] = {0x06000000u, 0x00200000u, 0x02400000u};
    for (int c = 0; c < 4; c++) {
        Ac &s = A[c];
        std::fprintf(f, "CPU %d insn %llu cycles_total %llu\n", c, (unsigned long long)s.insn, (unsigned long long)s.total);
        for (int k = 0; k < K_N; k++) for (int r = 0; r < R_N; r++) if (s.cnt[k][r] || s.cyc[k][r]) std::fprintf(f, "K %d %s %s n %llu cyc %llu\n", c, kn[k], rn[r], (unsigned long long)s.cnt[k][r], (unsigned long long)s.cyc[k][r]);
        if (hExec[c][0].empty()) continue;
        for (int r = 0; r < 3; r++) {
            size_t n = hExec[c][r].size();
            for (size_t b = 0; b < n; b += 16) {   // 32 byte blocks
                uint64 e = 0, p = 0; for (size_t i = b; i < b + 16 && i < n; i++) { e += hExec[c][r][i]; p += hPen[c][r][i]; }
                if (e || p) std::fprintf(f, "P %d %08X %llu %llu\n", c, base[r] + (uint32)(b * 2), (unsigned long long)e, (unsigned long long)p);
            }
        }
        for (auto &kv : iFill[c]) std::fprintf(f, "IF %d %08X %llu\n", c, kv.first << 4, (unsigned long long)kv.second);
        for (auto &kv : dFill[c]) std::fprintf(f, "DF %d %08X %llu\n", c, kv.first << 4, (unsigned long long)kv.second);
        for (auto &kv : dThru[c]) std::fprintf(f, "DT %d %08X %llu\n", c, kv.first << 6, (unsigned long long)kv.second);
        for (auto &kv : dWrite[c]) std::fprintf(f, "DW %d %08X %llu\n", c, kv.first << 6, (unsigned long long)kv.second);
    }
    std::fclose(f);
}
// command file polled now and then: "reset" or "dump NAME" (the driver writes it; removed when read)
static void Poll() {
    static unsigned n = 0; if (++n < 100000) return; n = 0;
    std::FILE *f = std::fopen("E:/AvP/learning/lane-perf-hw/ymir_hw/hw_cmd.txt", "r"); if (!f) return;
    char cmd[32] = {0}, nm[200] = {0}; int k = std::fscanf(f, "%31s %199s", cmd, nm); std::fclose(f);
    if (k < 1) return; std::remove("E:/AvP/learning/lane-perf-hw/ymir_hw/hw_cmd.txt");
    if (!std::strcmp(cmd, "reset")) { InitHist(); Reset(); resetVb = gsVbPub; }
    else if (!std::strcmp(cmd, "dump")) Dump(nm, gsVbPub);
}
}  // namespace hwp

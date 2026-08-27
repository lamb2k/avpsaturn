/* See avsp_tiles.h. C90, allocation-free, endian-independent. */
#include "avsp_tiles.h"

static unsigned long read_u32(const unsigned char *p)
{
    return ((unsigned long)p[0] << 24) | ((unsigned long)p[1] << 16) |
           ((unsigned long)p[2] << 8) | (unsigned long)p[3];
}

static unsigned int read_u16(const unsigned char *p)
{
    return ((unsigned int)p[0] << 8) | (unsigned int)p[1];
}

int avsp_tiles_open(AvspTileArchive *archive, const unsigned char *data,
                    unsigned long size)
{
    unsigned long codes_offset;
    unsigned long need;

    if (data == 0 || size < 0x30) return 0;
    if (read_u32(data) != AVSP_TILE_MAGIC) return 0;
    archive->data = data;
    archive->size = size;
    archive->tile_count = read_u32(data + 4);
    archive->palette_slots = read_u32(data + 8);
    codes_offset = read_u32(data + 12);
    if (archive->tile_count == 0 || archive->tile_count > 0x20000UL)
        return 0;
    if (archive->palette_slots == 0 || archive->palette_slots > 32) return 0;
    if (codes_offset != 0x10UL + 32UL + archive->palette_slots * 32UL)
        return 0;
    need = codes_offset + archive->tile_count * 4UL +
           archive->tile_count * (unsigned long)AVSP_TILE_BYTES;
    if (size < need) return 0;
    archive->bank_map = data + 0x10;
    archive->cram = data + 0x10 + 32;
    archive->codes = data + codes_offset;
    archive->tiles = archive->codes + archive->tile_count * 4UL;
    return 1;
}

long avsp_tiles_find(const AvspTileArchive *archive, unsigned long code)
{
    long lo = 0;
    long hi = (long)archive->tile_count - 1;
    while (lo <= hi)
    {
        long mid = lo + ((hi - lo) >> 1);
        unsigned long value = read_u32(archive->codes + mid * 4);
        if (value == code) return mid;
        if (value < code) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}

const unsigned char *avsp_tiles_texture(const AvspTileArchive *archive,
                                        long rank)
{
    if (rank < 0 || (unsigned long)rank >= archive->tile_count) return 0;
    return archive->tiles + (unsigned long)rank * AVSP_TILE_BYTES;
}

unsigned long avsp_tiles_code(const AvspTileArchive *archive, long rank)
{
    if (rank < 0 || (unsigned long)rank >= archive->tile_count) return 0;
    return read_u32(archive->codes + rank * 4);
}

int avsp_tiles_bank_slot(const AvspTileArchive *archive, int cps_bank)
{
    unsigned char slot;
    if (cps_bank < 0 || cps_bank >= 32) return -1;
    slot = archive->bank_map[cps_bank];
    if (slot == 0xFF || slot >= archive->palette_slots) return -1;
    return (int)slot;
}

unsigned int avsp_tiles_cram_color(const AvspTileArchive *archive, int slot,
                                   int index)
{
    if (slot < 0 || (unsigned long)slot >= archive->palette_slots) return 0;
    if (index < 0 || index >= 16) return 0;
    return read_u16(archive->cram + (slot * 16 + index) * 2);
}

int avsp_entry_tiles(unsigned short y, unsigned short code,
                     unsigned short attr, AvspEntryTile *out, int max_out)
{
    /* MAME 0.289 cps2_render_sprites block expansion, both flip axes. */
    unsigned long code17 =
        (unsigned long)code + (((unsigned long)y & 0x6000UL) << 3);
    int nx = ((attr >> 8) & 0xF) + 1;
    int ny = ((attr >> 12) & 0xF) + 1;
    int flip_x = (attr >> 5) & 1;
    int flip_y = (attr >> 6) & 1;
    int nxs;
    int nys;
    int count = 0;

    if (nx * ny > max_out) return -1;
    for (nys = 0; nys < ny; ++nys)
    {
        for (nxs = 0; nxs < nx; ++nxs)
        {
            unsigned long tile;
            if (flip_x || flip_y)
            {
                int sx = flip_x ? (nx - 1 - nxs) : nxs;
                int sy = flip_y ? (ny - 1 - nys) : nys;
                tile = code17 + (unsigned long)sx + 0x10UL * (unsigned long)sy;
            }
            else
            {
                tile = (code17 & ~0xFUL) +
                       ((code17 + (unsigned long)nxs) & 0xFUL) +
                       0x10UL * (unsigned long)nys;
            }
            out[count].code = tile;
            out[count].dx = (short)(nxs * 16);
            out[count].dy = (short)(nys * 16);
            out[count].flip_x = (unsigned char)flip_x;
            out[count].flip_y = (unsigned char)flip_y;
            ++count;
        }
    }
    return count;
}

long avsp_compose_entry_texture(const AvspTileArchive *archive,
                                unsigned short y, unsigned short code,
                                unsigned short attr, unsigned char *out,
                                unsigned long out_bytes)
{
    AvspEntryTile tiles[256];
    int nx = ((attr >> 8) & 0xF) + 1;
    int ny = ((attr >> 12) & 0xF) + 1;
    int width = nx * 16;
    int height = ny * 16;
    unsigned long need = (unsigned long)width *
                         (unsigned long)height / 2UL;
    int count;
    int tile;
    unsigned long clear;

    if (archive == 0 || out == 0 || out_bytes < need) return 0;
    count = avsp_entry_tiles(y, code, attr, tiles, 256);
    if (count <= 0) return 0;
    for (clear = 0; clear < need; ++clear) out[clear] = 0;
    for (tile = 0; tile < count; ++tile)
    {
        long rank = avsp_tiles_find(archive, tiles[tile].code);
        const unsigned char *source;
        int py;
        int px;
        if (rank < 0) return -1;
        source = avsp_tiles_texture(archive, rank);
        if (source == 0) return -1;
        for (py = 0; py < 16; ++py)
        {
            int source_y = tiles[tile].flip_y ? 15 - py : py;
            int dest_y = (int)tiles[tile].dy + py;
            for (px = 0; px < 16; ++px)
            {
                int source_x = tiles[tile].flip_x ? 15 - px : px;
                int dest_x = (int)tiles[tile].dx + px;
                unsigned char packed = source[source_y * 8 + source_x / 2];
                unsigned char pixel = (source_x & 1) ?
                    (unsigned char)(packed & 0x0F) :
                    (unsigned char)(packed >> 4);
                unsigned long dest = (unsigned long)dest_y *
                                     (unsigned long)(width / 2) +
                                     (unsigned long)(dest_x / 2);
                if (dest_x & 1)
                    out[dest] = (unsigned char)((out[dest] & 0xF0) | pixel);
                else
                    out[dest] = (unsigned char)((out[dest] & 0x0F) |
                                                (pixel << 4));
            }
        }
    }
    return (long)need;
}

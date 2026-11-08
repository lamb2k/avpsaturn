/* Bonus characters (SAT_GUESTS builds only; without the flag nothing here is compiled and the image is byte-identical).
   A guest takes one AvP character's slot (its ff81cc mask bit) in every mode. Each guest is one row of sat_guests[] (guests.c):
   its name, the slot bit it replaces, the bit of the BONUS CHARACTERS setting that turns it on, and its file variants (gen/guest_files.inc,
   from rounds.json "guest_files"). Guest code and data live in per-guest files under saturn/guests/<name>/.
   The switch is one place: sat_guest_sel. Today the OPTIONS row sets it; an unlock can drive the same variable later. */
#ifndef SAT_GUESTS_H
#define SAT_GUESTS_H
typedef struct {
    const char *name;            /* menu text */
    unsigned char slot_mask;     /* ff81cc bit replaced: 1 Warrior, 2 Schaefer, 4 Hunter, 8 Linn */
    unsigned char sel_bit;       /* bit of sat_guest_sel */
} SatGuest;
extern const SatGuest sat_guests[];
extern const int sat_guest_count;
extern unsigned char sat_guest_sel;          /* 0 OFF; bits per guest (row values: OFF, each guest, BOTH) */
extern const char *const sat_guest_row_names[];
extern const int sat_guest_row_n;
/* Slot bits taken by an active guest. */
int sat_guest_slots(void);
/* Stage file for a row and the characters in play: the guest's variant when a guest's slot is in play, else the arcade's choice. */
int sat_guest_file(int row, int chars, int variant, int arcade_file);
#endif

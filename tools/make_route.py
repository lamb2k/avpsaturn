#!/usr/bin/env python
"""Write the saved input route for the golden: Predator Warrior, Round 1 start, natural KO, continue, boss clear.
The schedule is the retained Round 1 route's; the coin and start pulses after frame 4200 give the continue. Output: frame word, on change.
Word bits: 1 coin, 2 start, 4 left, 8 right, 16 gun, 32 attack, 64 jump, 128 up, 256 down.
usage: make_route.py LAST > tools/routes/r1_pw_ko_boss.txt"""
import sys

def word(f):
    if f <= 4200:
        p = (f - 1200) % 180
        win = 1200 <= f <= 2400
        play = 2600 <= f < 4200
        coin, start = win and p < 3, win and 30 <= p < 33
        gun = (1500 <= f < 4200 and f % 90 < 5) or (play and f % 75 < 6)
        right, attack, jump = play, play and f % 310 < 7, play and f % 430 < 7
    else:
        r = f - 4200
        coin, start = 30 <= r % 600 < 34, 90 <= r % 600 < 94
        right, gun, attack, jump = True, r % 45 < 7, r % 180 < 8, r % 240 < 8
    return coin * 1 | start * 2 | right * 8 | gun * 16 | attack * 32 | jump * 64

last, prev = int(sys.argv[1]), None
print(f"last {last}")
for f in range(1, last + 1):
    w = word(f)
    if w != prev:
        print(f, w)
        prev = w

#!/usr/bin/env python3
import argparse,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[4]
p=argparse.ArgumentParser();p.add_argument('--negative-control',action='store_true');a=p.parse_args()
r=subprocess.run(['wsl.exe','wslpath','-a',str(R)],check=True,capture_output=True,text=True).stdout.strip();o='build/port_v2/integration/player_enemy/test'
c=f"cd '{r}' && mkdir -p build/port_v2/integration/player_enemy && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 src/port_v2/player/player.c src/port_v2/enemy/enemy.c src/port_v2/integration/player_enemy/player_enemy.c tests/port_v2/integration/player_enemy/integration_test.c -o {o} && ./{o}"+(' --negative-control' if a.negative_control else '')
subprocess.run(['wsl.exe','sh','-lc',c],check=True)

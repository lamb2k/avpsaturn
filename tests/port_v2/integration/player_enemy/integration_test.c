#include <stdio.h>
#include <string.h>
#include "../../../../src/port_v2/integration/player_enemy/player_enemy.h"
static int count, fail;
static int step(void) { ++count; return count != fail; }
static int check(int v,const char*m){if(v)return 1;fprintf(stderr,"%s\n",m);return 0;}
int main(int argc,char**argv){AvspPortV2PlayerEnemyLoadOps o;int n=argc==2&&!strcmp(argv[1],"--negative-control");o.load_tile_archive=step;o.load_background=step;o.load_player_idle=step;o.load_player_actions=step;o.create_player_sprites=step;count=0;fail=0;if(!check(avsp_port_v2_player_enemy_load(1,&o)&&count==5,"load order failed")||!check(avsp_port_v2_player_enemy_approvals_valid(),"locks failed"))return 1;if(n){count=0;fail=2;if(!check(!avsp_port_v2_player_enemy_load(1,&o)&&count==2,"failure did not stop order"))return 1;o.load_tile_archive=0;if(!check(!avsp_port_v2_player_enemy_load(1,&o),"missing dependency accepted"))return 1;}puts(n?"PlayerEnemy integration negative control: PASS":"PlayerEnemy integration contract: PASS");return 0;}

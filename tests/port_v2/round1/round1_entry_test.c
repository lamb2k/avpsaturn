#include "round1.h"

#include <stdio.h>

int main(void)
{
    AvspRound1Runtime runtime;
    avsp_round1_init(&runtime);
    if (!avsp_round1_entry_valid(&runtime))
        return 1;
    runtime.pools[0].free_stack[19] = 0u;
    if (avsp_round1_entry_valid(&runtime))
        return 2;
    puts("REIMPLEMENT-13 stable Round 1 entry: PASS");
    return 0;
}

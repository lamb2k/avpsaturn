#ifndef AVSP_SPEC02_ROUND1_ENTRY_DATA_H
#define AVSP_SPEC02_ROUND1_ENTRY_DATA_H

/* contract_sha256=3cfa5410fee3942a9bd6bb515f10aefdd293ee4cd628fb503d9685bce4c7c3f8 */
/* fixtures_sha256=24b74c91fa23c082d3ef6e7554c399d58552f7debae772e8492b422f8387b223 */
#define AVSP_ROUND1_ENTRY_PROGRAM_SHA256 "e5ef761fadc1b5a7df62e77c03025c0ebff0c2503cbc8be9c0077d4bd6cd24ba"

static const unsigned char avsp_round1_entry_program[AVSP_ROUND1_ENTRY_PROGRAM_BYTES] =
{
    0x0Au, 0x00u, 0x03u, 0xB0u, 0x01u, 0x40u, 0x06u, 0x00u, 0x18u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x3Cu, 0x00u, 0x00u, 0x00u, 0x3Cu, 0x16u, 0x02u, 0x00u, 0x00u, 0x00u, 0x2Cu, 0xFFu, 0xFFu
};

static const AvspRound1EntrySpawnSpec avsp_round1_entry_spawns[AVSP_ROUND1_FIRST_SPAWN_COUNT] =
{
    { 0xffa3c0u, 12u, 656, 312, 312, 0x1Fu, 8u, 16u, 512u, 5120u, 1u, 0x0012e8ecu, 87 },
    { 0xffa300u, 12u, 704, 296, 296, 0x1Fu, 8u, 3u, 512u, 5120u, 1u, 0x0012e8ecu, 87 },
    { 0xffa240u, 12u, 744, 280, 280, 0x1Fu, 8u, 9u, 512u, 5120u, 1u, 0x0012e8ecu, 87 },
    { 0xffa180u, 12u, 640, 320, 320, 0x1Fu, 7u, 0u, 512u, 4608u, 1u, 0x0012e8a8u, 87 },
    { 0xffa0c0u, 12u, 648, 280, 280, 0x1Fu, 7u, 0u, 512u, 4608u, 1u, 0x0012e8a8u, 87 },
    { 0xffa000u, 12u, 600, 300, 300, 0x1Fu, 7u, 0u, 512u, 4608u, 1u, 0x0012e8a8u, 87 },
    { 0xff9f40u, 12u, 696, 264, 264, 0x1Fu, 7u, 0u, 512u, 4608u, 1u, 0x0012e8a8u, 87 },
    { 0xff9e80u, 12u, 640, 256, 256, 0x1Fu, 6u, 0u, 512u, 4096u, 1u, 0x0012e8ecu, 87 },
    { 0xff9dc0u, 12u, 616, 304, 304, 0x1Fu, 6u, 0u, 512u, 4096u, 1u, 0x0012e8ecu, 87 },
    { 0xff9d00u, 12u, 632, 296, 296, 0x1Fu, 6u, 0u, 512u, 4096u, 1u, 0x0012e8ecu, 87 },
};

static const AvspRound1EntryStepSpec avsp_round1_entry_steps[AVSP_ROUND1_ENTRY_STEP_COUNT] =
{
    { AVSP_ROUND1_ENTRY_SET_POSITION, 0x0Au, 944u, 320u, 0u, 0x00128FAAUL, 0x00128FB0UL },
    { AVSP_ROUND1_ENTRY_SET_SUBHANDLER, 0x06u, 8u, 0u, 0u, 0x00128FB0UL, 0x00128FB2UL },
    { AVSP_ROUND1_ENTRY_SOURCE_18, 0x18u, 0u, 0u, 0u, 0x00128FB2UL, 0x00128FB4UL },
    { AVSP_ROUND1_ENTRY_DWELL, 0x00u, 0u, 60u, 0u, 0x00128FB4UL, 0x00128FB8UL },
    { AVSP_ROUND1_ENTRY_DWELL, 0x00u, 0u, 60u, 0u, 0x00128FB8UL, 0x00128FBCUL },
    { AVSP_ROUND1_ENTRY_SOURCE_16, 0x16u, 2u, 0u, 0u, 0x00128FBCUL, 0x00128FBEUL },
    { AVSP_ROUND1_ENTRY_DWELL, 0x00u, 0u, 44u, 0u, 0x00128FBEUL, 0x00128FC2UL },
    { AVSP_ROUND1_ENTRY_TERMINATE, 0xFFu, 0u, 0u, 0u, 0x00128FC2UL, 0x00128FC4UL },
};

#endif

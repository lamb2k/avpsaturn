#ifndef AVSP_SPEC02_ROUND1_ENTRY_DATA_H
#define AVSP_SPEC02_ROUND1_ENTRY_DATA_H

/* contract_sha256=5700f7c21d7820f0272f788b8177227de9a8047025817771efeed12cb421fe47 */
/* fixtures_sha256=589a5f597217663be9798bc8e4bd3b4a1d72a7b5a1ebb0f40c99637318cad76d */
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

static const unsigned char avsp_round1_scheduler_pool_order[AVSP_ROUND1_SCHEDULER_POOL_COUNT] =
{
    12u, 16u, 20u, 24u
};

static const AvspRound1DispatchSpec avsp_round1_required_dispatches[AVSP_ROUND1_REQUIRED_DISPATCH_COUNT] =
{
    { 12u, 0x00 },
    { 12u, 0x01 },
    { 12u, 0x06 },
    { 12u, 0x1F },
    { 16u, 0x06 },
    { 20u, 0x07 },
    { 20u, 0x08 },
    { 20u, 0x09 },
    { 20u, 0x0A },
    { 24u, 0x10 },
    { 24u, 0x3D },
    { 24u, 0x43 },
    { 24u, 0x45 },
    { 24u, 0x49 },
    { 24u, 0x4B },
    { 24u, 0x4E },
};

#define AVSP_ROUND1_CLASS1F_PRESENTATION_COUNT 190u
static const AvspRound1PresentationSpec avsp_round1_class1f_presentation[AVSP_ROUND1_CLASS1F_PRESENTATION_COUNT] =
{
    { 0x0012d380UL, 0x0012f638UL, 1u, 0u },
    { 0x0012d390UL, 0x0012f670UL, 1u, 0u },
    { 0x0012d3a0UL, 0x0012f6a8UL, 1u, 0u },
    { 0x0012d3b0UL, 0x0012f6daUL, 1u, 0u },
    { 0x0012d3c0UL, 0x0012f712UL, 1u, 0u },
    { 0x0012d3d0UL, 0x0012f72aUL, 1u, 0u },
    { 0x0012d3e0UL, 0x0012f762UL, 1u, 0u },
    { 0x0012d3f0UL, 0x0012f794UL, 1u, 0u },
    { 0x0012d404UL, 0x0012f794UL, 1u, 0u },
    { 0x0012d414UL, 0x0012f762UL, 1u, 0u },
    { 0x0012d424UL, 0x0012f72aUL, 1u, 0u },
    { 0x0012d434UL, 0x0012f712UL, 1u, 0u },
    { 0x0012d444UL, 0x0012f6daUL, 1u, 0u },
    { 0x0012d454UL, 0x0012f6a8UL, 1u, 0u },
    { 0x0012d464UL, 0x0012f670UL, 1u, 0u },
    { 0x0012d474UL, 0x0012f638UL, 1u, 0u },
    { 0x0012d488UL, 0x0012f7ccUL, 2u, 0u },
    { 0x0012d498UL, 0x0012f7e4UL, 2u, 0u },
    { 0x0012d4a8UL, 0x0012f7fcUL, 2u, 0u },
    { 0x0012d4b8UL, 0x0012f814UL, 2u, 0u },
    { 0x0012d4c8UL, 0x0012f82cUL, 2u, 0u },
    { 0x0012d4d8UL, 0x0012f85eUL, 2u, 0u },
    { 0x0012d4e8UL, 0x0012f890UL, 2u, 0u },
    { 0x0012d4f8UL, 0x0012f8b8UL, 2u, 0u },
    { 0x0012d50cUL, 0x0012f8b8UL, 2u, 0u },
    { 0x0012d51cUL, 0x0012f890UL, 2u, 0u },
    { 0x0012d52cUL, 0x0012f85eUL, 2u, 0u },
    { 0x0012d53cUL, 0x0012f82cUL, 2u, 0u },
    { 0x0012d54cUL, 0x0012f814UL, 2u, 0u },
    { 0x0012d55cUL, 0x0012f7fcUL, 2u, 0u },
    { 0x0012d56cUL, 0x0012f7e4UL, 2u, 0u },
    { 0x0012d57cUL, 0x0012f7ccUL, 2u, 0u },
    { 0x0012d590UL, 0x0012fa48UL, 1u, 0u },
    { 0x0012d5a0UL, 0x0012fa7aUL, 1u, 0u },
    { 0x0012d5b0UL, 0x0012faa2UL, 1u, 0u },
    { 0x0012d5c0UL, 0x0012fac0UL, 1u, 0u },
    { 0x0012d5d0UL, 0x0012f5acUL, 1u, 0u },
    { 0x0012d5e4UL, 0x0012fae8UL, 3u, 0u },
    { 0x0012d5f4UL, 0x0012fb10UL, 3u, 0u },
    { 0x0012d604UL, 0x0012fb38UL, 2u, 0u },
    { 0x0012d614UL, 0x0012f5deUL, 2u, 0u },
    { 0x0012d628UL, 0x0012f5deUL, 2u, 0u },
    { 0x0012d638UL, 0x0012f930UL, 4u, 0u },
    { 0x0012d648UL, 0x0012f712UL, 1u, 0u },
    { 0x0012d658UL, 0x0012fd0aUL, 1u, 0u },
    { 0x0012d668UL, 0x0012f5acUL, 1u, 0u },
    { 0x0012d678UL, 0x0012f5acUL, 1u, 0u },
    { 0x0012d890UL, 0x0012fe9eUL, 1u, 0u },
    { 0x0012d8a0UL, 0x0012febcUL, 1u, 1u },
    { 0x0012d8b0UL, 0x0012febcUL, 1u, 0u },
    { 0x0012d8c0UL, 0x0012fef4UL, 1u, 0u },
    { 0x0012d8d0UL, 0x0012ff22UL, 1u, 0u },
    { 0x0012d8e0UL, 0x0012f5acUL, 1u, 0u },
    { 0x0012d9dcUL, 0x00130120UL, 1u, 0u },
    { 0x0012d9ecUL, 0x0013013eUL, 1u, 0u },
    { 0x0012d9fcUL, 0x00130156UL, 1u, 0u },
    { 0x0012da0cUL, 0x0013016eUL, 1u, 4u },
    { 0x0012da1cUL, 0x0013016eUL, 1u, 0u },
    { 0x0012da2cUL, 0x0013018cUL, 1u, 0u },
    { 0x0012dad4UL, 0x0012ff4aUL, 1u, 0u },
    { 0x0012dae4UL, 0x0012ff9aUL, 1u, 6u },
    { 0x0012daf4UL, 0x0012ff9aUL, 1u, 0u },
    { 0x0012db04UL, 0x0012ffd8UL, 1u, 0u },
    { 0x0012db14UL, 0x0013000aUL, 1u, 0u },
    { 0x0012db24UL, 0x0012f5acUL, 1u, 0u },
    { 0x0012dd78UL, 0x0013020cUL, 14u, 0u },
    { 0x0012dd88UL, 0x00130294UL, 2u, 0u },
    { 0x0012dd9cUL, 0x00130294UL, 0u, 0u },
    { 0x0012ddb0UL, 0x00130346UL, 7u, 0u },
    { 0x0012de38UL, 0x00130346UL, 0u, 0u },
    { 0x0012de48UL, 0x00130354UL, 0u, 0u },
    { 0x0012de58UL, 0x00130346UL, 0u, 0u },
    { 0x0012de68UL, 0x00130354UL, 0u, 0u },
    { 0x0012de78UL, 0x00130362UL, 0u, 0u },
    { 0x0012de88UL, 0x00130370UL, 0u, 0u },
    { 0x0012de98UL, 0x001303a8UL, 0u, 0u },
    { 0x0012dea8UL, 0x0012fae8UL, 0u, 0u },
    { 0x0012deb8UL, 0x0012fb10UL, 0u, 0u },
    { 0x0012dec8UL, 0x0012fb38UL, 0u, 0u },
    { 0x0012ded8UL, 0x0012f5deUL, 0u, 0u },
    { 0x0012e04cUL, 0x001308a6UL, 0u, 0u },
    { 0x0012e05cUL, 0x0013088eUL, 0u, 0u },
    { 0x0012e06cUL, 0x001308c4UL, 0u, 0u },
    { 0x0012e07cUL, 0x0013088eUL, 0u, 0u },
    { 0x0012e08cUL, 0x001308e2UL, 0u, 0u },
    { 0x0012e09cUL, 0x0013088eUL, 0u, 0u },
    { 0x0012e214UL, 0x0013020cUL, 14u, 0u },
    { 0x0012e224UL, 0x0013020cUL, 14u, 0u },
    { 0x0012e234UL, 0x0013020cUL, 14u, 0u },
    { 0x0012e244UL, 0x0013020cUL, 14u, 0u },
    { 0x0012e254UL, 0x00130294UL, 0u, 0u },
    { 0x0012e268UL, 0x00130346UL, 0u, 0u },
    { 0x0012e38cUL, 0x0013065eUL, 0u, 0u },
    { 0x0012e39cUL, 0x0013067cUL, 0u, 0u },
    { 0x0012e3acUL, 0x0013069aUL, 0u, 0u },
    { 0x0012e3bcUL, 0x001306b8UL, 0u, 0u },
    { 0x0012e3ccUL, 0x001306d6UL, 0u, 0u },
    { 0x0012e3dcUL, 0x001306f4UL, 0u, 0u },
    { 0x0012e3ecUL, 0x00130712UL, 0u, 0u },
    { 0x0012e3fcUL, 0x00130730UL, 0u, 0u },
    { 0x0012e410UL, 0x0013074eUL, 0u, 0u },
    { 0x0012e420UL, 0x0013076cUL, 0u, 0u },
    { 0x0012e430UL, 0x0013078aUL, 0u, 0u },
    { 0x0012e440UL, 0x001307a8UL, 0u, 0u },
    { 0x0012e450UL, 0x001307c6UL, 0u, 0u },
    { 0x0012e460UL, 0x001307e4UL, 0u, 0u },
    { 0x0012e470UL, 0x00130802UL, 0u, 0u },
    { 0x0012e480UL, 0x00130820UL, 0u, 0u },
    { 0x0012e490UL, 0x0013083eUL, 0u, 0u },
    { 0x0012e4a0UL, 0x00130866UL, 0u, 0u },
    { 0x0012e550UL, 0x0012f930UL, 4u, 0u },
    { 0x0012e560UL, 0x00130928UL, 5u, 0u },
    { 0x0012e570UL, 0x00130046UL, 1u, 0u },
    { 0x0012e580UL, 0x00130946UL, 8u, 0u },
    { 0x0012e590UL, 0x00130946UL, 8u, 0u },
    { 0x0012e5a0UL, 0x00130946UL, 8u, 0u },
    { 0x0012e5b0UL, 0x00130946UL, 8u, 0u },
    { 0x0012e5c0UL, 0x00130946UL, 8u, 0u },
    { 0x0012e5d0UL, 0x00130946UL, 8u, 0u },
    { 0x0012e5e0UL, 0x001300eeUL, 1u, 0u },
    { 0x0012e5f0UL, 0x0012f5acUL, 1u, 0u },
    { 0x0012e604UL, 0x0012f930UL, 4u, 0u },
    { 0x0012e614UL, 0x0012fce2UL, 10u, 0u },
    { 0x0012e624UL, 0x0012fce2UL, 10u, 0u },
    { 0x0012e638UL, 0x0012fbfcUL, 10u, 0u },
    { 0x0012e648UL, 0x0012fc74UL, 10u, 0u },
    { 0x0012e65cUL, 0x0012f712UL, 1u, 0u },
    { 0x0012e66cUL, 0x0012f930UL, 4u, 0u },
    { 0x0012e67cUL, 0x0012f5deUL, 2u, 0u },
    { 0x0012e68cUL, 0x0012f5deUL, 2u, 0u },
    { 0x0012e708UL, 0x0012f638UL, 1u, 0u },
    { 0x0012e718UL, 0x0012f670UL, 1u, 0u },
    { 0x0012e728UL, 0x0012f6a8UL, 1u, 0u },
    { 0x0012e738UL, 0x0012f6daUL, 1u, 0u },
    { 0x0012e748UL, 0x0012f712UL, 1u, 0u },
    { 0x0012e758UL, 0x0012f72aUL, 1u, 0u },
    { 0x0012e768UL, 0x0012f762UL, 1u, 0u },
    { 0x0012e778UL, 0x0012f794UL, 1u, 0u },
    { 0x0012e78cUL, 0x0012f7ccUL, 2u, 0u },
    { 0x0012e79cUL, 0x0012f7e4UL, 2u, 0u },
    { 0x0012e7acUL, 0x0012f7fcUL, 2u, 0u },
    { 0x0012e7bcUL, 0x0012f814UL, 2u, 0u },
    { 0x0012e7ccUL, 0x0012f82cUL, 2u, 0u },
    { 0x0012e7dcUL, 0x0012f85eUL, 2u, 0u },
    { 0x0012e7ecUL, 0x0012f890UL, 2u, 0u },
    { 0x0012e7fcUL, 0x0012f8b8UL, 2u, 0u },
    { 0x0012e8a8UL, 0x0012f994UL, 1u, 0u },
    { 0x0012e8b8UL, 0x0012f9bcUL, 1u, 0u },
    { 0x0012e8c8UL, 0x0012f9e4UL, 1u, 0u },
    { 0x0012e8d8UL, 0x0012f9bcUL, 1u, 0u },
    { 0x0012e8ecUL, 0x0012f5deUL, 2u, 0u },
    { 0x0012e8fcUL, 0x0012fa0cUL, 2u, 0u },
    { 0x0012e90cUL, 0x0012fa2aUL, 2u, 0u },
    { 0x0012e91cUL, 0x0012fa0cUL, 2u, 0u },
    { 0x0012e944UL, 0x0012f5deUL, 2u, 0u },
    { 0x0012e954UL, 0x0012fce2UL, 10u, 0u },
    { 0x0012e964UL, 0x0012fce2UL, 10u, 0u },
    { 0x0012e9ccUL, 0x0012fc92UL, 11u, 0u },
    { 0x0012e9dcUL, 0x0012f5fcUL, 2u, 0u },
    { 0x0012e9f0UL, 0x0012fc74UL, 0u, 0u },
    { 0x0012ea00UL, 0x0012fc24UL, 0u, 0u },
    { 0x0012ea10UL, 0x0012fb98UL, 0u, 0u },
    { 0x0012ea24UL, 0x0012fb60UL, 0u, 0u },
    { 0x0012ea34UL, 0x0012fbfcUL, 0u, 0u },
    { 0x0012ea44UL, 0x0012fc74UL, 0u, 0u },
    { 0x0012ea54UL, 0x0012fc24UL, 0u, 0u },
    { 0x0012ea64UL, 0x0012fb98UL, 0u, 0u },
    { 0x0012eafcUL, 0x0012f638UL, 1u, 0u },
    { 0x0012eb0cUL, 0x0012f670UL, 1u, 0u },
    { 0x0012eb1cUL, 0x0012f6a8UL, 1u, 0u },
    { 0x0012eb2cUL, 0x0012f6daUL, 1u, 0u },
    { 0x0012eb3cUL, 0x0012f712UL, 1u, 0u },
    { 0x0012eb4cUL, 0x0012f72aUL, 1u, 0u },
    { 0x0012eb5cUL, 0x0012f762UL, 1u, 0u },
    { 0x0012eb6cUL, 0x0012f794UL, 1u, 0u },
    { 0x0012ec04UL, 0x0012f7ccUL, 2u, 0u },
    { 0x0012ec14UL, 0x0012f7e4UL, 2u, 0u },
    { 0x0012ec24UL, 0x0012f7fcUL, 2u, 0u },
    { 0x0012ec34UL, 0x0012f814UL, 2u, 0u },
    { 0x0012ec44UL, 0x0012f82cUL, 2u, 0u },
    { 0x0012ec54UL, 0x0012f85eUL, 2u, 0u },
    { 0x0012ec64UL, 0x0012f890UL, 2u, 0u },
    { 0x0012ec74UL, 0x0012f8b8UL, 2u, 0u },
    { 0x0012ee98UL, 0x0012f7ccUL, 2u, 0u },
    { 0x0012eea8UL, 0x0012f7e4UL, 2u, 0u },
    { 0x0012eeb8UL, 0x0012f7fcUL, 2u, 0u },
    { 0x0012eec8UL, 0x0012f814UL, 2u, 0u },
    { 0x0012eed8UL, 0x0012f82cUL, 2u, 0u },
    { 0x0012eee8UL, 0x0012f85eUL, 2u, 0u },
    { 0x0012eef8UL, 0x0012f890UL, 2u, 0u },
};

#define AVSP_ROUND1_CLASS1F_DISPATCH_ENTRY 0x060532UL
#define AVSP_ROUND1_CLASS1F_STATE_CONTEXT_COUNT 59u
static const AvspRound1StateContextSpec avsp_round1_class1f_state_contexts[AVSP_ROUND1_CLASS1F_STATE_CONTEXT_COUNT] =
{
    { 0x0000u, 0x0000u },
    { 0x0200u, 0x0000u },
    { 0x0200u, 0x0200u },
    { 0x0200u, 0x0400u },
    { 0x0200u, 0x0402u },
    { 0x0200u, 0x0404u },
    { 0x0200u, 0x0408u },
    { 0x0200u, 0x0600u },
    { 0x0200u, 0x0800u },
    { 0x0200u, 0x0A00u },
    { 0x0200u, 0x0C00u },
    { 0x0200u, 0x0C02u },
    { 0x0200u, 0x0C04u },
    { 0x0200u, 0x0E00u },
    { 0x0200u, 0x0E02u },
    { 0x0200u, 0x0E04u },
    { 0x0200u, 0x1000u },
    { 0x0200u, 0x1200u },
    { 0x0200u, 0x1400u },
    { 0x0200u, 0x1402u },
    { 0x0200u, 0x1404u },
    { 0x0200u, 0x1406u },
    { 0x0200u, 0x1408u },
    { 0x0200u, 0x1600u },
    { 0x0200u, 0x1800u },
    { 0x0200u, 0x1A00u },
    { 0x0200u, 0x1E00u },
    { 0x0202u, 0x0000u },
    { 0x0202u, 0x0002u },
    { 0x0202u, 0x0200u },
    { 0x0202u, 0x0202u },
    { 0x0202u, 0x0204u },
    { 0x0202u, 0x0206u },
    { 0x0202u, 0x0208u },
    { 0x0202u, 0x020Au },
    { 0x0208u, 0x0000u },
    { 0x0208u, 0x0200u },
    { 0x0208u, 0x0400u },
    { 0x0208u, 0x0600u },
    { 0x0208u, 0x0800u },
    { 0x0208u, 0x0802u },
    { 0x0208u, 0x0A00u },
    { 0x0208u, 0x0C00u },
    { 0x0208u, 0x0C02u },
    { 0x0208u, 0x0C04u },
    { 0x0208u, 0x0C06u },
    { 0x0208u, 0x0E00u },
    { 0x0208u, 0x0E02u },
    { 0x0208u, 0x1000u },
    { 0x0208u, 0x1006u },
    { 0x020Au, 0x0000u },
    { 0x020Au, 0x0200u },
    { 0x0400u, 0x0000u },
    { 0x0402u, 0x0000u },
    { 0x0402u, 0x0200u },
    { 0x0402u, 0x0400u },
    { 0x0402u, 0x0600u },
    { 0x0404u, 0x0000u },
    { 0x0600u, 0x0000u },
};

static const AvspRound1NavigationBoundsSpec avsp_round1_first_segment_bounds =
{
    720, 256, 752, 1072,
    272, 400
};

static const AvspRound1PlayerLocomotionSpec avsp_round1_player_locomotion =
{
    514u,
    516u,
    512u,
    10u,
    {255u, 2u, 6u, 255u, 4u, 3u, 5u, 255u, 0u, 1u, 7u, 255u, 255u, 255u, 255u, 255u}
};

static const AvspRound1PlayerMeleeSpec avsp_round1_player_melee =
{
    1536u,
    5120u,
    30u,
    4u,
    {1u, 2u, 3u, 4u},
    {0u, 1u, 2u, 3u}
};

static const AvspRound1PresentationSpec avsp_round1_player_melee_strikes[AVSP_ROUND1_PLAYER_MELEE_COUNT] =
{
    { 0x1600f8UL, 0x162a04UL, 8u, 1u },
    { 0x16014cUL, 0x162a82UL, 8u, 2u },
    { 0x1601c0UL, 0x1614a4UL, 8u, 3u },
    { 0x160234UL, 0x162b26UL, 19u, 4u },
};

static const AvspRound1PlayerWeaponSpec avsp_round1_player_weapon =
{
    3072u,
    3074u,
    6656u,
    6658u,
    0u,
    2u,
    12,
    1u,
    4u,
    16u,
    64u,
    3u,
    12u,
    2u,
    6u,
    0x05,
    0x8680u,
    0x0080u,
    0x8380u,
    0x03136aUL
};

static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_frames[AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT] =
{
    { 3072u, 0u, 0x001642f4UL, 0x00165694UL, 0u, 0u },
    { 3074u, 2u, 0x00165400UL, 0x00166bf8UL, 1u, 0u },
    { 3074u, 2u, 0x00165410UL, 0x00166c22UL, 1u, 0u },
    { 3074u, 2u, 0x00165410UL, 0x00166c22UL, 1u, 0u },
    { 3074u, 2u, 0x00165420UL, 0x00166c4cUL, 1u, 0u },
    { 3074u, 2u, 0x00165400UL, 0x00166bf8UL, 1u, 0u },
    { 3074u, 2u, 0x00165410UL, 0x00166c22UL, 1u, 0u },
    { 3074u, 2u, 0x00165410UL, 0x00166c22UL, 1u, 0u },
    { 3074u, 2u, 0x00165420UL, 0x00166c4cUL, 1u, 0u },
    { 3074u, 2u, 0x00165444UL, 0x00166c76UL, 1u, 0u },
    { 3074u, 2u, 0x00165454UL, 0x00166c9aUL, 1u, 0u },
    { 3074u, 2u, 0x00165454UL, 0x00166c9aUL, 1u, 0u },
    { 3074u, 2u, 0x00165464UL, 0x00166cbeUL, 1u, 0u },
    { 3074u, 2u, 0x00165444UL, 0x00166c76UL, 1u, 0u },
    { 3074u, 2u, 0x00165454UL, 0x00166c9aUL, 1u, 0u },
    { 3074u, 2u, 0x00165454UL, 0x00166c9aUL, 1u, 0u },
    { 3074u, 2u, 0x00165464UL, 0x00166cbeUL, 1u, 0u },
    { 3074u, 2u, 0x00165048UL, 0x001666beUL, 1u, 0u },
    { 3074u, 2u, 0x00165058UL, 0x001666dcUL, 1u, 0u },
    { 3074u, 2u, 0x00165058UL, 0x001666dcUL, 1u, 0u },
    { 3074u, 2u, 0x00165068UL, 0x001666faUL, 1u, 0u },
    { 3074u, 2u, 0x0016508cUL, 0x00166718UL, 1u, 0u },
    { 3074u, 2u, 0x0016509cUL, 0x00166736UL, 1u, 0u },
    { 3074u, 2u, 0x0016509cUL, 0x00166736UL, 1u, 0u },
    { 3074u, 2u, 0x001650acUL, 0x00166754UL, 1u, 0u },
    { 3074u, 2u, 0x0016508cUL, 0x00166718UL, 1u, 0u },
    { 3074u, 2u, 0x0016509cUL, 0x00166736UL, 1u, 0u },
    { 3074u, 2u, 0x0016509cUL, 0x00166736UL, 1u, 0u },
    { 3074u, 2u, 0x001650acUL, 0x00166754UL, 1u, 0u },
    { 3074u, 2u, 0x00165048UL, 0x001666beUL, 1u, 0u },
    { 3074u, 2u, 0x00165058UL, 0x001666dcUL, 1u, 0u },
    { 3074u, 2u, 0x00165058UL, 0x001666dcUL, 1u, 0u },
    { 3074u, 2u, 0x00165068UL, 0x001666faUL, 1u, 0u },
    { 3074u, 2u, 0x00165444UL, 0x00166c76UL, 1u, 0u },
    { 3074u, 2u, 0x00165454UL, 0x00166c9aUL, 1u, 0u },
    { 3074u, 2u, 0x00165454UL, 0x00166c9aUL, 1u, 0u },
    { 3074u, 2u, 0x00165464UL, 0x00166cbeUL, 1u, 0u },
    { 3074u, 2u, 0x00165444UL, 0x00166c76UL, 1u, 0u },
    { 3074u, 2u, 0x00165454UL, 0x00166c9aUL, 1u, 0u },
    { 3074u, 2u, 0x00165454UL, 0x00166c9aUL, 1u, 0u },
    { 3074u, 2u, 0x00165464UL, 0x00166cbeUL, 1u, 0u },
    { 3074u, 2u, 0x00165400UL, 0x00166bf8UL, 1u, 0u },
    { 3074u, 2u, 0x00165410UL, 0x00166c22UL, 1u, 0u },
    { 3074u, 2u, 0x00165410UL, 0x00166c22UL, 1u, 0u },
    { 3074u, 2u, 0x00165420UL, 0x00166c4cUL, 1u, 0u },
    { 3074u, 2u, 0x00165400UL, 0x00166bf8UL, 1u, 0u },
    { 3074u, 2u, 0x00165410UL, 0x00166c22UL, 1u, 0u },
    { 3074u, 2u, 0x00165410UL, 0x00166c22UL, 1u, 0u },
    { 3074u, 2u, 0x00165420UL, 0x00166c4cUL, 1u, 0u },
    { 0u, 0u, 0x00163158UL, 0x00165488UL, 1u, 0u },
};

static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_empty_frames[AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT] =
{
    { 6656u, 0u, 0x001642f4UL, 0x00165694UL, 0u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },
    { 0u, 0u, 0x00163158UL, 0x00165488UL, 1u, 0u },
};

static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_return_frame =
{
    2u, 2u, 0x00163158UL, 0x00165488UL, 1u, 0u
};

static const AvspRound1VecS16 avsp_round1_weapon_projectile_spawn_offsets[AVSP_ROUND1_WEAPON_PROJECTILE_PRESENTATION_COUNT] =
{
    { -21, 84 },
    { 22, 79 },
    { 36, 68 },
    { 43, 55 },
    { 43, 38 },
    { 32, 26 },
    { 16, 16 },
    { -10, 12 },
    { -24, 11 },
    { -46, 14 },
    { -54, 17 },
    { -66, 25 },
    { -75, 37 },
    { -76, 51 },
    { -70, 64 },
    { -47, 79 },
};

static const unsigned char avsp_round1_weapon_projectile_animation_selectors[AVSP_ROUND1_WEAPON_PROJECTILE_PRESENTATION_COUNT] =
{
    15u, 14u, 13u, 12u, 11u, 10u, 9u, 8u, 7u, 6u, 5u, 4u, 3u, 2u, 1u, 0u
};

static const unsigned char avsp_round1_weapon_projectile_angles_facing0[AVSP_ROUND1_WEAPON_PROJECTILE_ANGLE_COUNT] =
{
    40u, 42u, 44u, 46u, 48u, 50u, 49u, 47u, 45u, 43u, 41u, 40u
};

static const unsigned char avsp_round1_weapon_projectile_angles_facing1[AVSP_ROUND1_WEAPON_PROJECTILE_ANGLE_COUNT] =
{
    24u, 22u, 20u, 18u, 16u, 14u, 15u, 17u, 19u, 21u, 23u, 24u
};

static const unsigned char avsp_round1_weapon_projectile_player_selectors[AVSP_ROUND1_WEAPON_PROJECTILE_ANGLE_COUNT] =
{
    6u, 6u, 5u, 5u, 4u, 3u, 3u, 4u, 5u, 5u, 6u, 6u
};

static const AvspRound1VecS16 avsp_round1_weapon_projectile_motion[AVSP_ROUND1_WEAPON_PROJECTILE_MOTION_COUNT] =
{
    { 0, 3510 },
    { 300, 3492 },
    { 598, 3440 },
    { 890, 3355 },
    { 1173, 3240 },
    { 1446, 3092 },
    { 1704, 2916 },
    { 1947, 2713 },
    { 2171, 2481 },
    { 2374, 2225 },
    { 2552, 1948 },
    { 2706, 1653 },
    { 2835, 1340 },
    { 2936, 1017 },
    { 3010, 684 },
    { 3056, 343 },
    { 3072, 0 },
    { 3056, -343 },
    { 3010, -684 },
    { 2936, -1017 },
    { 2835, -1340 },
    { 2706, -1653 },
    { 2552, -1948 },
    { 2374, -2225 },
    { 2171, -2481 },
    { 1947, -2713 },
    { 1704, -2916 },
    { 1446, -3092 },
    { 1173, -3240 },
    { 890, -3355 },
    { 598, -3440 },
    { 300, -3492 },
    { 0, -3510 },
    { -300, -3492 },
    { -598, -3440 },
    { -890, -3355 },
    { -1173, -3240 },
    { -1446, -3092 },
    { -1704, -2916 },
    { -1947, -2713 },
    { -2171, -2481 },
    { -2374, -2225 },
    { -2552, -1948 },
    { -2706, -1653 },
    { -2835, -1340 },
    { -2936, -1017 },
    { -3010, -684 },
    { -3056, -343 },
    { -3072, 0 },
    { -3056, 343 },
    { -3010, 684 },
    { -2936, 1017 },
    { -2835, 1340 },
    { -2706, 1653 },
    { -2552, 1948 },
    { -2374, 2225 },
    { -2171, 2481 },
    { -1947, 2713 },
    { -1704, 2916 },
    { -1446, 3092 },
    { -1173, 3240 },
    { -890, 3355 },
    { -598, 3440 },
    { -300, 3492 },
};

static const AvspRound1AnimationStateSpec avsp_round1_weapon_projectile_presentations[AVSP_ROUND1_WEAPON_PROJECTILE_PRESENTATION_COUNT][2] =
{
    { { 8u, 0, 0x00030f6aUL, 0x000311aaUL, 0u, 1u }, { 8u, -32768, 0x00030f7aUL, 0x0003128aUL, 0u, 1u } },
    { { 8u, 0, 0x00030f8eUL, 0x000311b8UL, 0u, 1u }, { 8u, -32768, 0x00030f9eUL, 0x00031298UL, 0u, 1u } },
    { { 8u, 0, 0x00030fb2UL, 0x000311c6UL, 0u, 1u }, { 8u, -32768, 0x00030fc2UL, 0x000312a6UL, 0u, 1u } },
    { { 8u, 0, 0x00030fd6UL, 0x000311d4UL, 0u, 1u }, { 8u, -32768, 0x00030fe6UL, 0x000312b4UL, 0u, 1u } },
    { { 8u, 0, 0x00030ffaUL, 0x000311e2UL, 0u, 1u }, { 8u, -32768, 0x0003100aUL, 0x000312c2UL, 0u, 1u } },
    { { 8u, 0, 0x0003101eUL, 0x000311f0UL, 0u, 1u }, { 2u, -32768, 0x0003102eUL, 0x000312d0UL, 0u, 1u } },
    { { 8u, 0, 0x00031042UL, 0x000311feUL, 0u, 1u }, { 8u, -32768, 0x00031052UL, 0x000312deUL, 0u, 1u } },
    { { 8u, 0, 0x00031066UL, 0x0003120cUL, 0u, 1u }, { 8u, -32768, 0x00031076UL, 0x000312ecUL, 0u, 1u } },
    { { 8u, 0, 0x0003108aUL, 0x0003121aUL, 0u, 1u }, { 8u, -32768, 0x0003109aUL, 0x000312faUL, 0u, 1u } },
    { { 8u, 0, 0x000310aeUL, 0x00031228UL, 0u, 2u }, { 8u, -32768, 0x000310beUL, 0x00031308UL, 0u, 2u } },
    { { 8u, 0, 0x000310d2UL, 0x00031236UL, 0u, 2u }, { 8u, -32768, 0x000310e2UL, 0x00031316UL, 0u, 2u } },
    { { 8u, 0, 0x000310f6UL, 0x00031244UL, 0u, 2u }, { 8u, -32768, 0x00031106UL, 0x00031324UL, 0u, 2u } },
    { { 8u, 0, 0x0003111aUL, 0x00031252UL, 0u, 2u }, { 8u, -32768, 0x0003112aUL, 0x00031332UL, 0u, 2u } },
    { { 8u, 0, 0x0003113eUL, 0x00031260UL, 0u, 2u }, { 8u, -32768, 0x0003114eUL, 0x00031340UL, 0u, 2u } },
    { { 8u, 0, 0x00031162UL, 0x0003126eUL, 0u, 2u }, { 8u, -32768, 0x00031172UL, 0x0003134eUL, 0u, 2u } },
    { { 8u, 0, 0x00031186UL, 0x0003127cUL, 0u, 2u }, { 8u, -32768, 0x00031196UL, 0x0003135cUL, 0u, 2u } },
};

static const AvspRound1WeaponProjectileSpec avsp_round1_weapon_projectile =
{
    0u, 2u, 4u, 6u, 0x80u,
    0x50, 0x0220u, 0x10, 0x0120u, 0x3a, 0u,
    0u, 0u, 0x8000u
};

static const AvspRound1CollisionBoxSpec avsp_round1_weapon_projectile_hurt_box =
{
    0, 0, 0u, 0u, 0, 0u, 0, 0u, 0u
};

static const AvspRound1CollisionBoxSpec avsp_round1_weapon_projectile_attack_boxes[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =
{
    { 0, 0, 0u, 0u, 0, 0u, 0, 0u, 0u },
    { 16, 0, 18u, 5u, 0, 8u, -1, 0u, 6u },
    { 16, 0, 18u, 5u, 0, 8u, 0, 0u, 6u },
};

static const AvspRound1DamageClassValueSpec avsp_round1_weapon_damage_offense[AVSP_ROUND1_WEAPON_DAMAGE_OFFENSE_COUNT] =
{
    { 0u, 10u, 0u },
    { 2u, 10u, 4u }
};

static const AvspRound1DamageClassValueSpec avsp_round1_weapon_damage_defense[AVSP_ROUND1_WEAPON_DAMAGE_DEFENSE_COUNT] =
{
    { 16u, 10u, 33u }
};

static const AvspRound1DamageMatrixValueSpec avsp_round1_weapon_damage_matrix[AVSP_ROUND1_WEAPON_DAMAGE_MATRIX_COUNT] =
{
    { 33u, 6u, 24u },
    { 33u, 10u, 31u }
};

static const AvspRound1WeaponImpactSpec avsp_round1_weapon_impact =
{
    24u, 0x3a, 0u, 0u, 2u, 4u, 0x086f62UL,
    0u, 0u, 0x8000u,
    { 0x007eu, 0x0148u }
};

static const short avsp_round1_weapon_impact_variant_offsets[AVSP_ROUND1_WEAPON_IMPACT_VARIANT_COUNT] =
{
    12, 96, 196, 248, 348
};

static const AvspRound1AnimationStateSpec avsp_round1_weapon_impact_variant0_records[AVSP_ROUND1_WEAPON_IMPACT_PRESENTATION_COUNT] =
{
    { 2u, 0, 0x00086fdcUL, 0x00087180UL, 0u, 0u },
    { 2u, 0, 0x00086fecUL, 0x0008718eUL, 0u, 0u },
    { 2u, 0, 0x00086ffcUL, 0x0008719cUL, 0u, 0u },
    { 2u, 0, 0x0008700cUL, 0x000871aaUL, 0u, 0u },
    { 2u, -32768, 0x0008701cUL, 0x000871aaUL, 0u, 0u },
};

static const AvspRound1VecS16 avsp_round1_empty_effect_variant_offsets[AVSP_ROUND1_EMPTY_EFFECT_VARIANT_COUNT] =
{
    { 0, 84 },
    { 0, 78 },
    { 0, 84 },
    { 0, 68 },
};

static const AvspRound1AnimationStateSpec avsp_round1_empty_effect_variant1_records[AVSP_ROUND1_EMPTY_EFFECT_PRESENTATION_COUNT] =
{
    { 1u, 0, 0x0007a09cUL, 0x0007a140UL, 0u, 0u },
    { 1u, 0, 0x0007a0acUL, 0x0007a18cUL, 0u, 0u },
    { 1u, 0, 0x0007a0bcUL, 0x0007a1d8UL, 0u, 0u },
    { 1u, 0, 0x0007a0ccUL, 0x0007a224UL, 0u, 0u },
    { 1u, 0, 0x0007a0dcUL, 0x0007a270UL, 0u, 0u },
    { 1u, 0, 0x0007a0ecUL, 0x0007a2bcUL, 0u, 0u },
    { 1u, 0, 0x0007a0fcUL, 0x0007a308UL, 0u, 0u },
    { 1u, 0, 0x0007a10cUL, 0x0007a354UL, 0u, 0u },
    { 8u, 1, 0x0007a11cUL, 0x0007a3a0UL, 0u, 0u },
    { 4095u, -32767, 0x0007a12cUL, 0x0007a3a0UL, 0u, 0u },
};

#endif

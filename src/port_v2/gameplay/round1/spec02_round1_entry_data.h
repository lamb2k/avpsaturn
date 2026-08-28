#ifndef AVSP_SPEC02_ROUND1_ENTRY_DATA_H
#define AVSP_SPEC02_ROUND1_ENTRY_DATA_H

/* contract_sha256=b1613ab1bbd777abbcbeae7c5521463171c5cc1ad4b12367248a436acbb563af */
/* fixtures_sha256=45c2f8c90b2388f3990b32d9ce93552185138bc6396d26cd532caa117b60a388 */
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

#define AVSP_ROUND1_CLASS1F_PRESENTATION_COUNT 192u
static const AvspRound1PresentationSpec avsp_round1_class1f_presentation[AVSP_ROUND1_CLASS1F_PRESENTATION_COUNT] =
{
    { 0x0012d2f8UL, 0x0012f994UL, 1u, 0u },
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
    { 0x0012dd50UL, 0x00130248UL, 1u, 0u },
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
#define AVSP_ROUND1_CLASS1F_STATE_CONTEXT_COUNT 61u
static const AvspRound1StateContextSpec avsp_round1_class1f_state_contexts[AVSP_ROUND1_CLASS1F_STATE_CONTEXT_COUNT] =
{
    { 0x0000u, 0x0000u },
    { 0x0200u, 0x0000u },
    { 0x0200u, 0x0200u },
    { 0x0200u, 0x0400u },
    { 0x0200u, 0x0402u },
    { 0x0200u, 0x0404u },
    { 0x0200u, 0x0406u },
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
    { 0x0200u, 0x1C00u },
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

static const AvspRound1Class1fCurrentSpec avsp_round1_class1f_current =
{
    0x00ffb580UL, 0xffa000UL, 20u, 0x01, 960, 343, 343, 87, 111, -23, 38u, 120u, 48u, 119u, 8u, 39u, 141u,
    { 8u, 8u, 10u, 12u },
};

static const AvspRound1RecurringSpawnSpec avsp_round1_recurring_spawn =
{
    0x0200u, 0x0202u, 0x0204u,
    3900u, 60u, 1200u, 2100u, 640u, 208u, 720, 9u,
    { 0u, 35u, 55u, 70u },
    0xA2u, 8u, 7u, 3u, 31u,
    -48, 1008, 976, 344, 344, 4u, 0u,
    1u, 0u, 0xC580u, 0x44, 24u, 0x0404u
};

static const short avsp_round1_recurring_lane_offsets[AVSP_ROUND1_RECURRING_LANE_OFFSET_COUNT] =
{
    24, 40, 56, 72, 88, 104
};

static const unsigned char avsp_round1_recurring_selector_cycle[AVSP_ROUND1_RECURRING_SELECTOR_COUNT] =
{
    0u, 1u, 1u, 1u, 0u, 1u, 0u, 1u, 1u, 1u
};

static const unsigned char avsp_round1_recurring_lane_buckets[AVSP_ROUND1_RECURRING_LANE_BUCKET_COUNT] =
{
    0u, 0u, 0u, 0u, 1u, 1u, 1u, 1u, 2u, 2u, 2u, 2u, 3u, 3u, 3u, 3u,
    0u, 0u, 0u, 1u, 1u, 1u, 2u, 2u, 2u, 2u, 3u, 3u, 3u, 4u, 4u, 4u,
    0u, 0u, 1u, 1u, 1u, 2u, 2u, 2u, 3u, 3u, 3u, 4u, 4u, 4u, 5u, 5u,
    3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u
};

static const unsigned char avsp_round1_recurring_variants[AVSP_ROUND1_RECURRING_VARIANT_COUNT] =
{
    3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u,
    3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u,
    3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u,
    3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u,
    3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u,
    3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u
};

static const unsigned long avsp_round1_class1f_approach_records[AVSP_ROUND1_CLASS1F_APPROACH_RECORD_COUNT] =
{
    0x12ec04UL, 0x12ec14UL, 0x12ec24UL, 0x12ec34UL, 0x12ec44UL, 0x12ec54UL, 0x12ec64UL, 0x12ec74UL
};

static const unsigned long avsp_round1_class1f_attack_records[AVSP_ROUND1_CLASS1F_ATTACK_RECORD_COUNT] =
{
    0x12e8ecUL, 0x12e8fcUL, 0x12e90cUL, 0x12e91cUL
};

static const AvspRound1Class1fActionTargetSpec avsp_round1_class1f_action_targets[AVSP_ROUND1_CLASS1F_ACTION_TARGET_COUNT] =
{
    { 0u, 0x0607b8UL },
    { 2u, 0x06084eUL },
    { 4u, 0x0608b0UL },
    { 6u, 0x0609f6UL },
    { 8u, 0x060a08UL },
    { 10u, 0x060a1cUL },
    { 12u, 0x060a2aUL },
    { 14u, 0x060a86UL },
    { 16u, 0x060b1aUL },
    { 18u, 0x060b28UL },
    { 20u, 0x060b36UL },
    { 22u, 0x060c2eUL },
    { 24u, 0x060d6aUL },
    { 26u, 0x060d7eUL },
    { 28u, 0x060d88UL },
    { 30u, 0x060de0UL },
};

static const AvspRound1Class1fActionVariantSpec avsp_round1_class1f_action_variants[AVSP_ROUND1_CLASS1F_ACTION_VARIANT_COUNT] =
{
    { 0u, 2u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0x00u, 0x0000u },
    { 1u, 2u, 0u, 0u, 12u, 0u, 0u, 0u, 0u, 0x01u, 0x0000u },
    { 2u, 2u, 0u, 0u, 14u, 1u, 0u, 0u, 0u, 0x03u, 0x0000u },
    { 3u, 1u, 1u, 1u, 0u, 0u, 1u, 0u, 0u, 0x04u, 0x0000u },
    { 4u, 1u, 1u, 1u, 12u, 0u, 0u, 0u, 0u, 0x01u, 0x0000u },
    { 5u, 1u, 1u, 1u, 14u, 1u, 0u, 0u, 0u, 0x03u, 0x0000u },
    { 6u, 1u, 1u, 1u, 16u, 0u, 1u, 1u, 216u, 0x1Du, 0x0000u },
    { 7u, 1u, 1u, 1u, 18u, 0u, 0u, 0u, 216u, 0x1Du, 0x0000u },
    { 8u, 1u, 1u, 1u, 20u, 0u, 1u, 1u, 0u, 0x2Du, 0x0000u },
    { 9u, 1u, 1u, 1u, 28u, 0u, 0u, 0u, 0u, 0xC5u, 0x0420u },
};

static const AvspRound1Class1fActionSelectorSpec avsp_round1_class1f_action_selectors[AVSP_ROUND1_CLASS1F_ACTION_SELECTOR_COUNT] =
{
    { 0u, 0u, 4u },
    { 1u, 4u, 4u },
    { 34u, 8u, 5u },
    { 35u, 13u, 4u },
    { 36u, 17u, 6u },
    { 43u, 23u, 6u },
    { 52u, 29u, 4u },
    { 53u, 33u, 8u },
    { 54u, 41u, 10u },
    { 55u, 51u, 6u },
    { 56u, 57u, 6u },
    { 60u, 63u, 3u },
    { 62u, 66u, 2u },
    { 68u, 68u, 8u },
    { 69u, 76u, 8u },
    { 70u, 84u, 8u },
    { 71u, 92u, 8u },
    { 72u, 100u, 8u },
    { 73u, 108u, 8u },
    { 74u, 116u, 8u },
    { 76u, 124u, 5u },
    { 77u, 129u, 3u },
};

static const AvspRound1Class1fActionRecordSpec avsp_round1_class1f_action_records[AVSP_ROUND1_CLASS1F_ACTION_RECORD_COUNT] =
{
    { 0x0012e8a8UL, 0x0012e8b8UL, 0x0012f994UL, 9u, 0, 1u, 0u, 0u },
    { 0x0012e8b8UL, 0x0012e8c8UL, 0x0012f9bcUL, 9u, 0, 1u, 0u, 0u },
    { 0x0012e8c8UL, 0x0012e8d8UL, 0x0012f9e4UL, 9u, 0, 1u, 0u, 0u },
    { 0x0012e8d8UL, 0x0012e8a8UL, 0x0012f9bcUL, 9u, -32768, 1u, 0u, 0u },
    { 0x0012e8ecUL, 0x0012e8fcUL, 0x0012f5deUL, 9u, 0, 2u, 0u, 0u },
    { 0x0012e8fcUL, 0x0012e90cUL, 0x0012fa0cUL, 9u, 0, 2u, 0u, 0u },
    { 0x0012e90cUL, 0x0012e91cUL, 0x0012fa2aUL, 9u, 0, 2u, 0u, 0u },
    { 0x0012e91cUL, 0x0012e8ecUL, 0x0012fa0cUL, 9u, -32768, 2u, 0u, 0u },
    { 0x0012d590UL, 0x0012d5a0UL, 0x0012fa48UL, 4u, 0, 1u, 0u, 0u },
    { 0x0012d5a0UL, 0x0012d5b0UL, 0x0012fa7aUL, 4u, 0, 1u, 0u, 0u },
    { 0x0012d5b0UL, 0x0012d5c0UL, 0x0012faa2UL, 4u, 0, 1u, 0u, 0u },
    { 0x0012d5c0UL, 0x0012d5d0UL, 0x0012fac0UL, 4u, 0, 1u, 0u, 0u },
    { 0x0012d5d0UL, 0x0012d5d0UL, 0x0012f5acUL, 4u, -32768, 1u, 0u, 0u },
    { 0x0012d5e4UL, 0x0012d5f4UL, 0x0012fae8UL, 4u, 0, 3u, 0u, 0u },
    { 0x0012d5f4UL, 0x0012d604UL, 0x0012fb10UL, 4u, 0, 3u, 0u, 0u },
    { 0x0012d604UL, 0x0012d614UL, 0x0012fb38UL, 4u, 0, 2u, 0u, 0u },
    { 0x0012d614UL, 0x0012d614UL, 0x0012f5deUL, 4u, -32768, 2u, 0u, 0u },
    { 0x0012d628UL, 0x0012d638UL, 0x0012f5deUL, 6u, 0, 2u, 0u, 0u },
    { 0x0012d638UL, 0x0012d648UL, 0x0012f930UL, 7u, 0, 4u, 0u, 0u },
    { 0x0012d648UL, 0x0012d658UL, 0x0012f712UL, 7u, 0, 1u, 0u, 0u },
    { 0x0012d658UL, 0x0012d668UL, 0x0012fd0aUL, 6u, 0, 1u, 0u, 0u },
    { 0x0012d668UL, 0x0012d678UL, 0x0012f5acUL, 3u, 0, 1u, 0u, 0u },
    { 0x0012d678UL, 0x0012d678UL, 0x0012f5acUL, 4u, -32768, 1u, 0u, 0u },
    { 0x0012d890UL, 0x0012d8a0UL, 0x0012fe9eUL, 8u, 0, 1u, 0u, 0u },
    { 0x0012d8a0UL, 0x0012d8b0UL, 0x0012febcUL, 1u, 0, 1u, 1u, 0u },
    { 0x0012d8b0UL, 0x0012d8c0UL, 0x0012febcUL, 9u, 0, 1u, 0u, 0u },
    { 0x0012d8c0UL, 0x0012d8d0UL, 0x0012fef4UL, 10u, 0, 1u, 0u, 0u },
    { 0x0012d8d0UL, 0x0012d8e0UL, 0x0012ff22UL, 16u, 0, 1u, 0u, 0u },
    { 0x0012d8e0UL, 0x0012d8e0UL, 0x0012f5acUL, 8u, -32768, 1u, 0u, 0u },
    { 0x0012e65cUL, 0x0012e66cUL, 0x0012f712UL, 8u, 0, 1u, 0u, 0u },
    { 0x0012e66cUL, 0x0012e67cUL, 0x0012f930UL, 8u, 0, 4u, 0u, 0u },
    { 0x0012e67cUL, 0x0012e68cUL, 0x0012f5deUL, 4u, 0, 2u, 0u, 0u },
    { 0x0012e68cUL, 0x0012e68cUL, 0x0012f5deUL, 6u, -32768, 2u, 0u, 0u },
    { 0x0012e38cUL, 0x0012e39cUL, 0x0013065eUL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e39cUL, 0x0012e3acUL, 0x0013067cUL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e3acUL, 0x0012e3bcUL, 0x0013069aUL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e3bcUL, 0x0012e3ccUL, 0x001306b8UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e3ccUL, 0x0012e3dcUL, 0x001306d6UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e3dcUL, 0x0012e3ecUL, 0x001306f4UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e3ecUL, 0x0012e3fcUL, 0x00130712UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e3fcUL, 0x0012e3fcUL, 0x00130730UL, 8u, -32768, 0u, 0u, 0u },
    { 0x0012e410UL, 0x0012e420UL, 0x0013074eUL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e420UL, 0x0012e430UL, 0x0013076cUL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e430UL, 0x0012e440UL, 0x0013078aUL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e440UL, 0x0012e450UL, 0x001307a8UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e450UL, 0x0012e460UL, 0x001307c6UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e460UL, 0x0012e470UL, 0x001307e4UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e470UL, 0x0012e480UL, 0x00130802UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e480UL, 0x0012e490UL, 0x00130820UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e490UL, 0x0012e4a0UL, 0x0013083eUL, 8u, 0, 0u, 0u, 0u },
    { 0x0012e4a0UL, 0x0012e410UL, 0x00130866UL, 8u, -32768, 0u, 0u, 0u },
    { 0x0012da70UL, 0x0012da80UL, 0x0012fe9eUL, 8u, 0, 1u, 0u, 0u },
    { 0x0012da80UL, 0x0012da90UL, 0x0012febcUL, 1u, 0, 1u, 5u, 0u },
    { 0x0012da90UL, 0x0012daa0UL, 0x0012febcUL, 9u, 0, 1u, 0u, 0u },
    { 0x0012daa0UL, 0x0012dab0UL, 0x0012fef4UL, 10u, 0, 1u, 0u, 0u },
    { 0x0012dab0UL, 0x0012dac0UL, 0x0012ff22UL, 16u, 0, 1u, 0u, 0u },
    { 0x0012dac0UL, 0x0012dac0UL, 0x0012f5acUL, 8u, -32768, 1u, 0u, 0u },
    { 0x0012dad4UL, 0x0012dae4UL, 0x0012ff4aUL, 8u, 0, 1u, 0u, 0u },
    { 0x0012dae4UL, 0x0012daf4UL, 0x0012ff9aUL, 1u, 0, 1u, 6u, 0u },
    { 0x0012daf4UL, 0x0012db04UL, 0x0012ff9aUL, 9u, 0, 1u, 0u, 0u },
    { 0x0012db04UL, 0x0012db14UL, 0x0012ffd8UL, 10u, 0, 1u, 0u, 0u },
    { 0x0012db14UL, 0x0012db24UL, 0x0013000aUL, 16u, 0, 1u, 0u, 0u },
    { 0x0012db24UL, 0x0012db24UL, 0x0012f5acUL, 8u, -32768, 1u, 0u, 0u },
    { 0x0012e944UL, 0x0012e954UL, 0x0012f5deUL, 8u, 1, 2u, 0u, 1u },
    { 0x0012e954UL, 0x0012e964UL, 0x0012fce2UL, 5u, 0, 10u, 0u, 0u },
    { 0x0012e964UL, 0x0012e964UL, 0x0012fce2UL, 8u, -32768, 10u, 0u, 0u },
    { 0x0012e9ccUL, 0x0012e9dcUL, 0x0012fc92UL, 4u, 0, 11u, 0u, 0u },
    { 0x0012e9dcUL, 0x0012e9dcUL, 0x0012f5fcUL, 4095u, -32768, 2u, 0u, 0u },
    { 0x0012e708UL, 0x0012e718UL, 0x0012f638UL, 2u, 8, 1u, 0u, 8u },
    { 0x0012e718UL, 0x0012e728UL, 0x0012f670UL, 2u, 8, 1u, 0u, 8u },
    { 0x0012e728UL, 0x0012e738UL, 0x0012f6a8UL, 2u, 8, 1u, 0u, 8u },
    { 0x0012e738UL, 0x0012e748UL, 0x0012f6daUL, 2u, 8, 1u, 0u, 8u },
    { 0x0012e748UL, 0x0012e758UL, 0x0012f712UL, 2u, 8, 1u, 0u, 8u },
    { 0x0012e758UL, 0x0012e768UL, 0x0012f72aUL, 2u, 8, 1u, 0u, 8u },
    { 0x0012e768UL, 0x0012e778UL, 0x0012f762UL, 2u, 8, 1u, 0u, 8u },
    { 0x0012e778UL, 0x0012e708UL, 0x0012f794UL, 2u, -32760, 1u, 0u, 8u },
    { 0x0012eafcUL, 0x0012eb0cUL, 0x0012f638UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb0cUL, 0x0012eb1cUL, 0x0012f670UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb1cUL, 0x0012eb2cUL, 0x0012f6a8UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb2cUL, 0x0012eb3cUL, 0x0012f6daUL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb3cUL, 0x0012eb4cUL, 0x0012f712UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb4cUL, 0x0012eb5cUL, 0x0012f72aUL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb5cUL, 0x0012eb6cUL, 0x0012f762UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb6cUL, 0x0012eafcUL, 0x0012f794UL, 3u, -32760, 1u, 0u, 8u },
    { 0x0012eafcUL, 0x0012eb0cUL, 0x0012f638UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb0cUL, 0x0012eb1cUL, 0x0012f670UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb1cUL, 0x0012eb2cUL, 0x0012f6a8UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb2cUL, 0x0012eb3cUL, 0x0012f6daUL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb3cUL, 0x0012eb4cUL, 0x0012f712UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb4cUL, 0x0012eb5cUL, 0x0012f72aUL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb5cUL, 0x0012eb6cUL, 0x0012f762UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb6cUL, 0x0012eafcUL, 0x0012f794UL, 3u, -32760, 1u, 0u, 8u },
    { 0x0012eafcUL, 0x0012eb0cUL, 0x0012f638UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb0cUL, 0x0012eb1cUL, 0x0012f670UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb1cUL, 0x0012eb2cUL, 0x0012f6a8UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb2cUL, 0x0012eb3cUL, 0x0012f6daUL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb3cUL, 0x0012eb4cUL, 0x0012f712UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb4cUL, 0x0012eb5cUL, 0x0012f72aUL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb5cUL, 0x0012eb6cUL, 0x0012f762UL, 3u, 8, 1u, 0u, 8u },
    { 0x0012eb6cUL, 0x0012eafcUL, 0x0012f794UL, 3u, -32760, 1u, 0u, 8u },
    { 0x0012e78cUL, 0x0012e79cUL, 0x0012f7ccUL, 2u, 8, 2u, 0u, 8u },
    { 0x0012e79cUL, 0x0012e7acUL, 0x0012f7e4UL, 2u, 8, 2u, 0u, 8u },
    { 0x0012e7acUL, 0x0012e7bcUL, 0x0012f7fcUL, 2u, 8, 2u, 0u, 8u },
    { 0x0012e7bcUL, 0x0012e7ccUL, 0x0012f814UL, 2u, 8, 2u, 0u, 8u },
    { 0x0012e7ccUL, 0x0012e7dcUL, 0x0012f82cUL, 2u, 8, 2u, 0u, 8u },
    { 0x0012e7dcUL, 0x0012e7ecUL, 0x0012f85eUL, 2u, 8, 2u, 0u, 8u },
    { 0x0012e7ecUL, 0x0012e7fcUL, 0x0012f890UL, 2u, 8, 2u, 0u, 8u },
    { 0x0012e7fcUL, 0x0012e78cUL, 0x0012f8b8UL, 2u, -32760, 2u, 0u, 8u },
    { 0x0012ec04UL, 0x0012ec14UL, 0x0012f7ccUL, 2u, 8, 2u, 0u, 8u },
    { 0x0012ec14UL, 0x0012ec24UL, 0x0012f7e4UL, 3u, 8, 2u, 0u, 8u },
    { 0x0012ec24UL, 0x0012ec34UL, 0x0012f7fcUL, 2u, 8, 2u, 0u, 8u },
    { 0x0012ec34UL, 0x0012ec44UL, 0x0012f814UL, 3u, 8, 2u, 0u, 8u },
    { 0x0012ec44UL, 0x0012ec54UL, 0x0012f82cUL, 2u, 8, 2u, 0u, 8u },
    { 0x0012ec54UL, 0x0012ec64UL, 0x0012f85eUL, 3u, 8, 2u, 0u, 8u },
    { 0x0012ec64UL, 0x0012ec74UL, 0x0012f890UL, 2u, 8, 2u, 0u, 8u },
    { 0x0012ec74UL, 0x0012ec04UL, 0x0012f8b8UL, 3u, -32760, 2u, 0u, 8u },
    { 0x0012ec88UL, 0x0012ec98UL, 0x0012f7ccUL, 6u, 8, 2u, 0u, 8u },
    { 0x0012ec98UL, 0x0012eca8UL, 0x0012f7e4UL, 7u, 8, 2u, 0u, 8u },
    { 0x0012eca8UL, 0x0012ecb8UL, 0x0012f7fcUL, 6u, 8, 2u, 0u, 8u },
    { 0x0012ecb8UL, 0x0012ecc8UL, 0x0012f814UL, 7u, 8, 2u, 0u, 8u },
    { 0x0012ecc8UL, 0x0012ecd8UL, 0x0012f82cUL, 6u, 8, 2u, 0u, 8u },
    { 0x0012ecd8UL, 0x0012ece8UL, 0x0012f85eUL, 7u, 8, 2u, 0u, 8u },
    { 0x0012ece8UL, 0x0012ecf8UL, 0x0012f890UL, 6u, 8, 2u, 0u, 8u },
    { 0x0012ecf8UL, 0x0012ec88UL, 0x0012f8b8UL, 7u, -32760, 2u, 0u, 8u },
    { 0x0012ea24UL, 0x0012ea34UL, 0x0012fb60UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012ea34UL, 0x0012ea44UL, 0x0012fbfcUL, 8u, 0, 0u, 0u, 0u },
    { 0x0012ea44UL, 0x0012ea54UL, 0x0012fc74UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012ea54UL, 0x0012ea64UL, 0x0012fc24UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012ea64UL, 0x0012ea64UL, 0x0012fb98UL, 4095u, -32768, 0u, 0u, 0u },
    { 0x0012e9f0UL, 0x0012ea00UL, 0x0012fc74UL, 10u, 0, 0u, 0u, 0u },
    { 0x0012ea00UL, 0x0012ea10UL, 0x0012fc24UL, 8u, 0, 0u, 0u, 0u },
    { 0x0012ea10UL, 0x0012ea10UL, 0x0012fb98UL, 4095u, -32768, 0u, 0u, 0u },
};

static const AvspRound1Class1fMovementTableSpec avsp_round1_class1f_movement_tables[AVSP_ROUND1_CLASS1F_MOVEMENT_TABLE_COUNT] =
{
    { 1u, { { 0, 128 }, { 49, 125 }, { 97, 118 }, { 142, 106 }, { 180, 90 }, { 212, 71 }, { 236, 48 }, { 250, 24 }, { 256, 0 }, { 250, -24 }, { 236, -48 }, { 212, -71 }, { 180, -90 }, { 142, -106 }, { 97, -118 }, { 49, -125 }, { 0, -128 }, { -49, -125 }, { -97, -118 }, { -142, -106 }, { -180, -90 }, { -212, -71 }, { -236, -48 }, { -250, -24 }, { -256, 0 }, { -250, 24 }, { -236, 48 }, { -212, 71 }, { -180, 90 }, { -142, 106 }, { -97, 118 }, { -49, 125 } } },
    { 8u, { { 0, 1024 }, { 399, 1003 }, { 782, 945 }, { 1136, 850 }, { 1447, 723 }, { 1701, 568 }, { 1890, 391 }, { 2007, 199 }, { 2048, 0 }, { 2007, -199 }, { 1890, -391 }, { 1701, -568 }, { 1447, -723 }, { 1136, -850 }, { 782, -945 }, { 399, -1003 }, { 0, -1024 }, { -399, -1003 }, { -782, -945 }, { -1136, -850 }, { -1447, -723 }, { -1701, -568 }, { -1890, -391 }, { -2007, -199 }, { -2048, 0 }, { -2007, 199 }, { -1890, 391 }, { -1701, 568 }, { -1447, 723 }, { -1136, 850 }, { -782, 945 }, { -399, 1003 } } },
};

static const unsigned char avsp_round1_class1f_attack_timers[AVSP_ROUND1_CLASS1F_ATTACK_TIMER_COUNT] =
{
    30u, 30u, 30u, 30u, 60u, 60u, 60u, 60u, 120u, 120u, 120u, 120u, 160u, 160u, 160u, 160u
};

static const AvspRound1Class1fActionProgramSpec avsp_round1_class1f_action_program =
{
    0x05F0u, 0x0070u, 0x0260u, 0x0600u,
    0x0140u, 0x00E8u, { 0x16u, 0x0Au }, { 0x1Au, 0x06u },
    0x0020u, 0x0040u, 0x000Cu, 0x0018u,
    { 34u, 35u }, { 36u, 52u }, { 0x44u, 0x48u },
    { -65536L, -81920L, -98304L, -131072L },
    229376L, -32768L, 32, -8192L,
    { 0u, 0u, 0u, 0u, 0u, 0u, 2u, 2u, 2u, 2u, 2u, 2u, 4u, 4u, 4u, 4u, 4u, 4u, 4u, 4u, 4u, 4u, 4u, 4u, 6u, 6u, 6u, 6u, 6u, 6u, 6u, 6u },
    { 0u, 1u, 2u, 6u },
    { 1u, 1u, 4u, 3u },
    { 55u, 56u, 43u, 43u, 43u, 55u, 43u, 43u, 56u },
    { 0u, 0u, 0u, 0u, 0u, 32u, 32u, 32u, 32u, 32u, 32u, 32u, 32u, 64u, 64u, 64u, 64u, 64u, 64u, 96u, 96u, 96u, 96u, 96u, 128u, 128u, 128u, 128u, 128u, 128u, 128u, 128u },
    {
        { 8u, 8u, 8u, 8u, 10u, 10u, 10u, 10u, 12u, 12u, 12u, 12u, 16u, 16u, 16u, 16u, 17u, 18u, 19u, 20u, 21u, 22u, 23u, 24u, 25u, 26u, 27u, 28u, 29u, 30u, 31u, 32u },
        { 6u, 6u, 6u, 6u, 6u, 6u, 6u, 6u, 7u, 7u, 7u, 7u, 8u, 8u, 8u, 8u, 9u, 9u, 9u, 9u, 10u, 10u, 10u, 10u, 11u, 11u, 11u, 11u, 12u, 14u, 16u, 18u },
        { 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 2u, 2u, 2u, 2u, 2u, 2u, 2u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 3u, 4u, 4u, 4u, 4u, 6u, 8u, 10u, 16u },
        { 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 2u, 2u, 2u, 2u, 2u, 2u, 2u, 2u, 2u, 2u, 4u, 4u, 4u, 6u, 8u, 12u },
        { 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 1u, 2u, 2u, 2u, 3u, 5u, 8u },
    }
};

static const AvspRound1Class1fInitialSpec avsp_round1_class1f_initial_actors[AVSP_ROUND1_CLASS1F_INITIAL_ACTOR_COUNT] =
{
    { 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 16u, 0x8000, 216u, 0x0Fu, 1u },
    { 0x00ff9dc0UL, 0x0200u, 0x1000u, 616, 304, 304, 1u, 1u, 17u, 0x8000, 216u, 0x0Fu, 1u },
    { 0x00ff9e80UL, 0x0200u, 0x1000u, 640, 256, 256, 1u, 1u, 17u, 0x8000, 216u, 0x0Fu, 1u },
    { 0x00ff9f40UL, 0x0200u, 0x1200u, 696, 264, 264, 1u, 1u, 18u, 0x8000, 216u, 0x07u, 0u },
    { 0x00ffa000UL, 0x0200u, 0x1200u, 600, 300, 300, 1u, 1u, 17u, 0x8000, 216u, 0x07u, 0u },
    { 0x00ffa0c0UL, 0x0200u, 0x1200u, 648, 280, 280, 1u, 1u, 16u, 0x8000, 216u, 0x07u, 0u },
    { 0x00ffa180UL, 0x0200u, 0x1200u, 640, 320, 320, 1u, 1u, 18u, 0x8000, 216u, 0x07u, 0u },
    { 0x00ffa240UL, 0x0200u, 0x1400u, 744, 280, 280, 1u, 1u, 17u, 0x8000, 9u, 0x0Fu, 1u },
    { 0x00ffa300UL, 0x0200u, 0x1400u, 704, 296, 296, 1u, 1u, 19u, 0x8000, 3u, 0x0Fu, 1u },
    { 0x00ffa3c0UL, 0x0200u, 0x1400u, 656, 312, 312, 1u, 1u, 19u, 0x8000, 16u, 0x0Fu, 1u },
};

static const AvspRound1AnimationSequenceSpec avsp_round1_class1f_initial_sequences[AVSP_ROUND1_CLASS1F_INITIAL_SEQUENCE_COUNT] =
{
    { 0u, 4u, AVSP_ROUND1_ANIMATION_TERMINAL_LOOP_FIRST, { { 9u, 0, 0x0012e8a8UL, 0x0012f994UL, 1u, 0u }, { 9u, 0, 0x0012e8b8UL, 0x0012f9bcUL, 1u, 0u }, { 9u, 0, 0x0012e8c8UL, 0x0012f9e4UL, 1u, 0u }, { 9u, -32768, 0x0012e8d8UL, 0x0012f9bcUL, 1u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 1u, 4u, AVSP_ROUND1_ANIMATION_TERMINAL_LOOP_FIRST, { { 9u, 0, 0x0012e8ecUL, 0x0012f5deUL, 2u, 0u }, { 9u, 0, 0x0012e8fcUL, 0x0012fa0cUL, 2u, 0u }, { 9u, 0, 0x0012e90cUL, 0x0012fa2aUL, 2u, 0u }, { 9u, -32768, 0x0012e91cUL, 0x0012fa0cUL, 2u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 52u, 4u, AVSP_ROUND1_ANIMATION_TERMINAL_SELF_LOOP, { { 8u, 0, 0x0012e65cUL, 0x0012f712UL, 1u, 0u }, { 8u, 0, 0x0012e66cUL, 0x0012f930UL, 4u, 0u }, { 4u, 0, 0x0012e67cUL, 0x0012f5deUL, 2u, 0u }, { 6u, -32768, 0x0012e68cUL, 0x0012f5deUL, 2u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 60u, 3u, AVSP_ROUND1_ANIMATION_TERMINAL_STATE_GUARD, { { 8u, 1, 0x0012e944UL, 0x0012f5deUL, 2u, 0u }, { 5u, 0, 0x0012e954UL, 0x0012fce2UL, 10u, 0u }, { 8u, -32768, 0x0012e964UL, 0x0012fce2UL, 10u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 62u, 2u, AVSP_ROUND1_ANIMATION_TERMINAL_STATE_GUARD, { { 4u, 0, 0x0012e9ccUL, 0x0012fc92UL, 11u, 0u }, { 4095u, -32768, 0x0012e9dcUL, 0x0012f5fcUL, 2u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 76u, 5u, AVSP_ROUND1_ANIMATION_TERMINAL_STATE_GUARD, { { 8u, 0, 0x0012ea24UL, 0x0012fb60UL, 0u, 0u }, { 8u, 0, 0x0012ea34UL, 0x0012fbfcUL, 0u, 0u }, { 8u, 0, 0x0012ea44UL, 0x0012fc74UL, 0u, 0u }, { 8u, 0, 0x0012ea54UL, 0x0012fc24UL, 0u, 0u }, { 4095u, -32768, 0x0012ea64UL, 0x0012fb98UL, 0u, 0u } } },
};

static const unsigned short avsp_round1_class1f_initial_audio_commands[AVSP_ROUND1_CLASS1F_AIRBORNE_ACTOR_COUNT] =
{
    0x004Du, 0x0118u, 0x0000u
};

static const AvspRound1Class09InitialSpec avsp_round1_class09_initial_actors[AVSP_ROUND1_CLASS09_INITIAL_ACTOR_COUNT] =
{
    { 0x00ffb480UL, 992, 240, 240, 0x0200u, 0x0000u, 0u, 0x0006dbdaUL },
    { 0x00ffb500UL, 940, 240, 240, 0x0200u, 0x0000u, 0u, 0x0006dbdaUL },
};

static const unsigned char avsp_round1_class09_selector_table[8] =
{
    0u, 7u, 8u, 9u, 10u, 8u, 9u, 10u
};

static const AvspRound1AnimationStateSpec avsp_round1_class09_sequences[AVSP_ROUND1_CLASS09_SEQUENCE_COUNT][AVSP_ROUND1_CLASS09_SEQUENCE_RECORDS] =
{
    { { 8u, 0, 0x0006dbdaUL, 0x0006dd26UL, 1u, 1u }, { 8u, -32768, 0x0006dbeaUL, 0x0006dd26UL, 1u, 1u } },
    { { 8u, 0, 0x0006dbfeUL, 0x0006dd44UL, 1u, 1u }, { 8u, -32768, 0x0006dc0eUL, 0x0006dd44UL, 1u, 1u } },
    { { 8u, 0, 0x0006dc22UL, 0x0006dd68UL, 1u, 1u }, { 8u, -32768, 0x0006dc32UL, 0x0006dd68UL, 1u, 1u } },
    { { 8u, 0, 0x0006dc46UL, 0x0006dd8cUL, 1u, 1u }, { 8u, -32768, 0x0006dc56UL, 0x0006dd8cUL, 1u, 1u } },
    { { 8u, 0, 0x0006dc6aUL, 0x0006ddb0UL, 1u, 1u }, { 8u, -32768, 0x0006dc7aUL, 0x0006ddb0UL, 1u, 1u } },
};

static const unsigned char avsp_round1_class09_sequence_selectors[AVSP_ROUND1_CLASS09_SEQUENCE_COUNT] =
{
    0u, 7u, 8u, 9u, 10u
};

static const AvspRound1Class4eSpawnSpec avsp_round1_class4e_initial_spawns[AVSP_ROUND1_CLASS09_INITIAL_ACTOR_COUNT] =
{
    { 0x00ffc500UL, 816, 384, 296 },
    { 0x00ffc480UL, 848, 424, 296 },
};

static const AvspRound1VecS16 avsp_round1_class4e_jitter[AVSP_ROUND1_CLASS4E_JITTER_COUNT] =
{
    { 0, 0 },
    { 4, 0 },
    { 4, -4 },
    { 4, 4 },
    { -4, 0 },
    { -4, -4 },
    { -4, 4 },
    { -8, 8 },
};

static const AvspRound1AnimationStateSpec avsp_round1_class4e_records[AVSP_ROUND1_CLASS4E_PRESENTATION_COUNT] =
{
    { 2u, 0, 0x000929b0UL, 0x00092c58UL, 0u, 0u },
    { 2u, 0, 0x000929c0UL, 0x00092c66UL, 0u, 0u },
    { 2u, 0, 0x000929d0UL, 0x00092c74UL, 0u, 0u },
    { 2u, 0, 0x000929e0UL, 0x00092c82UL, 0u, 0u },
    { 4095u, -32768, 0x000929f0UL, 0x00092c90UL, 0u, 0u },
};

static const AvspRound1Class44GuardSpec avsp_round1_class44_guard =
{
    0x00ffc580UL, 792, 296, 296, 0x0200u, 0x0000u, 0x08d9a4UL, 0u, 0u, 0u, 0x8000u
};

static const AvspRound1AnimationStateSpec avsp_round1_class44_records[AVSP_ROUND1_CLASS44_PRESENTATION_COUNT] =
{
    { 4095u, -32768, 0x0008daf2UL, 0x0008db2eUL, 0u, 0u },
    { 4095u, -32768, 0x0008db1aUL, 0x0008db6aUL, 0u, 0u },
};

static const AvspRound1NavigationBoundsSpec avsp_round1_first_segment_bounds =
{
    720, 256, 752, 1072,
    272, 400
};

static const AvspRound1TerrainRecordSpec avsp_round1_first_segment_terrain_records[AVSP_ROUND1_TERRAIN_RECORD_COUNT] =
{
    { 0x00u, 0x80u, 0x80u, 0x80u, 0x80u, 0x80u, 0x80u, 0x80u },
    { 0x02u, 0x02u, 0x80u, 0x80u, 0x10u, 0x10u, 0x00u, 0x80u },
    { 0x02u, 0x02u, 0x80u, 0x80u, 0x10u, 0x10u, 0xFFu, 0x80u },
    { 0x02u, 0x02u, 0x80u, 0x80u, 0x10u, 0x08u, 0x00u, 0x80u },
    { 0x06u, 0x04u, 0x02u, 0x01u, 0x00u, 0x00u, 0x80u, 0x80u },
    { 0x06u, 0x04u, 0x02u, 0x01u, 0x00u, 0x08u, 0x80u, 0x80u },
    { 0x04u, 0x02u, 0x02u, 0x01u, 0x00u, 0x08u, 0x80u, 0x80u },
};

static const unsigned char avsp_round1_first_segment_terrain_packed[AVSP_ROUND1_TERRAIN_PACKED_BYTES] =
{
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0xA0u, 0xAAu, 0xAAu, 0xAAu, 0xAAu, 0xAAu, 0xAAu, 0xAAu, 0xAAu, 0x2Au, 0x00u, 0x00u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x01u, 0x00u, 0x50u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u,
    0x55u, 0x55u, 0x15u, 0x00u, 0x00u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x01u, 0x00u, 0x50u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x15u, 0x00u, 0x00u, 0x55u, 0x55u, 0x55u, 0x55u,
    0x55u, 0x55u, 0x55u, 0x55u, 0x55u, 0x01u, 0x00u, 0x00u
};

static const AvspRound1ObstacleSpec avsp_round1_coffee_shop_obstacle =
{
    0xffb380UL, 0x0A, 20u, 0x0200u, 0x0000u,
    1123, 323, 323, 0u, 0x06e136UL, 0x06e196UL, 1u, 1u,
    { 0, 0, 32u, 127u, 0, 6u, 0, 0u, 0u }
};

static const AvspRound1CameraSpec avsp_round1_coffee_shop_camera =
{
    640, 256, 640, 832, 256, 256, 0x40u, 0x20u,
    0x00C0, 0x00E0, 0x00A0, 0x0050, 0x0060, 0x0040,
    1u, 1200u,
    {0u, 1u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 7u, 8u, 8u, 9u, 9u, 10u, 10u, 11u, 11u, 11u, 11u}
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

static const AvspRound1PlayerJumpVectorSpec avsp_round1_player_jump_vectors[AVSP_ROUND1_PLAYER_JUMP_VECTOR_COUNT] =
{
    { 0L, 0L, 557056L, -32768L },
    { 0L, 0L, 786432L, -32768L },
    { -983040L, 26624L, 262144L, -14336L },
    { -589824L, 9216L, 786432L, -34816L },
    { 589824L, -8192L, 262144L, -32768L },
    { 557056L, -9216L, 786432L, -34816L },
};

static const AvspRound1PlayerJumpVectorSpec avsp_round1_player_jump_down_vectors[AVSP_ROUND1_PLAYER_JUMP_DOWN_VECTOR_COUNT] =
{
    { 393216L, -32768L, 0L, 0L },
    { 786432L, -40960L, 0L, 0L }
};

static const AvspRound1PlayerJumpSequenceSpec avsp_round1_player_jump_sequences[AVSP_ROUND1_PLAYER_JUMP_SEQUENCE_COUNT] =
{
    { 3u, 2u, { { 1u, 0, 0x15f2ccUL, 0x160bc6UL, 1u, 0u }, { 1u, -32768, 0x15f2dcUL, 0x160bc6UL, 1u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 4u, 5u, { { 8u, 0, 0x15f2f0UL, 0x160cdaUL, 2u, 0u }, { 5u, 0, 0x15f300UL, 0x160d02UL, 2u, 0u }, { 5u, 0, 0x15f310UL, 0x160d2aUL, 2u, 0u }, { 5u, 0, 0x15f320UL, 0x160d52UL, 2u, 0u }, { 4095u, -32768, 0x15f330UL, 0x160d86UL, 2u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 5u, 7u, { { 10u, 0, 0x15f344UL, 0x160beeUL, 2u, 0u }, { 3u, 0, 0x15f354UL, 0x160c16UL, 2u, 0u }, { 3u, 0, 0x15f364UL, 0x160c3eUL, 13u, 0u }, { 6u, 0, 0x15f374UL, 0x160c66UL, 14u, 0u }, { 6u, 0, 0x15f384UL, 0x160c84UL, 15u, 0u }, { 8u, 0, 0x15f394UL, 0x160cacUL, 16u, 0u }, { 4095u, -32768, 0x15f3a4UL, 0x160beeUL, 2u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 6u, 8u, { { 2u, 0, 0x15f3b8UL, 0x160beeUL, 2u, 0u }, { 10u, 0, 0x15f3c8UL, 0x160cacUL, 16u, 0u }, { 3u, 0, 0x15f3d8UL, 0x160c84UL, 15u, 0u }, { 3u, 0, 0x15f3e8UL, 0x160c66UL, 14u, 0u }, { 6u, 0, 0x15f3f8UL, 0x160c3eUL, 13u, 0u }, { 6u, 0, 0x15f408UL, 0x160c16UL, 2u, 0u }, { 6u, 0, 0x15f418UL, 0x160beeUL, 2u, 0u }, { 4095u, -32768, 0x15f428UL, 0x160beeUL, 2u, 0u } } },
    { 10u, 2u, { { 1u, 0, 0x15f2ccUL, 0x160bc6UL, 1u, 0u }, { 1u, -32768, 0x15f2dcUL, 0x160bc6UL, 1u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 15u, 3u, { { 4u, 0, 0x15f43cUL, 0x162baaUL, 18u, 0u }, { 10u, 0, 0x15f44cUL, 0x162bc8UL, 18u, 0u }, { 4095u, -32768, 0x15f45cUL, 0x162baaUL, 18u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 41u, 2u, { { 4u, 0, 0x15fc3cUL, 0x162ee2UL, 9u, 22u }, { 4095u, -32768, 0x15fc4cUL, 0x162ee2UL, 9u, 23u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 42u, 1u, { { 4095u, -32768, 0x15fce8UL, 0x16212cUL, 7u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 60u, 1u, { { 4095u, -32768, 0x15fc60UL, 0x162ee2UL, 9u, 35u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
};

static const AvspRound1PlayerPresentationActorSpec avsp_round1_player_jump_actor =
{
    0u, 0u, 0x8000u
};

static const AvspRound1PlayerWeaponSpec avsp_round1_player_weapon =
{
    3072u,
    0x0c02u,
    6656u,
    6658u,
    0u,
    2u,
    16u,
    64u,
    40u,
    12u,
    2u,
    6u,
    0,
    4,
    0x8680u,
    0x0080u,
    0x8380u,
    0x0002fc3cUL,
    0x00030cb6UL
};

static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_frames[AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT] =
{
    { 3072u, 0u, 0x0015f1f4UL, 0x001626a4UL, 1u, 0u },
    { 3074u, 2u, 0x0015e540UL, 0x00161772UL, 1u, 0u },
    { 3074u, 2u, 0x0015e540UL, 0x00161772UL, 1u, 0u },
    { 3074u, 2u, 0x0015e540UL, 0x00161772UL, 1u, 0u },
    { 3076u, 4u, 0x0015e550UL, 0x001618b2UL, 1u, 0u },
    { 3076u, 4u, 0x0015e560UL, 0x00161a0aUL, 1u, 0u },
    { 3076u, 4u, 0x0015e560UL, 0x00161a0aUL, 1u, 0u },
    { 3076u, 4u, 0x0015e570UL, 0x001618b2UL, 1u, 0u },
    { 3076u, 4u, 0x0015e580UL, 0x00161772UL, 1u, 0u },
    { 3076u, 4u, 0x0015e580UL, 0x00161772UL, 1u, 0u },
    { 3076u, 4u, 0x0015e580UL, 0x00161772UL, 1u, 0u },
    { 3076u, 4u, 0x0015e580UL, 0x00161772UL, 1u, 0u },
    { 3076u, 4u, 0x0015e580UL, 0x00161772UL, 1u, 0u },
    { 3076u, 4u, 0x0015e580UL, 0x00161772UL, 1u, 0u },
    { 3076u, 4u, 0x0015e580UL, 0x00161772UL, 1u, 0u },
    { 3076u, 4u, 0x0015e580UL, 0x00161772UL, 1u, 0u },
    { 3076u, 4u, 0x0015e580UL, 0x00161772UL, 1u, 0u },
    { 3076u, 4u, 0x0015e580UL, 0x00161772UL, 1u, 0u },
    { 3076u, 4u, 0x0015e580UL, 0x00161772UL, 1u, 0u },
    { 0u, 0u, 0x0015f1f4UL, 0x001626a4UL, 1u, 0u },
};

static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_empty_frames[AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT] =
{
    { 6656u, 0u, 0x0015f1f4UL, 0x001626a4UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },
    { 0u, 0u, 0x0015f1f4UL, 0x001626a4UL, 1u, 0u },
};

static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_return_frame =
{
    2u, 2u, 0x0015f1f4UL, 0x001626a4UL, 1u, 0u
};

static const AvspRound1VecS16 avsp_round1_weapon_parent_selector_offsets[AVSP_ROUND1_WEAPON_PARENT_SELECTOR_COUNT] =
{
    { 5, 86 },
    { -35, 76 },
    { -6, 90 },
    { -6, 53 },
    { 8, 49 },
    { 19, 54 },
};

static const AvspRound1AnimationStateSpec avsp_round1_weapon_parent_presentations[AVSP_ROUND1_WEAPON_PARENT_PRESENTATION_COUNT] =
{
    { 4u, 0, 0x0002fb48UL, 0x0002fbccUL, 0u, 1u },
    { 4u, 0, 0x0002fb58UL, 0x0002fbdaUL, 0u, 1u },
    { 4u, 0, 0x0002fb68UL, 0x0002fbe8UL, 0u, 1u },
    { 4u, 0, 0x0002fb78UL, 0x0002fbf6UL, 0u, 1u },
    { 4u, 0, 0x0002fb88UL, 0x0002fc04UL, 0u, 1u },
    { 4u, 0, 0x0002fb98UL, 0x0002fc12UL, 0u, 1u },
    { 4u, 0, 0x0002fba8UL, 0x0002fc20UL, 0u, 1u },
};

static const unsigned char avsp_round1_weapon_parent_route_angles[AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT] =
{
    17u, 35u, 47u
};

static const AvspRound1VecS16 avsp_round1_weapon_parent_motion_low[AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT][AVSP_ROUND1_WEAPON_PARENT_LOW_MOTION_COUNT] =
{
    { { 0, 0 }, { 15, -1 }, { 31, -3 }, { 47, -5 }, { 63, -7 }, { 79, -8 }, { 95, -10 }, { 111, -12 }, { 127, -14 }, { 143, -16 }, { 159, -17 }, { 175, -19 }, { 191, -21 }, { 206, -23 }, { 222, -25 }, { 238, -26 } },
    { { 0, 0 }, { -4, -17 }, { -9, -34 }, { -13, -52 }, { -18, -69 }, { -23, -87 }, { -27, -104 }, { -32, -122 }, { -37, -139 }, { -41, -157 }, { -46, -174 }, { -51, -192 }, { -55, -209 }, { -60, -227 }, { -64, -244 }, { -69, -262 } },
    { { 0, 0 }, { -15, -1 }, { -31, -3 }, { -47, -5 }, { -63, -7 }, { -79, -8 }, { -95, -10 }, { -111, -12 }, { -127, -14 }, { -143, -16 }, { -159, -17 }, { -175, -19 }, { -191, -21 }, { -206, -23 }, { -222, -25 }, { -238, -26 } },
};

static const AvspRound1VecS16 avsp_round1_weapon_parent_motion_high[AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT][AVSP_ROUND1_WEAPON_PARENT_HIGH_MOTION_COUNT] =
{
    { { 0, 0 }, { 254, -28 }, { 509, -57 }, { 764, -85 }, { 1018, -114 }, { 1273, -143 }, { 1528, -171 }, { 1782, -200 }, { 2037, -229 }, { 2292, -257 }, { 2546, -286 }, { 2801, -315 }, { 3056, -343 } },
    { { 0, 0 }, { -74, -279 }, { -148, -559 }, { -222, -838 }, { -296, -1118 }, { -370, -1398 }, { -445, -1677 }, { -519, -1957 }, { -593, -2237 }, { -667, -2516 }, { -741, -2796 }, { -816, -3076 }, { -890, -3355 } },
    { { 0, 0 }, { -254, -28 }, { -509, -57 }, { -764, -85 }, { -1018, -114 }, { -1273, -143 }, { -1528, -171 }, { -1782, -200 }, { -2037, -229 }, { -2292, -257 }, { -2546, -286 }, { -2801, -315 }, { -3056, -343 } },
};

static const AvspRound1VecS16 avsp_round1_air_weapon_selector_offsets[AVSP_ROUND1_AIR_WEAPON_SELECTOR_COUNT] =
{
    { 5, 86 },
    { -35, 76 },
    { -6, 90 },
    { -6, 53 },
    { 8, 49 },
    { 20, 55 },
    { -14, 70 },
};

static const AvspRound1AnimationStateSpec avsp_round1_air_weapon_presentations[AVSP_ROUND1_AIR_WEAPON_PRESENTATION_COUNT] =
{
    { 4u, 0, 0x0002fb48UL, 0x0002fbccUL, 0u, 1u },
    { 4u, 0, 0x0002fb58UL, 0x0002fbdaUL, 0u, 1u },
    { 4u, 0, 0x0002fb68UL, 0x0002fbe8UL, 0u, 1u },
    { 4u, 0, 0x0002fb78UL, 0x0002fbf6UL, 0u, 1u },
    { 4u, 0, 0x0002fb88UL, 0x0002fc04UL, 0u, 1u },
    { 4u, 0, 0x0002fb98UL, 0x0002fc12UL, 0u, 1u },
    { 4u, 0, 0x0002fba8UL, 0x0002fc20UL, 0u, 1u },
    { 4u, -32768, 0x0002fbb8UL, 0x0002fc2eUL, 0u, 1u },
};

static const AvspRound1PlayerJumpSequenceSpec avsp_round1_air_weapon_player_sequence =
{
    18u, AVSP_ROUND1_AIR_WEAPON_PLAYER_PRESENTATION_COUNT,
    {
        { 2u, 2, 0x15e9d8UL, 0x161dfcUL, 1u, 0u },
        { 2u, 2, 0x15e9e8UL, 0x161f10UL, 1u, 0u },
        { 2u, 2, 0x15e9f8UL, 0x162036UL, 1u, 0u },
        { 2u, 2, 0x15ea08UL, 0x161f10UL, 1u, 0u },
        { 4095u, -32766, 0x15ea18UL, 0x161dfcUL, 1u, 0u },
        { 0u, 0, 0UL, 0UL, 0u, 0u },
        { 0u, 0, 0UL, 0UL, 0u, 0u },
        { 0u, 0, 0UL, 0UL, 0u, 0u },
    }
};

static const AvspRound1VecS16 avsp_round1_air_weapon_motion_low[AVSP_ROUND1_AIR_WEAPON_LOW_TABLE_COUNT][AVSP_ROUND1_AIR_WEAPON_DIRECTION_COUNT] =
{
    { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } },
    { { 0, 18 }, { 1, 18 }, { 3, 17 }, { 4, 17 }, { 6, 16 }, { 7, 16 }, { 8, 15 }, { 10, 14 }, { 11, 12 }, { 12, 11 }, { 13, 10 }, { 14, 8 }, { 14, 6 }, { 15, 5 }, { 15, 3 }, { 15, 1 }, { 16, 0 }, { 15, -1 }, { 15, -3 }, { 15, -5 }, { 14, -6 }, { 14, -8 }, { 13, -10 }, { 12, -11 }, { 11, -12 }, { 10, -14 }, { 8, -15 }, { 7, -16 }, { 6, -16 }, { 4, -17 }, { 3, -17 }, { 1, -18 }, { 0, -18 }, { -1, -18 }, { -3, -17 }, { -4, -17 }, { -6, -16 }, { -7, -16 }, { -8, -15 }, { -10, -14 }, { -11, -12 }, { -12, -11 }, { -13, -10 }, { -14, -8 }, { -14, -6 }, { -15, -5 }, { -15, -3 }, { -15, -1 }, { -16, 0 }, { -15, 1 }, { -15, 3 }, { -15, 5 }, { -14, 6 }, { -14, 8 }, { -13, 10 }, { -12, 11 }, { -11, 12 }, { -10, 14 }, { -8, 15 }, { -7, 16 }, { -6, 16 }, { -4, 17 }, { -3, 17 }, { -1, 18 } },
    { { 0, 36 }, { 3, 36 }, { 6, 35 }, { 9, 34 }, { 12, 33 }, { 15, 32 }, { 17, 30 }, { 20, 28 }, { 22, 25 }, { 24, 23 }, { 26, 20 }, { 28, 17 }, { 29, 13 }, { 30, 10 }, { 31, 7 }, { 31, 3 }, { 32, 0 }, { 31, -3 }, { 31, -7 }, { 30, -10 }, { 29, -13 }, { 28, -17 }, { 26, -20 }, { 24, -23 }, { 22, -25 }, { 20, -28 }, { 17, -30 }, { 15, -32 }, { 12, -33 }, { 9, -34 }, { 6, -35 }, { 3, -36 }, { 0, -36 }, { -3, -36 }, { -6, -35 }, { -9, -34 }, { -12, -33 }, { -15, -32 }, { -17, -30 }, { -20, -28 }, { -22, -25 }, { -24, -23 }, { -26, -20 }, { -28, -17 }, { -29, -13 }, { -30, -10 }, { -31, -7 }, { -31, -3 }, { -32, 0 }, { -31, 3 }, { -31, 7 }, { -30, 10 }, { -29, 13 }, { -28, 17 }, { -26, 20 }, { -24, 23 }, { -22, 25 }, { -20, 28 }, { -17, 30 }, { -15, 32 }, { -12, 33 }, { -9, 34 }, { -6, 35 }, { -3, 36 } },
    { { 0, 54 }, { 4, 54 }, { 9, 53 }, { 13, 52 }, { 18, 50 }, { 22, 48 }, { 26, 45 }, { 30, 42 }, { 33, 38 }, { 37, 34 }, { 39, 30 }, { 42, 25 }, { 44, 20 }, { 45, 15 }, { 47, 10 }, { 47, 5 }, { 48, 0 }, { 47, -5 }, { 47, -10 }, { 45, -15 }, { 44, -20 }, { 42, -25 }, { 39, -30 }, { 37, -34 }, { 33, -38 }, { 30, -42 }, { 26, -45 }, { 22, -48 }, { 18, -50 }, { 13, -52 }, { 9, -53 }, { 4, -54 }, { 0, -54 }, { -4, -54 }, { -9, -53 }, { -13, -52 }, { -18, -50 }, { -22, -48 }, { -26, -45 }, { -30, -42 }, { -33, -38 }, { -37, -34 }, { -39, -30 }, { -42, -25 }, { -44, -20 }, { -45, -15 }, { -47, -10 }, { -47, -5 }, { -48, 0 }, { -47, 5 }, { -47, 10 }, { -45, 15 }, { -44, 20 }, { -42, 25 }, { -39, 30 }, { -37, 34 }, { -33, 38 }, { -30, 42 }, { -26, 45 }, { -22, 48 }, { -18, 50 }, { -13, 52 }, { -9, 53 }, { -4, 54 } },
    { { 0, 73 }, { 6, 72 }, { 12, 71 }, { 18, 69 }, { 24, 67 }, { 30, 64 }, { 35, 60 }, { 40, 56 }, { 45, 51 }, { 49, 46 }, { 53, 40 }, { 56, 34 }, { 59, 27 }, { 61, 21 }, { 62, 14 }, { 63, 7 }, { 64, 0 }, { 63, -7 }, { 62, -14 }, { 61, -21 }, { 59, -27 }, { 56, -34 }, { 53, -40 }, { 49, -46 }, { 45, -51 }, { 40, -56 }, { 35, -60 }, { 30, -64 }, { 24, -67 }, { 18, -69 }, { 12, -71 }, { 6, -72 }, { 0, -73 }, { -6, -72 }, { -12, -71 }, { -18, -69 }, { -24, -67 }, { -30, -64 }, { -35, -60 }, { -40, -56 }, { -45, -51 }, { -49, -46 }, { -53, -40 }, { -56, -34 }, { -59, -27 }, { -61, -21 }, { -62, -14 }, { -63, -7 }, { -64, 0 }, { -63, 7 }, { -62, 14 }, { -61, 21 }, { -59, 27 }, { -56, 34 }, { -53, 40 }, { -49, 46 }, { -45, 51 }, { -40, 56 }, { -35, 60 }, { -30, 64 }, { -24, 67 }, { -18, 69 }, { -12, 71 }, { -6, 72 } },
    { { 0, 91 }, { 7, 90 }, { 15, 89 }, { 23, 87 }, { 30, 84 }, { 37, 80 }, { 44, 75 }, { 50, 70 }, { 56, 64 }, { 61, 57 }, { 66, 50 }, { 70, 43 }, { 73, 34 }, { 76, 26 }, { 78, 17 }, { 79, 8 }, { 80, 0 }, { 79, -8 }, { 78, -17 }, { 76, -26 }, { 73, -34 }, { 70, -43 }, { 66, -50 }, { 61, -57 }, { 56, -64 }, { 50, -70 }, { 44, -75 }, { 37, -80 }, { 30, -84 }, { 23, -87 }, { 15, -89 }, { 7, -90 }, { 0, -91 }, { -7, -90 }, { -15, -89 }, { -23, -87 }, { -30, -84 }, { -37, -80 }, { -44, -75 }, { -50, -70 }, { -56, -64 }, { -61, -57 }, { -66, -50 }, { -70, -43 }, { -73, -34 }, { -76, -26 }, { -78, -17 }, { -79, -8 }, { -80, 0 }, { -79, 8 }, { -78, 17 }, { -76, 26 }, { -73, 34 }, { -70, 43 }, { -66, 50 }, { -61, 57 }, { -56, 64 }, { -50, 70 }, { -44, 75 }, { -37, 80 }, { -30, 84 }, { -23, 87 }, { -15, 89 }, { -7, 90 } },
    { { 0, 109 }, { 9, 109 }, { 18, 107 }, { 27, 104 }, { 36, 101 }, { 45, 96 }, { 53, 91 }, { 60, 84 }, { 67, 77 }, { 74, 69 }, { 79, 60 }, { 84, 51 }, { 88, 41 }, { 91, 31 }, { 94, 21 }, { 95, 10 }, { 96, 0 }, { 95, -10 }, { 94, -21 }, { 91, -31 }, { 88, -41 }, { 84, -51 }, { 79, -60 }, { 74, -69 }, { 67, -77 }, { 60, -84 }, { 53, -91 }, { 45, -96 }, { 36, -101 }, { 27, -104 }, { 18, -107 }, { 9, -109 }, { 0, -109 }, { -9, -109 }, { -18, -107 }, { -27, -104 }, { -36, -101 }, { -45, -96 }, { -53, -91 }, { -60, -84 }, { -67, -77 }, { -74, -69 }, { -79, -60 }, { -84, -51 }, { -88, -41 }, { -91, -31 }, { -94, -21 }, { -95, -10 }, { -96, 0 }, { -95, 10 }, { -94, 21 }, { -91, 31 }, { -88, 41 }, { -84, 51 }, { -79, 60 }, { -74, 69 }, { -67, 77 }, { -60, 84 }, { -53, 91 }, { -45, 96 }, { -36, 101 }, { -27, 104 }, { -18, 107 }, { -9, 109 } },
    { { 0, 128 }, { 10, 127 }, { 21, 125 }, { 32, 122 }, { 42, 118 }, { 52, 112 }, { 62, 106 }, { 70, 98 }, { 79, 90 }, { 86, 81 }, { 93, 71 }, { 98, 60 }, { 103, 48 }, { 107, 37 }, { 109, 24 }, { 111, 12 }, { 112, 0 }, { 111, -12 }, { 109, -24 }, { 107, -37 }, { 103, -48 }, { 98, -60 }, { 93, -71 }, { 86, -81 }, { 79, -90 }, { 70, -98 }, { 62, -106 }, { 52, -112 }, { 42, -118 }, { 32, -122 }, { 21, -125 }, { 10, -127 }, { 0, -128 }, { -10, -127 }, { -21, -125 }, { -32, -122 }, { -42, -118 }, { -52, -112 }, { -62, -106 }, { -70, -98 }, { -79, -90 }, { -86, -81 }, { -93, -71 }, { -98, -60 }, { -103, -48 }, { -107, -37 }, { -109, -24 }, { -111, -12 }, { -112, 0 }, { -111, 12 }, { -109, 24 }, { -107, 37 }, { -103, 48 }, { -98, 60 }, { -93, 71 }, { -86, 81 }, { -79, 90 }, { -70, 98 }, { -62, 106 }, { -52, 112 }, { -42, 118 }, { -32, 122 }, { -21, 125 }, { -10, 127 } },
    { { 0, 146 }, { 12, 145 }, { 24, 143 }, { 37, 139 }, { 48, 135 }, { 60, 128 }, { 71, 121 }, { 81, 113 }, { 90, 103 }, { 98, 92 }, { 106, 81 }, { 112, 68 }, { 118, 55 }, { 122, 42 }, { 125, 28 }, { 127, 14 }, { 128, 0 }, { 127, -14 }, { 125, -28 }, { 122, -42 }, { 118, -55 }, { 112, -68 }, { 106, -81 }, { 98, -92 }, { 90, -103 }, { 81, -113 }, { 71, -121 }, { 60, -128 }, { 48, -135 }, { 37, -139 }, { 24, -143 }, { 12, -145 }, { 0, -146 }, { -12, -145 }, { -24, -143 }, { -37, -139 }, { -48, -135 }, { -60, -128 }, { -71, -121 }, { -81, -113 }, { -90, -103 }, { -98, -92 }, { -106, -81 }, { -112, -68 }, { -118, -55 }, { -122, -42 }, { -125, -28 }, { -127, -14 }, { -128, 0 }, { -127, 14 }, { -125, 28 }, { -122, 42 }, { -118, 55 }, { -112, 68 }, { -106, 81 }, { -98, 92 }, { -90, 103 }, { -81, 113 }, { -71, 121 }, { -60, 128 }, { -48, 135 }, { -37, 139 }, { -24, 143 }, { -12, 145 } },
    { { 0, 164 }, { 14, 163 }, { 28, 161 }, { 41, 157 }, { 54, 151 }, { 67, 144 }, { 79, 136 }, { 91, 127 }, { 101, 116 }, { 111, 104 }, { 119, 91 }, { 126, 77 }, { 132, 62 }, { 137, 47 }, { 141, 32 }, { 143, 16 }, { 144, 0 }, { 143, -16 }, { 141, -32 }, { 137, -47 }, { 132, -62 }, { 126, -77 }, { 119, -91 }, { 111, -104 }, { 101, -116 }, { 91, -127 }, { 79, -136 }, { 67, -144 }, { 54, -151 }, { 41, -157 }, { 28, -161 }, { 14, -163 }, { 0, -164 }, { -14, -163 }, { -28, -161 }, { -41, -157 }, { -54, -151 }, { -67, -144 }, { -79, -136 }, { -91, -127 }, { -101, -116 }, { -111, -104 }, { -119, -91 }, { -126, -77 }, { -132, -62 }, { -137, -47 }, { -141, -32 }, { -143, -16 }, { -144, 0 }, { -143, 16 }, { -141, 32 }, { -137, 47 }, { -132, 62 }, { -126, 77 }, { -119, 91 }, { -111, 104 }, { -101, 116 }, { -91, 127 }, { -79, 136 }, { -67, 144 }, { -54, 151 }, { -41, 157 }, { -28, 161 }, { -14, 163 } },
    { { 0, 182 }, { 15, 181 }, { 31, 179 }, { 46, 174 }, { 61, 168 }, { 75, 161 }, { 88, 151 }, { 101, 141 }, { 113, 129 }, { 123, 115 }, { 132, 101 }, { 140, 86 }, { 147, 69 }, { 152, 52 }, { 156, 35 }, { 159, 17 }, { 160, 0 }, { 159, -17 }, { 156, -35 }, { 152, -52 }, { 147, -69 }, { 140, -86 }, { 132, -101 }, { 123, -115 }, { 113, -129 }, { 101, -141 }, { 88, -151 }, { 75, -161 }, { 61, -168 }, { 46, -174 }, { 31, -179 }, { 15, -181 }, { 0, -182 }, { -15, -181 }, { -31, -179 }, { -46, -174 }, { -61, -168 }, { -75, -161 }, { -88, -151 }, { -101, -141 }, { -113, -129 }, { -123, -115 }, { -132, -101 }, { -140, -86 }, { -147, -69 }, { -152, -52 }, { -156, -35 }, { -159, -17 }, { -160, 0 }, { -159, 17 }, { -156, 35 }, { -152, 52 }, { -147, 69 }, { -140, 86 }, { -132, 101 }, { -123, 115 }, { -113, 129 }, { -101, 141 }, { -88, 151 }, { -75, 161 }, { -61, 168 }, { -46, 174 }, { -31, 179 }, { -15, 181 } },
    { { 0, 201 }, { 17, 200 }, { 34, 197 }, { 51, 192 }, { 67, 185 }, { 82, 177 }, { 97, 167 }, { 111, 155 }, { 124, 142 }, { 136, 127 }, { 146, 111 }, { 155, 94 }, { 162, 76 }, { 168, 58 }, { 172, 39 }, { 175, 19 }, { 176, 0 }, { 175, -19 }, { 172, -39 }, { 168, -58 }, { 162, -76 }, { 155, -94 }, { 146, -111 }, { 136, -127 }, { 124, -142 }, { 111, -155 }, { 97, -167 }, { 82, -177 }, { 67, -185 }, { 51, -192 }, { 34, -197 }, { 17, -200 }, { 0, -201 }, { -17, -200 }, { -34, -197 }, { -51, -192 }, { -67, -185 }, { -82, -177 }, { -97, -167 }, { -111, -155 }, { -124, -142 }, { -136, -127 }, { -146, -111 }, { -155, -94 }, { -162, -76 }, { -168, -58 }, { -172, -39 }, { -175, -19 }, { -176, 0 }, { -175, 19 }, { -172, 39 }, { -168, 58 }, { -162, 76 }, { -155, 94 }, { -146, 111 }, { -136, 127 }, { -124, 142 }, { -111, 155 }, { -97, 167 }, { -82, 177 }, { -67, 185 }, { -51, 192 }, { -34, 197 }, { -17, 200 } },
    { { 0, 219 }, { 18, 218 }, { 37, 215 }, { 55, 209 }, { 73, 202 }, { 90, 193 }, { 106, 182 }, { 121, 169 }, { 135, 155 }, { 148, 139 }, { 159, 121 }, { 169, 103 }, { 177, 83 }, { 183, 63 }, { 188, 42 }, { 191, 21 }, { 192, 0 }, { 191, -21 }, { 188, -42 }, { 183, -63 }, { 177, -83 }, { 169, -103 }, { 159, -121 }, { 148, -139 }, { 135, -155 }, { 121, -169 }, { 106, -182 }, { 90, -193 }, { 73, -202 }, { 55, -209 }, { 37, -215 }, { 18, -218 }, { 0, -219 }, { -18, -218 }, { -37, -215 }, { -55, -209 }, { -73, -202 }, { -90, -193 }, { -106, -182 }, { -121, -169 }, { -135, -155 }, { -148, -139 }, { -159, -121 }, { -169, -103 }, { -177, -83 }, { -183, -63 }, { -188, -42 }, { -191, -21 }, { -192, 0 }, { -191, 21 }, { -188, 42 }, { -183, 63 }, { -177, 83 }, { -169, 103 }, { -159, 121 }, { -148, 139 }, { -135, 155 }, { -121, 169 }, { -106, 182 }, { -90, 193 }, { -73, 202 }, { -55, 209 }, { -37, 215 }, { -18, 218 } },
    { { 0, 237 }, { 20, 236 }, { 40, 232 }, { 60, 227 }, { 79, 219 }, { 97, 209 }, { 115, 197 }, { 131, 183 }, { 147, 168 }, { 160, 150 }, { 172, 131 }, { 183, 111 }, { 191, 90 }, { 198, 68 }, { 203, 46 }, { 206, 23 }, { 208, 0 }, { 206, -23 }, { 203, -46 }, { 198, -68 }, { 191, -90 }, { 183, -111 }, { 172, -131 }, { 160, -150 }, { 147, -168 }, { 131, -183 }, { 115, -197 }, { 97, -209 }, { 79, -219 }, { 60, -227 }, { 40, -232 }, { 20, -236 }, { 0, -237 }, { -20, -236 }, { -40, -232 }, { -60, -227 }, { -79, -219 }, { -97, -209 }, { -115, -197 }, { -131, -183 }, { -147, -168 }, { -160, -150 }, { -172, -131 }, { -183, -111 }, { -191, -90 }, { -198, -68 }, { -203, -46 }, { -206, -23 }, { -208, 0 }, { -206, 23 }, { -203, 46 }, { -198, 68 }, { -191, 90 }, { -183, 111 }, { -172, 131 }, { -160, 150 }, { -147, 168 }, { -131, 183 }, { -115, 197 }, { -97, 209 }, { -79, 219 }, { -60, 227 }, { -40, 232 }, { -20, 236 } },
    { { 0, 256 }, { 21, 254 }, { 43, 250 }, { 64, 244 }, { 85, 236 }, { 105, 225 }, { 124, 212 }, { 141, 197 }, { 158, 180 }, { 173, 162 }, { 186, 142 }, { 197, 120 }, { 206, 97 }, { 214, 74 }, { 219, 49 }, { 222, 25 }, { 224, 0 }, { 222, -25 }, { 219, -49 }, { 214, -74 }, { 206, -97 }, { 197, -120 }, { 186, -142 }, { 173, -162 }, { 158, -180 }, { 141, -197 }, { 124, -212 }, { 105, -225 }, { 85, -236 }, { 64, -244 }, { 43, -250 }, { 21, -254 }, { 0, -256 }, { -21, -254 }, { -43, -250 }, { -64, -244 }, { -85, -236 }, { -105, -225 }, { -124, -212 }, { -141, -197 }, { -158, -180 }, { -173, -162 }, { -186, -142 }, { -197, -120 }, { -206, -97 }, { -214, -74 }, { -219, -49 }, { -222, -25 }, { -224, 0 }, { -222, 25 }, { -219, 49 }, { -214, 74 }, { -206, 97 }, { -197, 120 }, { -186, 142 }, { -173, 162 }, { -158, 180 }, { -141, 197 }, { -124, 212 }, { -105, 225 }, { -85, 236 }, { -64, 244 }, { -43, 250 }, { -21, 254 } },
    { { 0, 274 }, { 23, 272 }, { 46, 268 }, { 69, 262 }, { 91, 253 }, { 113, 241 }, { 133, 227 }, { 152, 212 }, { 169, 193 }, { 185, 173 }, { 199, 152 }, { 211, 129 }, { 221, 104 }, { 229, 79 }, { 235, 53 }, { 238, 26 }, { 240, 0 }, { 238, -26 }, { 235, -53 }, { 229, -79 }, { 221, -104 }, { 211, -129 }, { 199, -152 }, { 185, -173 }, { 169, -193 }, { 152, -212 }, { 133, -227 }, { 113, -241 }, { 91, -253 }, { 69, -262 }, { 46, -268 }, { 23, -272 }, { 0, -274 }, { -23, -272 }, { -46, -268 }, { -69, -262 }, { -91, -253 }, { -113, -241 }, { -133, -227 }, { -152, -212 }, { -169, -193 }, { -185, -173 }, { -199, -152 }, { -211, -129 }, { -221, -104 }, { -229, -79 }, { -235, -53 }, { -238, -26 }, { -240, 0 }, { -238, 26 }, { -235, 53 }, { -229, 79 }, { -221, 104 }, { -211, 129 }, { -199, 152 }, { -185, 173 }, { -169, 193 }, { -152, 212 }, { -133, 227 }, { -113, 241 }, { -91, 253 }, { -69, 262 }, { -46, 268 }, { -23, 272 } },
};

static const AvspRound1VecS16 avsp_round1_air_weapon_motion_high[AVSP_ROUND1_AIR_WEAPON_HIGH_TABLE_COUNT][AVSP_ROUND1_AIR_WEAPON_DIRECTION_COUNT] =
{
    { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } },
    { { 0, 292 }, { 25, 291 }, { 49, 286 }, { 74, 279 }, { 97, 270 }, { 120, 257 }, { 142, 243 }, { 162, 226 }, { 180, 206 }, { 197, 185 }, { 212, 162 }, { 225, 137 }, { 236, 111 }, { 244, 84 }, { 250, 57 }, { 254, 28 }, { 256, 0 }, { 254, -28 }, { 250, -57 }, { 244, -84 }, { 236, -111 }, { 225, -137 }, { 212, -162 }, { 197, -185 }, { 180, -206 }, { 162, -226 }, { 142, -243 }, { 120, -257 }, { 97, -270 }, { 74, -279 }, { 49, -286 }, { 25, -291 }, { 0, -292 }, { -25, -291 }, { -49, -286 }, { -74, -279 }, { -97, -270 }, { -120, -257 }, { -142, -243 }, { -162, -226 }, { -180, -206 }, { -197, -185 }, { -212, -162 }, { -225, -137 }, { -236, -111 }, { -244, -84 }, { -250, -57 }, { -254, -28 }, { -256, 0 }, { -254, 28 }, { -250, 57 }, { -244, 84 }, { -236, 111 }, { -225, 137 }, { -212, 162 }, { -197, 185 }, { -180, 206 }, { -162, 226 }, { -142, 243 }, { -120, 257 }, { -97, 270 }, { -74, 279 }, { -49, 286 }, { -25, 291 } },
    { { 0, 585 }, { 50, 582 }, { 99, 573 }, { 148, 559 }, { 195, 540 }, { 241, 515 }, { 284, 486 }, { 324, 452 }, { 361, 413 }, { 395, 370 }, { 425, 324 }, { 451, 275 }, { 472, 223 }, { 489, 169 }, { 501, 114 }, { 509, 57 }, { 512, 0 }, { 509, -57 }, { 501, -114 }, { 489, -169 }, { 472, -223 }, { 451, -275 }, { 425, -324 }, { 395, -370 }, { 361, -413 }, { 324, -452 }, { 284, -486 }, { 241, -515 }, { 195, -540 }, { 148, -559 }, { 99, -573 }, { 50, -582 }, { 0, -585 }, { -50, -582 }, { -99, -573 }, { -148, -559 }, { -195, -540 }, { -241, -515 }, { -284, -486 }, { -324, -452 }, { -361, -413 }, { -395, -370 }, { -425, -324 }, { -451, -275 }, { -472, -223 }, { -489, -169 }, { -501, -114 }, { -509, -57 }, { -512, 0 }, { -509, 57 }, { -501, 114 }, { -489, 169 }, { -472, 223 }, { -451, 275 }, { -425, 324 }, { -395, 370 }, { -361, 413 }, { -324, 452 }, { -284, 486 }, { -241, 515 }, { -195, 540 }, { -148, 559 }, { -99, 573 }, { -50, 582 } },
    { { 0, 877 }, { 75, 873 }, { 149, 860 }, { 222, 838 }, { 293, 810 }, { 361, 773 }, { 426, 729 }, { 486, 678 }, { 542, 620 }, { 593, 556 }, { 638, 487 }, { 676, 413 }, { 708, 335 }, { 734, 254 }, { 752, 171 }, { 764, 85 }, { 768, 0 }, { 764, -85 }, { 752, -171 }, { 734, -254 }, { 708, -335 }, { 676, -413 }, { 638, -487 }, { 593, -556 }, { 542, -620 }, { 486, -678 }, { 426, -729 }, { 361, -773 }, { 293, -810 }, { 222, -838 }, { 149, -860 }, { 75, -873 }, { 0, -877 }, { -75, -873 }, { -149, -860 }, { -222, -838 }, { -293, -810 }, { -361, -773 }, { -426, -729 }, { -486, -678 }, { -542, -620 }, { -593, -556 }, { -638, -487 }, { -676, -413 }, { -708, -335 }, { -734, -254 }, { -752, -171 }, { -764, -85 }, { -768, 0 }, { -764, 85 }, { -752, 171 }, { -734, 254 }, { -708, 335 }, { -676, 413 }, { -638, 487 }, { -593, 556 }, { -542, 620 }, { -486, 678 }, { -426, 729 }, { -361, 773 }, { -293, 810 }, { -222, 838 }, { -149, 860 }, { -75, 873 } },
    { { 0, 1170 }, { 100, 1164 }, { 199, 1146 }, { 296, 1118 }, { 391, 1080 }, { 482, 1030 }, { 568, 972 }, { 649, 904 }, { 723, 827 }, { 791, 741 }, { 850, 649 }, { 902, 551 }, { 945, 446 }, { 978, 339 }, { 1003, 228 }, { 1018, 114 }, { 1024, 0 }, { 1018, -114 }, { 1003, -228 }, { 978, -339 }, { 945, -446 }, { 902, -551 }, { 850, -649 }, { 791, -741 }, { 723, -827 }, { 649, -904 }, { 568, -972 }, { 482, -1030 }, { 391, -1080 }, { 296, -1118 }, { 199, -1146 }, { 100, -1164 }, { 0, -1170 }, { -100, -1164 }, { -199, -1146 }, { -296, -1118 }, { -391, -1080 }, { -482, -1030 }, { -568, -972 }, { -649, -904 }, { -723, -827 }, { -791, -741 }, { -850, -649 }, { -902, -551 }, { -945, -446 }, { -978, -339 }, { -1003, -228 }, { -1018, -114 }, { -1024, 0 }, { -1018, 114 }, { -1003, 228 }, { -978, 339 }, { -945, 446 }, { -902, 551 }, { -850, 649 }, { -791, 741 }, { -723, 827 }, { -649, 904 }, { -568, 972 }, { -482, 1030 }, { -391, 1080 }, { -296, 1118 }, { -199, 1146 }, { -100, 1164 } },
    { { 0, 1462 }, { 125, 1455 }, { 249, 1433 }, { 370, 1398 }, { 488, 1350 }, { 602, 1288 }, { 710, 1215 }, { 811, 1130 }, { 904, 1033 }, { 989, 927 }, { 1063, 811 }, { 1127, 688 }, { 1181, 558 }, { 1223, 423 }, { 1254, 285 }, { 1273, 143 }, { 1280, 0 }, { 1273, -143 }, { 1254, -285 }, { 1223, -423 }, { 1181, -558 }, { 1127, -688 }, { 1063, -811 }, { 989, -927 }, { 904, -1033 }, { 811, -1130 }, { 710, -1215 }, { 602, -1288 }, { 488, -1350 }, { 370, -1398 }, { 249, -1433 }, { 125, -1455 }, { 0, -1462 }, { -125, -1455 }, { -249, -1433 }, { -370, -1398 }, { -488, -1350 }, { -602, -1288 }, { -710, -1215 }, { -811, -1130 }, { -904, -1033 }, { -989, -927 }, { -1063, -811 }, { -1127, -688 }, { -1181, -558 }, { -1223, -423 }, { -1254, -285 }, { -1273, -143 }, { -1280, 0 }, { -1273, 143 }, { -1254, 285 }, { -1223, 423 }, { -1181, 558 }, { -1127, 688 }, { -1063, 811 }, { -989, 927 }, { -904, 1033 }, { -811, 1130 }, { -710, 1215 }, { -602, 1288 }, { -488, 1350 }, { -370, 1398 }, { -249, 1433 }, { -125, 1455 } },
    { { 0, 1755 }, { 150, 1746 }, { 299, 1720 }, { 445, 1677 }, { 586, 1620 }, { 723, 1546 }, { 852, 1458 }, { 973, 1356 }, { 1085, 1240 }, { 1187, 1112 }, { 1276, 974 }, { 1353, 826 }, { 1417, 670 }, { 1468, 508 }, { 1505, 342 }, { 1528, 171 }, { 1536, 0 }, { 1528, -171 }, { 1505, -342 }, { 1468, -508 }, { 1417, -670 }, { 1353, -826 }, { 1276, -974 }, { 1187, -1112 }, { 1085, -1240 }, { 973, -1356 }, { 852, -1458 }, { 723, -1546 }, { 586, -1620 }, { 445, -1677 }, { 299, -1720 }, { 150, -1746 }, { 0, -1755 }, { -150, -1746 }, { -299, -1720 }, { -445, -1677 }, { -586, -1620 }, { -723, -1546 }, { -852, -1458 }, { -973, -1356 }, { -1085, -1240 }, { -1187, -1112 }, { -1276, -974 }, { -1353, -826 }, { -1417, -670 }, { -1468, -508 }, { -1505, -342 }, { -1528, -171 }, { -1536, 0 }, { -1528, 171 }, { -1505, 342 }, { -1468, 508 }, { -1417, 670 }, { -1353, 826 }, { -1276, 974 }, { -1187, 1112 }, { -1085, 1240 }, { -973, 1356 }, { -852, 1458 }, { -723, 1546 }, { -586, 1620 }, { -445, 1677 }, { -299, 1720 }, { -150, 1746 } },
    { { 0, 2048 }, { 175, 2037 }, { 349, 2007 }, { 519, 1957 }, { 684, 1890 }, { 843, 1804 }, { 994, 1701 }, { 1135, 1583 }, { 1266, 1447 }, { 1385, 1298 }, { 1488, 1136 }, { 1578, 964 }, { 1653, 782 }, { 1712, 593 }, { 1756, 399 }, { 1782, 200 }, { 1792, 0 }, { 1782, -200 }, { 1756, -399 }, { 1712, -593 }, { 1653, -782 }, { 1578, -964 }, { 1488, -1136 }, { 1385, -1298 }, { 1266, -1447 }, { 1135, -1583 }, { 994, -1701 }, { 843, -1804 }, { 684, -1890 }, { 519, -1957 }, { 349, -2007 }, { 175, -2037 }, { 0, -2048 }, { -175, -2037 }, { -349, -2007 }, { -519, -1957 }, { -684, -1890 }, { -843, -1804 }, { -994, -1701 }, { -1135, -1583 }, { -1266, -1447 }, { -1385, -1298 }, { -1488, -1136 }, { -1578, -964 }, { -1653, -782 }, { -1712, -593 }, { -1756, -399 }, { -1782, -200 }, { -1792, 0 }, { -1782, 200 }, { -1756, 399 }, { -1712, 593 }, { -1653, 782 }, { -1578, 964 }, { -1488, 1136 }, { -1385, 1298 }, { -1266, 1447 }, { -1135, 1583 }, { -994, 1701 }, { -843, 1804 }, { -684, 1890 }, { -519, 1957 }, { -349, 2007 }, { -175, 2037 } },
    { { 0, 2340 }, { 200, 2328 }, { 399, 2293 }, { 593, 2237 }, { 782, 2160 }, { 964, 2061 }, { 1136, 1944 }, { 1298, 1809 }, { 1447, 1654 }, { 1583, 1483 }, { 1701, 1298 }, { 1804, 1102 }, { 1890, 893 }, { 1957, 678 }, { 2007, 456 }, { 2037, 229 }, { 2048, 0 }, { 2037, -229 }, { 2007, -456 }, { 1957, -678 }, { 1890, -893 }, { 1804, -1102 }, { 1701, -1298 }, { 1583, -1483 }, { 1447, -1654 }, { 1298, -1809 }, { 1136, -1944 }, { 964, -2061 }, { 782, -2160 }, { 593, -2237 }, { 399, -2293 }, { 200, -2328 }, { 0, -2340 }, { -200, -2328 }, { -399, -2293 }, { -593, -2237 }, { -782, -2160 }, { -964, -2061 }, { -1136, -1944 }, { -1298, -1809 }, { -1447, -1654 }, { -1583, -1483 }, { -1701, -1298 }, { -1804, -1102 }, { -1890, -893 }, { -1957, -678 }, { -2007, -456 }, { -2037, -229 }, { -2048, 0 }, { -2037, 229 }, { -2007, 456 }, { -1957, 678 }, { -1890, 893 }, { -1804, 1102 }, { -1701, 1298 }, { -1583, 1483 }, { -1447, 1654 }, { -1298, 1809 }, { -1136, 1944 }, { -964, 2061 }, { -782, 2160 }, { -593, 2237 }, { -399, 2293 }, { -200, 2328 } },
    { { 0, 2633 }, { 225, 2619 }, { 448, 2580 }, { 667, 2516 }, { 879, 2430 }, { 1085, 2319 }, { 1278, 2187 }, { 1460, 2035 }, { 1628, 1861 }, { 1780, 1668 }, { 1914, 1461 }, { 2029, 1240 }, { 2126, 1005 }, { 2202, 763 }, { 2257, 513 }, { 2292, 257 }, { 2304, 0 }, { 2292, -257 }, { 2257, -513 }, { 2202, -763 }, { 2126, -1005 }, { 2029, -1240 }, { 1914, -1461 }, { 1780, -1668 }, { 1628, -1861 }, { 1460, -2035 }, { 1278, -2187 }, { 1085, -2319 }, { 879, -2430 }, { 667, -2516 }, { 448, -2580 }, { 225, -2619 }, { 0, -2633 }, { -225, -2619 }, { -448, -2580 }, { -667, -2516 }, { -879, -2430 }, { -1085, -2319 }, { -1278, -2187 }, { -1460, -2035 }, { -1628, -1861 }, { -1780, -1668 }, { -1914, -1461 }, { -2029, -1240 }, { -2126, -1005 }, { -2202, -763 }, { -2257, -513 }, { -2292, -257 }, { -2304, 0 }, { -2292, 257 }, { -2257, 513 }, { -2202, 763 }, { -2126, 1005 }, { -2029, 1240 }, { -1914, 1461 }, { -1780, 1668 }, { -1628, 1861 }, { -1460, 2035 }, { -1278, 2187 }, { -1085, 2319 }, { -879, 2430 }, { -667, 2516 }, { -448, 2580 }, { -225, 2619 } },
    { { 0, 2925 }, { 250, 2910 }, { 498, 2867 }, { 741, 2796 }, { 977, 2700 }, { 1205, 2577 }, { 1420, 2430 }, { 1622, 2261 }, { 1809, 2067 }, { 1978, 1854 }, { 2126, 1623 }, { 2255, 1377 }, { 2362, 1117 }, { 2446, 847 }, { 2508, 570 }, { 2546, 286 }, { 2560, 0 }, { 2546, -286 }, { 2508, -570 }, { 2446, -847 }, { 2362, -1117 }, { 2255, -1377 }, { 2126, -1623 }, { 1978, -1854 }, { 1809, -2067 }, { 1622, -2261 }, { 1420, -2430 }, { 1205, -2577 }, { 977, -2700 }, { 741, -2796 }, { 498, -2867 }, { 250, -2910 }, { 0, -2925 }, { -250, -2910 }, { -498, -2867 }, { -741, -2796 }, { -977, -2700 }, { -1205, -2577 }, { -1420, -2430 }, { -1622, -2261 }, { -1809, -2067 }, { -1978, -1854 }, { -2126, -1623 }, { -2255, -1377 }, { -2362, -1117 }, { -2446, -847 }, { -2508, -570 }, { -2546, -286 }, { -2560, 0 }, { -2546, 286 }, { -2508, 570 }, { -2446, 847 }, { -2362, 1117 }, { -2255, 1377 }, { -2126, 1623 }, { -1978, 1854 }, { -1809, 2067 }, { -1622, 2261 }, { -1420, 2430 }, { -1205, 2577 }, { -977, 2700 }, { -741, 2796 }, { -498, 2867 }, { -250, 2910 } },
    { { 0, 3218 }, { 275, 3201 }, { 548, 3153 }, { 816, 3076 }, { 1075, 2970 }, { 1326, 2834 }, { 1562, 2673 }, { 1784, 2487 }, { 1990, 2274 }, { 2176, 2039 }, { 2339, 1785 }, { 2480, 1515 }, { 2598, 1228 }, { 2691, 932 }, { 2759, 627 }, { 2801, 315 }, { 2816, 0 }, { 2801, -315 }, { 2759, -627 }, { 2691, -932 }, { 2598, -1228 }, { 2480, -1515 }, { 2339, -1785 }, { 2176, -2039 }, { 1990, -2274 }, { 1784, -2487 }, { 1562, -2673 }, { 1326, -2834 }, { 1075, -2970 }, { 816, -3076 }, { 548, -3153 }, { 275, -3201 }, { 0, -3218 }, { -275, -3201 }, { -548, -3153 }, { -816, -3076 }, { -1075, -2970 }, { -1326, -2834 }, { -1562, -2673 }, { -1784, -2487 }, { -1990, -2274 }, { -2176, -2039 }, { -2339, -1785 }, { -2480, -1515 }, { -2598, -1228 }, { -2691, -932 }, { -2759, -627 }, { -2801, -315 }, { -2816, 0 }, { -2801, 315 }, { -2759, 627 }, { -2691, 932 }, { -2598, 1228 }, { -2480, 1515 }, { -2339, 1785 }, { -2176, 2039 }, { -1990, 2274 }, { -1784, 2487 }, { -1562, 2673 }, { -1326, 2834 }, { -1075, 2970 }, { -816, 3076 }, { -548, 3153 }, { -275, 3201 } },
    { { 0, 3510 }, { 300, 3492 }, { 598, 3440 }, { 890, 3355 }, { 1173, 3240 }, { 1446, 3092 }, { 1704, 2916 }, { 1947, 2713 }, { 2171, 2481 }, { 2374, 2225 }, { 2552, 1948 }, { 2706, 1653 }, { 2835, 1340 }, { 2936, 1017 }, { 3010, 684 }, { 3056, 343 }, { 3072, 0 }, { 3056, -343 }, { 3010, -684 }, { 2936, -1017 }, { 2835, -1340 }, { 2706, -1653 }, { 2552, -1948 }, { 2374, -2225 }, { 2171, -2481 }, { 1947, -2713 }, { 1704, -2916 }, { 1446, -3092 }, { 1173, -3240 }, { 890, -3355 }, { 598, -3440 }, { 300, -3492 }, { 0, -3510 }, { -300, -3492 }, { -598, -3440 }, { -890, -3355 }, { -1173, -3240 }, { -1446, -3092 }, { -1704, -2916 }, { -1947, -2713 }, { -2171, -2481 }, { -2374, -2225 }, { -2552, -1948 }, { -2706, -1653 }, { -2835, -1340 }, { -2936, -1017 }, { -3010, -684 }, { -3056, -343 }, { -3072, 0 }, { -3056, 343 }, { -3010, 684 }, { -2936, 1017 }, { -2835, 1340 }, { -2706, 1653 }, { -2552, 1948 }, { -2374, 2225 }, { -2171, 2481 }, { -1947, 2713 }, { -1704, 2916 }, { -1446, 3092 }, { -1173, 3240 }, { -890, 3355 }, { -598, 3440 }, { -300, 3492 } },
};

static const AvspRound1WeaponChildSpawnSpec avsp_round1_air_weapon_child_spawn_normal[AVSP_ROUND1_WEAPON_CHILD_SPAWN_COUNT] =
{
    { 32, -16, -16, 0u },
    { -48, -8, -8, 0u },
    { -32, 16, 16, 0u },
    { 48, 8, 8, 0u },
    { 0, 0, 0, 1u },
};

static const AvspRound1WeaponChildSpawnSpec avsp_round1_air_weapon_child_spawn_collision[AVSP_ROUND1_WEAPON_CHILD_SPAWN_COUNT] =
{
    { 64, -16, -16, 2u },
    { 48, 16, 16, 2u },
    { 32, -8, -8, 2u },
    { 16, 8, 8, 2u },
    { 0, 0, 0, 1u },
};

static const AvspRound1AirWeaponProjectileSpec avsp_round1_air_weapon_projectile =
{
    3, 0u, 2u, 4u, 6u,
    9u,
    5u,
    1u,
    4u,
    2u,
    5u, 0xc0u, 0x8000u,
    0x030382UL,
    0x0002fc3cUL,
    24u,
    73u,
    1u
};

static const AvspRound1WeaponChildSpawnSpec avsp_round1_weapon_child_spawn_normal[AVSP_ROUND1_WEAPON_CHILD_SPAWN_COUNT] =
{
    { 32, -16, -16, 0u },
    { -48, -16, -16, 0u },
    { -32, 16, 16, 0u },
    { 48, 16, 16, 0u },
    { 0, 0, 0, 1u },
};

static const AvspRound1WeaponChildSpawnSpec avsp_round1_weapon_child_spawn_collision[AVSP_ROUND1_WEAPON_CHILD_SPAWN_COUNT] =
{
    { 64, -16, -16, 2u },
    { 48, 16, 16, 2u },
    { 32, -8, -8, 2u },
    { 16, 8, 8, 2u },
    { 0, 0, 0, 1u },
};

static const AvspRound1WeaponChildSequenceSpec avsp_round1_weapon_child_sequences[AVSP_ROUND1_WEAPON_CHILD_VARIANT_COUNT] =
{
    { 17u, { { 2u, 0, 0x0003078cUL, 0x00030a48UL, 0u, 1u }, { 2u, 0, 0x0003079cUL, 0x00030a56UL, 0u, 1u }, { 2u, 0, 0x000307acUL, 0x00030a64UL, 0u, 1u }, { 2u, 0, 0x000307bcUL, 0x00030a72UL, 0u, 2u }, { 2u, 0, 0x000307ccUL, 0x00030a80UL, 0u, 2u }, { 2u, 0, 0x000307dcUL, 0x00030a8eUL, 0u, 2u }, { 2u, 0, 0x000307ecUL, 0x00030a9cUL, 0u, 2u }, { 2u, 0, 0x000307fcUL, 0x00030aaaUL, 0u, 2u }, { 2u, 0, 0x0003080cUL, 0x00030ab8UL, 0u, 0u }, { 2u, 0, 0x0003081cUL, 0x00030ac6UL, 0u, 0u }, { 2u, 0, 0x0003082cUL, 0x00030ad4UL, 0u, 0u }, { 2u, 0, 0x0003083cUL, 0x00030ae2UL, 0u, 0u }, { 2u, 0, 0x0003084cUL, 0x00030af0UL, 0u, 0u }, { 2u, 0, 0x0003085cUL, 0x00030afeUL, 0u, 0u }, { 2u, 0, 0x0003086cUL, 0x00030b0cUL, 0u, 0u }, { 2u, 0, 0x0003087cUL, 0x00030b1aUL, 0u, 0u }, { 2u, -32768, 0x0003088cUL, 0x00030b28UL, 0u, 0u } } },
    { 10u, { { 4u, 0, 0x000308a0UL, 0x00030b36UL, 0u, 1u }, { 4u, 0, 0x000308b0UL, 0x00030b44UL, 0u, 3u }, { 4u, 0, 0x000308c0UL, 0x00030b52UL, 0u, 3u }, { 4u, 0, 0x000308d0UL, 0x00030b60UL, 0u, 4u }, { 4u, 0, 0x000308e0UL, 0x00030b78UL, 0u, 0u }, { 4u, 0, 0x000308f0UL, 0x00030b90UL, 0u, 0u }, { 4u, 0, 0x00030900UL, 0x00030b9eUL, 0u, 0u }, { 4u, 0, 0x00030910UL, 0x00030bacUL, 0u, 0u }, { 4u, 0, 0x00030920UL, 0x00030bbaUL, 0u, 0u }, { 4u, -32768, 0x00030930UL, 0x00030bc8UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 16u, { { 2u, 0, 0x00030944UL, 0x00030bd6UL, 0u, 1u }, { 2u, 0, 0x00030954UL, 0x00030be4UL, 0u, 5u }, { 2u, 0, 0x00030964UL, 0x00030bf2UL, 0u, 5u }, { 2u, 0, 0x00030974UL, 0x00030c00UL, 0u, 5u }, { 2u, 0, 0x00030984UL, 0x00030c0eUL, 0u, 6u }, { 2u, 0, 0x00030994UL, 0x00030c1cUL, 0u, 6u }, { 2u, 0, 0x000309a4UL, 0x00030c2aUL, 0u, 6u }, { 2u, 0, 0x000309b4UL, 0x00030c38UL, 0u, 6u }, { 2u, 0, 0x000309c4UL, 0x00030c46UL, 0u, 0u }, { 2u, 0, 0x000309d4UL, 0x00030c54UL, 0u, 0u }, { 2u, 0, 0x000309e4UL, 0x00030c62UL, 0u, 0u }, { 2u, 0, 0x000309f4UL, 0x00030c70UL, 0u, 0u }, { 2u, 0, 0x00030a04UL, 0x00030c7eUL, 0u, 0u }, { 2u, 0, 0x00030a14UL, 0x00030c8cUL, 0u, 0u }, { 2u, 0, 0x00030a24UL, 0x00030c9aUL, 0u, 0u }, { 2u, -32768, 0x00030a34UL, 0x00030ca8UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
};

static const AvspRound1WeaponProjectileSpec avsp_round1_weapon_projectile =
{
    0u, 2u, 4u, 6u, 0x50, 0x0220u, 0x10, 0x0120u,
    0, 4,
    5u,
    1u,
    6u, 0x8000u,
    0x02f870UL, 0x0306feUL,
    0x0002fc3cUL,
    0x00030cb6UL,
    127u,
    31u
};

static const AvspRound1CollisionBoxSpec avsp_round1_weapon_parent_attack_boxes[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =
{
    { 0, 0, 0u, 0u, 0, 0u, 0, 0u, 0u },
    { 0, -8, 4u, 12u, 0, 8u, 0, 8u, 25u },
    { 70, 31, 52u, 229u, -86, 141u, -125, 57u, 130u },
};

static const AvspRound1CollisionBoxSpec avsp_round1_weapon_child_attack_boxes[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =
{
    { 0, 0, 0u, 0u, 0, 0u, 0, 0u, 0u },
    { 0, 10, 16u, 10u, 0, 8u, 1, 8u, 14u },
    { 0, 24, 16u, 24u, 0, 8u, 1, 8u, 14u },
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

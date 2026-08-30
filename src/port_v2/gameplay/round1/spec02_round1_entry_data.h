#ifndef AVSP_SPEC02_ROUND1_ENTRY_DATA_H
#define AVSP_SPEC02_ROUND1_ENTRY_DATA_H

/* contract_sha256=75689cc3c7bc11a6178c621c004f58cca041ffc174f7df8354aeb4b83b4a9293 */
/* fixtures_sha256=8554c61db6b1b4e8e64ab6b726c66f2e87539f29084d43c529e119fddc37dcd8 */
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

static const AvspRound1CoffeeStageSetupSpec avsp_round1_coffee_stage_setup =
{
    2, 1u, 0x1Cu, 14, 25u, 14u, 22u, -4, -8, 0, 0x18u, 0, 0,
    8, 16, 0x8DEFu, 0xA998u, 8
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
    12u, 16u, 20u, 24u, 28u, 36u
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

static const AvspRound1Class1fSourceHitSpec avsp_round1_class1f_source_hit =
{
    0x0202u, 0x0002u, 0x0200u, 0x0012e04cUL, 0x001308a6UL,
    0x36u, 2u, 0x15u, 8u, 4u, 1u, 0u, 0u,
    { 0x0200u, 0x0202u, 0x0204u, 0x0206u, 0x0208u, 0x020Au },
    114688L, 0L, 753664L, -32768L,
    131072L, -4096L, 262144L, -49152L,
    3u, 0x37u, 0x38u, 0x39u, 0x17u,
    0xEDD9u, 0xC9A2u, 2u, 0u,
    { 10u, 10u, 10u, 10u, 40u, 40u, 40u, 40u, 60u, 60u, 60u, 90u, 90u, 90u, 120u, 120u },
    10u, 0u, 6u,
    {
        { 1u, 0, 0x0012e04cUL, 0x001308a6UL, 0u, 0u },
        { 1u, 0, 0x0012e05cUL, 0x0013088eUL, 0u, 0u },
        { 1u, 0, 0x0012e06cUL, 0x001308c4UL, 0u, 0u },
        { 1u, 0, 0x0012e07cUL, 0x0013088eUL, 0u, 0u },
        { 1u, 0, 0x0012e08cUL, 0x001308e2UL, 0u, 0u },
        { 1u, -32768, 0x0012e09cUL, 0x0013088eUL, 0u, 0u },
    },
    { 4095u, -32768, 0x0012ddb0UL, 0x00130346UL, 7u, 0u },
    { 4095u, -32768, 0x0012dd9cUL, 0x00130294UL, 0u, 0u },
    { 4095u, -32768, 0x0012ddb0UL, 0x00130346UL, 7u, 0u },
    11u,
    {
        { 3u, 0, 0x0012de38UL, 0x00130346UL, 0u, 0u },
        { 3u, 0, 0x0012de48UL, 0x00130354UL, 0u, 0u },
        { 3u, 0, 0x0012de58UL, 0x00130346UL, 0u, 0u },
        { 3u, 0, 0x0012de68UL, 0x00130354UL, 0u, 0u },
        { 2u, 0, 0x0012de78UL, 0x00130362UL, 0u, 0u },
        { 2u, 0, 0x0012de88UL, 0x00130370UL, 0u, 0u },
        { 2u, 0, 0x0012de98UL, 0x001303a8UL, 0u, 0u },
        { 2u, 0, 0x0012dea8UL, 0x0012fae8UL, 0u, 0u },
        { 2u, 0, 0x0012deb8UL, 0x0012fb10UL, 0u, 0u },
        { 2u, 0, 0x0012dec8UL, 0x0012fb38UL, 0u, 0u },
        { 8u, -32768, 0x0012ded8UL, 0x0012f5deUL, 0u, 0u },
    },
    0x0200u, 0x0000u, 0x1600u, 0u,
    0u, 0u, 1u, 1u, 1u, 2u, 1u,
    582, 310, 944, 320,
};

static const AvspRound1Class1fSourceKoSpec avsp_round1_class1f_source_ko =
{
    0x0400u, 0x0402u, 0x0404u, 0x0600u,
    { 0x0000u, 0x0200u, 0x0400u, 0x0600u },
    2u, 0x36u, 0u, 0x15u, 8u, 3u, 60u, 6u,
    114688L, 0L, 622592L, -20480L,
    131072L, 0L, 262144L, -49152L,
    {
        { 1u, 0, 0x0012e04cUL, 0x001308a6UL, 0u, 0u },
        { 1u, 0, 0x0012e05cUL, 0x0013088eUL, 0u, 0u },
        { 1u, 0, 0x0012e06cUL, 0x001308c4UL, 0u, 0u },
        { 1u, 0, 0x0012e07cUL, 0x0013088eUL, 0u, 0u },
        { 1u, 0, 0x0012e08cUL, 0x001308e2UL, 0u, 0u },
        { 1u, -32768, 0x0012e09cUL, 0x0013088eUL, 0u, 0u },
    },
    { 4095u, -32768, 0x0012ddb0UL, 0x00130346UL, 7u, 0u },
    { 4095u, -32768, 0x0012dd9cUL, 0x00130294UL, 0u, 0u },
};

static const AvspRound1RecurringSpawnSpec avsp_round1_recurring_spawn =
{
    0x0200u, 0x0202u, 0x0204u,
    3900u, 60u, 1200u, 2100u, 640u, 208u, 720, 9u,
    { 0u, 35u, 55u, 70u },
    0x06u, 8u, 7u, 3u, 31u,
    -48, 1008, 976, 344, 344, 4u, 0u,
    1u, 0u, 0xC580u, 0x44, 24u, 0x0404u,
    0x0402u, 0x0000u, -1, 1u,
    1u, 1u
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

static const AvspRound1Class1fActionRecordSpec avsp_round1_class1f_inner8_records[AVSP_ROUND1_CLASS1F_INNER8_RECORD_COUNT] =
{
    { 0x0012d404UL, 0x0012d414UL, 0x0012f794UL, 6u, 12, 1u, 0u, 12u },
    { 0x0012d414UL, 0x0012d424UL, 0x0012f762UL, 6u, 15, 1u, 0u, 15u },
    { 0x0012d424UL, 0x0012d434UL, 0x0012f72aUL, 6u, 12, 1u, 0u, 12u },
    { 0x0012d434UL, 0x0012d444UL, 0x0012f712UL, 6u, 15, 1u, 0u, 15u },
    { 0x0012d444UL, 0x0012d454UL, 0x0012f6daUL, 6u, 12, 1u, 0u, 12u },
    { 0x0012d454UL, 0x0012d464UL, 0x0012f6a8UL, 6u, 12, 1u, 0u, 12u },
    { 0x0012d464UL, 0x0012d474UL, 0x0012f670UL, 6u, 12, 1u, 0u, 12u },
    { 0x0012d474UL, 0x0012d404UL, 0x0012f638UL, 6u, -32750, 1u, 0u, 18u },
    { 0x0012d488UL, 0x0012d498UL, 0x0012f7ccUL, 6u, 19, 2u, 0u, 19u },
    { 0x0012d498UL, 0x0012d4a8UL, 0x0012f7e4UL, 6u, 267, 2u, 0u, 11u },
    { 0x0012d4a8UL, 0x0012d4b8UL, 0x0012f7fcUL, 6u, 527, 2u, 0u, 15u },
    { 0x0012d4b8UL, 0x0012d4c8UL, 0x0012f814UL, 6u, 793, 2u, 0u, 25u },
    { 0x0012d4c8UL, 0x0012d4d8UL, 0x0012f82cUL, 6u, 1047, 2u, 0u, 23u },
    { 0x0012d4d8UL, 0x0012d4e8UL, 0x0012f85eUL, 6u, 1292, 2u, 0u, 12u },
    { 0x0012d4e8UL, 0x0012d4f8UL, 0x0012f890UL, 6u, 1540, 2u, 0u, 4u },
    { 0x0012d4f8UL, 0x0012d488UL, 0x0012f8b8UL, 6u, -30958, 2u, 0u, 18u },
    { 0x0012d50cUL, 0x0012d51cUL, 0x0012f8b8UL, 6u, 11, 2u, 0u, 11u },
    { 0x0012d51cUL, 0x0012d52cUL, 0x0012f890UL, 6u, 11, 2u, 0u, 11u },
    { 0x0012d52cUL, 0x0012d53cUL, 0x0012f85eUL, 6u, 11, 2u, 0u, 11u },
    { 0x0012d53cUL, 0x0012d54cUL, 0x0012f82cUL, 6u, 11, 2u, 0u, 11u },
    { 0x0012d54cUL, 0x0012d55cUL, 0x0012f814UL, 6u, 11, 2u, 0u, 11u },
    { 0x0012d55cUL, 0x0012d56cUL, 0x0012f7fcUL, 6u, 11, 2u, 0u, 11u },
    { 0x0012d56cUL, 0x0012d57cUL, 0x0012f7e4UL, 6u, 11, 2u, 0u, 11u },
    { 0x0012d57cUL, 0x0012d50cUL, 0x0012f7ccUL, 6u, -32757, 2u, 0u, 11u },
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
    { 0x0012e550UL, 0x0012e560UL, 0x0012f930UL, 6u, 0, 4u, 0u, 0u },
    { 0x0012e560UL, 0x0012e570UL, 0x00130928UL, 7u, 0, 5u, 0u, 0u },
    { 0x0012e570UL, 0x0012e580UL, 0x00130046UL, 6u, 0, 1u, 0u, 0u },
    { 0x0012e580UL, 0x0012e590UL, 0x00130946UL, 1u, 1, 8u, 0u, 1u },
    { 0x0012e590UL, 0x0012e5a0UL, 0x00130946UL, 4u, 0, 8u, 0u, 0u },
    { 0x0012e5a0UL, 0x0012e5b0UL, 0x00130946UL, 1u, 2, 8u, 0u, 2u },
    { 0x0012e5b0UL, 0x0012e5c0UL, 0x00130946UL, 4u, 0, 8u, 0u, 0u },
    { 0x0012e5c0UL, 0x0012e5d0UL, 0x00130946UL, 1u, 3, 8u, 0u, 3u },
    { 0x0012e5d0UL, 0x0012e5e0UL, 0x00130946UL, 4u, 0, 8u, 0u, 0u },
    { 0x0012e5e0UL, 0x0012e5f0UL, 0x001300eeUL, 6u, 0, 1u, 0u, 0u },
    { 0x0012e5f0UL, 0x0012e5f0UL, 0x0012f5acUL, 7u, -32768, 1u, 0u, 0u },
    { 0x0012e604UL, 0x0012e614UL, 0x0012f930UL, 6u, 0, 4u, 0u, 0u },
    { 0x0012e614UL, 0x0012e624UL, 0x0012fce2UL, 5u, 0, 10u, 0u, 0u },
    { 0x0012e624UL, 0x0012e624UL, 0x0012fce2UL, 8u, -32768, 10u, 0u, 0u },
    { 0x0012e638UL, 0x0012e648UL, 0x0012fbfcUL, 4u, 0, 10u, 0u, 0u },
    { 0x0012e648UL, 0x0012e638UL, 0x0012fc74UL, 4u, -32768, 10u, 0u, 0u },
    { 0x0012e65cUL, 0x0012e66cUL, 0x0012f712UL, 8u, 0, 1u, 0u, 0u },
    { 0x0012e66cUL, 0x0012e67cUL, 0x0012f930UL, 8u, 0, 4u, 0u, 0u },
    { 0x0012e67cUL, 0x0012e68cUL, 0x0012f5deUL, 4u, 0, 2u, 0u, 0u },
    { 0x0012e68cUL, 0x0012e68cUL, 0x0012f5deUL, 6u, -32768, 2u, 0u, 0u },
};

static const AvspRound1Class1fMovementTableSpec avsp_round1_class1f_inner8_movement_tables[AVSP_ROUND1_CLASS1F_INNER8_MOVEMENT_TABLE_COUNT] =
{
    { 4u, { { 0, 512 }, { 199, 501 }, { 391, 472 }, { 568, 425 }, { 723, 361 }, { 850, 284 }, { 945, 195 }, { 1003, 99 }, { 1024, 0 }, { 1003, -99 }, { 945, -195 }, { 850, -284 }, { 723, -361 }, { 568, -425 }, { 391, -472 }, { 199, -501 }, { 0, -512 }, { -199, -501 }, { -391, -472 }, { -568, -425 }, { -723, -361 }, { -850, -284 }, { -945, -195 }, { -1003, -99 }, { -1024, 0 }, { -1003, 99 }, { -945, 195 }, { -850, 284 }, { -723, 361 }, { -568, 425 }, { -391, 472 }, { -199, 501 } } },
    { 11u, { { 0, 1408 }, { 548, 1379 }, { 1075, 1299 }, { 1562, 1169 }, { 1990, 995 }, { 2339, 781 }, { 2598, 537 }, { 2759, 274 }, { 2816, 0 }, { 2759, -274 }, { 2598, -537 }, { 2339, -781 }, { 1990, -995 }, { 1562, -1169 }, { 1075, -1299 }, { 548, -1379 }, { 0, -1408 }, { -548, -1379 }, { -1075, -1299 }, { -1562, -1169 }, { -1990, -995 }, { -2339, -781 }, { -2598, -537 }, { -2759, -274 }, { -2816, 0 }, { -2759, 274 }, { -2598, 537 }, { -2339, 781 }, { -1990, 995 }, { -1562, 1169 }, { -1075, 1299 }, { -548, 1379 } } },
    { 12u, { { 0, 1536 }, { 598, 1505 }, { 1173, 1417 }, { 1704, 1276 }, { 2171, 1085 }, { 2552, 852 }, { 2835, 586 }, { 3010, 299 }, { 3072, 0 }, { 3010, -299 }, { 2835, -586 }, { 2552, -852 }, { 2171, -1085 }, { 1704, -1276 }, { 1173, -1417 }, { 598, -1505 }, { 0, -1536 }, { -598, -1505 }, { -1173, -1417 }, { -1704, -1276 }, { -2171, -1085 }, { -2552, -852 }, { -2835, -586 }, { -3010, -299 }, { -3072, 0 }, { -3010, 299 }, { -2835, 586 }, { -2552, 852 }, { -2171, 1085 }, { -1704, 1276 }, { -1173, 1417 }, { -598, 1505 } } },
    { 15u, { { 0, 1920 }, { 748, 1881 }, { 1466, 1771 }, { 2130, 1595 }, { 2714, 1357 }, { 3190, 1065 }, { 3543, 733 }, { 3763, 374 }, { 3840, 0 }, { 3763, -374 }, { 3543, -733 }, { 3190, -1065 }, { 2714, -1357 }, { 2130, -1595 }, { 1466, -1771 }, { 748, -1881 }, { 0, -1920 }, { -748, -1881 }, { -1466, -1771 }, { -2130, -1595 }, { -2714, -1357 }, { -3190, -1065 }, { -3543, -733 }, { -3763, -374 }, { -3840, 0 }, { -3763, 374 }, { -3543, 733 }, { -3190, 1065 }, { -2714, 1357 }, { -2130, 1595 }, { -1466, 1771 }, { -748, 1881 } } },
    { 18u, { { 0, 2304 }, { 897, 2257 }, { 1759, 2126 }, { 2557, 1914 }, { 3256, 1628 }, { 3828, 1278 }, { 4252, 879 }, { 4515, 448 }, { 4608, 0 }, { 4515, -448 }, { 4252, -879 }, { 3828, -1278 }, { 3256, -1628 }, { 2557, -1914 }, { 1759, -2126 }, { 897, -2257 }, { 0, -2304 }, { -897, -2257 }, { -1759, -2126 }, { -2557, -1914 }, { -3256, -1628 }, { -3828, -1278 }, { -4252, -879 }, { -4515, -448 }, { -4608, 0 }, { -4515, 448 }, { -4252, 879 }, { -3828, 1278 }, { -3256, 1628 }, { -2557, 1914 }, { -1759, 2126 }, { -897, 2257 } } },
    { 19u, { { 0, 2432 }, { 947, 2383 }, { 1857, 2244 }, { 2699, 2020 }, { 3437, 1718 }, { 4041, 1349 }, { 4488, 928 }, { 4766, 473 }, { 4864, 0 }, { 4766, -473 }, { 4488, -928 }, { 4041, -1349 }, { 3437, -1718 }, { 2699, -2020 }, { 1857, -2244 }, { 947, -2383 }, { 0, -2432 }, { -947, -2383 }, { -1857, -2244 }, { -2699, -2020 }, { -3437, -1718 }, { -4041, -1349 }, { -4488, -928 }, { -4766, -473 }, { -4864, 0 }, { -4766, 473 }, { -4488, 928 }, { -4041, 1349 }, { -3437, 1718 }, { -2699, 2020 }, { -1857, 2244 }, { -947, 2383 } } },
    { 23u, { { 0, 2944 }, { 1147, 2885 }, { 2248, 2716 }, { 3267, 2445 }, { 4161, 2080 }, { 4891, 1633 }, { 5433, 1124 }, { 5770, 573 }, { 5888, 0 }, { 5770, -573 }, { 5433, -1124 }, { 4891, -1633 }, { 4161, -2080 }, { 3267, -2445 }, { 2248, -2716 }, { 1147, -2885 }, { 0, -2944 }, { -1147, -2885 }, { -2248, -2716 }, { -3267, -2445 }, { -4161, -2080 }, { -4891, -1633 }, { -5433, -1124 }, { -5770, -573 }, { -5888, 0 }, { -5770, 573 }, { -5433, 1124 }, { -4891, 1633 }, { -4161, 2080 }, { -3267, 2445 }, { -2248, 2716 }, { -1147, 2885 } } },
    { 25u, { { 0, 3200 }, { 1246, 3135 }, { 2443, 2953 }, { 3551, 2658 }, { 4523, 2261 }, { 5317, 1775 }, { 5906, 1221 }, { 6271, 623 }, { 6400, 0 }, { 6271, -623 }, { 5906, -1221 }, { 5317, -1775 }, { 4523, -2261 }, { 3551, -2658 }, { 2443, -2953 }, { 1246, -3135 }, { 0, -3200 }, { -1246, -3135 }, { -2443, -2953 }, { -3551, -2658 }, { -4523, -2261 }, { -5317, -1775 }, { -5906, -1221 }, { -6271, -623 }, { -6400, 0 }, { -6271, 623 }, { -5906, 1221 }, { -5317, 1775 }, { -4523, 2261 }, { -3551, 2658 }, { -2443, 2953 }, { -1246, 3135 } } },
};

static const AvspRound1Class1fInner8ProgramSpec avsp_round1_class1f_inner8_program =
{
    0xA3C0u,
    600u, 0x6db6u, 0xf555u,
    { 1u, 2u, 1u, 2u, 1u, 1u, 2u, 1u, 2u, 1u, 1u, 1u, 1u, 2u, 1u, 2u },
    { 62u, 77u, 164u, 31u, 172u, 106u, 28u, 179u, 48u, 0u, 196u, 250u, 81u, 248u, 95u, 193u },
    { -29507, 23373, 1649, -2818 },
    { 121u, 224u, 110u, 53u, 148u, 150u, 35u, 231u, 173u, 247u, 145u, 60u, 72u, 15u, 141u, 63u, 182u, 60u, 105u, 227u, 50u, 135u, 195u, 244u, 155u, 135u, 169u, 98u, 133u, 180u, 141u, 1u },
    { 155u, 48u, 65u, 19u, 129u, 248u, 173u, 103u, 243u, 129u, 55u, 182u, 184u, 216u, 84u, 43u, 92u, 126u, 38u, 121u, 72u, 53u, 78u, 38u, 40u, 82u, 49u, 192u, 222u, 171u, 54u, 205u },
    { 59u, 156u, 89u, 84u },
    { 220u, 204u, 35u, 120u, 20u, 172u, 198u, 232u, 254u, 33u, 11u, 152u, 5u, 60u, 249u, 243u, 238u, 160u, 76u, 222u, 81u, 67u, 217u, 78u, 183u, 137u, 77u, 224u, 235u, 177u, 252u, 137u },
    0x0012D5E4UL, 0x0012D488UL, 0x0012D404UL, 0x0012D628UL,
    0x0012E65CUL, 0x0012D50CUL, 0x0012E604UL, 0x0012E638UL, 0x0012E550UL,
    96u, 12u, 16u, 12u, 8u, 24u,
    { 65536L, -65536L }, 0L, 786432L, -38400L
};

static const unsigned char avsp_round1_class1f_attack_timers[AVSP_ROUND1_CLASS1F_ATTACK_TIMER_COUNT] =
{
    30u, 30u, 30u, 30u, 60u, 60u, 60u, 60u, 120u, 120u, 120u, 120u, 160u, 160u, 160u, 160u
};

static const AvspRound1Class1fActionProgramSpec avsp_round1_class1f_action_program =
{
    0x05F0u, 0x0070u, 0x0260u, 0x0600u, 1u,
    0x0140u, 0x00E8u, { 0x16u, 0x0Au }, { 0x1Au, 0x06u },
    0x0020u, 0x0040u, 0x000Cu, 0x0018u,
    { 34u, 35u }, { 36u, 52u }, { 0x44u, 0x48u },
    { -65536L, -81920L, -98304L, -131072L },
    229376L, -32768L, 32, -8192L,
    53u, 54u, 77u, 62u, 1u,
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
    { 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 16u, 0x8000, 216u, 0x0Fu, 1u, 1u, 1u },
    { 0x00ff9dc0UL, 0x0200u, 0x1000u, 616, 304, 304, 1u, 1u, 17u, 0x8000, 216u, 0x0Fu, 1u, 1u, 1u },
    { 0x00ff9e80UL, 0x0200u, 0x1000u, 640, 256, 256, 1u, 1u, 17u, 0x8000, 216u, 0x0Fu, 1u, 1u, 1u },
    { 0x00ff9f40UL, 0x0200u, 0x1200u, 696, 264, 264, 1u, 1u, 18u, 0x8000, 216u, 0x07u, 0u, 1u, 1u },
    { 0x00ffa000UL, 0x0200u, 0x1200u, 600, 300, 300, 1u, 1u, 17u, 0x8000, 216u, 0x07u, 0u, 1u, 1u },
    { 0x00ffa0c0UL, 0x0200u, 0x1200u, 648, 280, 280, 1u, 1u, 16u, 0x8000, 216u, 0x07u, 0u, 1u, 1u },
    { 0x00ffa180UL, 0x0200u, 0x1200u, 640, 320, 320, 1u, 1u, 18u, 0x8000, 216u, 0x07u, 0u, 1u, 1u },
    { 0x00ffa240UL, 0x0200u, 0x1400u, 744, 280, 280, 1u, 1u, 17u, 0x8000, 9u, 0x0Fu, 1u, 1u, 1u },
    { 0x00ffa300UL, 0x0200u, 0x1400u, 704, 296, 296, 1u, 1u, 19u, 0x8000, 3u, 0x0Fu, 1u, 1u, 1u },
    { 0x00ffa3c0UL, 0x0200u, 0x1400u, 656, 312, 312, 1u, 1u, 19u, 0x8000, 16u, 0x0Fu, 1u, 1u, 1u },
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

static const AvspRound1Type16Spec avsp_round1_type16 =
{
    0x03537eUL, 0x0413d2UL, 0x01778cUL, 0x0177a2UL, 0x00035882UL, 0x0003589eUL, 0x0011ae02UL, 0x0011ae8eUL,
    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 20u,
    { 0, 0, 8u, 8u, 0, 8u, 0, 20u, 10u },
    { 1, 45, 20u, 46u, 0, 6u, 0, 0u, 0u }
};

static const AvspRound1Type16MotionSpec avsp_round1_type16_motion[AVSP_ROUND1_TYPE16_MOTION_COUNT] =
{
    { 524288L, -8192L, 262144L, -16384L, 0L },
    { 475136L, -9216L, 245760L, -20480L, 0L },
    { 425984L, -10240L, 229376L, -28672L, 0L },
};

static const AvspRound1AnimationStateSpec avsp_round1_type16_parent_records[AVSP_ROUND1_TYPE16_PARENT_PRESENTATION_COUNT] =
{
    { 6u, 0, 0x0012e550UL, 0x0012f930UL, 4u, 0u },
    { 7u, 0, 0x0012e560UL, 0x00130928UL, 5u, 0u },
    { 6u, 0, 0x0012e570UL, 0x00130046UL, 1u, 0u },
    { 1u, 1, 0x0012e580UL, 0x00130946UL, 8u, 0u },
    { 4u, 0, 0x0012e590UL, 0x00130946UL, 8u, 0u },
    { 1u, 2, 0x0012e5a0UL, 0x00130946UL, 8u, 0u },
    { 4u, 0, 0x0012e5b0UL, 0x00130946UL, 8u, 0u },
    { 1u, 3, 0x0012e5c0UL, 0x00130946UL, 8u, 0u },
    { 4u, 0, 0x0012e5d0UL, 0x00130946UL, 8u, 0u },
    { 6u, 0, 0x0012e5e0UL, 0x001300eeUL, 1u, 0u },
    { 7u, -32768, 0x0012e5f0UL, 0x0012f5acUL, 1u, 0u },
};

static const AvspRound1AnimationStateSpec avsp_round1_type16_records[AVSP_ROUND1_TYPE16_PRESENTATION_COUNT] =
{
    { 10u, 0, 0x000355dcUL, 0x0003570cUL, 0u, 1u },
    { 5u, 0, 0x000355ecUL, 0x0003571aUL, 0u, 1u },
    { 7u, 0, 0x000355fcUL, 0x00035728UL, 0u, 1u },
    { 3u, -32768, 0x0003560cUL, 0x00035736UL, 0u, 1u },
    { 6u, 0, 0x00035620UL, 0x00035744UL, 0u, 2u },
    { 6u, 0, 0x00035630UL, 0x00035770UL, 0u, 2u },
    { 6u, 0, 0x00035640UL, 0x00035794UL, 0u, 2u },
    { 6u, 0, 0x00035650UL, 0x000357c0UL, 0u, 2u },
    { 6u, 0, 0x00035660UL, 0x000357e4UL, 0u, 2u },
    { 4u, 0, 0x00035670UL, 0x00035808UL, 0u, 0u },
    { 4095u, -32768, 0x00035680UL, 0x00035824UL, 0u, 0u },
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

static const AvspRound1Class4eRngSpec avsp_round1_class4e_rng[AVSP_ROUND1_CLASS09_INITIAL_ACTOR_COUNT] =
{
    { 0x00ffc480UL, 0xcdb5u, 0x691eu, 28u },
    { 0x00ffc500UL, 0x691eu, 0x3b59u, 24u },
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

static const AvspRound1AnimationStateSpec avsp_round1_class4e_variant1_records[AVSP_ROUND1_CLASS4E_VARIANT1_PRESENTATION_COUNT] =
{
    { 4u, 0, 0x00092914UL, 0x00092c04UL, 0u, 0u },
    { 4u, 0, 0x00092924UL, 0x00092c12UL, 0u, 0u },
    { 4095u, -32768, 0x00092934UL, 0x00092c12UL, 0u, 0u },
};

static const AvspRound1AnimationStateSpec avsp_round1_class4e_variant10_records[AVSP_ROUND1_CLASS4E_VARIANT10_PRESENTATION_COUNT] =
{
    { 1u, 0, 0x00092e50UL, 0x000931f8UL, 0u, 0u },
    { 1u, 0, 0x00092e60UL, 0x00093206UL, 0u, 0u },
    { 1u, 0, 0x00092e70UL, 0x00093214UL, 0u, 0u },
    { 1u, 0, 0x00092e80UL, 0x00093222UL, 0u, 0u },
    { 1u, 0, 0x00092e90UL, 0x00093230UL, 0u, 0u },
    { 4095u, -32768, 0x00092ea0UL, 0x0009323eUL, 0u, 0u },
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

static const AvspRound1Class43Spec avsp_round1_class43 =
{
    0x43, 0u, 2u, 4u, 7u, 80, -1, 0x08ce44UL
};

static const unsigned char avsp_round1_class43_animation_selectors[AVSP_ROUND1_CLASS43_SELECTOR_COUNT] =
{
    5u, 6u, 7u, 15u, 5u, 6u, 7u, 15u, 0u, 1u, 2u, 3u, 4u, 8u, 9u, 10u, 11u, 12u, 13u, 14u, 0u, 1u, 2u, 3u, 4u, 8u, 9u, 10u, 11u, 12u, 13u, 14u
};

static const unsigned char avsp_round1_class43_sequence_offsets[AVSP_ROUND1_CLASS43_SEQUENCE_COUNT] =
{
    0u, 6u, 12u, 18u, 24u, 30u, 36u, 40u, 44u, 48u, 56u, 64u, 66u, 67u, 68u, 69u
};

static const AvspRound1AnimationStateSpec avsp_round1_class43_records[AVSP_ROUND1_CLASS43_PRESENTATION_COUNT] =
{
    { 4u, 0, 0x0008d14aUL, 0x0008d5eaUL, 0u, 0u },
    { 4u, 0, 0x0008d15aUL, 0x0008d5f8UL, 0u, 0u },
    { 4u, 0, 0x0008d16aUL, 0x0008d606UL, 0u, 0u },
    { 4u, 0, 0x0008d17aUL, 0x0008d614UL, 0u, 0u },
    { 4u, 0, 0x0008d18aUL, 0x0008d622UL, 0u, 0u },
    { 4u, -32768, 0x0008d19aUL, 0x0008d630UL, 0u, 0u },
    { 4u, 0, 0x0008d1aeUL, 0x0008d63eUL, 0u, 0u },
    { 4u, 0, 0x0008d1beUL, 0x0008d64cUL, 0u, 0u },
    { 4u, 0, 0x0008d1ceUL, 0x0008d65aUL, 0u, 0u },
    { 4u, 0, 0x0008d1deUL, 0x0008d668UL, 0u, 0u },
    { 4u, 0, 0x0008d1eeUL, 0x0008d676UL, 0u, 0u },
    { 4u, -32768, 0x0008d1feUL, 0x0008d684UL, 0u, 0u },
    { 4u, 0, 0x0008d212UL, 0x0008d692UL, 0u, 0u },
    { 4u, 0, 0x0008d222UL, 0x0008d6a0UL, 0u, 0u },
    { 4u, 0, 0x0008d232UL, 0x0008d6aeUL, 0u, 0u },
    { 4u, 0, 0x0008d242UL, 0x0008d6bcUL, 0u, 0u },
    { 4u, 0, 0x0008d252UL, 0x0008d6caUL, 0u, 0u },
    { 4u, -32768, 0x0008d262UL, 0x0008d6d8UL, 0u, 0u },
    { 4u, 0, 0x0008d276UL, 0x0008d6e6UL, 0u, 0u },
    { 4u, 0, 0x0008d286UL, 0x0008d6f4UL, 0u, 0u },
    { 4u, 0, 0x0008d296UL, 0x0008d702UL, 0u, 0u },
    { 4u, 0, 0x0008d2a6UL, 0x0008d710UL, 0u, 0u },
    { 4u, 0, 0x0008d2b6UL, 0x0008d71eUL, 0u, 0u },
    { 4u, -32768, 0x0008d2c6UL, 0x0008d72cUL, 0u, 0u },
    { 4u, 0, 0x0008d2daUL, 0x0008d73aUL, 0u, 0u },
    { 4u, 0, 0x0008d2eaUL, 0x0008d748UL, 0u, 0u },
    { 4u, 0, 0x0008d2faUL, 0x0008d756UL, 0u, 0u },
    { 4u, 0, 0x0008d30aUL, 0x0008d764UL, 0u, 0u },
    { 4u, 0, 0x0008d31aUL, 0x0008d772UL, 0u, 0u },
    { 4u, -32768, 0x0008d32aUL, 0x0008d780UL, 0u, 0u },
    { 4u, 0, 0x0008d33eUL, 0x0008d78eUL, 0u, 0u },
    { 4u, 0, 0x0008d34eUL, 0x0008d79cUL, 0u, 0u },
    { 4u, 0, 0x0008d35eUL, 0x0008d7aaUL, 0u, 0u },
    { 4u, 0, 0x0008d36eUL, 0x0008d7b8UL, 0u, 0u },
    { 4u, 0, 0x0008d37eUL, 0x0008d7c6UL, 0u, 0u },
    { 4u, -32768, 0x0008d38eUL, 0x0008d7d4UL, 0u, 0u },
    { 4u, 0, 0x0008d3a2UL, 0x0008d7e2UL, 0u, 0u },
    { 4u, 0, 0x0008d3b2UL, 0x0008d7f0UL, 0u, 0u },
    { 4u, 0, 0x0008d3c2UL, 0x0008d7feUL, 0u, 0u },
    { 4u, -32768, 0x0008d3d2UL, 0x0008d80cUL, 0u, 0u },
    { 4u, 0, 0x0008d3e6UL, 0x0008d81aUL, 0u, 0u },
    { 4u, 0, 0x0008d3f6UL, 0x0008d828UL, 0u, 0u },
    { 4u, 0, 0x0008d406UL, 0x0008d836UL, 0u, 0u },
    { 4u, -32768, 0x0008d416UL, 0x0008d844UL, 0u, 0u },
    { 4u, 0, 0x0008d42aUL, 0x0008d852UL, 0u, 0u },
    { 4u, 0, 0x0008d43aUL, 0x0008d860UL, 0u, 0u },
    { 4u, 0, 0x0008d44aUL, 0x0008d86eUL, 0u, 0u },
    { 4u, -32768, 0x0008d45aUL, 0x0008d87cUL, 0u, 0u },
    { 4u, 0, 0x0008d46eUL, 0x0008d88aUL, 0u, 0u },
    { 4u, 0, 0x0008d47eUL, 0x0008d898UL, 0u, 0u },
    { 4u, 0, 0x0008d48eUL, 0x0008d8a6UL, 0u, 0u },
    { 4u, 0, 0x0008d49eUL, 0x0008d8d0UL, 0u, 0u },
    { 4u, 0, 0x0008d4aeUL, 0x0008d8c2UL, 0u, 0u },
    { 4u, 0, 0x0008d4beUL, 0x0008d8b4UL, 0u, 0u },
    { 4u, 0, 0x0008d4ceUL, 0x0008d8a6UL, 0u, 0u },
    { 4u, -32768, 0x0008d4deUL, 0x0008d8deUL, 0u, 0u },
    { 4u, 0, 0x0008d4f2UL, 0x0008d8ecUL, 0u, 0u },
    { 4u, 0, 0x0008d502UL, 0x0008d8faUL, 0u, 0u },
    { 4u, 0, 0x0008d512UL, 0x0008d908UL, 0u, 0u },
    { 4u, 0, 0x0008d522UL, 0x0008d932UL, 0u, 0u },
    { 4u, 0, 0x0008d532UL, 0x0008d924UL, 0u, 0u },
    { 4u, 0, 0x0008d542UL, 0x0008d940UL, 0u, 0u },
    { 4u, 0, 0x0008d552UL, 0x0008d908UL, 0u, 0u },
    { 4u, -32768, 0x0008d562UL, 0x0008d916UL, 0u, 0u },
    { 4u, 0, 0x0008d576UL, 0x0008d94eUL, 0u, 0u },
    { 4u, -32768, 0x0008d586UL, 0x0008d95cUL, 0u, 0u },
    { 4095u, -32768, 0x0008d59aUL, 0x0008d96aUL, 0u, 0u },
    { 4095u, -32768, 0x0008d5aeUL, 0x0008d978UL, 0u, 0u },
    { 4095u, -32768, 0x0008d5c2UL, 0x0008d986UL, 0u, 0u },
    { 4095u, -32768, 0x0008d5d6UL, 0x0008d994UL, 0u, 0u },
};

static const AvspRound1Class45MotionSpec avsp_round1_class43_motion[AVSP_ROUND1_CLASS43_MOTION_COUNT] =
{
    { 0, 2048, -96, 896, 1792, -96 },
    { 256, 1920, -96, 640, 1536, -96 },
    { 512, 1792, -96, 384, 1280, -96 },
    { 768, 1664, -96, 128, 1024, -96 },
    { 128, 1536, -96, 768, 2048, -96 },
    { 384, 1408, -96, 512, 2304, -96 },
    { 640, 1280, -96, 256, 2560, -96 },
    { 896, 1152, -96, 0, 2816, -96 },
};

static const unsigned long avsp_round1_class45_source_slots[AVSP_ROUND1_CLASS45_SCENE_ACTOR_COUNT] =
{
    0x00ffb680UL, 0x00ffb700UL, 0x00ffb780UL, 0x00ffb800UL, 0x00ffb880UL, 0x00ffb900UL, 0x00ffb980UL, 0x00ffba00UL, 0x00ffba80UL, 0x00ffbb00UL, 0x00ffbb80UL, 0x00ffbc00UL, 0x00ffbc80UL, 0x00ffbd00UL, 0x00ffbd80UL, 0x00ffbe00UL, 0x00ffbe80UL, 0x00ffbf00UL, 0x00ffbf80UL, 0x00ffc000UL, 0x00ffc080UL, 0x00ffc100UL, 0x00ffc180UL, 0x00ffc200UL, 0x00ffc280UL, 0x00ffc300UL, 0x00ffc380UL, 0x00ffc400UL
};

static const AvspRound1Class45SpawnGroupSpec avsp_round1_class45_spawn_groups[AVSP_ROUND1_CLASS45_SPAWN_GROUP_COUNT] =
{
    { 5u, 0, 128, -1 },
    { 5u, 0, 128, -1 },
    { 65535u, 48, 64, -1 },
};

static const unsigned char avsp_round1_class45_animation_selectors[AVSP_ROUND1_CLASS45_SELECTOR_COUNT] =
{
    0u, 1u, 0u, 3u, 4u, 5u, 0u, 1u, 1u, 3u, 4u, 5u, 0u, 1u, 3u, 3u, 4u, 5u, 0u, 1u, 4u, 3u, 4u, 5u, 0u, 1u, 5u, 3u, 4u, 5u, 0u, 1u
};

static const AvspRound1AnimationStateSpec avsp_round1_class45_records[AVSP_ROUND1_CLASS45_PRESENTATION_COUNT] =
{
    { 4095u, -32768, 0x0008dedcUL, 0x0008df54UL, 0u, 0u },
    { 4095u, -32768, 0x0008def0UL, 0x0008df62UL, 0u, 0u },
    { 4095u, -32768, 0x0008df18UL, 0x0008df88UL, 0u, 0u },
    { 4095u, -32768, 0x0008df2cUL, 0x0008df96UL, 0u, 0u },
    { 4095u, -32768, 0x0008df40UL, 0x0008dfa4UL, 0u, 0u },
};

static const AvspRound1Class45MotionSpec avsp_round1_class45_motion[AVSP_ROUND1_CLASS45_MOTION_COUNT] =
{
    { 0, 2048, -96, -896, 2048, -96 },
    { 128, 1920, -96, -768, 1920, -96 },
    { 256, 1792, -96, -640, 1792, -96 },
    { 384, 1664, -96, -512, 1664, -96 },
    { 512, 1536, -96, -384, 1536, -96 },
    { 640, 1408, -96, -256, 1408, -96 },
    { 768, 1280, -96, -128, 1280, -96 },
    { 896, 1152, -96, 0, 1152, -96 },
};

static const unsigned long avsp_round1_class47_source_slots[AVSP_ROUND1_CLASS47_SCENE_ACTOR_COUNT] =
{
    0x00ffbd80UL, 0x00ffc180UL, 0x00ffc200UL, 0x00ffc380UL
};

static const AvspRound1Class47Spec avsp_round1_class47 =
{
    0x47, 0u, 4u, 7u, 80, -1, 0x08eb86UL
};

static const unsigned char avsp_round1_class47_animation_selectors[AVSP_ROUND1_CLASS47_SELECTOR_COUNT] =
{
    0u, 1u, 2u, 3u, 4u, 5u, 6u, 0u, 1u, 2u, 3u, 4u, 5u, 6u, 0u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 7u, 8u, 7u, 8u, 0u, 1u, 2u, 3u, 4u
};

static const AvspRound1AnimationStateSpec avsp_round1_class47_records[AVSP_ROUND1_CLASS47_PRESENTATION_COUNT] =
{
    { 4095u, -32768, 0x0008ee38UL, 0x0008eeecUL, 0u, 0u },
    { 4095u, -32768, 0x0008ee4cUL, 0x0008eefaUL, 0u, 0u },
    { 4095u, -32768, 0x0008ee60UL, 0x0008ef08UL, 0u, 0u },
    { 4095u, -32768, 0x0008ee74UL, 0x0008ef16UL, 0u, 0u },
    { 4095u, -32768, 0x0008ee88UL, 0x0008ef24UL, 0u, 0u },
    { 4095u, -32768, 0x0008ee9cUL, 0x0008ef32UL, 0u, 0u },
    { 4095u, -32768, 0x0008eeb0UL, 0x0008ef40UL, 0u, 0u },
    { 4095u, -32768, 0x0008eec4UL, 0x0008ef4eUL, 0u, 0u },
    { 4095u, -32768, 0x0008eed8UL, 0x0008ef5cUL, 0u, 0u },
};

static const AvspRound1Class45MotionSpec avsp_round1_class47_motion[AVSP_ROUND1_CLASS47_MOTION_COUNT] =
{
    { 0, 2048, -96, 896, 1792, -96 },
    { 256, 1920, -96, 640, 1536, -96 },
    { 512, 1792, -96, 384, 1280, -96 },
    { 768, 1664, -96, 128, 1024, -96 },
    { 128, 1536, -96, 768, 2048, -96 },
    { 384, 1408, -96, 512, 2304, -96 },
    { 640, 1280, -96, 256, 2560, -96 },
    { 896, 1152, -96, 0, 2816, -96 },
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

static const AvspRound1AnimationStateSpec avsp_round1_coffee_shop_obstacle_records[AVSP_ROUND1_OBSTACLE_PARENT_RECORD_COUNT] =
{
    { 4095u, -32768, 0x06e136UL, 0x06e196UL, 1u, 1u },
    { 1u, 0, 0x06e14aUL, 0x06e1b4UL, 0u, 0u },
    { 4095u, -32768, 0x06e15aUL, 0x06e1ccUL, 0u, 0u },
    { 4095u, -32768, 0x06e16eUL, 0x06e1eaUL, 0u, 0u },
    { 4095u, -32768, 0x06e182UL, 0x06e202UL, 0u, 0u },
};

static const AvspRound1ObstacleChildSequenceSpec avsp_round1_coffee_shop_obstacle_child_sequences[AVSP_ROUND1_OBSTACLE_CHILD_VARIANTS] =
{
    { 5u, { { 8u, 0, 0x09bbf0UL, 0x09bdb2UL, 0u, 0u }, { 8u, 0, 0x09bc00UL, 0x09bdc0UL, 0u, 0u }, { 8u, 0, 0x09bc10UL, 0x09bdceUL, 0u, 0u }, { 8u, 0, 0x09bc20UL, 0x09bddcUL, 0u, 0u }, { 8u, -32768, 0x09bc30UL, 0x09bdeaUL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 8u, { { 5u, 0, 0x09bc44UL, 0x09bdf8UL, 0u, 0u }, { 5u, 0, 0x09bc54UL, 0x09be30UL, 0u, 0u }, { 5u, 0, 0x09bc64UL, 0x09be22UL, 0u, 0u }, { 5u, 0, 0x09bc74UL, 0x09be14UL, 0u, 0u }, { 5u, 0, 0x09bc84UL, 0x09be06UL, 0u, 0u }, { 5u, 0, 0x09bc94UL, 0x09be14UL, 0u, 0u }, { 5u, 0, 0x09bca4UL, 0x09be22UL, 0u, 0u }, { 5u, -32768, 0x09bcb4UL, 0x09be30UL, 0u, 0u } } },
    { 6u, { { 6u, 0, 0x09bcc8UL, 0x09be4cUL, 0u, 0u }, { 6u, 0, 0x09bcd8UL, 0x09be5aUL, 0u, 0u }, { 6u, 0, 0x09bce8UL, 0x09be3eUL, 0u, 0u }, { 6u, 0, 0x09bcf8UL, 0x09be68UL, 0u, 0u }, { 6u, 0, 0x09bd08UL, 0x09be3eUL, 0u, 0u }, { 6u, -32768, 0x09bd18UL, 0x09be5aUL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
    { 6u, { { 7u, 0, 0x09bd2cUL, 0x09be76UL, 0u, 0u }, { 7u, 0, 0x09bd3cUL, 0x09bea0UL, 0u, 0u }, { 7u, 0, 0x09bd4cUL, 0x09be92UL, 0u, 0u }, { 7u, 0, 0x09bd5cUL, 0x09be84UL, 0u, 0u }, { 7u, 0, 0x09bd6cUL, 0x09be92UL, 0u, 0u }, { 7u, -32768, 0x09bd7cUL, 0x09bea0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u }, { 0u, 0, 0UL, 0UL, 0u, 0u } } },
};

static const AvspRound1AnimationStateSpec avsp_round1_coffee_shop_obstacle_child_release =
{ 4095u, -32768, 0x09bd90UL, 0x09beaeUL, 0u, 0u };

static const AvspRound1ObstacleLifecycleSpec avsp_round1_coffee_shop_obstacle_lifecycle =
{
    0x15c168UL, 0xffb380UL, 0x06DE92UL, 0x11af76UL,
    688u, 1123, 323, 323, 0,
    0x0200u, 0x0400u, 0x0402u, 0x0404u, 0x0604u,
    0x8000u, 0x1Du, 36u, 0x05, 4u,
    { 3u, 2u, 1u, 0u },
    8u, 25u, 14u, 3u, 1,
    { 0, 48, 88u, 48u, 0, 40u, 1, 3u, 25u },
    { 0, 64, 16u, 64u, 0, 6u, 0, 0u, 0u },
    { 1280, 1536, 0, -128, 1024, 1280, 0, -128 }
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

static const AvspRound1PlayerSpecialSpec avsp_round1_player_special =
{
    0x0800u, 0x0802u, 0x0804u, 0x0804u, 0x0000u,
    47u, 11u, 6u, 24u, 0x4B, 24u, 0x3D,
    0x0091u, 0x0096u
};

static const AvspRound1AnimationStateSpec avsp_round1_player_special_records[AVSP_ROUND1_PLAYER_SPECIAL_PRESENTATION_COUNT] =
{
    { 4u, 1, 0x0015fd10UL, 0x001626ccUL, 0u, 0u },
    { 4u, 1, 0x0015fd20UL, 0x001626faUL, 0u, 0u },
    { 3u, 1, 0x0015fd30UL, 0x00162728UL, 0u, 0u },
    { 1u, 0, 0x0015fd40UL, 0x001627b8UL, 0u, 0u },
    { 3u, 0, 0x0015fd50UL, 0x001627b8UL, 0u, 11u },
    { 4u, 0, 0x0015fd60UL, 0x001627e0UL, 0u, 11u },
    { 4u, 0, 0x0015fd70UL, 0x0016280eUL, 0u, 11u },
    { 4u, 0, 0x0015fd80UL, 0x001627e0UL, 0u, 11u },
    { 4u, 0, 0x0015fd90UL, 0x001627b8UL, 0u, 11u },
    { 4u, 0, 0x0015fda0UL, 0x001627e0UL, 0u, 11u },
    { 4u, 0, 0x0015fdb0UL, 0x0016280eUL, 0u, 11u },
    { 4u, 0, 0x0015fdc0UL, 0x001627e0UL, 0u, 11u },
    { 4u, 1, 0x0015fdd0UL, 0x00162728UL, 0u, 0u },
    { 4u, 0, 0x0015fde0UL, 0x0016278aUL, 0u, 0u },
    { 4u, 0, 0x0015fdf0UL, 0x0016275cUL, 0u, 0u },
    { 16u, 0, 0x0015fe00UL, 0x001626ccUL, 0u, 0u },
    { 4095u, -32768, 0x0015fe10UL, 0x001626a4UL, 0u, 0u },
};

static const unsigned char avsp_round1_player_special_visible_durations[AVSP_ROUND1_PLAYER_SPECIAL_PRESENTATION_COUNT] =
{
    4u, 4u, 3u, 1u, 5u, 4u, 4u, 4u, 4u, 4u, 6u, 4u, 4u, 4u, 4u, 16u, 1u
};

static const AvspRound1AnimationStateSpec avsp_round1_class4b_records[AVSP_ROUND1_CLASS4B_PRESENTATION_COUNT] =
{
    { 1u, 0, 0x0008f8e0UL, 0x0008fae4UL, 0u, 0u },
    { 1u, 1, 0x0008f8f0UL, 0x0008fae4UL, 0u, 0u },
    { 1u, 2, 0x0008f900UL, 0x0008fb02UL, 0u, 0u },
    { 1u, 3, 0x0008f910UL, 0x0008fb02UL, 0u, 0u },
    { 1u, 4, 0x0008f920UL, 0x0008fb2cUL, 0u, 0u },
    { 1u, 5, 0x0008f930UL, 0x0008fb2cUL, 0u, 0u },
    { 1u, 6, 0x0008f940UL, 0x0008fb44UL, 0u, 0u },
    { 1u, 7, 0x0008f950UL, 0x0008fb44UL, 0u, 0u },
    { 1u, 8, 0x0008f960UL, 0x0008fae4UL, 0u, 0u },
    { 1u, 9, 0x0008f970UL, 0x0008fae4UL, 0u, 0u },
    { 1u, 10, 0x0008f980UL, 0x0008fb02UL, 0u, 0u },
    { 1u, 11, 0x0008f990UL, 0x0008fb02UL, 0u, 0u },
    { 1u, 12, 0x0008f9a0UL, 0x0008fb2cUL, 0u, 0u },
    { 1u, 13, 0x0008f9b0UL, 0x0008fb2cUL, 0u, 0u },
    { 1u, 14, 0x0008f9c0UL, 0x0008fb44UL, 0u, 0u },
    { 1u, 15, 0x0008f9d0UL, 0x0008fb44UL, 0u, 0u },
    { 1u, 0, 0x0008f9e0UL, 0x0008fae4UL, 0u, 0u },
    { 1u, 1, 0x0008f9f0UL, 0x0008fae4UL, 0u, 0u },
    { 1u, 2, 0x0008fa00UL, 0x0008fb02UL, 0u, 0u },
    { 1u, 3, 0x0008fa10UL, 0x0008fb02UL, 0u, 0u },
    { 1u, 4, 0x0008fa20UL, 0x0008fb2cUL, 0u, 0u },
    { 1u, 5, 0x0008fa30UL, 0x0008fb2cUL, 0u, 0u },
    { 1u, 6, 0x0008fa40UL, 0x0008fb44UL, 0u, 0u },
    { 1u, 7, 0x0008fa50UL, 0x0008fb44UL, 0u, 0u },
    { 1u, 8, 0x0008fa60UL, 0x0008fae4UL, 0u, 0u },
    { 1u, 9, 0x0008fa70UL, 0x0008fae4UL, 0u, 0u },
    { 1u, 10, 0x0008fa80UL, 0x0008fb02UL, 0u, 0u },
    { 1u, 11, 0x0008fa90UL, 0x0008fb02UL, 0u, 0u },
    { 1u, 12, 0x0008faa0UL, 0x0008fb2cUL, 0u, 0u },
    { 1u, 13, 0x0008fab0UL, 0x0008fb2cUL, 0u, 0u },
    { 1u, 14, 0x0008fac0UL, 0x0008fb44UL, 0u, 0u },
    { 1u, -32753, 0x0008fad0UL, 0x0008fb44UL, 0u, 0u },
};

static const AvspRound1AnimationStateSpec avsp_round1_class3d_records[AVSP_ROUND1_CLASS3D_PRESENTATION_COUNT] =
{
    { 2u, 0, 0x0009a918UL, 0x0009a9aeUL, 0u, 0u },
    { 2u, 0, 0x0009a928UL, 0x0009a9bcUL, 0u, 0u },
    { 2u, 0, 0x0009a938UL, 0x0009a9caUL, 0u, 0u },
    { 2u, 0, 0x0009a948UL, 0x0009a9d8UL, 0u, 0u },
    { 2u, 0, 0x0009a958UL, 0x0009a9e6UL, 0u, 0u },
    { 2u, 0, 0x0009a968UL, 0x0009a9f4UL, 0u, 0u },
    { 2u, 0, 0x0009a978UL, 0x0009aa02UL, 0u, 0u },
    { 2u, 0, 0x0009a988UL, 0x0009aa10UL, 0u, 0u },
    { 4095u, -32768, 0x0009a998UL, 0x0009a9acUL, 0u, 0u },
};

static const AvspRound1VecS16 avsp_round1_class3d_offsets[AVSP_ROUND1_CLASS3D_OFFSET_COUNT] =
{
    { -61, -13 },
    { -48, -19 },
    { -24, -23 },
    { 0, -24 },
    { 24, -23 },
    { 48, -19 },
    { 61, -13 },
    { 72, 0 },
    { 61, 13 },
    { 48, 19 },
    { 24, 23 },
    { 0, 24 },
    { -24, 23 },
    { -48, 19 },
    { -61, 13 },
    { -72, 0 },
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
    3u,
    6u,
    1u,
    0u,
    1u,
    1u,
    0,
    4,
    0x8680u,
    0x0080u,
    0x8380u,
    0x0002fc3cUL,
    0x00030cb6UL
};

static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_frames[AVSP_ROUND1_PLAYER_WEAPON_SELECTOR_COUNT][AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT] =
{
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
    },
    {
        { 3072u, 0u, 0x0015f1f4UL, 0x001626a4UL, 1u, 0u },
        { 3074u, 2u, 0x0015e594UL, 0x0016179aUL, 1u, 0u },
        { 3074u, 2u, 0x0015e594UL, 0x0016179aUL, 1u, 0u },
        { 3074u, 2u, 0x0015e594UL, 0x0016179aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5a4UL, 0x001618daUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5b4UL, 0x00161a38UL, 1u, 0u },
        { 3076u, 4u, 0x0015e5b4UL, 0x00161a38UL, 1u, 0u },
        { 3076u, 4u, 0x0015e5c4UL, 0x001618daUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5d4UL, 0x0016179aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5d4UL, 0x0016179aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5d4UL, 0x0016179aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5d4UL, 0x0016179aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5d4UL, 0x0016179aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5d4UL, 0x0016179aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5d4UL, 0x0016179aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5d4UL, 0x0016179aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5d4UL, 0x0016179aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5d4UL, 0x0016179aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e5d4UL, 0x0016179aUL, 1u, 0u },
        { 0u, 0u, 0x0015f1f4UL, 0x001626a4UL, 1u, 0u },
    },
    {
        { 3072u, 0u, 0x0015f1f4UL, 0x001626a4UL, 1u, 0u },
        { 3074u, 2u, 0x0015e5e8UL, 0x001617c2UL, 1u, 0u },
        { 3074u, 2u, 0x0015e5e8UL, 0x001617c2UL, 1u, 0u },
        { 3074u, 2u, 0x0015e5e8UL, 0x001617c2UL, 1u, 0u },
        { 3076u, 4u, 0x0015e5f8UL, 0x00161902UL, 1u, 0u },
        { 3076u, 4u, 0x0015e608UL, 0x00161a66UL, 1u, 0u },
        { 3076u, 4u, 0x0015e608UL, 0x00161a66UL, 1u, 0u },
        { 3076u, 4u, 0x0015e618UL, 0x00161902UL, 1u, 0u },
        { 3076u, 4u, 0x0015e628UL, 0x001617c2UL, 1u, 0u },
        { 3076u, 4u, 0x0015e628UL, 0x001617c2UL, 1u, 0u },
        { 3076u, 4u, 0x0015e628UL, 0x001617c2UL, 1u, 0u },
        { 3076u, 4u, 0x0015e628UL, 0x001617c2UL, 1u, 0u },
        { 3076u, 4u, 0x0015e628UL, 0x001617c2UL, 1u, 0u },
        { 3076u, 4u, 0x0015e628UL, 0x001617c2UL, 1u, 0u },
        { 3076u, 4u, 0x0015e628UL, 0x001617c2UL, 1u, 0u },
        { 3076u, 4u, 0x0015e628UL, 0x001617c2UL, 1u, 0u },
        { 3076u, 4u, 0x0015e628UL, 0x001617c2UL, 1u, 0u },
        { 3076u, 4u, 0x0015e628UL, 0x001617c2UL, 1u, 0u },
        { 3076u, 4u, 0x0015e628UL, 0x001617c2UL, 1u, 0u },
        { 0u, 0u, 0x0015f1f4UL, 0x001626a4UL, 1u, 0u },
    },
    {
        { 3072u, 0u, 0x0015f1f4UL, 0x001626a4UL, 1u, 0u },
        { 3074u, 2u, 0x0015e63cUL, 0x001617eaUL, 1u, 0u },
        { 3074u, 2u, 0x0015e63cUL, 0x001617eaUL, 1u, 0u },
        { 3074u, 2u, 0x0015e63cUL, 0x001617eaUL, 1u, 0u },
        { 3076u, 4u, 0x0015e64cUL, 0x0016192aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e65cUL, 0x00161a94UL, 1u, 0u },
        { 3076u, 4u, 0x0015e65cUL, 0x00161a94UL, 1u, 0u },
        { 3076u, 4u, 0x0015e66cUL, 0x0016192aUL, 1u, 0u },
        { 3076u, 4u, 0x0015e67cUL, 0x001617eaUL, 1u, 0u },
        { 3076u, 4u, 0x0015e67cUL, 0x001617eaUL, 1u, 0u },
        { 3076u, 4u, 0x0015e67cUL, 0x001617eaUL, 1u, 0u },
        { 3076u, 4u, 0x0015e67cUL, 0x001617eaUL, 1u, 0u },
        { 3076u, 4u, 0x0015e67cUL, 0x001617eaUL, 1u, 0u },
        { 3076u, 4u, 0x0015e67cUL, 0x001617eaUL, 1u, 0u },
        { 3076u, 4u, 0x0015e67cUL, 0x001617eaUL, 1u, 0u },
        { 3076u, 4u, 0x0015e67cUL, 0x001617eaUL, 1u, 0u },
        { 3076u, 4u, 0x0015e67cUL, 0x001617eaUL, 1u, 0u },
        { 3076u, 4u, 0x0015e67cUL, 0x001617eaUL, 1u, 0u },
        { 3076u, 4u, 0x0015e67cUL, 0x001617eaUL, 1u, 0u },
        { 0u, 0u, 0x0015f1f4UL, 0x001626a4UL, 1u, 0u },
    },
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
    { 4u, -32768, 0x0002fbb8UL, 0x0002fc2eUL, 0u, 1u },
};

static const unsigned short avsp_round1_weapon_target_distance_thresholds[AVSP_ROUND1_WEAPON_TARGET_DISTANCE_COUNT] =
{
    0u, 13u, 16u, 22u, 30u, 38u, 48u, 58u, 70u, 88u, 103u, 123u, 153u, 192u, 251u, 352u
};

static const unsigned char avsp_round1_weapon_target_presentation_selectors[AVSP_ROUND1_WEAPON_TARGET_DISTANCE_COUNT] =
{
    7u, 7u, 7u, 7u, 6u, 6u, 6u, 6u, 5u, 5u, 5u, 5u, 4u, 4u, 4u, 4u
};

static const unsigned char avsp_round1_weapon_parent_route_angles[AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT] =
{
    17u, 18u, 19u, 20u, 21u, 22u, 23u, 24u, 25u, 26u, 27u, 28u, 29u, 30u, 31u, 32u, 33u, 34u, 35u, 36u, 37u, 38u, 39u, 40u, 41u, 42u, 43u, 44u, 45u, 46u, 47u
};

static const AvspRound1VecS16 avsp_round1_weapon_parent_motion_low[AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT][AVSP_ROUND1_WEAPON_PARENT_LOW_MOTION_COUNT] =
{
    { { 0, 0 }, { 15, -1 }, { 31, -3 }, { 47, -5 }, { 63, -7 }, { 79, -8 }, { 95, -10 }, { 111, -12 }, { 127, -14 }, { 143, -16 }, { 159, -17 }, { 175, -19 }, { 191, -21 }, { 206, -23 }, { 222, -25 }, { 238, -26 } },
    { { 0, 0 }, { 15, -3 }, { 31, -7 }, { 47, -10 }, { 62, -14 }, { 78, -17 }, { 94, -21 }, { 109, -24 }, { 125, -28 }, { 141, -32 }, { 156, -35 }, { 172, -39 }, { 188, -42 }, { 203, -46 }, { 219, -49 }, { 235, -53 } },
    { { 0, 0 }, { 15, -5 }, { 30, -10 }, { 45, -15 }, { 61, -21 }, { 76, -26 }, { 91, -31 }, { 107, -37 }, { 122, -42 }, { 137, -47 }, { 152, -52 }, { 168, -58 }, { 183, -63 }, { 198, -68 }, { 214, -74 }, { 229, -79 } },
    { { 0, 0 }, { 14, -6 }, { 29, -13 }, { 44, -20 }, { 59, -27 }, { 73, -34 }, { 88, -41 }, { 103, -48 }, { 118, -55 }, { 132, -62 }, { 147, -69 }, { 162, -76 }, { 177, -83 }, { 191, -90 }, { 206, -97 }, { 221, -104 } },
    { { 0, 0 }, { 14, -8 }, { 28, -17 }, { 42, -25 }, { 56, -34 }, { 70, -43 }, { 84, -51 }, { 98, -60 }, { 112, -68 }, { 126, -77 }, { 140, -86 }, { 155, -94 }, { 169, -103 }, { 183, -111 }, { 197, -120 }, { 211, -129 } },
    { { 0, 0 }, { 13, -10 }, { 26, -20 }, { 39, -30 }, { 53, -40 }, { 66, -50 }, { 79, -60 }, { 93, -71 }, { 106, -81 }, { 119, -91 }, { 132, -101 }, { 146, -111 }, { 159, -121 }, { 172, -131 }, { 186, -142 }, { 199, -152 } },
    { { 0, 0 }, { 12, -11 }, { 24, -23 }, { 37, -34 }, { 49, -46 }, { 61, -57 }, { 74, -69 }, { 86, -81 }, { 98, -92 }, { 111, -104 }, { 123, -115 }, { 136, -127 }, { 148, -139 }, { 160, -150 }, { 173, -162 }, { 185, -173 } },
    { { 0, 0 }, { 11, -12 }, { 22, -25 }, { 33, -38 }, { 45, -51 }, { 56, -64 }, { 67, -77 }, { 79, -90 }, { 90, -103 }, { 101, -116 }, { 113, -129 }, { 124, -142 }, { 135, -155 }, { 147, -168 }, { 158, -180 }, { 169, -193 } },
    { { 0, 0 }, { 10, -14 }, { 20, -28 }, { 30, -42 }, { 40, -56 }, { 50, -70 }, { 60, -84 }, { 70, -98 }, { 81, -113 }, { 91, -127 }, { 101, -141 }, { 111, -155 }, { 121, -169 }, { 131, -183 }, { 141, -197 }, { 152, -212 } },
    { { 0, 0 }, { 8, -15 }, { 17, -30 }, { 26, -45 }, { 35, -60 }, { 44, -75 }, { 53, -91 }, { 62, -106 }, { 71, -121 }, { 79, -136 }, { 88, -151 }, { 97, -167 }, { 106, -182 }, { 115, -197 }, { 124, -212 }, { 133, -227 } },
    { { 0, 0 }, { 7, -16 }, { 15, -32 }, { 22, -48 }, { 30, -64 }, { 37, -80 }, { 45, -96 }, { 52, -112 }, { 60, -128 }, { 67, -144 }, { 75, -161 }, { 82, -177 }, { 90, -193 }, { 97, -209 }, { 105, -225 }, { 113, -241 } },
    { { 0, 0 }, { 6, -16 }, { 12, -33 }, { 18, -50 }, { 24, -67 }, { 30, -84 }, { 36, -101 }, { 42, -118 }, { 48, -135 }, { 54, -151 }, { 61, -168 }, { 67, -185 }, { 73, -202 }, { 79, -219 }, { 85, -236 }, { 91, -253 } },
    { { 0, 0 }, { 4, -17 }, { 9, -34 }, { 13, -52 }, { 18, -69 }, { 23, -87 }, { 27, -104 }, { 32, -122 }, { 37, -139 }, { 41, -157 }, { 46, -174 }, { 51, -192 }, { 55, -209 }, { 60, -227 }, { 64, -244 }, { 69, -262 } },
    { { 0, 0 }, { 3, -17 }, { 6, -35 }, { 9, -53 }, { 12, -71 }, { 15, -89 }, { 18, -107 }, { 21, -125 }, { 24, -143 }, { 28, -161 }, { 31, -179 }, { 34, -197 }, { 37, -215 }, { 40, -232 }, { 43, -250 }, { 46, -268 } },
    { { 0, 0 }, { 1, -18 }, { 3, -36 }, { 4, -54 }, { 6, -72 }, { 7, -90 }, { 9, -109 }, { 10, -127 }, { 12, -145 }, { 14, -163 }, { 15, -181 }, { 17, -200 }, { 18, -218 }, { 20, -236 }, { 21, -254 }, { 23, -272 } },
    { { 0, 0 }, { 0, -18 }, { 0, -36 }, { 0, -54 }, { 0, -73 }, { 0, -91 }, { 0, -109 }, { 0, -128 }, { 0, -146 }, { 0, -164 }, { 0, -182 }, { 0, -201 }, { 0, -219 }, { 0, -237 }, { 0, -256 }, { 0, -274 } },
    { { 0, 0 }, { -1, -18 }, { -3, -36 }, { -4, -54 }, { -6, -72 }, { -7, -90 }, { -9, -109 }, { -10, -127 }, { -12, -145 }, { -14, -163 }, { -15, -181 }, { -17, -200 }, { -18, -218 }, { -20, -236 }, { -21, -254 }, { -23, -272 } },
    { { 0, 0 }, { -3, -17 }, { -6, -35 }, { -9, -53 }, { -12, -71 }, { -15, -89 }, { -18, -107 }, { -21, -125 }, { -24, -143 }, { -28, -161 }, { -31, -179 }, { -34, -197 }, { -37, -215 }, { -40, -232 }, { -43, -250 }, { -46, -268 } },
    { { 0, 0 }, { -4, -17 }, { -9, -34 }, { -13, -52 }, { -18, -69 }, { -23, -87 }, { -27, -104 }, { -32, -122 }, { -37, -139 }, { -41, -157 }, { -46, -174 }, { -51, -192 }, { -55, -209 }, { -60, -227 }, { -64, -244 }, { -69, -262 } },
    { { 0, 0 }, { -6, -16 }, { -12, -33 }, { -18, -50 }, { -24, -67 }, { -30, -84 }, { -36, -101 }, { -42, -118 }, { -48, -135 }, { -54, -151 }, { -61, -168 }, { -67, -185 }, { -73, -202 }, { -79, -219 }, { -85, -236 }, { -91, -253 } },
    { { 0, 0 }, { -7, -16 }, { -15, -32 }, { -22, -48 }, { -30, -64 }, { -37, -80 }, { -45, -96 }, { -52, -112 }, { -60, -128 }, { -67, -144 }, { -75, -161 }, { -82, -177 }, { -90, -193 }, { -97, -209 }, { -105, -225 }, { -113, -241 } },
    { { 0, 0 }, { -8, -15 }, { -17, -30 }, { -26, -45 }, { -35, -60 }, { -44, -75 }, { -53, -91 }, { -62, -106 }, { -71, -121 }, { -79, -136 }, { -88, -151 }, { -97, -167 }, { -106, -182 }, { -115, -197 }, { -124, -212 }, { -133, -227 } },
    { { 0, 0 }, { -10, -14 }, { -20, -28 }, { -30, -42 }, { -40, -56 }, { -50, -70 }, { -60, -84 }, { -70, -98 }, { -81, -113 }, { -91, -127 }, { -101, -141 }, { -111, -155 }, { -121, -169 }, { -131, -183 }, { -141, -197 }, { -152, -212 } },
    { { 0, 0 }, { -11, -12 }, { -22, -25 }, { -33, -38 }, { -45, -51 }, { -56, -64 }, { -67, -77 }, { -79, -90 }, { -90, -103 }, { -101, -116 }, { -113, -129 }, { -124, -142 }, { -135, -155 }, { -147, -168 }, { -158, -180 }, { -169, -193 } },
    { { 0, 0 }, { -12, -11 }, { -24, -23 }, { -37, -34 }, { -49, -46 }, { -61, -57 }, { -74, -69 }, { -86, -81 }, { -98, -92 }, { -111, -104 }, { -123, -115 }, { -136, -127 }, { -148, -139 }, { -160, -150 }, { -173, -162 }, { -185, -173 } },
    { { 0, 0 }, { -13, -10 }, { -26, -20 }, { -39, -30 }, { -53, -40 }, { -66, -50 }, { -79, -60 }, { -93, -71 }, { -106, -81 }, { -119, -91 }, { -132, -101 }, { -146, -111 }, { -159, -121 }, { -172, -131 }, { -186, -142 }, { -199, -152 } },
    { { 0, 0 }, { -14, -8 }, { -28, -17 }, { -42, -25 }, { -56, -34 }, { -70, -43 }, { -84, -51 }, { -98, -60 }, { -112, -68 }, { -126, -77 }, { -140, -86 }, { -155, -94 }, { -169, -103 }, { -183, -111 }, { -197, -120 }, { -211, -129 } },
    { { 0, 0 }, { -14, -6 }, { -29, -13 }, { -44, -20 }, { -59, -27 }, { -73, -34 }, { -88, -41 }, { -103, -48 }, { -118, -55 }, { -132, -62 }, { -147, -69 }, { -162, -76 }, { -177, -83 }, { -191, -90 }, { -206, -97 }, { -221, -104 } },
    { { 0, 0 }, { -15, -5 }, { -30, -10 }, { -45, -15 }, { -61, -21 }, { -76, -26 }, { -91, -31 }, { -107, -37 }, { -122, -42 }, { -137, -47 }, { -152, -52 }, { -168, -58 }, { -183, -63 }, { -198, -68 }, { -214, -74 }, { -229, -79 } },
    { { 0, 0 }, { -15, -3 }, { -31, -7 }, { -47, -10 }, { -62, -14 }, { -78, -17 }, { -94, -21 }, { -109, -24 }, { -125, -28 }, { -141, -32 }, { -156, -35 }, { -172, -39 }, { -188, -42 }, { -203, -46 }, { -219, -49 }, { -235, -53 } },
    { { 0, 0 }, { -15, -1 }, { -31, -3 }, { -47, -5 }, { -63, -7 }, { -79, -8 }, { -95, -10 }, { -111, -12 }, { -127, -14 }, { -143, -16 }, { -159, -17 }, { -175, -19 }, { -191, -21 }, { -206, -23 }, { -222, -25 }, { -238, -26 } },
};

static const AvspRound1VecS16 avsp_round1_weapon_parent_motion_high[AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT][AVSP_ROUND1_WEAPON_PARENT_HIGH_MOTION_COUNT] =
{
    { { 0, 0 }, { 254, -28 }, { 509, -57 }, { 764, -85 }, { 1018, -114 }, { 1273, -143 }, { 1528, -171 }, { 1782, -200 }, { 2037, -229 }, { 2292, -257 }, { 2546, -286 }, { 2801, -315 }, { 3056, -343 } },
    { { 0, 0 }, { 250, -57 }, { 501, -114 }, { 752, -171 }, { 1003, -228 }, { 1254, -285 }, { 1505, -342 }, { 1756, -399 }, { 2007, -456 }, { 2257, -513 }, { 2508, -570 }, { 2759, -627 }, { 3010, -684 } },
    { { 0, 0 }, { 244, -84 }, { 489, -169 }, { 734, -254 }, { 978, -339 }, { 1223, -423 }, { 1468, -508 }, { 1712, -593 }, { 1957, -678 }, { 2202, -763 }, { 2446, -847 }, { 2691, -932 }, { 2936, -1017 } },
    { { 0, 0 }, { 236, -111 }, { 472, -223 }, { 708, -335 }, { 945, -446 }, { 1181, -558 }, { 1417, -670 }, { 1653, -782 }, { 1890, -893 }, { 2126, -1005 }, { 2362, -1117 }, { 2598, -1228 }, { 2835, -1340 } },
    { { 0, 0 }, { 225, -137 }, { 451, -275 }, { 676, -413 }, { 902, -551 }, { 1127, -688 }, { 1353, -826 }, { 1578, -964 }, { 1804, -1102 }, { 2029, -1240 }, { 2255, -1377 }, { 2480, -1515 }, { 2706, -1653 } },
    { { 0, 0 }, { 212, -162 }, { 425, -324 }, { 638, -487 }, { 850, -649 }, { 1063, -811 }, { 1276, -974 }, { 1488, -1136 }, { 1701, -1298 }, { 1914, -1461 }, { 2126, -1623 }, { 2339, -1785 }, { 2552, -1948 } },
    { { 0, 0 }, { 197, -185 }, { 395, -370 }, { 593, -556 }, { 791, -741 }, { 989, -927 }, { 1187, -1112 }, { 1385, -1298 }, { 1583, -1483 }, { 1780, -1668 }, { 1978, -1854 }, { 2176, -2039 }, { 2374, -2225 } },
    { { 0, 0 }, { 180, -206 }, { 361, -413 }, { 542, -620 }, { 723, -827 }, { 904, -1033 }, { 1085, -1240 }, { 1266, -1447 }, { 1447, -1654 }, { 1628, -1861 }, { 1809, -2067 }, { 1990, -2274 }, { 2171, -2481 } },
    { { 0, 0 }, { 162, -226 }, { 324, -452 }, { 486, -678 }, { 649, -904 }, { 811, -1130 }, { 973, -1356 }, { 1135, -1583 }, { 1298, -1809 }, { 1460, -2035 }, { 1622, -2261 }, { 1784, -2487 }, { 1947, -2713 } },
    { { 0, 0 }, { 142, -243 }, { 284, -486 }, { 426, -729 }, { 568, -972 }, { 710, -1215 }, { 852, -1458 }, { 994, -1701 }, { 1136, -1944 }, { 1278, -2187 }, { 1420, -2430 }, { 1562, -2673 }, { 1704, -2916 } },
    { { 0, 0 }, { 120, -257 }, { 241, -515 }, { 361, -773 }, { 482, -1030 }, { 602, -1288 }, { 723, -1546 }, { 843, -1804 }, { 964, -2061 }, { 1085, -2319 }, { 1205, -2577 }, { 1326, -2834 }, { 1446, -3092 } },
    { { 0, 0 }, { 97, -270 }, { 195, -540 }, { 293, -810 }, { 391, -1080 }, { 488, -1350 }, { 586, -1620 }, { 684, -1890 }, { 782, -2160 }, { 879, -2430 }, { 977, -2700 }, { 1075, -2970 }, { 1173, -3240 } },
    { { 0, 0 }, { 74, -279 }, { 148, -559 }, { 222, -838 }, { 296, -1118 }, { 370, -1398 }, { 445, -1677 }, { 519, -1957 }, { 593, -2237 }, { 667, -2516 }, { 741, -2796 }, { 816, -3076 }, { 890, -3355 } },
    { { 0, 0 }, { 49, -286 }, { 99, -573 }, { 149, -860 }, { 199, -1146 }, { 249, -1433 }, { 299, -1720 }, { 349, -2007 }, { 399, -2293 }, { 448, -2580 }, { 498, -2867 }, { 548, -3153 }, { 598, -3440 } },
    { { 0, 0 }, { 25, -291 }, { 50, -582 }, { 75, -873 }, { 100, -1164 }, { 125, -1455 }, { 150, -1746 }, { 175, -2037 }, { 200, -2328 }, { 225, -2619 }, { 250, -2910 }, { 275, -3201 }, { 300, -3492 } },
    { { 0, 0 }, { 0, -292 }, { 0, -585 }, { 0, -877 }, { 0, -1170 }, { 0, -1462 }, { 0, -1755 }, { 0, -2048 }, { 0, -2340 }, { 0, -2633 }, { 0, -2925 }, { 0, -3218 }, { 0, -3510 } },
    { { 0, 0 }, { -25, -291 }, { -50, -582 }, { -75, -873 }, { -100, -1164 }, { -125, -1455 }, { -150, -1746 }, { -175, -2037 }, { -200, -2328 }, { -225, -2619 }, { -250, -2910 }, { -275, -3201 }, { -300, -3492 } },
    { { 0, 0 }, { -49, -286 }, { -99, -573 }, { -149, -860 }, { -199, -1146 }, { -249, -1433 }, { -299, -1720 }, { -349, -2007 }, { -399, -2293 }, { -448, -2580 }, { -498, -2867 }, { -548, -3153 }, { -598, -3440 } },
    { { 0, 0 }, { -74, -279 }, { -148, -559 }, { -222, -838 }, { -296, -1118 }, { -370, -1398 }, { -445, -1677 }, { -519, -1957 }, { -593, -2237 }, { -667, -2516 }, { -741, -2796 }, { -816, -3076 }, { -890, -3355 } },
    { { 0, 0 }, { -97, -270 }, { -195, -540 }, { -293, -810 }, { -391, -1080 }, { -488, -1350 }, { -586, -1620 }, { -684, -1890 }, { -782, -2160 }, { -879, -2430 }, { -977, -2700 }, { -1075, -2970 }, { -1173, -3240 } },
    { { 0, 0 }, { -120, -257 }, { -241, -515 }, { -361, -773 }, { -482, -1030 }, { -602, -1288 }, { -723, -1546 }, { -843, -1804 }, { -964, -2061 }, { -1085, -2319 }, { -1205, -2577 }, { -1326, -2834 }, { -1446, -3092 } },
    { { 0, 0 }, { -142, -243 }, { -284, -486 }, { -426, -729 }, { -568, -972 }, { -710, -1215 }, { -852, -1458 }, { -994, -1701 }, { -1136, -1944 }, { -1278, -2187 }, { -1420, -2430 }, { -1562, -2673 }, { -1704, -2916 } },
    { { 0, 0 }, { -162, -226 }, { -324, -452 }, { -486, -678 }, { -649, -904 }, { -811, -1130 }, { -973, -1356 }, { -1135, -1583 }, { -1298, -1809 }, { -1460, -2035 }, { -1622, -2261 }, { -1784, -2487 }, { -1947, -2713 } },
    { { 0, 0 }, { -180, -206 }, { -361, -413 }, { -542, -620 }, { -723, -827 }, { -904, -1033 }, { -1085, -1240 }, { -1266, -1447 }, { -1447, -1654 }, { -1628, -1861 }, { -1809, -2067 }, { -1990, -2274 }, { -2171, -2481 } },
    { { 0, 0 }, { -197, -185 }, { -395, -370 }, { -593, -556 }, { -791, -741 }, { -989, -927 }, { -1187, -1112 }, { -1385, -1298 }, { -1583, -1483 }, { -1780, -1668 }, { -1978, -1854 }, { -2176, -2039 }, { -2374, -2225 } },
    { { 0, 0 }, { -212, -162 }, { -425, -324 }, { -638, -487 }, { -850, -649 }, { -1063, -811 }, { -1276, -974 }, { -1488, -1136 }, { -1701, -1298 }, { -1914, -1461 }, { -2126, -1623 }, { -2339, -1785 }, { -2552, -1948 } },
    { { 0, 0 }, { -225, -137 }, { -451, -275 }, { -676, -413 }, { -902, -551 }, { -1127, -688 }, { -1353, -826 }, { -1578, -964 }, { -1804, -1102 }, { -2029, -1240 }, { -2255, -1377 }, { -2480, -1515 }, { -2706, -1653 } },
    { { 0, 0 }, { -236, -111 }, { -472, -223 }, { -708, -335 }, { -945, -446 }, { -1181, -558 }, { -1417, -670 }, { -1653, -782 }, { -1890, -893 }, { -2126, -1005 }, { -2362, -1117 }, { -2598, -1228 }, { -2835, -1340 } },
    { { 0, 0 }, { -244, -84 }, { -489, -169 }, { -734, -254 }, { -978, -339 }, { -1223, -423 }, { -1468, -508 }, { -1712, -593 }, { -1957, -678 }, { -2202, -763 }, { -2446, -847 }, { -2691, -932 }, { -2936, -1017 } },
    { { 0, 0 }, { -250, -57 }, { -501, -114 }, { -752, -171 }, { -1003, -228 }, { -1254, -285 }, { -1505, -342 }, { -1756, -399 }, { -2007, -456 }, { -2257, -513 }, { -2508, -570 }, { -2759, -627 }, { -3010, -684 } },
    { { 0, 0 }, { -254, -28 }, { -509, -57 }, { -764, -85 }, { -1018, -114 }, { -1273, -143 }, { -1528, -171 }, { -1782, -200 }, { -2037, -229 }, { -2292, -257 }, { -2546, -286 }, { -2801, -315 }, { -3056, -343 } },
};

static const AvspRound1VecS16 avsp_round1_weapon_parent_base_motion[AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT] =
{
    { 509, -57 },
    { 501, -114 },
    { 489, -169 },
    { 472, -223 },
    { 451, -275 },
    { 425, -324 },
    { 395, -370 },
    { 361, -413 },
    { 324, -452 },
    { 284, -486 },
    { 241, -515 },
    { 195, -540 },
    { 148, -559 },
    { 99, -573 },
    { 50, -582 },
    { 0, -585 },
    { -50, -582 },
    { -99, -573 },
    { -148, -559 },
    { -195, -540 },
    { -241, -515 },
    { -284, -486 },
    { -324, -452 },
    { -361, -413 },
    { -395, -370 },
    { -425, -324 },
    { -451, -275 },
    { -472, -223 },
    { -489, -169 },
    { -501, -114 },
    { -509, -57 },
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

static const AvspRound1PlayerWeaponEffectSpec avsp_round1_parent_weapon_effect =
{
    0x08F080UL, 24u, 0x49, 0u, 8u, 1u, 1u
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
    12,
    12, 16u,
    127u,
    31u
};

static const AvspRound1CollisionBoxSpec avsp_round1_weapon_parent_attack_boxes[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =
{
    { 0, 0, 0u, 0u, 0, 0u, 0, 0u, 0u },
    { 0, -8, 4u, 12u, 0, 8u, 0, 8u, 25u },
    { 70, 31, 52u, 229u, -86, 141u, -125, 57u, 130u },
};

static const unsigned char avsp_round1_weapon_parent_impact_variants[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =
{
    0u, 10u, 138u
};

static const AvspRound1CollisionBoxSpec avsp_round1_weapon_child_attack_boxes[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =
{
    { 0, 0, 0u, 0u, 0, 0u, 0, 0u, 0u },
    { 0, 10, 16u, 10u, 0, 8u, 1, 8u, 14u },
    { 0, 24, 16u, 24u, 0, 8u, 1, 8u, 14u },
};

static const unsigned char avsp_round1_weapon_child_impact_variants[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =
{
    0u, 1u, 1u
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

static const AvspRound1CoffeeSceneRecordSpec avsp_round1_coffee_scene_records[AVSP_ROUND1_COFFEE_SCENE_RECORD_COUNT] =
{
    { 0x0015c108UL, 0x00ffb600UL, 2072u, 512u, 752, 336, 4u, 0x02, 0u, 0, 0u, 0u, 0u, 0u },
    { 0x0015c128UL, 0x00ffb580UL, 2072u, 512u, 816, 336, 4u, 0x01, 0u, 0, 0u, 0u, 0u, 0u },
    { 0x0015c158UL, 0x00ffb400UL, 2242u, 672u, 1104, 336, 4u, 0x01, 1u, 0, 0u, 0u, 0u, 0u },
    { 0x0015c178UL, 0x00ffb300UL, 2617u, 736u, 1152, 336, 4u, 0x02, 0u, 0, 0u, 0u, 0u, 0u },
};

static const AvspRound1AnimationStateSpec avsp_round1_class01_records[AVSP_ROUND1_CLASS01_PRESENTATION_COUNT] =
{
    { 8u, 0, 0x0006b45aUL, 0x0006b48eUL, 0u, 0u },
    { 8u, 0, 0x0006b46aUL, 0x0006b4b4UL, 0u, 0u },
    { 8u, -32768, 0x0006b47aUL, 0x0006b4daUL, 0u, 0u },
};

static const AvspRound1AnimationStateSpec avsp_round1_class02_records[AVSP_ROUND1_CLASS02_PRESENTATION_COUNT] =
{
    { 4095u, -32768, 0x0006b66cUL, 0x0006b6a8UL, 1u, 0u },
    { 4095u, -32768, 0x0006b680UL, 0x0006b6baUL, 1u, 0u },
};

static const AvspRound1Class01Spec avsp_round1_class01 =
{
    0x06B2FAUL, 0x06B520UL, 240u, 60u, 360u, 192u, 40u,
    5u, 6u, 0x1F, 5u, 0x006du, 0x0139u
};

static const AvspRound1Class02Spec avsp_round1_class02 =
{
    0x06B534UL, 0x06B6EAUL, 0x0011af76UL, 0x0006b6f4UL,
    16u, 0x01A0u, 5u, 28u, 0x05, 1u, 8, 64, -8, 25, -1, 0x0077u, 1u, 0u,
    { 0, 48, 88u, 48u, 0, 40u, 1, 3u, 0u },
    { 8, 64, 8u, 32u, -4, 4u, 0, 0u, 0u }
};

/* Source-display cadence derived from the accepted recurring-controller
 * transaction ledger. This is diagnostic replay timing, not a gameplay
 * transition trigger. */
#define AVSP_ROUND1_COFFEE_SHOP_DEFAULT_SOURCE_UPDATES 1u
#define AVSP_ROUND1_COFFEE_SHOP_UPDATE_CADENCE_COUNT 4
static const AvspRound1SceneUpdateCadence avsp_round1_coffee_shop_update_cadence[AVSP_ROUND1_COFFEE_SHOP_UPDATE_CADENCE_COUNT] =
{
    { 2075u, 3u },
    { 2165u, 4u },
    { 2260u, 0u },
    { 2265u, 0u },
};

/* Diagnostic-only replay of the accepted ORACLE-10 Coffee Shop
 * controller ledger. Native gameplay remains controller-driven;
 * this table exists only for source/native scene differential runs. */
#define AVSP_ROUND1_COFFEE_SHOP_INPUT_RUN_COUNT 177
static const AvspRound1SceneInputRun avsp_round1_coffee_shop_input_runs[AVSP_ROUND1_COFFEE_SHOP_INPUT_RUN_COUNT] =
{
    { 2040u, 2069u, 0x0000u },
    { 2070u, 2074u, 0x0010u },
    { 2075u, 2159u, 0x0000u },
    { 2160u, 2164u, 0x0010u },
    { 2165u, 2249u, 0x0000u },
    { 2250u, 2254u, 0x0010u },
    { 2255u, 2339u, 0x0000u },
    { 2340u, 2344u, 0x0010u },
    { 2345u, 2429u, 0x0000u },
    { 2430u, 2434u, 0x0010u },
    { 2435u, 2519u, 0x0000u },
    { 2520u, 2524u, 0x0010u },
    { 2525u, 2599u, 0x0000u },
    { 2600u, 2609u, 0x0008u },
    { 2610u, 2614u, 0x0018u },
    { 2615u, 2624u, 0x0008u },
    { 2625u, 2630u, 0x0018u },
    { 2631u, 2699u, 0x0008u },
    { 2700u, 2705u, 0x0018u },
    { 2706u, 2774u, 0x0008u },
    { 2775u, 2780u, 0x0018u },
    { 2781u, 2789u, 0x0008u },
    { 2790u, 2794u, 0x0038u },
    { 2795u, 2796u, 0x0028u },
    { 2797u, 2849u, 0x0008u },
    { 2850u, 2855u, 0x0018u },
    { 2856u, 2879u, 0x0008u },
    { 2880u, 2884u, 0x0018u },
    { 2885u, 2924u, 0x0008u },
    { 2925u, 2930u, 0x0018u },
    { 2931u, 2969u, 0x0008u },
    { 2970u, 2974u, 0x0018u },
    { 2975u, 2999u, 0x0008u },
    { 3000u, 3005u, 0x0018u },
    { 3006u, 3009u, 0x0008u },
    { 3010u, 3016u, 0x0048u },
    { 3017u, 3059u, 0x0008u },
    { 3060u, 3064u, 0x0018u },
    { 3065u, 3074u, 0x0008u },
    { 3075u, 3080u, 0x0018u },
    { 3081u, 3099u, 0x0008u },
    { 3100u, 3106u, 0x0028u },
    { 3107u, 3149u, 0x0008u },
    { 3150u, 3155u, 0x0018u },
    { 3156u, 3224u, 0x0008u },
    { 3225u, 3230u, 0x0018u },
    { 3231u, 3239u, 0x0008u },
    { 3240u, 3244u, 0x0018u },
    { 3245u, 3299u, 0x0008u },
    { 3300u, 3305u, 0x0018u },
    { 3306u, 3329u, 0x0008u },
    { 3330u, 3334u, 0x0018u },
    { 3335u, 3374u, 0x0008u },
    { 3375u, 3380u, 0x0018u },
    { 3381u, 3409u, 0x0008u },
    { 3410u, 3416u, 0x0028u },
    { 3417u, 3419u, 0x0008u },
    { 3420u, 3424u, 0x0018u },
    { 3425u, 3439u, 0x0008u },
    { 3440u, 3446u, 0x0048u },
    { 3447u, 3449u, 0x0008u },
    { 3450u, 3455u, 0x0018u },
    { 3456u, 3509u, 0x0008u },
    { 3510u, 3514u, 0x0018u },
    { 3515u, 3524u, 0x0008u },
    { 3525u, 3530u, 0x0018u },
    { 3531u, 3599u, 0x0008u },
    { 3600u, 3605u, 0x0018u },
    { 3606u, 3674u, 0x0008u },
    { 3675u, 3680u, 0x0018u },
    { 3681u, 3689u, 0x0008u },
    { 3690u, 3694u, 0x0018u },
    { 3695u, 3719u, 0x0008u },
    { 3720u, 3726u, 0x0028u },
    { 3727u, 3749u, 0x0008u },
    { 3750u, 3755u, 0x0018u },
    { 3756u, 3779u, 0x0008u },
    { 3780u, 3784u, 0x0018u },
    { 3785u, 3824u, 0x0008u },
    { 3825u, 3830u, 0x0018u },
    { 3831u, 3869u, 0x0008u },
    { 3870u, 3874u, 0x0058u },
    { 3875u, 3876u, 0x0048u },
    { 3877u, 3899u, 0x0008u },
    { 3900u, 3905u, 0x0018u },
    { 3906u, 3959u, 0x0008u },
    { 3960u, 3964u, 0x0018u },
    { 3965u, 3974u, 0x0008u },
    { 3975u, 3980u, 0x0018u },
    { 3981u, 4029u, 0x0008u },
    { 4030u, 4036u, 0x0028u },
    { 4037u, 4049u, 0x0008u },
    { 4050u, 4055u, 0x0018u },
    { 4056u, 4124u, 0x0008u },
    { 4125u, 4130u, 0x0018u },
    { 4131u, 4139u, 0x0008u },
    { 4140u, 4144u, 0x0018u },
    { 4145u, 4199u, 0x0008u },
    { 4200u, 4200u, 0x0000u },
    { 4201u, 4206u, 0x0078u },
    { 4207u, 4207u, 0x0068u },
    { 4208u, 4244u, 0x0008u },
    { 4245u, 4251u, 0x0018u },
    { 4252u, 4289u, 0x0008u },
    { 4290u, 4296u, 0x0018u },
    { 4297u, 4334u, 0x0008u },
    { 4335u, 4341u, 0x0018u },
    { 4342u, 4379u, 0x0008u },
    { 4380u, 4386u, 0x0038u },
    { 4387u, 4387u, 0x0028u },
    { 4388u, 4424u, 0x0008u },
    { 4425u, 4431u, 0x0018u },
    { 4432u, 4439u, 0x0008u },
    { 4440u, 4447u, 0x0048u },
    { 4448u, 4469u, 0x0008u },
    { 4470u, 4476u, 0x0018u },
    { 4477u, 4514u, 0x0008u },
    { 4515u, 4521u, 0x0018u },
    { 4522u, 4559u, 0x0008u },
    { 4560u, 4566u, 0x0038u },
    { 4567u, 4567u, 0x0028u },
    { 4568u, 4604u, 0x0008u },
    { 4605u, 4611u, 0x0018u },
    { 4612u, 4649u, 0x0008u },
    { 4650u, 4656u, 0x0018u },
    { 4657u, 4679u, 0x0008u },
    { 4680u, 4687u, 0x0048u },
    { 4688u, 4694u, 0x0008u },
    { 4695u, 4701u, 0x0018u },
    { 4702u, 4739u, 0x0008u },
    { 4740u, 4746u, 0x0038u },
    { 4747u, 4747u, 0x0028u },
    { 4748u, 4784u, 0x0008u },
    { 4785u, 4791u, 0x0018u },
    { 4792u, 4829u, 0x0008u },
    { 4830u, 4836u, 0x0018u },
    { 4837u, 4874u, 0x0008u },
    { 4875u, 4881u, 0x0018u },
    { 4882u, 4919u, 0x0008u },
    { 4920u, 4926u, 0x0078u },
    { 4927u, 4927u, 0x0068u },
    { 4928u, 4964u, 0x0008u },
    { 4965u, 4971u, 0x0018u },
    { 4972u, 5009u, 0x0008u },
    { 5010u, 5016u, 0x0018u },
    { 5017u, 5054u, 0x0008u },
    { 5055u, 5061u, 0x0018u },
    { 5062u, 5099u, 0x0008u },
    { 5100u, 5106u, 0x0038u },
    { 5107u, 5107u, 0x0028u },
    { 5108u, 5144u, 0x0008u },
    { 5145u, 5151u, 0x0018u },
    { 5152u, 5159u, 0x0008u },
    { 5160u, 5167u, 0x0048u },
    { 5168u, 5189u, 0x0008u },
    { 5190u, 5196u, 0x0018u },
    { 5197u, 5234u, 0x0008u },
    { 5235u, 5241u, 0x0018u },
    { 5242u, 5279u, 0x0008u },
    { 5280u, 5286u, 0x0038u },
    { 5287u, 5287u, 0x0028u },
    { 5288u, 5324u, 0x0008u },
    { 5325u, 5331u, 0x0018u },
    { 5332u, 5369u, 0x0008u },
    { 5370u, 5376u, 0x0018u },
    { 5377u, 5399u, 0x0008u },
    { 5400u, 5407u, 0x0048u },
    { 5408u, 5414u, 0x0008u },
    { 5415u, 5421u, 0x0018u },
    { 5422u, 5459u, 0x0008u },
    { 5460u, 5466u, 0x0038u },
    { 5467u, 5467u, 0x0028u },
    { 5468u, 5504u, 0x0008u },
    { 5505u, 5511u, 0x0018u },
    { 5512u, 5549u, 0x0008u },
    { 5550u, 5556u, 0x0018u },
    { 5557u, 5566u, 0x0008u },
};

#endif

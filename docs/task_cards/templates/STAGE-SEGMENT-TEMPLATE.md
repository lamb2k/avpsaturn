# Stage-segment task-card template

Instantiate only one measured segment at a time. Replace every placeholder and
add the instantiated cards to `project_state.yaml` before activation.

```text
STAGE-<n>-<segment>-CAPTURE
  read-only source evidence; two repeats plus perturbation
STAGE-<n>-<segment>-PACKAGE
  exact assets, palettes, audio, phase manifest, provenance, canaries
STAGE-<n>-<segment>-BEHAVIOR
  route guard, encounters, spawns, AI/collision, boss rules as measured
STAGE-<n>-<segment>-INTEGRATE
  add one dependency to the accepted predecessor
QA-<n>-<segment>
  independent exact-image/readback/workload validation
```

Each card must declare source anchors, current `production_head`, owned paths,
approved regression locks, disabled systems, DEV repeat and negative control,
dedicated diagnostic, pinned-emulator review, phase residency, physical
workload classification, blockers, and exact next experiment. Add USER_REVIEW
only when visible or feel output requires it.

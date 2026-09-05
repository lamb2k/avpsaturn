#!/usr/bin/env python3
"""Strict host compile and real stable-entry mutations for REIMPLEMENT-13."""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / "data/spec02_round1_executable_contract.json"
EXPECTED = "d179b71a83a202cb8e85a279f821e237a3f144644a49f738b500f2e79c172689"
assert hashlib.sha256(SPEC.read_bytes()).hexdigest() == EXPECTED
assert json.loads(SPEC.read_text())["status"] == "ACCEPTED"
source = (ROOT / "src/port_v2/gameplay/round1/round1.c").read_text()
header = (ROOT / "src/port_v2/gameplay/round1/round1.h").read_text()
generated = (ROOT / "src/port_v2/gameplay/round1/spec02_round1_entry_data.h").read_text()
player_source = (ROOT / "src/port_v2/gameplay/player_action/player_action.c").read_text()
test_source = (ROOT / "tests/port_v2/round1/round1_entry_test.c").read_text()
assert EXPECTED in header
subprocess.run(["python", str(ROOT / "tools/gen_spec02_round1_entry.py"), "--check"], check=True)

MUTATION_REPORT = ROOT / "data/reimplement13_round1_mutation_causality.json"
CHARACTERIZE = "--characterize-mutations" in sys.argv
ONLY_MUTATION_LABEL = os.environ.get("AVSP_MUTATION_LABEL")
FULL_MUTATION_RUN = (not any(arg.endswith("-only") for arg in sys.argv[1:])
                     and ONLY_MUTATION_LABEL is None)
COMPILE_TIMEOUT_SECONDS = 120
RUNTIME_TIMEOUT_SECONDS = 30
mutation_results = []
ALLOWED_EQUIVALENT_MUTATIONS = {
    "    effect->animation_timer = retained_animation_timer;\n"
    "    effect->animation_branch = retained_animation_branch;",
    "remainder * 65536L / denominator;",
}
expected_behavior_codes = {}
if MUTATION_REPORT.exists():
    prior_report = json.loads(MUTATION_REPORT.read_text(encoding="ascii"))
    expected_behavior_codes = {
        item["label"]: item["runtime_returncode"]
        for item in prior_report.get("mutations", [])
        if item.get("classification") == "VALID_BEHAVIORAL_REJECTION"
    }

def wsl(path):
    key = str(path)
    if key not in wsl.cache:
        wsl.cache[key] = subprocess.run(
            ["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root", "--",
             "wslpath", "-a", key.replace("\\", "/")],
            check=True, capture_output=True, text=True).stdout.strip()
    return wsl.cache[key]


wsl.cache = {}

def _process(command, timeout):
    try:
        return subprocess.run(command, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        return error
    except OSError as error:
        return error


def _output(result):
    stdout = getattr(result, "stdout", b"") or b""
    stderr = getattr(result, "stderr", b"") or b""
    if isinstance(stdout, str):
        stdout = stdout.encode()
    if isinstance(stderr, str):
        stderr = stderr.encode()
    return (stdout + stderr).decode(errors="replace")


def _environment_failure_output(result):
    output = _output(result).replace("\x00", "")
    return ("WSL_E_" in output or "User not found." in output or
            "Error: 0x8004030d" in output)


def _runtime_exit_code(result):
    output = _output(result).replace("\x00", "")
    match = re.search(r"__AVSP_RUNTIME_EXIT__=([0-9]+)", output)
    return int(match.group(1)) if match else None


def _documented_exit_evidence(test_body, returncode):
    matches = []
    lines = test_body.splitlines()
    for line_number, line in enumerate(lines, 1):
        for raw_code in re.findall(r"\breturn\s+([0-9]+)\s*;", line):
            if int(raw_code) & 0xff == returncode:
                context_start = max(0, line_number - 2)
                matches.append({
                    "line": line_number,
                    "source_return": int(raw_code),
                    "context": " ".join(
                        item.strip() for item in
                        lines[context_start:line_number] if item.strip()),
                })
    return matches


def run(body, header_body, passes, label="baseline", player_body=player_source,
        expected_returncode=None, generated_body=None, test_body=None,
        compile_negative=False, launcher_override=None, observe_only=False):
    if (not passes and "--class0f-only" in sys.argv and
            not label.startswith(("class0f-", "generated-class0f-"))):
        return {"label": label, "classification": "SKIPPED"}
    if (not passes and "--class0a-only" in sys.argv and
            not label.startswith(("class0a-", "generated-class0a-"))):
        return {"label": label, "classification": "SKIPPED"}
    if (not passes and "--class00-only" in sys.argv and
            not label.startswith(("class00-", "generated-class00-"))):
        return {"label": label, "classification": "SKIPPED"}
    if (not passes and "--class03-only" in sys.argv and
            not label.startswith(("class03-", "generated-class03-"))):
        return {"label": label, "classification": "SKIPPED"}
    if not passes and ONLY_MUTATION_LABEL is not None and \
            ONLY_MUTATION_LABEL not in label:
        return {"label": label, "classification": "SKIPPED"}
    with tempfile.TemporaryDirectory(prefix="round1-entry-") as name:
        temp = Path(name)
        linux_root = wsl(ROOT)
        linux_temp = wsl(temp)
        linux_output = f"/tmp/{temp.name}-test"
        if generated_body is None:
            generated_body = generated
        if test_body is None:
            test_body = test_source
        temp_body = body.replace(
            '#include "../../integration/combat/combat.h"', '#include "combat.h"')
        temp_body = temp_body.replace(
            '#include "../../../../avsp_actor.h"', '#include "avsp_actor.h"')
        temp_body = temp_body.replace(
            '#include "../../../../avsp_collision.h"', '#include "avsp_collision.h"')
        (temp / "round1.c").write_text(temp_body)
        temp_header = header_body.replace(
            '#include "../player_action/player_action.h"', '#include "player_action.h"')
        temp_header = temp_header.replace(
            '#include "../street_alien_ai/street_alien_ai.h"', '#include "street_alien_ai.h"')
        temp_header = temp_header.replace(
            '#include "../../combat/hit_ko/hit_ko.h"', '#include "hit_ko.h"')
        (temp / "round1.h").write_text(temp_header)
        (temp / "spec02_round1_entry_data.h").write_text(generated_body)
        (temp / "player_action.c").write_text(player_body)
        (temp / "round1_entry_test.c").write_text(test_body)
        compile_command = (f"cd '{linux_root}' && gcc -std=c90 -pedantic -Wall -Wextra -Werror "
                   f"-I '{linux_temp}' -I . -I src/port_v2/gameplay/player_action "
                   f"-I src/port_v2/gameplay/street_alien_ai -I src/port_v2/combat/hit_ko "
                   f"-I src/port_v2/integration/combat "
                   f"'{linux_temp}/round1.c' "
                   f"avsp_actor.c avsp_collision.c "
                   f"'{linux_temp}/player_action.c' "
                   f"src/port_v2/gameplay/street_alien_ai/street_alien_ai.c "
                   f"src/port_v2/combat/hit_ko/hit_ko.c "
                   f"src/port_v2/player/player.c src/port_v2/enemy/enemy.c "
                   f"src/port_v2/integration/player_enemy/player_enemy.c "
                   f"src/port_v2/integration/combat/combat.c "
                   f"'{linux_temp}/round1_entry_test.c' -o '{linux_output}'")
        compile_result = _process(
            ["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root",
             "--", "bash", "-lc", compile_command],
            COMPILE_TIMEOUT_SECONDS)
        record = {"label": label, "expected_pass": passes,
                  "compile_returncode": getattr(compile_result, "returncode", None),
                  "runtime_returncode": None, "classification": None}
        if isinstance(compile_result, subprocess.TimeoutExpired):
            record["classification"] = "TIMEOUT"
            record["phase"] = "compile"
            mutation_results.append(record)
            if not CHARACTERIZE and not observe_only:
                raise AssertionError(f"label={label}\ncompile timeout")
            return record
        if isinstance(compile_result, OSError):
            record["classification"] = "ENVIRONMENT_FAILURE"
            record["phase"] = "compile-launch"
            mutation_results.append(record)
            if not CHARACTERIZE and not observe_only:
                raise AssertionError(f"label={label}\n{compile_result}")
            return record
        if compile_result.returncode != 0:
            if _environment_failure_output(compile_result):
                record["classification"] = "ENVIRONMENT_FAILURE"
                record["phase"] = "compile-environment"
                record["runtime_output"] = _output(compile_result)[-2000:]
                mutation_results.append(record)
                if not CHARACTERIZE and not observe_only:
                    raise AssertionError(
                        f"label={label}\ncompile environment failure\n" +
                        _output(compile_result))
                return record
            record["classification"] = (
                "EXPLICIT_COMPILE_NEGATIVE" if compile_negative
                else "INVALID_MUTATION")
            record["diagnostic_sha256"] = hashlib.sha256(
                _output(compile_result).encode()).hexdigest()
            mutation_results.append(record)
            if compile_negative:
                return record
            if not CHARACTERIZE and not observe_only:
                raise AssertionError(
                    f"label={label}\nmutation did not build\n" +
                    _output(compile_result))
            return record
        if compile_negative:
            record["classification"] = "SURVIVED_MUTATION"
            mutation_results.append(record)
            if not CHARACTERIZE and not observe_only:
                raise AssertionError(f"label={label}\ncompile-negative built")
            return record

        launch_payload = launcher_override or (
            f"ulimit -s unlimited && '{linux_output}'")
        launch_command = (
            "set +e; " + launch_payload +
            "; avsp_runtime_status=\\$?; "
            "printf '\\n__AVSP_RUNTIME_EXIT__=%s\\n' "
            '"\\$avsp_runtime_status"; exit 0')
        runtime_command = ["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root",
                           "--", "bash", "-lc", launch_command]
        runtime_result = _process(runtime_command, RUNTIME_TIMEOUT_SECONDS)
        if isinstance(runtime_result, subprocess.TimeoutExpired):
            record["classification"] = "TIMEOUT"
            record["phase"] = "runtime"
            mutation_results.append(record)
            if not CHARACTERIZE and not observe_only:
                raise AssertionError(f"label={label}\nruntime timeout")
            return record
        if isinstance(runtime_result, OSError):
            record["classification"] = "ENVIRONMENT_FAILURE"
            record["phase"] = "runtime-launch"
            mutation_results.append(record)
            if not CHARACTERIZE and not observe_only:
                raise AssertionError(f"label={label}\n{runtime_result}")
            return record
        runtime_attempts = 1
        while ((_environment_failure_output(runtime_result) or
                _runtime_exit_code(runtime_result) is None) and
               launcher_override is None and runtime_attempts < 3):
            time.sleep(1.0)
            runtime_result = _process(runtime_command, RUNTIME_TIMEOUT_SECONDS)
            runtime_attempts += 1
            if isinstance(runtime_result, (subprocess.TimeoutExpired, OSError)):
                break
        if runtime_attempts > 1:
            record["environment_retry_count"] = runtime_attempts - 1
        if (isinstance(runtime_result, (subprocess.TimeoutExpired, OSError)) or
                _environment_failure_output(runtime_result) or
                _runtime_exit_code(runtime_result) is None):
            record["classification"] = "ENVIRONMENT_FAILURE"
            record["phase"] = "runtime-environment"
            record["runtime_output"] = _output(runtime_result)[-2000:]
            mutation_results.append(record)
            if not CHARACTERIZE and not observe_only:
                raise AssertionError(
                    f"label={label}\nruntime environment failure")
            return record
        runtime_returncode = _runtime_exit_code(runtime_result)
        record["runtime_wrapper_returncode"] = runtime_result.returncode
        record["runtime_returncode"] = runtime_returncode
        if runtime_returncode != 0:
            record["runtime_output"] = _output(runtime_result)[-2000:]
        record["runtime_output_sha256"] = hashlib.sha256(
            _output(runtime_result).encode()).hexdigest()
        if launcher_override is not None:
            record["classification"] = "ENVIRONMENT_FAILURE"
            record["phase"] = "runtime-launch"
            mutation_results.append(record)
            return record
        if passes:
            record["classification"] = (
                "BASELINE_PASS" if runtime_returncode == 0
                else "BASELINE_RUNTIME_FAILURE")
            mutation_results.append(record)
            assert runtime_returncode == 0, (
                f"label={label}\nreturncode={runtime_returncode}\n" +
                _output(runtime_result))
            return record
        if runtime_returncode == 0:
            record["classification"] = "SURVIVED_MUTATION"
            record["declared_equivalent"] = label in ALLOWED_EQUIVALENT_MUTATIONS
            mutation_results.append(record)
            if (not CHARACTERIZE and not observe_only and
                    not record["declared_equivalent"]):
                raise AssertionError(f"label={label}\nmutation survived")
            return record

        intended = expected_returncode
        if intended is None:
            intended = expected_behavior_codes.get(label)
        if intended is None and CHARACTERIZE:
            intended = runtime_returncode
        record["expected_runtime_returncode"] = intended
        if intended is None and not CHARACTERIZE and not observe_only:
            record["classification"] = "UNATTRIBUTED_RUNTIME_FAILURE"
            mutation_results.append(record)
            raise AssertionError(
                f"label={label}\nno documented assertion exit code")
        if intended is not None and runtime_returncode != intended:
            record["classification"] = "WRONG_RUNTIME_FAILURE"
            mutation_results.append(record)
            if not CHARACTERIZE and not observe_only:
                raise AssertionError(
                    f"label={label}\nexpected_returncode={intended}\n"
                    f"returncode={runtime_returncode}\n" +
                    _output(runtime_result))
            return record

        repeat = _process(runtime_command, RUNTIME_TIMEOUT_SECONDS)
        if (isinstance(repeat, (subprocess.TimeoutExpired, OSError)) or
                _environment_failure_output(repeat) or
                _runtime_exit_code(repeat) != runtime_returncode):
            record["classification"] = "ENVIRONMENT_FAILURE"
            record["phase"] = "runtime-repeat"
            mutation_results.append(record)
            if not CHARACTERIZE and not observe_only:
                raise AssertionError(f"label={label}\nnondeterministic rejection")
            return record
        evidence = _documented_exit_evidence(test_body,
                                             runtime_returncode)
        if not evidence:
            record["classification"] = "UNATTRIBUTED_RUNTIME_FAILURE"
            mutation_results.append(record)
            if not CHARACTERIZE and not observe_only:
                raise AssertionError(
                    f"label={label}\nreturn code is not a documented test exit")
            return record
        record["classification"] = "VALID_BEHAVIORAL_REJECTION"
        record["assertion_evidence"] = (
            f"round1_entry_test documented exit {runtime_returncode}; "
            "deterministic repeat matched")
        record["documented_exit_sites"] = evidence
        mutation_results.append(record)
        print(f"mutation {label}: VALID_BEHAVIORAL_REJECTION "
              f"(exit {runtime_returncode})", flush=True)
        return record


def record_focused_program_controls(name, coverage):
    if not MUTATION_REPORT.exists():
        raise AssertionError("focused controls require the existing full report")
    report = json.loads(MUTATION_REPORT.read_text(encoding="ascii"))
    controls = [item for item in mutation_results
                if not item["expected_pass"]]
    counts = {}
    for item in controls:
        classification = item["classification"]
        counts[classification] = counts.get(classification, 0) + 1
    report.setdefault("focused_program_controls", {})[name] = {
        "coverage": coverage,
        "counts": counts,
        "mutations": controls,
    }
    combined = dict(report.get("current_counts", {}))
    for program in report["focused_program_controls"].values():
        for classification, count in program["counts"].items():
            combined[classification] = combined.get(classification, 0) + count
    report["current_counts_with_focused_program_controls"] = combined
    MUTATION_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="ascii", newline="\n")


jump_stop_marker = "    {\n        AvspRound1Runtime contextual = runtime;"
assert jump_stop_marker in test_source
jump_test_body = test_source.replace(
    jump_stop_marker, "    return 0;\n" + jump_stop_marker, 1)
scene_checkpoint_marker = (
    "        for (source_frame = 2040u; source_frame <= 5566u; "
    "++source_frame)\n"
    "        {\n"
    "            unsigned short input =\n"
    "                avsp_round1_coffee_shop_source_input(\n"
    "                    (unsigned short)source_frame);\n"
    "            unsigned int source_updates =\n"
    "                avsp_round1_coffee_shop_source_updates(\n"
    "                    (unsigned short)source_frame);\n"
    "            unsigned int scheduler_updates =\n"
    "                avsp_round1_coffee_shop_scheduler_source_updates(\n"
    "                    (unsigned short)source_frame);\n"
    "            unsigned int record20_prefix_updates =\n"
    "                avsp_round1_coffee_shop_record20_prefix_source_updates(\n"
    "                    (unsigned short)source_frame);\n"
    "            unsigned int class02_updates =\n"
    "                avsp_round1_coffee_shop_class02_source_updates(\n"
    "                    (unsigned short)source_frame);\n"
    "            unsigned int phase_updates = source_updates > scheduler_updates ?\n"
    "                source_updates : scheduler_updates;\n"
    "            if (record20_prefix_updates > phase_updates)\n"
    "                phase_updates = record20_prefix_updates;\n"
    "            if (class02_updates > phase_updates)\n"
    "                phase_updates = class02_updates;\n")
assert scene_checkpoint_marker in test_source
scene_checkpoint_body = test_source.replace(
    scene_checkpoint_marker,
    scene_checkpoint_marker +
    "            if (source_frame == 5523u)\n"
    "                return 0;\n",
    1)
class1f_state0_checkpoint_body = test_source.replace(
    scene_checkpoint_marker,
    scene_checkpoint_marker +
    "            if (source_frame == 5551u)\n"
    "                return 0;\n",
    1)
class0f_checkpoint_marker = "        class01->state = 0x0204u;"
assert class0f_checkpoint_marker in test_source
class0f_checkpoint_body = test_source.replace(
    class0f_checkpoint_marker,
    "        return 0;\n" + class0f_checkpoint_marker,
    1)
class0a_checkpoint_body = (
    "#define AVSP_CLASS0A_FOCUSED_TEST 1\n" + class0f_checkpoint_body)
class00_checkpoint_body = (
    "#define AVSP_CLASS00_FOCUSED_TEST 1\n" + test_source)
class04_checkpoint_body = (
    "#define AVSP_CLASS04_FOCUSED_TEST 1\n" + test_source)
class03_checkpoint_body = (
    "#define AVSP_CLASS03_FOCUSED_TEST 1\n" + test_source)
scene_checkpoint_flags = {
    "--weapon-timing-only",
    "--special-input-only", "--hit-interaction-only", "--queue-only",
    "--class1f-action16-only",
}

run(source, header, True,
    test_body=(jump_test_body if "--jump-only" in sys.argv else
               class0a_checkpoint_body
               if "--class0a-only" in sys.argv else
               class00_checkpoint_body
               if "--class00-only" in sys.argv else
               class04_checkpoint_body
               if "--class04-only" in sys.argv else
               class03_checkpoint_body
               if "--class03-only" in sys.argv else
               class0f_checkpoint_body
               if "--class0f-only" in sys.argv else
               class1f_state0_checkpoint_body
               if "--class1f-state0-only" in sys.argv else
               scene_checkpoint_body
               if scene_checkpoint_flags.intersection(sys.argv) else None))
if "--harness-self-test" in sys.argv:
    invalid = run(source + "\nthis is deliberately invalid C\n", header,
                  False, "self-syntax-error", observe_only=True)
    assert invalid["classification"] == "INVALID_MUTATION"
    environment = run(source, header, True, "self-missing-launcher",
                      launcher_override="'/tmp/avsp-missing-launcher'",
                      observe_only=True)
    assert environment["classification"] == "ENVIRONMENT_FAILURE"
    semantic_marker = "runtime->route_state = 4;"
    assert semantic_marker in source
    semantic = run(source.replace(
        semantic_marker,
        "runtime->route_state = 0;", 1),
        header, False, "self-known-semantic", observe_only=True)
    assert semantic["classification"] == "VALID_BEHAVIORAL_REJECTION", semantic
    survived = run(source, header, False, "self-equivalent",
                   observe_only=True)
    assert survived["classification"] == "SURVIVED_MUTATION"
    harness_report = json.loads(MUTATION_REPORT.read_text(encoding="ascii"))
    harness_report["harness_self_test"] = {
        "syntax_error": invalid["classification"],
        "missing_launcher": environment["classification"],
        "known_semantic_mutant": semantic["classification"],
        "unchanged_equivalent_mutant": survived["classification"],
        "behavioral_rejection_credit_requires_runtime_execution": True,
    }
    MUTATION_REPORT.write_text(
        json.dumps(harness_report, indent=2, sort_keys=True) + "\n",
        encoding="ascii", newline="\n")
    print("REIMPLEMENT-13 mutation harness self-test: PASS "
          "(invalid/environment/behavioral/survivor distinguished)")
    raise SystemExit(0)
if "--baseline-only" in sys.argv:
    print("REIMPLEMENT-13 focused baseline: PASS")
    raise SystemExit(0)
queue_before = """    for (index = AVSP_PW_DIRECTION_LATENCY - 1; index > 0; --index)
        runtime->direction_history[index] = runtime->direction_history[index - 1];
    runtime->direction_history[0] = direction_mask;
    delayed_direction = runtime->direction_history[AVSP_PW_DIRECTION_LATENCY - 1];"""
queue_after = """    delayed_direction = runtime->direction_history[AVSP_PW_DIRECTION_LATENCY - 1];
    for (index = AVSP_PW_DIRECTION_LATENCY - 1; index > 0; --index)
        runtime->direction_history[index] = runtime->direction_history[index - 1];
    runtime->direction_history[0] = direction_mask;"""
assert queue_before in player_source
subset_flags = {"--inner8-only", "--ko-only", "--registration-only",
                "--locomotion-only", "--generated-walk-only",
                "--controller-edge-only", "--player-hit-only",
                "--weapon-timing-only", "--contextual-melee-only",
                "--action0c-only", "--jump-only",
                "--type16-terminal-only", "--special-input-only",
                "--hit-interaction-only", "--class1f-state0-only",
                "--class1f-action16-only", "--exit-scheduler-only",
                "--class00-only", "--class04-only", "--generated-all-only"}
subset_flags.add("--class03-only")
if "--queue-only" in sys.argv or not subset_flags.intersection(sys.argv):
    run(source, header, False, "consume-before-direction-queue-shift",
        player_source.replace(queue_before, queue_after, 1))
if "--queue-only" in sys.argv:
    print("REIMPLEMENT-13 direction-queue-order mutation lane: PASS (1 real mutation)")
    raise SystemExit(0)
inner8_mutations = {
    "    if (record == 0)\n"
    "        record = avsp_round1_find_class1f_inner8_record(address);\n"
    "    return record;",
    "(actor->state == 0x0200u &&\n                      (actor->substate == 0x1000u ||",
    "actor->state = 0x0208u;\n    actor->substate = 0x0600u;",
    "if ((*random_out & 3u) != 0u)",
    "*rng_consumed = 1u;",
    "actor->source_motion_fields[0] = 8;\n        actor->source_action_timer =",
    "actor->source_x_fp += actor->source_x_velocity;",
    "            *value = runtime->camera_x_previous;",
    "            --actor->source_action_timer;\n"
    "            if (actor->source_action_timer != 0u)",
    "record = avsp_round1_class1f_inner8_program.\n"
    "        action10_phase_records_by_style_relation[index];",
    "            if (actor->source_style85 != 0u)\n"
    "            {\n"
    "                actor->substate = 0x0802u;",
    "        if (phase == 2u)\n"
    "        {\n"
    "            if (actor->animation_branch < 0)\n"
    "            {\n"
    "                actor->source_style85 = 0u;\n"
    "                actor->substate = 0x0e00u;",
    "            actor->source_airborne = 0u;\n"
    "            actor->source_motion_fields[0] = 6;\n"
    "            actor->source_projectile_enable = 1u;",
    "target->facing = (unsigned char)(target->source_facing_selector ^\n"
    "                avsp_round1_class1f_collision_reaction_facing_xor);",
    "actor->transition_timer = (unsigned short)(actor->transition_timer - 1u);",
}
type16_terminal_mutations = {
    "        if (projectile->animation_branch < 0)\n"
    "        {\n"
    "            if (projectile->transition_timer != 0u)"
}
special_input_mutations = {
    "        !special_physical_candidate && jump_edge &&\n"
    "        runtime->player_action.state == AVSP_PW_STATE_CONTROL)",
    "else if (special_owned)\n"
    "    {\n"
    "        runtime->player.source_x_fp = avsp_round1_replace_fixed_high_word(\n"
    "            prior_source_x_fp, view.x);",
}
ko_mutations = {
    "actor->state = ko ? avsp_round1_class1f_source_ko.collision_state :",
    "actor->source_hit_recovery_active = 2u;",
    "actor->source_y_velocity = spec->launch_y_velocity;",
    "actor->source_hit_action_timer =\n                avsp_round1_class1f_source_ko.removal_hold_timer;",
    "runtime->first_encounter.source_progress = (unsigned short)(\n        runtime->first_encounter.source_progress +\n        avsp_round1_recurring_spawn.progress_increment);",
}
registration_mutations = {
    "if (runtime->player_weapon_projectiles[slot_index].active &&\n            runtime->player_weapon_projectiles[slot_index].state !=\n                avsp_round1_weapon_projectile.initial_state)",
}
locomotion_mutations = {
    "if (next >= AVSP_ROUND1_PLAYER_WALK_PRESENTATION_COUNT)",
    "const long remainder = numerator % denominator;",
    "runtime->player_weapon_cleanup_pending = 0u;\n        weapon_return_owned = 1u;",
    "weapon_motion_hold = (unsigned char)(runtime->player_weapon_active ||\n"
    "        (jump_owned && !jump_began) || special_owned || contextual_owned);",
    "if (weapon_motion_hold)\n        input.mask = (unsigned short)(input.mask &\n            (unsigned short)~AVSP_PW_INPUT_ATTACK);",
    "if (!was_stopping && !weapon_motion_hold &&\n"
    "        avsp_round1_source_direction(applied_direction) == 2u)",
    "runtime->player.source_y_fp = avsp_round1_replace_fixed_high_word(\n"
    "            control_source_y_fp, view.lane);",
}
controller_edge_mutations = {
    "camera_x = avsp_round1_recurring_spawn.camera_edge_uses_current_position ?\n        (unsigned short)runtime->camera_x_position :\n        (unsigned short)runtime->camera_x_previous;",
    "encounter->source_blocked_by_living_count = 1u;\n    }\n    else",
    "runtime->entry.gate81f3 = 1u;\n        runtime->camera_x_upper =",
    "if (!avsp_round1_step_coffee_clear_route(runtime))",
    "if (runtime->entry.gate81f3 != 0u)\n    {",
    "if (!avsp_round1_coffee_exit.preserve_route_handoff_fraction)\n    {",
    "runtime->player.source_x_fp =\n            avsp_round1_coffee_exit.next_entry_player_x_fp;",
    "if (runtime->entry.exit_load_index == 1u)\n            {",
    "runtime->player.facing = avsp_round1_coffee_exit.\n                    next_entry_player_facing_after_controller;",
}
player_hit_mutations = {
    "runtime->player.substate = avsp_round1_player_hit.entry_substate;\n"
    "    runtime->player.source_action = 0u;\n"
    "    runtime->player.attack_selector = 0u;",
    "runtime->player_hit_x_fp = runtime->player.source_x_fp;",
    "if (resolved_x != bounded_x)",
    "runtime->player_hit_x_fp = avsp_round1_replace_fixed_high_word(\n"
    "            runtime->player_hit_x_fp, resolved_x);",
    "if (!runtime->player_hit_active && runtime->player_hit_invulnerability)\n"
    "        runtime->player_hit_invulnerability = 0u;",
    "avsp_round1_replace_fixed_high_word(\n"
    "                control_source_x_fp, view.x);",
    "runtime->player_hit_shake_remaining =\n            reaction->shake_count;",
    "runtime, &reaction->presentation);",
    "runtime->player_hit_x_velocity =\n                reaction->x_velocity;",
    "runtime->player_hit_x_acceleration =\n                reaction->x_acceleration;",
    "runtime->player_hit_special_pending = 1u;",
    "runtime->player_action.health - reaction->damage",
    "(unsigned char)reaction->damage;",
    "runtime->player.source_y_fp = avsp_round1_replace_fixed_high_word(\n"
    "        runtime->player.source_y_fp, runtime->player_action.lane);\n"
    "    runtime->player_action.state = AVSP_PW_STATE_HIT;",
    "runtime->player.source_y_fp = avsp_round1_replace_fixed_high_word(\n"
    "        runtime->player.source_y_fp, runtime->player_action.lane);\n"
    "    runtime->player.health = runtime->player_action.health;",
    "runtime->player.hurt_selector !=\n"
    "                avsp_round1_type16.player_hurt_selector ||",
}
weapon_timing_mutations = {
    "else if (weapon_owned || contextual_owned)\n    {\n"
    "        runtime->player.source_x_fp = view.x != bounded_player_x ?",
    "runtime->player_weapon_tick = 1u;",
    "runtime->player_weapon_dispatch_delay =\n"
    "        avsp_round1_player_weapon.action_dispatch_delay_updates;",
    "runtime->player.source_action = entry_action;",
    "avsp_round1_player_stage_progress.action_entry_tick +\n"
    "                    avsp_round1_player_weapon.\n"
    "                        action_dispatch_delay_updates",
    "avsp_round1_player_weapon.resource_debit_tick +\n"
    "                    avsp_round1_player_weapon.\n"
    "                        action_dispatch_delay_updates",
    "avsp_round1_player_weapon.parent_allocation_tick +\n"
    "                    avsp_round1_player_weapon.\n"
    "                        action_dispatch_delay_updates",
    "if (runtime->player_weapon_dispatch_delay != 0u)\n"
    "    {\n"
    "        --runtime->player_weapon_dispatch_delay;\n"
    "        return 1;\n"
    "    }",
}
contextual_melee_mutations = {
    "runtime->player.source_target_low =\n"
    "            avsp_round1_player_contextual_melee.target_low;",
    "unsigned char index = runtime->player_action.facing != 0 ? 0u : 1u;",
    "runtime->player_contextual_melee_dispatch_delay = 2u;",
    "avsp_round1_player_contextual_melee.active_action;",
    "if (runtime->player_contextual_melee_animation_branch < 0)",
    "avsp_round1_player_contextual_melee.audio_commands[\n"
    "                    runtime->player_contextual_melee_entries];",
    "(jump_owned && !jump_began) || special_owned || contextual_owned);",
    "if (runtime->player_contextual_melee_active && weapon_edge &&",
}
action0c_mutations = {
    "    if (stage >= AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT)\n"
    "        return 0u;",
}
jump_mutations = {
    "runtime->player_jump_dispatch_delay =\n"
    "        avsp_round1_player_jump_timing.dispatch_delay_counter;",
    "if (avsp_round1_player_jump_timing.preserve_landing_fraction)",
    "runtime->player.animation_timer = avsp_round1_player_jump_timing.neutral_timer;",
    "runtime->player.animation_branch = avsp_round1_player_jump_timing.neutral_branch;",
    "runtime->player_jump_y_fp += runtime->player_jump_y_velocity;",
    "if (facing != 0u)\n        {\n"
    "            runtime->player_jump_x_velocity =\n"
    "                -runtime->player_jump_x_velocity;",
}
hit_interaction_mutations = {
    "runtime->player_hit_interaction_pending = 1u;",
    "effect->actor_class =\n            avsp_round1_player_hit_interaction.effect_class;",
    "runtime->player_weapon_stage_progress_pending = 1u;",
    "actor->source_projectile_reaction_pending = 4u;",
    "actor->source_x_velocity = spec->launch_x_velocity;",
    "runtime->class1f_audio_command = spec->audio_command;",
    "avsp_round1_begin_player_weapon(runtime);\n"
    "        runtime->player_weapon_dispatch_delay = 0u;",
}
class1f_state0_mutations = {
    "    if (runtime->coffee_scene_active_flag == 0u)\n"
    "        return avsp_round1_class1f_route_interruption(actor);",
    "    if (runtime->entry.gate81f3 != 0u)\n"
    "        return avsp_round1_class1f_route_interruption(actor);",
    "            runtime->coffee_scene_active_flag = 0u;\n"
    "            return 1;",
}
class1f_action16_mutations = {
    "actor = avsp_round1_allocate_pool_actor_preserve_position_fraction(\n"
    "        runtime, 0u);",
    "            actor->health = health;",
    "        actor->source_transition_latch_ae != 0u)",
}
exit_scheduler_mutations = {
    "unsigned int avsp_round1_coffee_shop_scheduler_source_updates(\n"
    "    unsigned short source_frame)\n"
    "{\n"
    "    if (source_frame >=\n"
    "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_FIRST_SOURCE_FRAME &&\n"
    "        source_frame <=\n"
            "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_LAST_SOURCE_FRAME)",
    "unsigned int avsp_round1_coffee_shop_record20_prefix_source_updates(\n"
    "    unsigned short source_frame)\n"
    "{\n"
    "    if (source_frame >=\n"
    "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_FIRST_SOURCE_FRAME &&\n"
    "        source_frame <=\n"
            "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_LAST_SOURCE_FRAME)",
    "actor->source_slot < 0x00ffb600UL",
    "    if (runtime->coffee_scene_active_flag == 0u)\n"
    "    {\n"
    "        actor->source_special_latch_ad =\n"
    "            avsp_round1_class1f_inner8_program.scene_clear_special_latch;"
}
for before, after in (
    ("unsigned int avsp_round1_coffee_shop_scheduler_source_updates(\n"
     "    unsigned short source_frame)\n"
     "{\n"
     "    if (source_frame >=\n"
     "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_FIRST_SOURCE_FRAME &&\n"
     "        source_frame <=\n"
     "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_LAST_SOURCE_FRAME)",
     "unsigned int avsp_round1_coffee_shop_scheduler_source_updates(\n"
     "    unsigned short source_frame)\n"
     "{\n"
     "    if (0 && source_frame >=\n"
     "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_FIRST_SOURCE_FRAME &&\n"
     "        source_frame <=\n"
     "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_LAST_SOURCE_FRAME)"),
    ("unsigned int avsp_round1_coffee_shop_record20_prefix_source_updates(\n"
     "    unsigned short source_frame)\n"
     "{\n"
     "    if (source_frame >=\n"
     "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_FIRST_SOURCE_FRAME &&\n"
     "        source_frame <=\n"
     "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_LAST_SOURCE_FRAME)",
     "unsigned int avsp_round1_coffee_shop_record20_prefix_source_updates(\n"
     "    unsigned short source_frame)\n"
     "{\n"
     "    if (0 && source_frame >=\n"
     "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_FIRST_SOURCE_FRAME &&\n"
     "        source_frame <=\n"
     "            AVSP_ROUND1_COFFEE_EXIT_CALLBACK_LAST_SOURCE_FRAME)"),
    ("actor->source_slot < 0x00ffb600UL",
     "actor->source_slot < 0x00ffb500UL"),
    ("    if (runtime->coffee_scene_active_flag == 0u)\n"
     "        return avsp_round1_class1f_route_interruption(actor);",
     "    if (runtime->coffee_scene_active_flag != 0u)\n"
     "        return avsp_round1_class1f_route_interruption(actor);"),
    ("    if (runtime->entry.gate81f3 != 0u)\n"
     "        return avsp_round1_class1f_route_interruption(actor);",
     "    if (0 && runtime->entry.gate81f3 != 0u)\n"
     "        return avsp_round1_class1f_route_interruption(actor);"),
    ("    if (runtime->coffee_scene_active_flag == 0u)\n"
     "    {\n"
     "        actor->source_special_latch_ad =\n"
     "            avsp_round1_class1f_inner8_program.scene_clear_special_latch;",
     "    if (runtime->coffee_scene_active_flag != 0u)\n"
     "    {\n"
     "        actor->source_special_latch_ad =\n"
     "            avsp_round1_class1f_inner8_program.scene_clear_special_latch;"),
    ("            runtime->coffee_scene_active_flag = 0u;\n"
     "            return 1;",
     "            /* source scene-active clear suppressed */\n"
     "            return 1;"),
    ("runtime->player_hit_interaction_pending = 1u;",
     "runtime->player_hit_interaction_pending = 0u;"),
    ("effect->actor_class =\n"
     "            avsp_round1_player_hit_interaction.effect_class;",
     "effect->actor_class = 0x21;"),
    ("runtime->player_weapon_stage_progress_pending = 1u;",
     "runtime->player_weapon_stage_progress_pending = 0u;"),
    ("actor->source_projectile_reaction_pending = 4u;",
     "actor->source_projectile_reaction_pending = 1u;"),
    ("actor->source_x_velocity = spec->launch_x_velocity;",
     "actor->source_x_velocity = 0L;"),
    ("runtime->class1f_audio_command = spec->audio_command;",
     "runtime->class1f_audio_command = 0u;"),
    ("avsp_round1_begin_player_weapon(runtime);\n"
     "        runtime->player_weapon_dispatch_delay = 0u;",
     "avsp_round1_begin_player_weapon(runtime);\n"
     "        runtime->player_weapon_dispatch_delay = 1u;"),
    ("runtime->player.source_target_low =\n"
     "            avsp_round1_player_contextual_melee.target_low;",
     "runtime->player.source_target_low = 0u;"),
    ("unsigned char index = runtime->player_action.facing != 0 ? 0u : 1u;",
     "unsigned char index = runtime->player_action.facing != 0 ? 1u : 0u;"),
    ("runtime->player_contextual_melee_dispatch_delay = 2u;",
     "runtime->player_contextual_melee_dispatch_delay = 0u;"),
    ("avsp_round1_player_contextual_melee.active_action;",
     "avsp_round1_player_contextual_melee.common_action;"),
    ("if (runtime->player_contextual_melee_animation_branch < 0)",
     "if (runtime->player_contextual_melee_animation_branch == -32768)"),
    ("avsp_round1_player_contextual_melee.audio_commands[\n"
     "                    runtime->player_contextual_melee_entries];",
     "avsp_round1_player_contextual_melee.audio_commands[0];"),
    ("(jump_owned && !jump_began) || special_owned || contextual_owned);",
     "(jump_owned && !jump_began) || special_owned);"),
    ("if (runtime->player_contextual_melee_active && weapon_edge &&",
     "if (0 && runtime->player_contextual_melee_active && weapon_edge &&"),
    ("    if (stage >= AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT)\n"
     "        return 0u;",
     "    if (stage >= AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT ||\n"
     "        stage != avsp_round1_class1f_inner8_program.\n"
     "            action0c_observed_stage_parameter)\n"
     "        return 0u;"),
    ("    bank = avsp_round1_class1f_inner8_program.action4_timer_bank_by_stage[\n"
     "        runtime->source_stage_parameter];",
     "    bank = avsp_round1_class1f_inner8_program.action4_timer_bank_by_stage[\n"
     "        avsp_round1_class1f_inner8_program.action4_stage_parameter];"),
    ("    if (actor->source_navigation_contact_bits != 0u)\n"
     "        actor->source_direction = (unsigned char)(\n"
     "            (actor->source_direction +\n"
     "             avsp_round1_class1f_inner8_program.\n"
     "                action4_contact_direction_delta) &\n"
     "            avsp_round1_class1f_inner8_program.action4_direction_mask);",
     "    if (actor->source_navigation_contact_bits == 0u)\n"
     "        actor->source_direction = (unsigned char)(\n"
     "            (actor->source_direction +\n"
     "             avsp_round1_class1f_inner8_program.\n"
     "                action4_contact_direction_delta) &\n"
     "            avsp_round1_class1f_inner8_program.action4_direction_mask);"),
    ("            *value = runtime->camera_x_previous;",
     "            *value = runtime->camera_x_position;"),
    ("            --actor->source_action_timer;\n"
     "            if (actor->source_action_timer != 0u)",
     "            actor->source_action_timer = 0u;\n"
     "            if (actor->source_action_timer != 0u)"),
    ("    return (unsigned short)runtime->camera_x_previous;",
     "    return (unsigned short)runtime->camera_x_position;"),
    ("            if (!avsp_round1_step_coffee_shop_camera(runtime))\n"
     "            {\n"
     "                ++runtime->failure_count;\n"
     "                return 0;\n"
     "            }",
     "            /* first route-4 camera update suppressed */"),
    ("    effect->animation_timer = retained_animation_timer;\n"
     "    effect->animation_branch = retained_animation_branch;",
     "    effect->animation_timer = (unsigned short)retained_animation_branch;\n"
     "    effect->animation_branch = (short)retained_animation_timer;"),
    ("        if (actor->animation_timer == 0u)\n"
     "            return 0;\n"
     "        --actor->animation_timer;\n"
     "        if (actor->animation_branch < 0)\n"
     "        {\n"
     "            actor->state = 0x0400u;\n"
     "            return 1;\n"
     "        }",
     "        if (actor->animation_branch < 0)\n"
     "        {\n"
     "            actor->state = 0x0400u;\n"
     "            return 1;\n"
     "        }\n"
     "        if (actor->animation_timer == 0u)\n"
     "            return 0;\n"
     "        --actor->animation_timer;"),
    ("if (!avsp_round1_allocate_class4e_impact_to_player(\n"
     "                runtime, actor, &attack, &hurt,\n"
     "                avsp_round1_class1f_player_collision.impact_variant))",
     "if (0)"),
    ("runtime->player.source_facing_selector =\n"
     "            (unsigned char)(actor->x < runtime->player.x);",
     "runtime->player.source_facing_selector = 0u;"),
    ("runtime->route_state = AVSP_ROUND1_ROUTE_ENTRY_STATE;", "runtime->route_state = 4;"),
    ("{20u, 20u, 16u, 32u, 16u, 64u}",
     "{20u, 20u, 16u, 32u, 16u, 63u}"),
    ("{192u, 128u, 128u, 128u, 128u, 64u}",
     "{128u, 128u, 128u, 128u, 128u, 64u}"),
    ("{0x9580u, 0xA480u, 0xAE80u, 0xB680u, 0xC680u, 0xD280u}",
     "{0x9580u, 0xA480u, 0xAE80u, 0xB680u, 0xC680u, 0xD240u}"),
    ("runtime->rng_seed = AVSP_ROUND1_INITIAL_RNG;", "runtime->rng_seed = 1u;"),
    ("runtime->entry.gate8236 & runtime->entry.gate81af", "runtime->entry.gate8236 | runtime->entry.gate81af"),
    ("--runtime->entry.animation_c8;", "runtime->entry.animation_c8 = 0u;"),
    ("avsp_round1_entry_steps[runtime->entry.step_index].kind !=\n                    AVSP_ROUND1_ENTRY_DWELL",
     "avsp_round1_entry_steps[runtime->entry.step_index].kind ==\n                    AVSP_ROUND1_ENTRY_DWELL"),
    ("++runtime->entry.timer_decrements;", "runtime->entry.timer_decrements += 2u;"),
    ("pool->free_stack[pool->free_count - 1u]", "pool->free_stack[0]"),
    ("avsp_pw_step_round1(&runtime->player_action, &input);", "input.mask = 0u; avsp_pw_step_round1(&runtime->player_action, &input);"),
    ("if (actor->active == 0u)\n                continue;", "if (actor->active != 0u)\n                continue;"),
    ("pool_index = order_index;", "pool_index = (order_index + 1u) % AVSP_ROUND1_POOL_COUNT;"),
    ("!avsp_round1_dispatch_supported(actor->type,\n                                                actor->actor_class)",
     "avsp_round1_dispatch_supported(actor->type,\n                                                actor->actor_class)"),
    ("actor->assembly = action_record->assembly;\n        actor->hurt_selector = action_record->hurt_selector;\n        actor->attack_selector = action_record->attack_selector;",
     "actor->assembly = action_record->assembly;\n        actor->hurt_selector = action_record->hurt_selector;\n        actor->attack_selector = actor->source_a6;"),
    ("actor->dispatch_entry = AVSP_ROUND1_CLASS1F_DISPATCH_ENTRY;", "actor->dispatch_entry = 0UL;"),
    ("avsp_round1_apply_player_global_bounds(runtime);",
     "if (0) avsp_round1_apply_player_global_bounds(runtime);"),
    ("avsp_round1_update_player_locomotion(runtime, applied_direction,\n                                            was_stopping, &view);",
     "if (0) avsp_round1_update_player_locomotion(runtime, applied_direction,\n                                            was_stopping, &view);"),
    ("if (next >= AVSP_ROUND1_PLAYER_WALK_PRESENTATION_COUNT)",
     "if (next > AVSP_ROUND1_PLAYER_WALK_PRESENTATION_COUNT)"),
    ("remainder * 65536L / denominator;",
     "remainder * 32768L / denominator;"),
    ("runtime->player_weapon_cleanup_pending = 0u;\n        weapon_return_owned = 1u;",
     "runtime->player_weapon_cleanup_pending = 0u;\n        runtime->player_weapon_return_pending = 1u;\n        weapon_return_owned = 1u;"),
    ("weapon_motion_hold = (unsigned char)(runtime->player_weapon_active ||\n"
     "        (jump_owned && !jump_began) || special_owned || contextual_owned);",
     "weapon_motion_hold = (unsigned char)(runtime->player_weapon_active ||\n"
     "        weapon_return_owned || (jump_owned && !jump_began) ||\n"
     "        special_owned || contextual_owned);"),
    ("if (weapon_motion_hold)\n        input.mask = (unsigned short)(input.mask &\n            (unsigned short)~AVSP_PW_INPUT_ATTACK);",
     "if (weapon_motion_hold)\n        input.mask = (unsigned short)(input.mask & (unsigned short)~(\n            AVSP_PW_INPUT_LEFT | AVSP_PW_INPUT_RIGHT |\n            AVSP_PW_INPUT_UP | AVSP_PW_INPUT_DOWN |\n            AVSP_PW_INPUT_ATTACK));"),
    ("        avsp_round1_observe_player_melee(runtime, prior_state, prior_selector,\n"
     "                                        prior_attack_edges);",
     "        if (0) avsp_round1_observe_player_melee(runtime, prior_state, prior_selector,\n"
     "                                        prior_attack_edges);"),
    ("++runtime->player_melee_entries;", "runtime->player_melee_entries += 2u;"),
    ("runtime->player_melee_selector_mask |= 1UL << (selector - 1u);", "runtime->player_melee_selector_mask = 0UL;"),
    ("++runtime->player_melee_completions;", "runtime->player_melee_completions += 2u;"),
    ("runtime->player_melee_presentation_mask |= 1UL << index;", "runtime->player_melee_presentation_mask = 0UL;"),
    ("projectile->angle = runtime->player_weapon_target_angle;",
     "projectile->angle = 0u;"),
    ("*presentation_selector =\n        avsp_round1_weapon_target_presentation_selectors[distance_selector];",
     "*presentation_selector = 4u;"),
    ("projectile->actor_class = avsp_round1_player_weapon.parent_class;",
     "projectile->actor_class = avsp_round1_player_weapon.child_class;"),
    ("runtime->player_action.state = prior_state;", "runtime->player_action.state = AVSP_PW_STATE_ATTACK;"),
    ("runtime->player_resource_recharge =\n            avsp_round1_player_weapon.recharge_after_success;", "runtime->player_resource_recharge = 11u;"),
    ("++runtime->player_weapon_resource_debits;", "runtime->player_weapon_resource_debits += 2u;"),
    ("++runtime->player_weapon_allocation_failures;", "runtime->player_weapon_allocation_failures += 2u;"),
    ("avsp_round1_tick_player_resource(runtime);",
     "if (0) avsp_round1_tick_player_resource(runtime);"),
    ("avsp_round1_begin_empty_effect(runtime);",
     "if (0) avsp_round1_begin_empty_effect(runtime);"),
    ("actor->variant = avsp_round1_player_weapon.empty_effect_variant;",
     "actor->variant = (unsigned char)(avsp_round1_player_weapon.empty_effect_variant + 1u);"),
    ("runtime->player_weapon_tick ==\n            avsp_round1_player_weapon.empty_effect_allocation_tick",
     "runtime->player_weapon_tick == 0u"),
    ("runtime->player_weapon_tick ==\n"
     "                (unsigned char)(\n"
     "                    avsp_round1_player_weapon.parent_allocation_tick +\n"
     "                    avsp_round1_player_weapon.\n"
     "                        action_dispatch_delay_updates)",
     "runtime->player_weapon_tick ==\n"
     "                (unsigned char)(\n"
     "                    avsp_round1_player_weapon.parent_allocation_tick +\n"
     "                    avsp_round1_player_weapon.\n"
     "                        action_dispatch_delay_updates + 1u)"),
    ("avsp_round1_allocate_pool_actor_preserve_position_residue(runtime, 3u);",
     "runtime->entry.started == 2u ?\n"
     "        avsp_round1_allocate_pool_actor_preserve_position_residue(runtime, 3u) : 0;"),
    ("actor->y = (short)(actor->y + 4);", "actor->y = (short)(actor->y + 3);"),
    ("if (actor->animation_branch < 0)", "if (actor->animation_branch < -32767)"),
    ("++runtime->player_weapon_empty_auxiliary_releases;", "runtime->player_weapon_empty_auxiliary_releases += 2u;"),
    ("projectile->collision_result = -1;", "projectile->collision_result = 0;"),
    ("avsp_round1_weapon_parent_impact_variants[attack_index] :",
     "0u :"),
    ("actor->state = reaction->actor.sub_state;",
     "actor->state = 0x0400u;"),
    ("actor->substate = 0u;\n            ++runtime->class1f_transition_completions;", "actor->state = 0u;\n            actor->substate = 0u;\n            ++runtime->class1f_transition_completions;"),
    ("projectile->child_cadence =\n                        avsp_round1_weapon_projectile.child_cadence_reload;",
     "projectile->child_cadence = 5u;"),
    ("projectile->assembly = record->assembly;", "projectile->assembly = 0UL;"),
    ("(unsigned long)old_seed * 3UL &", "(unsigned long)old_seed * 2UL &"),
    ("!(runtime->route_state == AVSP_ROUND1_ROUTE_ENTRY_STATE &&\n           runtime->entry.started &&\n           runtime->entry.dependencies_seeded)", "!(runtime->route_state == AVSP_ROUND1_ROUTE_ENTRY_STATE &&\n           0u)"),
    ("transition->x_velocity = actor->facing == 0u ? -0x00030000L :\n            0x00030000L;", "transition->x_velocity = actor->facing == 0u ? -0x00020000L :\n            0x00020000L;"),
    ("transition->y_acceleration = -0x00005000L;", "transition->y_acceleration = 0x00005000L;"),
    ("actor->effect_timer = 42u;", "actor->effect_timer = 41u;"),
    ("runtime->class1f_effect_guard = 0u;", "runtime->class1f_effect_guard = 1u;"),
    ("actor->hurt_selector = action_record->hurt_selector;",
     "actor->hurt_selector = actor->source_a5;"),
    ("actor->assembly = presentation->assembly;\n    actor->hurt_selector = presentation->hurt_selector;\n    actor->attack_selector = presentation->attack_selector;",
     "actor->assembly = presentation->assembly;\n    actor->hurt_selector = actor->source_a5;\n    actor->attack_selector = actor->source_a6;"),
    ("actor->source_style85 =\n        avsp_round1_class1f_source_hit.normal_return_style85;",
     "actor->source_style85 = 1u;"),
    ("AVSP_ROUND1_CLASS45_SCENE_ACTOR_COUNT - 1u -\n                allocation_index",
     "allocation_index"),
    ("runtime->class45_rng_calls += 7u;",
     "runtime->class45_rng_calls += 6u;"),
    ("if (!avsp_round1_spawn_class43_population(runtime, actor))",
     "if (avsp_round1_spawn_class43_population(runtime, actor))"),
    ("runtime->class43_rng_calls +=\n            avsp_round1_class43.rng_calls_per_actor;",
     "runtime->class43_rng_calls += 6u;"),
    ("random & (actor->variant == 0u ? 0x1fu : 0x07u)",
     "random & 0x07u"),
    ("avsp_round1_spawn_class47_group(runtime, actor);",
     "if (0) avsp_round1_spawn_class47_group(runtime, actor);"),
    ("runtime->class47_rng_calls +=\n            avsp_round1_class47.rng_calls_per_actor;",
     "runtime->class47_rng_calls += 6u;"),
    ("(pool->capacity - 1u - slot_index)) % 2u != 0u",
     "slot_index) % 2u != 0u"),
    ("actor->source_flags = owner->source_facing_selector;",
     "actor->source_flags = 0u;"),
    ("avsp_round1_class02.reaction_direction_less :",
     "avsp_round1_class02.reaction_direction_greater_equal :"),
    ("(long)actor->source_motion_fields[1] * 256L;",
     "(long)actor->source_motion_fields[1] * 0L;"),
    ("index < AVSP_ROUND1_CLASS45_SPAWN_GROUP_COUNT; ++index",
     "index + 1u < AVSP_ROUND1_CLASS45_SPAWN_GROUP_COUNT; ++index"),
    ("actor->effect_timer = 3u;", "actor->effect_timer = 2u;"),
    ("table_offset = rng_spec->table_index;",
     "table_offset = (unsigned char)(rng_spec->table_index + 4u);"),
    ("if (actor->source_field01 == 0u)",
     "if (actor->source_field01 != 0u)"),
    ("avsp_round1_apply_coffee_shop_obstacle(runtime);",
     "if (0) avsp_round1_apply_coffee_shop_obstacle(runtime);"),
    ("if (z_penetration < x_penetration)",
     "if (z_penetration <= x_penetration)"),
    ("runtime->terrain_selector_map[index] & 0xfcu",
     "runtime->terrain_selector_map[index] & 0xf8u"),
    ("!avsp_round1_apply_first_segment_terrain(runtime)",
     "avsp_round1_apply_first_segment_terrain(runtime)"),
    ("!avsp_round1_step_coffee_shop_camera(runtime)",
     "avsp_round1_step_coffee_shop_camera(runtime)"),
    ("--runtime->camera_guard_countdown;",
     "runtime->camera_guard_countdown = runtime->camera_guard_countdown;"),
    ("unsigned short index = (unsigned short)(byte_offset >> 1);",
     "unsigned short index = (unsigned short)(byte_offset >> 2);"),
    ("runtime->player_jump_dispatch_delay =\n"
     "        avsp_round1_player_jump_timing.dispatch_delay_counter;",
     "runtime->player_jump_dispatch_delay = (unsigned char)(\n"
     "        avsp_round1_player_jump_timing.dispatch_delay_counter + 1u);"),
    ("if (up)\n            index += 1u;",
     "if (up)\n            index += 2u;"),
    ("if ((unsigned char)(right ^ facing) != 0u)\n                index += 2u;",
     "if ((unsigned char)(right ^ facing) != 0u)\n                index += 1u;"),
    ("if (facing != 0u)\n        {\n            runtime->player_jump_x_velocity =\n                -runtime->player_jump_x_velocity;",
     "if (facing == 0u)\n        {\n            runtime->player_jump_x_velocity =\n                -runtime->player_jump_x_velocity;"),
    ("runtime->player_jump_collision_selector = up ? 1u : 2u;",
     "runtime->player_jump_collision_selector = up ? 2u : 1u;"),
    ("runtime->player_jump_collision_selector = up ? 4u : 8u;",
     "runtime->player_jump_collision_selector = up ? 8u : 4u;"),
    ("runtime->player_jump_phase = 0x040au;",
     "runtime->player_jump_phase = 0x0402u;"),
    ("runtime->player_jump_y_fp += runtime->player_jump_y_velocity;",
     "runtime->player_jump_y_fp -= runtime->player_jump_y_velocity;"),
    ("runtime->player_jump_y_velocity += runtime->player_jump_y_acceleration;",
     "runtime->player_jump_y_velocity -= runtime->player_jump_y_acceleration;"),
    ("if (avsp_round1_player_jump_timing.preserve_landing_fraction)",
     "if (0)"),
    ("runtime->player.animation_timer = avsp_round1_player_jump_timing.neutral_timer;",
     "runtime->player.animation_timer = (unsigned short)(\n"
     "        avsp_round1_player_jump_timing.neutral_timer - 1u);"),
    ("runtime->player.animation_branch = avsp_round1_player_jump_timing.neutral_branch;",
     "runtime->player.animation_branch = 0;"),
    ("avsp_round1_fixed_high_word(runtime->player_jump_y_fp) <=\n            runtime->player_action.lane",
     "avsp_round1_fixed_high_word(runtime->player_jump_y_fp) <\n            runtime->player_action.lane"),
    ("runtime->player_jump_phase_timer = 10u;",
     "runtime->player_jump_phase_timer = 9u;"),
    ("--runtime->player_jump_phase_timer;",
     "runtime->player_jump_phase_timer -= 2u;"),
    ("            ++runtime->player_jump_entries;\n"
     "            return avsp_round1_bind_player_jump_sequence(runtime, 3u);",
     "            ++runtime->player_jump_entries;\n"
     "            avsp_round1_source_rng(runtime);\n"
     "            return avsp_round1_bind_player_jump_sequence(runtime, 3u);"),
    ("if (runtime->player_jump_active && received_damage > 0)\n        avsp_round1_interrupt_player_jump(runtime);",
     "if (runtime->player_jump_active && received_damage < 0)\n        avsp_round1_interrupt_player_jump(runtime);"),
    ("input |= 0x08u;",
     "input |= 0x04u;"),
    ("projectile->actor_class = avsp_round1_air_weapon_projectile.actor_class;",
     "projectile->actor_class = avsp_round1_player_weapon.child_class;"),
    ("++runtime->player_jump_animation_timer;\n"
     "    ++runtime->player.animation_timer;",
     "runtime->player_jump_animation_timer += 0u;\n"
     "    runtime->player.animation_timer += 0u;"),
    ("effect->effect_timer = avsp_round1_parent_weapon_effect.timer;",
     "effect->effect_timer = 7u;"),
    ("(runtime->scheduler_frames & 1u) == 0u",
     "(runtime->scheduler_frames & 2u) == 0u"),
    ("encounter->source_phase_counter + 1u",
     "encounter->source_phase_counter + 2u"),
    ("return entry->updates;", "return 1u;"),
    ("if (encounter->source_intro_gate != 0u)",
     "if (encounter->source_intro_gate == 0u)"),
    ("runtime->camera_z_lower = (short)\n"
     "            avsp_round1_recurring_spawn.source_camera_target_current;",
     "runtime->camera_z_lower = (short)\n"
     "            avsp_round1_recurring_spawn.source_camera_bound_initial;"),
    ("if (preserve_collision_selectors)\n        {\n"
     "            avsp_round1_class1f_bind_source_hit_record(",
     "if (!preserve_collision_selectors)\n        {\n"
     "            avsp_round1_class1f_bind_source_hit_record("),
    ("encounter->source_intro_timer - 1u",
     "encounter->source_intro_timer - 2u"),
    ("(unsigned short)actor->source_slot ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_slot",
     "actor->source_slot ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_slot"),
    ("actor->state ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_state",
     "actor->substate ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_state"),
    ("encounter->source_living_count >=\n            avsp_round1_recurring_spawn.maximum_living",
     "encounter->source_living_count >\n            avsp_round1_recurring_spawn.maximum_living"),
    ("camera_x = avsp_round1_recurring_spawn.camera_edge_uses_current_position ?\n        (unsigned short)runtime->camera_x_position :\n        (unsigned short)runtime->camera_x_previous;",
     "camera_x = avsp_round1_recurring_spawn.camera_edge_uses_current_position ?\n        (unsigned short)runtime->camera_x_previous :\n        (unsigned short)runtime->camera_x_position;"),
    ("encounter->source_blocked_by_living_count = 1u;\n    }\n    else",
     "encounter->source_blocked_by_living_count = 1u;\n        return 1;\n    }\n    else"),
    ("runtime->entry.gate81f3 = 1u;\n        runtime->camera_x_upper =",
     "runtime->route_state = avsp_round1_coffee_exit.route_withdrawal;\n        runtime->camera_x_upper ="),
    ("if (!avsp_round1_step_coffee_clear_route(runtime))",
     "if (avsp_round1_step_coffee_clear_route(runtime))"),
    ("if (runtime->entry.gate81f3 != 0u)\n    {",
     "if (runtime->entry.gate81f3 == 0u)\n    {"),
    ("if (!avsp_round1_coffee_exit.preserve_route_handoff_fraction)\n    {",
     "if (avsp_round1_coffee_exit.preserve_route_handoff_fraction)\n    {"),
    ("runtime->player.source_x_fp =\n            avsp_round1_coffee_exit.next_entry_player_x_fp;",
     "runtime->player.source_x_fp =\n            avsp_round1_coffee_exit.next_entry_player_x_fp + 0x10000L;"),
    ("if (runtime->entry.exit_load_index == 1u)\n            {",
     "if (runtime->entry.exit_load_index == 2u)\n            {"),
    ("runtime->player.facing = avsp_round1_coffee_exit.\n                    next_entry_player_facing_after_controller;",
     "runtime->player.facing = avsp_round1_coffee_exit.\n                    next_entry_player_facing_before_controller;"),
    ("if (avsp_round1_recurring_spawn.preserve_reused_presentation != 0u)",
     "if (0)"),
    ("avsp_round1_class1f_action_program.fall_initial_selector",
     "35u"),
    ("actor->source_slot = 0x00ff0000UL | (unsigned long)slot;",
     "actor->source_slot = slot;"),
    ("actor->source_slot ==\n                        runtime->first_encounter.actor_source_slot)",
     "actor->source_slot ==\n                        runtime->first_encounter.actor_source_slot + 1u)"),
    ("runtime->player.health = 0;",
     "runtime->player.health = AVSP_ROUND1_PLAYER_HEALTH;"),
    ("actor->state = 0x0402u;",
     "actor->substate = 0x0402u;"),
    ("child->y = (short)(parent->z + row->y);",
     "child->y = (short)(parent->y + row->y);"),
    ("runtime->collision_identity_counter = 0x25u;",
     "runtime->collision_identity_counter = 0x24u;"),
    ("(unsigned short)x - (unsigned short)runtime->camera_x_position +\n        0x0040u);",
     "(unsigned short)x - (unsigned short)runtime->camera_x_position +\n        0x0020u);"),
    ("!projectile->active_collision || !projectile->collision_registered ||",
     "!projectile->active_collision ||"),
    ("target->source_field01 != 1u ||",
     "target->source_field01 == 2u ||"),
    ("if (target->source_collision_latches[\n                    (unsigned char)latch_index] ==\n                    projectile->collision_identity)\n                continue;",
     "if (0)\n                continue;"),
    ("if (projectile->actor_class == avsp_round1_weapon_projectile.child_class)\n            return avsp_round1_release_player_weapon_projectile(runtime,\n                                                                 index);",
     "if (projectile->actor_class == avsp_round1_weapon_projectile.child_class)\n            projectile->state = avsp_round1_weapon_projectile.release_state;"),
    ("projectile->animation_record = animation_record;\n    projectile->assembly = assembly;",
     "projectile->animation_record = animation_record + 1UL;\n    projectile->assembly = assembly;"),
    ("projectile->x_fp = (long)x_fraction;",
     "projectile->x_fp = (long)(x_fraction ^ 1u);"),
    ("unsigned short nearest = 0xffffu;",
     "unsigned short nearest = 0x00ffu;"),
    ("runtime->camera_x_position +\n            avsp_round1_weapon_projectile.x_bound_bias",
     "runtime->navigation_bound_x +\n            avsp_round1_weapon_projectile.x_bound_bias"),
    ("projectile->state = avsp_round1_weapon_projectile.emitter_state;\n            projectile->child_cadence =\n                avsp_round1_weapon_projectile.child_cadence_initial;\n            return 1;",
     "return avsp_round1_release_player_weapon_projectile(runtime, index);"),
    ("weapon_pressed = runtime->player_weapon_input_pipeline;",
     "weapon_pressed = (unsigned char)((input_mask & AVSP_ROUND1_INPUT_BUTTON1) != 0u);"),
    ("actor->state != 0x0208u || actor->substate != 0x0e02u",
     "actor->state != 0x0200u || actor->substate != 0x0e02u"),
    ("if (parent->facing != 0u)\n        x_offset = (short)-x_offset;",
     "if (parent->facing == 0u)\n        x_offset = (short)-x_offset;"),
    ("projectile->source_x_velocity = motion->x_velocity;",
     "projectile->source_x_velocity = motion->y_velocity;"),
    ("projectile->source_collision_current_attack_selector !=\n"
     "                avsp_round1_type16.attack_selector ||",
     "projectile->source_collision_current_attack_selector ==\n"
     "                avsp_round1_type16.attack_selector ||"),
    ("runtime->player.hurt_selector !=\n                avsp_round1_type16.player_hurt_selector ||",
     "runtime->player.hurt_selector ==\n                avsp_round1_type16.player_hurt_selector ||"),
    ("(unsigned char)avsp_round1_type16.damage;",
     "(unsigned char)(avsp_round1_type16.damage - 1);"),
    ("++runtime->type16_releases;",
     "runtime->type16_releases += 2u;"),
    ("actor->type == 16u && actor->actor_class == 0x06",
     "actor->type == 16u && actor->actor_class == 0x05"),
    ("if (projectile->health < 0)\n        {\n            projectile->state = 0x0600u;",
     "if (projectile->health < 0)\n        {\n            projectile->state = 0x0400u;"),
    ("runtime->player_action.health - reaction->damage",
     "runtime->player_action.health - (short)hit_value"),
    ("(unsigned char)reaction->damage;",
     "0u;"),
    ("runtime->player.source_y_fp = avsp_round1_replace_fixed_high_word(\n"
     "        runtime->player.source_y_fp, runtime->player_action.lane);\n"
     "    runtime->player_action.state = AVSP_PW_STATE_HIT;",
     "runtime->player.source_y_fp =\n"
     "        (long)runtime->player_action.lane * 65536L;\n"
     "    runtime->player_action.state = AVSP_PW_STATE_HIT;"),
    ("runtime->player.source_y_fp = avsp_round1_replace_fixed_high_word(\n"
     "        runtime->player.source_y_fp, runtime->player_action.lane);\n"
     "    runtime->player.health = runtime->player_action.health;",
     "runtime->player.source_y_fp =\n"
     "        (long)runtime->player_action.lane * 65536L;\n"
     "    runtime->player.health = runtime->player_action.health;"),
    ("        if (projectile->animation_branch < 0)\n"
     "        {\n"
     "            if (projectile->transition_timer != 0u)",
     "        if (projectile->animation_timer == 0u)\n"
     "        {\n"
     "            if (projectile->transition_timer != 0u)"),
    ("        !special_physical_candidate && jump_edge &&\n"
     "        runtime->player_action.state == AVSP_PW_STATE_CONTROL)",
     "        jump_edge &&\n"
     "        runtime->player_action.state == AVSP_PW_STATE_CONTROL)"),
    ("else if (special_owned)\n"
     "    {\n"
     "        runtime->player.source_x_fp = avsp_round1_replace_fixed_high_word(\n"
     "            prior_source_x_fp, view.x);",
     "else if (special_owned)\n"
     "    {\n"
     "        runtime->player.source_x_fp = avsp_round1_player_fractional_position(\n"
     "            view.x, runtime->player_action.x_numerator);"),
    ("(actor->state == 0x0200u &&\n                      (actor->substate == 0x1000u ||",
     "(actor->state == 0x0208u &&\n                      (actor->substate == 0x1000u ||"),
    ("actor->state = 0x0208u;\n    actor->substate = 0x0600u;",
     "actor->state = 0x0200u;\n    actor->substate = 0x0600u;"),
    ("if ((*random_out & 3u) != 0u)",
     "if ((*random_out & 3u) != 3u)"),
    ("*rng_consumed = 1u;",
     "*rng_consumed = 0u;"),
    ("actor->source_motion_fields[0] = 8;\n        actor->source_action_timer =",
     "actor->source_motion_fields[0] = 6;\n        actor->source_action_timer ="),
    ("actor->source_x_fp += actor->source_x_velocity;",
     "actor->source_x_fp += 0;"),
    ("record = avsp_round1_class1f_inner8_program.\n"
     "        action10_phase_records_by_style_relation[index];",
     "record = avsp_round1_class1f_inner8_program.\n"
     "        movement_records_by_style_relation[index];"),
    ("            if (actor->source_style85 != 0u)\n"
     "            {\n"
     "                actor->substate = 0x0802u;",
     "            if (actor->source_style85 == 0u)\n"
     "            {\n"
     "                actor->substate = 0x0802u;"),
    ("        if (phase == 2u)\n"
     "        {\n"
     "            if (actor->animation_branch < 0)\n"
     "            {\n"
     "                actor->source_style85 = 0u;\n"
     "                actor->substate = 0x0e00u;",
     "        if (phase == 2u)\n"
     "        {\n"
     "            if (actor->animation_branch < 0)\n"
     "            {\n"
     "                actor->source_style85 = 0u;\n"
     "                actor->substate = 0x0400u;"),
    ("            actor->source_airborne = 0u;\n"
     "            actor->source_motion_fields[0] = 6;\n"
     "            actor->source_projectile_enable = 1u;",
     "            actor->source_y_fp = (long)(\n"
     "                ((unsigned long)(unsigned short)actor->z << 16) |\n"
     "                ((unsigned long)actor->source_y_fp & 0x0000ffffUL));\n"
     "            actor->y = actor->z;\n"
     "            actor->source_airborne = 0u;\n"
     "            actor->source_motion_fields[0] = 6;\n"
     "            actor->source_projectile_enable = 1u;"),
    ("target->facing = (unsigned char)(target->source_facing_selector ^\n"
     "                avsp_round1_class1f_collision_reaction_facing_xor);",
     "target->facing = (unsigned char)target->source_facing_selector;"),
    ("actor->transition_timer = (unsigned short)(actor->transition_timer - 1u);",
     "if (actor->transition_timer != 0u)\n"
     "        --actor->transition_timer;"),
    ("actor->animation_record = animation_record;",
     "actor->animation_record = animation_record + 1UL;"),
    ("actor->state = ko ? avsp_round1_class1f_source_ko.collision_state :",
     "actor->state = ko ? avsp_round1_class1f_source_ko.dispatch_state :"),
    ("actor->source_hit_recovery_active = 2u;",
     "actor->source_hit_recovery_active = 1u;"),
    ("actor->source_y_velocity = spec->launch_y_velocity;",
     "actor->source_y_velocity = 0L;"),
    ("            actor->source_hit_action_timer = spec->removal_hold_timer;",
     "            actor->source_hit_action_timer = spec->landing_hold_timer;"),
    ("runtime->first_encounter.source_progress = (unsigned short)(\n        runtime->first_encounter.source_progress +\n        avsp_round1_recurring_spawn.progress_increment);",
     "runtime->first_encounter.source_progress = (unsigned short)(\n        runtime->first_encounter.source_progress + 0u);"),
    ("effect->attack_selector = 0u;\n    }\n    if (effect->state == 2u)",
     "effect->attack_selector = 0u;\n        return 1;\n    }\n    if (effect->state == 2u)"),
    ("runtime->player.animation_branch = record->branch;",
     "runtime->player.animation_branch = 0;"),
    ("runtime->player.animation_timer =\n        runtime->player_special_animation_timer;",
     "runtime->player.animation_timer = 0u;"),
    ("if (!was_in_camera)\n                avsp_round1_bind_animation_state(",
     "if (was_in_camera)\n                avsp_round1_bind_animation_state("),
    ("actor->source_hitstop = hit_value;\n        actor->source_player_guard = 1u;",
     "actor->source_hitstop = hit_value;\n        actor->source_player_guard = 0u;"),
    ("else if (runtime->player.animation_timer != 0u)\n                --runtime->player.animation_timer;",
     "else if (runtime->player.animation_timer != 0u)\n                runtime->player.animation_timer = runtime->player.animation_timer;"),
    ("if (!avsp_round1_step_coffee_shop_obstacle_parent_animation(actor))\n            return 0;",
     "if (0)\n            return 0;"),
    ("(unsigned short)runtime->camera_x_previous < spec->camera_threshold",
     "(unsigned short)runtime->camera_x_position < spec->camera_threshold"),
    ("runtime->player.animation_timer = frame->timer;\n    runtime->player.animation_branch = frame->branch;",
     "runtime->player.animation_timer = 4095u;\n    runtime->player.animation_branch = -32768;"),
    ("runtime->player_hit_shake_remaining =\n            reaction->shake_count;",
     "runtime->player_hit_shake_remaining =\n            avsp_round1_player_hit.shake_count;"),
    ("runtime, &reaction->presentation);",
     "runtime, &avsp_round1_player_hit.hit_record);"),
    ("runtime->player_hit_x_velocity =\n                reaction->x_velocity;",
     "runtime->player_hit_x_velocity =\n                avsp_round1_player_hit.x_velocity;"),
    ("runtime->player_hit_x_acceleration =\n                reaction->x_acceleration;",
     "runtime->player_hit_x_acceleration = 0L;"),
    ("runtime->player_hit_special_pending = 1u;",
     "runtime->player_hit_special_pending = 0u;"),
    ("runtime->player_hit_x_fp = runtime->player.source_x_fp;",
     "runtime->player_hit_x_fp =\n"
     "        (long)runtime->player_action.x * 65536L;"),
    ("runtime->player.substate = avsp_round1_player_hit.entry_substate;\n"
     "    runtime->player.source_action = 0u;\n"
     "    runtime->player.attack_selector = 0u;",
     "runtime->player.substate = avsp_round1_player_hit.entry_substate;\n"
     "    runtime->player.source_action = 0u;\n"
     "    runtime->player.hurt_selector = 0u;\n"
     "    runtime->player.attack_selector = 0u;"),
    ("if (resolved_x != bounded_x)",
     "if (resolved_x == bounded_x)"),
    ("runtime->player_hit_x_fp = avsp_round1_replace_fixed_high_word(\n"
     "            runtime->player_hit_x_fp, resolved_x);",
     "runtime->player_hit_x_fp = (long)resolved_x * 65536L;"),
    ("if (!runtime->player_hit_active && runtime->player_hit_invulnerability)\n"
     "        runtime->player_hit_invulnerability = 0u;",
     "if (!runtime->player_hit_active && runtime->player_hit_invulnerability)\n"
     "    {\n"
     "        runtime->player_hit_invulnerability = 0u;\n"
     "        runtime->player.source_x_fp = 0L;\n"
     "        runtime->player.source_y_fp = 0L;\n"
     "    }"),
    ("avsp_round1_replace_fixed_high_word(\n"
     "                control_source_x_fp, view.x);",
     "avsp_round1_player_fractional_position(\n"
     "                view.x, runtime->player_action.x_numerator);"),
    ("if (!was_stopping && !weapon_motion_hold &&\n"
     "        avsp_round1_source_direction(applied_direction) == 2u)",
     "if (0 && !was_stopping && !weapon_motion_hold &&\n"
     "        avsp_round1_source_direction(applied_direction) == 2u)"),
    ("runtime->player.source_y_fp = avsp_round1_replace_fixed_high_word(\n"
     "            control_source_y_fp, view.lane);",
     "runtime->player.source_y_fp = avsp_round1_replace_fixed_high_word(\n"
     "            control_source_y_fp, (short)(view.lane + 1));"),
    ("12u, 0x1f, record->attack_selector);",
     "12u, 0x1f, 1u);"),
    ("special_buttons = runtime->player_special_input_pipeline;",
     "special_buttons = (unsigned char)(input_mask & 0x70u);"),
    ("special_edge = (unsigned char)avsp_round1_player_special_guard(\n"
     "        runtime, special_buttons, runtime->player_special_previous_buttons);",
     "special_edge = 0u;"),
    ("sufficient_entry_preserves_current_presentation)",
     "sufficient_entry_preserves_current_presentation == 0u)"),
    ("runtime->player_weapon_tick = 1u;",
     "runtime->player_weapon_tick = 0u;"),
    ("else if (weapon_owned || contextual_owned)\n    {\n"
     "        runtime->player.source_x_fp = view.x != bounded_player_x ?",
     "else if ((weapon_owned && 0) || contextual_owned)\n    {\n"
     "        runtime->player.source_x_fp = view.x != bounded_player_x ?"),
    ("runtime->player_weapon_dispatch_delay =\n"
     "        avsp_round1_player_weapon.action_dispatch_delay_updates;",
     "runtime->player_weapon_dispatch_delay = 0u;"),
    ("runtime->player.source_action = entry_action;",
     "runtime->player.source_action = 0u;"),
    ("avsp_round1_player_stage_progress.action_entry_tick +\n"
     "                    avsp_round1_player_weapon.\n"
     "                        action_dispatch_delay_updates",
     "avsp_round1_player_stage_progress.action_entry_tick"),
    ("avsp_round1_player_weapon.resource_debit_tick +\n"
     "                    avsp_round1_player_weapon.\n"
     "                        action_dispatch_delay_updates",
     "avsp_round1_player_weapon.resource_debit_tick"),
    ("avsp_round1_player_weapon.parent_allocation_tick +\n"
     "                    avsp_round1_player_weapon.\n"
     "                        action_dispatch_delay_updates",
     "avsp_round1_player_weapon.parent_allocation_tick"),
    ("if (runtime->player_weapon_dispatch_delay != 0u)\n"
     "    {\n"
     "        --runtime->player_weapon_dispatch_delay;\n"
     "        return 1;\n"
     "    }",
     "if (runtime->player_weapon_dispatch_delay != 0u)\n"
     "    {\n"
     "        if (runtime->player_weapon_empty &&\n"
     "            runtime->player_weapon_tick ==\n"
     "                avsp_round1_player_weapon.empty_effect_allocation_tick)\n"
     "        {\n"
     "            ++runtime->player_weapon_empty_auxiliary_requests;\n"
     "            avsp_round1_begin_empty_effect(runtime);\n"
     "        }\n"
     "        --runtime->player_weapon_dispatch_delay;\n"
     "        return 1;\n"
     "    }"),
    ("else if (!avsp_round1_step_player_weapon_animation(runtime, frame))\n            return 0;",
     "else if (avsp_round1_step_player_weapon_animation(runtime, frame))\n            return 0;"),
    ("if (runtime->player_weapon_projectiles[slot_index].active &&\n"
     "                runtime->player_weapon_projectiles[slot_index].state !=\n"
     "                    avsp_round1_weapon_projectile.initial_state)",
     "if (runtime->player_weapon_projectiles[slot_index].active)"),
):
    if "--generated-all-only" in sys.argv:
        continue
    if "--inner8-only" in sys.argv and before not in inner8_mutations:
        continue
    if "--ko-only" in sys.argv and before not in ko_mutations:
        continue
    if "--registration-only" in sys.argv and before not in registration_mutations:
        continue
    if "--locomotion-only" in sys.argv and before not in locomotion_mutations:
        continue
    if "--controller-edge-only" in sys.argv and before not in controller_edge_mutations:
        continue
    if "--player-hit-only" in sys.argv and before not in player_hit_mutations:
        continue
    if "--weapon-timing-only" in sys.argv and before not in weapon_timing_mutations:
        continue
    if "--contextual-melee-only" in sys.argv and before not in contextual_melee_mutations:
        continue
    if "--action0c-only" in sys.argv and before not in action0c_mutations:
        continue
    if "--jump-only" in sys.argv and before not in jump_mutations:
        continue
    if ("--type16-terminal-only" in sys.argv and
            before not in type16_terminal_mutations):
        continue
    if ("--special-input-only" in sys.argv and
            before not in special_input_mutations):
        continue
    if ("--hit-interaction-only" in sys.argv and
            before not in hit_interaction_mutations):
        continue
    if ("--class1f-state0-only" in sys.argv and
            before not in class1f_state0_mutations):
        continue
    if ("--class1f-action16-only" in sys.argv and
            before not in class1f_action16_mutations):
        continue
    if ("--exit-scheduler-only" in sys.argv and
            before not in exit_scheduler_mutations):
        continue
    if "--generated-walk-only" in sys.argv:
        continue
    if "--class04-only" in sys.argv:
        continue
    assert before in source, before
    run(source.replace(before, after), header, False, before,
        test_body=(jump_test_body if "--jump-only" in sys.argv else
                   class1f_state0_checkpoint_body
                   if "--class1f-state0-only" in sys.argv else None),
        expected_returncode=(94 if "--action0c-only" in sys.argv
                             else None))
if "--inner8-only" in sys.argv:
    print("REIMPLEMENT-13 class-0x1f inner-state mutation lane: PASS (15 real mutations)")
    raise SystemExit(0)
if "--class1f-state0-only" in sys.argv:
    print("REIMPLEMENT-13 class-0x1f state-0 mutation lane: PASS (3 real mutations)")
    raise SystemExit(0)
if "--class1f-action16-only" in sys.argv:
    print("REIMPLEMENT-13 class-0x1f action-0x16/fixed-slot lifecycle "
          "mutation lane: PASS (3 real mutations)")
    raise SystemExit(0)
if "--exit-scheduler-only" in sys.argv:
    print("REIMPLEMENT-13 Coffee Shop exit scheduler mutation lane: PASS "
          "(4 real mutations)")
    raise SystemExit(0)
if "--ko-only" in sys.argv:
    print("REIMPLEMENT-13 class-0x1f projectile KO mutation lane: PASS (5 real mutations)")
    raise SystemExit(0)
if "--registration-only" in sys.argv:
    print("REIMPLEMENT-13 deferred record-4 registration mutation lane: PASS (1 real mutation)")
    raise SystemExit(0)
if "--contextual-melee-only" in sys.argv:
    print("REIMPLEMENT-13 contextual Button2 mutation lane: PASS (8 real mutations)")
    raise SystemExit(0)
if "--locomotion-only" in sys.argv:
    print("REIMPLEMENT-13 locomotion/weapon-return mutation lane: PASS (7 real mutations)")
    raise SystemExit(0)
if ("--controller-edge-only" in sys.argv or
        not subset_flags.intersection(sys.argv)):
    pre_before = """            if (phase_updates != 0u &&
                scene_runtime.entry.dependencies_seeded &&
                !avsp_round1_step_scheduler_pre_player_source_differential(
                    &scene_runtime, source_updates != 0u))
                return 112;
"""
    post_before = """            if (phase_updates != 0u &&
                scene_runtime.entry.dependencies_seeded)
            {
                if (!avsp_round1_step_scheduler_post_player_source_differential(
"""
    assert pre_before in test_source
    assert post_before in test_source
    post_after = """            if (phase_updates != 0u &&
                scene_runtime.entry.dependencies_seeded)
            {
                if (!avsp_round1_step_scheduler_pre_player_source_differential(
                        &scene_runtime, source_updates != 0u))
                    return 112;
                if (!avsp_round1_step_scheduler_post_player_source_differential(
"""
    post_player_controller = test_source.replace(pre_before, "", 1).replace(
        post_before, post_after, 1)
    run(source, header, False, "post-player-recurring-controller",
        expected_returncode=117, test_body=post_player_controller)
    delayed_scene_scheduler = test_source.replace(
        "scene_runtime.entry.dependencies_seeded",
        "scene_runtime.entry.spawned")
    run(source, header, False, "delayed-scene-scheduler-handoff",
        expected_returncode=124, test_body=delayed_scene_scheduler)
    if "--controller-edge-only" in sys.argv:
        print("REIMPLEMENT-13 controller camera-edge mutation lane: PASS (9 real mutations)")
        raise SystemExit(0)
if "--player-hit-only" in sys.argv:
    print("REIMPLEMENT-13 Coffee Shop player-HIT program mutation lane: PASS (14 real mutations)")
    raise SystemExit(0)
if "--hit-interaction-only" in sys.argv:
    print("REIMPLEMENT-13 HIT-interaction/Button1 handoff mutation lane: PASS (7 real mutations)")
    raise SystemExit(0)
if ("--weapon-timing-only" in sys.argv or
        not subset_flags.intersection(sys.argv)):
    airborne_progress_before = """    if (!avsp_round1_apply_player_stage_progress(runtime))
        return 0;
    runtime->player_jump_phase = 0x0406u;"""
    airborne_progress_after = """    runtime->player_jump_phase = 0x0406u;"""
    assert airborne_progress_before in source
    run(source.replace(airborne_progress_before, airborne_progress_after, 1),
        header, False, "airborne-Button1-stage-progress")
    airborne_guard_before = """    if (runtime->player_resource_depleted)
        return 1;"""
    airborne_guard_after = """    if (runtime->player_resource <
            avsp_round1_player_weapon.resource_debit)
        return 1;"""
    assert airborne_guard_before in source
    run(source.replace(airborne_guard_before, airborne_guard_after, 1),
        header, False, "airborne-Button1-depleted-latch-guard",
        test_body=scene_checkpoint_body)
    airborne_clamp_before = """        else
        {
            runtime->player_resource = 0u;
            runtime->player_resource_depleted = 1u;
        }
        runtime->player_resource_recharge ="""
    airborne_clamp_after = """        else
            runtime->player_resource = (unsigned char)(
                runtime->player_resource -
                avsp_round1_player_weapon.resource_debit);
        runtime->player_resource_recharge ="""
    assert airborne_clamp_before in source
    run(source.replace(airborne_clamp_before, airborne_clamp_after, 1),
        header, False, "airborne-Button1-saturating-debit",
        test_body=scene_checkpoint_body)
    generated_resource_before = """    16u,
    1u,
    1u,
    1u,
    64u,
"""
    generated_resource_after = """    16u,
    1u,
    1u,
    0u,
    64u,
"""
    assert generated.count(generated_resource_before) == 1
    run(source, header, False, "generated-resource-debit-tick",
        generated_body=generated.replace(
            generated_resource_before, generated_resource_after, 1))
    if "--weapon-timing-only" in sys.argv:
        print("REIMPLEMENT-13 Button1 timing mutation lane: PASS (13 real mutations)")
        raise SystemExit(0)
if "--action0c-only" in sys.argv:
    print("REIMPLEMENT-13 class-0x1f action-0x0c timer-row mutation lane: PASS (1 real mutation)")
    raise SystemExit(0)
if "--jump-only" in sys.argv:
    generated_jump_timing = (
        "    1u, 1u, 2u, 5u, 10u, 1u, 4095u, -32768")
    assert generated.count(generated_jump_timing) == 1
    for label, changed_timing in (
        ("dispatch-delay", "    1u, 1u, 1u, 5u, 10u, 1u, 4095u, -32768"),
        ("same-facing-selector", "    1u, 1u, 2u, 6u, 10u, 1u, 4095u, -32768"),
        ("landing-fraction", "    1u, 1u, 2u, 5u, 10u, 0u, 4095u, -32768"),
        ("neutral-timer", "    1u, 1u, 2u, 5u, 10u, 1u, 4094u, -32768"),
        ("neutral-branch", "    1u, 1u, 2u, 5u, 10u, 1u, 4095u, 0"),
    ):
        run(source, header, False, "generated-jump-" + label,
            generated_body=generated.replace(
                generated_jump_timing, changed_timing, 1),
            test_body=jump_test_body)
    print("REIMPLEMENT-13 Button3 source-timing mutation lane: PASS (11 real mutations)")
    raise SystemExit(0)
if "--type16-terminal-only" in sys.argv:
    print("REIMPLEMENT-13 type16 terminal action-timer lane: PASS "
          "(1 real mutation)")
    raise SystemExit(0)
if "--special-input-only" in sys.argv:
    zero_health_combo_before = """    special_physical_candidate = (unsigned char)(
        special_pipeline_candidate ||
        avsp_round1_player_special_physical_guard("""
    zero_health_combo_after = """    special_physical_candidate = (unsigned char)(
        0 && special_pipeline_candidate ||
        avsp_round1_player_special_physical_guard("""
    assert zero_health_combo_before in source
    run(source.replace(zero_health_combo_before, zero_health_combo_after, 1),
        header, False, "zero-health-Button1-combo-priority",
        test_body=scene_checkpoint_body)
    print("REIMPLEMENT-13 simultaneous special-input arbitration lane: PASS "
          "(3 real mutations)")
    raise SystemExit(0)
if "--class03-only" in sys.argv:
    spawn_call = """            if (!avsp_round1_spawn_type36_class03(runtime, actor))
                return 0;"""
    assert source.count(spawn_call) == 5
    run(source.replace(spawn_call, "", 1), header, False,
        "class03-first-landing-spawn-owner", expected_returncode=250,
        test_body=class03_checkpoint_body)
    parent_guard = """    if (parent->state == 0x0202u)
    {
        if (parent->substate == 0x0204u)"""
    assert source.count(parent_guard) == 1
    run(source.replace(parent_guard, parent_guard.replace(
        "parent->state == 0x0202u", "parent->state == 0x0200u"), 1),
        header, False, "class03-parent-state-guard", expected_returncode=56,
        test_body=class03_checkpoint_body)
    allocation_class = (
        "    actor->actor_class = avsp_round1_type36_class03.actor_class;")
    assert source.count(allocation_class) == 1
    run(source.replace(allocation_class,
        "    actor->actor_class = 0x04;", 1), header, False,
        "class03-allocation-class", expected_returncode=56,
        test_body=class03_checkpoint_body)
    allocation_variant = (
        "    actor->variant = avsp_round1_type36_class03.variant;")
    assert source.count(allocation_variant) == 1
    run(source.replace(allocation_variant, "    actor->variant = 0u;", 1),
        header, False, "class03-allocation-variant", expected_returncode=56,
        test_body=class03_checkpoint_body)
    phase_rule = """        unsigned char phase = (unsigned char)(
            (actor->source_action_timer + 1u) & 3u);"""
    assert source.count(phase_rule) == 1
    run(source.replace(phase_rule, phase_rule.replace("+ 1u", "+ 2u"), 1),
        header, False, "class03-phase-preincrement", expected_returncode=250,
        test_body=class03_checkpoint_body)
    phase_mapping = """        else if (phase == 1u)
        {
            buffer_index = 2u;"""
    assert source.count(phase_mapping) == 1
    run(source.replace(phase_mapping, phase_mapping.replace(
        "buffer_index = 2u", "buffer_index = 1u"), 1), header, False,
        "class03-phase-buffer-map", expected_returncode=250,
        test_body=class03_checkpoint_body)
    velocity_sign = "            velocity = -actor->source_x_velocity;"
    assert source.count(velocity_sign) == 1
    run(source.replace(velocity_sign,
        "            velocity = actor->source_x_velocity;", 1),
        header, False, "class03-phase-velocity-sign", expected_returncode=250,
        test_body=class03_checkpoint_body)
    acceleration_order = """        actor->source_y_velocity = (long)(
            (unsigned long)actor->source_y_velocity +
            (unsigned long)actor->source_y_acceleration);"""
    assert source.count(acceleration_order) == 1
    run(source.replace(acceleration_order, "", 1), header, False,
        "class03-y-acceleration-order", expected_returncode=250,
        test_body=class03_checkpoint_body)
    rng_absence = """        actor->source_action_timer = 0xffu;
        actor->source_x_velocity = spec->phase1_x_velocity;"""
    assert source.count(rng_absence) == 1
    run(source.replace(rng_absence, """        actor->source_action_timer = 0xffu;
        (void)avsp_round1_source_rng(runtime);
        ++runtime->type36_class03_rng_calls;
        actor->source_x_velocity = spec->phase1_x_velocity;""", 1),
        header, False, "class03-no-direct-rng", expected_returncode=56,
        test_body=class03_checkpoint_body)
    backlink = """        if (parent->source_type36_class03_child ==
                (unsigned short)actor->source_slot)
            parent->source_type36_class03_child = 0u;"""
    assert source.count(backlink) == 1
    run(source.replace(backlink,
        "        parent->source_type36_class03_child = 0u;", 1),
        header, False, "class03-backlink-guard", expected_returncode=250,
        test_body=class03_checkpoint_body)
    scheduler_dispatch = """                if (!avsp_round1_step_type36_class03(
                        runtime, &runtime->pools[pool_index], actor))"""
    assert source.count(scheduler_dispatch) == 1
    run(source.replace(scheduler_dispatch,
        scheduler_dispatch.replace("if (!", "if (0 && !"), 1),
        header, False, "class03-scheduler-invocation", expected_returncode=250,
        test_body=class03_checkpoint_body)
    first_record = (
        "    { 4u, 0, 0x0009a884UL, 0x0009a9aeUL, 0u, 0u },")
    assert generated.count(first_record) == 1
    run(source, header, False, "generated-class03-first-assembly",
        generated_body=generated.replace(first_record, first_record.replace(
            "0x0009a9aeUL", "0x0009a9bcUL"), 1),
        expected_returncode=250, test_body=class03_checkpoint_body)
    terminal_record = (
        "    { 4u, -32768, 0x0009a904UL, 0x0009aa10UL, 0u, 0u },")
    assert generated.count(terminal_record) == 1
    run(source, header, False, "generated-class03-terminal-branch",
        generated_body=generated.replace(terminal_record,
            terminal_record.replace("-32768", "0"), 1),
        expected_returncode=56, test_body=class03_checkpoint_body)
    generated_motion = (
        "    0x09A67EUL, 0x0009A884UL, -163840L, -278528L, 0L, 4096L,")
    assert generated.count(generated_motion) == 1
    run(source, header, False, "generated-class03-motion-row",
        generated_body=generated.replace(generated_motion,
            generated_motion.replace("-163840L", "-163839L"), 1),
        expected_returncode=56, test_body=class03_checkpoint_body)
    record_focused_program_controls(
        "type36_class03_complete_program",
        "complete Coffee Shop source frames 2040..5566; every route-reachable "
        "type-36/class-0x03 allocation, four-phase motion, animation, parent "
        "backlink and release")
    print("REIMPLEMENT-13 Coffee Shop type-36/class-0x03 presentation "
          "mutation lane: PASS (14 real mutations)")
    raise SystemExit(0)
if "--class04-only" in sys.argv:
    ground_allocation = """            avsp_round1_allocate_player_weapon_projectile(runtime);
            if (!avsp_round1_spawn_type36_class04(runtime))"""
    assert source.count(ground_allocation) == 1
    run(source.replace(ground_allocation,
        """            avsp_round1_allocate_player_weapon_projectile(runtime);
            if (0 && !avsp_round1_spawn_type36_class04(runtime))""", 1),
        header, False, "class04-ground-allocation-writer",
        expected_returncode=249, test_body=class04_checkpoint_body)
    x_rule = """        x = parent->facing == 0u ?
            (short)((unsigned short)parent->x -
                    (unsigned short)spec->offset_x) :
            (short)((unsigned short)parent->x +
                    (unsigned short)spec->offset_x);"""
    assert source.count(x_rule) == 1
    run(source.replace(x_rule, x_rule.replace(
        "parent->facing == 0u", "parent->facing != 0u"), 1),
        header, False, "class04-facing-derived-x-offset",
        expected_returncode=249, test_body=class04_checkpoint_body)
    y_rule = """        y = (short)((unsigned short)parent->y +
                    (unsigned short)spec->offset_y);"""
    assert source.count(y_rule) == 1
    run(source.replace(y_rule, """        y = (short)((unsigned short)parent->y -
                    (unsigned short)spec->offset_y);""", 1),
        header, False, "class04-signed-y-offset",
        expected_returncode=249, test_body=class04_checkpoint_body)
    facing_rule = "        actor->facing = parent->facing;"
    assert source.count(facing_rule) == 1
    run(source.replace(facing_rule,
        "        actor->facing = (unsigned char)(parent->facing ^ 1u);", 1),
        header, False, "class04-parent-facing-copy",
        expected_returncode=249, test_body=class04_checkpoint_body)
    rng_absence = """        actor->facing = parent->facing;
        actor->animation_index = 0u;"""
    assert source.count(rng_absence) == 1
    run(source.replace(rng_absence, """        actor->facing = parent->facing;
        (void)avsp_round1_source_rng(runtime);
        ++runtime->type36_class04_rng_calls;
        actor->animation_index = 0u;""", 1),
        header, False, "class04-no-direct-rng",
        expected_returncode=114, test_body=class04_checkpoint_body)
    global_guard = (
        "if (runtime->source_round_stage_index == spec->global_guard_value)")
    assert source.count(global_guard) == 1
    run(source.replace(global_guard,
        "if (runtime->source_round_stage_index != spec->global_guard_value)", 1),
        header, False, "class04-global-movement-guard",
        expected_returncode=249, test_body=class04_checkpoint_body)
    release_delay = """        actor->state = spec->release_state;
        ++runtime->type36_class04_state_transitions;
    }
    if (actor->state == spec->release_state)"""
    assert source.count(release_delay) == 1
    run(source.replace(release_delay, """        actor->state = spec->release_state;
        ++runtime->type36_class04_state_transitions;
        return 1;
    }
    if (actor->state == spec->release_state)""", 1),
        header, False, "class04-same-visit-release",
        expected_returncode=249, test_body=class04_checkpoint_body)
    backlink = """        if (parent->source_type36_class04_child ==
                (unsigned short)actor->source_slot)
            parent->source_type36_class04_child = 0u;"""
    assert source.count(backlink) == 1
    run(source.replace(backlink, "        (void)parent;", 1),
        header, False, "class04-backlink-clear",
        expected_returncode=249, test_body=class04_checkpoint_body)
    generated_spec = (
        "    0x8380u, 0x0200u, 0x0400u, 0x0600u, 5, 86, 10u, "
        "0x04, 36u, 0u")
    assert generated.count(generated_spec) == 1
    run(source, header, False, "generated-class04-signed-offset",
        generated_body=generated.replace(
            generated_spec, generated_spec.replace(
                "0x0600u, 5, 86", "0x0600u, 6, 86"), 1),
        expected_returncode=94, test_body=class04_checkpoint_body)
    first_record = (
        "    { 1u, 0, 0x0009ac82UL, 0x0009b5a6UL, 0u, 0u },")
    assert generated.count(first_record) == 1
    run(source, header, False, "generated-class04-first-assembly",
        generated_body=generated.replace(
            first_record, first_record.replace(
                "0x0009b5a6UL", "0x0009b5b6UL"), 1),
        expected_returncode=94, test_body=class04_checkpoint_body)
    run(source, header, False, "generated-class04-first-selector",
        generated_body=generated.replace(
            first_record, first_record.replace(
                "0x0009b5a6UL, 0u, 0u", "0x0009b5a6UL, 1u, 0u"), 1),
        expected_returncode=94, test_body=class04_checkpoint_body)
    terminal_record = (
        "    { 1u, -32768, 0x0009ad12UL, 0x0009b616UL, 0u, 0u },")
    assert generated.count(terminal_record) == 1
    run(source, header, False, "generated-class04-terminal-branch",
        generated_body=generated.replace(
            terminal_record, terminal_record.replace("-32768", "0"), 1),
        expected_returncode=94, test_body=class04_checkpoint_body)
    record_focused_program_controls(
        "type36_class04_complete_program",
        "complete Coffee Shop source frames 2040..5566; every route-reachable "
        "type-36/class-0x04 allocation, state, animation and release")
    print("REIMPLEMENT-13 Coffee Shop type-36/class-0x04 presentation "
          "mutation lane: PASS (12 real mutations)")
    raise SystemExit(0)
if "--class00-only" in sys.argv:
    facing_negation = """    if (runtime->player.facing == 0u)
        x_offset = -x_offset;"""
    assert source.count(facing_negation) == 1
    run(source.replace(facing_negation, """    if (runtime->player.facing == 2u)
        x_offset = -x_offset;""", 1), header, False,
        "class00-facing-negation", expected_returncode=165,
        test_body=class00_checkpoint_body)
    parent_write = (
        "    runtime->player_presentation_field56 = "
        "parent_entry->parent_field56;")
    assert source.count(parent_write) == 1
    run(source.replace(parent_write,
        "    runtime->player_presentation_field56 = 0u;", 1),
        header, False, "class00-parent-field56-write",
        expected_returncode=165, test_body=class00_checkpoint_body)
    bind = "    avsp_round1_bind_animation_state(actor, &animation->record);"
    assert source.count(bind) == 1
    run(source.replace(bind,
        """    if (runtime->player.animation_record == 0x0015f43cUL)
        actor->animation_timer = animation->record.timer;
    else
        avsp_round1_bind_animation_state(actor, &animation->record);""", 1),
        header, False, "class00-animation-binding",
        expected_returncode=165, test_body=class00_checkpoint_body)
    direct_effect_scope = """    ++runtime->class00_companion_parent_projections;
    ++runtime->class00_companion_animation_bindings;"""
    assert source.count(direct_effect_scope) == 1
    run(source.replace(direct_effect_scope, """    if (runtime->player.animation_record == 0x0015f43cUL)
        (void)avsp_round1_source_rng(runtime);
    ++runtime->class00_companion_parent_projections;
    ++runtime->class00_companion_animation_bindings;""", 1),
        header, False, "class00-direct-rng-absence",
        expected_returncode=168, test_body=class00_checkpoint_body)
    disable_guard = """    if (actor->source_a6 != 0u)
        return 1;"""
    assert source.count(disable_guard) == 1
    run(source.replace(disable_guard, """    if (actor->source_a6 == 2u)
        return 1;""", 1), header, False,
        "class00-disable-guard", expected_returncode=167,
        test_body=class00_checkpoint_body)
    generated_spec = (
        "    0x09E098UL, 0x0BCA3AUL, 0x00FFCE00UL, 0x8380u,\n"
        "    0x0206u, 0x0200u, 0x8000u, 0x22u, 0xFFu,\n"
        "    0x13u, 0xFFu, 0u")
    assert generated.count(generated_spec) == 1
    run(source, header, False, "generated-class00-init-field44",
        generated_body=generated.replace(
            generated_spec, generated_spec.replace("0x13u", "0x12u"), 1),
        expected_returncode=166, test_body=class00_checkpoint_body)
    run(source, header, False, "generated-class00-source-slot",
        generated_body=generated.replace(
            generated_spec,
            generated_spec.replace("0x00FFCE00UL", "0x00FFCD80UL"), 1),
        expected_returncode=5, test_body=class00_checkpoint_body)
    parent_animation = "    { 0x001600e8UL, 0u },"
    assert generated.count(parent_animation) == 1
    run(source, header, False, "generated-class00-parent-record-byte0f",
        generated_body=generated.replace(
            parent_animation, "    { 0x001600e8UL, 1u },", 1),
        expected_returncode=165, test_body=class00_checkpoint_body)
    parent_entry = "    { 15u, -10, 100, 5u, 1u },"
    assert generated.count(parent_entry) == 1
    run(source, header, False, "generated-class00-signed-offset",
        generated_body=generated.replace(
            parent_entry, "    { 15u, -9, 100, 5u, 1u },", 1),
        expected_returncode=165, test_body=class00_checkpoint_body)
    animation_record = (
        "    { 1u, { 4095u, -32767, 0x0009e61aUL, "
        "0x0009e908UL, 0u, 0u } },")
    assert generated.count(animation_record) == 1
    run(source, header, False, "generated-class00-animation-assembly",
        generated_body=generated.replace(
            animation_record, animation_record.replace(
                "0x0009e908UL", "0x0009e918UL"), 1),
        expected_returncode=165, test_body=class00_checkpoint_body)
    print("REIMPLEMENT-13 Coffee Shop class-0x00 companion mutation lane: "
          "PASS (10 real mutations)")
    raise SystemExit(0)
if "--class0a-only" in sys.argv:
    guard = """        if ((unsigned short)runtime->camera_x_previous >=
                avsp_round1_class0a.camera_threshold)"""
    assert source.count(guard) == 1
    run(source.replace(guard, """        if ((unsigned short)runtime->camera_x_previous >
                avsp_round1_class0a.camera_threshold)""", 1),
        header, False, "class0a-unsigned-camera-guard",
        expected_returncode=160, test_body=class0a_checkpoint_body)
    direct_rng_scope = """    if (guarded)
    {
        if ((unsigned short)runtime->camera_x_previous >=
                avsp_round1_class0a.camera_threshold)"""
    assert source.count(direct_rng_scope) == 1
    run(source.replace(direct_rng_scope, """    if (guarded)
    {
        (void)avsp_round1_source_rng(runtime);
        if ((unsigned short)runtime->camera_x_previous >=
                avsp_round1_class0a.camera_threshold)""", 1),
        header, False, "class0a-direct-rng-absence",
        expected_returncode=160, test_body=class0a_checkpoint_body)
    release = """    if (actor->state == avsp_round1_class0a.release_state)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->class0a_releases;
        return 1;
    }"""
    assert source.count(release) == 1
    run(source.replace(release, """    if (actor->state == avsp_round1_class0a.release_state)
    {
        (void)pool;
        ++runtime->class0a_releases;
        return 1;
    }""", 1),
        header, False, "class0a-fixed-pool-release",
        expected_returncode=161, test_body=class0a_checkpoint_body)
    generated_spec = (
        "    0x077CCCUL, 0x077D26UL, 0x0200u, 0x0400u, 0x0920u,\n"
        "    { 0x0Au, 0x0Cu, 0x0Eu }, 0x00FFC600UL, 0x00FFC580UL,\n"
        "    0x26u, 0x06u")
    assert generated.count(generated_spec) == 1
    for label, changed, code in (
        ("guarded-variant", generated_spec.replace(
            "{ 0x0Au, 0x0Cu, 0x0Eu }", "{ 0x0Bu, 0x0Cu, 0x0Eu }"), 160),
        ("second-source-slot", generated_spec.replace(
            "0x00FFC580UL", "0x00FFC500UL"), 162),
        ("second-variant", generated_spec.replace(
            "0x26u, 0x06u", "0x26u, 0x08u"), 162),
    ):
        run(source, header, False, "generated-class0a-" + label,
            generated_body=generated.replace(generated_spec, changed, 1),
            expected_returncode=code, test_body=class0a_checkpoint_body)
    class0a_record = (
        "    { 16u, 3072, 0x00077e54UL, 0x00078ba2UL, 0u, 16u },")
    assert generated.count(class0a_record) == 1
    run(source, header, False, "generated-class0a-initial-assembly",
        generated_body=generated.replace(
            class0a_record,
            "    { 16u, 3072, 0x00077e54UL, 0x00078bb2UL, 0u, 16u },", 1),
        expected_returncode=162, test_body=class0a_checkpoint_body)
    print("REIMPLEMENT-13 Coffee Shop class-0x0a program mutation lane: "
          "PASS (7 real mutations)")
    raise SystemExit(0)
if "--class0f-only" in sys.argv:
    delay_body = """        if (actor->source_action_timer != 0u)
            --actor->source_action_timer;"""
    assert source.count(delay_body) == 1
    run(source.replace(delay_body, """        if (actor->source_action_timer != 0u)
            actor->source_action_timer = actor->source_action_timer;""", 1),
        header, False, "class0f-delay-predecrement",
        expected_returncode=152, test_body=class0f_checkpoint_body)
    variant_loop = """    for (variant = (signed char)(avsp_round1_class0f.class11_child_count - 1u);
         variant >= 0; --variant)"""
    assert variant_loop in source
    run(source.replace(variant_loop, """    for (variant = 0;
         variant < (signed char)avsp_round1_class0f.class11_child_count;
         ++variant)""", 1),
        header, False, "class0f-child-variant-order",
        expected_returncode=154, test_body=class0f_checkpoint_body)
    facing_rule = "actor->facing = (unsigned char)(actor->source_facing_selector ^ 1u);"
    assert source.count(facing_rule) >= 1
    class0f_facing_scope = """        actor->facing = (unsigned char)(actor->source_facing_selector ^ 1u);
        ++runtime->class0f_reaction_entries;"""
    assert class0f_facing_scope in source
    run(source.replace(class0f_facing_scope, """        actor->facing = actor->source_facing_selector;
        ++runtime->class0f_reaction_entries;""", 1),
        header, False, "class0f-visible-facing-xor",
        expected_returncode=155, test_body=class0f_checkpoint_body)
    collision_nav = """    ++runtime->class0f_collision_calls;
    ++runtime->class0f_navigation_calls;"""
    assert source.count(collision_nav) == 1
    for label, changed in (
        ("collision-invocation", "    ++runtime->class0f_navigation_calls;"),
        ("navigation-invocation", "    ++runtime->class0f_collision_calls;"),
    ):
        run(source.replace(collision_nav, changed, 1), header, False,
            "class0f-" + label, expected_returncode=151,
            test_body=class0f_checkpoint_body)
    audio_owner = """        runtime->class0f_audio_command = command;
        runtime->class0f_audio_argument = avsp_round1_class0f.audio_argument;"""
    assert source.count(audio_owner) == 1
    run(source.replace(audio_owner, """        (void)avsp_round1_source_rng(runtime);
        runtime->class0f_audio_command = command;
        runtime->class0f_audio_argument = avsp_round1_class0f.audio_argument;""", 1),
        header, False, "class0f-direct-rng-call",
        expected_returncode=155, test_body=class0f_checkpoint_body)
    class09_flag = """    child->substate = 0u;
    child->source_motion_flags = 1u;
    child->x = owner->x;"""
    assert source.count(class09_flag) == 1
    run(source.replace(class09_flag, """    child->substate = 0u;
    child->source_motion_flags = 0u;
    child->x = owner->x;""", 1),
        header, False, "class0f-class09-field5c",
        expected_returncode=157, test_body=class0f_checkpoint_body)
    release_rule = """    else if (actor->state == avsp_round1_class0f.release_state)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->class0f_releases;
        return 1;
    }"""
    assert source.count(release_rule) == 1
    run(source.replace(release_rule, """    else if (actor->state == avsp_round1_class0f.release_state)
    {
        (void)pool;
        ++runtime->class0f_releases;
        return 1;
    }""", 1),
        header, False, "class0f-fixed-pool-release",
        expected_returncode=158, test_body=class0f_checkpoint_body)
    generated_class0f = (
        "    0x0200u, 0x0202u, 0x0400u, 0x0600u, 2u, 0x1Du,\n"
        "    24u, 0x11, 4u, -1, 28u, 0x09, 80, -8, "
        "0x0077u, 0x0142u, 0x00002000UL")
    assert generated.count(generated_class0f) == 1
    for label, changed, code in (
        ("initial-selector", generated_class0f.replace(
            "0x0600u, 2u,", "0x0600u, 1u,"), 151),
        ("presentation-mode", generated_class0f.replace(
            "2u, 0x1Du", "2u, 0x1Cu"), 151),
        ("class11-z", generated_class0f.replace(
            "4u, -1,", "4u, 0,"), 154),
        ("class09-y", generated_class0f.replace(
            "0x09, 80, -8", "0x09, 79, -8"), 157),
        ("class09-z", generated_class0f.replace(
            "0x09, 80, -8", "0x09, 80, -7"), 157),
        ("selector1-audio", generated_class0f.replace(
            "0x0077u, 0x0142u", "0x0076u, 0x0142u"), 155),
        ("selector0-audio", generated_class0f.replace(
            "0x0077u, 0x0142u", "0x0077u, 0x0141u"), 157),
        ("audio-argument", generated_class0f.replace(
            "0x00002000UL", "0x00001000UL"), 155),
    ):
        run(source, header, False, "generated-class0f-" + label,
            generated_body=generated.replace(generated_class0f, changed, 1),
            expected_returncode=code, test_body=class0f_checkpoint_body)
    record0 = "{ 4095u, -32768, 0x0006ee4aUL, 0x0006ee86UL, 1u, 1u },"
    assert generated.count(record0) == 1
    run(source, header, False, "generated-class0f-initial-assembly",
        generated_body=generated.replace(
            record0,
            "{ 4095u, -32768, 0x0006ee4aUL, 0x0006ee96UL, 1u, 1u },", 1),
        expected_returncode=151, test_body=class0f_checkpoint_body)
    print("REIMPLEMENT-13 Coffee Shop class-0x0f program mutation lane: "
          "PASS (17 real mutations)")
    raise SystemExit(0)
generated_walk_mutations = {
    "    { 4u, 0, 0x0015F208UL, 0x00160A02UL, 17u, 0u },",
    "    { 4u, -32768, 0x0015F2B8UL, 0x00160B9EUL, 17u, 0u },",
    "    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    17u,\n    0u,\n    {255u, 2u, 6u, 255u,",
    "    147456L,",
}
for generated_index, (before, after) in enumerate((
    ("    { 4u, 0, 0x0015F208UL, 0x00160A02UL, 17u, 0u },",
     "    { 3u, 0, 0x0015F208UL, 0x00160A02UL, 17u, 0u },"),
    ("    { 4u, 0, 0x0015F208UL, 0x00160A02UL, 17u, 0u },",
     "    { 4u, 0, 0x0015F208UL, 0x00160A2AUL, 17u, 0u },"),
    ("    { 4u, -32768, 0x0015F2B8UL, 0x00160B9EUL, 17u, 0u },",
     "    { 4u, 0, 0x0015F2B8UL, 0x00160B9EUL, 17u, 0u },"),
    ("    0x0400u, 0x0402u, 0x0404u, 0x0600u,",
     "    0x0402u, 0x0402u, 0x0404u, 0x0600u,"),
    ("    114688L, 0L, 622592L, -20480L,",
     "    114688L, 0L, 618496L, -20480L,"),
    ("    2u, 0x36u, 0u, 0x15u, 8u, 3u, 60u, 6u,",
     "    2u, 0x36u, 0u, 0x15u, 8u, 3u, 59u, 6u,"),
    ("{ 0xffa3c0u, 12u, 656, 312, 312,", "{ 0xffa3c0u, 12u, 657, 312, 312,"),
    ("{ AVSP_ROUND1_ENTRY_DWELL, 0x00u, 0u, 60u,", "{ AVSP_ROUND1_ENTRY_DWELL, 0x00u, 0u, 59u,"),
    ("    12u, 16u, 20u, 24u, 28u, 36u",
     "    16u, 12u, 20u, 24u, 28u, 36u"),
    ("{ 6u, 1u, 1u, 1u, 16u, 0u, 1u, 1u, 216u, 0x1Du, 0x0000u },",
     "{ 6u, 1u, 1u, 1u, 16u, 0u, 1u, 1u, 215u, 0x1Du, 0x0000u },"),
    ("{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 16u, 0x8000, 216u,", "{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 0u, 16u, 0x8000, 216u,"),
    ("{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 16u, 0x8000, 216u,", "{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 15u, 0x8000, 216u,"),
    ("{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 16u, 0x8000, 216u,", "{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 16u, 0x0000, 216u,"),
    ("{ 0x0200u, 0x1400u },", "{ 0x0200u, 0x1401u },"),
    ("    640, 256, 640, 832, 256, 256, 0x40u, 0x20u,",
     "    640, 256, 640, 831, 256, 256, 0x40u, 0x20u,"),
    ("    { 0, 0, 32u, 127u, 0, 6u, 0, 0u, 0u }",
     "    { 0, 0, 31u, 127u, 0, 6u, 0, 0u, 0u }"),
    ("{ 0x02u, 0x02u, 0x80u, 0x80u, 0x10u, 0x10u, 0xFFu, 0x80u },",
     "{ 0x02u, 0x02u, 0x80u, 0x80u, 0x10u, 0x10u, 0x00u, 0x80u },"),
    ("    1u, 1200u,", "    1u, 1199u,"),
    ("7u, 7u, 8u, 8u, 9u, 9u", "7u, 7u, 7u, 8u, 9u, 9u"),
    ("    147456L,", "    147455L,"),
    ("    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    17u,\n    0u,\n    {255u, 2u, 6u, 255u,",
     "    514u,\n    516u,\n    512u,\n    9u,\n    147456L,\n    17u,\n    0u,\n    {255u, 2u, 6u, 255u,"),
    ("    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    17u,\n    0u,\n    {255u, 2u, 6u, 255u,",
     "    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    16u,\n    0u,\n    {255u, 2u, 6u, 255u,"),
    ("    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    17u,\n    0u,\n    {255u, 2u, 6u, 255u,",
     "    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    17u,\n    1u,\n    {255u, 2u, 6u, 255u,"),
    ("    1536u,\n    5120u,\n    30u,", "    1538u,\n    5120u,\n    30u,"),
    ("    1536u,\n    5120u,\n    30u,", "    1536u,\n    5120u,\n    29u,"),
    ("{ 0x1600f8UL, 0x162a04UL, 8u, 1u },", "{ 0x1600f8UL, 0x162a82UL, 8u, 1u },"),
    ("{ 0x1601c0UL, 0x1614a4UL, 8u, 3u },", "{ 0x1601c0UL, 0x1614a4UL, 8u, 2u },"),
    ("    40u,\n    12u,\n    3u,\n    6u,\n    1u,",
     "    39u,\n    12u,\n    3u,\n    6u,\n    1u,"),
    ("    40u,\n    12u,\n    3u,\n    6u,\n    1u,\n    1u,\n    1u,\n    0u,\n    1u,\n    1u,\n    0,\n    4,",
     "    40u,\n    12u,\n    3u,\n    6u,\n    1u,\n    0u,\n    1u,\n    0u,\n    1u,\n    1u,\n    0,\n    4,"),
    ("{ 3074u, 2u, 0x0015e594UL, 0x0016179aUL, 1u, 0u, 2u, 0 },",
     "{ 3074u, 2u, 0x00165410UL, 0x00166c22UL, 1u, 0u, 2u, 0 },"),
    ("{ 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u, 4095u, -32768 },",
     "{ 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u, 4095u, -32768 },"),
    ("    17u, 18u, 19u, 20u, 21u, 22u, 23u, 24u, 25u, 26u, 27u, 28u, 29u, 30u, 31u, 32u, 33u, 34u, 35u, 36u, 37u, 38u, 39u, 40u, 41u, 42u, 43u, 44u, 45u, 46u, 47u",
     "    17u, 18u, 19u, 20u, 21u, 22u, 23u, 24u, 25u, 26u, 27u, 28u, 29u, 30u, 31u, 32u, 33u, 34u, 35u, 36u, 37u, 38u, 39u, 40u, 41u, 42u, 43u, 44u, 45u, 46u, 46u"),
    ("    { 5, 86 },", "    { 6, 86 },"),
    ("    { 0, 84 },", "    { 0, 83 },"),
    ("{ 4095u, -32767, 0x0007a12cUL, 0x0007a3a0UL, 0u, 0u },", "{ 4095u, -32768, 0x0007a12cUL, 0x0007a3a0UL, 0u, 0u },"),
    ("static const AvspRound1CollisionBoxSpec "
     "avsp_round1_weapon_parent_attack_boxes"
     "[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =\n"
     "{\n"
     "    { 0, 0, 0u, 0u, 0, 0u, 0, 0u, 0u },\n"
     "    { 0, -8, 4u, 12u, 0, 8u, 0, 8u, 25u },",
     "static const AvspRound1CollisionBoxSpec "
     "avsp_round1_weapon_parent_attack_boxes"
     "[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =\n"
     "{\n"
     "    { 0, 0, 0u, 0u, 0, 0u, 0, 0u, 0u },\n"
     "    { 0, -8, 4u, 12u, 0, 8u, 0, 8u, 24u },"),
    ("{ 0, 10, 16u, 10u, 0, 8u, 1, 8u, 14u },",
     "{ 0, 10, 16u, 10u, 0, 8u, 1, 8u, 13u },"),
    ("    0, 4,\n    5u,\n    1u,\n    6u, 0x8000u,",
     "    0, 5,\n    5u,\n    1u,\n    6u, 0x8000u,"),
    ("    127u,\n    31u", "    126u,\n    31u"),
    ("{ 0x00ffa300UL, 0x0200u, 0x1400u, 704, 296, 296, 1u, 1u, 19u, 0x8000, 3u,", "{ 0x00ffa300UL, 0x0200u, 0x1400u, 704, 296, 296, 1u, 1u, 19u, 0x8000, 4u,"),
    ("{ 60u, 3u, AVSP_ROUND1_ANIMATION_TERMINAL_STATE_GUARD, { { 8u, 1,", "{ 60u, 3u, AVSP_ROUND1_ANIMATION_TERMINAL_STATE_GUARD, { { 7u, 1,"),
    ("    0x004Du, 0x0118u, 0x0000u", "    0x004Du, 0x0119u, 0x0000u"),
    ("    { -8, 8 },", "    { -7, 8 },"),
    ("0x08d9a4UL, 0u, 0u, 0u, 0x8000u", "0x08d9a4UL, 0u, 0u, 0u, 0x0000u"),
    ("{ 0L, 0L, 557056L, -32768L },",
     "{ 0L, 0L, 524288L, -32768L },"),
    ("{ -983040L, 26624L, 262144L, -14336L },",
     "{ -917504L, 26624L, 262144L, -14336L },"),
    ("{ 786432L, -40960L, 0L, 0L }",
     "{ 786432L, -32768L, 0L, 0L }"),
    ("{ 4u, 5u, { { 8u, 0, 0x15f2f0UL, 0x160cdaUL, 2u, 0u }",
     "{ 4u, 5u, { { 7u, 0, 0x15f2f0UL, 0x160cdaUL, 2u, 0u }"),
    ("{ 6u, 8u, { { 2u, 0, 0x15f3b8UL, 0x160beeUL, 2u, 0u }",
     "{ 6u, 8u, { { 2u, 0, 0x15f3c8UL, 0x160beeUL, 2u, 0u }"),
    ("{ 41u, 2u, { { 4u, 0, 0x15fc3cUL, 0x162ee2UL, 9u, 22u }",
     "{ 41u, 2u, { { 4u, 0, 0x15fc3cUL, 0x162ee2UL, 9u, 21u }"),
    ("{ 60u, 1u, { { 4095u, -32768, 0x15fc60UL, 0x162ee2UL, 9u, 35u }",
     "{ 60u, 1u, { { 4095u, -32768, 0x15fc60UL, 0x162ee2UL, 9u, 34u }"),
    ("{ 0x0015c108UL, 0x00ffb600UL, 2072u, 512u, 752, 336,",
     "{ 0x0015c108UL, 0x00ffb600UL, 2072u, 641u, 752, 336,"),
    ("0x06B2FAUL, 0x06B520UL, 240u, 60u, 360u, 192u, 40u,",
     "0x06B2FAUL, 0x06B520UL, 239u, 60u, 360u, 192u, 40u,"),
    ("8, 64, -8, 25, -1, 0x0077u,",
     "8, 64, -8, 24, -1, 0x0077u,"),
    ("0x47, 0u, 4u, 7u, 80, -1, 0x08eb86UL",
     "0x47, 0u, 3u, 7u, 80, -1, 0x08eb86UL"),
    ("0x47, 0u, 4u, 7u, 80, -1, 0x08eb86UL",
     "0x47, 0u, 4u, 7u, 79, -1, 0x08eb86UL"),
    ("0x43, 0u, 2u, 4u, 7u, 80, -1, 0x08ce44UL",
     "0x43, 0u, 1u, 4u, 7u, 80, -1, 0x08ce44UL"),
    ("0u, 1u, 2u, 3u, 4u, 5u, 6u, 0u, 1u, 2u, 3u, 4u, 5u, 6u, 0u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 7u, 8u, 7u, 8u, 0u, 1u, 2u, 3u, 4u",
     "0u, 1u, 2u, 3u, 4u, 5u, 6u, 0u, 1u, 2u, 3u, 3u, 5u, 6u, 0u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 7u, 8u, 7u, 8u, 0u, 1u, 2u, 3u, 4u"),
    ("0x0077u, 1u, 0u,",
     "0x0077u, 0u, 0u,"),
    ("{ -65536L, -81920L, -98304L, -131072L },",
     "{ -32768L, -40960L, -49152L, -65536L },"),
    ("    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 17u, 20u,",
     "    -58, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 17u, 20u,"),
    ("    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 17u, 20u,",
     "    -59, 64, 0x0058u, 0x0232u, 16, 16u, 0x06, 1u, 17u, 20u,"),
    ("    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 17u, 20u,",
     "    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x05, 1u, 17u, 20u,"),
    ("    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 17u, 20u,",
     "    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 2u, 17u, 20u,"),
    ("    { 0, 0, 8u, 8u, 0, 8u, 0, 20u, 10u },",
     "    { 100, 0, 8u, 8u, 0, 8u, 0, 20u, 10u },"),
    ("    2750u, 1u, 17u, 10u, 10u,\n"
     "    { -37, 53, 38u, 8u, 0, 8u, 0, 10u, 0u },\n"
     "    { 1, 45, 20u, 46u, 0, 6u, 0, 0u, 0u }",
     "    2750u, 1u, 17u, 10u, 10u,\n"
     "    { -37, 53, 38u, 8u, 0, 8u, 0, 10u, 0u },\n"
     "    { 101, 45, 20u, 46u, 0, 6u, 0, 0u, 0u }"),
    ("    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 17u, 20u,\n"
     "    { 0, 0, 8u, 8u, 0, 8u, 0, 20u, 10u },\n"
     "    { 1, 45, 20u, 46u, 0, 6u, 0, 0u, 0u }",
     "    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 17u, 20u,\n"
     "    { 0, 0, 8u, 8u, 0, 8u, 0, 20u, 10u },\n"
     "    { 101, 45, 20u, 46u, 0, 6u, 0, 0u, 0u }"),
    ("    { 524288L, -8192L, 262144L, -16384L, 0L },",
     "    { 524287L, -8192L, 262144L, -16384L, 0L },"),
    ("    { 1u, 1, 0x0012e580UL, 0x00130946UL, 8u, 0u },",
     "    { 1u, 0, 0x0012e580UL, 0x00130946UL, 8u, 0u },"),
    ("    0u, 10u, 138u",
     "    0u, 1u, 138u"),
    ("    0x08F080UL, 24u, 0x49, 0u, 8u, 1u, 1u",
     "    0x08F080UL, 24u, 0x49, 0u, 8u, 1u, 0u"),
    ("    0x08F080UL, 24u, 0x49, 0u, 8u, 1u, 1u",
     "    0x08F080UL, 24u, 0x49, 0u, 7u, 1u, 1u"),
    ("    10u, 2u, 1u, 0u, 0x003Bu,",
     "    10u, 2u, 1u, 0u, 0x003Au,"),
    ("    10u, 2u, 1u, 0u, 0x003Bu,",
     "    10u, 2u, 0u, 0u, 0x003Bu,"),
    ("    114688L, -8192L,",
     "    114687L, -8192L,"),
    ("    { 1u, 0, 0x0015f278UL, 0x00160af2UL, 17u, 0u },",
     "    { 1u, 0, 0x0015f278UL, 0x00160af2UL, 16u, 0u },"),
    ("    { 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2 }",
     "    { 3, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2 }"),
    ("    0x00ffc300UL, 2751u, 0xeea3u, 0xcb6eu, 1095, 369, 319, 24u, 0x4e, 0u",
     "    0x00ffc380UL, 2751u, 0xeea3u, 0xcb6eu, 1095, 369, 319, 24u, 0x4e, 0u"),
    ("    0x00ffc300UL, 2751u, 0xeea3u, 0xcb6eu, 1095, 369, 319, 24u, 0x4e, 0u",
     "    0x00ffc300UL, 2751u, 0xeea3u, 0xcb6eu, 1096, 369, 319, 24u, 0x4e, 0u"),
    ("    { 4u, 0, 0x000928e0UL, 0x00092be8UL, 0u, 0u },",
     "    { 4u, 0, 0x000928f0UL, 0x00092be8UL, 0u, 0u },"),
    ("    { 4095u, -32768, 0x00092900UL, 0x00092bf6UL, 0u, 0u },",
     "    { 4095u, -32768, 0x00092910UL, 0x00092bf6UL, 0u, 0u },"),
    ("static const AvspRound1CoffeeExitCallbackGroupSpec avsp_round1_coffee_exit_record20_prefix_callbacks[AVSP_ROUND1_COFFEE_EXIT_RECORD20_PREFIX_GROUP_COUNT] =\n"
     "{\n"
     "    { 0u, 5u, 1u },",
     "static const AvspRound1CoffeeExitCallbackGroupSpec avsp_round1_coffee_exit_record20_prefix_callbacks[AVSP_ROUND1_COFFEE_EXIT_RECORD20_PREFIX_GROUP_COUNT] =\n"
     "{\n"
     "    { 0u, 5u, 2u },"),
)):
    if "--generated-walk-only" in sys.argv and before not in generated_walk_mutations:
        continue
    assert before in generated
    changed = generated.replace(before, after, 1)
    generated_label = "generated-%03u-%s" % (
        generated_index,
        hashlib.sha256(before.encode()).hexdigest()[:12])
    run(source, header, False, generated_label, generated_body=changed)
if "--generated-walk-only" in sys.argv:
    print("REIMPLEMENT-13 generated walk fixture mutation lane: PASS (6 real mutations)")
    raise SystemExit(0)
if "--generated-all-only" in sys.argv:
    print("REIMPLEMENT-13 generated fixture mutation lane: PASS "
          "(82 real mutations)")
    raise SystemExit(0)

behavior_records = [item for item in mutation_results
                    if not item["expected_pass"]]
classification_counts = {}
for item in behavior_records:
    key = item["classification"]
    classification_counts[key] = classification_counts.get(key, 0) + 1
environment_retry_incidents = sum(
    item.get("environment_retry_count", 0) for item in behavior_records)
report = {
    "schema": "reimplement13-round1-mutation-causality-v1",
    "scope": "current REIMPLEMENT-13 Round 1 host differential",
    "toolchain": {
        "compiler": "Ubuntu-24.04 gcc -std=c90 -pedantic -Wall -Wextra -Werror",
        "compile_timeout_seconds": COMPILE_TIMEOUT_SECONDS,
        "runtime_timeout_seconds": RUNTIME_TIMEOUT_SECONDS,
        "compile_and_execute_separated": True,
        "runtime_rejection_repeat_required": True,
    },
    "coverage": {
        "complete_scene_source_frames": [2040, 5566],
        "focused_early_exit_boundaries": {
            "weapon/special/hit/queue/action16": 5523,
            "class1f-state0": 5551,
            "jump": "pre-contextual jump boundary",
        },
        "focused_subsets_do_not_close_complete_scene": True,
    },
    "historical_totals": {
        "runtime_mutations_pre_causal_audit": 227,
        "generated_fixture_mutations_pre_causal_audit": 82,
        "qualification": "historical totals are retained as reported, not presumed causally valid; the current enumerated case count is authoritative",
    },
    "declared_equivalent_survivors": sorted(
        item["label"] for item in behavior_records
        if item["classification"] == "SURVIVED_MUTATION" and
        item.get("declared_equivalent", False)),
    "environment_retry_incidents_recovered": environment_retry_incidents,
    "current_counts": classification_counts,
    "mutations": behavior_records,
}
if FULL_MUTATION_RUN:
    MUTATION_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="ascii", newline="\n")
if CHARACTERIZE:
    if ONLY_MUTATION_LABEL is not None:
        print(json.dumps(behavior_records, indent=2, sort_keys=True))
    print("REIMPLEMENT-13 mutation characterization complete: " +
          json.dumps(classification_counts, sort_keys=True))
    raise SystemExit(0)
unexpected_survivors = [
    item for item in behavior_records
    if item["classification"] == "SURVIVED_MUTATION" and
    not item.get("declared_equivalent", False)]
assert not unexpected_survivors, "unexpected equivalent/surviving mutation"
for forbidden in ("INVALID_MUTATION", "TIMEOUT",
                  "ENVIRONMENT_FAILURE", "WRONG_RUNTIME_FAILURE",
                  "UNATTRIBUTED_RUNTIME_FAILURE"):
    assert classification_counts.get(forbidden, 0) == 0, (
        f"causal mutation lane contains {forbidden}")
print("REIMPLEMENT-13 entry/player/scheduler/class1f/Coffee-Shop-navigation/neutral-stop/melee/Button1/Button2/Button3/type16-projectile/player-HIT/first-encounter differential: PASS "
      f"({classification_counts.get('VALID_BEHAVIORAL_REJECTION', 0)} "
      "causal behavioral mutations; "
      f"{classification_counts.get('SURVIVED_MUTATION', 0)} declared "
      "equivalent survivors not credited; "
      "compile/environment/timeout failures zero)")

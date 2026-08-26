#!/usr/bin/env python3
"""Maintain the sole Round 1 route-segment x authority-family closure matrix."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COVERAGE=ROOT/'data/round1_system_coverage.yaml'
ROUTE=ROOT/'data/oracle10_round1_route.json'
PLAYER=ROOT/'data/oracle11_predator_warrior_authority.json'
GLOBAL_AUDIO=ROOT/'data/oracle11_global_audio_load_release.json'
NAVIGATION=ROOT/'data/oracle11_round1_navigation.json'
ENEMIES=ROOT/'data/oracle11_round1_enemy_archetypes.json'
AUXILIARY=ROOT/'data/oracle11_round1_auxiliary_authority.json'
ENCOUNTERS=ROOT/'data/oracle11_round1_encounter_route_authority.json'
BOSS=ROOT/'data/oracle11_round1_boss_orchestration.json'
HANDOFF=ROOT/'data/oracle11_round1_handoff.json'
RNG=ROOT/'data/oracle11_round1_rng.json'
RECONCILIATION=ROOT/'data/oracle11_round1_writer_reconciliation.json'
SPEC02=ROOT/'data/spec02_round1_executable_contract.json'
FAMILIES=(
 'predator-warrior-player-authority','round1-navigation-terrain-camera',
 'actor-scheduler-allocation-lifecycle','round1-enemy-archetypes',
 'pickups-equipment-weapons-projectiles-hazards-destructibles',
 'encounters-waves-scripted-triggers','round1-boss',
 'stage-clear-failure-continue-round2-handoff','gameplay-audio-load-release',
 'rng-consumption')
ROUTES=('baseline-completion-a','baseline-completion-b','perturbed-completions',
        'failure-continue','targeted-counterfactuals')
CLOSED_PAIRS={('0x1f',12),('0x05',4),('0x10',24),('0x20',24),
              ('0x3a',24),('0x47',24),('0x54',24)}

def overlaps(a,b): return a[0]<=b[1] and b[0]<=a[1]

def build(coverage,route):
    closed_pairs=set(CLOSED_PAIRS)
    enemy_report=None
    if ENEMIES.exists():
        enemy_report=json.loads(ENEMIES.read_text(encoding='ascii'))
        if enemy_report['status']=='SOURCE_CLOSED':
            closed_pairs.update((item['class'],item['type'])
                for item in enemy_report['archetypes'])
    auxiliary_report=None
    if AUXILIARY.exists():
        auxiliary_report=json.loads(AUXILIARY.read_text(encoding='ascii'))
        if auxiliary_report['status']=='SOURCE_CLOSED':
            closed_pairs.update((item['class'],item['type'])
                for item in auxiliary_report['archetypes'])
            for item in auxiliary_report['phantom_census_aliases']:
                parts=item['id'].split('-')
                closed_pairs.add((f"0x{parts[2]}",int(parts[4])))
    encounter_report=None
    closed_route_segments=set()
    if ENCOUNTERS.exists():
        encounter_report=json.loads(ENCOUNTERS.read_text(encoding='ascii'))
        if encounter_report['status']=='SOURCE_CLOSED':
            closed_route_segments.update(
                item['route_segment'] for item in encounter_report['segment_bindings']
                if item['classification']=='SOURCE_CLOSED')
    handoff_report=None
    if HANDOFF.exists():
        handoff_report=json.loads(HANDOFF.read_text(encoding='ascii'))
    bodies={x['id']:x for x in coverage['bodies']}
    if 'rng-consumption' not in bodies:
        bodies['rng-consumption']={'status':'OBSERVED','accepted_evidence':['data/oracle10_round1_route.json']}
    actors=route['actor_instances']
    rows=[]
    for segment in route['segments']:
        span=segment['source_frame_range']
        live=[x for x in actors if overlaps(span,x['source_frame_range'])]
        player=any(x['type']==0 and x['class']=='0x00' and x['slot_address']=='0xff8380' for x in live)
        nonplayer=any(x['slot_address']!='0xff8380' for x in live)
        enemies=any(x['type']==12 and x['class'] in ('0x00','0x01','0x06','0x1f') for x in live)
        boss=any(x['type']==12 and x['class']=='0x06' for x in live)
        nav=any(x['type']==20 and x['class'] in ('0x07','0x08','0x09','0x0a') for x in live)
        rng=any(span[0]<=x['frame']<=span[1] for x in route['rng_changes'])
        audio=any(span[0]<=x<=span[1] for x in route['audio_change_frames'])
        load=any(span[0]<=x<=span[1] for x in route['load_release_boundary_frames'])
        applicable={
          FAMILIES[0]:player,FAMILIES[1]:player or nav,FAMILIES[2]:nonplayer,
          FAMILIES[3]:enemies,FAMILIES[4]:player or nonplayer,
          FAMILIES[5]:enemies,FAMILIES[6]:boss,FAMILIES[7]:True,
          FAMILIES[8]:audio or load,FAMILIES[9]:rng}
        cells=[]
        for family in FAMILIES:
            required=applicable[family]
            status=bodies[family]['status'] if required else 'NOT_REQUIRED_FOR_ROUND1'
            cells.append({'authority_family':family,'required':required,
                'classification':status,'coverage_universe':list(ROUTES),
                'evidence':bodies[family].get('accepted_evidence',[]),
                'unresolved':required and status in ('OBSERVED','PARTIAL','UNKNOWN')})
        rows.append({'route_segment':segment['id'],'source_frame_range':span,
            'route_edge':segment['state_transitions'],'cells':cells})
    required_cells=[c for r in rows for c in r['cells'] if c['required']]
    counts={s:sum(c['classification']==s for c in required_cells)
            for s in ('OBSERVED','PARTIAL','UNKNOWN')}
    unmapped_pairs=[]
    for x in route['actor_archetypes']:
        pair=(x['class'],x['type'])
        if pair not in closed_pairs and x.get('source_closure_status') not in ('SOURCE_CLOSED','NOT_REQUIRED_FOR_ROUND1'):
            unmapped_pairs.append({'class':pair[0],'type':pair[1],'id':x['id']})
    unmapped_edges=[{'segment':s['id'],'source_frame_range':s['source_frame_range']}
        for s in route['segments'] if s['id'] not in closed_route_segments and
        s.get('source_closure_status') not in ('SOURCE_CLOSED','NOT_REQUIRED_FOR_ROUND1')]
    writer_pcs=set(route['baseline_writer_bindings']['route']['unique_pcs'])
    writer_pcs.update(route['baseline_writer_bindings']['qsound']['unique_pcs'])
    for value in route['baseline_writer_bindings']['actor'].values():writer_pcs.update(value['writer_pcs'])
    if enemy_report and enemy_report['status']=='SOURCE_CLOSED':
        writer_pcs.difference_update(enemy_report['owned_authoritative_writer_pcs'])
    if auxiliary_report and auxiliary_report['status']=='SOURCE_CLOSED':
        writer_pcs.difference_update(auxiliary_report['owned_authoritative_writer_pcs'])
    if encounter_report and encounter_report['status']=='SOURCE_CLOSED':
        writer_pcs.difference_update(encounter_report['owned_authoritative_writer_pcs'])
    if handoff_report and handoff_report['status']=='SOURCE_CLOSED':
        writer_pcs.difference_update(handoff_report['owned_authoritative_writer_pcs'])
    rng_report=None
    if RNG.exists():
        rng_report=json.loads(RNG.read_text(encoding='ascii'))
    if rng_report and rng_report['status']=='SOURCE_CLOSED':
        writer_pcs.difference_update(rng_report['owned_authoritative_writer_pcs'])
    reconciliation_report=None
    if RECONCILIATION.exists():
        reconciliation_report=json.loads(RECONCILIATION.read_text(encoding='ascii'))
    if reconciliation_report and reconciliation_report['status']=='SOURCE_CLOSED':
        writer_pcs.difference_update(
            reconciliation_report['owned_authoritative_writer_pcs'])
    events={
      'spawn':len(unmapped_pairs),'damage':1 if counts['PARTIAL'] else 0,
      'audio':len(route['audio_change_frames']) if bodies[FAMILIES[8]]['status']!='SOURCE_CLOSED' else 0,
      'load':len(route['load_release_boundary_frames']) if bodies[FAMILIES[8]]['status']!='SOURCE_CLOSED' else 0,
      'release':len(unmapped_pairs),'rng':route['rng_change_count'] if bodies[FAMILIES[9]]['status']!='SOURCE_CLOSED' else 0}
    gate={'required_observed':counts['OBSERVED'],'required_partial':counts['PARTIAL'],
      'required_unknown':counts['UNKNOWN'],'unmapped_actor_class_type_pairs':len(unmapped_pairs),
      'unmapped_route_edges':len(unmapped_edges),'unowned_events':events,
      'orphan_authoritative_writers':len(writer_pcs),
      'spec02_eligible':all(v==0 for v in counts.values()) and not unmapped_pairs and not unmapped_edges and not any(events.values()) and not writer_pcs}
    return {'schema':'round1-route-authority-matrix-v1','coverage_universe':{
      'rule':'union of both baseline completions, completing perturbations, failure/continue and every targeted counterfactual route',
      'routes':list(ROUTES)},'authority_families':list(FAMILIES),
      'segment_count':len(rows),'cell_count':len(rows)*len(FAMILIES),'rows':rows,
      'unmapped_actor_class_type_pairs':unmapped_pairs,'unmapped_route_edges':unmapped_edges,
      'closure_gate':gate}

def main():
    coverage=json.loads(COVERAGE.read_text(encoding='utf-8'))
    route=json.loads(ROUTE.read_text(encoding='utf-8'))
    player=json.loads(PLAYER.read_text(encoding='utf-8'))
    if player['status']=='SOURCE_CLOSED':
        body=next(item for item in coverage['bodies']
            if item['id']=='predator-warrior-player-authority')
        body['status']='SOURCE_CLOSED'
        evidence=body.setdefault('accepted_evidence',[])
        for item in ('data/oracle11_predator_warrior_authority.json',
                     'data/oracle11_predator_player_audio.json'):
            if item not in evidence:evidence.append(item)
        body['counterfactual']=(
          'all required player bodies and every route-reachable player-origin '
          'gameplay-audio trigger are source-closed; score-only packed-BCD '
          'routines are rejected as audio ownership')
        body['exact_next_experiment']=(
          'Retain the closed Predator Warrior contract while global audio, '
          'route, actor and encounter families are closed.')
    if GLOBAL_AUDIO.exists():
        global_audio=json.loads(GLOBAL_AUDIO.read_text(encoding='ascii'))
        body=next(item for item in coverage['bodies']
            if item['id']=='gameplay-audio-load-release')
        body['status']=global_audio['status']
        evidence=body.setdefault('accepted_evidence',[])
        item='data/oracle11_global_audio_load_release.json'
        if item not in evidence:evidence.append(item)
        item='data/oracle11_global_audio_handlers.json'
        if item not in evidence:evidence.append(item)
        item='data/oracle11_global_audio_trigger_owners.json'
        if item not in evidence:evidence.append(item)
        item='data/oracle11_global_load_release_boundaries.json'
        if item not in evidence:evidence.append(item)
        body['counterfactual']=(
          'the shared main queue, audio-CPU command dispatcher/table/handlers, '
          'grouped QSound effects, and all 175 non-player trigger owners/guards '
          'are source-closed; all four load/release boundaries have source '
          'guards, callers, package identities, legal windows, and suppressions')
        body['exact_next_experiment']=(
          'Retain the closed global audio/load/release contract while the next '
          'dependency-safe ORACLE-11 authority family is closed.')
    if NAVIGATION.exists():
        navigation=json.loads(NAVIGATION.read_text(encoding='ascii'))
        body=next(item for item in coverage['bodies']
            if item['id']=='round1-navigation-terrain-camera')
        body['status']=navigation['status']
        evidence=body.setdefault('accepted_evidence',[])
        for item in ('data/oracle11_round1_navigation.json',
                     'data/oracle08_round1_navigation_bounds.json',
                     'data/oracle10_round1_route.json'):
            if item not in evidence:evidence.append(item)
        body['counterfactual']=(
          'two byte-identical route completions, a completing directional '
          'perturbation, the accepted directional/obstacle controls, and the '
          'route-wide hold/remove controls bind all source bounds, six terrain '
          'records, four navigation bodies, obstacle response, and all 19 '
          'camera lock/unlock runs without a guessed route guard')
        body['exact_next_experiment']=(
          'Retain the closed navigation/terrain/camera contract while the '
          'Round 1 enemy-archetype family is source-closed; damage, destruction '
          'and presentation edges of type-20 actors remain with their declared '
          'authority families.')
    if ENEMIES.exists():
        enemies=json.loads(ENEMIES.read_text(encoding='ascii'))
        body=next(item for item in coverage['bodies']
            if item['id']=='round1-enemy-archetypes')
        body['status']=enemies['status']
        evidence=body.setdefault('accepted_evidence',[])
        for item in ('data/oracle11_round1_enemy_archetypes.json',
                     'data/oracle09_street_alien_state_facing_presentation.json',
                     'data/oracle10_round1_route.json'):
            if item not in evidence:evidence.append(item)
        body['counterfactual']=(
          'two byte-identical route completions bind every route-reachable '
          'state/phase, writer, RNG call, animation/assembly/collision-selector '
          'record and damage edge for classes 0x00, 0x01, 0x06 and 0x1f; '
          'class-removal and offense-suppression controls discriminate every '
          'archetype, with the accepted ORACLE-09 state controls retained')
        body['exact_next_experiment']=(
          'Retain all four source-closed enemy actor contracts while pickups, '
          'hazards, destructibles, encounters, boss orchestration, route '
          'handoff and RNG ownership are closed in their declared families.')
    if AUXILIARY.exists():
        auxiliary=json.loads(AUXILIARY.read_text(encoding='ascii'))
        body=next(item for item in coverage['bodies']
            if item['id']=='pickups-equipment-weapons-projectiles-hazards-destructibles')
        body['status']=auxiliary['status']
        evidence=body.setdefault('accepted_evidence',[])
        for item in ('data/oracle11_round1_auxiliary_authority.json',
                     'data/oracle11_predator_weapon_projectile_resource.json',
                     'data/oracle11_round1_navigation.json'):
            if item not in evidence:evidence.append(item)
        body['counterfactual']=(
          'two byte-identical auxiliary completions plus twelve corrected '
          'full-route class/type suppressions bind every dispatched type-16, '
          'type-20 and type-24 actor; four generic-census half-stride aliases '
          'are proven NOT_REQUIRED, while the original zero-removal controls '
          'are explicitly rejected and preserved outside accepted evidence')
        body['exact_next_experiment']=(
          'Retain the closed player and auxiliary content contracts while '
          'encounter/wave/scripted trigger, boss orchestration, route handoff '
          'and global RNG ownership are source-closed.')
    if ENCOUNTERS.exists():
        encounters=json.loads(ENCOUNTERS.read_text(encoding='ascii'))
        body=next(item for item in coverage['bodies']
            if item['id']=='encounters-waves-scripted-triggers')
        body['status']=encounters['status']
        evidence=body.setdefault('accepted_evidence',[])
        for item in ('data/oracle11_round1_encounter_route_authority.json',
                     'data/oracle06_round1_encounter.json',
                     'data/oracle10_round1_route.json'):
            if item not in evidence:evidence.append(item)
        body['counterfactual']=(
          'two byte-identical completing captures bind all 94 route segments, '
          '14 global route-state edges, 609 route-writer transactions and 56 '
          'Round 1 enemy spawns; completing and non-completing offense, class '
          'removal and route perturbations discriminate the source guards')
        body['exact_next_experiment']=(
          'Retain the closed encounter/wave/scripted-trigger and 94-segment '
          'route map while boss phase/clear orchestration is source-closed.')
    if BOSS.exists():
        boss=json.loads(BOSS.read_text(encoding='ascii'))
        body=next(item for item in coverage['bodies'] if item['id']=='round1-boss')
        body['status']=boss['status']
        evidence=body.setdefault('accepted_evidence',[])
        for item in ('data/oracle11_round1_boss_orchestration.json',
                     'data/oracle11_round1_enemy_archetypes.json',
                     'data/oracle11_round1_encounter_route_authority.json'):
            if item not in evidence:evidence.append(item)
        body['counterfactual']=(
          'two byte-identical completions bind the class-0x06 actor to all 11 '
          'controller phases, eight boss-room spawns, 216 boss RNG calls and '
          'the exact terminal clear writer; suppressing that writer holds the '
          'completed boss sequence in Round 1, and removing class 0x06 cannot clear')
        body['exact_next_experiment']=(
          'Retain the closed boss actor/controller/clear contract while stage '
          'clear, results and the stable Round 2 handoff are source-closed.')
    if HANDOFF.exists():
        handoff=json.loads(HANDOFF.read_text(encoding='ascii'))
        body=next(item for item in coverage['bodies']
            if item['id']=='stage-clear-failure-continue-round2-handoff')
        body['status']=handoff['status']
        evidence=body.setdefault('accepted_evidence',[])
        for item in ('data/oracle11_round1_handoff.json',
                     'data/oracle11_round1_boss_orchestration.json',
                     'data/oracle11_predator_warrior_authority.json',
                     'data/oracle11_global_load_release_boundaries.json'):
            if item not in evidence:evidence.append(item)
        body['counterfactual']=(
          'two byte-identical completions bind the three source stage-clear '
          'player phases, all four post-clear route edges, the accepted '
          'failure/continue branch and four load/release boundaries; the '
          'completing perturbations reach stable Round 2 while exact clear '
          'suppression, class-0x06 removal and no-continue controls cannot')
        body['exact_next_experiment']=(
          'Retain the closed Round 1 clear and stable Round 2 handoff while '
          'route-wide global RNG algorithm, caller ownership and exact '
          'consumption order are source-closed.')
    if RNG.exists():
        rng=json.loads(RNG.read_text(encoding='ascii'))
        body=next(item for item in coverage['bodies'] if item['id']=='rng-consumption')
        body['status']=rng['status']
        evidence=body.setdefault('accepted_evidence',[])
        for item in ('data/oracle11_round1_rng.json',
                     'data/oracle11_round1_enemy_archetypes.json',
                     'data/oracle11_round1_auxiliary_authority.json',
                     'data/oracle10_round1_route.json'):
            if item not in evidence:evidence.append(item)
        body['counterfactual']=(
          'two byte-identical completion ledgers contain exactly 2,280 calls '
          'on 1,023 seed-change frames with zero recurrence or ownership gaps; '
          'the completing route and offense perturbations change consumption '
          'while freezing the shared seed prevents Round 1 completion')
        body['exact_next_experiment']=(
          'Reconcile every remaining authoritative writer PC against the '
          'already source-closed authority-family evidence without weakening '
          'the sole 94 x 10 zero-gap gate.')
    coverage['route_segment_authority_matrix']=build(coverage,route)
    coverage['spec02_closure_gate']=coverage['route_segment_authority_matrix']['closure_gate']
    if coverage['spec02_closure_gate']['spec02_eligible']:
        accepted_spec=(SPEC02.exists() and
          json.loads(SPEC02.read_text(encoding='ascii')).get('status')=='ACCEPTED')
        coverage['next_card']=('REIMPLEMENT-13-SOURCE-CLOSED-ROUND1' if accepted_spec
          else 'SPEC-02-ROUND1-EXECUTABLE-CONTRACT')
    COVERAGE.write_bytes((json.dumps(coverage,sort_keys=True,indent=2)+'\n').encode('ascii'))
    gate=coverage['spec02_closure_gate']
    print('Round 1 authority matrix: segments=%d cells=%d eligible=%s' % (
      coverage['route_segment_authority_matrix']['segment_count'],
      coverage['route_segment_authority_matrix']['cell_count'],gate['spec02_eligible']))
    print(json.dumps(gate,sort_keys=True))
if __name__=='__main__':main()

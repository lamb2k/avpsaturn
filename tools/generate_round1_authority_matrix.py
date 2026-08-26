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
        if pair not in CLOSED_PAIRS and x.get('source_closure_status') not in ('SOURCE_CLOSED','NOT_REQUIRED_FOR_ROUND1'):
            unmapped_pairs.append({'class':pair[0],'type':pair[1],'id':x['id']})
    unmapped_edges=[{'segment':s['id'],'source_frame_range':s['source_frame_range']}
        for s in route['segments'] if s.get('source_closure_status') not in ('SOURCE_CLOSED','NOT_REQUIRED_FOR_ROUND1')]
    writer_pcs=set(route['baseline_writer_bindings']['route']['unique_pcs'])
    writer_pcs.update(route['baseline_writer_bindings']['qsound']['unique_pcs'])
    for value in route['baseline_writer_bindings']['actor'].values():writer_pcs.update(value['writer_pcs'])
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
        body['counterfactual']=(
          'the shared main queue-to-QSound-RAM transport is source-closed; '
          'non-player trigger provenance, audio-CPU transport and four '
          'load/release edges remain open')
        body['exact_next_experiment']=(
          'Bind the 175 non-player trigger provenance groups, shared-RAM to '
          'audio-CPU/QSound transport, and four load/release boundary guards.')
    coverage['route_segment_authority_matrix']=build(coverage,route)
    coverage['spec02_closure_gate']=coverage['route_segment_authority_matrix']['closure_gate']
    COVERAGE.write_bytes((json.dumps(coverage,sort_keys=True,indent=2)+'\n').encode('ascii'))
    gate=coverage['spec02_closure_gate']
    print('Round 1 authority matrix: segments=%d cells=%d eligible=%s' % (
      coverage['route_segment_authority_matrix']['segment_count'],
      coverage['route_segment_authority_matrix']['cell_count'],gate['spec02_eligible']))
    print(json.dumps(gate,sort_keys=True))
if __name__=='__main__':main()

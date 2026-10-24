"""Reproducible transferred marginal calibration and independently seeded mechanism checks.

Medical variables are neither calibrated nor interpreted here. These observations
are survey responses, not randomized communication-treatment effects.
"""
from __future__ import annotations
import json, statistics
from pathlib import Path
from regional_sim import Config, World
from regional_sim.scenarios import Shock

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'calibration'/'travel_information_results.json'

def run(seed, shock=True, silent=False, n=3000):
    shocks=(Shock(2.,'road_closure',-1,0.,36.),) if shock else ()
    w=World(Config(households=n,days=3,seed=seed,trace='',availability_extension=False,extra_shocks=shocks))
    if silent:
        w.internet[:]=False; w.news_access[:]=False
    prefs={'route':float(w.pref_route_change.mean()),'shift':float(w.pref_time_shift.mean())}
    final=w.run();w.invariants()
    keys=('completed_commutes','road_alerts_received','commute_first_choices',
          'message_informed_first_commute_choices','message_informed_first_route_choices',
          'message_informed_first_shift_choices','informed_commute_requests',
          'informed_route_choices','informed_shift_choices','alternate_route_trips',
          'travel_capacity_rejections','peer_relocation_plans_received')
    result={k:(final[k] if k in final else int(w.stats[k])) for k in keys}
    result.update(seed=seed,prefs=prefs,final_goods_error=final['goods_error_max'])
    nreq=result['message_informed_first_commute_choices']
    result['conditional_route_share']=result['message_informed_first_route_choices']/nreq if nreq else None
    result['conditional_shift_share']=result['message_informed_first_shift_choices']/nreq if nreq else None
    return result

def main():
    seeds=(47,48,49)
    cases={
      'official_and_peer_road_notice':[run(s) for s in seeds],
      'no_communications_control':[run(s,silent=True) for s in seeds],
      'routine_control':[run(s,shock=False) for s in seeds],
    }
    # Direct marginal moment matching, not causal calibration:
    # proportions are drawn once per synthetic household.
    targets={'reported_avoid_rush_hour':.48,'reported_route_change':.44}
    samples={'prefers_time_shift':float(statistics.mean(x['prefs']['shift'] for x in cases['official_and_peer_road_notice'])),
             'prefers_route_change':float(statistics.mean(x['prefs']['route'] for x in cases['official_and_peer_road_notice']))}
    out={'status':'transferred closure-behavior marginal calibration, no independently estimated communication effect',
         'target_study':'Ye, Mokhtarian & Circella, Fix I-5 Sacramento (2008 closure; published 2012)',
         'targets':targets,'sampled_preference_means':samples,'cases':cases,
         'medical_outcomes':'out of scope; excluded from fitting and report',
         'limits':['conditional-on-awareness mapping is a transfer assumption',
                   'Fix I-5 marginals are nonexclusive; joint effects not published in extracted abstract',
                   'alternative road capacity and trip time are C-level assumptions',
                   'perceived accuracy, exposure, workplace flexibility, destination and peer coordination remain uncalibrated']}
    OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()

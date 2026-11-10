"""Evidence-bounded inverse calibration. Does not claim historical event reconstruction.

The observed customer counts mix residential/nonresidential and have a different
boundary from the 2024 household denominator; resulting power factors are
conditional sensitivity-fit parameters, not measured transmission capacities.
"""
from __future__ import annotations
import json, statistics, sys, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from regional_sim.engine import Config, World
from regional_sim.scenarios import Shock

B = {x['id']:x for x in json.loads((ROOT/'benchmarks'/'observations.json').read_text())['observations']}
N = 10000
FIT_SEEDS = (42,43,44)
CHECK_SEEDS = (46,47)

def power_probe(multiplier:float, hour:float, seed:int) -> dict:
    w=World(Config(households=N, days=4, seed=seed, trace=''))
    w.t=hour
    w.shock(Shock(hour,'power',-1,multiplier,1))
    w.power()
    result={'outage_fraction':w.power_unserved_households_last/N,
            'unserved_kwh':w.energy_unserved_kwh,
            'mean_noncritical_service':float(w.power_ratio.mean())}
    w.invariants();w.trace.close()
    return result

def fit_power(hour, target, seeds=FIT_SEEDS):
    lo,hi=.01,1.0
    checks=[]
    for k in range(9):
        mid=(lo+hi)/2
        v=statistics.mean(power_probe(mid,hour,s)['outage_fraction'] for s in seeds)
        checks.append({'trial':k,'multiplier':mid,'outage_fraction':v})
        if v>target: lo=mid
        else: hi=mid
    candidate=min(checks,key=lambda v:abs(v['outage_fraction']-target))
    return candidate['multiplier'],checks

def commute_run(freeflow, seed, n=10000, days=5):
    w=World(Config(households=n,days=days,seed=seed,trace='',free_flow_minutes=freeflow))
    result=w.run()
    return result['mean_morning_commute_minutes']

def mean_results(m,h,seeds):
    xs=[power_probe(m,h,s) for s in seeds]
    vals=[a['outage_fraction'] for a in xs]
    return {'mean_outage_fraction':statistics.mean(vals),
            'sample_sd':statistics.stdev(vals) if len(vals)>1 else 0.,
            'min':min(vals),'max':max(vals),
            'expanded_customer_equivalents_PROXY':statistics.mean(vals)*B['acs2024_households']['value'],
            'mean_unserved_kwh_in_one_simulated_hour':statistics.mean(x['unserved_kwh'] for x in xs)}

def main():
    target_commute=B['acs2024_commute']['value']
    base=[commute_run(24.,s) for s in FIT_SEEDS]
    initial=24.*target_commute/statistics.mean(base)
    # 2nd pass corrects minor nonlinearities/rounding (no source constraints changed).
    first=[commute_run(initial,s) for s in FIT_SEEDS]
    freeflow=initial*target_commute/statistics.mean(first)
    after=[commute_run(freeflow,s) for s in CHECK_SEEDS]
    hh=B['acs2024_households']['value']
    targets={'peak':B['aep2022_peak']['value']/hh,'mid':B['aep2022_mid']['value']/hh}
    m1,trace1=fit_power(20.,targets['peak'])
    m2,trace2=fit_power(38.,targets['mid'])
    shocks=[Shock(20.,'power',-1,m1,18.), Shock(38.,'power',-1,m2,14.85)]
    (ROOT/'configs'/'aep_2022_proxy_shocks.json').write_text(json.dumps([vars(s) for s in shocks],indent=2)+'\n')
    cfg=json.loads((ROOT/'configs'/'development.json').read_text())
    cfg.update({'free_flow_minutes':round(freeflow,6),'days':4,'scenario':'routine'})
    (ROOT/'configs'/'calibrated_2024.json').write_text(json.dumps(cfg,indent=2)+'\n')
    result={'status':'PARTIAL PROXY CALIBRATION, NOT independently validated',
            'benchmark_file':'benchmarks/observations.json',
            'methods':{'commute':'paired-seed scaling of BPR t0 to mean morning one-way commute_arrival minutes vs ACS commuters',
                       'outage':'inverse-fit exogenous regional power multiplier to observed customer counts divided by 2024 all-CBSA household estimate; one proxy observation per factor',
                       'historical_time':'hour 20 is Tuesday 20:00, hour 38 Wednesday 14:00; Thursday restoration timing imposed externally; world time origin is synthetic not the real 2022 calendar',
                       'scope_caveat':'AEP outage includes nonresidential customers, storm-initiated damage, and a boundary different from CBSA 18140; expansion is NOT measured and cannot be considered a fitted service territory',
                       'model_caveat':'Household ranks are a fractional-energy-allocation proxy, NOT actual feeder circuit disconnections; critical service prioritized independently'},
            'fitting_seeds':list(FIT_SEEDS),'evaluation_seeds':list(CHECK_SEEDS),
            'commute':{'observed_minutes':target_commute,'published_margin_of_error_minutes':B['acs2024_commute']['published_margin_of_error'],
                       'initial_freeflow_minutes':24.,'fitted_freeflow_minutes':freeflow,
                       'before_fit_mean_minutes':statistics.mean(base),'fit_seed_firstpass_mean_minutes':statistics.mean(first),
                       'other_seed_mean_minutes':statistics.mean(after), 'other_seed_values':after},
            'power':{'denominator_CBSA_households_2024':hh,'denominator_MOE':B['acs2024_households']['published_margin_of_error'],
                     'events':[]},
            'gaps':['AEP Columbus-area all-account denominator and 2022 same-date geography unavailable',
                    'Only two observed outage points; two shock multipliers are inverse-forced, not independent validation',
                    'Peak count approximation has no published sampling CI; cannot report calibrated statistical CIs',
                    'Model lacks electrical line topology, protection coordination and repair crew scheduling',
                    'NERC reported firm MW shed cannot be equated to outages without real sectoral load/account mapping',
                    'Communication figures are all-service-area social impressions rather than comparable individual exposure counts',
                    'No measured matched-shock effect data for payments, roads, retail losses, water/clinic demand or precautionary buying',
                    'No independent shock-response benchmark held out for final validation',
                    'June 15 AEP bulletin has an internally inconsistent statewide-vs-Columbus outage total; WOSU 87,560 Franklin County at 13:11 is an imperfect corroboration of 87,000 Columbus 14:00']}
    for label,h,target,m,trace in (('peak',20.,targets['peak'],m1,trace1),('mid',38.,targets['mid'],m2,trace2)):
        fit=mean_results(m,h,FIT_SEEDS); other=mean_results(m,h,CHECK_SEEDS)
        result['power']['events'].append({'name':label,'relative_hour':h,
            'observed_approx_accounts':B['aep2022_'+label]['value'],
            'target_PROXY_fraction':target,'fit_external_power_multiplier':m,
            'fit_seeds':fit,'unseen_seeds_same_event_NOT_independent_historical_validation':other,
            'bisection_trials':trace})
    # Run the actual interlinked DES with the calibrated inputs and test conservation.
    full=[]
    for seed in CHECK_SEEDS:
        w=World(Config(households=N,days=4,seed=seed,trace='',free_flow_minutes=freeflow,
                       extra_shocks=tuple(shocks)))
        final=w.run();w.invariants()
        control=World(Config(households=N,days=4,seed=seed,trace='',free_flow_minutes=freeflow))
        routine=control.run();control.invariants()
        downstream=('energy_unserved_kwh','grocery_spoiled_units','unmet_grocery_units','message_exposures',
                    'message_reach','sales_units','clinic_completed','water_unmet_m3',
                    'payment_failures','shop_power_closures')
        paired_differences={k:round(final[k]-routine[k],5) for k in downstream}
        at_hour={h:int(x) for h,x,_ in w.power_hourly}
        full.append({'seed':seed,'hour20_unserved_households':at_hour.get(20.),
                     'hour38_unserved_households':at_hour.get(38.),
                     'peak_unserved_household_fraction':final['power_unserved_households_peak']/N,
                     'unserved_household_hours':final['power_unserved_household_hours'],
                     'unserved_kwh':final['energy_unserved_kwh'],
                     'grocery_spoiled_units':final['grocery_spoiled_units'],
                     'unmet_grocery_units':final['unmet_grocery_units'],
                     'message_exposures':final['message_exposures'],
                     'goods_error_max':final['goods_error_max'],
                     'money_conserved':final['total_money_cents']==w.money_initial,
                     'reserves_conserved':w.reserve_total()==w.reserve_initial,
                     'final_unserved_households':final['power_unserved_households_last'],
                     'paired_differences_vs_same_seed_routine_NOT_empirical_targets':paired_differences})
    result['full_interlinked_runs']=full
    path=ROOT/'calibration'/'results.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'commute':result['commute'],
                      'power':[{k:v for k,v in e.items() if k!='bisection_trials'} for e in result['power']['events']],
                      'full_interlinked_runs':full},indent=2))

if __name__=='__main__':main()

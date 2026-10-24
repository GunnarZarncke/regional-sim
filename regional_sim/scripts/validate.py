"""Reproducible software-validation runs. NOT independent external empirical validation."""
from __future__ import annotations
import json, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regional_sim import Config, World
from regional_sim.scenarios import Shock

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports'
REPORT.mkdir(exist_ok=True)


def run(n, days, seed, shock=None, **kwargs):
    cfg = Config(households=n, days=days, seed=seed, trace='',
                 extra_shocks=(shock,) if shock is not None else (), **kwargs)
    w = World(cfg)
    x = w.run()
    return x, dict(w.stats), dict(w.trace.counts)


def summary(xs):
    a = list(map(float, xs))
    return {'mean': statistics.mean(a), 'sample_sd': statistics.stdev(a) if len(a) > 1 else None,
            'range': [min(a), max(a)], 'n_seeds': len(a)}


seeds = (42, 43, 44, 45)
shock = Shock(25, 'power', -1, .35, 24)
metrics = ('energy_unserved_kwh', 'message_reach', 'message_exposures', 'sales_units',
           'clinic_completed', 'clinic_queue', 'grocery_spoiled_units', 'goods_error_max',
           'unmet_grocery_units', 'stockouts', 'payment_failures', 'mean_power_service',
           'supplier_grocery', 'warehouse_grocery', 'retail_grocery', 'water_unmet_m3', 'interrupted_feeder_hours')
paired=[]
for seed in seeds:
    ordinary, os, ot = run(10000, 5, seed)
    disrupted, ds, dt = run(10000, 5, seed, shock)
    paired.append({'seed': seed, 'ordinary':ordinary, 'disrupted':disrupted,
                   'difference':{k:disrupted[k]-ordinary[k] for k in metrics},
                   'ordinary_event_counts':ot, 'disrupted_event_counts':dt})

# Domain-isolation smoke checks; these are synthetic interventions, not historical events.
domains=('power','road','communication','supply','payments','retail','services','demand')
isolations=[]
for d in domains:
    base, bs, _ = run(1200, 3, 101)
    shocked, ss, _ = run(1200, 3, 101, Shock(25,d,-1,(1.8 if d=='demand' else .1),24))
    isolations.append({'domain':d, 'baseline':{k:base[k] for k in metrics},
                       'shocked':{k:shocked[k] for k in metrics},
                       'stats_delta':{key:int(ss.get(key,0)-bs.get(key,0)) for key in
                                      ('travel_capacity_rejections','payment_network_declined','logistics_delays','stockouts')},
                       'note':'No effect at household level need not imply no domain response; buffering can mask short shocks.'})

result={
  'status':'INTERNAL SOFTWARE CHECKS ONLY; not an external scientific validation',
  'reference':'synthetic Columbus OH CBSA 18140, reference year 2024',
  'paired_shock':vars(shock), 'seeds':list(seeds),
  'paired':paired,
  'across_seed_difference':{k:summary([p['difference'][k] for p in paired]) for k in metrics},
  'domain_shock_smoke':isolations,
  'heldout_scenarios_used':False,
  'independently_documented_response_benchmark_passed_per_domain':False,
}
with open(REPORT/'internal_validation.json','w',encoding='utf8') as f:
    json.dump(result,f,indent=2)
print(json.dumps(result['across_seed_difference'],indent=2))

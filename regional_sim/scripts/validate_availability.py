"""Run transparent fitted-point and nonfitted operational availability smoke checks."""
import json, statistics
from pathlib import Path
from regional_sim.engine import World, Config
from regional_sim.scenarios import Shock
from regional_sim.availability import relocation_probability, SMB_SHUTDOWN_1D

out={"source_targets":{"household_day1_intention":.33,"household_day14_intention":.83,"smb_day1_shutdown_intention":.49},
     "interpretation":"These are fitted stated-response targets, NOT independent historical validation.","runs":[]}
for duration,days in ((24,3),(336,16)):
 for seed in (41,42,43):
  w=World(Config(households=2400,retailers=120,days=days,seed=seed,trace='',
      extra_shocks=(Shock(0.,'power',-1,0.,duration),)))
  end=w.run(); daily=w.metrics
  rec={"duration_hours":duration,"seed":seed,"n":2400,"retailers":120,
       "first_day_away_fraction":daily[0]["people_temporarily_away"]/2400,
       "last_affected_day_away_fraction":daily[duration//24-1]["people_temporarily_away"]/2400,
       "first_day_power_closed_retail_fraction":1-daily[0]["firms_power_operable"]/120,
       "first_day_grid_unavailable_site_fraction":1-daily[0]["normal_grid_site_access"]/120,
       "relocations_completed":end["relocation_completed"],"returns_completed":end["relocation_returned"],
       "last_away_count":end["people_temporarily_away"],
       "outside_region_grocery_need_units":end["outside_region_grocery_requirement_units"],
       "goods_conservation_error_max":end["goods_error_max"]}
  out["runs"].append(rec)
out["mean_checks"]={}
for duration in (24,336):
 rs=[x for x in out["runs"] if x["duration_hours"]==duration]
 target=relocation_probability(duration)
 k=f"{duration}h"
 out["mean_checks"][k]={"stated_intent_target":target,
     "simulated_last_affected_day_away_fraction_mean":statistics.mean(x["last_affected_day_away_fraction"] for x in rs),
     "simulated_last_affected_day_away_fraction_range":[min(x["last_affected_day_away_fraction"] for x in rs),max(x["last_affected_day_away_fraction"] for x in rs)],
     "simulated_first_day_firm_power_closed_fraction_mean":statistics.mean(x["first_day_power_closed_retail_fraction"] for x in rs),
     "all_returned_at_end":all(x["relocations_completed"]==x["returns_completed"] for x in rs)}
path=Path('calibration/availability_results.json');path.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out["mean_checks"],indent=2))

"""Direction-only coupling checks. Magnitudes are not calibrated."""
import unittest
import numpy as np
from regional_sim import Config, World
from regional_sim.scenarios import Shock


def world(n=128, days=2, seed=23, **kw):
    return World(Config(households=n, days=days, seed=seed, trace="",
                        availability_extension=False, **kw))


class CouplingDirectionTests(unittest.TestCase):
    def test_road_closure_defers_main_corridor_freight(self):
        blocked = world()
        blocked.shock(Shock(0, "road_closure", -1, 0.0, 24))
        open_road = world()
        q = np.array([10.0, 0.0])
        blocked.ship(blocked.wh, blocked.n, q.copy(), 0, "retailer_restock")
        open_road.ship(open_road.wh, open_road.n, q.copy(), 0, "retailer_restock")
        sid_b, sid_o = blocked.ship_id, open_road.ship_id
        blocked.ship_depart(sid_b)
        open_road.ship_depart(sid_o)
        self.assertGreater(blocked.stats["logistics_delays"], 0)
        self.assertEqual(open_road.stats["logistics_delays"], 0)
        self.assertGreater(open_road.stats["vehicle_trips"], 0)
        self.assertIn(sid_b, blocked.shipments)
        blocked.trace.close()
        open_road.trace.close()

    def test_payments_shock_declines_electronic_transfer(self):
        w = world()
        w.shock(Shock(0, "payments", -1, 0.0, 24))
        self.assertIsNone(w.transfer(0, w.n, 100, "retail_sale"))
        self.assertGreater(w.stats["payment_network_declined"], 0)
        w.trace.close()

    def test_power_to_payments_blocks_then_ablates(self):
        linked = world()
        linked.comm_up[:] = False
        self.assertIsNone(linked.transfer(0, linked.n, 100, "retail_sale"))
        ablated = world(disable_coupling=("power_to_payments",))
        ablated.comm_up[:] = False
        self.assertIsNotNone(ablated.transfer(0, ablated.n, 100, "retail_sale"))
        linked.trace.close()
        ablated.trace.close()

    def test_power_to_retail_closures_exceed_ablation_on_short_run(self):
        shock = Shock(1, "power", -1, 0.0, 24)
        on = world(n=400, days=2, extra_shocks=(shock,))
        off = world(n=400, days=2, extra_shocks=(shock,),
                    disable_coupling=("power_to_retail",))
        a, b = on.run(), off.run()
        self.assertGreater(a["shop_power_closures"], b["shop_power_closures"])
        self.assertGreaterEqual(a["grocery_spoiled_units"], b["grocery_spoiled_units"])

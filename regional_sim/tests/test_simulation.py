import math
import unittest
from dataclasses import FrozenInstanceError
from regional_sim import Config, World
from regional_sim.policy import Action
from regional_sim.scenarios import Shock, generate


def world(n=128, days=2, seed=23, **kw):
    return World(Config(households=n, days=days, seed=seed, trace='', **kw))

class ModelTests(unittest.TestCase):
    def test_reproducible_seed(self):
        a, b = world(), world()
        x, y = a.run(), b.run()
        self.assertEqual(x, y)
        self.assertEqual(dict(a.trace.counts), dict(b.trace.counts))

    def test_different_seeds(self):
        a, b = world(seed=12), world(seed=13)
        self.assertFalse((a.income == b.income).all())
        self.assertNotEqual(a.run()['household_grocery'], b.run()['household_grocery'])

    def test_money_goods_and_reserve_invariants(self):
        w = world(n=512, days=4)
        w.run()
        w.invariants()
        self.assertGreater(w.stats['grocery_sales_units_milli'], 0)
        self.assertGreater(w.stats['vehicle_trips'], 0)
        self.assertGreater(w.produced[0], 0)
        self.assertGreater(w.consumed[0], 0)

    def test_goods_shipment_has_transit_account(self):
        w = world()
        pre = w.goods_total().copy()
        w.ship(w.wh, w.n, __import__('numpy').array([10., .0]), 0, 'retailer_restock')
        self.assertGreater(w.in_transit[0], 0)
        self.assertAlmostEqual(float(w.goods_total()[0]), float(pre[0]))
        w.ship_depart(1)
        # goods cannot appear at destination before a real transport arrival
        self.assertGreater(w.in_transit[0], 0)
        w.ship_arrival(1)
        self.assertAlmostEqual(float(w.in_transit[0]), 0.)
        w.invariants()
        w.trace.close()

    def test_reserve_facility_is_explicit_not_created(self):
        w = world()
        sender = 0
        receiver = w.n if w.bank[w.n] != w.bank[0] else w.n + 1
        w.facility_reserve += int(w.reserve[0])
        w.reserve[0] = 0
        reserve_before = w.reserve_total()
        tx = w.transfer(sender, receiver, 900, 'wage')
        self.assertIsNotNone(tx)
        w.settle(tx)
        self.assertEqual(w.facility_debt[0], 900)
        self.assertEqual(w.reserve_total(), reserve_before)
        w.invariants()
        w.trace.close()

    def test_policy_cannot_read_other_private_balances(self):
        w = world()
        o = w.obs(0)
        self.assertNotIn('world', o.__dataclass_fields__)
        self.assertNotIn('other_household_balances', o.__dataclass_fields__)
        with self.assertRaises(FrozenInstanceError):
            o.balance_cents = 0
        w.trace.close()

    def test_fabricated_participant_stockout_claim_rejected(self):
        w = world()
        w.t = 5.
        w.actions[900] = (0, Action('send', payload='retail_stockout'), 'requested')
        w.action(900)
        self.assertEqual(len(w.messages), 0)
        self.assertEqual(w.actions[900][2], 'rejected')
        w.trace.close()

    def test_complex_contagion_counts_independent_sources_not_forwards(self):
        w = world()
        i = 3
        w.attention[i] = 1.
        w.internet[i] = True
        w.comm_up[:] = True
        w.threshold[i] = 2
        for mid, origin, evidence in [(1, 0, 'firsthand'), (2, 0, 'firsthand'),
                                      (3, 7, 'opinion'), (4, 7, 'firsthand')]:
            w.messages[mid] = dict(id=mid, sender=origin, origin=origin, created=0.,
                                   claim='retail_stockout', evidence=evidence, ttl=0, recipients=set())
            w.deliver((mid, i, 'close'))
            if mid < 4:
                self.assertFalse(w.adopted[i])
        self.assertTrue(w.adopted[i])
        self.assertEqual(len(w.claim_sources[i]['retail_stockout']), 2)
        self.assertGreater(w.stats['repeated_source_exposures'], 0)
        w.trace.close()

    def test_power_balance_priority_and_recovery(self):
        w = world(n=1200, days=3)
        w.shock(Shock(0., 'power', 0, .15, 10.))
        w.power()
        self.assertLess(w.power_ratio[0], .95)
        self.assertGreaterEqual(w.critical_ratio[0], w.power_ratio[0])
        w.factor.clear()
        w.t = 11
        w.power()
        self.assertAlmostEqual(w.power_ratio[0], 1., places=6)
        w.invariants()
        w.trace.close()

    def test_disruption_drives_messaging_and_unserved_energy(self):
        w = world(n=480, days=3, extra_shocks=(Shock(10., 'power', -1, .35, 24.),))
        s = w.run()
        self.assertGreater(s['energy_unserved_kwh'], 0)
        self.assertGreater(s['interrupted_feeder_hours'], 0)
        self.assertGreater(s['message_exposures'], 0)
        self.assertAlmostEqual(s['mean_power_service'], 1.)

    def test_road_saturation_defers_trip(self):
        w = world()
        for j in range(6):
            self.assertTrue(w.road_trip(0, 1, 'commute_arrival', (0, 0, 0)))
        self.assertFalse(w.road_trip(0, 1, 'commute_arrival', (0, 0, 0)))
        w.trace.close()

    def test_ablation_isolation_power_to_retail(self):
        # Direct mechanism check: disabled coupling prevents store closure on same feeder.
        a, b = world(n=600), world(n=600, disable_coupling=('power_to_retail',))
        for w in (a,b):
            w.t = 12
            w.attended[w.n:w.wh] = 999
            w.power_ratio[:] = 0.
            w.shop_arrival((None, 0, 1., 0))
        self.assertEqual(a.stats['shop_power_closed'], 1)
        self.assertEqual(b.stats['shop_power_closed'], 0)
        a.trace.close(); b.trace.close()

    def test_weekend_retail_and_essential_shift(self):
        w = world(n=240)
        w.employed[1] = True
        w.remote[1] = False
        w.job[1] = 0
        self.assertTrue(w.shift_for(1, 5))  # Saturday, scheduled retail coverage
        w.employed[0] = True
        w.remote[0] = False
        w.job[0] = 0
        self.assertFalse(w.shift_for(0, 5))
        w.trace.close()

    def test_medication_sale_moves_money_and_physical_stock(self):
        w = world(n=480)
        w.t = 10.
        i, account = 0, w.n
        w.attended[account] = 999
        before = float(w.goods[i, 1])
        stock_before = float(w.goods[account, 1])
        self.assertGreater(stock_before, .5)
        w.shop_arrival((None, i, .5, 1))
        self.assertAlmostEqual(float(w.goods[i, 1] - before), .5)
        self.assertAlmostEqual(float(stock_before - w.goods[account, 1]), .5)
        w.invariants()
        w.trace.close()

    def test_shop_intention_respects_published_opening_time(self):
        from dataclasses import replace
        from regional_sim.policy import ScriptedPolicy
        import random
        w = world()
        o = replace(w.obs(0), time=23., groceries=0., pending_grocery_purchase=False)
        acts = ScriptedPolicy().decide(o, random.Random(1))
        buy = next(x for x in acts if x.kind == 'buy')
        self.assertGreater(buy.delay_hours, 8.)
        self.assertLess(buy.delay_hours, 10.)
        w.trace.close()

    def test_scenario_prespecified_and_reproducible(self):
        self.assertEqual(generate('severe', 30, 12, 5), generate('severe', 30, 12, 5))
        self.assertNotEqual(generate('severe', 30, 12, 5), generate('severe', 30, 12, 6))
        self.assertEqual(generate('routine', 30, 12, 5), [])

if __name__ == '__main__':
    unittest.main()

class CalibrationMechanismTests(unittest.TestCase):
    def test_shock_at_hourly_tick_precedes_power_recalculation(self):
        w=world(n=600,days=2,extra_shocks=(Shock(20.,'power',-1,.3,2.),))
        w.run()
        hour_to_out={h:n for h,n,_ in w.power_hourly}
        self.assertEqual(hour_to_out[19.],0)
        self.assertGreater(hour_to_out[20.],0)
        self.assertEqual(hour_to_out[22.],0)

    def test_configurable_free_flow_affects_travel(self):
        a,b=world(n=400,free_flow_minutes=24.),world(n=400,free_flow_minutes=18.)
        a.road_trip(0,1,'commute_arrival',(0,0,0))
        b.road_trip(0,1,'commute_arrival',(0,0,0))
        self.assertGreater(a.stats['travel_minutes_total'],b.stats['travel_minutes_total'])
        a.trace.close(); b.trace.close()

    def test_power_outage_counts_bounded_by_population(self):
        w=world(n=500,days=2,extra_shocks=(Shock(20.,'power',-1,.6,2.),))
        s=w.run()
        self.assertTrue(0<=s['power_unserved_households_peak']<=w.n)
        self.assertEqual(s['power_unserved_households_last'],0)

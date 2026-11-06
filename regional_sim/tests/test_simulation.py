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
            w.store_workaround[:] = False
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

class AvailabilityExtensionTests(unittest.TestCase):
    def test_stated_response_curve_exact_fit(self):
        from regional_sim.availability import relocation_probability, relocation_trigger_hours
        self.assertAlmostEqual(relocation_probability(24), .33, places=12)
        self.assertAlmostEqual(relocation_probability(14 * 24), .83, places=12)
        for u in (.02, .33, .7, .82):
            self.assertAlmostEqual(relocation_probability(relocation_trigger_hours(u)), u, places=10)
        self.assertTrue(math.isinf(relocation_trigger_hours(.9)))

    def test_power_loss_makes_site_unavailable_without_damage(self):
        w = world(n=1200, days=2)
        w.shock(Shock(0., 'power', -1, 0., 24.))
        w.power()
        self.assertEqual(w.store_site_usable.sum(), 0)
        self.assertEqual(w.store_operational.sum(), w.store_workaround.sum())
        self.assertEqual(w.goods_total()[0], w.goods_initial[0])
        w.invariants(); w.trace.close()

    def test_relocation_is_reversible_and_consumes_roads(self):
        w = world(n=1200, days=4, extra_shocks=(Shock(0., 'power', -1, 0., 48.),))
        s = w.run()
        self.assertGreater(s['relocation_completed'], 0)
        self.assertEqual(s['people_temporarily_away'], 0)
        self.assertEqual(s['relocation_completed'], s['relocation_returned'])
        self.assertGreater(s['outside_region_grocery_requirement_units'], 0)
        w.invariants()

    def test_away_household_cannot_complete_local_shopping(self):
        w = world(n=480)
        w.t = 12.
        w.household_local[0] = False
        w.attended[w.n] = 999
        stock = w.goods[0, 0]
        w.shop_arrival((None, 0, 1., 0))
        self.assertEqual(w.goods[0, 0], stock)
        self.assertFalse(w.shift_for(0, 0))
        w.invariants(); w.trace.close()

    def test_availability_extension_can_be_ablated(self):
        a = world(n=480, days=2, extra_shocks=(Shock(0.,'power',-1,0.,24.),))
        b = world(n=480, days=2, availability_extension=False,
                  extra_shocks=(Shock(0.,'power',-1,0.,24.),))
        a.run(); b.run()
        self.assertGreater(a.stats['relocation_completed'], 0)
        self.assertEqual(b.stats['relocation_completed'], 0)
        self.assertEqual(b.snapshot()['people_temporarily_away'], 0)

class OperationalDependencyTests(unittest.TestCase):
    def test_road_shutdown_blocks_departure_without_disappearing_people(self):
        power = (Shock(0., 'power', -1, 0., 24.),)
        a = world(n=1200, days=3, retailers=60, extra_shocks=power)
        b = world(n=1200, days=3, retailers=60,
                  extra_shocks=power + (Shock(0., 'road', -1, 0., 24.),))
        s1, s2 = a.run(), b.run()
        self.assertGreater(s1['relocation_completed'], 0)
        self.assertEqual(s2['relocation_completed'], 0)
        self.assertGreater(s2['relocation_transport_deferred'], 0)
        self.assertEqual(s2['people_locally_present'], 1200)
        a.invariants(); b.invariants()

class PolicyOwnershipAndSocialCausalityTests(unittest.TestCase):
    def test_world_never_relocates_if_policy_does_not_request_it(self):
        class Stay:
            def decide(self, o, rng):
                return [Action('none')]
        w = World(Config(households=480, days=3, trace='',
                         extra_shocks=(Shock(0., 'power', -1, 0., 36.),)), policy=Stay())
        end = w.run()
        self.assertEqual(end['relocation_completed'], 0)
        self.assertEqual(end['people_temporarily_away'], 0)
        self.assertGreater(end['power_unserved_household_hours'], 0)

    def test_custom_policy_can_request_relocation_without_outage(self):
        class Independent:
            def decide(self, o, rng):
                return [Action('relocate')] if o.locally_present and not o.relocation_pending else [Action('none')]
        w = World(Config(households=80, days=1, trace=''), policy=Independent())
        end = w.run()
        self.assertGreater(end['relocation_completed'], 0)
        w.invariants()

    def test_baseline_policy_consumes_independent_stockout_messages(self):
        from dataclasses import replace
        from regional_sim.policy import ScriptedPolicy
        import random
        w = world(n=100)
        o = replace(w.obs(0), groceries=0., household_size=2, grocery_need_daily=1.,
                    balance_cents=50000, cash_cents=0, time=10.,
                    availability_enabled=False, pending_grocery_purchase=False,
                    current_claim_exposures={'retail_stockout': 0}, adoption_threshold=2)
        ordinary = ScriptedPolicy().decide(o, random.Random(31))
        reinforced = ScriptedPolicy().decide(replace(o, current_claim_exposures={'retail_stockout':2}), random.Random(31))
        self.assertEqual(next(a.amount for a in ordinary if a.kind == 'buy'), 2.5)
        self.assertEqual(next(a.amount for a in reinforced if a.kind == 'buy'), 4.)
        w.trace.close()

    def test_power_message_does_not_force_baseline_relocation(self):
        from dataclasses import replace
        from regional_sim.policy import ScriptedPolicy
        import random
        w = world(n=100)
        o = replace(w.obs(0), time=12., home_outage_hours=0,
                    current_claim_exposures={'power_interruption':3},
                    relocation_preference_threshold_hours=2., power_at_home=True)
        acts = ScriptedPolicy().decide(o, random.Random(5))
        self.assertNotIn('relocate', [a.kind for a in acts])
        w.trace.close()

    def test_policy_can_cancel_a_transport_deferred_move(self):
        w = world(n=100)
        w.t = 10.
        i=0
        aid=5000
        w.actions[aid]=(i,Action('relocate'),'requested')
        w.action(aid)
        self.assertTrue(w.relocation_pending[i])
        self.assertIn(aid, w.obs(i).pending_action_ids)
        w.actions[aid]=(i,Action('relocate'),'deferred')
        w.actions[aid+1]=(i,Action('cancel',reference=aid),'requested')
        w.action(aid+1)
        self.assertFalse(w.relocation_pending[i])
        w.relocation_depart(i)
        self.assertTrue(w.household_local[i])
        w.trace.close()

    def test_actual_delivered_social_claims_change_purchase_intention(self):
        from dataclasses import replace
        from regional_sim.policy import ScriptedPolicy
        import random
        w = world(n=100)
        i = 0
        w.attention[i] = 1.
        w.internet[i] = True
        w.comm_up[:] = True
        w.threshold[i] = 2
        before = replace(w.obs(i), time=10., groceries=0., grocery_need_daily=1.,
                         balance_cents=50000, cash_cents=0, availability_enabled=False,
                         pending_grocery_purchase=False)
        for mid, origin in ((1, 19), (2, 20)):
            w.messages[mid] = dict(id=mid, sender=origin, origin=origin, created=8.,
                                   claim='retail_stockout', evidence='firsthand', ttl=0, recipients=set())
            w.deliver((mid,i,'close'))
        after = replace(w.obs(i), time=10., groceries=0., grocery_need_daily=1.,
                        balance_cents=50000, cash_cents=0, availability_enabled=False,
                        pending_grocery_purchase=False)
        self.assertEqual(after.current_claim_exposures.get('retail_stockout'),2)
        b=ScriptedPolicy().decide(before,random.Random(7));a=ScriptedPolicy().decide(after,random.Random(7))
        self.assertEqual(next(x.amount for x in b if x.kind=='buy'),2.5)
        self.assertEqual(next(x.amount for x in a if x.kind=='buy'),4.)
        w.trace.close()

    def test_daily_drops_messages_older_than_two_days(self):
        w = world(n=80, days=1)
        w.t = 72.
        w.messages[1] = dict(id=1, sender=0, origin=0, created=0., claim="old", evidence="firsthand", ttl=0, recipients=set())
        w.messages[2] = dict(id=2, sender=0, origin=0, created=50., claim="recent", evidence="firsthand", ttl=0, recipients=set())
        w.daily()
        self.assertNotIn(1, w.messages)
        self.assertIn(2, w.messages)
        w.trace.close()

    def test_accepted_relocation_survives_daily_cleanup(self):
        w = world(n=100)
        i, aid = 0, 9000
        w.t = 23.95
        w.actions[aid] = (i, Action('relocate'), 'requested')
        w.action(aid)
        self.assertEqual(w.actions[aid][2], 'accepted')
        w.t = 24.
        w.daily()
        self.assertEqual(w.actions[aid][2], 'accepted')
        self.assertTrue(w.relocation_pending[i])
        w.trace.close()

import unittest
from dataclasses import replace
from regional_sim import Config, World
from regional_sim.policy import ScriptedPolicy, Action, MessageView
from regional_sim.scenarios import Shock


def world(**kw):
    return World(Config(households=360, days=3, seed=32, trace='', **kw))


class TravelInformationTests(unittest.TestCase):
    def test_no_omniscient_advisory_before_delivery(self):
        w = world()
        w.shock(Shock(2, 'road_closure', 0, 0, 24))
        self.assertFalse(w.obs(0).road_alert)
        self.assertFalse(w.obs(1).road_alert)
        w.trace.close()

    def test_only_valid_notice_or_real_delay_can_be_reported(self):
        w=world()
        w.t=6
        w.actions[900]=(0,Action('send',payload='road_delay'),'requested')
        w.action(900)
        self.assertEqual(w.actions[900][2], 'rejected')
        w.last_road_delay[0]=5
        w.actions[901]=(0,Action('send',payload='road_delay'),'requested')
        w.comm_up[:]=True; w.internet[0]=True
        w.action(901)
        self.assertNotIn(901,w.actions)
        self.assertEqual(w.messages[1]['claim'], 'road_delay:0')
        w.trace.close()

    def test_peer_report_gives_information_not_world_state(self):
        w=world(); w.t=6; w.internet[12]=True; w.attention[12]=1; w.comm_up[:]=True
        w.messages[1]=dict(id=1,sender=0,origin=0,created=5,claim='road_delay:0',evidence='firsthand',ttl=0,recipients=set())
        w.deliver((1,12,'close'))
        self.assertTrue(w.obs(12).road_alert)
        self.assertFalse(w.obs(13).road_alert)
        w.trace.close()

    def test_route_options_have_distinct_actual_capacity(self):
        w=world();w.shock(Shock(0,'road_closure',0,0,24));w.t=6
        self.assertFalse(w.road_trip(0,1,'commute_arrival',(0,0,0),'main'))
        self.assertTrue(w.road_trip(0,1,'commute_arrival',(0,0,0),'alternate'))
        self.assertIn((6,0,'alternate'),w.road_used)
        w.trace.close()

    def test_regionwide_zero_roads_prevents_alternative_route(self):
        w=world();w.shock(Shock(0,'road',-1,0,24));w.t=6
        self.assertFalse(w.road_trip(0,1,'commute_arrival',(0,0,0),'alternate'))
        w.trace.close()

    def test_information_changes_commute_but_not_uninformed_control(self):
        w=world(); w.t=7
        w.employed[0]=True; w.remote[0]=False; w.pref_route_change[0]=True;w.pref_time_shift[0]=True
        o=w.obs(0)
        p=ScriptedPolicy()
        import random
        x=p.decide(replace(o,road_alert=False,scheduled_shift=True),random.Random(1))
        y=p.decide(replace(o,road_alert=True,scheduled_shift=True),random.Random(1))
        ax=[a for a in x if a.kind=='commute'][0]
        ay=[a for a in y if a.kind=='commute'][0]
        self.assertEqual(ax.payload,'main')
        self.assertEqual(ay.payload,'alternate')
        self.assertGreater(ay.delay_hours-ax.delay_hours,2.49)
        w.trace.close()

    def test_peer_plan_coordinates_route_only_not_willingness_to_leave(self):
        w=world();w.t=24
        import random
        p=ScriptedPolicy()
        o=w.obs(0)
        props=dict(locally_present=True,availability_enabled=True,home_outage_hours=24,
                   relocation_preference_threshold_hours=12.,road_alert=False,peer_relocation_route='alternate')
        actions=p.decide(replace(o,**props),random.Random(3))
        self.assertEqual([a for a in actions if a.kind=='relocate'][0].target,1)
        actions=p.decide(replace(o,**dict(props,relocation_preference_threshold_hours=100)),random.Random(3))
        self.assertFalse(any(a.kind=='relocate' for a in actions))
        w.trace.close()

    def test_published_marginal_preferences_within_sampling_error(self):
        w=World(Config(households=10000,days=1,seed=49,trace=''))
        self.assertLess(abs(w.pref_route_change.mean()-.44),.02)
        self.assertLess(abs(w.pref_time_shift.mean()-.48),.02)
        w.trace.close()

if __name__=='__main__': unittest.main()

class RequestRevisionTests(unittest.TestCase):
    def test_deferred_commute_can_be_cancelled_and_replanned(self):
        w=world();w.t=7;w.employed[0]=True;w.remote[0]=False
        w.pref_route_change[0]=True
        w.shock(Shock(7,'road_closure',0,0,24))
        w.actions[200]=(0,Action('commute',payload='main'),'requested')
        w.commute_action_id[0]=200
        w.action(200)
        self.assertEqual(w.actions[200][2],'deferred')
        w.road_alert_until[0]=9
        from random import Random
        choices=ScriptedPolicy().decide(w.obs(0),Random(1))
        self.assertTrue(any(a.kind=='cancel' and a.reference==200 for a in choices))
        self.assertTrue(any(a.kind=='commute' and a.payload=='alternate' for a in choices))
        w.actions[201]=(0,Action('cancel',reference=200),'requested')
        w.action(201)
        self.assertEqual(w.actions[200][2],'cancelled')
        w.trace.close()

    def test_peer_relocation_plan_is_authentic_and_zone_local(self):
        w=world();w.t=6;w.internet[12]=True;w.attention[12]=1;w.comm_up[:]=True
        w.messages[1]=dict(id=1,sender=0,origin=0,created=5,
                           claim='relocation_intent:0:alternate',evidence='firsthand_intention',ttl=0,recipients=set())
        w.deliver((1,12,'close'))
        self.assertEqual(w.obs(12).peer_relocation_route,'alternate')
        self.assertEqual(w.obs(13).peer_relocation_route,'')
        w.trace.close()

class TravelRevisionTests(unittest.TestCase):
    def test_pending_relocation_changes_route_only_by_policy(self):
        w=world();w.t=24
        w.hh_outage_hours[0]=24
        w.pref_route_change[0]=True
        w.relocation_pending[0]=True
        w.relocation_action_id[0]=901
        w.actions[901]=(0,Action('relocate',payload='while_unpowered',target=-1),'deferred')
        w.road_alert_until[0]=30
        from random import Random
        moves=ScriptedPolicy().decide(w.obs(0),Random(3))
        self.assertTrue(any(a.kind=='cancel' and a.reference==901 for a in moves))
        self.assertTrue(any(a.kind=='relocate' and a.target==1 for a in moves))
        w.trace.close()

    def test_forwarded_plan_is_not_misrepresented_as_direct_contact(self):
        w=world();w.t=6;w.internet[12]=True;w.attention[12]=1;w.comm_up[:]=True
        w.messages[1]=dict(id=1,sender=24,origin=0,created=5,
                           claim='relocation_intent:0:alternate',evidence='firsthand_intention',ttl=1,recipients=set())
        w.deliver((1,12,'close'))
        self.assertEqual(w.obs(12).peer_relocation_route,'')
        w.trace.close()

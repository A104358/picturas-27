"""Fail-closed maintenance tests. No Docker mutation, host-clock or real PKI change."""
import argparse
import importlib.util
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('picturas_maintenance',ROOT/'ops/maintenance.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def participant(running=True):
    return {'Id':'FIXTURE','Config':{'Labels':{'com.docker.compose.service':'video_tool'}},
      'State':{'Running':running,'Pid':123 if running else 0,'StartedAt':'FIXTURE','ExitCode':0},
      'Image':'FIXTURE-image','HostConfig':{'RestartPolicy':{'Name':'on-failure'}},
      'NetworkSettings':{'Networks':{}},'Mounts':[]}

class MaintenanceTests(unittest.TestCase):
    def fixture(self,mode='compromise'):
        op=m.Maintenance.__new__(m.Maintenance)
        op.args=argparse.Namespace(mode=mode,project='picturas-test',fixture_proof=None,browser_proof=None)
        op.state={'mode':mode,'operation':'FIXTURE','command_monotonic_ns':time.monotonic_ns(),
          't_comando':'FIXTURE-original-command','t_isolado':None,'interrupted_work':mode=='compromise'}
        op.begin=lambda:None;op.close_admissions=lambda:None;op.phases=[]
        op.save=lambda phase: (op.phases.append(phase),op.state.update(phase=phase))
        return op

    def test_compromise_never_waits_for_work_and_observes_cut_after_termination(self):
        op=self.fixture();alive=[True];calls=[]
        op.containers=lambda:[participant(alive[0])]
        op.planned_busy=lambda:self.fail('compromise waited for a job')
        def command(args,**kwargs):
            calls.append(args)
            if args[1]=='kill':alive[0]=False
        def probe(action):
            self.assertFalse(alive[0]);self.assertEqual(action,'cut');return {'all_closed':True}
        op.probe=probe
        with patch.object(m,'command',command):op.isolate()
        self.assertEqual(calls[0][1:3],['update','--restart=no'])
        self.assertEqual(calls[1][1],'kill')
        self.assertEqual(op.state['phase'],'isolated');self.assertIsNotNone(op.state['t_isolado'])

    def test_no_cut_evidence_never_sets_isolated_timestamp(self):
        for evidence in (False,None):
            op=self.fixture();op.containers=lambda:[participant(False)]
            def probe(_):
                if evidence is None:raise RuntimeError('observer_unavailable')
                return {'all_closed':False}
            op.probe=probe
            with self.assertRaises(RuntimeError):op.isolate()
            self.assertIsNone(op.state['t_isolado']);self.assertEqual(op.phases[-1],'isolation_incomplete')

    def test_over_30_seconds_is_failure_and_original_clock_is_not_reset(self):
        op=self.fixture();op.state['command_monotonic_ns']-=31_000_000_000
        original=op.state['command_monotonic_ns'];op.containers=lambda:[participant(False)]
        op.probe=lambda _: {'all_closed':True};op.isolate();op.isolate()
        self.assertFalse(op.state['isolation_target_met'])
        self.assertEqual(op.state['phase'],'isolated_over_30s')
        self.assertEqual(op.state['command_monotonic_ns'],original)

    def test_10_second_target_is_distinct_from_30_second_limit(self):
        op=self.fixture();op.state['command_monotonic_ns']-=11_000_000_000
        op.containers=lambda:[participant(False)];op.probe=lambda _: {'all_closed':True}
        op.isolate()
        self.assertTrue(op.state['isolation_limit_met']);self.assertFalse(op.state['isolation_target_met'])
        self.assertEqual(op.state['phase'],'isolated')

    def test_durable_admission_marker_can_cancel_only_its_unchanged_deferral(self):
        with tempfile.TemporaryDirectory() as directory:
            op=self.fixture('planned');op.gate=Path(directory)/'gate/admissions-closed'
            op.close_admissions=lambda:m.Maintenance.close_admissions(op)
            op.close_admissions()
            self.assertEqual(__import__('json').loads(op.gate.read_text()),op.state['operation'])
            self.assertEqual(op.gate.stat().st_mode & 0o777,0o600)
            op.containers=lambda:[participant()];op.manifest=lambda:{}
            op.state.update(phase='deferred_busy',participants_before=op.participants(op.containers()),certificates_before={})
            op.cancel();self.assertFalse(op.gate.exists());self.assertEqual(op.state['phase'],'cancelled')

    def test_planned_busy_defers_without_stopping_any_participant(self):
        op=self.fixture('planned');op.planned_busy=lambda:True
        with patch.object(m,'command',side_effect=AssertionError('must not stop')):
            with self.assertRaisesRegex(RuntimeError,'deferred_busy'):op.isolate()
        self.assertEqual(op.phases[-1],'deferred_busy');self.assertIsNone(op.state['t_isolado'])

    def test_business_interruption_cannot_use_technical_fixture_exception(self):
        op=self.fixture();op.root=Path('/tmp');op.args.fixture_proof='/tmp/does-not-matter'
        with self.assertRaisesRegex(RuntimeError,'forbidden_for_normal'):op.fixture_reconciliation()
        op.args.fixture_proof=None
        with self.assertRaisesRegex(RuntimeError,'requires_reconciliation'):op.start_for_verification()

    def test_retirement_does_not_start_participants_without_browser_proof(self):
        op=self.fixture('planned');op.state.update(ca_changed=True,t_isolado='FIXTURE',phase='pki_activated_isolated')
        op.start_for_verification=lambda:self.fail('started before browser trust withdrawal')
        with self.assertRaisesRegex(RuntimeError,'browser_trust_withdrawal_proof_required'):op.reopen()

    def test_partial_start_is_stopped_and_keeps_gate_closed(self):
        op=self.fixture();op.state['t_isolado']='FIXTURE';alive=[True];op.containers=lambda:[participant(alive[0])]
        calls=[];op.close_admissions=lambda:calls.append('closed')
        def command(args,**kwargs):
            calls.append(args[1])
            if args[1]=='kill':alive[0]=False
        with patch.object(m,'command',command):op.stop_partial('restart_failed')
        self.assertEqual(calls,['update','kill','closed']);self.assertEqual(op.phases[-1],'failed_isolated')
        self.assertEqual(op.state['failure'],'restart_failed')

if __name__=='__main__':unittest.main(verbosity=2)

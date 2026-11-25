import argparse,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('maintenance_seal',ROOT/'ops/maintenance.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class SealTests(unittest.TestCase):
 def fixture(self,root):
  op=m.Maintenance.__new__(m.Maintenance)
  op.base=root;op.args=argparse.Namespace(project='picturas-test',fixture_proof=None)
  op.state={'operation':'a'*32,'interrupted_work':True}
  case=root/op.state['operation']/'reconciliation';case.mkdir(parents=True)
  report=case/'report.json';m.durable(report,{'sealed':True,'unknown':0,'cases':[{'state':'lost'}]})
  m.durable(case/'seal.json',{'operation':op.state['operation'],'project':'picturas-test','complete':True,'pending':0,
    'files':{'report.json':hashlib.sha256(report.read_bytes()).hexdigest()}})
  op.state['reconciliation']={'type':'business_runs','operation':op.state['operation'],'case':str(case),
   'seal_sha256':hashlib.sha256((case/'seal.json').read_bytes()).hexdigest()}
  op.gate=root/'gate';m.durable(op.gate,op.state['operation']);op.containers=lambda:[]
  return op,case
 def test_valid_seal_reaches_pki_checks_before_any_consumer_start(self):
  with tempfile.TemporaryDirectory() as temp:
   op,_=self.fixture(Path(temp))
   with patch.object(m,'command',side_effect=RuntimeError('valid_seal_reached_pki')) as calls:
    with self.assertRaisesRegex(RuntimeError,'reached_pki'):op.start_for_verification()
   self.assertEqual(Path(calls.call_args.args[0][0]).name,'pki.sh')
 def test_changed_bytes_permissions_or_operation_never_start_consumers(self):
  for change in ('bytes','permissions','operation'):
   with tempfile.TemporaryDirectory() as temp:
    op,case=self.fixture(Path(temp))
    if change=='bytes':(case/'report.json').write_text('{}')
    elif change=='permissions':(case/'report.json').chmod(0o644)
    else:op.state['reconciliation']['operation']='b'*32
    with patch.object(m,'command',side_effect=AssertionError('consumer command forbidden')):
     with self.assertRaisesRegex(RuntimeError,'reconciliation'):op.start_for_verification()
 def test_unsealed_or_pending_case_cannot_be_used_as_proof(self):
  with tempfile.TemporaryDirectory() as temp:
   op,case=self.fixture(Path(temp));report={'sealed':False,'unknown':1,'cases':[{'state':'indeterminate'}]}
   m.durable(case/'report.json',report)
   seal=json.loads((case/'seal.json').read_text());seal['files']['report.json']=hashlib.sha256((case/'report.json').read_bytes()).hexdigest()
   m.durable(case/'seal.json',seal);op.state['reconciliation']['seal_sha256']=hashlib.sha256((case/'seal.json').read_bytes()).hexdigest()
   with patch.object(m,'command',side_effect=AssertionError('consumer command forbidden')):
    with self.assertRaisesRegex(RuntimeError,'pending'):op.start_for_verification()
if __name__=='__main__':unittest.main()

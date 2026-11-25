import importlib.util,sys,unittest
from pathlib import Path
from types import SimpleNamespace
OPS=Path(__file__).resolve().parents[3]/'ops'
sys.path.insert(0,str(OPS))
spec=importlib.util.spec_from_file_location('inventory_policy',OPS/'reconcile.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class InventoryTests(unittest.TestCase):
 def fixture(self):
  native=m.Native.__new__(m.Native)
  native.projects=SimpleNamespace(uploads=SimpleNamespace(count_documents=lambda _:0))
  return native,{'projects':[{'_id':'p','activeToken':0,'committedToken':0}],
   'runs':[],'all_runs':[],'processes':[],'accounts':[],'results':[],'artifacts':[],'objects':{},'queues':[]}
 def test_legacy_debit_without_process_or_receipt_is_not_silently_cleared(self):
  native,snapshot=self.fixture();snapshot['projects'][0].update(activeToken=7,committedToken=6,pendingAdvancedOps=4)
  self.assertEqual(native.classify(snapshot)[1],1)
 def test_legacy_basic_run_without_process_metadata_is_still_ambiguous(self):
  native,snapshot=self.fixture();snapshot['projects'][0].update(activeToken=7,committedToken=6)
  self.assertEqual(native.classify(snapshot)[1],1)
 def test_deliberately_fenced_known_run_does_not_create_a_phantom_new_execution(self):
  native,snapshot=self.fixture();snapshot['projects'][0].update(activeToken=8,committedToken=6)
  snapshot['all_runs']=[{'_id':'run','project_id':'p','token':7,'invalidated':True,'phase':'reconciled'}]
  self.assertEqual(native.classify(snapshot)[1],0)
 def test_orphan_objects_and_directories_prevent_a_clean_inventory(self):
  native,snapshot=self.fixture();snapshot['orphan_objects']=[{'key':'unknown'}];snapshot['orphan_directories']=['unknown']
  self.assertEqual(native.classify(snapshot)[1],2)
 def test_pending_uploads_and_unattributed_processes_are_never_replayed_or_erased(self):
  native,snapshot=self.fixture();native.projects.uploads.count_documents=lambda _:1
  snapshot['processes']=[{'msg_id':'unknown'}]
  self.assertEqual(native.classify(snapshot)[1],2);self.assertEqual(len(snapshot['processes']),1)
 def test_a_processing_pointer_without_a_run_requires_investigation(self):
  native,snapshot=self.fixture();snapshot['projects'][0]['processingRunId']='missing'
  self.assertEqual(native.classify(snapshot)[1],1)
if __name__=='__main__':unittest.main()

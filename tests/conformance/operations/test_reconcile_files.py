import importlib.util,tempfile,unittest,uuid
from pathlib import Path
spec=importlib.util.spec_from_file_location('files',Path(__file__).resolve().parents[3]/'ops/reconcile_files.py')
files=importlib.util.module_from_spec(spec);spec.loader.exec_module(files)

class FileTests(unittest.TestCase):
 def fixture(self,root):
  run=str(uuid.uuid4());directory=root/'runs'/run;directory.mkdir(parents=True)
  (directory/'partial.bin').write_bytes(b'known partial output')
  return directory,{'operation':'a'*32,'runs':[{'run_id':run,'manifest':files.manifest(directory)}]}
 def test_crash_after_rename_before_journal_is_recovered_without_second_move(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);directory,plan=self.fixture(root)
   first=files.quarantine(plan,root);self.assertFalse(directory.exists())
   self.assertEqual(first,files.quarantine(plan,root))
 def test_changed_output_or_missing_without_quarantine_proof_is_not_deleted(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);directory,plan=self.fixture(root)
   (directory/'partial.bin').write_bytes(b'changed')
   with self.assertRaisesRegex(RuntimeError,'changed'):files.quarantine(plan,root)
   self.assertTrue(directory.exists())
   (directory/'partial.bin').unlink();directory.rmdir()
   with self.assertRaisesRegex(RuntimeError,'missing'):files.quarantine(plan,root)
 def test_symlinks_and_run_traversal_are_refused(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);directory,plan=self.fixture(root)
   (directory/'escape').symlink_to(root)
   with self.assertRaisesRegex(RuntimeError,'symlink'):files.manifest(directory)
   plan['runs'][0]['run_id']='../other'
   with self.assertRaisesRegex(RuntimeError,'invalid_run'):files.quarantine(plan,root)
 def test_originally_absent_directory_is_a_verified_noop(self):
  with tempfile.TemporaryDirectory() as temp:
   plan={'operation':'a'*32,'runs':[{'run_id':str(uuid.uuid4()),'manifest':None}]}
   self.assertTrue(files.quarantine(plan,Path(temp))['runs'][0]['quarantined'])
 def test_symlinked_quarantine_parent_never_moves_original_files(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);directory,plan=self.fixture(root)
   (root/'quarantine').symlink_to(root/'runs')
   with self.assertRaisesRegex(RuntimeError,'symlink'):files.quarantine(plan,root)
   self.assertTrue((directory/'partial.bin').exists())

if __name__=='__main__':unittest.main()

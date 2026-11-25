import importlib.util,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('maintenance_lock',ROOT/'ops/maintenance.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class LockTests(unittest.TestCase):
 def test_kernel_releases_shared_maintenance_lock_after_process_is_killed(self):
  with tempfile.TemporaryDirectory() as temp:
   code="import sys,time;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from maintenance import acquire_lock;fd=acquire_lock(Path(sys.argv[2]));print('READY',flush=True);time.sleep(30)"
   child=subprocess.Popen([sys.executable,'-c',code,str(ROOT/'ops'),temp],stdout=subprocess.PIPE)
   try:
    self.assertEqual(child.stdout.readline(),b'READY\n')
    with self.assertRaisesRegex(RuntimeError,'locked'):m.acquire_lock(Path(temp))
    child.kill();child.wait(timeout=5)
    fd=m.acquire_lock(Path(temp));m.release_lock(fd)
    self.assertTrue((Path(temp)/'operation.lock').exists())
   finally:
    if child.poll() is None:child.kill();child.wait(timeout=5)
    child.stdout.close()
if __name__=='__main__':unittest.main()

"""Preserve this WIP while pulling the shared branch. Never commits or pushes."""
import hashlib,json,os,stat,subprocess,sys,uuid
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
ROOT=Path.home()/'picturas-secrets'
OUT=REPO/'tests/conformance/results/2026-11-24'
ENV=dict(os.environ,PICTURAS_SECRETS_DIR=str(ROOT),GIT_TERMINAL_PROMPT='0')
def git(*args,allowed=False):
 p=subprocess.run(['git',*args],cwd=REPO,env=ENV,capture_output=True)
 if p.returncode and not allowed:raise RuntimeError('git_'+args[0]+'_failed')
 return p
def value(*args):return git(*args).stdout.decode().strip()
def durable(file,data):
 temp=file.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2));temp.chmod(0o600);os.replace(temp,file)
def fingerprint(file):
 return {'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'mode':stat.S_IMODE(file.stat().st_mode)}
assert value('branch','--show-current')=='fase2-refactor'
assert not git('diff','--cached','--name-only').stdout,'unexpected_staged_changes'
resume=len(sys.argv)>1 and sys.argv[1]=='--resume'
if resume:
 state=json.loads((ROOT/'b11-sync-state.json').read_text());before=state['files_before']
 assert value('rev-parse','HEAD')==state['head_after'],'branch_changed_during_restore'
 untracked=set(git('ls-tree','-r','--name-only',state['stash_oid']+'^3').stdout.decode().splitlines())
else:
 paths=set(git('diff','--name-only','-z').stdout.decode().split('\0')+
  git('ls-files','--others','--exclude-standard','-z').stdout.decode().split('\0'))-{''}
 before={p:fingerprint(REPO/p) for p in paths if (REPO/p).is_file()}
 untracked=set(git('ls-files','--others','--exclude-standard','-z').stdout.decode().split('\0'))-{''}
 state={'head_before':value('rev-parse','HEAD'),'files_before':before,'complete':False}
 durable(ROOT/'b11-sync-state.json',state)
 git('stash','push','--include-untracked','--message','codex-b11-sync-'+uuid.uuid4().hex)
 state['stash_oid']=value('rev-parse','refs/stash');durable(ROOT/'b11-sync-state.json',state)
 pull=git('pull','--rebase','origin','fase2-refactor',allowed=True)
 durable(ROOT/'b11-sync-pull-private.json',{'stdout':pull.stdout.decode(errors='replace'),'stderr':pull.stderr.decode(errors='replace')})
 if pull.returncode:raise RuntimeError('pull_failed_wip_preserved_in_private_checkpoint')
 state['head_after']=value('rev-parse','HEAD');durable(ROOT/'b11-sync-state.json',state)
 restored=git('stash','apply','--index',state['stash_oid'],allowed=True)
 if restored.returncode:
  durable(ROOT/'b11-sync-apply-private.json',{'stdout':restored.stdout.decode(errors='replace'),'stderr':restored.stderr.decode(errors='replace')})
  raise RuntimeError('restore_requires_conflict_resolution_stash_preserved')
assert not git('diff','--name-only','--diff-filter=U').stdout,'unresolved_conflict'
for name in untracked:
 if name in before:
  file=REPO/name
  intentional={'tests/conformance/operations/sync-branch.py','tests/conformance/operations/run-b11.sh'} if resume else set()
  assert file.exists() and (fingerprint(file)['sha256']==before[name]['sha256'] or name in intentional),'untracked_file_not_restored'
  # Git preserves the executable bit, not all POSIX permission bits. Restore the
  # original private permissions of generated reports after verifying their bytes.
  file.chmod(before[name]['mode'])
changed=[name for name,original in before.items() if (REPO/name).exists() and fingerprint(REPO/name)!=original]
state.update(complete=True,merged_wip_files=changed);durable(ROOT/'b11-sync-state.json',state)
refs=value('stash','list','--format=%gd %H').splitlines()
ref=next(line.split()[0] for line in refs if line.split()[1]==state['stash_oid'])
git('stash','drop',ref)  # Only this exact, already-restored stash; never an older human stash.
report={k:state[k] for k in ('head_before','head_after','complete','merged_wip_files')}
report['remote_changed']=state['head_before']!=state['head_after'];report['conflicts']=False
report['own_stash_restored_and_removed']=True
if resume:
 report['sync_helper_edits']=[p for p in changed if p in intentional]
 report['merged_wip_files']=[p for p in changed if p not in intentional]
durable(OUT/'B11-sync.json',report)
print(json.dumps({'before':state['head_before'][:7],'after':state['head_after'][:7],
 'conflicts':False,'merged_wip_files':changed,'own_stash_restored_and_removed':True}))

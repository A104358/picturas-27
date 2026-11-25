"""Contained filesystem quarantine. Runs without network or installation secrets."""
import hashlib,json,os,re,sys
from pathlib import Path

def manifest(path):
    if path.is_symlink():raise RuntimeError('symlink_in_run_directory')
    if not path.exists():return None
    result=[]
    for file in sorted(path.rglob('*')):
        if file.is_symlink():raise RuntimeError('symlink_in_run_directory')
        if file.is_file():
            digest=hashlib.sha256()
            with file.open('rb') as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
            result.append({'path':str(file.relative_to(path)),'size':file.stat().st_size,'sha256':digest.hexdigest()})
    return result

def quarantine(plan,images=Path('/images')):
    if not re.fullmatch('[a-f0-9]{32}',plan['operation']):raise RuntimeError('invalid_operation')
    for directory in (images,images/'runs',images/'quarantine',images/'quarantine'/plan['operation']):
        if directory.is_symlink():raise RuntimeError('symlink_in_quarantine_parent')
    results=[]
    for item in plan['runs']:
        run=item['run_id']
        if not re.fullmatch('[a-f0-9-]{36}',run):raise RuntimeError('invalid_run')
        source=images/'runs'/run
        target=images/'quarantine'/plan['operation']/run
        before=manifest(source);after=manifest(target)
        if before is not None:
            if before!=item['manifest'] or after is not None:raise RuntimeError('run_files_changed_or_target_exists')
            target.parent.mkdir(parents=True,exist_ok=True)
            source.rename(target)
            for parent in (target.parent,source.parent):
                fd=os.open(parent,os.O_RDONLY)
                try:os.fsync(fd)
                finally:os.close(fd)
        elif item['manifest'] is not None and after!=item['manifest']:
            raise RuntimeError('run_files_missing_without_quarantine_evidence')
        results.append({'run_id':run,'quarantined':True,'manifest':manifest(target)})
    return {'operation':plan['operation'],'runs':results}

if __name__=='__main__':
    print(json.dumps(quarantine(json.loads(Path('/case/local-plan.json').read_text()))))

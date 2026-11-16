"""Collect source/configuration counts and public certificate metadata, never secrets."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

import yaml

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]


def run(*command):
    return subprocess.check_output(command,cwd=ROOT,text=True).strip()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=BASE/'static-inventory-2026-11-16.json')
    args=parser.parse_args()
    services=yaml.safe_load((ROOT/'docker-compose.yaml').read_text())['services']
    tracked=run('git','ls-files').splitlines()
    folders=('apiGateway/','projects/','users/','subscriptions/','imageStorageService/','wsGateway/','frontend/','Tools/')
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in tracked
            if name.startswith(folders) and Path(name).suffix in ('.js','.ts','.tsx','.py','.json')
            and 'lock' not in Path(name).name and '/tests/' not in name and '/certs/' not in name}
    keys=[];certificates=[];disabled=[]
    for name in tracked:
        path=ROOT/name
        if path.is_file() and path.suffix in ('.key','.pem','.crt'):
            content=path.read_text(errors='replace')
            if re.search('-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----',content):keys.append(name)
            if '-----BEGIN CERTIFICATE-----' in content:
                validity=subprocess.run(['openssl','x509','-in',str(path),'-noout','-startdate','-enddate'],capture_output=True,text=True)
                if validity.returncode==0:
                    expired=subprocess.run(['openssl','x509','-in',str(path),'-noout','-checkend','0'],capture_output=True).returncode!=0
                    certificates.append({'file':name,'validity':validity.stdout.strip().splitlines(),'expired_now':expired})
    for name in hashes:
        if Path(name).suffix in ('.js','.ts','.tsx'):
            for number,line in enumerate((ROOT/name).read_text().splitlines(),1):
                if re.search(r'rejectUnauthorized\s*:\s*false',line):disabled.append({'file':name,'line':number})
    ports=[{'service':name,'bindings':[str(v) for v in config.get('ports',[])]} for name,config in services.items() if config.get('ports')]
    report={'recorded_at':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'source_commit':run('git','rev-parse','HEAD'),
            'application_diff_from_66bc6f9':run('git','diff','66bc6f9','HEAD','--name-only','--',*[s.rstrip('/') for s in folders],'docker-compose.yaml','rabbitMQ').splitlines(),
            'method':'Read tracked source/configuration and public certificate metadata only; no services started and no secret values emitted.',
            'services':len(services),'published_service_count':len(ports),'published_binding_count':sum(len(p['bindings']) for p in ports),
            'published_bindings':ports,'healthcheck_count':sum(bool(s.get('healthcheck')) for s in services.values()),
            'explicit_memory_limit_count':sum(bool(s.get('mem_limit') or s.get('deploy',{}).get('resources',{}).get('limits',{}).get('memory')) for s in services.values()),
            'private_key_file_paths':keys,'certificate_public_validity':certificates,
            'tls_verification_disabled':disabled,'source_hashes':hashes}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'services':len(services),'published_bindings':report['published_binding_count'],
                      'healthchecks':report['healthcheck_count'],'memory_limits':report['explicit_memory_limit_count'],
                      'private_key_files':len(keys),'expired_certificates':sum(c['expired_now'] for c in certificates),
                      'tls_verification_disabled_sites':len(disabled)}))


if __name__=='__main__':
    main()

"""Control one kill/restart of the explicitly named disposable video worker."""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import selectors
import subprocess
import time

BASE = Path(__file__).resolve().parent
WORKER = 'picturas-quality-20261114-video_tool-1'
PROJECT = 'picturas-quality-20261114'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE/'live-recovery-2026-11-14.json')
    args = parser.parse_args()
    label = subprocess.check_output(['docker', 'inspect', WORKER, '--format', '{{index .Config.Labels "com.docker.compose.project"}}'], text=True).strip()
    if label != PROJECT:
        raise RuntimeError('Refusing to interrupt a worker outside the experiment')
    command = ['docker','run','--rm','-i','--network',PROJECT+'_elk','--cpus','1','--memory','512m',
               '--env-file','/tmp/'+PROJECT+'/probe.env','--entrypoint','node',
               'sha256:5c21e207f6ad56fa1764b5d7b62bee8cd7ba94f8ef7565ab4fe4464e3bf3a950','-']
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    process.stdin.write((BASE/'live-recovery-probe.cjs').read_text())
    process.stdin.close()
    control = {'recorded_at':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'worker':WORKER, 'project_label_verified':True, 'interrupted':False}
    selector = selectors.DefaultSelector()
    selector.register(process.stderr, selectors.EVENT_READ)
    deadline = time.monotonic()+120
    while process.poll() is None and time.monotonic()<deadline:
        if not selector.select(timeout=0.5):
            continue
        line=process.stderr.readline().strip()
        if line == 'RECOVERY_READY':
            control['kill_started_at_ms']=time.time()*1000
            subprocess.run(['docker','kill','--signal','KILL',WORKER],check=True,capture_output=True,text=True)
            control['kill_completed_at_ms']=time.time()*1000
            time.sleep(0.5)
            code='const a=require("amqplib");(async()=>{const c=await a.connect({hostname:process.env.RABBITMQ_HOST,port:Number(process.env.RABBITMQ_PORT),username:process.env.RABBITMQ_USER,password:process.env.RABBITMQ_PASS});const h=await c.createChannel();const q=await h.checkQueue("video_queue");console.log(JSON.stringify({ready:q.messageCount,consumers:q.consumerCount}));await c.close();})().catch(()=>process.exitCode=1);'
            queue=subprocess.run(['docker','exec',PROJECT+'-projects-1','node','-e',code],capture_output=True,text=True)
            control['queue_before_restart']=json.loads(queue.stdout) if queue.returncode==0 else {'observation_failed':True}
            subprocess.run(['docker','start',WORKER],check=True,capture_output=True,text=True)
            control['restart_completed_at_ms']=time.time()*1000
            control['interrupted']=True
            print('Interrupted and restarted only the disposable video worker.',flush=True)
            break
    if not control['interrupted']:
        print('Interruption point not observed; no worker was killed.',flush=True)
    stdout=process.stdout.read()
    process.wait(timeout=240)
    result=json.loads(stdout)
    args.output.write_text(json.dumps({'controller':control,'probe':result},indent=2)+'\n')
    print(json.dumps({'interrupted':control['interrupted'],'completed':result.get('completed'),'persisted':result.get('persisted'),'failures':result.get('failures')},indent=2))
    if process.returncode or not control['interrupted']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

"""Derive metrics from the isolated load generator and raw resource samples."""
import gzip
import argparse
import json
from pathlib import Path
import statistics

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api', type=Path, default=BASE/'live-api-isolated-2026-11-14.json')
    parser.add_argument('--resources', type=Path, default=BASE/'live-resources-isolated-2026-11-14.jsonl.gz')
    parser.add_argument('--output', type=Path, default=BASE/'live-analysis-2026-11-14.json')
    args = parser.parse_args()
    api = json.loads(args.api.read_text())
    with gzip.open(args.resources,'rt') as stream:
        records = [json.loads(line) for line in stream]
    samples = [row for row in records if row['type']=='sample']
    intervals = [(b['unix_ms']-a['unix_ms']) for a,b in zip(samples,samples[1:])]
    report = {'source':args.api.name, 'resource_source':args.resources.name,
              'load_generator':api['load_generator'], 'failures':api['failures'],
              'sampling':{'count':len(samples),'median_interval_ms':statistics.median(intervals),'max_interval_ms':max(intervals)},
              'upload_method':'Median of 500 ms before request; maximum from request start through 500 ms after response. Warm services, no forced GC.',
              'uploads':[], 'batches':[], 'access':api['access'], 'sampled_outputs':api['outputs'],
              'limits':['Three batches and one upload per size; no population percentiles.',
                        'Cgroup memory includes cache/descendants; Node RSS sums may include shared pages.',
                        'Short memory peaks can occur between samples.',
                        'Queue residual includes publication/delivery overhead, not only queue wait.',
                        'Commit observation has polling/request overhead. Only one output per batch was downloaded and probed.']}
    for upload in api['uploads']:
        before = [s for s in samples if upload['started_at_ms']-500<=s['unix_ms']<upload['started_at_ms']]
        during = [s for s in samples if upload['started_at_ms']<=s['unix_ms']<=upload['ended_at_ms']+500]
        if not before or not during:
            raise RuntimeError('Resource samples do not cover an upload')
        row = dict(upload)
        row['baseline_samples']=len(before)
        row['observation_samples']=len(during)
        row['resources']={}
        for name in ('api_gateway','projects','img_storage','nginx'):
            row['resources'][name]={}
            fields=('memory_current_bytes',) if name=='nginx' else ('memory_current_bytes','node_rss_sum_bytes')
            for field in fields:
                baseline=statistics.median(s['services'][name][field] for s in before)
                peak=max(s['services'][name][field] for s in during)
                row['resources'][name][field]={'baseline':baseline,'peak':peak,'delta':peak-baseline}
        report['uploads'].append(row)
    responses={r['correlation_id']:r for r in api['amqp'] if r.get('correlation_id') and r.get('status')}
    for batch in api['batches']:
        row={k:v for k,v in batch.items() if k!='socket_events'}
        row['observed_videos_per_minute']=batch['output_count']*60000/batch['elapsed_ms']
        row['jobs']=[]
        requests=[r for r in api['amqp'] if r.get('project_id')==batch['project_id']]
        for request in requests:
            response=responses.get(request['message_id'])
            if response is None:
                raise RuntimeError('Missing tapped response for a video request')
            events=[e for e in batch['socket_events'] if e['event']=='video-progress' and e.get('media_id')==request['media_id']]
            timestamps=[e['unix_ms'] for e in events]
            between=[b-a for a,b in zip(timestamps,timestamps[1:])]
            row['jobs'].append({'media_id':request['media_id'],'request_observed_at_ms':request['unix_ms'],
                                'response_observed_at_ms':response['unix_ms'],'worker_processing_ms':response['worker_processing_ms'],
                                'request_to_response_ms':response['unix_ms']-request['unix_ms'],
                                'non_processing_residual_ms':response['unix_ms']-request['unix_ms']-response['worker_processing_ms'],
                                'status':response['status'],'progress_event_count':len(events),
                                'dispatch_to_first_progress_ms':timestamps[0]-batch['started_at_ms'] if timestamps else None,
                                'max_inter_progress_gap_ms':max(between) if between else None,
                                'progress_monotonic':all(b['percent']>=a['percent'] for a,b in zip(events,events[1:])),
                                'final_percent':events[-1]['percent'] if events else None})
        project_events=[e['unix_ms'] for e in batch['socket_events'] if e.get('project_id')==batch['project_id']]
        project_timeline=[batch['started_at_ms'],*project_events,batch['observed_commit_at_ms']]
        row['max_project_event_gap_with_boundaries_ms']=max(b-a for a,b in zip(project_timeline,project_timeline[1:]))
        window=[s for s in samples if batch['started_at_ms']<=s['unix_ms']<=batch['observed_commit_at_ms']]
        if len(window)>=2:
            first,last=window[0],window[-1]
            row['video_worker_mean_cpu_cores']=(last['services']['video_tool']['cpu_usage_usec']-first['services']['video_tool']['cpu_usage_usec'])/1000/(last['unix_ms']-first['unix_ms'])
            row['video_worker_peak_cgroup_bytes']=max(s['services']['video_tool']['memory_current_bytes'] for s in window)
        report['batches'].append(row)
    times=[b['elapsed_ms'] for b in report['batches']]
    report['batch_summary']={'n':len(times),'min_ms':min(times),'median_ms':statistics.median(times),'max_ms':max(times),
                             'committed_outputs':sum(b['output_count'] for b in report['batches'])}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'sampling':report['sampling'],'batches':report['batch_summary'],'failures':report['failures']},indent=2))


if __name__ == '__main__':
    main()

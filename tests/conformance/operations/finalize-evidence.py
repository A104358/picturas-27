"""Link the last EXP to the pre-change local baseline. No instrument mutation."""
import json,re
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'tests/conformance/results/2026-11-24'
names=re.findall(r'evaluation/results/(EXP-\d{8}T\d{6}Z)/report.md',(OUT/'B11-EXP-run.txt').read_text())
assert names,'missing_EXP_report'
folder=Path('evaluation/results')/names[-1]
metrics=json.loads((REPO/folder/'summary.json').read_text())['metrics']
base=json.loads((OUT/'B11-baseline.json').read_text())
for name in ('S01','S02','S03','S04','S16','S17'):
 value=metrics[name]
 assert value['admitidos']==0 and value['inconclusivos']==0 and value['controlos_ok']==value['controlos_total'],name
assert metrics['S05']['fracao']==1 and metrics['S18']['todas']==0 and metrics['S18']['loopback']==0
assert metrics['S12']['controlos_ok'] and not metrics['S12']['invalidas'] and not metrics['S12']['censurado'] and metrics['S12']['limite_superior_max_ms']<=2000
deltas={name:round(metrics['S21'][name]['mediana_ms']-base['metrics']['S21'][name]['mediana_ms'],3) for name in ('get_project','get_user')}
guard=all(delta<=5 for delta in deltas.values()) and all(metrics['S21'][name]['erros']==0 and metrics['S21'][name]['n']==20 for name in deltas)
assert guard,'S21_local_regression'
value={'baseline':base['result'],'result':str(folder),'metrics':metrics,'S21_delta_ms':deltas,
 'local_guard_passed':guard,'official_comparison':'B12 on BF host; this is EXP only'}
(OUT/'B11-final-metrics.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'result':str(folder),'S05':1,'S21_ms':{k:metrics['S21'][k]['mediana_ms'] for k in deltas},'S21_delta_ms':deltas}))

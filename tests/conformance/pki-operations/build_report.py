"""Render the pilot and complete channel inventory from public evidence only."""
import datetime as dt,json,re,statistics
from pathlib import Path
REPO=Path(__file__).resolve().parents[3];OUT=REPO/'tests/conformance/results/2026-11-24'
def read(name):return json.loads((OUT/name).read_text())
def stamp(value):return dt.datetime.fromisoformat(value).timestamp()
trials=[read('B10-trial-'+str(n)+'.json') for n in (1,2,3)]
assert all(s['phase']=='reopened' and s['channel_controls']['passed'] for s in trials)
assert all(s['isolation_ms']<=30000 for s in trials)
controls=len(trials[0]['channel_controls']['rows'])
assert all(len(s['channel_controls']['rows'])==controls and s['cut']['local_effects']['stable_after_cut'] for s in trials)
durations=[];lines=['# B10 — piloto PKI-C4 B / S20','',
 'Instalação técnica `picturas-pki-pilot-b10`, dataset novo, separado das instalações preservadas. '
 'Responsável pela execução: Codex, com autorização do utilizador. Commit de partida `cb1e028` '
 'com alterações B10 ainda sem commit. Hardware, versões, identidades e digests efetivos: '
 '[manifesto público](../tests/conformance/results/2026-11-24/B10-runtime-manifest.json).',
 '', 'Carga por tentativa: uma conta anónima e um projeto técnico; job real de vídeo 90 s, '
 '1280×720, 30 fps, quatro passos brightness 1.01; sem Process de domínio ou débito. Cada tipo tem ligação '
 'persistente prévia: HTTP interno, HTTPS público, WSS owner, pool Mongo autenticado, AMQP '
 'autenticado, S3 HEAD assinado e HTTP/2 gRPC. Os probes interiores e exteriores são '
 'independentes; o observador não tem Docker socket. Não é carga de produção.', '',
 '| Tentativa | t_detectado → comando (ms) | Isolamento completo (ms) | Último corte independente (ms) | Isolado → reabertura (s) | Comando → reabertura (s) | Resultado |',
 '|---|---:|---:|---:|---:|---:|---|']
phases=[]
for n,s in enumerate(trials,1):
 total=stamp(s['t_reabertura'])-stamp(s['t_comando'])
 substitution=stamp(s['t_reabertura'])-stamp(s['t_isolado']);durations.append(substitution)
 reaction=(stamp(s['t_comando'])-stamp(s['t_detectado']))*1000
 lines.append(f'| [{n}](../tests/conformance/results/2026-11-24/B10-trial-{n}.json) | {reaction:.3f} | {s["isolation_ms"]:.3f} | {s["isolation"]["independent_cut_ms"]:.3f} | {substitution:.3f} | {total:.3f} | PASS |')
 e={v['phase']:stamp(v['at']) for v in s['events']}
 phases.append([n,e['preparing_pki']-stamp(s['t_isolado']),e['pki_activated_isolated']-e['preparing_pki'],
  s['quarantine_written_at_ns']/1e9-e['pki_activated_isolated'],
  (s['browser-proof']['inspected_at_ns']-s['browser-ready']['ready_at_ns'])/1e9,
  e['verifying_isolated']-e['restarting_isolated'],e['verified_admissions_closed']-e['verifying_isolated']])
lines+=['',f'Substituição medida: **mínimo {min(durations):.3f} s; mediana {statistics.median(durations):.3f} s; máximo {max(durations):.3f} s** (n=3). '
 f'O máximo **{max(durations):.3f} s** é o critério empírico contextual de comparação neste cenário, registado em 24/11/2026; '
 'não é um SLA universal, uma escolha de máquina BF/MF nem um prazo de 15/5 minutos. '
 'As três observações completas ficaram abaixo de 30 s e do alvo 10 s de isolamento.', '',
 '| Tentativa | Pausa operador até retire (s) | Emissão/staging/ativação (s) | Ativação → quarentena concluída (s) | Preparação browser → inspeção (s) | Reinício (s) | Material/consumidores/controlos (s) |',
 '|---|---:|---:|---:|---:|---:|---:|']
lines += ['| '+' | '.join(str(row[0]) if i==0 else f'{v:.3f}' for i,v in enumerate(row))+' |' for row in phases]
lines+=['', 'Os tempos incluem a intervenção do agente/operador, o arranque dos backends para '
 'quarentena e a inspeção visual. O tempo entre comando e deteção é uma declaração sintética '
 'do piloto, sem promessa de deteção de incidentes reais. A coluna da quarentena usa o mtime '
 'do recibo privado concluído; fases independentes podem sobrepor-se. As colunas parciais '
 'não devem ser somadas para omitir pausas; o total deriva sempre dos timestamps originais.', '',
 'Em cada tentativa: 33 participantes novos (32 vivos e bootstrap concluído), manifesto '
 'completo, 15 folhas com chaves novas e CA com chave nova, CA antiga excluída dos contextos '
 f'vivos, {controls} controlos TLS/identidade/dados e recusa das seis tentativas de sessão antiga. '
 'AMQP não emitiu ticket nesse contexto; outros canais forneceram tickets ainda dentro '
 'dos 7200 s de validade. Nenhum timeout foi contado como recusa. As fotografias nativas '
 'imediatamente antes do comando e depois da reabertura registam ligações/consumidores '
 'por principal; no estado isolado os zeros assentam no PID zero do broker e na recusa '
 'de novas ligações. Quatro amostras independentes do output parcial confirmam que '
 'deixou de mudar após o corte. A observação de PID zero '
 'de todos os contentores prova que o worker deixou de executar efeitos locais. Mensagem '
 'durável e diretório apenas da fixture foram postos em quarentena (D-33/decisão 42), '
 'sem replay, compensação ou alteração de domínio.', '',
 'Controlos adicionais: [Seaweed interno 28/28](../tests/conformance/results/2026-11-24/B10-seaweed-internal.json), '
 '[aplicação real Firefox + WSS](../tests/conformance/results/2026-11-24/B10-browser-live.json), '
 '[falhas reais](../tests/conformance/results/2026-11-24/B10-negative-real.json) e '
 '[operação de recuperação](../tests/conformance/results/2026-11-24/B10-fault-operation.json). '
 'A operação adicional também confirma 4369/25672/15692 inacessíveis da rede RabbitMQ.', '',
 '## Execuções e limites preservados', '',
 'A instalação inicial em diretório temporário perdeu a CA/estado após interrupção. Foi '
 'desmontada sem `-v`; os seus sete volumes foram preservados. Não integra a amostra válida. '
 'A instalação persistente usa outro projeto e volumes novos; não houve reconstrução de confiança '
 'sobre o dataset perdido. Os registos iniciais de renovação/readiness são mantidos nos resultados.', '',
 'Os três primeiros ensaios também passaram os cortes, mas não tinham a fotografia nativa '
 'por principal imediatamente antes de cada comando, nem as quatro amostras de estabilidade '
 'do output parcial. Foram preservados como '
 '[initial-trial-1](../tests/conformance/results/2026-11-24/B10-initial-trial-1.json), '
 '[initial-trial-2](../tests/conformance/results/2026-11-24/B10-initial-trial-2.json) e '
 '[initial-trial-3](../tests/conformance/results/2026-11-24/B10-initial-trial-3.json). '
 'Isolamento 3719.220/3816.579/3845.157 ms; substituição 187.634/194.929/191.465 s. '
 'A amostra final de três usa o harness completo e quatro passos brightness, para manter '
 'o job ativo durante a fotografia nativa. Os 118 controlos originais foram completados '
 'com as três portas administrativas Rabbit locais. Estes seis ensaios e o diagnóstico '
 'não são fundidos numa distribuição com carga/instrumentação diferentes.', '',
 'Quatro preparações de observadores falharam antes de qualquer job/incidente; '
 '[bruto](../tests/conformance/results/2026-11-24/B10-preparation-failures.json). '
 'A tentativa de diagnóstico teve isolamento de 3775.108 ms, mas a primeira verificação '
 'dos clientes antigos no Node devolveu EOF/reset no TLS 1.3. A aplicação ficou isolada. '
 'Foi corrigida a sonda para obter alertas TLS 1.2, com controlo positivo no mesmo protocolo; '
 'o generative-mock mantém o TLS 1.3. Repetiu-se só a verificação da mesma operação, '
 'sem reemitir CA nem reiniciar relógios. '
 '[Falha inicial](../tests/conformance/results/2026-11-24/B10-diagnostic-initial-failure.json) e '
 '[diagnóstico completo](../tests/conformance/results/2026-11-24/B10-diagnostic-control-retry.json) '
 'permanecem separados das três tentativas comparáveis; o tempo completo não foi apagado.', '',
 'Os controlos do browser usaram Firefox 159.0 com NSS isolado: nova CA positiva, antiga '
 'recusada, nome errado recusado e expirado recusado. Os avisos nativos foram inspecionados '
 'visualmente pelo Codex, sem exceções. A aplicação real e o owner WSS fresco foram também '
 'observados; o ator não é apresentado como confirmação humana do utilizador. As capturas '
 'ficam privadas, com hashes públicos. A sequência reproduzível está no '
 '[runbook](pki-operations.md).', '',
 'Na segunda tentativa final houve dois timeouts de preparação/captura da página '
 'nativa de CA antiga. A instalação manteve-se isolada. Repetiu-se apenas a preparação '
 'visual da mesma CA/operação; depois foram inspecionados os quatro casos e os restantes '
 'controlos passaram. Os dois erros constam do bruto da tentativa e todo o seu tempo '
 'integra a substituição e o máximo contextual. Não houve reemissão nem reset de relógio.', '',
 'A reabertura de uma instalação normal após compromisso continua bloqueada até ao B11. '
 'O piloto técnico não prova reconciliação de domínio. S20 é conformidade deste bloco; '
 'o instrumento de medição não foi alterado. A verificação conjunta e a comparação BF/MF '
 'oficiais continuam no B12.']
lines+=['','## Ligações/consumidores por principal','',
 'Em cada célula: ligações/consumidores, tentativas 1 · 2 · 3. Antes: fotografia nativa '
 'imediatamente anterior à declaração. Isolado: zero por terminação real do broker e '
 'recusa de conexões; não se apresenta uma consulta indisponível como contagem zero. '
 'Depois: nova fotografia nativa após reabertura. A ligação extra do video_tool antes '
 'é o observador autenticado, sem consumidor adicional.', '',
 '| Principal | Antes | Isolado | Reaberto |','|---|---|---|---|']
for principal in sorted(trials[-1]['registered_consumers']):
 values=[]
 for stage in ['broker-before','broker-isolated','broker-reopened']:
  counts=[]
  for s in trials:
   count=s[stage]['principals'][principal]
   if stage=='broker-isolated':assert count=={'connections':0,'consumers':0}
   else:assert count['connections']>0 and count['consumers']>0
   counts.append(str(count['connections'])+'/'+str(count['consumers']))
  values.append(' · '.join(counts))
 lines.append('| '+principal+' | '+' | '.join(values)+' |')
(REPO/'docs/refactor-piloto-pki.md').write_text('\n'.join(lines)+'\n')

manifest=read('B10-runtime-manifest.json');last=trials[-1]
def ref(service):return f'[{service}](#i-{service.lower()})'
def cert(service):return f'[C-{service}](#c-{service.lower()})'
rows=[]
def channel(name,services,certificate,assertion,evidence):
 rows.append((name,', '.join(ref(s) for s in services)+'; '+cert(certificate),assertion,evidence))
api=[('api_gateway','projects','leitura/mutação legítimas, RS256 contextual, posse/partilha'),
 ('api_gateway','users','registo/login/anónimo e perfil; identidade e sujeito'),
 ('api_gateway','subscriptions','plano/billing mock e titular autorizado'),
 ('projects','users','presença/quota no contexto permitido'),('projects','img_storage','operações storage no projeto'),
 ('users','projects','limpeza restrita à conta removida'),('ws_gateway','projects','join/revalidação com autorização fresca'),
 ('expand_ai_tool','generative-mock','outpainting real por requests/mTLS')]
for a,b,operation in api:
 channel(a+' → '+b,[a,b],b,'mTLS e par/operação D4; '+operation+'. Sem certificado, par errado, CA antiga e nome errado recusados.',
         'P + D4 + FUNC; PASS')
channel('Browser → nginx',['frontend','nginx'],'nginx','NSS isolado; nova CA válida, CA retirada/expirado/nome errado recusados; aplicação e WSS owner frescos.','BROWSER + P; PASS')
for target in ['frontend','api_gateway','ws_gateway']:
 channel('nginx → '+target,['nginx',target],target,'Upstream HTTPS validado, SNI próprio, cliente nginx. Conteúdo/API/polling/upgrade legítimos; sockets antigos cortados; novo contexto sem CA retirada.','P + D4 + FUNC + BROWSER; PASS')
channel('nginx → SeaweedFS S3',['nginx','seaweedfs'],'seaweedfs','HTTPS 9000, GET/HEAD/Range de URL assinada; métodos/permissões indevidos recusados.','P + S3 + F02; PASS')
channel('img_storage → SeaweedFS S3',['img_storage','seaweedfs'],'seaweedfs','AWS SDK sobre HTTPS; HEAD nativo por reabertura, PUT/GET/remoção reais pelo pipeline; scope próprio.','P native_s3_head + S3 + F02; PASS')
channel('s3-bootstrap → SeaweedFS S3',['s3-bootstrap','seaweedfs'],'seaweedfs','Job Node de arranque com CA validada e identidade admin só nele; headBucket termina com exit 0 a cada recriação.','P participants_loaded + I-s3-bootstrap; PASS')
channel('nginx → SeaweedFS filer (percurso removido)',['nginx','seaweedfs'],'seaweedfs','Não existe proxy de acesso ao filer; 8888/18888 inacessíveis da rede e /s3-console/ recusado. Não há um salto HTTP escondido.','P bypass + S3; PASS (percurso fechado)')
for owner,db,port in [('users','user',27019),('projects','project',27018),('subscriptions','subscription',27017)]:
 target=owner+'_mongoDB'
 channel(owner+' → '+target,[owner,target],target,f'TLS de servidor, principal {owner}_svc; leitura nativa e escrita só em {db}. Credencial inválida/outra BD/nome errado/CA antiga recusados; pool antigo cortado.', 'P + S16 + FUNC; PASS')
 channel('mongo-backup → '+target,['mongo-backup',target],target,f'mongodump --ssl --sslCAFile, backup_ro só leitura em {db}; processo recriado e CA nova montada. Leitura/role nativas verificadas; escrita indevida recusada.', 'P backup role + I-mongo-backup + S16; PASS')
 channel('administrador → '+target,[target],target,'Admin apenas por exec/harness de confiança, TLS e credencial fora do repositório; sem porta no host; fixture/cleanup de segurança por principal admin.', 'P + S16 + S18; PASS')
for principal in sorted(last['registered_consumers']):
 channel(principal+' → RabbitMQ',[principal,'rabbitmq'],'rabbitmq',
  'AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key.',
  'P native AMQPS + registered_consumers + S16 + F02; PASS')
channel('administrador → RabbitMQ management',['rabbitmq'],'rabbitmq','HTTPS 15671 com credencial admin; principal de worker recusado, 5672/15672 fechados e sem portas host.','P + S16 + S18; PASS')
channel('RabbitMQ CLI/epmd/distribution/Prometheus locais',['rabbitmq'],'rabbitmq','4369/25672/15692 só em loopback, inacessíveis do elk. CLI local usa cookie privado; esses listeners locais não são apresentados como TLS.','P adicional B10-fault-operation + config; PASS (rede fechada)')
for role,port in [('master HTTPS',9333),('volume HTTPS',8080),('filer HTTPS',8888),('master gRPC',19333),('volume gRPC',18080),('filer gRPC',18888),('S3 gRPC',19000)]:
 channel('SeaweedFS interno → '+role+' :'+str(port),['seaweedfs'],'seaweedfs',
  'Mesmo processo/namespace; TLS/mTLS real, folha servida atual, ausência de cliente e CA antiga (cliente/servidor) recusadas. '+
  ('19000 acessível só no elk com CN seaweedfs; HTTP/2 SETTINGS observado.' if port==19000 else 'Listener só loopback; inacessível a outros serviços.'),
  'LOOPBACK (4 controlos por listener) + P bypass; PASS')
channel('administrador → SeaweedFS',['seaweedfs'],'seaweedfs','Administração pelo namespace local; master/volume/filer fora do alcance do elk; APIs HTTPS com certificado de cliente.','LOOPBACK + P; PASS (fronteira loopback)')
matrix=['# Matriz PKI-C5 por canal — B10','',
 'Snapshot executado em 24/11/2026, `fase2-refactor`, base `cb1e028` + B10 sem commit. '
 'Cada linha remete para os IDs de imagem/versões e o perfil de certificado completos abaixo. '
 'Resultados refletem probes e operações reais; não são uma inferência de configuração do fornecedor.', '',
 '## Comandos e bruto', '',
 '- **P**: `run-b10.sh begin|replace|resume 1|2|3` → '
 '[trial 1](../tests/conformance/results/2026-11-24/B10-trial-1.json), '
 '[trial 2](../tests/conformance/results/2026-11-24/B10-trial-2.json), '
 '[trial 3](../tests/conformance/results/2026-11-24/B10-trial-3.json). '
 f'{controls} controlos por tentativa, manifestos reais e retomas antigas; '
 '[operação adicional](../tests/conformance/results/2026-11-24/B10-fault-operation.json) inclui as três portas Rabbit locais.',
 '- **D4**: `in-network.sh picturas-dev mtls-pki/b5-mtls.py` → '
 '[B10-b5-mtls-dev.txt](../tests/conformance/results/2026-11-24/B10-b5-mtls-dev.txt). '
 'Matriz por par, sem certificado/outra CA/expirado/EKU errado, plaintext e sem retoma nos servidores internos.',
 '- **FUNC**: `in-network.sh picturas-dev b4-identity.py|b4-routes.py|b4-functional.py|mtls-pki/b5-functional.py|websocket/b8-functional.py` → '
 '[B4](../tests/conformance/results/2026-11-24/B10-b4-routes-dev.txt), '
 '[B5](../tests/conformance/results/2026-11-24/B10-b5-functional-dev.txt), '
 '[B8](../tests/conformance/results/2026-11-24/B10-b8-functional-dev.txt). '
 'Guardar/leitura/mutações/cleanup/expand real/owner WSS. A guarda de validade e os clientes são testados por '
 '[b5-guard.sh](../tests/conformance/results/2026-11-24/B10-b5-guard-dev.txt).',
 '- **F02**: `evaluation/.venv/bin/python tests/conformance/data-channels/b2-functional.py` → '
 '[imagem/vídeo](../tests/conformance/results/2026-11-24/B10-F02-dev.txt); '
 '[smoke](../tests/conformance/results/2026-11-24/B10-smoke-dev.txt).',
 '- **S16/S3/S18**: `med.py run --campaign EXP --quick --metrics S01,S02,S03,S04,S05,S12,S16,S17,S18,S21`, '
 'de `evaluation/` com `.venv/bin/python`, `MED_WS_JOIN_FORMAT=v2`, projeto `picturas-nfr-exp`; '
 '[registo](../tests/conformance/results/2026-11-24/B10-EXP-run.txt). '
 'S16 verifica canais de dados/ACL; S17 e S05/F02 cobrem S3 e URLs legítimos. Instrumento congelado intacto.',
 '- **BROWSER**: `run-b10.sh browser n`, inspeção visual separada e `browser-live` → '
 '[Firefox aplicação/WSS](../tests/conformance/results/2026-11-24/B10-browser-live.json) e recibos nos trials. '
 'Ator Codex, sem atribuir confirmação humana; NSS isolado, sem bypass. Capturas privadas com hashes públicos.',
 '- **LOOPBACK**: `run-b10.sh channels` → '
 '[28 controlos reais](../tests/conformance/results/2026-11-24/B10-seaweed-internal.json). '
 'Namespace de rede do SeaweedFS só para o harness de confiança; não abre os listeners aos serviços.', '',
 '## Canais e asserções', '', '| Canal | Imagens/versões e certificado | Asserção | Prova / resultado |', '|---|---|---|---|']
matrix += ['| '+' | '.join(row)+' |' for row in rows]
matrix+=['', 'Os volumes `image_data`, `whisper_models` e dados persistentes são acessos a ficheiros, '
 'sem handshake TLS. Não contêm segredos da instalação por desenho; só o worker/serviço '
 'autorizado recebe os mounts necessários. A CA privada nunca é montada nos serviços. '
 'Os HTTPS internos do SeaweedFS aceitam clientes da CA sem allowlist de CN; a fronteira '
 'validada na decisão 20 é loopback, comprovada nos probes de rede, e não se declara aí '
 'uma allowlist inexistente. Os gRPC usam `allowed_commonNames=seaweedfs`.', '',
 '## Imagens e versões efetivas', '',
 '[Manifesto integral](../tests/conformance/results/2026-11-24/B10-runtime-manifest.json): '
 '`image_id` é o identificador SHA-256 imutável local; `repo_digests` preserva os digests '
 'de registo quando existem. Imagens construídas localmente podem não ter RepoDigest; '
 'não se inventa um digest de registo. O mesmo image_id foi usado na dev/EXP. '
 'As bibliotecas e OpenSSL completos constam do JSON por serviço.']
for image in manifest['services']:
 service=image['service'];versions=image['versions']
 if isinstance(versions,dict):
  runtime=versions['runtime'];runtime=('Node '+runtime['node']+' / OpenSSL '+runtime['openssl']) if isinstance(runtime,dict) else ('Python '+runtime.split()[0]+' / '+versions.get('ssl',''))
  libraries=', '.join(k+' '+v for k,v in versions.get('libraries',{}).items())
 else:runtime=versions.splitlines()[0];libraries='Versão completa no manifesto.'
 matrix += ['',f'### I-{service}', '',f'`{image["image_id"]}`; {runtime}. '+libraries]
 if image['repo_digests']:matrix.append('Registo: '+', '.join('`'+d+'`' for d in image['repo_digests'])+'.')
matrix+=['', '## Certificados efetivamente servidos/carregados', '',
 'Todos pertencem à CA nova cujo fingerprint DER SHA-256 é '
 '`'+last['certificates_loaded']['nginx']['ca']+'`. '
 'Emissor, SAN, EKU, validade e serial abaixo são públicos. Os fingerprints anteriores '
 'e novos, contextos vivos e respetivos testes estão no bruto de cada tentativa.']
for service,profile in sorted(last['certificates_loaded'].items()):
 matrix+=['',f'### C-{service}','', '`'+profile['certificate']+'`','', '```text',profile['public_profile'],'```']
matrix+=['','## Limites e conclusão','',
 'A cobertura de canais não equivale a reconciliação de domínio. O B11 continua necessário '
 'para reabrir uma instalação normal com trabalhos interrompidos. A fixture D-33 é técnica '
 'e exclusiva. Limites de carga, tentativas de preparação/diagnóstico, tempos de operador '
 'e critério contextual da substituição estão no [relatório do piloto](refactor-piloto-pki.md). '
 'Sem CRL/OCSP: retirada significa nova CA e todas as chaves novas. Não houve rollback da CA retirada.']
(REPO/'docs/refactor-matriz-canais.md').write_text('\n'.join(matrix)+'\n')
print(json.dumps({'pilot_trials':3,'channel_rows':len(rows),'images':len(manifest['services']),'certificates':len(last['certificates_loaded'])}))

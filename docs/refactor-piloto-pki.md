# B10 — piloto PKI-C4 B / S20

Instalação técnica `picturas-pki-pilot-b10`, dataset novo, separado das instalações preservadas. Responsável pela execução: Codex, com autorização do utilizador. Commit de partida `cb1e028` com alterações B10 ainda sem commit. Hardware, versões, identidades e digests efetivos: [manifesto público](../tests/conformance/results/2026-11-24/B10-runtime-manifest.json).

Carga por tentativa: uma conta anónima e um projeto técnico; job real de vídeo 90 s, 1280×720, 30 fps, quatro passos brightness 1.01; sem Process de domínio ou débito. Cada tipo tem ligação persistente prévia: HTTP interno, HTTPS público, WSS owner, pool Mongo autenticado, AMQP autenticado, S3 HEAD assinado e HTTP/2 gRPC. Os probes interiores e exteriores são independentes; o observador não tem Docker socket. Não é carga de produção.

| Tentativa | t_detectado → comando (ms) | Isolamento completo (ms) | Último corte independente (ms) | Isolado → reabertura (s) | Comando → reabertura (s) | Resultado |
|---|---:|---:|---:|---:|---:|---|
| [1](../tests/conformance/results/2026-11-24/B10-trial-1.json) | 37.155 | 3674.078 | 1705.075 | 136.389 | 140.063 | PASS |
| [2](../tests/conformance/results/2026-11-24/B10-trial-2.json) | 41.312 | 3665.975 | 3154.859 | 350.643 | 354.309 | PASS |
| [3](../tests/conformance/results/2026-11-24/B10-trial-3.json) | 36.818 | 3685.628 | 2214.321 | 170.098 | 173.784 | PASS |

Substituição medida: **mínimo 136.389 s; mediana 170.098 s; máximo 350.643 s** (n=3). O máximo **350.643 s** é o critério empírico contextual de comparação neste cenário, registado em 24/11/2026; não é um SLA universal, uma escolha de máquina BF/MF nem um prazo de 15/5 minutos. As três observações completas ficaram abaixo de 30 s e do alvo 10 s de isolamento.

| Tentativa | Pausa operador até retire (s) | Emissão/staging/ativação (s) | Ativação → quarentena concluída (s) | Preparação browser → inspeção (s) | Reinício (s) | Material/consumidores/controlos (s) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 0.171 | 2.135 | 32.615 | 24.277 | 39.233 | 26.039 |
| 2 | 0.164 | 2.143 | 32.689 | 31.261 | 38.391 | 28.517 |
| 3 | 0.158 | 2.133 | 32.601 | 57.406 | 38.779 | 29.056 |

Os tempos incluem a intervenção do agente/operador, o arranque dos backends para quarentena e a inspeção visual. O tempo entre comando e deteção é uma declaração sintética do piloto, sem promessa de deteção de incidentes reais. A coluna da quarentena usa o mtime do recibo privado concluído; fases independentes podem sobrepor-se. As colunas parciais não devem ser somadas para omitir pausas; o total deriva sempre dos timestamps originais.

Em cada tentativa: 33 participantes novos (32 vivos e bootstrap concluído), manifesto completo, 15 folhas com chaves novas e CA com chave nova, CA antiga excluída dos contextos vivos, 121 controlos TLS/identidade/dados e recusa das seis tentativas de sessão antiga. AMQP não emitiu ticket nesse contexto; outros canais forneceram tickets ainda dentro dos 7200 s de validade. Nenhum timeout foi contado como recusa. As fotografias nativas imediatamente antes do comando e depois da reabertura registam ligações/consumidores por principal; no estado isolado os zeros assentam no PID zero do broker e na recusa de novas ligações. Quatro amostras independentes do output parcial confirmam que deixou de mudar após o corte. A observação de PID zero de todos os contentores prova que o worker deixou de executar efeitos locais. Mensagem durável e diretório apenas da fixture foram postos em quarentena (D-33/decisão 42), sem replay, compensação ou alteração de domínio.

Controlos adicionais: [Seaweed interno 28/28](../tests/conformance/results/2026-11-24/B10-seaweed-internal.json), [aplicação real Firefox + WSS](../tests/conformance/results/2026-11-24/B10-browser-live.json), [falhas reais](../tests/conformance/results/2026-11-24/B10-negative-real.json) e [operação de recuperação](../tests/conformance/results/2026-11-24/B10-fault-operation.json). A operação adicional também confirma 4369/25672/15692 inacessíveis da rede RabbitMQ.

## Execuções e limites preservados

A instalação inicial em diretório temporário perdeu a CA/estado após interrupção. Foi desmontada sem `-v`; os seus sete volumes foram preservados. Não integra a amostra válida. A instalação persistente usa outro projeto e volumes novos; não houve reconstrução de confiança sobre o dataset perdido. Os registos iniciais de renovação/readiness são mantidos nos resultados.

Os três primeiros ensaios também passaram os cortes, mas não tinham a fotografia nativa por principal imediatamente antes de cada comando, nem as quatro amostras de estabilidade do output parcial. Foram preservados como [initial-trial-1](../tests/conformance/results/2026-11-24/B10-initial-trial-1.json), [initial-trial-2](../tests/conformance/results/2026-11-24/B10-initial-trial-2.json) e [initial-trial-3](../tests/conformance/results/2026-11-24/B10-initial-trial-3.json). Isolamento 3719.220/3816.579/3845.157 ms; substituição 187.634/194.929/191.465 s. A amostra final de três usa o harness completo e quatro passos brightness, para manter o job ativo durante a fotografia nativa. Os 118 controlos originais foram completados com as três portas administrativas Rabbit locais. Estes seis ensaios e o diagnóstico não são fundidos numa distribuição com carga/instrumentação diferentes.

Quatro preparações de observadores falharam antes de qualquer job/incidente; [bruto](../tests/conformance/results/2026-11-24/B10-preparation-failures.json). A tentativa de diagnóstico teve isolamento de 3775.108 ms, mas a primeira verificação dos clientes antigos no Node devolveu EOF/reset no TLS 1.3. A aplicação ficou isolada. Foi corrigida a sonda para obter alertas TLS 1.2, com controlo positivo no mesmo protocolo; o generative-mock mantém o TLS 1.3. Repetiu-se só a verificação da mesma operação, sem reemitir CA nem reiniciar relógios. [Falha inicial](../tests/conformance/results/2026-11-24/B10-diagnostic-initial-failure.json) e [diagnóstico completo](../tests/conformance/results/2026-11-24/B10-diagnostic-control-retry.json) permanecem separados das três tentativas comparáveis; o tempo completo não foi apagado.

Os controlos do browser usaram Firefox 159.0 com NSS isolado: nova CA positiva, antiga recusada, nome errado recusado e expirado recusado. Os avisos nativos foram inspecionados visualmente pelo Codex, sem exceções. A aplicação real e o owner WSS fresco foram também observados; o ator não é apresentado como confirmação humana do utilizador. As capturas ficam privadas, com hashes públicos. A sequência reproduzível está no [runbook](pki-operations.md).

Na segunda tentativa final houve dois timeouts de preparação/captura da página nativa de CA antiga. A instalação manteve-se isolada. Repetiu-se apenas a preparação visual da mesma CA/operação; depois foram inspecionados os quatro casos e os restantes controlos passaram. Os dois erros constam do bruto da tentativa e todo o seu tempo integra a substituição e o máximo contextual. Não houve reemissão nem reset de relógio.

A reabertura de uma instalação normal após compromisso continua bloqueada até ao B11. O piloto técnico não prova reconciliação de domínio. S20 é conformidade deste bloco; o instrumento de medição não foi alterado. A verificação conjunta e a comparação BF/MF oficiais continuam no B12.

## Ligações/consumidores por principal

Em cada célula: ligações/consumidores, tentativas 1 · 2 · 3. Antes: fotografia nativa imediatamente anterior à declaração. Isolado: zero por terminação real do broker e recusa de conexões; não se apresenta uma consulta indisponível como contagem zero. Depois: nova fotografia nativa após reabertura. A ligação extra do video_tool antes é o observador autenticado, sem consumidor adicional.

| Principal | Antes | Isolado | Reaberto |
|---|---|---|---|
| bg_remove_ai_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| binarization_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| border_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| brightness_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| contrast_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| cut_ai_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| cut_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| expand_ai_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| obj_ai_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| people_ai_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| projects | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| resize_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| rotate_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| saturation_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| text_ai_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| upgrade_ai_tool | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| video_tool | 2/1 · 2/1 · 2/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| watermark_tool_ms | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |
| ws_gateway | 1/1 · 1/1 · 1/1 | 0/0 · 0/0 · 0/0 | 1/1 · 1/1 · 1/1 |

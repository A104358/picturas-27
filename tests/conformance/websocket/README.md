# B8 — WebSocket

Executar na `picturas-dev`, com `PICTURAS_SECRETS_DIR` da instalação. Os testes
usam apenas fixtures; não imprimem JWT, links ou credenciais.

```bash
node tests/conformance/websocket/authorization.test.js
node tests/conformance/websocket/ws-route.test.js
tests/conformance/in-network.sh picturas-dev websocket/b8-functional.py
tests/conformance/in-network.sh picturas-dev websocket/b8-wire-limits.py 10
tests/conformance/in-network.sh picturas-dev websocket/b8-load.py
```

`b8-functional.py outage` anuncia `READY_STOP_PROJECTS` e `READY_START_PROJECTS`;
no host, parar/iniciar apenas `projects` nesses pontos (`b8-outage.py [projeto]` faz isso). Não reiniciar nginx até o
teste acabar, para manter o socket existente e provar a expiração sem revalidação.
O contentor de teste não recebe o socket Docker. F01/F02, smoke e as suítes B4/B5
continuam a correr separadamente. Os resultados ficam em `results/<data>/B8-*`.

O teste `client-reconnect.test.js` transpila o módulo real do frontend com o
TypeScript da imagem e controla a rede/timers: sessão igual após reconexão, falha
de rede sem logout, sessão recusada sem anónimo novo e remount durante validação.
Recebe o caminho de `frontend/lib/project-socket.ts` como argumento e a variável
`B8_TS_COMPILER` pode apontar para o TypeScript instalado na imagem.

## Contrato e limites

`join-project` recebe `{projectId, access:{kind:"owner"}}` ou
`{projectId, access:{kind:"share", shareId}}`. Sujeito/expiração vêm exclusivamente
do JWT verificado da ligação. A confirmação distingue `joined`, `denied`,
`unavailable`, `invalid_request`, `session_expired` e `rate_limited`.

Desde a decisão 53 (D-30 A), uma autorização que expira **suspende** o contexto em vez
de o remover: não recebe eventos, conta nos limites 512/4096, continua a ser revalidado
(250 ms enquanto falha) e retoma só com um allow novo, sem join; o cliente recebe
`project-access` `suspended`. `deny` remove e o JWT expirado fecha a ligação.

A nova rota `POST /internal/ws/projects/:projectId/authorize` é montada antes do
middleware de identidade do gateway e tem a sua própria lista mTLS: só
`ws_gateway`. O gateway e os restantes certificados da mesma CA recebem 403.
Não existe encaminhamento público para delegar sujeitos. A rota lê a primária
Mongo atual, sem cache e sem alterar presença, versão ou lugares de editor.

Os valores abaixo são configuráveis por ambiente do serviço (por exemplo, num
override Compose); o código recusa alargar os máximos de protocolo/segurança.

| Ambiente | Valor inicial |
|----------|---------------|
| `WS_TIMEOUT_MS`, `WS_REVALIDATE_MS`, `WS_LEASE_MS` | 1000, 1000, 5000 |
| `WS_RETRY_MS` (≤ `WS_REVALIDATE_MS`) | 250 |
| `WS_ACTIVE`, `WS_PENDING`, `WS_BATCH_SIZE`, `WS_BODY_BYTES` | 4, 16, 50, 65536 |
| `WS_CONNECTIONS`, `WS_CONTEXTS`, `WS_ROOMS`, `WS_PATHS` | 512, 4096, 32, 4 |
| `WS_SUBJECT_RATE`, `WS_SUBJECT_BURST` | 5/s, 10 |
| `WS_GLOBAL_RATE`, `WS_GLOBAL_BURST` | 100/s, 200 |
| `WS_BUCKETS`, `WS_RETENTION_MS` | 2048, 2000 |

Pedido/resposta internos contam bytes do JSON UTF-8 completo, com envelope.
O cursor divide os projetos grandes antes de exceder 50 avaliações ou 64 KiB.
Uma avaliação que não caiba sozinha é recusada; não se trunca. A fila tem um lote
ativo e um pendente por projeto; uma substituição conserva o menor deadline,
prioriza o plano recente e conclui explicitamente os joins retirados. Contextos
de revalidação retirados continuam devidos no próprio estado limitado. Não há
fila adicional de joins/promessas/ciclos. O cursor de projetos inclui os que
ainda não obtiveram vaga; o cursor de membros persiste entre ciclos.

## Relógios e emissão

Os prazos de fila e autorização usam `performance.now()`. O prazo do JWT é
ancorado conservadoramente nesse relógio quando a ligação é autenticada, e a
expiração absoluta é também conferida com `Date.now()` em cada emissão e ciclo.
Um recuo do relógio de parede não prolonga o prazo ancorado; um avanço pode cortar
mais cedo. Um allow vale no máximo cinco segundos desde a admissão da avaliação
(antes da consulta), nunca desde a receção da resposta; filas/falhas não renovam.
Geração, sequência, referência e envelope correlacionam todos os resultados.

Cada emissão protegida verifica JWT e pelo menos uma via apresentada ainda
válida para o projeto. Preview/progresso pessoais exigem também o destinatário e
o projeto no envelope do broker; contexto ausente é descartado. Não se usa
`io.to()` para emitir conteúdo protegido. Outra via válida apresentada preserva
o acesso após uma negação. Leave/disconnect invalidam avaliações e libertam
reservas; JWT inválido fecha também a ligação Engine.IO.

Os testes de carga física medem receção no cliente e separam eventos emitidos
antes/depois da revogação. Os testes do motor verificam a guarda imediatamente
antes da emissão, mesmo sem executar o timer. N1/J1/P1 e 512/4096 são corpus de
ensaio; não representam capacidade universal. A telemetria de dez em dez
segundos regista apenas contagens, cadência, latência, RSS e CPU, sem identificadores.

Os limites JSON dos controlos são medidos nos bytes recebidos pelo parser Socket.IO, antes de normalizar espaços e escapes Unicode. Os controlos de bytes usam frames exatos e ACK da aplicação (`b8-wire-limits.py`), além do teste isolado de `protocol.js`. Eventos binários de entrada são recusados: este protocolo de controlo é JSON, evitando uma fila de reconstrução de anexos. O encoder de saída mantém o comportamento original. Os resultados iniciais do diagnóstico síncrono foram preservados; contavam JSON normalizado e não servem como prova dos limites de wire.

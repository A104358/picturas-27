# Testes de conformidade (Fase 2)

[Plano, §5](../../docs/refactor-plano.md#5-testes-de-conformidade-o-que-além-das-métricas-prova-cada-decisão) · [Passagem](../../docs/refactor-handoff.md)

As métricas do `med.py` (S01–S18, U01–U25) medem o efeito da refatoração. Os testes desta
pasta provam o que as decisões exigem e o `med.py` não cobre. A ferramenta de medição
fica congelada em `evaluation/`; nada daqui a altera nem a importa.

## Organização

Uma pasta por grupo do plano §5, criada pelo bloco que a introduz:

| Pasta | Grupo | Casos | Bloco |
|-------|-------|-------|-------|
| `identity/` | Identidade | S06, S07, D7 | B4 |
| `mtls-pki/` | mTLS e PKI | S08, S09, S19, S20, ensaios PKI | B1, B5, B10 |
| `policy/` | Política | S13, S14, S15, presets | B4 |
| `websocket/` | WebSocket | S10, S11, WS-T01–T10, WS-N1, J1, P1, L1–L3, R1, B1, E1 | B8 |
| `sessions/` | Sessões | SEC-01–SEC-04, AR-01–AR-12 (só fixtures) | B9 |
| `upload/` | Upload | S22–S24, U11–U14, U16, U21–U24, U26, UL-01–UL-12 | B6, B7 |
| `operations/` | Operação | piloto PKI-C4, OPS-C1 | B10, B11 |
| `diagnostics/` | Diagnóstico | F07–F10 | B12 |

A regressão existente (F01–F03) corre com `run-f01.sh`.

## Resultados

O bruto fica em `results/<AAAA-MM-DD>/`, um ficheiro por execução, com o comando, o commit e
a saída.

## Regras

- Correm contra uma stack própria (`picturas-dev` ou `picturas-nfr-exp`), nunca contra a
  `picturas-nfr`.
- Só usam fixtures: nunca perfis, volumes ou relógios reais (plano §1, regra 7).
- Os resultados não guardam segredos: JWT, URLs assinados, tokens de upload, `shareId`s,
  chaves ou palavras-passe ficam redigidos.
- Um 5xx ou um timeout nunca contam como recusa.

## B4 — identidade e autorização HTTP

Os ficheiros do B4 ficam na raiz desta pasta (`b4-*.py`, com `b4_common.py` partilhado),
em vez de `identity/` e `policy/`, porque partilham fixtures e cobrem os dois grupos.

| Ficheiro | Prova |
|----------|-------|
| `b4-route-matrix.py` | Estático: cada declaração de rota/verbo tem uma linha em `docs/refactor-matriz-rotas.md`, com verbo e caminho iguais. `--fix` atualiza os números de linha depois de mexer no código |
| `b4-identity.py` | S06 (sessão HS256: alg, segredo, typ, iss, aud, exp, 7 dias, sub), S07 (identidade RS256: peer mTLS, alg, chave, iss, typ, kid, exp ≤30 s, método, rota, share, aud de outro serviço, sujeito) e D7 |
| `b4-routes.py` | Cada linha `B4-Rnnn` da matriz: chamador legítimo aceite e recusas; S13 (ACL-C1, links sem `expiresAt`, revogação), S14, S15, presets e F05 |
| `b4-functional.py` | Cenário curto de fumo (dono, partilha, D7, perfil, subscrição, serviços diretos) |

```bash
export PICTURAS_SECRETS_DIR=…   # a mesma instalação da stack
python3 tests/conformance/b4-route-matrix.py
python3 tests/conformance/b4-identity.py
python3 tests/conformance/b4-routes.py
```

Precisam de `requests`, `urllib3`, `PyJWT` e `cryptography`. O harness é de confiança: lê a
CA, os certificados de serviço e, para forjar identidades, o segredo HS256 e a chave RS256
do gateway; nunca os imprime. Desde o B3 só o nginx publica uma porta: os testes com
chamadas diretas aos serviços correm a partir de um contentor na rede da stack (ver abaixo). "Autorizado" num controlo positivo quer dizer: resposta de domínio, nem 401/403 nem
5xx.

## Correr dentro da rede da stack (desde o B3)

`in-network.sh` constrói uma imagem pequena (`runner.Dockerfile`: Python, `requests`,
`urllib3`, `PyJWT`, `cryptography`, sem segredos) e corre o teste num contentor ligado à rede
`<projeto>_elk`. Monta o repositório e `$PICTURAS_SECRETS_DIR` só para leitura, e define
`B4_DIRECT=network` (nome do serviço e porta do contentor) e `B4_BASE_URL=https://nginx`.
Recusa o projeto `picturas-nfr`.

```bash
tests/conformance/in-network.sh picturas-dev b4-routes.py
```

Os testes que só usam o nginx (`mtls-pki/b1-smoke.py`, `data-channels/b2-functional.py`)
continuam a correr no host, pela porta 8080.

## Quota diária e supervisão (B3)

| Ficheiro | Prova |
|----------|-------|
| `users-quota.py` | Quota de uma conta free (`FREE_DAILY_OP` = 5): duas operações seguidas no mesmo dia aceites (o defeito 701 anterior ao B4), limite de 5 respeitado pelo `PUT` e pelo `GET` de reserva |
| `diagnostics/f08-restart.py [projeto] [url]` | F08: mata o processo `node` de cada serviço Node (como um OOM) e mede o reinício, o healthcheck e o primeiro pedido servido pelo nginx. Mínimo ≤30 s, alvo ≤10 s. Corre no host (usa o `docker`) |

## B5 — mTLS e TLS por salto (`mtls-pki/`)

| Ficheiro | Onde corre | Prova |
|----------|-----------|-------|
| `mtls-pki/b5-mtls.py` | `in-network.sh` | S08 em cada servidor interno (sem certificado, outra CA, expirado, EKU só de servidor, plaintext); matriz D4 (cada certificado de serviço só aceite por quem o lista, 403 nos outros); S09 por par; sem retoma de sessão (com controlo positivo no nginx público); verificação estática do código e do nginx |
| `mtls-pki/b5-guard.sh [projeto]` | host (`docker`) | Guarda de validade Node e Python com certificados descartáveis gerados dentro do contentor (expirado, ainda não válido, válido, expira em 12 s); identidade do servidor verificada pelos clientes (`projects`, `expand_ai`) |
| `mtls-pki/b5-functional.py` | `in-network.sh` | wss pelo nginx com eventos de processamento; `expand_ai` generativo (outpainting por mTLS); eliminação de conta com limpeza dos projetos (`users` → `projects`) |

## B8 — WebSocket

Contrato, comandos, relógios, limites e corpus físico: [`websocket/README.md`](websocket/README.md). Inclui motor/fila com relógio isolado, sockets reais/mTLS, indisponibilidade/recuperação, cliente do frontend e cargas N1/J1/P1/L1/L2. O adaptador legacy/v2 da medição é provado separadamente, sem alterar `medlib/`, critérios ou casos.

B9 session and assisted-recovery commands: [`sessions/README.md`](sessions/README.md).

B10 applied PKI, pilot and fault-injection commands:
[`pki-operations/README.md`](pki-operations/README.md). Public evidence uses an
explicit allowlist; private installation material and browser profiles stay outside Git.

## B7 — direct video upload

- `upload/b7-flow.py` runs against nginx on the host: request, early refusals, one-use PUT,
  confirmation, cancellation and concurrent claims.
- `upload/b7-signature.py` runs in the stack network with `in-network.sh`: it verifies that
  the signed S3 PUT binds length, content type and internal Host, then removes its fixture.
- `upload/b7-browser.py` uses a real Chromium and the production UI. It checks image and video
  upload, invalid file, free/premium duration limits and cancellation while the PUT is in progress.
  It needs Playwright with Chromium and the installation CA; private fixtures stay in a
  temporary directory outside the repository.
- `upload/b7-late-cleanup.py` holds a real PUT open across the first expiry cleanup, lets it
  finish, advances only that fixture's deadline to the 900 + 120 second safety sweep, and
  checks that no staging object or media remains. Run it on the host with `picturas-dev` up.
- `upload/b7-lifecycle.py` exercises token expiry, version changes between request and PUT,
  interrupted versus complete bodies, idempotent confirmation, private staging and invalid
  video rejection. It also restarts `projects` across direct receive, copy and commit markers,
  checks durable hash completion, and retries cleanup after a controlled `img_storage` outage.
  It advances only its own fixture records in the dev MongoDB.

| Lifecycle case | Evidence |
|---|---|
| UL-01 | `b7-flow.py` concurrent claims and replay; `b7-lifecycle.py` interrupted claim |
| UL-02 | `b6-adapter.py` auth, ACL, quota and byte preservation; `b7-browser.py` new UI |
| UL-03 | `b7-lifecycle.py` incomplete versus complete PUT and repeat confirmation |
| UL-04 | `b7-lifecycle.py` expired token; `b6-capacity.py` idle/slots; `b7-late-cleanup.py` deadline/safety sweep |
| UL-05 | `b7-lifecycle.py` version fence; B4 share/revocation and `b6-races.py` conflicting commit |
| UL-06 | `b7-lifecycle.py` private staging; `b7-signature.py` bound PUT; `b7-flow.py` immutable one-use candidate |
| UL-07 | `b7-lifecycle.py` restart at receive, copy, commit and hash markers; `b6-races.py` single commit |
| UL-08 | `b7-lifecycle.py` unpublished copy cleanup and original preservation; `b7-late-cleanup.py` late writer |
| UL-09 | `b7-lifecycle.py` hash completion after restart; B6 adapter's ready/media checks |
| UL-10 | `b7-lifecycle.py` invalid format, private staging, foreign authority and wrong S3 object; B5 mTLS checks and B6 valid probe |
| UL-11 | `b7-lifecycle.py` storage outage, cleanup retry and published original preservation |
| UL-12 | `b6-capacity.py`, `b7-browser.py` and EXP quick resource/latency guards |

The crash markers in UL-07/08 are fixture state injection followed by a real process
restart; they do not pause the process at every instruction. UL-10's remaining byte/time
limits are enforced by the B6 bounded relay, but this suite does not independently inject
each violation. D-28 B also leaves continuous direct PUT
bodies without a 600-second absolute limit; its 900 + 120 second sweep was tested for
a writer finishing between the first and second cleanup.

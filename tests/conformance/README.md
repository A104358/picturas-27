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

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

# Resultados EXP — 2026-11-23T23:32:59Z

Commit `56f9f1c33bfe27758c0a194a381f4e8e7c4d9cf4` · host `13th Gen Intel(R) Core(TM) i7-13700H`

## RNF 1 — Segurança

| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |
|---|---|---|---|---|---|
| S01 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 15 tentativas |
| S02 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 20 tentativas |
| S03 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 8 tentativas |
| S04 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 5 tentativas |
| S12 | principal | 5000 | 2000 | CUMPRE_ALVO | 998 ms |
| S16 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 24 tentativas |
| S17 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 15 tentativas |
| S18 | principal | todas=0 | todas=0, loopback=0 | CUMPRE_ALVO | nenhuma porta interna publicada |
| S05 | guarda | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| S21 | guarda | 10 | 5 | COMPARATIVA | avaliada em `compare` contra a BF |

## RNF 2 — Eficiência no upload

| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |
|---|---|---|---|---|---|
| U01 | principal | 64 | 32 | NAO_MEDIDA |  |
| U20 | principal | rondas_3de3=1, oom=0 | rondas_3de3=3, oom=0 | NAO_MEDIDA |  |
| U19 | principal | status=[401, 403], gateway_delta_mib=8 | resposta_ms=100 | NAO_MEDIDA |  |
| U18 | principal | 1.0 | 1.0 | NAO_MEDIDA |  |
| U04 | principal | nginx=128, seaweedfs=256 | nginx=64, seaweedfs=128 | NAO_MEDIDA |  |
| U08 | principal | pico=F+16MiB por componente, residuos=0 | pico_mib=16, residuos=0 | NAO_MEDIDA |  |
| U09 | guarda | 3000 | 1000 | NAO_MEDIDA |  |
| U25 | guarda | erros=0, razao=1.1 | erros=0, razao=1.0 | NAO_MEDIDA |  |
| U15 | guarda | 1.0 | 1.0 | NAO_MEDIDA |  |
| U17 | guarda | 1.0 | 1.0 | NAO_MEDIDA |  |
| U10 | guarda | 1.1 | 1.0 | NAO_MEDIDA |  |

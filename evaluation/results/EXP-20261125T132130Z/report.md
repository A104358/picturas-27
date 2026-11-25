# Resultados EXP — 2026-11-25T13:21:30Z

Commit `1091f8779b0e74824c61acd75a99358e9c0f8821` · host `Apple M4 Pro`

## RNF 1 — Segurança

| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |
|---|---|---|---|---|---|
| S01 | principal | 0 | 0 | NAO_MEDIDA |  |
| S02 | principal | 0 | 0 | NAO_MEDIDA |  |
| S03 | principal | 0 | 0 | NAO_MEDIDA |  |
| S04 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 15 tentativas |
| S12 | principal | 5000 | 2000 | CUMPRE_ALVO | 1164 ms |
| S16 | principal | 0 | 0 | NAO_MEDIDA |  |
| S17 | principal | 0 | 0 | NAO_MEDIDA |  |
| S18 | principal | todas=0 | todas=0, loopback=0 | NAO_MEDIDA |  |
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

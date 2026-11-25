# Resultados MF — 2026-11-25T13:53:56Z

Commit `465099be090ece1125bc2994307783ae4ac6f534` · host `Apple M4 Pro`

## RNF 1 — Segurança

| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |
|---|---|---|---|---|---|
| S01 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 45 tentativas |
| S02 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 60 tentativas |
| S03 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 24 tentativas |
| S04 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 15 tentativas |
| S12 | principal | 5000 | 2000 | CUMPRE_ALVO | 1168 ms |
| S16 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 72 tentativas |
| S17 | principal | 0 | 0 | CUMPRE_ALVO | 0 admitidos em 45 tentativas |
| S18 | principal | todas=0 | todas=0, loopback=0 | CUMPRE_ALVO | nenhuma porta interna publicada |
| S05 | guarda | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| S21 | guarda | 10 | 5 | COMPARATIVA | avaliada em `compare` contra a BF |

## RNF 2 — Eficiência no upload

| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |
|---|---|---|---|---|---|
| U01 | principal | 64 | 32 | CUMPRE_MINIMO | 44.3 MiB |
| U20 | principal | rondas_3de3=1, oom=0 | rondas_3de3=3, oom=0 | CUMPRE_ALVO | 3/3 rondas |
| U19 | principal | status=[401, 403], gateway_delta_mib=8 | resposta_ms=100 | CUMPRE_ALVO | +0.0 MiB, 26 ms |
| U18 | principal | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| U04 | principal | nginx=128, seaweedfs=256 | nginx=64, seaweedfs=128 | CUMPRE_MINIMO | nginx +0.5 MiB, seaweedfs +134.6 MiB (máx.); 5/5 amostras válidas |
| U08 | principal | pico=F+16MiB por componente, residuos=0 | pico_mib=16, residuos=0 | CUMPRE_ALVO | pico máx. 0.0 MiB |
| U09 | guarda | 3000 | 1000 | CUMPRE_ALVO | 843 ms |
| U25 | guarda | erros=0, razao=1.1 | erros=0, razao=1.0 | CUMPRE_ALVO | 0.72 |
| U15 | guarda | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| U17 | guarda | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| U10 | guarda | 1.1 | 1.0 | COMPARATIVA | avaliada em `compare` contra a BF |

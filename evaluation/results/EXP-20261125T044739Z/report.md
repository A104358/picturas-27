# Resultados EXP — 2026-11-25T04:47:39Z

Commit `383561e530fdb84127a44a3bca80e4f623c8eb22` · host `Apple M4 Pro`

## RNF 1 — Segurança

| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |
|---|---|---|---|---|---|
| S01 | principal | 0 | 0 | NAO_MEDIDA |  |
| S02 | principal | 0 | 0 | NAO_MEDIDA |  |
| S03 | principal | 0 | 0 | NAO_MEDIDA |  |
| S04 | principal | 0 | 0 | INCONCLUSIVO | 1 inconclusivos: W05[ws] |
| S12 | principal | 5000 | 2000 | NAO_MEDIDA |  |
| S16 | principal | 0 | 0 | NAO_MEDIDA |  |
| S17 | principal | 0 | 0 | NAO_MEDIDA |  |
| S18 | principal | todas=0 | todas=0, loopback=0 | NAO_MEDIDA |  |
| S05 | guarda | 1.0 | 1.0 | NAO_MEDIDA |  |
| S21 | guarda | 10 | 5 | COMPARATIVA | avaliada em `compare` contra a BF |

## RNF 2 — Eficiência no upload

| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |
|---|---|---|---|---|---|
| U01 | principal | 64 | 32 | CUMPRE_MINIMO | 45.5 MiB |
| U20 | principal | rondas_3de3=1, oom=0 | rondas_3de3=3, oom=0 | NAO_MEDIDA |  |
| U19 | principal | status=[401, 403], gateway_delta_mib=8 | resposta_ms=100 | NAO_MEDIDA |  |
| U18 | principal | 1.0 | 1.0 | NAO_MEDIDA |  |
| U04 | principal | nginx=128, seaweedfs=256 | nginx=64, seaweedfs=128 | CUMPRE_MINIMO | nginx +0.5 MiB, seaweedfs +139.7 MiB (máx.); 5/5 amostras válidas |
| U08 | principal | pico=F+16MiB por componente, residuos=0 | pico_mib=16, residuos=0 | NAO_CUMPRE | resíduos temporários após 60 s |
| U09 | guarda | 3000 | 1000 | CUMPRE_ALVO | 858 ms |
| U25 | guarda | erros=0, razao=1.1 | erros=0, razao=1.0 | CUMPRE_ALVO | 0.56 |
| U15 | guarda | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| U17 | guarda | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| U10 | guarda | 1.1 | 1.0 | COMPARATIVA | avaliada em `compare` contra a BF |

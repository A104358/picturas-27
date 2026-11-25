# Resultados EXP — 2026-11-25T03:49:07Z

Commit `5d6419df518b8fca6d65380b816cbf2ea2dae21b` · host `Apple M4 Pro`

## RNF 1 — Segurança

| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |
|---|---|---|---|---|---|
| S01 | principal | 0 | 0 | NAO_MEDIDA |  |
| S02 | principal | 0 | 0 | NAO_MEDIDA |  |
| S03 | principal | 0 | 0 | NAO_MEDIDA |  |
| S04 | principal | 0 | 0 | NAO_MEDIDA |  |
| S12 | principal | 5000 | 2000 | NAO_MEDIDA |  |
| S16 | principal | 0 | 0 | NAO_MEDIDA |  |
| S17 | principal | 0 | 0 | NAO_MEDIDA |  |
| S18 | principal | todas=0 | todas=0, loopback=0 | NAO_MEDIDA |  |
| S05 | guarda | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| S21 | guarda | 10 | 5 | COMPARATIVA | avaliada em `compare` contra a BF |

## RNF 2 — Eficiência no upload

| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |
|---|---|---|---|---|---|
| U01 | principal | 64 | 32 | CUMPRE_ALVO | 13.1 MiB |
| U20 | principal | rondas_3de3=1, oom=0 | rondas_3de3=3, oom=0 | CUMPRE_MINIMO | 1/3 rondas |
| U19 | principal | status=[401, 403], gateway_delta_mib=8 | resposta_ms=100 | NAO_MEDIDA |  |
| U18 | principal | 1.0 | 1.0 | NAO_MEDIDA |  |
| U04 | principal | nginx=128, seaweedfs=256 | nginx=64, seaweedfs=128 | CUMPRE_ALVO | nginx +0.4 MiB, seaweedfs +126.4 MiB (máx.); 1/1 amostras válidas |
| U08 | principal | pico=F+16MiB por componente, residuos=0 | pico_mib=16, residuos=0 | CUMPRE_ALVO | pico máx. 0.0 MiB |
| U09 | guarda | 3000 | 1000 | INCONCLUSIVO | sem amostras de 500 MiB |
| U25 | guarda | erros=0, razao=1.1 | erros=0, razao=1.0 | NAO_MEDIDA |  |
| U15 | guarda | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| U17 | guarda | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| U10 | guarda | 1.1 | 1.0 | COMPARATIVA | avaliada em `compare` contra a BF |

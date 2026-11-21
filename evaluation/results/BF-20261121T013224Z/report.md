# Resultados BF — 2026-11-21T01:32:24Z

Commit `d6b4497d116fe2ec265040084f6ec126cb84ad49` · host `Apple M4 Pro`

## RNF 1 — Segurança

| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |
|---|---|---|---|---|---|
| S01 | principal | 0 | 0 | NAO_CUMPRE | 36 admitidos: G02[publica], G03[publica], G04[publica], G05[publica], G06[publica], G07[publica], G08[publica], G09[publica], G10[publica], G11[publica], G12[publica], G13[publica] |
| S02 | principal | 0 | 0 | NAO_CUMPRE | 54 admitidos: D02[host], D02[rede], D03[host], D03[rede], D04a[host], D04a[rede], D04b[host], D04b[rede], D05[host], D05[rede], D06[host], D06[rede] |
| S03 | principal | 0 | 0 | NAO_CUMPRE | 24 admitidos: D06[host], D06[rede], D07[host], D07[rede], D08[host], D08[rede], D15[host], D15[rede] |
| S04 | principal | 0 | 0 | NAO_CUMPRE | 15 admitidos: W01[ws], W02[ws], W03[ws], W04[ws], W05[ws] |
| S12 | principal | 5000 | 2000 | NAO_CUMPRE | sem corte durante a janela de observação |
| S16 | principal | 0 | 0 | NAO_CUMPRE | 63 admitidos: a:project[host], a:project[rede], a:subscription[rede], a:user[host], a:user[rede], c:projects->user[host], c:projects->user[rede], c:subscriptions->project[host], c:subscriptions->project[rede], c:users->project[host], c:users->project[rede], d1:projects[host] |
| S17 | principal | 0 | 0 | NAO_CUMPRE | 42 admitidos: B1[host], B1[rede], B2[host], B2[rede], R1[host], R1[rede], R2[host], R2[rede], R3[host], R3[rede], R4[host], R4[rede] |
| S18 | principal | todas=0 | todas=0, loopback=0 | NAO_CUMPRE | 12 bindings em todas as interfaces |
| S05 | guarda | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| S21 | guarda | 10 | 5 | COMPARATIVA | avaliada em `compare` contra a BF |

## RNF 2 — Eficiência no upload

| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |
|---|---|---|---|---|---|
| U01 | principal | 64 | 32 | NAO_CUMPRE | pico 1976 MiB (limite do contentor 2 GiB); processo morreu: api_gateway 12× |
| U20 | principal | rondas_3de3=1, oom=0 | rondas_3de3=3, oom=0 | NAO_CUMPRE | 0/3 rondas |
| U19 | principal | status=[401, 403], gateway_delta_mib=8 | resposta_ms=100 | NAO_CUMPRE | gateway +965.7 MiB |
| U18 | principal | 1.0 | 1.0 | NAO_CUMPRE | 6 OOM durante recusas |
| U04 | principal | nginx=128, seaweedfs=256 | nginx=64, seaweedfs=128 | NAO_CUMPRE | nginx +0.4 MiB, seaweedfs +619.2 MiB (máx.); 5/38 amostras válidas |
| U08 | principal | pico=F+16MiB por componente, residuos=0 | pico_mib=16, residuos=0 | CUMPRE_MINIMO | pico máx. 500.0 MiB |
| U09 | guarda | 3000 | 1000 | NAO_CUMPRE | 14/20 uploads de 500 MiB falharam; aceites: máx. 15776 ms, mediana 6171 ms |
| U25 | guarda | erros=0, razao=1.1 | erros=0, razao=1.0 | NAO_CUMPRE | 6 erros |
| U15 | guarda | 1.0 | 1.0 | CUMPRE_ALVO | 100% |
| U17 | guarda | 1.0 | 1.0 | NAO_CUMPRE | 86.0% |
| U10 | guarda | 1.1 | 1.0 | COMPARATIVA | avaliada em `compare` contra a BF |

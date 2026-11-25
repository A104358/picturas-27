# Comparação BF vs MF

BF: `BF-20261121T013224Z` · MF: `MF-20261125T153646Z`

| Métrica | BF | MF | Estado MF |
|---|---|---|---|
| S01 | 36 admitidos: G02[publica], G03[publica], G04[publica], G05[publica], G06[publica], G07[publica], G08[publica], G09[publica], G10[publica], G11[publica], G12[publica], G13[publica] | 0 admitidos em 45 tentativas | CUMPRE_ALVO |
| S02 | 54 admitidos: D02[host], D02[rede], D03[host], D03[rede], D04a[host], D04a[rede], D04b[host], D04b[rede], D05[host], D05[rede], D06[host], D06[rede] | 0 admitidos em 60 tentativas | CUMPRE_ALVO |
| S03 | 24 admitidos: D06[host], D06[rede], D07[host], D07[rede], D08[host], D08[rede], D15[host], D15[rede] | 0 admitidos em 24 tentativas | CUMPRE_ALVO |
| S04 | 15 admitidos: W01[ws], W02[ws], W03[ws], W04[ws], W05[ws] | 0 admitidos em 15 tentativas | CUMPRE_ALVO |
| S12 | sem corte durante a janela de observação | 1125 ms | CUMPRE_ALVO |
| S16 | 63 admitidos: a:project[host], a:project[rede], a:subscription[rede], a:user[host], a:user[rede], c:projects->user[host], c:projects->user[rede], c:subscriptions->project[host], c:subscriptions->project[rede], c:users->project[host], c:users->project[rede], d1:projects[host] | 0 admitidos em 72 tentativas | CUMPRE_ALVO |
| S17 | 42 admitidos: B1[host], B1[rede], B2[host], B2[rede], R1[host], R1[rede], R2[host], R2[rede], R3[host], R3[rede], R4[host], R4[rede] | 0 admitidos em 45 tentativas | CUMPRE_ALVO |
| S18 | 12 bindings em todas as interfaces | nenhuma porta interna publicada | CUMPRE_ALVO |
| S05 | 100% | 100% | CUMPRE_ALVO |
| S21 | get_project 6.1 ms, get_user 3.5 ms | get_project 5.5 ms (Δ -0.7), get_user 5.3 ms (Δ +1.9) | CUMPRE_ALVO |
| U01 | pico 1976 MiB (limite do contentor 2 GiB); processo morreu: api_gateway 12× | 45.4 MiB | CUMPRE_MINIMO |
| U20 | 0/3 rondas; 3 rondas com OOM | 3/3 rondas | CUMPRE_ALVO |
| U19 | gateway +965.7 MiB | +0.1 MiB, 26 ms | CUMPRE_ALVO |
| U18 | 6 OOM durante recusas | 100% | CUMPRE_ALVO |
| U04 | nginx +0.4 MiB, seaweedfs +619.2 MiB (máx.); 5/38 amostras válidas | nginx +0.5 MiB, seaweedfs +142.6 MiB (máx.); 5/5 amostras válidas | CUMPRE_MINIMO |
| U08 | pico máx. 500.0 MiB | pico máx. 0.0 MiB | CUMPRE_ALVO |
| U09 | 14/20 uploads de 500 MiB falharam; aceites: máx. 15776 ms, mediana 6171 ms | 806 ms | CUMPRE_ALVO |
| U25 | 6 erros | 0.58 | CUMPRE_ALVO |
| U15 | 100% | 100% | CUMPRE_ALVO |
| U17 | 86.0% | 100% | CUMPRE_ALVO |
| U10 | 18 estratos comparados (2 estratos sem base: nenhum upload aceite na BF) | razão máx. 0.89 | CUMPRE_ALVO |

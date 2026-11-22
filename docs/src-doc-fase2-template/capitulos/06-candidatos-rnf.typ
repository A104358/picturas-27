#import "../template.typ": *

// Capítulo inteiro na horizontal (tabelas largas). Para voltar ao vertical, retirar o #paisagem[ ].
#paisagem[
= Candidatos a Requisitos Não Funcionais

#orientacao[
  *Origem:* Exercício 6, Bloco 2, secção 5 do _template_.

  *Objetivo do capítulo:* escolher *dois* requisitos não funcionais *distintos* a melhorar nesta fase, a partir dos
  cenários de qualidade mais prioritários do capítulo 5. Cada um é classificado segundo a ISO/IEC 25010 (característica e,
  quando aplicável, subcaracterística) e parte de uma fragilidade concreta da solução de base, com evidência.

  Cada candidato é depois especificado, implementado e avaliado por si, ainda que os dois possam estar relacionados.
  A coluna do cenário liga o candidato ao `QS-nn` do capítulo 5, que é a entrada do Exercício 7 (capítulo 7).
]

#tab([Candidatos a requisitos não funcionais da Fase 2],
  tabela(
    colunas: (1.6cm, 2.6cm, 3cm, 2.4cm, 2.8cm, 2.6cm, 2cm, 3cm, 2.8cm),
    tamanho: 7.5pt,
    [\#], [Característica / subcaracterística (ISO/IEC 25010)], [Fragilidade na base (evidência)], [Origem (padrão global / vídeo / interação)], [Impacto nos _stakeholders_ (pertinência)], [Exigência técnica (complexidade)], [Cenário (`QS-nn`, cap. 5)], [Escala e método de medição (esboço)], [Pré-requisitos / efeitos colaterais],
    [CAND-1 (= QC-06)], [Segurança — confidencialidade, integridade e autenticidade], [Proteção do _gateway_ não cobre todas as identidades/rotas/_storage_/WS; efeitos indevidos verificados. (EV-24, EV-43)], [Padrão global, herdado pelas operações de vídeo], [Protege projetos, originais, resultados e colaboradores; relevante para imagem e vídeo], [Coordenar verificação de ator, autorização de domínio, mTLS/TLS, identidade delegada e revogação, preservando rotas legítimas], [QS-01 principal; QS-07 complementar], [Casos finitos por fronteira para QS-01; efeitos/bytes/eventos e latência de corte para QS-07, por fronteira/janela], [PKI/sessões/migração e dados legítimos; _overhead_/disponibilidade/manutenibilidade. EV-24/EV-43/EV-44; H-14],
    [CAND-2 (= QC-05)], [Eficiência de desempenho — utilização de recursos; comportamento temporal como guarda], [Buffers integrais em três Node; pressão/retenção/OOM e aceitação lenta em pilotos. (EV-08, EV-11, EV-42)], [Interação entre entrada global e tamanho do vídeo; não um defeito dos efeitos PIL], [Viabiliza o carregamento existente sem esgotar o _gateway_/_host_ ou impedir outros pedidos], [_Streaming_ limitado nos dois transportes, validação/estado/S3, métricas até trabalho completo e compatibilidade], [QS-02], [Memória/CPU/rede/disco, tempos até _ready_/_hash_/_cleanup_, falhas/integridade, por serviço/janela], [Autorização antes do corpo, _staging_, quota preservada, _cache_/_hash_ coerentes; não esconder custo no _storage_. EV-08/EV-11/EV-42/EV-44; H-15/H-18],
  ),
)

== Quantificação

#orientacao[
  Indiquem a *escala* (o que se mede e em que unidade) e o *método de medição* (cenário, carga, ambiente e instrumento) de
  cada candidato. O objetivo é mostrar que o requisito é mensurável e que sabem como o medir.

  Os valores medidos na base, os valores-alvo e os valores mínimos aceitáveis *só são fixados após a medição inicial
  (_baseline_, capítulo 10)*. Não os inventem: preencham as três últimas linhas da tabela só depois de medir a base,
  indicando a origem de cada valor (e.g., medição, referência externa, necessidade de um _stakeholder_).
]

#tab([Quantificação dos requisitos não funcionais],
  tabela(
    colunas: (4.2cm, 1fr, 1fr),
    [], [CAND-1 / QS-01 e complemento QS-07], [CAND-2 / QS-02],
    [Escala (o que se mede e em que unidade)], [Tentativas/efeitos indevidos e sucessos legítimos por caso; bytes/eventos e tempo de corte/latência em ms], [RSS/cgroup/pico agregado em MiB, CPU-s, bytes por fronteira/disco, OOM/reinícios, tempos em ms, integridade e sucesso por tentativa],
    [Cenário de medição], [QS-01: público/_host_/_peer_ Docker, dono/editor/leitor/outro e chamada/entrada válida ou adulterada por caso. QS-07: membro admitido, revogação, eventos ativos e controlo de via alternativa], [Corpus de vídeo PAD e real, transportes novo/legado separados, validação/_hash_/_cleanup_ e pedidos leves pareados],
    [Carga], [Casos materializados com controlo positivo; WS-N1=50, J1=510, P1=200; fronteiras L/R/B/E do contrato], [10/100 MiB _free_/premium e 500 MiB premium, H/T e processo reiniciado/aquecido; C=1/C=3; 1024 MiB/+1 byte como fronteira funcional separada],
    [Ambiente], [Host oficial dedicado Apple M4 Pro (Docker Desktop com 12 CPU e 7,7 GiB de RAM em VM Linux), _stack_ isolada `picturas-nfr`. Diagnóstico exploratório inicial em Ubuntu 22.04 LTS (i7-13700H). (EV-28, EV-45)], [Mesmo host dedicado Apple M4 Pro (12 CPU, 7,7 GiB RAM), _stack_ `picturas-nfr`. Gerador de carga executado fora dos contentores Node medidos. (EV-45)],
    [Instrumento], [Instrumento formal congelado `evaluation/med.py` (v`638516104ae9`), critérios em `evaluation/criteria.yaml`, testes em `cases/security.yaml`. Resultados brutos em `evaluation/results/BF-20261121T013224Z/`.], [Instrumento `evaluation/med.py` (v`638516104ae9`), gerador de _streaming_ HTTP de ficheiros PAD/reais, coletores de _cgroups_/Docker stats e integridade SHA-256. Resultados brutos em `evaluation/results/BF-20261121T013224Z/`.],
    [Valor medido na base], [
      Efeitos indevidos admitidos na _baseline_ formal (BF-20261121T013224Z):\
      - Entrada pública (S01): 36/45 admitidos (80%);\
      - API interna host/rede (S02): 54/60 admitidos (90%);\
      - Storage/signer (S03): 24/24 admitidos (100%);\
      - Salas/eventos WS (S04): 15/15 admitidos (100%);\
      - Acessos MongoDB (S16): 63/72 admitidos (87,5%);\
      - Acessos RabbitMQ/S3 (S17): 42/45 admitidos (93,3%);\
      - Portas no host (S18): 12 portas expostas em 10 serviços;\
      - Tempo de corte WS (S12): sem corte (>30 s, 263 eventos).\
      Guardas: S05 legítimas: 45/45 (100%); S21 latência: 6,1 ms / 3,5 ms de referência.
    ], [
      Recursos e capacidade na _baseline_ formal (BF-20261121T013224Z):\
      - Pico adicional Node (U01): 1976 / 1011 / 1001 MiB (500 MiB); gateway morreu 12×;\
      - Concorrência C=3 (U20): 0/3 nas 3 rondas (OOM em todas);\
      - Desperdício pré-recusa (U19): +966 MiB, 401 aos 10,6 s;\
      - Recusa de inválidos (U18): 15/21 (71%; I1 e I6 geram 502 + OOM);\
      - Memória S3 (U04): máx. +619 MiB (mediana +585 MiB);\
      - Disco temporário (U08): 500 MiB nginx, 500 MiB `projects` (0 resíduos).\
      Guardas: U09 aceitação: 14/20 falharam (500 MiB), aceites mediana 6171 ms; U25 coexistência: 6 erros (2/par) e OOM nos 3 pares; U15 integridade: 86/86 (100%); U17 válidos aceites: 86/100 (86%); U10 tempo total: 500 MiB (H) 8440–8904 ms, (T) 0 aceites.
    ],
    [Valor-alvo (e origem)], [
      - S01, S02, S03, S04, S16, S17: 0 efeitos indevidos admitidos (Política P);\
      - S18: 0 portas publicadas fora da rede Docker (Engenharia E);\
      - S12: tempo de corte WS $<= 2000$ ms (Decisão D).\
      Guardas: S05: 100% operações legítimas concluídas (P); S21: sobrecarga latência $<= +5$ ms (E).
    ], [
      - U01: pico adicional Node $<= 32$ MiB (D, EVAL-M1);\
      - U20: 3/3 rondas com 3 uploads de 500 MiB sem OOM (D);\
      - U19: $<= 100$ ms após cabeçalhos sem consumo de corpo (E);\
      - U18: 100% recusa correta de uploads inválidos (P / Requisito R);\
      - U04: incremento nginx $<= +64$ MiB e S3 $<= +128$ MiB (D / E);\
      - U08: $<= 16$ MiB/upload sem _spool_ integral e 0 resíduos (E).\
      Guardas: U09: aceitação pós-envio $< 1000$ ms (R); U25: 0 falhas e latência $<= "controlo"$ (D); U15: integridade SHA-256 100% (P); U17: 100% válidos aceites (P); U10: tempo total $<= "BF"$ (D).
    ],
    [Valor mínimo aceitável (e origem)], [
      - S01, S02, S03, S04, S16, S17: 0 efeitos indevidos admitidos (P);\
      - S18: 0 portas publicadas fora do _loopback_ (E);\
      - S12: tempo de corte WS $<= 5000$ ms (D).\
      Guardas: S05: 100% de sucesso (P); S21: sobrecarga latência $<= +10$ ms (E).
    ], [
      - U01: pico adicional Node $<= 64$ MiB (D);\
      - U20: 3/3 sem OOM em pelo menos uma das rondas (D);\
      - U19: $<= 8$ MiB gastos antes de recusa 401 (E);\
      - U18: 100% recusa correta de uploads inválidos (P / R);\
      - U04: incremento nginx $<= +128$ MiB e S3 $<= +256$ MiB (D / E);\
      - U08: $<= C times (F + 16 "MiB")$ e 0 resíduos (E).\
      Guardas: U09: aceitação pós-envio $< 3000$ ms (R); U25: 0 falhas e latência $<= 1,10 times "controlo"$ (D); U15: integridade SHA-256 100% (P); U17: 100% válidos aceites (P); U10: tempo total $<= 1,10 times "BF"$ (D).
    ],
  ),
)

== Relação entre os dois candidatos

Autorização antes do corpo é pré-requisito para reduzir trabalho em pedidos indevidos. Por outro lado, retirar o corpo dos Node exige controlar a escrita/leitura S3 e o estado de _pending_. TLS/assinatura/consultas acrescentam CPU/latência; _streaming_/_hash_ posterior alteram I/O, estados e risco de falha. Os dois RNF são avaliados separadamente, com U25/funcionalidade como guardas e sem inferir causa isolada de um resultado final conjunto.

== Evidência exploratória 

#tab([Evidência exploratória],
  tabela(
    colunas: (4cm, 5cm, 1fr),
    [Descrição], [Localização (_scripts_, dados, resultados)], [Como repetir],
    [Bloco 1: processamento misto, extração, testes existentes], [`memory-bank/intents/001-.../evidence/validacao-2026-11-09.txt` e `preparacao.cjs`], [Seguir o registo em instalação descartável, revendo alvos. Histórico de 8/74 testes e ensaio funcional; não repetido no Bloco 2. EV-28],
    [B14: carga e acessos internos com asserções de bytes, uma falha de worker], [`memory-bank/intents/001-.../evidence/README.md`], [Preparação/corpus/gerador/coletores identificados no índice; nomes fixos e ações mutantes exigem adaptação/isolar. Não executar nos volumes retidos. EV-41],
    [B16: _uploads_ e matriz de segurança auditada], [`memory-bank/intents/001-.../evidence/nfr-2026-11-16/README.md`], [Gerador PAD e _probes_ arquivados; corrigir _premium_/asserções/serviços ausentes antes de reutilizar. EV-42/EV-43],
  ),
)
]

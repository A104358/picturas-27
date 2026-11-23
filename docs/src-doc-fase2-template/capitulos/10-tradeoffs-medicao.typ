#import "../template.typ": *

= Trade-offs, Medição e Preservação Funcional

#orientacao[
  *Origem:* Exercício 7, secção 5 do _template_ (e os riscos de preservação funcional do Bloco 2, secção 6).

  *Objetivo do capítulo:* mostrar que as decisões foram avaliadas além do atributo que melhoram (_trade-offs_), que a
  melhoria foi medida de forma comparável (antes e depois) e que o comportamento funcional foi preservado.

  A mesma medição é feita *antes e depois* do _refactoring_, no mesmo ambiente. *Não inventem valores* de _baseline_, alvo
  ou mínimo aceitável: fixam-se após a medição inicial. Guardem os _scripts_, os dados e o ambiente das medições para os
  reutilizar como _baseline_.
]

== Matriz de efeitos

#orientacao[
  Para cada decisão, indiquem se cada atributo *melhora* (↑), *degrada* (↓) ou fica *neutro* (=), e justifiquem. Incluam
  no mínimo quatro atributos, e entre eles a característica do outro cenário: uma melhoria num atributo costuma ter um
  custo noutro, e é isso que esta matriz deve revelar. Se uma decisão degradar um atributo, digam como a equipa vai
  gerir esse custo.
]

#paisagem[
#tab([Matriz de efeitos das decisões],
  tabela(
    colunas: (1.6cm, 2.7cm, 3.2cm, 2.4cm, 3cm, 3.5cm, 1fr),
    tamanho: 8pt,
    [Decisão], [Desempenho], [Disponibilidade / Fiabilidade], [Segurança], [Usabilidade], [Manutenibilidade / Testabilidade], [Justificação],
    [DA-1], [↓ possível pelo custo de identidade, TLS e consultas], [↓ disponibilidade por novas dependências; ↑ integridade de acesso], [↑ autorização ponta a ponta], [#sym.eq capacidade funcional; ↓ possível na reconexão], [↓ gestão inicial de confiança e pares; ↑ contratos e _probes_ verificáveis], [Mitigar TLS, consultas e falhas por testes de timeout, renovação e reconciliação; não autorizar em falha protege o domínio. EV-44; H-14/H-17/H-18],
    [DA-2], [↑ eficiência de memória; ↓ possível na latência por I/O adicional], [↑ menor pressão de recursos; ↓ risco se estados/cópias não forem reconciliados], [↑ autenticação antes do corpo; ↓ risco se o _pending_ ou o S3 falhar], [#sym.eq capacidade funcional; ↑ aceitação e ↓ possíveis por erros mal explicados], [↓ dois transportes e estados; ↑ domínio e _commit_ comuns], [Mitigar I/O, estados e discrepâncias com limites reais, testes dos dois percursos e guardas U09/U25/U15/U17/U10. EV-42/EV-44; H-15–H-18],
  ),
)
]

== Interação entre DA-1 e DA-2

#tab([Interação entre as decisões],
  tabela(
    colunas: (2.2cm, 2.2cm, 4.4cm, 1fr),
    [Decisão A], [Decisão B], [Efeito (pré-requisito, sinergia ou conflito)], [Razão / evidência],
    [DA-1], [DA-2], [Pré-requisito], [Autorização de emissão/transporte/objeto e identidade confiável impedem que o novo S3 contorne a política ou consuma corpo antes do controlo. EV-44; H-14/H-15],
    [DA-2], [DA-1], [Sinergia], [_Streaming_ e admissão antes do corpo podem reduzir recursos de pedidos indevidos; não substituem autenticação do _peer_. H-15/H-18],
    [DA-1], [DA-2], [Conflito], [TLS/assinatura/_queries_ podem degradar latência/CPU enquanto DA-2 procura reduzir recursos; U25 G e tempos equivalentes têm de passar por avaliação. EV-45; H-18],
    [DA-2], [DA-1], [Dependência de consistência], [Domínio escolhe quando um _media_ passa a ser utilizável; _hash_/_cache_/limpeza incorretos podem violar isolamento apesar de TLS válido. EV-44; H-16],
  ),
)

== Plano de medição

#tab([Plano de medição],
  tabela(
    colunas: (1.6cm, 3.2cm, 3cm, 2.6cm, 2.4cm, 2.8cm),
    tamanho: 8pt,
    [Cenário], [Cenário de teste e carga], [Ambiente (máquina, recursos, versões)], [O que se regista], [Repetições e agregação], [Onde ficam os _scripts_ e os dados],
    [QS-01 e complemento QS-07], [Matriz pública/_host_/_peer_ Docker com dono/editor/leitor/outro; rotas `users`/`subscriptions`/_storage_, TLS por canal; _join_/revogação/falha/expiração WS. N1=50, J1=510, P1=200; L1/L2 testam recusa de 513/4097.], [Host oficial de avaliação Apple M4 Pro (Docker Desktop com 12 CPU e 7,7 GiB de RAM em VM Linux), _stack_ isolada `picturas-nfr`, commit de teste `d6b4497d` (código de aplicação idêntico a `0523102`). Diagnóstico exploratório inicial em Ubuntu i7-13700H (EV-28).], [Tentativas e controlos positivos, estado/bytes/eventos, _timings_, falhas de rede/TLS/domínio separadas, fila/CPU/RSS/latência; sem segredos.], [Três repetições por caso materializado e janelas WS de 30 s; _raw_/mediana/máximo sem p95 de três amostras. Preparação, admissão e janela distinguidas.], [Instrumento formal `evaluation/med.py` (congelado na versão `638516104ae9`), critérios em `evaluation/criteria.yaml`, casos em `cases/security.yaml`. Resultados brutos da baseline arquivados em `evaluation/results/BF-20261121T013224Z/`. Especificação em `docs/metricas.md` e `docs/planoMedicao.md`.],
    [QS-02], [100 normais (perfis/tamanhos/H-T/estados), nove C=3, coexistência separada com três _uploads_/600 pedidos leves; formatos/fronteiras e ambos os transportes materializados. 1024 MiB/+1 byte só guarda funcional separada.], [Mesmo host oficial Apple M4 Pro (12 CPU, 7,7 GiB RAM), _stack_ `picturas-nfr`, commit `d6b4497d`. Gerador de carga em fluxo e coletores de monitorização executados fora dos contentores Node medidos.], [RSS absoluto/incremento/retido, _cgroup_ e pico simultâneo, CPU/rede/disco/temporários, $t_0$/$t_"send"$/$t_"ready"$/$t_"hash"$/$t_"cleanup"$, integridade, nomes/versão/quota, OOM/erros e pedidos leves.], [Cinco tentativas por estrato, três rodadas C=3 e três pares de coexistência; conservar falhas e denominador. Memória do grupo não é dividida por três. U25 compara com/sem carga na mesma campanha.], [Instrumento `evaluation/med.py` (v`638516104ae9`), gerador de _streaming_ HTTP com ficheiros PAD/reais. Resultados brutos da baseline formal arquivados em `evaluation/results/BF-20261121T013224Z/`. Especificação e critérios em `docs/metricas.md` e `docs/planoMedicao.md`.],
  ),
)

== Resultados das medições

#orientacao[
  Para cada requisito não funcional, apresentem os valores medidos *antes* (_baseline_) e *depois* do _refactoring_, com o
  mesmo método e nas mesmas condições (plano acima), e comparem-nos com o valor-alvo e o valor mínimo aceitável fixados no
  capítulo 6. Os dados brutos e os _scripts_ ficam no repositório entregue.

  Na análise, sejam críticos: o que melhorou, o que não foi atingido e porquê, que outros atributos foram afetados
  (confirmando ou não a matriz de efeitos) e que ameaças à validade das medições existem.
]

#paisagem[
#tab([Resultados das medições (Baseline Formal vs. Alvos e Medição Final)],
  tabela(
    colunas: (1.1cm, 1.8cm, 1fr, 3.2cm, 2.2cm, 2.2cm, 1.8cm, 1.6cm),
    tamanho: 7pt,
    [ID], [Tipo], [Métrica (o que se mede, unidade)], [Antes (Baseline BF)], [Mínimo aceitável], [Valor-alvo], [Depois (MF)], [Atingido?],
    // RNF 1
    [S01], [Principal], [Efeitos indevidos entrada pública (recursos de outro utilizador)], [36/45 admitidos (12 de 15 casos; 80%)], [0], [0], [#preencher[...]], [#preencher[...]],
    [S02], [Principal], [Efeitos indevidos chamada direta API interna (host e rede Docker)], [54/60 admitidos (9 de 10 casos; 90%)], [0], [0], [#preencher[...]], [#preencher[...]],
    [S03], [Principal], [Operações indevidas no storage/signer (originais e resultados)], [24/24 admitidos (4 de 4 casos; 100%)], [0], [0], [#preencher[...]], [#preencher[...]],
    [S04], [Principal], [Eventos protegidos ou entradas em sala WS sem autorização], [15/15 admitidos (5 de 5 casos; 100%)], [0], [0], [#preencher[...]], [#preencher[...]],
    [S12], [Principal], [Tempo de corte da receção WS após revogação (ms)], [sem corte (>30 s; 263 eventos após revogação)], [$<= 5000$ ms], [$<= 2000$ ms], [#preencher[...]], [#preencher[...]],
    [S16], [Principal], [Acessos indevidos às bases de dados MongoDB], [63/72 admitidos (87,5%)], [0], [0], [#preencher[...]], [#preencher[...]],
    [S17], [Principal], [Acessos indevidos ao broker RabbitMQ e ao S3], [42/45 admitidos (14 de 15 casos; 93,3%)], [0], [0], [#preencher[...]], [#preencher[...]],
    [S18], [Principal], [Portas de serviços internos publicadas no host], [12 portas em 10 serviços (todas as interfaces)], [0 fora de _loopback_], [0 publicadas], [#preencher[...]], [#preencher[...]],
    [S05], [Guarda], [Operações legítimas concluídas com sucesso (%)], [45/45 (100%)], [100%], [100%], [#preencher[...]], [#preencher[...]],
    [S21], [Guarda], [Sobrecarga de latência em pedidos leves ($Delta$ da mediana)], [6,1 ms / 3,5 ms (medianas de referência)], [$<= +10$ ms], [$<= +5$ ms], [#preencher[...]], [#preencher[...]],
    // RNF 2
    [U01], [Principal], [Pico de memória adicional por serviço Node no upload (MiB)], [1976 / 1011 / 1001 MiB (500 MiB); gateway morreu 12×], [$<= 64$ MiB], [$<= 32$ MiB], [#preencher[...]], [#preencher[...]],
    [U20], [Principal], [3 uploads simultâneos de 500 MiB em concorrência (C=3)], [0/3 nas 3 rondas (OOM em todas as rondas)], [3/3 sem OOM], [3/3 nas 3 rondas], [#preencher[...]], [#preencher[...]],
    [U19], [Principal], [Recurso gasto antes de recusar upload sem token], [+966 MiB gastos, 401 após 10,6 s (500 MiB recebidos)], [$<= 8$ MiB], [$<= 100$ ms pós-cabeçalhos], [#preencher[...]], [#preencher[...]],
    [U18], [Principal], [Recusa correta de uploads com parâmetros inválidos (%)], [15/21 (71%); casos I1 e I6 geram 502 + OOM], [100%], [100%], [#preencher[...]], [#preencher[...]],
    [U04], [Principal], [Memória adicional do nginx e SeaweedFS no upload (MiB)], [+0,4 / +619 MiB máx. (mediana +585 MiB)], [$+<= 128$ / $+<= 256$ MiB], [$+<= 64$ / $+<= 128$ MiB], [#preencher[...]], [#preencher[...]],
    [U08], [Principal], [Disco temporário por componente e resíduos após envio], [500 MiB no nginx, 500 MiB no `projects`; 0 resíduos (cumpre o mínimo na BF)], [$<= C times (F + 16 "MiB")$; 0 resíduos], [$<= 16$ MiB/upload; 0 resíduos], [#preencher[...]], [#preencher[...]],
    [U09], [Guarda], [Tempo de aceitação após fim do envio do corpo (ms)], [14/20 falharam (500 MiB); aceites mediana 6171 ms], [$< 3000$ ms], [$< 1000$ ms], [#preencher[...]], [#preencher[...]],
    [U25], [Guarda], [Pedidos leves durante uploads concorrentes (erros / latência)], [6 erros (2 por par); gateway sofreu OOM nos 3 pares], [0 falhas; $<= 1,10 times "controlo"$], [$<= "controlo"$], [#preencher[...]], [#preencher[...]],
    [U15], [Guarda], [Integridade SHA-256 do ficheiro original armazenado (%)], [86/86 (100%)], [100%], [100%], [#preencher[...]], [#preencher[...]],
    [U17], [Guarda], [Uploads válidos aceites e concluídos com sucesso (%)], [86/100 (86%)], [100%], [100%], [#preencher[...]], [#preencher[...]],
    [U10], [Guarda], [Tempo total de envio do upload de 500 MiB (ms)], [500 MiB (H): 8440–8904 ms; (T): 0 uploads aceites], [$<= 1,10 times "BF"$], [$<= "BF"$], [#preencher[...]], [#preencher[...]],
  ),
)
]

*Análise dos resultados* (por requisito não funcional):

#preencher[O que melhorou, o que não foi atingido e porquê, efeitos noutros atributos de qualidade e ameaças à validade das medições.]

== Preservação funcional

#tab([Preservação funcional e testes de regressão],
  tabela(
    colunas: (2.4cm, 3.8cm, 2.8cm, 3.2cm, 1fr),
    tamanho: 8.5pt,
    [Zona alterada], [Testes de regressão existentes (`Tools/video/tests`, `projects/tests`, …)], [Lacunas de teste], [Testes acrescentados], [Resultado (imagem e vídeo)],
    [DA-1: confiança/API/ACL], [`projects/tests/video-pipeline.test.js`, `process-batch.test.js`, `frame-extraction.test.js` — cobrem regras/_commit_ de processamento], [Não são testes _end-to-end_ de mTLS/JWT/_owner_/serviço/_billing_/rotas legítimas], [#preencher[…]], [#preencher[…]],
    [DA-1: WS/sessões], [Testes de vídeo cobrem produtor/progresso em âmbito limitado, não política de sala], [Falta autorização de _room_/expiração/permanência, eventos pessoais, reconexão e importação], [#preencher[…]], [#preencher[…]],
    [DA-2: HTTP/_upload_/_storage_], [Suites do orquestrador/worker validam semântica a jusante], [Não provam _buffers_ limitados, estados de _upload_, _rollback_ S3/DB, _hash_ assíncrono ou compatibilidade HTTP], [#preencher[…]], [#preencher[…]],
    [DA-2: _pipeline_/resultados], [`test_video_processor.py` e `test_frame_extraction.py`; testes Node de vídeo/extração], [Falta combinação real com transportes/PKI novos, cargas e imagens mistas], [#preencher[…]], [#preencher[…]],
    [Ambos: legendas/IA], [`test_subtitles.py` usa _recognizer_ simulado, FFmpeg real; _no-op_ e regras já testáveis], [Simulação não avalia Whisper real nem mTLS `expand_ai`→_mock_], [#preencher[…]], [#preencher[…]],
  ),
)

#tab([Riscos para a preservação funcional e mitigação],
  tabela(
    colunas: (3.4cm, 3.2cm, 4cm, 3.2cm),
    tamanho: 8.5pt,
    [Risco], [Funcionalidade afetada (imagem / vídeo)], [Mitigação], [Teste de regressão],
    [Novo controlo recusa _callers_ legítimos/partilhas/limpeza de conta], [Imagem e vídeo], [Matriz por serviço/operação/identidade e controlo positivo; autorização de domínio preservada], [Suites atuais de `projects/tests` não cobrem toda a matriz; acrescentar cenários integrados S01–S20/F04–F06],
    [Adaptador ou transporte novo altera API, versão ou quota], [Vídeo e projetos mistos], [204/`X-Project-Version` legado, CAS/conflito definido, nenhuma cobrança no _upload_, domínio/_commit_ comum], [`video-pipeline.test.js`, `process-batch.test.js`; acrescentar HTTP/recursos/erro de ambos os transportes e U24],
    [_Bytes_ pendentes/errados entram em _preview_/_Apply_/_export_], [Imagem e vídeo], [Isolamento efetivo, confirmação idempotente e teste de cada fronteira de falha; não presumir transação S3/Mongo], [`frame-extraction.test.js` e testes de processador cobrem resultados; faltam testes integrados S23/S24/U15/U16/U21–U23],
    [_Hash_ em falta confunde _cache_ ou oculta trabalho posterior], [_Preview_ e vídeo], [Leitura/escrita de _cache_ suspensas ou isolamento provado; medir $t_"hash"$ e consumo completo], [Testes de vídeo não provam _cache_/_hash_ assíncronos; UL-09 proposto, não executado],
    [Alterar efeitos, ordem, áudio, legendas ou extração], [Imagem/vídeo/misto], [Manter _pipeline_ por projeto, _trim_/_speed_ por vídeo e extração terminal/única, sem novos efeitos], [`Tools/video/tests/test_video_processor.py`, `test_frame_extraction.py`, `test_subtitles.py`; incluir fala real],
    [Cortar WS deixa _frontend_ incoerente ou troca anónimo], [Sessões/progresso de ambos], [Reconexão explícita, nova autorização por sala, preservar identidade/duas vias válidas], [Faltam testes integrados WS/expiração/importação; WS-T/AR são planos, não testes passados],
  ),
)

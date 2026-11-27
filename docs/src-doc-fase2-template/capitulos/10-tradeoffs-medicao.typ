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
    [DA-1], [↓ pequeno pelo custo de identidade, TLS e consultas (medido: S21 Δ −0,7/+1,9 ms, alvo ≤ +5)], [↓ disponibilidade por novas dependências (confirmado: W05, decisão 53), ↑ integridade de acesso], [↑ autorização ponta a ponta], [#sym.eq capacidade funcional, ↓ possível na reconexão], [↓ gestão inicial de confiança e pares, ↑ contratos e _probes_ verificáveis], [Mitigar TLS, consultas e falhas por testes de timeout, renovação e reconciliação. Não autorizar em falha protege o domínio. EV-44, H-14/H-17/H-18. *Confirmado na MF:* custo de latência pequeno e dentro do alvo. A perda de disponibilidade materializou-se nos contextos WS já admitidos, que deixavam de ser revalidados durante uma falha da `projects`, e foi gerida pela suspensão do contexto (decisão 53), sem conceder acesso sem autorização.],
    [DA-2], [↑ eficiência de memória (U01 1976 → 45,4 MiB). Latência também ↑ (U09 806 ms, U10 ≤0,89× BF), contra o ↓ previsto], [↑ menor pressão de recursos (U20 3/3, U25 sem erros). ↓ risco de estados confirmado pelo defeito do _hash_ órfão (decisão 51), corrigido], [↑ autenticação antes do corpo. ↓ risco se o _pending_ ou o S3 falhar], [#sym.eq capacidade funcional, ↑ aceitação e ↓ possíveis por erros mal explicados], [↓ dois transportes e estados, ↑ domínio e _commit_ comuns], [Mitigar I/O, estados e discrepâncias com limites reais, testes dos dois percursos e guardas U09/U25/U15/U17/U10. EV-42/EV-44, H-15–H-18. *Confirmado na MF:* o ↓ de latência previsto não aconteceu, porque o _hash_ saiu do caminho até _ready_ e o SeaweedFS deixou de ser o teto da BF. Parte do custo de memória passou para o SeaweedFS (U04 só no mínimo).],
  ),
)
]

== Interação entre DA-1 e DA-2

#tab([Interação entre as decisões],
  tabela(
    colunas: (2.2cm, 2.2cm, 4.4cm, 1fr),
    [Decisão A], [Decisão B], [Efeito (pré-requisito, sinergia ou conflito)], [Razão / evidência],
    [DA-1], [DA-2], [Pré-requisito], [Autorização de emissão/transporte/objeto e identidade confiável impedem que o novo S3 contorne a política ou consuma corpo antes do controlo. EV-44, H-14/H-15],
    [DA-2], [DA-1], [Sinergia], [_Streaming_ e admissão antes do corpo podem reduzir recursos de pedidos indevidos, não substituem autenticação do _peer_. H-15/H-18],
    [DA-1], [DA-2], [Conflito], [TLS/assinatura/_queries_ podem degradar latência/CPU enquanto DA-2 procura reduzir recursos, U25 G e tempos equivalentes têm de passar por avaliação. EV-45, H-18. Medido na MF: U25 sem erros (razão 0,58), S21 e U10 dentro do alvo. O conflito não se materializou neste corpus.],
    [DA-2], [DA-1], [Dependência de consistência], [Domínio escolhe quando um _media_ passa a ser utilizável. _Hash_/_cache_/limpeza incorretos podem violar isolamento apesar de TLS válido. EV-44, H-16],
  ),
)

== Plano de medição

#tab([Plano de medição],
  tabela(
    colunas: (1.6cm, 3.2cm, 3cm, 2.6cm, 2.4cm, 2.8cm),
    tamanho: 8pt,
    [Cenário], [Cenário de teste e carga], [Ambiente (máquina, recursos, versões)], [O que se regista], [Repetições e agregação], [Onde ficam os _scripts_ e os dados],
    [QS-01 e complemento QS-07], [Matriz pública/_host_/_peer_ Docker com dono/editor/leitor/outro, rotas `users`/`subscriptions`/_storage_, TLS por canal, _join_/revogação/falha/expiração WS. N1=50, J1=510, P1=200, L1/L2 testam recusa de 513/4097.], [Host oficial de avaliação Apple M4 Pro (Docker Desktop com 12 CPU e 7,7 GiB de RAM em VM Linux), _stack_ isolada `picturas-nfr`, commit de teste `d6b4497d` (código de aplicação idêntico a `0523102`). Diagnóstico exploratório inicial em Ubuntu i7-13700H (EV-28). MF no mesmo _host_: _commit_ `c8a5e3d` (aplicação igual ao congelamento `9b4e87d`), `MED_WS_JOIN_FORMAT=v2` e variáveis TLS do plano §6.], [Tentativas e controlos positivos, estado/bytes/eventos, _timings_, falhas de rede/TLS/domínio separadas, fila/CPU/RSS/latência, sem segredos.], [Três repetições por caso materializado e janelas WS de 30 s. _Raw_/mediana/máximo sem p95 de três amostras. Preparação, admissão e janela distinguidas.], [Instrumento formal `evaluation/med.py` (congelado na versão `638516104ae9`), critérios em `evaluation/criteria.yaml`, casos em `cases/security.yaml`. Resultados brutos da baseline arquivados em `evaluation/results/BF-20261121T013224Z/`. Especificação em `docs/metricas.md` e `docs/planoMedicao.md`.],
    [QS-02], [100 normais (perfis/tamanhos/H-T/estados), nove C=3, coexistência separada com três _uploads_/600 pedidos leves. Formatos/fronteiras e ambos os transportes materializados. 1024 MiB/+1 byte só guarda funcional separada.], [Mesmo host oficial Apple M4 Pro (12 CPU, 7,7 GiB RAM), _stack_ `picturas-nfr`, commit `d6b4497d`. Gerador de carga em fluxo e coletores de monitorização executados fora dos contentores Node medidos.], [RSS absoluto/incremento/retido, _cgroup_ e pico simultâneo, CPU/rede/disco/temporários, $t_0$/$t_"send"$/$t_"ready"$/$t_"hash"$/$t_"cleanup"$, integridade, nomes/versão/quota, OOM/erros e pedidos leves.], [Cinco tentativas por estrato, três rodadas C=3 e três pares de coexistência, conservar falhas e denominador. Memória do grupo não é dividida por três. U25 compara com/sem carga na mesma campanha.], [Instrumento `evaluation/med.py` (v`638516104ae9`), gerador de _streaming_ HTTP com ficheiros PAD/reais. Resultados brutos da baseline formal arquivados em `evaluation/results/BF-20261121T013224Z/`. Especificação e critérios em `docs/metricas.md` e `docs/planoMedicao.md`.],
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
    colunas: (1.1cm, 1.6cm, 1fr, 3.2cm, 2.2cm, 2.2cm, 2.8cm, 1.4cm),
    tamanho: 7pt,
    [ID], [Tipo], [Métrica (o que se mede, unidade)], [Antes (Baseline BF)], [Mínimo aceitável], [Valor-alvo], [Depois (MF)], [Atingido?],
    // RNF 1
    [S01], [Principal], [Efeitos indevidos entrada pública (recursos de outro utilizador)], [36/45 admitidos (12 de 15 casos, 80%)], [0], [0], [0/45 admitidos], [Alvo],
    [S02], [Principal], [Efeitos indevidos chamada direta API interna (host e rede Docker)], [54/60 admitidos (9 de 10 casos, 90%)], [0], [0], [0/60 admitidos], [Alvo],
    [S03], [Principal], [Operações indevidas no storage/signer (originais e resultados)], [24/24 admitidos (4 de 4 casos, 100%)], [0], [0], [0/24 admitidos], [Alvo],
    [S04], [Principal], [Eventos protegidos ou entradas em sala WS sem autorização], [15/15 admitidos (5 de 5 casos, 100%)], [0], [0], [0/15 admitidos], [Alvo],
    [S12], [Principal], [Tempo de corte da receção WS após revogação (ms)], [sem corte (>30 s, 263 eventos após revogação)], [$<= 5000$ ms], [$<= 2000$ ms], [1125 ms, 0 eventos após o limite], [Alvo],
    [S16], [Principal], [Acessos indevidos às bases de dados MongoDB], [63/72 admitidos (87,5%)], [0], [0], [0/72 admitidos], [Alvo],
    [S17], [Principal], [Acessos indevidos ao broker RabbitMQ e ao S3], [42/45 admitidos (14 de 15 casos, 93,3%)], [0], [0], [0/45 admitidos], [Alvo],
    [S18], [Principal], [Portas de serviços internos publicadas no host], [12 portas em 10 serviços (todas as interfaces)], [0 fora de _loopback_], [0 publicadas], [0 publicadas (só o nginx)], [Alvo],
    [S05], [Guarda], [Operações legítimas concluídas com sucesso (%)], [45/45 (100%)], [100%], [100%], [45/45 (100%)], [Alvo],
    [S21], [Guarda], [Sobrecarga de latência em pedidos leves ($Delta$ da mediana)], [6,1 ms / 3,5 ms (medianas de referência)], [$<= +10$ ms], [$<= +5$ ms], [5,5 / 5,3 ms ($Delta$ −0,7 / +1,9 ms)], [Alvo],
    // RNF 2
    [U01], [Principal], [Pico de memória adicional por serviço Node no upload (MiB)], [1976 / 1011 / 1001 MiB (500 MiB), gateway morreu 12×], [$<= 64$ MiB], [$<= 32$ MiB], [45,4 MiB (máx.), nenhum processo morreu], [Mínimo],
    [U20], [Principal], [3 uploads simultâneos de 500 MiB em concorrência (C=3)], [0/3 nas 3 rondas (OOM em todas as rondas)], [3/3 sem OOM], [3/3 nas 3 rondas], [3/3 nas 3 rondas, 0 OOM], [Alvo],
    [U19], [Principal], [Recurso gasto antes de recusar upload sem token], [+966 MiB gastos, 401 após 10,6 s (500 MiB recebidos)], [$<= 8$ MiB], [$<= 100$ ms pós-cabeçalhos], [+0,1 MiB, 401 aos 26 ms], [Alvo],
    [U18], [Principal], [Recusa correta de uploads com parâmetros inválidos (%)], [15/21 (71%), casos I1 e I6 geram 502 + OOM], [100%], [100%], [21/21 (100%), 0 OOM], [Alvo],
    [U04], [Principal], [Memória adicional do nginx e SeaweedFS no upload (MiB)], [+0,4 / +619 MiB máx. (mediana +585 MiB)], [$+<= 128$ / $+<= 256$ MiB], [$+<= 64$ / $+<= 128$ MiB], [+0,5 / +142,6 MiB máx. (5/5 amostras válidas)], [Mínimo],
    [U08], [Principal], [Disco temporário por componente e resíduos após envio], [500 MiB no nginx, 500 MiB no `projects`. 0 resíduos (cumpre o mínimo na BF)], [$<= C times (F + 16 "MiB")$, 0 resíduos], [$<= 16$ MiB/upload, 0 resíduos], [0 MiB em todos os componentes, 0 resíduos], [Alvo],
    [U09], [Guarda], [Tempo de aceitação após fim do envio do corpo (ms)], [14/20 falharam (500 MiB), aceites mediana 6171 ms], [$< 3000$ ms], [$< 1000$ ms], [20/20 aceites, máx. 806 ms], [Alvo],
    [U25], [Guarda], [Pedidos leves durante uploads concorrentes (erros / latência)], [6 erros (2 por par). Gateway sofreu OOM nos 3 pares], [0 falhas, $<= 1,10 times "controlo"$], [$<= "controlo"$], [0 erros, razão máx. 0,58], [Alvo],
    [U15], [Guarda], [Integridade SHA-256 do ficheiro original armazenado (%)], [86/86 (100%)], [100%], [100%], [100/100 (100%)], [Alvo],
    [U17], [Guarda], [Uploads válidos aceites e concluídos com sucesso (%)], [86/100 (86%)], [100%], [100%], [100/100 (100%)], [Alvo],
    [U10], [Guarda], [Mediana do tempo total por estrato (10/100/500 MiB, perfil, H/T, frio/aquecido), face à BF], [Medianas por estrato, 500 MiB (H): 8440–8904 ms, (T): 0 aceites (2 estratos sem base)], [$<= 1,10 times "BF"$ em cada estrato], [$<= "BF"$ em cada estrato], [razão máx. 0,89 (18 estratos com base), 500 MiB: 3,7–4,1 s], [Alvo],
  ),
)
]

A coluna «Depois (MF)» é a medição final oficial `MF-20261125T153646Z` (EV-55), comparada com a BF pelo `med.py compare` sem avisos de comparabilidade (mesmo _host_, corpus, critérios, casos e instrumento). A primeira MF, `MF-20261125T135356Z` (EV-54), fica no repositório e é discutida nas ameaças à validade.

*Análise dos resultados* (por requisito não funcional):

*CAND-1: Segurança.* Todas as métricas principais cumprem o alvo. Os efeitos indevidos admitidos passaram de 36/45, 54/60, 24/24, 15/15, 63/72 e 42/45 na BF para 0 nos mesmos casos (S01–S04, S16, S17). Deixou de haver portas internas publicadas (S18) e a receção WS é cortada 1125 ms depois da revogação (S12), quando na BF não havia corte. As guardas mostram que a proteção não bloqueou o uso legítimo (S05 45/45) e custou pouco em latência (S21: −0,7 ms em `get_project`, +1,9 ms em `get_user`). A matriz de efeitos confirma-se no sentido previsto: o custo de desempenho da DA-1 existe mas é pequeno, e a dependência da `projects` reduziu a disponibilidade do WS numa falha. Esse custo foi gerido com a suspensão do contexto (decisão 53), que mantém a regra de nunca emitir sem autorização válida. «0 admitidos» refere-se ao corpus finito de casos materializados, não à ausência de qualquer vulnerabilidade. Ficam declarados os residuais JWT-C1, SESS-C1 e LINK-C1.

*CAND-2: Eficiência no _upload_.* O pico adicional nos serviços Node caiu de 1976 MiB, com o _gateway_ a morrer 12 vezes, para 45,4 MiB, e três _uploads_ simultâneos de 500 MiB passaram nas três rondas sem OOM (U20). U19, U18 e U08 cumprem o alvo, e as guardas também (U09, U25, U15, U17, U10). Dois alvos não foram atingidos:
- *U01* fica no mínimo (45,4 MiB, alvo 32): o pico restante está no `img_storage`, nos _buffers_ por parte _multipart_ do adaptador do POST antigo, no estrato frio de 500 MiB, já reduzido pela recolha de memória depois de cada parte (decisão 45).
- *U04* fica no mínimo (SeaweedFS +142,6 MiB, alvo 128): o pico é memória viva do SeaweedFS 4.47. Ler em janelas de 4 MiB com `GOGC=25` (decisão 33) baixou o valor de cerca de +860 MiB. `GOMEMLIMIT` reduzia mais, mas aumentava o tempo de _upload_ em cerca de 70%.

A matriz de efeitos previa uma possível perda de latência na DA-2 e aconteceu o contrário: o tempo pós-envio passou de uma mediana de 6171 ms (com 14/20 falhas) para um máximo de 806 ms, e o tempo total ficou abaixo da BF em todos os estratos (500 MiB: de 8,4–8,9 s para 3,7–4,1 s). Isto deve-se a o _hash_ ter saído do caminho até _ready_ (o seu custo continua, em segundo plano) e a o armazenamento deixar de parar em cerca de 7 GiB (D-22). O risco de estados adicionais confirmou-se com o defeito do _hash_ órfão (decisão 51), encontrado e corrigido antes da MF.

*Ameaças à validade:*
- *Um só _host_ e amostras pequenas.* BF e MF correram no mesmo Apple M4 Pro (Docker Desktop, 12 CPU, 7,7 GiB), o que torna a comparação válida mas limita a generalização. Há 5 tentativas por estrato, 3 rondas C=3 e 3 pares de coexistência. Os resultados são medianas e máximos, sem intervalos de confiança.
- *Duas MF.* A MF1 cumpriu todas as métricas exceto a guarda U10, com razões 1,22 e 1,12 em dois estratos de 10 MiB (+56 e +27 ms). O código era o mesmo da EXP completa, onde esses estratos deram 0,94, e nessa janela até o envio do lado do cliente ficou mais lento, o que aponta para ruído do _host_ (inferido, não provado). Antes de repetir, fixou-se em _commit_ a regra de que a segunda MF completa seria a oficial para *todas* as métricas, fosse qual fosse o resultado (decisão 59). Ambas são reportadas. A repetição de uma campanha depois de ver um resultado é uma ameaça de seleção. A mitigação foi a regra prévia e a repetição integral, não só da métrica falhada.
- *Instrumento.* O `med.py`, os critérios e os casos da MF têm os mesmos _hashes_ que o instrumento final registado na BF. As únicas diferenças de execução são as previstas no plano §6 (`MED_WS_JOIN_FORMAT=v2` e TLS nos canais de dados), com o valor por omissão igual ao da BF.
- *Âmbito das métricas de _upload_.* As métricas oficiais medem o POST antigo através do adaptador (D-06). O fluxo novo (PUT direto) foi provado pela conformidade e por medições EXP, fora desta comparação.
- *Amostragem e tetos.* A U08 amostra o disco a cada 100 ms e pode perder picos mais curtos. Os tetos WS e as 3 vagas de _upload_ são valores configurados e exercitados pelo corpus, não capacidade demonstrada.

== Preservação funcional

#tab([Preservação funcional e testes de regressão],
  tabela(
    colunas: (2.4cm, 3.8cm, 2.8cm, 3.2cm, 1fr),
    tamanho: 8.5pt,
    [Zona alterada], [Testes de regressão existentes (`Tools/video/tests`, `projects/tests`, …)], [Lacunas de teste], [Testes acrescentados], [Resultado (imagem e vídeo)],
    [DA-1: confiança/API/ACL], [`projects/tests/video-pipeline.test.js`, `process-batch.test.js`, `frame-extraction.test.js`: cobrem regras/_commit_ de processamento], [Não são testes _end-to-end_ de mTLS/JWT/_owner_/serviço/_billing_/rotas legítimas], [`b4-route-matrix.py`, `b4-identity.py`, `b4-routes.py` (controlo legítimo e recusas por linha da matriz de rotas), `b4-functional.py`, `mtls-pki/b5-mtls.py`, `b5-functional.py`, `b5-guard.sh`, `mtls-pki/b1-smoke.py`, `users-quota.py`, `operations/b11-functional.py`], [Passam na verificação final (25/11, EV-53): identidade 92/92, rotas 636/636, mTLS 147/147, funcional B5 10/10, guarda 14/14, quota 10/10, B11 21/21. MF: S05 45/45.],
    [DA-1: WS/sessões], [Testes de vídeo cobrem produtor/progresso em âmbito limitado, não política de sala], [Falta autorização de _room_/expiração/permanência, eventos pessoais, reconexão e importação], [`websocket/authorization.test.js` e restantes unitários do motor, `client-reconnect.test.js`, `b8-functional.py`, `b8-outage.py`, `b8-wire-limits.py`, `b8-load.py` (N1/J1/P1/L1/L2), `sessions/` (emissor, perfil, cliente, mutações, `b9-functional.py`, `b9-browser.py`)], [Passam depois da decisão 53: funcional 33/33, indisponibilidade 5/5, limites de _wire_ 36/36, cargas sem eventos após o corte. Sessões 20/20 e 35 verificações no _browser_.],
    [DA-2: HTTP/_upload_/_storage_], [Suites do orquestrador/worker validam semântica a jusante], [Não provam _buffers_ limitados, estados de _upload_, _rollback_ S3/DB, _hash_ assíncrono ou compatibilidade HTTP], [`upload/b6-adapter.py`, `b6-races.py`, `b6-capacity.py`, `b7-flow.py`, `b7-signature.py`, `b7-lifecycle.py`, `b7-late-cleanup.py`, `ul10-probe-limits.py`, `b12-hash-orphan.py`, `b7-browser.py`], [Todos passam. `b12-hash-orphan.py` falhava antes da decisão 51 (2 vagas presas) e passa depois. MF: U15 e U17 100/100.],
    [DA-2: _pipeline_/resultados], [`test_video_processor.py` e `test_frame_extraction.py`, testes Node de vídeo/extração], [Falta combinação real com transportes/PKI novos, cargas e imagens mistas], [F01 nas imagens da _stack_ (`run-f01.sh`), `regression/b12-regression.py` de ponta a ponta (8 ferramentas PIL num lote, _watermark_, 7 ferramentas de IA, vídeo pelos dois transportes com _trim_/_speed_, _preview_, projeto misto, legendas, extração, quota, partilhas, _presets_, subscrição, eliminação de conta), `regression/b12-browser-export.py`], [F01 11/11 Node e 74/74 vídeo, regressão 105/105, exportação ZIP/PDF 4/4. A regressão encontrou um defeito anterior à fase (o _watermark_ falhava sempre), corrigido (decisão 47).],
    [Ambos: legendas/IA], [`test_subtitles.py` usa _recognizer_ simulado, FFmpeg real, _no-op_ e regras já testáveis], [Simulação não avalia Whisper real nem mTLS `expand_ai`→_mock_], [`b12-regression.py` (legendas e IA na _stack_ real), `mtls-pki/b5-functional.py` (`expand_ai` generativo por mTLS até ao `generative-mock`)], [Passam. A qualidade da transcrição continua sem corpus de referência (H-09).],
  ),
)

#tab([Riscos para a preservação funcional e mitigação],
  tabela(
    colunas: (3.4cm, 3.2cm, 4cm, 3.2cm),
    tamanho: 8.5pt,
    [Risco], [Funcionalidade afetada (imagem / vídeo)], [Mitigação], [Teste de regressão],
    [Novo controlo recusa _callers_ legítimos/partilhas/limpeza de conta], [Imagem e vídeo], [Matriz por serviço/operação/identidade e controlo positivo, autorização de domínio preservada], [`b4-routes.py` (controlo legítimo por linha da matriz, 636/636), `b5-functional.py` (limpeza de conta `users` → `projects`), S05 100% na MF],
    [Adaptador ou transporte novo altera API, versão ou quota], [Vídeo e projetos mistos], [204/`X-Project-Version` legado, CAS/conflito definido, nenhuma cobrança no _upload_, domínio/_commit_ comum], [`video-pipeline.test.js`, `process-batch.test.js`, `b6-adapter.py` (204/`X-Project-Version`, quota, editor sim e leitor não, U24), `b6-races.py` (409), `b7-flow.py`, regressão 105/105],
    [_Bytes_ pendentes/errados entram em _preview_/_Apply_/_export_], [Imagem e vídeo], [Isolamento efetivo, confirmação idempotente e teste de cada fronteira de falha, não presumir transação S3/Mongo], [`frame-extraction.test.js`, `b7-lifecycle.py` (_staging_ privado, confirmação idempotente, reinícios em cada marcador), `b7-signature.py`, `b6-races.py`, U15/U17 100% na MF],
    [_Hash_ em falta confunde _cache_ ou oculta trabalho posterior], [_Preview_ e vídeo], [Leitura/escrita de _cache_ suspensas ou isolamento provado, medir $t_"hash"$ e consumo completo], [`b7-lifecycle.py` (UL-09: _hash_ concluído depois de reinício), `b12-hash-orphan.py` (bomba de _hash_ não bloqueia com _media_ apagada)],
    [Alterar efeitos, ordem, áudio, legendas ou extração], [Imagem/vídeo/misto], [Manter _pipeline_ por projeto, _trim_/_speed_ por vídeo e extração terminal/única, sem novos efeitos], [`Tools/video/tests/` (F01 74/74), `b12-regression.py` (efeitos, ordem, _trim_/_speed_, legendas, extração, 105/105)],
    [Cortar WS deixa _frontend_ incoerente ou troca anónimo], [Sessões/progresso de ambos], [Reconexão explícita, nova autorização por sala, preservar identidade/duas vias válidas], [`client-reconnect.test.js`, `b8-outage.py` (5/5), `b9-browser.py` e testes de sessões (AR-01–AR-12), contrato WS-T02/T04 revisto (decisão 53)],
  ),
)

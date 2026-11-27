#import "../template.typ": *

#set heading(numbering: "A.1.")
#counter(heading).update(0)

= Instruções de execução

#orientacao[
  Indiquem os passos mínimos para lançar a solução a partir do repositório (pré-requisitos, comandos, projeto de teste) e
  para repetir as medições (antes e depois do _refactoring_) (_scripts_, dados, ambiente). Quem avalia, ou a equipa na fase seguinte, deve
  conseguir repetir o que descrevem sem ajuda. No glossário, definam os termos específicos do projeto ou da disciplina
  usados no relatório.
]

Os comandos estão em _shell_ POSIX (macOS ou Linux, no Windows, Git Bash ou WSL). Todos partem da raiz do
repositório entregue.

== Pré-requisitos

#tabela-campos(
  [Docker], [Docker Desktop ou Docker Engine com Compose v2. Pelo menos 8 CPU e 8 GiB de RAM atribuídos ao Docker. A primeira construção ocupa cerca de 15 GiB de disco e demora 15 a 30 minutos.],
  [Medição], [Python 3 com `venv`, `ffmpeg`/`ffprobe` no PATH e pelo menos 60 GiB livres (corpus de teste e imagens da _stack_ isolada).],
  [Portas], [`8080` livre (entrada única por nginx). A _stack_ de medição usa a `28080`.],
  [Dados de teste], [Vídeos de exemplo em `samples/video/` (com fala, sem fala, `.mov`, corrompido e acima do limite _free_), descritos no respetivo `README.md`.],
)

== Lançar a solução

*Solução de base (BF, _commit_ `0523102`).* Não precisa de segredos externos:

```bash
git switch --detach 0523102
docker compose up -d --build
```

*Solução refatorada (branch `fase2-refactor`).* Os segredos e os certificados deixaram de estar no repositório
(DA-1, B1): cada instalação gera os seus, num diretório fora do repositório, que nunca se copia entre
computadores.

```bash
git switch fase2-refactor
export PICTURAS_SECRETS_DIR=$HOME/.picturas-secrets   # exportado em todas as shells usadas
ops/secrets.sh init                                   # segredos por serviço
ops/pki.sh init                                       # CA da instalação e certificado por serviço
ops/pki.sh check && docker compose up -d --build
```

Sem `PICTURAS_SECRETS_DIR` exportado, o `docker compose` recusa arrancar (intencional). Em ambos os casos, a
aplicação fica em `https://localhost:8080` (aceitar o certificado local). Depois de reconstruir o _frontend_,
correr `docker compose restart nginx` para evitar um 502.

*Projeto de teste.* Registar uma conta (ou usar o modo anónimo), criar um projeto, carregar imagens e vídeos de
`samples/video/`, montar um _pipeline_ com efeitos comuns, `trim`/`speed`, legendas e extração de fotogramas, e
aplicar. O progresso chega pelo WebSocket e os resultados descarregam-se em ZIP.

== Testes de regressão e de conformidade

```bash
# Worker de vídeo no host (precisa de ffmpeg/ffprobe)
cd Tools/video && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q tests && cd ../..

# Regressão F01 (testes Node e de vídeo) nas imagens do produto, numa stack já montada
tests/conformance/run-f01.sh <projeto-compose>
```

Os testes de conformidade das decisões estão em `tests/conformance/<grupo>/` e guardam o resultado bruto em
`tests/conformance/results/<AAAA-MM-DD>/`. Correm sempre contra uma _stack_ própria (`picturas-dev` ou
`picturas-nfr-exp`) e só com _fixtures_.

== Repetir as medições (BF e MF)

O instrumento é `evaluation/med.py`, congelado na versão `638516104ae9`. Não se altera `med.py`, `medlib/`,
`criteria.yaml` nem `cases/` entre a BF e a MF. As únicas alterações permitidas são as do plano §6 (formato do
_join_ WS e TLS nos canais de dados, por variáveis `MED_*` com o valor por omissão igual ao da BF), registadas
com `med.py freeze`. O `manifest.json` de cada campanha guarda os _hashes_ do instrumento. O
`med.py` monta a sua própria _stack_ isolada (`picturas-nfr`), sem tocar nos volumes nem nas portas da
instalação de desenvolvimento.

```bash
cd evaluation
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.med.example .env.med
.venv/bin/python med.py preflight --campaign BF   # verifica Docker, CPU, RAM e disco
.venv/bin/python med.py corpus                    # gera o corpus (~2,5 GiB, guardar até à MF)
.venv/bin/python med.py stack up                  # build e arranque da stack isolada
.venv/bin/python med.py run --campaign BF         # campanha completa (~2-3 h)
.venv/bin/python med.py stack down                # ATENÇÃO: down -v (apaga os volumes da stack isolada)
```

O `med.py stack up` e o `stack down` fazem `docker compose down -v` do projeto isolado marcado em
`evaluation/.run/stack.json`. Para parar uma _stack_ sem perder dados usa-se `docker compose -p <projeto> down`,
sem `-v`.

*Medição final (MF).* No *mesmo computador* da BF, com o código refatorado e `PICTURAS_SECRETS_DIR` exportado. O
`.env.med` não se copia do exemplo: `ops/secrets.sh med-render` escreve-o fora do repositório (em
`$PICTURAS_SECRETS_DIR/med-exp.env`) e `evaluation/.env.med` é uma ligação simbólica para esse ficheiro
(`ops/secrets.sh med-env` só imprime as credenciais `MED_*`). Sem as credenciais de administração e
por serviço, esses casos ficam `INCONCLUSIVO`. As variáveis de ambiente prevalecem sobre o ficheiro:

```bash
export MED_COMPOSE_PROJECT=picturas-nfr MED_WS_JOIN_FORMAT=v2
.venv/bin/python med.py stack up                  # down -v só da picturas-nfr, build e arranque
.venv/bin/python med.py preflight --campaign MF   # exige >=60 GiB livres e árvore sem alterações
.venv/bin/python med.py run --campaign MF         # ~1 h
.venv/bin/python med.py compare results/BF-20261121T013224Z results/MF-<UTC>
```

A MF oficial é `MF-20261125T153646Z`. A primeira, `MF-20261125T135356Z`, fica no repositório e é reportada no
capítulo 10 (decisão 59).

O `compare` só classifica se o _host_, os limites, o corpus, os critérios, os casos e a versão do instrumento
forem iguais aos da BF. Caso contrário, todas as métricas ficam `COMPARACAO_INVALIDA`. Medições noutros
computadores usam `--campaign EXP` (com `MED_COMPOSE_PROJECT=picturas-nfr-exp`) e nunca entram no `compare`.
Cada campanha fica em `evaluation/results/<CAMPANHA>-<UTC>/`: `manifest.json` (commit, _host_, Docker, imagens,
corpus), `raw/<métrica>.jsonl` (uma linha por tentativa, sem segredos), `summary.json` e `report.md`.

= Glossário

#tabela(
  colunas: (4cm, 1fr),
  tamanho: 8.5pt,
  [Termo], [Definição],
  [_Apply_], [Comando que aplica o _pipeline_ do projeto a todos os _media_ (`POST …/process`). É aí que se cobra a quota de operações.],
  [BF / MF / EXP], [Campanhas do `med.py`: _baseline_ formal (antes do _refactoring_), medição final (depois, no mesmo _host_) e medição experimental (outro computador ou verificação intermédia, fora da comparação).],
  [Bloco (B0–B12)], [Unidade de implementação do plano de refatoração (`docs/refactor-plano.md`), com dependências e critério de aceitação próprios.],
  [CAND-n], [Candidato a requisito não funcional (capítulo 6), derivado de um cenário de qualidade prioritário.],
  [Candidato (_upload_)], [Objeto S3 imutável, numa chave nova e única que o cliente não pode escrever, sobre o qual se valida o ficheiro antes do _commit_ no projeto.],
  [Cenário de qualidade (QS-nn)], [Especificação verificável de um atributo de qualidade com seis elementos: fonte, estímulo, artefacto, ambiente, resposta e medida da resposta.],
  [Classe A / B / C], [Classificação das táticas: A, _refactoring_ puro, B, alteração visível que é o objeto da melhoria. C, funcionalidade nova, rejeitada nesta fase.],
  [Corpus], [Conjunto fixo de ficheiros de teste (PAD e vídeos reais) gerado pelo `med.py` e reutilizado sem alterações na BF e na MF.],
  [Corte (WS)], [Fim da receção de eventos protegidos de um projeto por uma ligação WebSocket depois de a autorização cessar, medido pela S12.],
  [DA-n], [Decisão arquitetural registada ao estilo ADR (capítulo 8): contexto, tática, alternativas, consequências e desvios.],
  [EV-nn / H-nn], [Evidência verificável (código, configuração, mensagem, medição ou documento) e hipótese ainda por confirmar, registo no Anexo C.],
  [Guarda], [Métrica que não pode piorar além do mínimo aceitável (e.g., S05, U15), uma guarda que falhe invalida a melhoria.],
  [JWT HS256 / RS256], [_Token_ de sessão do utilizador (assinatura simétrica) e identidade interna de curta duração emitida pelo _gateway_ (assinatura assimétrica, ≤30 s, com audiência e contexto).],
  [_Loopback_], [Interface local (`127.0.0.1`): uma porta ligada só a ela não é alcançável a partir de outras máquinas nem de outros contentores.],
  [`med.py`], [Instrumento automatizado de medição dos dois RNF (`evaluation/`). Executa os casos, recolhe dados brutos e classifica-os face a `criteria.yaml`.],
  [mTLS], [TLS mútuo: cliente e servidor apresentam certificados da CA da instalação. A autorização exige também a identidade específica do par e a operação permitida.],
  [OOM], [_Out of memory_: o processo é terminado por exceder o limite de memória do contentor.],
  [PKI / CA], [Infraestrutura de chaves da instalação: uma autoridade de certificação local (365 dias) e um certificado por serviço (30 dias), geridos por `ops/pki.sh`.],
  [Principal (credencial)], [Identidade própria de cada serviço perante MongoDB, RabbitMQ e S3, com privilégio mínimo para as suas operações.],
  [RSS], [_Resident set size_: memória física ocupada por um processo. Base das métricas U01 e U04.],
  [Sala (WS) / _join_], [Canal Socket.IO de um projeto. O _join_ é o pedido de entrada, autorizado pela `projects`.],
  [_Spike_], [Ensaio curto e descartável (SP-01 a SP-11, bloco B0) para confirmar uma hipótese técnica antes de implementar.],
  [_Spool_], [Escrita do corpo integral de um pedido em disco temporário antes de o processar (medido pela U08).],
  [_Staging_], [Área controlada do S3 onde ficam os _bytes_ de uma tentativa de _upload_ até à validação. Nunca visível como _media_ do projeto.],
  [TAT-nn], [Tática arquitetural candidata (capítulo 7), ligada a um cenário e classificada A/B/C.],
  [Tentativa de _upload_], [Registo, numa coleção própria, de um carregamento em curso (pedido, PUT, validação, confirmação), com prazos e limites.],
)

= Registo de Evidências e Hipóteses

As evidências (`EV-01` a `EV-55`) e hipóteses (`H-01` a `H-18`) citadas ao longo deste relatório têm origem na análise de arquitetura, inspeção de código, dados de execução e literatura dos Exercícios 6 e 7. O catálogo seguinte identifica a sua localização exata e o facto factual ou previsão técnica que sustentam.

#paisagem[
#tab([Registo de Evidências (EV-01 a EV-55)],
  tabela(
    colunas: (1.8cm, 3.4cm, 6.2cm, 1fr),
    tamanho: 7.5pt,
    [ID], [Tipo], [Localização / Fonte], [O que demonstra / Registo],
    [EV-01], [Histórico/configuração], [`git rev-parse HEAD`, `git rev-parse 0523102`, `git log -6`, `git diff --name-only 0523102 HEAD`, registo], [Identifica checkout e base da aplicação. Mudanças locais anteriores limitadas a documentos e infraestrutura de agentes.],
    [EV-02], [Documento], [Enunciado HTML, v1.1: Objetivo, Contexto, tarefas 0–3 e Resultado Esperado], [Exige análise global/vídeo, sequência completa, evidências, alternativas, matriz e preservação funcional. Bloco 2 trata escolhas de RNF.],
    [EV-03], [Documento], [HTML de apoio, introdução e padrões 1–7], [Distingue níveis de análise. Identifica Pipeline Monolith local e Competing Consumers como alternativa.],
    [EV-04], [Documento], [PDF PL1-G4, v2.0, pp.1–10, 11–33, 34–46, 49–61, 62–67, 70–76], [Domínio, casos de uso, 83 requisitos, 15 entradas de qualidade em §5.2, RNF herdados, decisões e limitações. DA-01/06 explicam concentração e duplicação, números de desempenho são históricos.],
    [EV-05], [Documento], [Diretrizes Fase 2, v1, pp.1–3], [Dois RNF distintos, ISO/IEC 25010:2011, refactoring com preservação funcional, baseline antes de alterar, medições repetíveis e IA documentada.],
    [EV-06], [Diagrama], [SVG global e PlantUML, linhas 24–102 da fonte], [Representação global existente, vídeo realçado, volume e filas. Inspeção visual e confronto com código.],
    [EV-07], [Configuração], [`nginx/nginx.conf:12–21, 24–39, 63–100`], [Limite 1100m, TLS, destinos frontend/API/WS/S3.],
    [EV-08], [Código], [`apiGateway/app.js:25–27`, `auth/auth.js:3–41`, `routes/projects.js:17–26, 409–499, 506–530, 574–607`], [Prefixos públicos, JWT, buffers de upload, headers de identidade/versão e encaminhamento do Apply.],
    [EV-09], [Configuração], [`docker-compose.yaml:39–227, 255–273, 468–567`], [Implantação, portas, três MongoDB, volume partilhado, um serviço de vídeo, cache Whisper, rede bridge, frontend e WS. Não configura autoscaling.],
    [EV-10], [Código/modelos], [`projects/models/project.js:3–57`, `models/process.js:3–15`, `models/result.js:3–11`, `app.js:8–13,34–37`, `routes/projects.js` (2732 linhas), `users/app.js:12`, `subscriptions/app.js:9`], [Pipeline/media/token/versionamento e dados por serviço. Camadas existentes com lógica concentrada nas rotas.],
    [EV-11], [Código], [`imageStorageService/server.js:9–12`, `route/upload.js:6–31`, `route/images.js:10–27`, `services/storage.js:3–38`, `uploadImage.js:5–21`, `getPresignedUrl.js:6–26`], [Buffer de upload, bucket partilhado com prefixos por utilizador/projeto/estágio, UUID, URLs de uma hora e fachada sem middleware de autenticação próprio.],
    [EV-12], [Código], [`projects/utils/video.js:11–48, 84–142, 145–209`, `routes/projects.js:1267–1393`], [Tipos, limites, ffprobe em temporário, filtragem de efeitos, validação da extração, metadados e operações.],
    [EV-13], [Código], [`projects/routes/projects.js:1397–1465, 1469–1516`, `utils/video.js:175–202`], [Inserção/reordenação validam extração única e terminal, novas ferramentas entram antes dela.],
    [EV-14], [Código/mensagem], [`projects/routes/projects.js:1521–1677, 1744–1808`, `utils/processBatch.js:1–14`, `utils/project_msg.js:26–39`], [Apply, quota, preparação de fontes, barreira de registo, bifurcação, pedido completo de vídeo e HTTP 201 de despacho.],
    [EV-15], [Código], [`projects/routes/projects.js:169–255, 484–524`, `utils/rabbit_mq.js:11–54`, `Tools/utils/rabbit_mq.py:26–41`, `Tools/utils/tool_msg.py:41–80`], [Cadeia de imagens, publicação sem confirmação, ack do callback Node sem await, auto-ack Python e correlação/contrato dos erros.],
    [EV-16], [Código/mensagem], [`Tools/video/video.py:45–74, 76–124, 126–180`], [Consumidor com prefetch 1 e heartbeat 0. Progresso, correlação, publicação, erros tratados e ack final. Não define persistência ou publisher confirms.],
    [EV-17], [Código], [`Tools/video/video_processor.py:97–164, 167–278, 286–369`], [Trim/speed, decode/PIL/encode ordinário, progresso, ficheiro temporário, `os.replace`, normalização, estágios e exceções ao preview curto.],
    [EV-18], [Código], [`Tools/video/effects.py:11–79`, `Tools/brightness/brightness.py:29–42`, restantes ferramentas PIL em `Tools/`], [Funções e registo local, parâmetros comuns e duplicação de operações PIL. Workers de imagem acoplados aos helpers de mensagens.],
    [EV-19], [Código], [`Tools/video/subtitles.py:15–22, 33–82`, `video_processor.py:319–369`], [Reconhecimento local, cache por processo, no-op, sanitização de texto/tempos, renderização e ordem. Timeout de renderização não é timeout de trabalho completo.],
    [EV-20], [Código], [`Tools/video/frame_extraction.py:11–97`, `video_processor.py:294–315`], [Amostragem limitada, seeks no original ou timeline editada, folha de preview, manifesto e diretórios temporários.],
    [EV-21], [Código], [`projects/utils/frameResults.js:6–49`, `routes/projects.js:375–482, 972–1048`, `controllers/project.js:93–99`], [Validação/persistência por fotograma, rollback de melhor esforço, barreira/token, commit condicional, URLs e ZIP em memória.],
    [EV-22], [Código], [`wsGateway/index.js:17–35,54–124`, `utils/rabbit_mq.js:32–87`], [Rooms, tradução para eventos Socket.IO e reconexão do consumidor WS ao broker, não mantém histórico de progresso.],
    [EV-23], [Código], [`frontend/components/toolbar/toolbar.tsx:51–97`, `lib/projects.ts:47–61,446–478`, `app/dashboard/[pid]/page.tsx:88–132,300–315,430–448,841–875,894–927`], [Deteção de vídeo, ferramentas ocultas, estado local, progressos por vídeo, PDF oculto e overlay durante execução.],
    [EV-24], [Código/configuração], [`docker-compose.yaml:63–71,82–87,96–101,118–119,135–179,203–208,502–512`, `apiGateway/routes/projects.js:17–20`, `projects/routes/projects.js:72–85`, `middleware/shareAuth.js:4–42`, `utils/caller.js:3–12`, `users/utils/fieldCrypto.js:3–39`], [Portas e segredos em configuração versionada, TLS não validado, confiança interna, acesso normal e cifra de campos. Não se reproduzem valores secretos neste documento.],
    [EV-25], [Código], [`users/routes/users.js:46–73,130–171`, `projects/utils/video.js:205–209`, `routes/projects.js:1744–1808,2252–2353`], [Quota gratuita/premium, soma por vídeo, mapeamento 701→403, invalidação ao cancelar e reembolso só de `pendingAdvancedOps`.],
    [EV-26], [Código], [`projects/routes/projects.js:1082–1164,257–369`, `utils/cacheKey.js`], [Preview sem reserva de operações, chave por hash/ferramentas, cache persistente e seleção de tipo de media.],
    [EV-27], [Testes], [`Tools/video/tests/`, `projects/tests/`, `Tools/video/tests/test_subtitles.py:1–20,23–85`, `tests/conftest.py:11–30`], [Testes de efeitos, áudio, ordem, determinismo, falhas tratadas, legendas simuladas, extração e barreiras/tokens. Não cobrem todos os RNF.],
    [EV-28], [Execução], [Registo de 2026-11-09 e script], [Ambiente/serviços/hashes, 8 testes Node e 74 Python aprovados, ensaio misto por API, exportação MP4/ZIP e extração. Limitações e comandos de reprodução registados.],
    [EV-29], [Inventário/documento], [Inventário da leitura inicial com `rg --files docs`, `memory-bank/README.md`, `project.yaml`, `.specsmd/aidlc/context-config.yaml`, PDF PL1-G4, p.1, enunciado], [Regista a indisponibilidade inicial dos documentos anteriores, *resolvida nesta revisão por EV-34–EV-36*. O ID é preservado para rastreabilidade. Não representa uma fonte atualmente em falta nem requisitos Fase 2 já aprovados.],
    [EV-30], [Referência técnica], [RabbitMQ: confirmações, consulta 2026-11-09, secções de acknowledgements, requeue e publisher confirms], [Ack de consumo e confirmação de publicação são garantias distintas. Reentrega de pedidos não confirmados não demonstra processamento exatamente uma vez.],
    [EV-31], [Literatura], [Hohpe/Woolf: Pipes and Filters, Competing Consumers, consulta 2026-11-09], [Decomposição em etapas ligadas por canais. Múltiplos consumidores concorrentes numa fila, sem distribuição por broadcast.],
    [EV-32], [Norma/documento], [Ficha ISO/IEC 25010:2011, diretrizes p.2, PDF PL1-G4 pp.45–46], [Edição requerida, oito características e classificação dos RNF usados na análise. Não se mistura com a edição 2023.],
    [EV-33], [Documentação/configuração], [`README.md:85–176,438–483`, secções de execução/testes, `AGENTS.md`, `AUTHORS.md`, `samples/video/README.md`, `rabbitMQ/definitions.json:1–350`, `docker-compose.yaml:39–227,229–554`, Dockerfiles dos serviços e `Tools/video/`], [Topologia global, filas diretas/duráveis, origem de legendas/extração, 16 ferramentas implantadas e fila residual scale, modelos, backup Mongo, mock e instalação. ELK está comentado e não é uma capacidade ativa de observabilidade.],
    [EV-34], [Documento], [Requisitos anteriores, capa novembro de 2025, §§2–4 e 6.2–6.3, pp.19–26 (PDF 24–31), tarefas corretivas pp.33–34], [Catálogo direto de 21 RNF, critérios quantitativos, stakeholders, RF47 intercalado e lacunas de numeração, RNF45 não se reduz a persistência S3, RNF54 tem conflito entre descrição e fit criterion.],
    [EV-35], [Documento/diagramas], [Solução arquitetural anterior, capa janeiro de 2026, §2 (pp.2–13), §3 (pp.13–18), §§4–6 (pp.19–27), §§7–11 (pp.28–40), §12 (pp.41–44)], [Microserviços/REST/AMQP, MinIO histórico, camadas/vistas, mecanismos de dirty/versionamento/presença/presets, tokens/reembolso e avaliação histórica. Figuras 1 e 4 inspecionadas nas páginas PDF 38 e 44. Conclusões de conformidade não são certificações do checkout atual.],
    [EV-36], [Material letivo], [Aula 11: Architectural Styles, JM Fernandes, outubro de 2021, slides 2–8, 10–20, 22–25], [Estilo idealizado/realizado, catálogo por vista, camadas, pipelines incrementais versus batch, Publish–Subscribe e Client–Server/N-Tier. Referência a Fairbanks (2010), capítulo 14, é bibliografia dos slides, não uma obra consultada diretamente nesta revisão.],
    [EV-37], [Código de suporte herdado], [`projects/routes/projects.js:594–680,776–805,2170–2249,2522–2602`, `controllers/project.js:72–99`, `models/project.js:59–72`, `models/presence.js:15–20`, `utils/presence.js:6–94`, `users/models/preset.js:20–31`, `users/routes/presets.js:85–176,223–239`, `frontend/components/presets/presets-dialog.tsx:53–85`, `components/projects/share-dialog.tsx:76–103`, `components/operations-counter.tsx:5–25`, `providers/theme-provider.tsx:15–50`, `app/layout.tsx:36–44`], [UUID/partilha persistente e bloqueio por dirty. Versões condicionais, limite de presença e TTL. Presets persistentes/índice único/mínimo de duas ferramentas, atualização otimista ao aplicar, contador e tema. O assistente guarda previews no estágio S3 preview. Não há prova de expiração do objeto só porque o URL expira.],
    [EV-38], [Material fornecido], [Enunciado Bloco 2 e template, 1.1, 2026-11-04], [Secções 4–7, seis elementos dos cenários, dois candidatos, continuação de IDs e quantificação final após baseline. Originais organizados sem alterar bytes.],
    [EV-39], [Material fornecido], [Enunciado Ex. 7 e template, 3.0, 2026-11-17, incluindo Anexos A/B], [Cenários vêm do Bloco 2 sem redefinição. Pelo menos três táticas por cenário, classes A/B/C, duas DA, duas alternativas por DA, vistas/trade-offs/medição/regressão/IA. A versão 3.0 remove revisão cruzada.],
    [EV-40], [Verificação estática], [Manifesto de organização/comparação, `git diff --name-only 484be13 1d7103b` limitado a aplicação/Compose, caminhos registados], [Nenhuma diferença de aplicação nesses caminhos. Quatro novos materiais preservados por SHA-256. Não foi arrancada stack nem consultado runtime/volumes.],
    [EV-41], [Exploração histórica B14], [Índice de evidências, achados], [Ensaios Linux de 14/11: uploads/recursos, acessos com controlo, vídeo e uma interrupção. Há leitura de objeto verificada por hash no suplemento. Universo e limitações não se agregam ao B16 ARM.],
    [EV-42], [Exploração histórica B16: upload], [Auditoria dos JSON, originais e scripts, métricas §2.2], [14 uploads válidos observados. 500 MiB premium: três sucessos, pós-envio 6704,0–7976,6 ms, gateway até 2049,6 MiB absolutos. Outro caso free-500 registou 502/OOM. São pilotos Mac/ARM com pequeno n, não BF nesta máquina.],
    [EV-43], [Exploração histórica auditada: segurança], [Auditoria por caso, métricas §2.3], [G03/G04 verificam mutações no projeto da vítima, W01 recebeu evento sem token. G02/D06 têm asserções incompletas e G08/G09 serviço ausente/500: não os contar como efeito provado ou proteção. Não há taxa universal de bypass.],
    [EV-44], [Decisões e âmbito], [Ideias/justificação, histórico, upload, WS], [Par QC-06+QC-05 acordado como comunicado pelo utilizador. Escolhas técnicas individuais de identidade/mTLS/WS/PKI e UP-C1/C2/C3 A. UP-C4–C9 continuam não selecionadas e não há implementação/refactoring iniciado.],
    [EV-45], [Planeamento e recursos observados], [Plano, revisão, manifesto de host], [Host desta máquina/Luís selecionado, EVAL-B1/C1/R1/M1 A têm validação individual limitada, U25 é G. 60 dimensões de avaliação. BF/MF e calibração por executar, sem aprovação implícita dos 60 limiares.],
    [EV-46], [Código/testes, releitura estática], [Testes do orquestrador, vídeo, schemas, caller, WS, frontend], [Suites existentes de processamento/áudio/extração/legendas simuladas. Caller decodifica JWT sem verificar assinatura e WS não autoriza salas como no contrato proposto, frontend envia multipart. Não há novos testes executados nesta continuação.],
    [EV-47], [Referências primárias complementares], [ISO 25010:2011, fichas/resumos SEI Deriving Architectural Tactics e Security and Survivability, consulta 18/11], [Edição ISO exigida e ligação entre cenários, táticas e decisões. Consultados os resumos oficiais, não o livro SAIP nem o texto integral desses relatórios. O catálogo concreto utilizado é o Anexo A de EV-39.],
    [EV-48], [Inventário dos materiais consultados], [Quatro novos ficheiros e `docs/lectures/`, índice Ex. 7], [Não foram fornecidos no workspace os slides 9 nem as quatro folhas `Apoio/Taticas` citadas no Ex. 7. Usa-se o Anexo A incluído no HTML 3.0 e as fontes disponíveis. Não se simula leitura dos materiais ausentes.],
    [EV-49], [Revisão documental e releitura estática: 20/11/2026], [Verificação da revisão, checkout `405b6c0`, WS, caller e rotas], [QS-01 distingue tentativa de acesso de revogação, agora QS-07 complementar. Corrigem-se o sentido dos efeitos e as filas dos diagramas. Diff da aplicação vazio desde o início do Bloco 1 no âmbito registado, originais e registo anterior preservados. Não prova implementação, testes, acordo adicional ou baseline.],
    [EV-50], [Decisões antes de implementar: 21/11/2026], [`docs/refactor-handoff.md` §2.3 e §2.6, `docs/refactor-plano.md` §8, `docs/architecture/fase2-upload-ciclo-vida.md` (seleção de 21/11)], [UP-C4 a UP-C9 escolhidas (opção A em todas), dúvidas D-01 a D-15 respondidas e plano em blocos B0–B12. D-15: não há clientes reais e a entrega parte de um _reset_ geral, sem migração de sessões, contas ou _media_. Supera, neste ponto, o estado registado em EV-44.],
    [EV-51], [Implementação: _spikes_ e B1, 21–22/11/2026], [Branch `fase2-refactor`, _commits_ `02623a4` (B0) e `1ab09fa` (B1), `docs/refactor-spikes.md`, `tests/spikes/SP-01..SP-11/results/`, `tests/conformance/results/2026-11-21/` e `2026-11-22/`], [11 _spikes_ (6 suportados, 5 com limitações, que originaram D-16 a D-19). PKI e segredos fora do Git. Regressão F01 8/8 Node e 74/74 vídeo, `med.py` EXP S05 `--quick` = 100%. Não é a medição final (MF).],
    [EV-52], [Implementação B2–B12, 23–25/11/2026], [Branch `fase2-refactor`, integrado em `main` no _merge_ `e0a880a`. _Commits_ por bloco no capítulo 8, `docs/refactor-handoff.md` (§2.6 decisões 17–61, §3 estado dos blocos), `docs/refactor-matriz-rotas.md`, `docs/refactor-matriz-canais.md`], [Todos os blocos B0–B12 feitos, sem cortes da §7 do plano (decisão 29). Desvios face às decisões registados nas decisões da §2.6 e no capítulo 8. Congelamento antes da MF: `9b4e87d`.],
    [EV-53], [Conformidade completa e regressão: 25/11/2026], [`tests/conformance/run-b12.sh`, `tests/conformance/results/2026-11-25/B12-conf-*.txt` e `B12-conf-index.txt`], [Todas as suítes do plano §5 passam em `picturas-dev`: identidade 92/92, rotas 636/636, mTLS 147/147, WS 33/33 e indisponibilidade 5/5, sessões 20/20, B11 21/21, F01 11/11 Node e 74/74 vídeo, regressão de ponta a ponta 105/105, exportação 4/4. Pilotos B10 e testes B2 de acesso direto não repetidos (decisão 49).],
    [EV-54], [Primeira MF: 25/11/2026], [`evaluation/results/MF-20261125T135356Z/` (`report.md`, `compare.md`), diagnóstico na D-36 do _handoff_], [Todas as métricas cumprem, exceto a guarda U10 (razão máx. 1,22 em `free-10-H-frio`, 1,12 em `free-10-T-aquecido`). Mesmo código da EXP completa, onde esses estratos deram 0,94. Ruído do _host_ inferido, não provado. Reportada, não oficial (decisão 59).],
    [EV-55], [MF oficial: 25/11/2026], [`evaluation/results/MF-20261125T153646Z/` (`report.md`, `summary.json`, `compare.md` com a BF). Regra fixada antes de correr no _commit_ `e1ee41b`], [`compare` sem avisos de comparabilidade. Todas as métricas principais e guardas cumprem: alvo em todas exceto U01 (45,4 MiB) e U04 (SeaweedFS +142,6 MiB), no mínimo. Valores na Tabela 29.],
  )
)

#tab([Registo de Hipóteses e Inferências Prospetivas (H-01 a H-18)],
  tabela(
    colunas: (1.5cm, 1fr, 1fr, 3.2cm),
    tamanho: 7.5pt,
    [ID], [Hipótese], [Como confirmar ou refutar], [Estado],
    [H-01], [ALT-1, materializando vídeo entre efeitos, tende a aumentar a latência de um vídeo face ao caminho ordinário atual. O ganho de modularidade tem custo de I/O e possíveis recodificações.], [Mesmo conjunto de vídeos/efeitos, hardware e limites. Medir latência por vídeo, I/O e equivalência de frames/áudio antes/depois. Incluir formatos intermédios sem perdas.], [Por confirmar],
    [H-02], [ALT-2 melhora débito e espera de lotes quando existem CPU/RAM suficientes. Mais réplicas no portátil saturado podem não melhorar.], [Ensaios com 1/2/4 consumidores e carga idêntica. Separar tempo em fila, execução, p95 de conclusão, CPU e RSS. Não escalar durante a baseline atual.], [Por confirmar],
    [H-03], [Existem janelas de perda/repetição entre publicação, ack e persistência. Retentativas podem não produzir um único resultado coerente.], [Em ambiente de teste isolado, interromper worker/broker/orquestrador em pontos definidos. Verificar reentrega, ficheiros, Process, Result, token e quota. Testar exceção tratada e SIGKILL separadamente.], [Por confirmar],
    [H-04], [ALT-1 reduz o alcance de implantação de uma alteração de efeito, mas aumenta contratos, ALT-2 mantém o esforço interno de alteração e a duplicação PIL.], [Tarefa de manutenção equivalente em ramos experimentais: medir módulos/serviços tocados, dependências, tempo e regressões, sem introduzir funcionalidade na entrega.], [Por confirmar],
    [H-05], [Buffers integrais e ZIP em memória limitam uploads/exportação concorrentes de ficheiros grandes.], [Ensaiar cargas de 10/100/500 MB autorizadas pelo perfil. Medir RSS em gateway, projects e storage, falhas e tempo pós-envio, preservar geradores e limites.], [Por confirmar],
    [H-06], [Ocultação de ferramentas e erros tardios tornam a criação de pipelines menos compreensível. Mudar só os workers não resolve a operabilidade.], [Utilizadores com tarefas iguais em projetos só de imagem e mistos. Medir sucesso, erros, tempo e compreensão, comparar sem alterar catálogo funcional.], [Por confirmar],
    [H-07], [As portas internas e a confiança da fachada permitem contornar algumas verificações do percurso normal.], [Testar acesso/autorização com duas contas de teste e por cada fronteira publicada, incluindo expiração dos URLs. Sem ler dados reais de terceiros.], [Por confirmar],
    [H-08], [Whisper, estágios adicionais e preview de extração prejudicam tempo de resposta e espera de tarefas simples no consumidor único. Replicar pode aliviar espera, não o custo individual.], [Cargas separadas/mistas de efeitos comuns, fala/sem fala e extração, com modelo frio/quente. Medir execução/fila, CPU/RAM e bytes intermédios.], [Por confirmar],
    [H-09], [O reconhecimento real pode produzir erros e variação que os testes com recognizer simulado não revelam.], [Corpus de fala com transcrição de referência, idioma/duração fixos e modelo/versionamento registados, comparar texto e repetibilidade.], [Por confirmar],
    [H-10], [O intervalo entre eventos pode exceder 5 s em fila, reconhecimento e estágios lentos.], [Capturar timestamps dos eventos de uma sessão de teste, incluindo períodos sem avanço. Comparar maior intervalo observado com critérios MVP/produção.], [Por confirmar],
    [H-11], [A aprovação da suite não implica taxa de sucesso operacional ≥95% ou ≥99,5%.], [Definir corpus válido, distribuição de efeitos e falhas, repetições e denominador. Medir sucesso de ponta a ponta com intervalo de confiança.], [Por confirmar],
    [H-12], [Com várias réplicas e Apply concorrentes no mesmo projeto, caminhos de trabalho comuns podem colidir. Tokens protegem o commit mas não isolam todos os ficheiros.], [Dois Apply sobre o mesmo projeto e sobre projetos distintos. Verificar escrita/limpeza de `src`/`out`, duplicados, tokens e integridade final, com diretórios isolados por execução no protótipo.], [Por confirmar],
    [H-13], [Os mecanismos herdados podem apoiar RNF de partilha, presets e IA, mas a inspeção estática e os testes de vídeo não demonstram os percentis, limites temporais, disponibilidade, retenção e invariantes sob concorrência exigidos nesses RNF.], [Ensaiar geração de links (99% $< 1$ s), sincronização entre dispositivos (≤5 s), presets (95% ≤2 s, 100 ciclos sem duplicação/perda), concorrência de edição/presença, retenção do assistente e carga/uptime de IA. Resolver o conflito 10 s/3 s de RNF54 antes de aceitar um limiar. Reutilizar corpus/ambiente fixos, não inventar novos alvos.], [Por confirmar],
    [H-14], [Autenticar/autorizar em cada fronteira e revalidar WS reduz os efeitos indevidos dos casos conhecidos, com custos de CPU/latência e indisponibilidade em falha.], [Repetir casos corrigidos com controlos positivos, TLS/peer/domínio e carga WS. Medir corte e overhead sem apresentar erro 500 como segurança.], [*Confirmada* no corpus de casos: S01–S04, S16 e S17 com 0 admitidos, S12 1125 ms, S05 100%. Custo de latência dentro do alvo (S21 Δ ≤ +1,9 ms). Indisponibilidade em falha observada nos contextos WS já admitidos e gerida pela decisão 53 (EV-55)],
    [H-15], [Novo percurso nginx/S3 e streaming limitado no adaptador reduzem a dependência RSS Node/tamanho, sem deslocar um custo inaceitável para nginx/S3/disco.], [BF/MF no mesmo host/budget/corpus, C=1/C=3, memória agregada, temporários, bytes/CPU e tempos até ready/hash/cleanup, comparar cada transporte.], [*Confirmada em parte*: pico Node 1976 → 45,4 MiB e U20 3/3 sem OOM. Parte do custo passou para o SeaweedFS, com U04 e U01 só no mínimo (EV-55)],
    [H-16], [Hash posterior pode reduzir t_ready, mas acrescenta atraso/leituras e exige cache/retoma coerentes.], [Medir t_ready/t_hash/t_complete, originais e previews antes/depois do hash. Injetar falhas só em fixtures autorizadas.], [*Confirmada*: U09 máx. 806 ms (BF: mediana 6171 ms) e U10 ≤0,89× BF. O custo do _hash_ continua em segundo plano. Exigiu tratar a _media_ apagada antes do _hash_ (decisão 51) (EV-52, EV-55)],
    [H-17], [Adaptador, controlos de confiança e tentativas cabem no orçamento do host e no prazo académico sem reduzir cobertura.], [Calibrar por fase, inventariar disco/serviços e esforço da equipa, materializar instrumentos/corpus antes do congelamento.], [*Confirmada em parte*: todos os blocos foram feitos sem cortes, mas o disco do _host_ obrigou a quatro limpezas autorizadas (D-26, D-32, D-34, D-38) e os pilotos B10 não foram repetidos na verificação final (decisão 49)],
    [H-18], [Benefícios conjuntos de segurança e upload mantêm U25 e os fluxos legítimos, apesar de mais TLS/queries/estados.], [Ensaios de coexistência/latência pareados e regressões de imagem/vídeo/partilha/quota/billing, conservando todos os erros.], [*Confirmada*: U25 com 0 erros e razão máx. 0,58, S05 100%, regressão 105/105 (EV-53, EV-55)],
  )
)
]

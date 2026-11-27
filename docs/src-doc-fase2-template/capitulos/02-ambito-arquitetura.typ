#import "../template.typ": *

= Âmbito e Vista da Arquitetura

Este capítulo e os capítulos 3–5 recuperam o *diagnóstico da solução de base* (`0523102`), realizado nos Exercícios 6 e 7. As portas expostas, a ausência de autorização WS e os _buffers_ integrais descritos nessa análise são propriedades da base. A implementação final e as alterações a essas propriedades encontram-se nos capítulos 8–10. As referências de linhas de EV-07–EV-27 e EV-37/EV-46 devem ser consultadas nessa revisão histórica, não no código final.

== Preparação e ambiente

#tab([Preparação e ambiente],
  tabela-campos(
    [Commit de partida], [`052310226c51fa57a17101c7bd1ad795674aac95` (`0523102`)],
    [Comando(s) de arranque], [
      - _Aplicação base:_ arranque histórico com `docker compose up -d --build` na raiz, acesso em `https://localhost:8080`. A base usava um certificado autoassinado; esse comportamento histórico não é uma instrução para ultrapassar avisos. Na entrega final, gerar segredos/PKI e importar a CA verificada num perfil dedicado do navegador, conforme o Anexo A e `docs/pki-operations.md`. Após reconstruir o frontend: `docker compose restart nginx`. (EV-09, EV-33, EV-52)
      - _Instrumento formal de avaliação:_ `evaluation/med.py` (`med.py stack up`, depois `med.py run --campaign BF` ou `--campaign MF`) executado sobre a _stack_ isolada `picturas-nfr`, que o próprio `med.py` constrói e arranca (Anexo A.4), garantindo ausência de interferência com volumes ou portas da instalação de desenvolvimento.
    ],
    [Ambientes de execução], [
      - _Ambiente de diagnóstico exploratório inicial (EV-28):_ Ubuntu 22.04.5 LTS, kernel Linux 6.8.0-138-generic, x86_64, Intel Core i7-13700H (14 núcleos, 20 vCPU). 15 GiB RAM e 2 GiB _swap_, Docker 29.9.2, _build_ `a82e528`, Docker Compose v5.6.1.
      - _Ambiente da baseline formal (BF) e avaliação comparativa (MF):_ Host dedicado Apple M4 Pro (macOS, Darwin 24.6.0, arm64), com 12 CPU e 7,7 GiB de RAM atribuídos ao Docker Desktop (VM Linux 6.10.14-linuxkit, cgroup v2), Docker Engine 28.5.1. Valores registados em `evaluation/results/BF-20261121T013224Z/manifest.json`. Campanha oficial `BF-20261121T013224Z` recolhida a 21/11/2026 sobre o _commit_ `d6b4497d116fe2ec265040084f6ec126cb84ad49` (código de aplicação estritamente idêntico a `0523102`).
    ],
  ),
)

*Como é orquestrado o processamento em lote de imagens e de vídeos:*

O comando _Apply_ envia `POST /api-gateway/projects/:user/:project/process`, com JWT e versão do projeto, pelo nginx e API Gateway (EV-07, EV-08). O serviço `projects` valida a sequência do projeto e reserva em `users` as operações necessárias (EV-14, EV-25). De seguida, descarrega os originais do S3 para o volume `image_data` e regista todos os registos `Process` do lote antes de publicar os primeiros pedidos (EV-14). Para cada *imagem*, envia a primeira ferramenta para a fila `<tool>_queue`. Cada resposta em `project_queue` faz `projects` avançar para a etapa seguinte (EV-15). Para cada item com `media_type: "video"`, publica um único pedido em `video_queue` com o _pipeline_ completo aplicável àquele vídeo (EV-10, EV-12, EV-14). O worker de vídeo processa todos os estágios internamente e emite percentagens para `ws_queue`. O `wsGateway` entrega o evento `video-progress` ao cliente por Socket.IO (EV-16, EV-22). Por fim, `projects` persiste as saídas em S3, cria registos `Result` e publica a conclusão. Os URLs e o ZIP usam os resultados do token confirmado, incluindo os fotogramas individuais quando há extração (EV-21, EV-28). O sistema distingue os dois tipos de _media_ desde o _upload_ (endpoints `/img` e `/video` separados com validação por `ffprobe`) até ao despacho (granularidade por etapa para imagens, mensagem única por vídeo) e à resposta (fotogramas extraídos mantêm referência ao `img_id` do vídeo de origem).

== Fontes consultadas

#tab([Fontes consultadas],
  tabela(
    colunas: (5.5cm, 3cm, 1fr),
    [Fonte], [Versão / data], [Usada para],
    [`README.md`, `AGENTS.md`], [Base `0523102`; entrega `e0a880a`], [Diagnóstico histórico e instruções atuais de arquitetura, execução, PKI, ferramentas e testes, distinguidos pela revisão consultada.],
    [`doc-ext-requisitos.pdf`], [Fase 1 2025/2026, novembro 2025, 39 pp.], [RNF43–RNF66 (§6.2, pp.19–25): requisitos de qualidade herdados, critérios e inconsistências.],
    [`doc-ext-requisitos-2627.pdf`], [PL1-G4, v2.0, 2026-10-23, 85 pp.], [Casos de uso, catálogo de requisitos, classificação de qualidade, rastreabilidade e decisões DA-01–DA-10.],
    [`doc-sol-arquitetural.pdf`], [Fase 2 2025/2026, janeiro 2026, 51 pp.], [Arquitetura herdada: táticas, vistas estrutural/runtime/_deployment_, limitações históricas.],
    [Slides da aula 11: Architectural Styles], [J. M. Fernandes, outubro 2021, 25 slides], [Estilo idealizado versus realizado, Pipes and Filters, Batch Sequential, Publish–Subscribe e níveis de vista.],
    [HTML de apoio: padrões arquiteturais], [Sem versão/data explícita], [Distinção dos três níveis (global, vídeo, interior), sete famílias de padrões, enquadramento de ALT-1/ALT-2.],
    [Diretrizes da Fase 2], [Versão 1, 2026-11-04, 3 pp.], [Preservação funcional, dois RNF distintos, ISO/IEC 25010:2011, _baseline_ e avaliação reprodutível.],
    [Código e configuração da aplicação], [Base `0523102`; final `9b4e87d` / `c8a5e3d`], [Diagnóstico da base e confronto das decisões com nginx, gateways, domínio, armazenamento, ferramentas, worker, filas, testes e operação final. O código da aplicação é igual nos dois commits finais.],
    [Instrumento e critérios de avaliação (`evaluation/med.py`, `criteria.yaml`)], [_Hash_ final `12c60c7f7695`, 23/11/2026], [Instrumento de medição e critérios congelados. Evolução autorizada registada em `manifest.json` da BF (`instrumento_historico` e `instrumento_final`) e nas notas 24/25 de `evaluation/IMPLEMENTATION_NOTES.md`.],
    [Métricas e plano de medição (`docs/metricas.md`, `planoMedicao.md`)], [Novembro 2026], [Catálogo das 21 métricas selecionadas, protocolo de execução da baseline formal (BF) e campanha `BF-20261121T013224Z`.],
    [Hohpe & Woolf: Pipes and Filters e Competing Consumers], [Catálogo EIP, consulta 2026-11-09], [Fundamentação das alternativas ALT-1 e ALT-2.],
    [RabbitMQ: Consumer Acknowledgements], [Documentação oficial, consulta 2026-11-09], [Distinção entre confirmação de consumo, confirmação de publicação e reentrega.],
    [ISO/IEC 25010:2011], [Edição 2011, consulta 2026-11-09], [Modelo de oito características. Classificação de RNF e atributos de qualidade.],
    [Enunciados e _templates_ dos Exercícios 6 e 7], [Ex. 6: 1.1, 2026-11-04, Ex. 7: 3.0, 2026-11-17], [Estrutura e regras dos capítulos 2 a 10. Originais em `docs/exercises/*/sources/` (EV-02, EV-38, EV-39).],
    [Plano e passagem de trabalho da refatoração (`docs/refactor-plano.md`, `docs/refactor-handoff.md`)], [2026-11-21 a 25], [Decisões fechadas antes de implementar, blocos B0–B12, estado da implementação, desvios e resultados da MF (EV-50 a EV-55).],
  ),
)

#paisagem[
== Vista da arquitetura global

#figure(
  image("../images/arquitetura-base-legivel.svg", width: 100%, height: 14cm, fit: "contain"),
  caption: [Arquitetura global da solução de base; o caminho do vídeo está destacado a laranja],
)
]

*Ferramenta / notação:* vista de componentes/contentores em SVG, gerada por `images/gerar-diagnostico.py` da pasta do relatório. É uma síntese legível da fonte PlantUML histórica `docs/exercises/06-architectural-patterns/diagrams/arquitetura_global.puml` (EV-06). MongoDB aparece dentro do serviço proprietário por economia gráfica, não como base partilhada. A sincronização REST é distinta das filas assíncronas.

#tab([Legenda da vista da arquitetura],
  tabela(
    colunas: (5cm, 1fr),
    [Elemento (cor, forma ou estilo)], [Significado],
    [Setas laranja e worker de vídeo realçado], [Caminho específico do vídeo: uma mensagem por _pipeline_/vídeo.],
    [Setas cinzentas], [Relações globais e processamento de imagens.],
    [Caixa violeta], [Volume de trabalho `image_data`, partilhado por projects e workers no mesmo host.],
    [Nomes MongoDB dentro dos serviços], [Persistência separada por domínio; SeaweedFS/S3 armazena os ficheiros binários.],
    [Caixa RabbitMQ e setas], [Transporte assíncrono com exchange direto na base; filas discriminadas na sequência e no texto.],
  ),
)

*Análise da vista da arquitetura global:*

A arquitetura global do PictuRAS (Figura 1) organiza-se através de um estilo de microserviços orientados a eventos e comunicação REST, coordenados de forma centralizada pelo serviço `projects` (EV-03, EV-07–EV-10, EV-35). Os pedidos externos dos clientes entram exclusivamente pela porta HTTPS 8080 através do _reverse proxy_ nginx, sendo o tráfego HTTP de API reencaminhado para o `apiGateway` (Express com validação de JWT) e as comunicações bidirecionais persistentes para o `wsGateway` (Socket.IO).

Os dados de negócio distribuem-se por bases de dados MongoDB isoladas por domínio funcional (`users_db`, `projects_db` e `subscriptions_db`), assegurando o padrão _Database-per-Service_. O armazenamento binário de originais, resultados e imagens temporárias de pré-visualização é assegurado pelo SeaweedFS (compatível com a API S3), acedido através da fachada `imageStorageService`.

O transporte de trabalho computacional assenta num _broker_ RabbitMQ durável com _exchange_ direto `picturas`. A vista arquitetural destaca uma bifurcação estrutural clara entre os dois tipos de _media_:
- *Caminho global de imagens (setas cinzentas):* Cada uma das 16 ferramentas de processamento de imagem opera como um microserviço autónomo em Python/PIL ou modelos de inteligência artificial, consumindo pedidos individuais passo a passo da respetiva fila `<tool>_queue` com confirmação automática de consumo (_auto-ack_) e acedendo ao volume de trabalho partilhado `image_data`.
- *Caminho de vídeo (setas laranja e worker realçado):* O processamento de vídeo diverge radicalmente do padrão de passos distribuídos. Todo o processamento de vídeo está concentrado num único contentor monolítico (`video_tool`), que consome pedidos na fila `video_queue`. Ao contrário das imagens, o worker de vídeo recebe o _pipeline_ completo numa única mensagem, executa internamente todas as etapas de descodificação, efeitos matriciais e recodificação em FFmpeg/PIL, e emite eventos de progresso contínuo para a fila `ws_queue`, consumida pelo `wsGateway` para notificação ao cliente.

*Ressalvas técnicas observadas no diagrama:* A «entrada única» através do nginx representa o percurso aplicacional nominal, mas não constitui uma fronteira de segurança exclusiva na solução de base, uma vez que a configuração do `docker-compose.yaml` expõe diretamente portas de serviços internos e bases de dados no _host_ (EV-24, EV-33). Adicionalmente, o volume partilhado `image_data` é montado em simultâneo pelo orquestrador e pelos trabalhadores, impondo acoplamento de sistema de ficheiros local.

#paisagem[
== Sequência de um pedido completo

#figure(
  image("../images/sequencia-base-a.svg", width: 100%, height: 14cm, fit: "contain"),
  caption: [Sequência na base: (a) upload, definição do pipeline e despacho de um vídeo],
)
]
#paisagem[
#figure(
  image("../images/sequencia-base-b.svg", width: 100%),
  caption: [Sequência na base: (b) progresso, resultados e descarga],
)
]

O catálogo completo de todas as evidências (`EV-01` a `EV-55`) e hipóteses (`H-01` a `H-18`), com a localização detalhada no repositório e o respetivo facto ou inferência técnica, encontra-se consolidado no Anexo C para consulta e rastreabilidade sistemática.

As sequências são vistas lógicas SVG geradas pela mesma fonte do diagrama global. Agrupam nginx/API e fachada/S3 para manter a legibilidade; não representam um salto de segurança omitido na implementação final. Todos os Process são registados localmente na projects antes de publicar no broker. As mensagens de imagem regressam à projects entre etapas; o vídeo mantém o pipeline completo dentro do worker. As respostas e os eventos para o browser passam pelo nginx.

#tab([Passos do pedido completo],
  tabela(
    colunas: (3cm, 3.6cm, 1fr, 3.4cm),
    [Passo], [Origem → Destino], [Mensagem / _endpoint_ / fila], [Evidência],
    [Carregamento do vídeo], [Browser → nginx → API Gateway → `projects`], [`POST /api-gateway/projects/:u/:p/video`, campo multipart `video`, JWT e `X-Project-Version`, `ffprobe`, limites por perfil, gravação de `media_type: "video"` e chave S3.], [EV-07, EV-08, EV-10, EV-12],
    [Definição do _pipeline_], [Browser → gateway → `projects`], [`POST .../:u/:p/tool` com `procedure` e `params`, posições persistidas. `POST .../:u/:p/reorder` para reordenar.], [EV-10, EV-13],
    [_Apply_ e quota], [Browser → gateway → `projects` → `users`], [`POST .../:u/:p/process`, consulta/reserva em `GET /:caller/process/:nOps`, token de execução.], [EV-08, EV-14, EV-25],
    [Preparação do lote], [`projects` → S3 → `image_data`, `projects` → MongoDB], [_Download_ por _stream_ e criação de todos os `Process` antes do primeiro despacho. HTTP 201 confirma o despacho, não a conclusão.], [EV-14],
    [Despacho], [`projects` → RabbitMQ → workers], [Imagens: `<tool>_queue`, uma etapa por pedido. Vídeo: `video_queue`, _pipeline_ completo numa mensagem.], [EV-14, EV-15, EV-16],
    [Progresso], [`video_tool` → `ws_queue` → `wsGateway` → browser], [`messageId` com prefixo `update-client-video-progress-`. Campos `user`, `projectId`, `imgId`, `preview`, `percent`, evento Socket.IO `video-progress`.], [EV-16, EV-22, EV-23],
    [Resultado], [Browser → gateway → `projects`/S3], [`GET .../:u/:p/process/url` fornece URLs do token confirmado, `GET .../:u/:p/process` produz ZIP.], [EV-11, EV-21, EV-28],
  ),
)

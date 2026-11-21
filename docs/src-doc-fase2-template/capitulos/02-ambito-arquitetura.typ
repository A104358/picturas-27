#import "../template.typ": *

= Âmbito e Vista da Arquitetura

#orientacao[
  *Origem:* Exercício 6, Bloco 1, secções 0 e 1 do _template_ (preparação, fontes, vista global e sequência).

  *Objetivo do capítulo:* situar o leitor. Mostra como a solução foi lançada, em que fontes se baseia a análise e como é
  a arquitetura da solução de base, com o caminho do vídeo em destaque. É a base factual dos capítulos seguintes.

  *Foco:* a *extensão de vídeo, enquadrada no padrão global* da solução. Não analisem o vídeo isoladamente: o que o vídeo
  faz só se percebe à luz do que a solução faz como um todo.

  *Rigor:* cada afirmação sobre o sistema atual cita uma evidência (`EV-nn`) ou é assumida como hipótese (`H-nn`). A
  secção 2.4 explica como se escreve uma evidência.
]

== Preparação e ambiente

#tab([Preparação e ambiente],
  tabela-campos(
    [Commit de partida], [`052310226c51fa57a17101c7bd1ad795674aac95` (`0523102`)],
    [Comando(s) de arranque], [`docker compose up -d --build` na raiz; acesso em `https://localhost:8080` aceitando o certificado local. Após reconstruir o frontend: `docker compose restart nginx`. Não usar `down -v` em instalações com dados a preservar. (EV-09, EV-33)],
    [Ambiente (SO, CPU, RAM, versões de Docker e Compose)], [Ubuntu 22.04.5 LTS; kernel Linux 6.8.0-138-generic, x86_64; Intel Core i7-13700H, 14 núcleos e 20 CPU lógicos; RAM de 15 GiB e _swap_ de 2 GiB; Docker 29.9.2, _build_ `a82e528`; Docker Compose v5.6.1. (EV-28)],
  ),
)

*Como é orquestrado o processamento em lote de imagens e de vídeos:*

O comando _Apply_ envia `POST /api-gateway/projects/:user/:project/process`, com JWT e versão do projeto, pelo nginx e API Gateway (EV-07, EV-08). O serviço `projects` valida a sequência do projeto e reserva em `users` as operações necessárias (EV-14, EV-25). De seguida, descarrega os originais do S3 para o volume `image_data` e regista todos os registos `Process` do lote antes de publicar os primeiros pedidos (EV-14). Para cada *imagem*, envia a primeira ferramenta para a fila `<tool>_queue`; cada resposta em `project_queue` faz `projects` avançar para a etapa seguinte (EV-15). Para cada item com `media_type: "video"`, publica um único pedido em `video_queue` com o _pipeline_ completo aplicável àquele vídeo (EV-10, EV-12, EV-14). O worker de vídeo processa todos os estágios internamente e emite percentagens para `ws_queue`; o `wsGateway` entrega o evento `video-progress` ao cliente por Socket.IO (EV-16, EV-22). Por fim, `projects` persiste as saídas em S3, cria registos `Result` e publica a conclusão; os URLs e o ZIP usam os resultados do token confirmado, incluindo os fotogramas individuais quando há extração (EV-21, EV-28). O sistema distingue os dois tipos de _media_ desde o _upload_ (endpoints `/img` e `/video` separados com validação por `ffprobe`) até ao despacho (granularidade por etapa para imagens; mensagem única por vídeo) e à resposta (fotogramas extraídos mantêm referência ao `img_id` do vídeo de origem).

== Fontes consultadas

#tab([Fontes consultadas],
  tabela(
    colunas: (5.5cm, 3cm, 1fr),
    [Fonte], [Versão / data], [Usada para],
    [`README.md`, `AGENTS.md`], [Commit `484be13`], [Arquitetura, execução, ferramentas de imagem/vídeo, regras posteriores ao MVP, tipos de _media_ e testes.],
    [`doc-ext-requisitos.pdf`], [Fase 1 2025/2026; novembro 2025; 39 pp.], [RNF43–RNF66 (§6.2, pp.19–25): requisitos de qualidade herdados, critérios e inconsistências.],
    [`doc-ext-requisitos-2627.pdf`], [PL1-G4, v2.0, 2026-10-23; 85 pp.], [Casos de uso, catálogo de requisitos, classificação de qualidade, rastreabilidade e decisões DA-01–DA-10.],
    [`doc-sol-arquitetural.pdf`], [Fase 2 2025/2026; janeiro 2026; 51 pp.], [Arquitetura herdada: táticas, vistas estrutural/runtime/_deployment_, limitações históricas.],
    [Slides da aula 11 — Architectural Styles], [J. M. Fernandes; outubro 2021; 25 slides], [Estilo idealizado versus realizado, Pipes and Filters, Batch Sequential, Publish–Subscribe e níveis de vista.],
    [HTML de apoio — padrões arquiteturais], [Sem versão/data explícita], [Distinção dos três níveis (global, vídeo, interior); sete famílias de padrões; enquadramento de ALT-1/ALT-2.],
    [Diretrizes da Fase 2], [Versão 1, 2026-11-04; 3 pp.], [Preservação funcional, dois RNF distintos, ISO/IEC 25010:2011, _baseline_ e avaliação reprodutível.],
    [Código e configuração da aplicação], [Commit `484be13`], [nginx, gateways, `projects`, `users`, `subscriptions`, armazenamento, ferramentas PIL/IA, worker de vídeo, filas, Compose, testes e backups.],
    [Hohpe & Woolf — Pipes and Filters e Competing Consumers], [Catálogo EIP; consulta 2026-11-09], [Fundamentação das alternativas ALT-1 e ALT-2.],
    [RabbitMQ — Consumer Acknowledgements], [Documentação oficial; consulta 2026-11-09], [Distinção entre confirmação de consumo, confirmação de publicação e reentrega.],
    [ISO/IEC 25010:2011], [Edição 2011; consulta 2026-11-09], [Modelo de oito características; classificação de RNF e atributos de qualidade.],
  ),
)

== Vista da arquitetura global

#orientacao[
  *Nota:* a vista de arquitetura global existe em formato SVG/PlantUML no repositório, em `docs/exercises/06-architectural-patterns/diagrams/`. Incluir a imagem compilada em `images/arquitetura_global.png` antes da entrega final.
]

#figure(kind: image,
  figura-pendente[vista da arquitetura global com o caminho do vídeo destacado — fonte: `diagrams/arquitetura_global_plantuml.svg` (EV-06)],
  caption: [Vista da arquitetura global com o caminho do vídeo destacado],
)

*Ferramenta / notação:* PlantUML, vista de componentes/contentores; fonte editável em `docs/exercises/06-architectural-patterns/diagrams/arquitetura_global.puml`. (EV-06)

#tab([Legenda da vista da arquitetura],
  tabela(
    colunas: (5cm, 1fr),
    [Elemento (cor, forma ou estilo)], [Significado],
    [Setas laranja e worker de vídeo realçado], [Caminho específico do vídeo — uma mensagem por _pipeline_/vídeo.],
    [Setas cinzentas], [Relações globais e processamento de imagens.],
    [Tracejado violeta], [Acesso ao volume de trabalho partilhado `image_data`.],
    [Cilindros], [Persistência em MongoDB (por domínio) e SeaweedFS/S3.],
    [Filas retangulares], [Transporte assíncrono por RabbitMQ (exchange direto).],
  ),
)

== Sequência de um pedido completo

#orientacao[
  *O que é uma evidência (`EV-nn`).* Uma evidência é a referência *verificável* que sustenta uma afirmação sobre o
  sistema atual. Deve permitir que outra pessoa, no _commit_ de partida, confirme o que afirmam sem ter de adivinhar.
  Pode ser:
  - *código*, com ficheiro e linhas (e.g., `video.py:8-9`);
  - *configuração*, com ficheiro e linha (e.g., `docker-compose.yml`, definição de uma fila ou de um volume);
  - *mensagem* observada (e.g., conteúdo de uma mensagem na fila, resposta de um _endpoint_);
  - *medição* ou *registo de execução*, com o comando usado e o resultado;
  - *documento*, com a secção (e.g., `doc-sol-arquitetural.pdf`, secção 3).

  Regras: o ID é sequencial (`EV-01`, `EV-02`, …), único, e nunca se reutiliza. Como o relatório não tem um registo
  separado, *descrevam a evidência no sítio onde a usam pela primeira vez* (formato: `EV-nn`: localização — o que
  mostra); nas ocorrências seguintes basta o ID. Uma afirmação sem evidência não é um facto: marquem-na como
  *hipótese* (`H-nn`) e indiquem como a confirmar ou refutar.
]

#figure(kind: image,
  figura-pendente[diagrama de sequência do processamento em lote de um projeto com vídeos — fonte: `diagrams/sequencia_processamento.svg`],
  caption: [Sequência do processamento em lote de um projeto com vídeos],
)

#tab([Passos do pedido completo],
  tabela(
    colunas: (3cm, 3.6cm, 1fr, 3.4cm),
    [Passo], [Origem → Destino], [Mensagem / _endpoint_ / fila], [Evidência],
    [Carregamento do vídeo], [Browser → nginx → API Gateway → `projects`], [`POST /api-gateway/projects/:u/:p/video`; campo multipart `video`; JWT e `X-Project-Version`; `ffprobe`; limites por perfil; gravação de `media_type: "video"` e chave S3.], [EV-07, EV-08, EV-10, EV-12],
    [Definição do _pipeline_], [Browser → gateway → `projects`], [`POST .../:u/:p/tool` com `procedure` e `params`; posições persistidas. `POST .../:u/:p/reorder` para reordenar.], [EV-10, EV-13],
    [_Apply_ e quota], [Browser → gateway → `projects` → `users`], [`POST .../:u/:p/process`; consulta/reserva em `GET /:caller/process/:nOps`; token de execução.], [EV-08, EV-14, EV-25],
    [Preparação do lote], [`projects` → S3 → `image_data`; `projects` → MongoDB], [_Download_ por _stream_ e criação de todos os `Process` antes do primeiro despacho. HTTP 201 confirma o despacho, não a conclusão.], [EV-14],
    [Despacho], [`projects` → RabbitMQ → workers], [Imagens: `<tool>_queue`, uma etapa por pedido. Vídeo: `video_queue`, _pipeline_ completo numa mensagem.], [EV-14, EV-15, EV-16],
    [Progresso], [`video_tool` → `ws_queue` → `wsGateway` → browser], [`messageId` com prefixo `update-client-video-progress-`; campos `user`, `projectId`, `imgId`, `preview`, `percent`; evento Socket.IO `video-progress`.], [EV-16, EV-22, EV-23],
    [Resultado], [Browser → gateway → `projects`/S3], [`GET .../:u/:p/process/url` fornece URLs do token confirmado; `GET .../:u/:p/process` produz ZIP.], [EV-11, EV-21, EV-28],
  ),
)

# Revisão da vista antes — 23/11/2026

## Âmbito

Revisão documental pedida pelo utilizador para verificar e corrigir
`docs/src-doc-fase2-template/images/vista_antes.png`. A referência é a aplicação
base `0523102`; o checkout consultado é `933ae11`. A comparação dos caminhos de
aplicação com a base não apresenta diferenças. O plano/handoff mantêm B0–B12 por
iniciar; as decisões do desenho futuro não são comportamento existente nesta vista.

## Confronto com o repositório

Os caminhos seguintes são relativos à raiz do repositório.

| Ponto | Fonte consultada | Representação corrigida |
|-------|------------------|-------------------------|
| Entrada e protocolos | `nginx/nginx.conf`, `docker-compose.yaml` | TLS público em :8080; HTTP nos saltos nginx → API, WS e S3. Socket.IO e eventos passam pelo nginx nos dois sentidos. |
| Corpo antes da autenticação | `apiGateway/routes/projects.js`, `upload.single("video")` antes de `auth.checkToken` | Buffer integral do vídeo antes de verificar JWT; não desenhar autorização antes do corpo na base. |
| HTTPS interno | Agentes HTTPS em `apiGateway/routes/{projects,users,subscriptions}.js` e `projects/routes/projects.js` | Certificado remoto não validado; isso não significa tráfego sem cifra. Sem mTLS de serviço verificado. |
| Upload no orquestrador | `projects/routes/projects.js`, `projects/utils/video.js`, `projects/utils/imageStorage.js` | Buffer integral, temporário para ffprobe, hash síncrono e envio multipart HTTP ao storage. |
| Storage/S3 | `imageStorageService/server.js`, `route/upload.js`, `services/{uploadImage,s3Client}.js`, nginx `/s3/` | Buffer no img_storage, rotas sem autenticação, API S3 por HTTP; acesso público a objetos separado do percurso do upload. |
| APIs de perfis e planos | `apiGateway/routes/{users,subscriptions}.js`, `projects/routes/projects.js` | Gateway também chama users e subscriptions diretamente; projects consulta users para perfil/quota. Quota só no Apply. |
| Pedidos e respostas | `projects/utils/project_msg.js`, `Tools/video/video.py`, `rabbitMQ/definitions.json` | Broker e workers separados; pedidos nas filas de imagem/video_queue e resultados em project_queue para projects. |
| Produtores de eventos | `projects/utils/project_msg.js`, `Tools/video/video.py`, `wsGateway/index.js` | projects publica eventos; o worker de vídeo publica progresso; ws_queue alimenta ws_gateway. |
| Identidade e permanência WS | `wsGateway/index.js` | JWT opcional, join sem autorização do projeto, sem revalidação nem corte ao expirar; nenhuma consulta WS → projects na base. |

Frontend, MongoDB/backup, volumes e canais IA continuam fora desta vista parcial;
o seu inventário está na vista global e nos documentos de arquitetura. A vista
não atribui todas as fragilidades ao upload nem representa o desenho futuro.

## Artefactos e renderização

- Fonte: [before.mmd](../diagrams/before.mmd), igual ao bloco antes da
  [resolução](../resolution.md).
- Configuração: [before-render.json](../diagrams/before-render.json), layout ELK,
  orientação vertical, tema neutral e fonte de 18 px.
- Imagem: [vista_antes.png](../../../src-doc-fase2-template/images/vista_antes.png),
  2194 × 2690 px, escala 2 e fundo branco.
- Renderizador usado: Mermaid CLI **11.17.1**. Comando reproduzível no
  [índice do exercício](../README.md#regenerate-the-before-image).
- O browser local precisou de execução fora da sandbox; a configuração local do
  Puppeteer e o browser descarregado ficaram em `/tmp`, fora do repositório.

| Artefacto | SHA-256 |
|-----------|---------|
| before.mmd | `e7b2dd91ffac5195ff7768a0f2fc3f2bfa3ffe0236460e8aacc36657894644e8` |
| before-render.json | `fe22931c2147a8104a3b70bb79236cd2c188e62a2104e6103d841dbc55a46ab7` |
| vista_antes.png | `748b2e9a6630d0bb36038d40c4f4156779d2aa7fc0e7fd90431166bd7d0b503d` |

## Verificação e limites

- Mermaid renderizado sem erro; PNG aberto e inspecionado visualmente, sem texto
  sobreposto. A primeira disposição foi revista antes de guardar a imagem final.
- Fonte inline, configuração e PNG final conferidos; PNG válido e igual à imagem
  inspecionada. Legenda do capítulo 9 sincronizada com a revisão.
- Referências locais e whitespace verificados.
- Aplicação, instrumento congelado e resultados BF não alterados. Nenhum serviço,
  volume ou base de dados foi iniciado/alterado por esta revisão.
- Sem compilação integral do relatório: o executável Typst não está disponível.
  Sem novos testes da aplicação ou medições de RNF. Sem commit.

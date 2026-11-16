# PictuRAS — Fase 2: ideias 1 e 2 com as decisões tomadas

Extrato das ideias 1 e 2 do catálogo de upgrades não funcionais
(`memory-bank/intents/001-phase-2-quality-improvements/upgrade-ideas.md`), já com as soluções
propostas e as decisões da equipa de 16/11/2026. As medições foram feitas nessa data, num stack
isolado; o ambiente, as limitações e os scripts estão descritos no catálogo («Como ler este
documento») e em `memory-bank/intents/001-phase-2-quality-improvements/evidence/nfr-2026-11-16/`.
As referências a outras ideias (5, 7, 8, 9, 11) remetem para o catálogo.

A última secção explica cada decisão: porque foi escolhida, que outras opções havia e porque
ficaram de fora. Quando havia uma opção mais forte, diz-se qual é e porque não foi usada agora.

---

## Ideia 1: Autorização verificada ponta-a-ponta

**Tipo:** Segurança — confidencialidade, integridade e autenticidade.

**Ideia:** Fazer com que a identidade de quem pede seja **verificada criptograficamente em cada
fronteira** (gateway, `projects`, `img_storage`, WebSocket) e que a posse do projeto seja
confirmada no servidor, em vez de se confiar em parâmetros e cabeçalhos escolhidos pelo cliente.

**Situação base:** O gateway verifica o JWT, mas aceita `?owner=<id>` em 22 rotas e reencaminha o
pedido para o projeto desse dono. `projects` confia no cabeçalho `X-Caller-Id` e, na falta dele,
faz `jwt.decode` (sem verificar assinatura). `img_storage` não tem qualquer autenticação. O
`ws_gateway` aceita ligações sem token e deixa qualquer socket entrar na sala de qualquer
projeto. Todas estas portas estão publicadas no host pelo `docker-compose.yaml`.

Para além do que a matriz mede, por inspeção do código: os 32 serviços partilham uma única rede
Docker (`elk`); os dois MongoDB (27018, 27019) estão publicados no host e aceitam ligações sem
credenciais; o SeaweedFS (9000) usa as credenciais por omissão `admin`/`admin123`; `users`
(10001) e `subscriptions` (11001) estão publicados e não têm middleware de autenticação (por
exemplo, `GET /` da `users` lista todos os utilizadores e `PUT /:user` altera o `type`). Estes
pontos não foram medidos e sobrepõem-se às ideias 5 e 9.

**Diagnóstico completo:**

O middleware do gateway só compara o utilizador do token com o do caminho; o dono real vem depois
de um parâmetro que o cliente controla:

```js
// apiGateway/routes/projects.js (padrão repetido em 22 rotas)
const ownerId = req.query.owner || req.params.user;
const callerId = req.authUserId || req.params.user;
axios.post(projectsURL + `${ownerId}/${req.params.project}/img`, data, { headers: { "X-Caller-Id": callerId, ... } })
```

Em `projects`, sem `?share=`, o pedido é tratado como «acesso normal do dono» e nunca se compara
quem chama com o dono:

```js
// projects/middleware/shareAuth.js
if (!shareId) return next(); // acesso normal (dono / rotas sem share)

// projects/utils/caller.js
const forwarded = req.headers["x-caller-id"];
if (forwarded) return String(forwarded);
...
const payload = jwt.decode(token);        // decode, não verify
```

```js
// imageStorageService/route/upload.js — sem middleware de autenticação
router.post("/:userId/:projectId/:stage", upload.single("file"), async (req, res) => { ... });

// wsGateway/index.js — sem verificar se o socket pode ver o projeto
socket.on("join-project", (projectId) => { socket.join(`project:${projectId}`); });
```

Impacto nos stakeholders: um utilizador registado qualquer lê o projeto e descarrega os originais
de outro utilizador, altera-lhe o pipeline e injeta-lhe media, **pela entrada pública**
(`https://localhost:8080/api-gateway/`). Viola diretamente o RNF44 e o `REQ-VID-ACCESS-001`
(«acesso restrito ao projeto»). Para utilizadores (incluindo premium, que pagam) é perda de
privacidade e de integridade do trabalho; para o operador é responsabilidade legal (RGPD) e
perda de confiança. Quem alcançar a rede Docker ou as portas publicadas faz ainda mais: apaga
todos os projetos de um utilizador sem qualquer credencial.

**Quantificação:**

*Cenário e carga:* matriz finita de pedidos negativos (devem ser recusados) com dois utilizadores
sintéticos `free` («dono» e «intruso») e um projeto do dono com uma imagem; um pedido por caso.
*Ambiente:* o comum. *Instrumento:* `security.mjs` e `verify.mjs` (cliente HTTP/Socket.IO),
verificando o efeito no estado do dono e, nas leituras, o SHA-256 dos bytes descarregados.

| Caso | Superfície | Pedido não autorizado | Resultado medido |
|------|------------|-----------------------|------------------|
| G01 | gateway | JWT do intruso no caminho do dono | 401 — recusado |
| G02 | gateway | JWT do intruso + `?owner=<dono>`, ler projeto | **200**; mesmo `_id`, nome exposto, original descarregado com SHA-256 igual |
| G03 | gateway | idem, acrescentar ferramenta | **201**; pipeline do dono 0→1, versão 1→2 |
| G04 | gateway | idem, upload de imagem | **204**; media do dono 1→2 |
| D01 | projects:9001 | sem identidade | 401 — recusado |
| D02 | projects:9001 | `X-Caller-Id` forjado, sem token | **200** |
| D03 | projects:9001 | JWT de outro utilizador | **200** |
| D04 | projects:9001 | JWT feito à mão a nomear o dono | 401 — recusado |
| D05 | projects:9001 | `DELETE /:user` sem identidade | **204**; conta com 1 projeto ficou com 0 |
| D06 | img_storage:11000 | pedir URL assinado do original, sem token | **200** (igualdade de bytes já provada em `live-access-supplement-2026-11-14.json`) |
| D07 | img_storage:11000 | escrever objeto no prefixo do dono | **201** |
| D08 | img_storage:11000 | apagar objeto no prefixo do dono | **201** |
| W01 | socket.io | socket **sem token** entra na sala do projeto | recebeu `project-op TOOL_ADDED` com o pipeline |

Resultado: **10 operações não autorizadas admitidas em 13 casos negativos**, 3 delas pela entrada
pública. O controlo positivo (dono lê o próprio projeto) passou. Os casos D usam as portas de
loopback do stack isolado; no `docker-compose.yaml` original as mesmas portas são publicadas em
`0.0.0.0`.

*Mínimo aceitável e alvo:* **0 admitidas** na matriz acordada, com **100% dos controlos
positivos** a passar (dono, partilha de leitura, partilha de edição, worker a guardar
resultados, preview e exportação). Mínimo e alvo coincidem porque um único bypass conhecido
anula o objetivo. Guarda: sobrecarga por pedido medida e ≤ 10 ms em mediana (proposta).

**Solução proposta.**

*Decisões tomadas:*

| # | Decisão | Escolha |
|---|---------|---------|
| D1 | Contra quem nos protegemos | Todos os casos: entrada pública (G, W), rede Docker e portas dos serviços (D), bases de dados e S3 diretos |
| D2 | Quem decide a posse e a partilha | Em camadas: o gateway faz as verificações baratas, a `projects` decide |
| D3 | Como a `projects` sabe quem chama | Identidade assinada pelo gateway, em substituição do `X-Caller-Id` |
| D4 | Identidade de serviço nas chamadas sem utilizador | mTLS |
| D5 | Rede e portas publicadas | Publicar só em `127.0.0.1` |
| D6.2 | Quem entra na sala de um projeto | Bilhete assinado pela `projects` (na resposta do `GET` do projeto), verificado pelo `ws_gateway` |
| D8 | Modelo de partilha | Links com expiração |
| D9 | Serviços no âmbito | Incluir `users` e `subscriptions` |
| D11 | Token de upload da ideia 2 | Verificação própria e simplificada |

*Como fica cada fronteira:*

1. **Gateway (pedidos de utilizador).** Verifica o JWT como hoje e mantém a verificação barata
   (sem `share`, o utilizador do caminho tem de ser o do JWT). Depois emite uma **identidade
   assinada** de curta duração, `{ sub, share?, aud, iat, exp }`, com uma chave própria do
   gateway (diferente do segredo dos JWT de utilizador), e envia-a num cabeçalho dedicado. O
   `X-Caller-Id` deixa de existir.
2. **`projects`.** Verifica a assinatura, o destinatário (`aud`) e a validade dessa identidade e
   deriva dela o chamador (`getCallerId`). Não precisa do segredo dos JWT de utilizador. É ela
   que decide: sem `share`, exige chamador = dono em todas as rotas, incluindo `GET`, `POST` e
   `DELETE /:user` e `/presence`; com `share`, aplica a regra atual (`checkSharePermission`) e a
   expiração (ponto 8).
3. **Chamadas entre serviços sem utilizador** (hoje `projects` → `img_storage` e
   `projects` → `users` para a quota). mTLS: o serviço chamado só aceita ligações com um
   certificado de cliente emitido por uma CA interna do projeto e com a identidade esperada. Os
   certificados são novos (os atuais estão expirados, ideia 11), gerados por script e mantidos
   fora do repositório.
4. **`ws_gateway`.** A resposta do `GET` do projeto inclui um **bilhete**
   `{ sub, project, perm, exp }` assinado pela `projects`. O frontend envia-o no `join-project`.
   O `ws_gateway` verifica a assinatura, a validade e que `sub` coincide com o utilizador do JWT
   do socket, e só então faz `join`. A assinatura é assimétrica: o `ws_gateway` só tem a chave
   pública e não consegue emitir bilhetes.
5. **`users` e `subscriptions`.** Entram na matriz. Passam a aceitar só pedidos vindos do
   gateway (identidade assinada) ou de serviços (mTLS). Sobrepõe-se à ideia 5.
6. **Bases de dados e S3.** MongoDB com utilizador e palavra-passe por serviço; SeaweedFS com
   credenciais fora do repositório. Sobrepõe-se à ideia 9.
7. **Portas.** Todas as portas publicadas, exceto a do nginx (8080), passam a
   `127.0.0.1:<porta>`. A rede `elk` mantém-se única. A proteção contra os casos D vem dos
   pontos 2 a 6, não das portas.
8. **Partilha com expiração.** Novo campo `sharedLinks[].expiresAt`; `checkSharePermission`
   responde 410 depois dessa data; o diálogo de partilha permite escolher a validade.

*Em aberto (por decidir):*

- **D7, o parâmetro `owner`.** Facto verificado: com partilha, o frontend já põe o dono no
  caminho (`pathUidFor` em `frontend/lib/projects.ts`); sem partilha, envia `owner=<o próprio>`.
  O `?owner=` é portanto redundante em todos os casos. As opções são validá-lo (sem `share`,
  igual ao JWT; com `share`, igual ao dono do projeto) ou ignorá-lo no gateway. Qualquer das
  duas fecha G02–G04 sem mudar o frontend.
- **D10, como medir.** Com as portas em `127.0.0.1`, os casos D continuam alcançáveis a partir
  do host, por isso medem-se como hoje e têm de dar 401/403. Fica por decidir se se repete a
  matriz a partir de dentro de um contentor da rede `elk`, e que casos novos entram (partilha
  expirada e revogada, leitura vs. edição, socket com e sem bilhete, token de upload da
  ideia 2).
- **D6.1:** recusar ligações WebSocket sem token, ou aceitá-las sem permitir `join`.
- **D6.3:** expulsar os sockets já ligados quando uma partilha é revogada ou expira. Com
  bilhete, a verificação só acontece no `join`.
- **JWT de utilizador em HS256 ou RS256.** Com a D3, a `projects` deixa de precisar do segredo,
  por isso a questão fica limitada aos três serviços que já o têm.
- **Links existentes** (sem `expiresAt`): sem validade, ou com uma validade por omissão.
- **Validades** do bilhete e da identidade assinada.

*Onde mexer:*

- `apiGateway/routes/projects.js`: deixar de usar `req.query.owner` como dono sem validação
  (forma a decidir em D7); trocar `X-Caller-Id` pela identidade assinada nas 22 rotas;
  `forwardAxiosError`; pôr `auth.checkToken` antes de `upload.single`.
- `apiGateway/auth/auth.js`: `checkToken` mantém a dispensa da comparação quando há `share` (com
  partilha o caminho traz o dono, que é diferente do utilizador do JWT); a partilha passa a ser
  validada na `projects`. Novo módulo que emite a identidade assinada.
- `projects/utils/caller.js`: `getCallerId` deriva o chamador da identidade assinada verificada
  e ignora `X-Caller-Id` e `jwt.decode`.
- `projects/middleware/shareAuth.js`: `checkSharePermission` (expiração),
  `requireEditPermission` (sem `share`, exigir chamador = dono).
- `projects/models/project.js`: `sharedLinks[].expiresAt`.
- `projects/routes/projects.js`: `requireOwner`, `requireAuth`; aplicar a `GET /:user`,
  `POST /:user`, `DELETE /:user` e às rotas `/:user/:project/presence` (hoje usam `getCallerId`,
  que confia no `X-Caller-Id`); emitir o bilhete do WebSocket na resposta do `GET` do projeto.
- `projects/utils/imageStorage.js`, `projects/utils/presence.js` e as chamadas à `users`: cliente
  HTTPS com certificado de cliente (mTLS).
- `imageStorageService/server.js`, `users/bin/www`, `subscriptions/bin/www`: servidor HTTPS a
  exigir certificado de cliente; `users` e `subscriptions` aceitam também a identidade assinada
  do gateway.
- `wsGateway/index.js`: `join-project` verifica o bilhete; `connection` conforme D6.1.
- `frontend/lib/projects.ts` e `frontend/app/dashboard/[pid]/page.tsx`: guardar o bilhete do
  `GET` e enviá-lo no `join-project`; diálogo de partilha com validade.
- `docker-compose.yaml`: portas em `127.0.0.1`; credenciais do MongoDB e do SeaweedFS; chaves
  da identidade assinada e do bilhete e certificados mTLS montados a partir de fora do
  repositório.
- Script de geração da CA interna e dos certificados de serviço.
- Testes: transformar `security.mjs` em suíte de regressão com os controlos positivos e os casos
  novos que se decidirem em D10.

**Avaliação AI: 9,5 / 10.** *Pertinência* máxima: é uma falha explorável hoje por qualquer
utilizador registado, através da entrada pública, com impacto direto em confidencialidade e
integridade dos dados de todos os perfis, e contradiz requisitos escritos (RNF44,
REQ-VID-ACCESS-001). *Complexidade* alta: atravessa quatro serviços, obriga a desenhar identidade
de serviço e a preservar os fluxos legítimos (partilha, workers, previews), e a avaliação é uma
matriz reprodutível antes/depois com controlos positivos — sólida e barata de repetir. Não leva
10 porque uma matriz finita não prova segurança completa.

---

## Ideia 2: Upload em streaming com memória limitada

**Tipo:** Eficiência de desempenho — utilização de recursos (primária) e comportamento temporal
(`REQ-VID-SUBMIT-008`).

**Ideia:** Fazer o ficheiro atravessar gateway → `projects` → storage **em fluxo**, com no máximo
uma cópia temporária em disco para o `ffprobe` e o hash, de modo que a memória por upload deixe
de depender do tamanho do ficheiro.

**Situação base:** Os três serviços Node usam `multer.memoryStorage()`. O mesmo vídeo fica
inteiro em RAM no gateway, outra vez em `projects` (que ainda o escreve para um temporário para
o `ffprobe` e o percorre para o SHA-256) e outra vez no storage antes de ir para o S3. O nginx
aceita corpos até 1100 MB.

**Diagnóstico completo:**

```js
// apiGateway/routes/projects.js
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });          // sem limits
data.append("video", req.file.buffer, { ... });       // segunda cópia no FormData

// projects/routes/projects.js — addProjectMedia()
videoMeta = await probeVideoBuffer(req.file.buffer, req.file.originalname);
data.append("file", req.file.buffer, { ... });
const sha = crypto.createHash("sha256").update(req.file.buffer).digest("hex");

// imageStorageService/services/uploadImage.js
Body: file.buffer,
```

Impacto: o perfil premium tem direito a 1 GB por vídeo (`VIDEO_PREMIUM_MAX_SIZE_MB: 1024`), mas
um único upload de 500 MiB já leva o gateway ao limite de 2 GiB. O gateway é o ponto único de
entrada: quando esgota a memória, **todos** os utilizadores ficam sem serviço (ver ideia 7).
Para o operador, a memória necessária cresce com `tamanho × uploads simultâneos × 3 serviços`,
o que torna o custo imprevisível. Para o utilizador, a aceitação de ficheiros grandes excede o
prazo do requisito.

**Quantificação:**

*Cenário:* upload de vídeo válido (MP4/H.264/AAC, 10 s, 720p) preenchido com uma caixa `free` até
exatamente 10, 100 e 500 MiB, através de nginx e gateway, concorrência 1; 10 e 100 MiB com perfil
free e premium, 500 MiB com premium. *Instrumento:* `uploads.mjs`. Memória: `VmHWM` (pico de RSS
do processo Node desde o `clear_refs` feito antes do pedido) lido em `/proc` — é o pico exato,
sem amostragem. Tempo: cliente HTTP que regista o instante em que o último byte é entregue ao
socket e o instante da resposta; «pós-envio» é a diferença.

| Tamanho | Pico RSS gateway | Pico RSS projects | Pico RSS storage | Tempo total | Aceitação pós-envio |
|---------|------------------|-------------------|------------------|-------------|---------------------|
| 10 MiB (n=5, quente) | +0 a +31 MiB | +0 a +21 MiB | +0 a +21 MiB | 0,23–0,27 s | **155–193 ms** |
| 10 MiB (1.º pedido, frio) | +41 MiB | +26 MiB | +23 MiB | 1,52 s | 1447 ms |
| 100 MiB (n=5) | 114→**480 MiB** (+366 no 1.º) | 138→310 MiB (+172) | 118→281 MiB (+163) | 1,35–2,11 s | **665–1320 ms** (mediana 992) |
| 500 MiB (n=3) | 282→**2050 MiB** (+1767 no 1.º) | 355→1114 MiB (+759) | 329→1058 MiB (+729) | 10,2–11,6 s | **6,7–8,0 s** (mediana 6,9) |

Leituras: o gateway gasta ≈ 3,5× o tamanho do ficheiro; `projects` e storage ≈ 1,5× cada. A
memória **não é devolvida**: depois dos uploads de 500 MiB o gateway ficou com ≈ 1040 MiB de RSS
em repouso (os incrementos seguintes são menores porque reutiliza o que reteve). Um upload de
500 MiB feito a seguir matou o processo do gateway por OOM (2 GiB) e a resposta foi 502.
`REQ-VID-SUBMIT-008` (MVP < 3 s, alvo < 1 s após o envio): **cumprido a 10 MiB, falhado a
500 MiB** (6,7–8,0 s). Esta medição fecha a lacuna registada no exercício 6.

*Mínimo aceitável:* pico de RSS adicional por upload ≤ 64 MiB em cada serviço, para qualquer
tamanho até 500 MiB; aceitação pós-envio < 3 s a 500 MiB (valor MVP do requisito).
*Alvo:* ≤ 32 MiB adicionais, independente do tamanho; pós-envio < 1 s a 10 MiB e < 3 s a
500 MiB; 3 uploads simultâneos de 500 MiB sem reinício de nenhum serviço. Guardas: mesmo SHA-256
guardado, mesmas respostas de validação (400 para duração, tamanho, codec), temporários removidos
após sucesso e após erro, ocupação de disco temporário reportada.

**Decisões a tomar e onde mexer:**

Decisões: (a) *streaming puro* com contrapressão vs. *spool em disco limitado* — o `ffprobe`
precisa de um ficheiro pesquisável e o MP4 pode ter o `moov` no fim, por isso recomenda-se
**um** spool em disco em `projects` e streaming nos outros dois; (b) o gateway passa a ser proxy
de fluxo (sem interpretar o multipart) depois de autenticar; (c) alternativa mais profunda:
upload direto para o S3 por URL pré-assinado de `PUT`, com `projects` a validar depois — muda o
contrato público, pelo que fica como alternativa a discutir — **é a escolhida, com ajustes: ver
«Solução proposta» abaixo**; (d) `proxy_request_buffering` no nginx (hoje o nginx escreve o
corpo em disco antes de o entregar, o que explica parte do pós-envio).

Onde mexer na solução por streaming (alternativa (a)/(b), não escolhida):

- `apiGateway/routes/projects.js`: handlers de `POST /:user/:project/img` e `/video` (substituir
  `upload.single` + `FormData` por `req.pipe` para um pedido `https` a jusante); `checkToken`
  antes de qualquer leitura do corpo.
- `projects/routes/projects.js`: `addProjectMedia` (multer `diskStorage` com `limits.fileSize`
  por perfil, hash por `createReadStream`, `finally` a apagar o temporário); `storage`/`upload`.
- `projects/utils/video.js`: `probeVideoBuffer` → `probeVideoFile(path)`; `ffprobe` mantém-se.
- `projects/utils/imageStorage.js`: `post_image` (corpo em fluxo, já aceita `FormData` com
  streams).
- `imageStorageService/route/upload.js`: trocar `memoryStorage` por parser de fluxo (busboy).
- `imageStorageService/services/uploadImage.js`: `uploadImage` (`Body` como stream;
  `s3.upload` já faz multipart com partes de 5 MiB).
- `nginx/nginx.conf`: `proxy_request_buffering off` e `client_max_body_size` em
  `location /api-gateway/`.
- `docker-compose.yaml`: `mem_limit` nos três serviços, para tornar o orçamento explícito.

**Solução proposta: upload direto para o S3, com o nginx como porteiro.**

Fica escolhida a alternativa (c), com três ajustes que resolvem as suas desvantagens: validação
em dois momentos, hash fora do caminho crítico e S3 invisível para o cliente. Os bytes do vídeo
passam só pelo nginx, que os encaminha em fluxo para o SeaweedFS. Nenhum serviço Node guarda o
ficheiro em memória: o gateway e a `projects` só tratam pedidos JSON de poucos KB. Abrange os
vídeos, onde está o problema medido. As imagens mantêm o caminho atual, com `limits.fileSize` no
multer (ideia 8), e podem migrar para o mesmo fluxo mais tarde.

*Fluxo:*

1. **Pedido de upload.** O frontend faz `POST /:user/:project/video/uploads` (pelo gateway, com
   JWT) com `{ name, size, type, duration, width, height }`. A duração e a resolução são lidas no
   browser por um elemento `<video preload="metadata">`, sem enviar o ficheiro.
2. **Validação prévia.** A `projects` verifica perfil, quota diária e limites
   (`VIDEO_FREE_*`, `VIDEO_PREMIUM_*`) sobre os valores declarados e recusa com as mesmas
   respostas de hoje (400 por duração, tamanho ou tipo; 403 por quota). Se passar, cria o registo
   do media com `status: "pending"` e `expires_at`, fixa a chave definitiva no stage `src` e
   devolve um **token opaco** de uso único, válido por poucos minutos, com o endereço de envio
   (ex.: `/api-gateway/uploads/<token>`).
3. **Envio.** O browser faz `PUT /api-gateway/uploads/<token>` com o ficheiro. É a mesma origem,
   por isso não há CORS.
4. **Porteiro (nginx).** `location /api-gateway/uploads/` faz `auth_request` a uma rota interna
   do gateway. O gateway verifica o JWT como em qualquer pedido e pergunta à `projects`, com a
   identidade assinada (decisão D3 da ideia 1), se o token existe, não expirou, não foi usado e
   pertence a esse utilizador. É uma verificação própria e simplificada (decisão D11 da
   ideia 1): não repete as regras de posse e partilha, porque essas já foram aplicadas no passo 2,
   quando o token foi emitido. A resposta traz num cabeçalho o caminho de `PUT` pré-assinado no
   S3, com o tamanho fixado no valor declarado. O nginx encaminha o corpo para `seaweedfs:9000` em fluxo
   (`proxy_request_buffering off`). O cliente nunca vê o bucket, a chave nem a assinatura.
5. **Confirmação e validação final.** O frontend faz
   `POST /:user/:project/video/uploads/<token>/confirm`. A `projects` corre o `ffprobe` sobre um
   URL interno de leitura (`getInternalUrl`). O `ffprobe` lê por *range requests* só o início do
   ficheiro e o `moov`, mesmo que este esteja no fim, e não o vídeo inteiro. É esta a validação
   que manda, porque os valores do passo 1 podem ser falsos. Compara também o tamanho real
   (`HEAD`) com o declarado. Se falhar, apaga o objeto e o registo e responde 400 como hoje. Se
   passar, marca `status: "ready"` e responde ao utilizador.
6. **Hash em segundo plano.** Depois de responder, a `projects` lê o objeto em fluxo, calcula o
   SHA-256 e grava `og_sha256`. É o único passo que lê o ficheiro todo, mas deixa de contar para
   o tempo de aceitação. O hash só serve de chave da cache de previews (`makePreviewCacheKey` em
   `projects/utils/cacheKey.js`). Enquanto não existir, o preview gera-se sem cache.
7. **Limpeza.** Uma tarefa periódica na `projects` apaga os objetos e registos `pending` com
   `expires_at` ultrapassado: uploads abandonados ou interrompidos e clientes que declararam
   valores falsos e nunca confirmaram.

*Validação em dois momentos.* A validação prévia apanha os erros honestos (vídeo longo demais,
ficheiro grande demais, quota esgotada) antes de se enviar um único byte: o utilizador sabe em
milissegundos, em vez de esperar pelo upload inteiro. A validação final, no servidor, continua a
ser obrigatória e é a única em que se confia. Os objetos órfãos não desaparecem, mas passam a
vir só de uploads interrompidos ou de clientes mal-intencionados, e o passo 7 remove-os.

*S3 invisível, e uma correção ao que existe hoje.* O nginx já expõe hoje `location /s3/` com
`proxy_pass` direto para `seaweedfs:9000`, sem nenhum filtro, e a porta 9000 também está
publicada no host. O SeaweedFS exige assinatura, mas as credenciais de administrador têm valores
por omissão conhecidos (`admin`/`admin123`, ver ideia 9). Por isso esta solução não abre uma
porta nova. O `/s3/` não pode simplesmente ser fechado: o browser carrega media e resultados por
URLs de leitura assinados reescritos para `/s3` (`getPublicUrl` em
`imageStorageService/services/getPresignedUrl.js`). Fica restrito a `GET`/`HEAD`
(`limit_except`), e a porta 9000 passa a ser publicada só em `127.0.0.1` (decisão D5 da
ideia 1). As credenciais do SeaweedFS saem do repositório (decisão D1 da ideia 1). As leituras
podem passar mais tarde pelo mesmo esquema de token opaco.

*Onde mexer:*

- `frontend/lib/projects.ts`: upload de vídeo em três passos (pedido com metadados lidos por
  `<video>`, `PUT` com progresso por `XMLHttpRequest.upload.onprogress`, confirmação).
- `apiGateway/routes/projects.js`: rotas JSON de pedido e confirmação, sem multer; rota interna
  para o `auth_request` (verifica o JWT e consulta a `projects`). A rota multipart
  `POST /:user/:project/video` é retirada.
- `projects/routes/projects.js`: rotas de pedido e confirmação; verificação simplificada do
  token; `addProjectMedia` deixa de receber vídeos; tarefa de limpeza.
- `projects/models/project.js`: `og_sha256` deixa de ser `required`; novos campos `status`,
  `expires_at` e token (ou uma coleção `uploads` própria).
- `projects/utils/video.js`: `probeVideoBuffer` → `probeVideoUrl(url)`.
- `projects/utils/imageStorage.js` e `imageStorageService`: rotas para o URL pré-assinado de `PUT`
  (`getSignedUrlPromise("putObject", …)` com `ContentLength`), `HEAD`, leitura em fluxo para o
  hash e remoção, todas atrás do mTLS (decisão D4 da ideia 1).
- `nginx/nginx.conf`: `location /api-gateway/uploads/` com `auth_request`, `auth_request_set`,
  `proxy_pass` com variável (exige `resolver 127.0.0.11`), `proxy_request_buffering off` e
  `client_max_body_size 1100m` só aqui; `location` interna de autorização com
  `proxy_pass_request_body off`; `/s3/` com `limit_except GET HEAD`; `client_max_body_size`
  global baixado (ideia 8).
- `docker-compose.yaml`: `9000` do `seaweedfs` publicada só em `127.0.0.1`; `mem_limit` nos
  serviços Node.

*A confirmar antes de implementar:*

- Se o SeaweedFS 4.47 respeita o `Content-Length` assinado num `PUT` pré-assinado. Se não, o
  `HEAD` do passo 5 e o `client_max_body_size` cobrem o caso.
- A assinatura v4 inclui o `Host`: o nginx tem de enviar a montante o host com que o URL foi
  assinado (`seaweedfs:9000`), e não o `$host` público.
- O tempo do `ffprobe` por URL com o `moov` no fim (mais leituras por *range*) a 500 MiB.
- Que um `PUT` interrompido a meio não deixa no SeaweedFS um objeto parcial visível.

*Como se avalia:* com os mesmos instrumentos e cenários (`uploads.mjs`, `VmHWM`, 10/100/500 MiB).
Esperado: pico de RSS adicional próximo de 0 nos três serviços Node, porque o gateway só vê JSON,
e memória do nginx constante. O pós-envio passa a ser o `ffprobe` por *range* mais a escrita no
MongoDB, independente do tamanho, previsivelmente < 1 s a 500 MiB (a medir). Guardas novas:
SHA-256 presente pouco depois da resposta e igual ao calculado hoje; mesmas respostas 400/403;
nenhum objeto `pending` depois do prazo de limpeza; 3 uploads simultâneos de 500 MiB sem
reinício de nenhum serviço.

**Avaliação AI: 9 / 10.** *Pertinência* muito alta: afeta o caso de uso central da extensão de
vídeo, tem um requisito escrito que falha (`REQ-VID-SUBMIT-008` a 500 MiB) e o efeito colateral é
a queda do serviço para todos. *Complexidade* alta: três serviços, contrapressão, limpeza de
temporários em todos os caminhos de erro e preservação da validação; a avaliação é exemplar
porque a métrica (pico de RSS por serviço e tempo pós-envio) é objetiva e repetível com os
mesmos ficheiros. Perde um ponto por o cenário medido ser de concorrência 1 e de conteúdo
artificial (caixa `free`).

**Nota: a solução proposta corrige também o incidente da ideia 7.** A queda medida na ideia 7
foi provocada por um upload de 500 MiB que levou o gateway ao OOM. Com esta solução o gateway
deixa de receber o ficheiro e só trata pedidos JSON de poucos KB. A sua memória deixa de crescer
com o tamanho e o número de uploads, e esse gatilho desaparece. Pela mesma razão, o consumo de
memória dos serviços Node passa a ser previsível, e o `mem_limit` pedido na ideia 7 pode ser
fixado sem risco de matar um upload legítimo. Fica por resolver a parte de supervisão da 7: se
o gateway cair por outro motivo (um bug, um `throw` num *callback*), o `nodemon` continua a
impedir o reinício. Essa parte é barata (`node` em vez de `nodemon`, `healthcheck`) e pode entrar
no mesmo trabalho, que assim cobre as duas ideias.

---


## Justificação das decisões

Cada decisão indica a escolha, a razão, as alternativas e porque ficaram de fora. A marca
**«Havia opção mais forte»** assinala os casos em que se escolheu de propósito uma opção menos
forte do que outra disponível, com a razão dessa escolha.

### Ideia 1

**D1. Contra quem nos protegemos: todos os casos (entrada pública, rede e portas, bases de dados
e S3).**
*Porquê:* o objetivo medido é «0 admitidas»; um único caminho aberto anula os restantes. Os
MongoDB sem credenciais e o SeaweedFS com `admin`/`admin123` permitem ler e alterar os dados
sem passar por nenhum serviço, por isso fechar só as camadas de cima deixaria o mesmo dano
acessível por baixo.
*Alternativas:* só a entrada pública (casos G e W) é mais pequena, mas deixa os casos D e as
bases de dados abertos; incluir a rede mas não as bases de dados deixa o bypass mais direto de
todos. *Custo assumido:* mais serviços e configuração, e sobreposição com a ideia 9.

**D2. Quem decide a posse e a partilha: em camadas.**
*Porquê:* o gateway rejeita cedo e barato o que é claramente inválido (JWT inválido, utilizador
do caminho diferente do JWT sem partilha); a `projects`, que é dona dos dados, toma a decisão
final. Se uma camada falhar, a outra continua a proteger.
*Alternativas:* só o gateway não tem os dados dos projetos (teria de os pedir à `projects` em
cada pedido ou duplicá-los) e deixa a `projects` aberta a quem a alcance diretamente; só a
`projects` funciona, mas deixa passar pedidos claramente inválidos até ao serviço de dados.
*Custo assumido:* regras em dois sítios. Para reduzir o risco de divergirem, o gateway só faz
verificações de forma e identidade; a regra de posse e partilha existe só na `projects`.

**D3. Como a `projects` sabe quem chama: identidade assinada pelo gateway.**
*Porquê:* hoje os JWT de utilizador usam HS256, em que quem consegue verificar também consegue
emitir. Dar esse segredo à `projects` acrescentaria um quarto serviço capaz de forjar tokens de
qualquer utilizador. Com a identidade assinada, a `projects` só confia numa chave própria do
gateway, com destinatário e validade curtos, e o formato dos tokens de utilizador não muda.
*Alternativas:* verificar o JWT do utilizador na `projects` com HS256 é o mais simples mas
espalha o segredo; confiar no `X-Caller-Id` depois de isolar a rede deixa qualquer contentor
falsificar a identidade (caso D02).
**Havia opção mais forte:** verificar o próprio JWT do utilizador em todos os serviços, com
**RS256** (só a `users` assina; os restantes têm a chave pública). É a forma mais literal de
«verificada ponta-a-ponta», porque a prova é a do utilizador e não uma emitida pelo gateway, e
um gateway comprometido não poderia criar identidades. *Porque não agora:* obriga a mudar a
emissão de tokens na `users` e todos os verificadores, e invalida as sessões existentes. A
identidade assinada resolve os casos medidos com alterações só no gateway e na `projects`, e
fica compatível com uma migração futura para RS256 (que está em aberto). O risco aceite é que o
gateway passa a ser emissor de confiança, o que na prática já é: vê todos os tokens que passam.

**D4. Identidade de serviço nas chamadas sem utilizador: mTLS.**
*Porquê:* é a única opção em que nenhum segredo vive no código ou em variáveis da aplicação, e a
autenticação é mútua (o cliente também confirma que fala com o serviço certo). Os serviços já
comunicam por HTTPS, com certificados expirados e sem validação (ideia 11), pelo que o mTLS
aproveita e corrige essa infraestrutura.
*Alternativas:* só rede é perímetro (um contentor comprometido na mesma rede tem acesso total);
chave estática dá acesso total se vazar e não expira, num projeto que já tem segredos no
repositório; JWT de serviço tem validade, mas o segredo continua partilhado.
*Custo assumido:* criar uma CA interna, emitir e renovar certificados e configurar clientes e
servidores HTTPS em cada serviço Node. É a opção mais trabalhosa das quatro.

**D5. Rede e portas publicadas: publicar só em `127.0.0.1`.**
*Porquê:* fecha o acesso a partir da rede local (hoje as portas estão em `0.0.0.0`) com uma
alteração de uma linha por porta, e mantém as ferramentas de depuração do dia a dia (consola do
RabbitMQ, MongoDB, SeaweedFS) acessíveis na máquina de quem desenvolve. A proteção contra os
casos D não depende desta decisão: vem da autorização na `projects`, do mTLS e das credenciais
(D1–D4).
**Havia opção mais forte:** retirar as portas do perfil de execução, passando as de depuração
para um ficheiro *override* de desenvolvimento, e **segmentar a rede** (frente, aplicação, dados,
ferramentas), para que uma ferramenta de IA comprometida não chegue à `projects` nem ao MongoDB.
*Porque não agora:* oferece um nível de proteção suficiente em conjunto com D1–D4, continua
favorável à depuração e ao trabalho futuro na aplicação, e evita mapear já todas as dependências
entre os 32 serviços. **Antes de um deploy real em grande escala, aconselha-se** retirar todas as
portas exceto a do nginx e segmentar a rede (liga com a separação de perfis da ideia 7).

**D6.2. Quem entra na sala de um projeto: bilhete assinado pela `projects`.**
*Porquê:* o `ws_gateway` decide sozinho, só com uma chave pública, sem chamadas a outro serviço
em cada `join`, e continua a funcionar se a `projects` estiver lenta ou em baixo. Fica também
fora do esquema da base de dados da `projects`.
*Alternativas:* ler o MongoDB da `projects` atravessa a fronteira entre serviços; enviar os
eventos para as salas de cada utilizador autorizado não funciona com partilhas por link, porque
a `projects` não sabe quem tem o link.
**Havia opção mais forte** (em atualidade da decisão): o `ws_gateway` perguntar à `projects` em
cada `join`, que reflete sempre o estado atual, incluindo uma revogação acabada de fazer. *Porque
não agora:* custa um pedido HTTP por entrada e cria uma dependência em tempo real entre os dois
serviços. O atraso na revogação fica limitado à validade do bilhete, que deve ser curta (em
aberto), e só afeta novos `join`. Quem já está ligado continua a receber eventos em qualquer das
duas opções, o que é tratado à parte em D6.3 (em aberto).

**D8. Modelo de partilha: links com expiração.**
*Porquê:* limita no tempo o dano de um link que vaze, com uma alteração pequena (um campo, uma
verificação, uma opção no diálogo de partilha), sem mudar a forma como se partilha.
*Alternativas:* manter como está deixa os links válidos para sempre, salvo revogação manual.
**Havia opção mais forte:** partilha só com utilizadores convidados (o link deixa de bastar; é
preciso ser a pessoa convidada). *Porque não agora:* é uma alteração funcional (convites, lista
de membros, interface), fora do âmbito de um trabalho de requisitos não funcionais. A expiração
reduz a exposição sem mudar o produto.

**D9. Serviços no âmbito: incluir `users` e `subscriptions`.**
*Porquê:* estão publicados no host e não têm autenticação (por inspeção: `GET /` lista todos os
utilizadores, `PUT /:user` altera o perfil). Deixá-los fora tornaria «0 admitidas» verdadeiro só
dentro de uma matriz incompleta.
*Alternativa:* excluir fecha o âmbito mais cedo, mas teria de ficar escrito como limitação.
*Custo assumido:* mais trabalho, sobreposição com a ideia 5 e possibilidade de encontrar mais
casos abertos ao medir.

**D11. Token de upload da ideia 2: verificação própria e simplificada.**
*Porquê:* a autorização completa (posse, partilha, perfil, quota) é feita uma vez, quando o token
é emitido (passo 2 da ideia 2). No `auth_request` basta confirmar que o token existe, não
expirou, não foi usado e pertence ao utilizador do JWT. Mantém o caminho do upload independente
das regras gerais.
**Havia opção mais forte:** reutilizar o mesmo código de posse e partilha da ideia 1 também no
`auth_request`, para haver uma só regra. *Porque não agora:* a verificação do token não repete
essas regras, só confirma uma autorização já dada, por isso o risco de divergência é baixo. Fica
mitigado com casos na matriz: token reutilizado, token de outro utilizador e token expirado.

**Pontos em aberto (sem decisão):** D7 (o parâmetro `owner`, que é redundante em todos os casos,
validado ou ignorado), D10 (como medir: só do host, ou também de dentro da rede; que casos
novos entram), D6.1 (ligações WebSocket sem token), D6.3 (expulsar sockets após revogação ou
expiração), JWT de utilizador em HS256 ou RS256, regra para links existentes sem `expiresAt`, e
validades do bilhete e da identidade assinada.

### Ideia 2

**Upload direto para o S3 com o nginx como porteiro** (em vez de streaming pelos três serviços
Node).
*Porquê:* os bytes do vídeo passam só pelo nginx, que é feito para isto; nenhum serviço Node
guarda o ficheiro em memória, por isso o problema de memória deixa de existir em vez de ficar
apenas limitado. Evita a parte mais difícil do streaming: contrapressão e limpeza de temporários
em três serviços. O contrato visto pelo cliente continua a ser um endpoint da API, sem S3 visível.
*Alternativa:* streaming pelos três serviços, com uma cópia temporária na `projects`. Não muda o
frontend e mantém a validação antes de guardar, mas os serviços Node continuam no caminho dos
bytes e a implementação toca em três serviços com casos de erro difíceis.
*Custo assumido:* o frontend passa a fazer três passos; é preciso a tarefa de limpeza; e há
pontos a testar no SeaweedFS (listados na ideia).

**Validação em dois momentos.**
*Porquê:* a validação prévia, sobre os metadados lidos no browser, avisa o utilizador em
milissegundos antes de enviar o ficheiro; a final, com `ffprobe` no servidor, é a única em que
se confia. *Alternativa:* só validar depois, o que obriga a enviar ficheiros que vão ser
recusados.

**Hash em segundo plano.**
*Porquê:* o SHA-256 só serve de chave da cache de previews, por isso pode chegar depois da
resposta. O tempo de aceitação deixa de depender do tamanho do ficheiro.
*Alternativas:* calcular no cliente e confirmar no S3 (`x-amz-checksum-sha256`) evitaria ler o
ficheiro no servidor, mas não se sabe se o SeaweedFS suporta esse cabeçalho; usar o ETag do S3
não serve, porque nos uploads multipart não é o hash do conteúdo.
**Havia opção mais forte**, se o SeaweedFS a suportar: o hash calculado no cliente e confirmado
pelo S3, que dispensa a leitura no servidor. Fica para depois de testar o suporte.

**S3 invisível, com o nginx como porteiro.**
*Porquê:* o cliente só vê um endereço opaco da própria API; não há CORS nem assinaturas expostas.
O `/s3/` público não pode ser fechado, porque o browser carrega media por URLs de leitura
assinados, por isso fica limitado a `GET`/`HEAD`.
*Alternativa:* entregar ao cliente o URL pré-assinado do S3, que é mais simples mas expõe o
bucket, a chave e a assinatura e obriga a configurar CORS.

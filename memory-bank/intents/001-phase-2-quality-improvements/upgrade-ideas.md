# PictuRAS — Fase 2: catálogo de upgrades não funcionais

Levantamento das possibilidades de melhoria não funcional encontradas no checkout
`66bc6f9`, com medições feitas a 16/11/2026. Estende o trabalho existente (QC-01 a QC-06,
`team-review.md`, `live-findings.md`); onde uma ideia corresponde a uma direção já estudada, isso
está indicado. Classificação segundo a ISO/IEC 25010:2011, como pedem as diretrizes.

## Como ler este documento

**Ambiente comum das medições novas (16/11).** MacBook Apple M4 Pro (12 núcleos, 24 GB), Docker
Desktop 28.5.1 (VM Linux arm64 com 12 CPU e 7,65 GiB). Stack isolado `picturas-nfr`, construído a
partir deste checkout, com 13 serviços (nginx, api_gateway, ws_gateway, projects, users,
img_storage, seaweedfs, rabbitmq, 2 MongoDB, video_tool, brightness_tool, border_tool), volumes
próprios e portas em `127.0.0.1` deslocadas. Limite de 2 CPU / 2 GiB em `api_gateway`, `projects`,
`img_storage` e `video_tool`; os restantes sem limite, como no `docker-compose.yaml`. Cliente de
carga: Node 22 no host. Scripts e resultados brutos em
[`evidence/nfr-2026-11-16/`](evidence/nfr-2026-11-16/).

**Limitações que valem para tudo.** Amostras pequenas (2–3 repetições): são pilotos, não
percentis. O relatório de origem refere 26 contentores de outro checkout
(`picturas-27-extension`), mas a expressão «parados-mas-ativos» não permite saber o seu
estado/carga. Esse ruído fica por caracterizar no manifesto da baseline formal. `frontend`, `subscriptions` e as
ferramentas de IA não entraram no stack; o que lhes diz respeito está marcado como **não medido**.
Os valores «mínimo aceitável» e «alvo» são **propostas de engenharia** para a equipa discutir,
exceto quando vêm de um requisito existente (indicado caso a caso).

**Estado da revisão de 16/11.** As notas AI são juízos qualitativos e não prioridades
aprovadas ou classificação docente. As ideias 1/2 estão sincronizadas com
[o extrato de decisões e justificação](../../../docs/fase2-ideias-1-e-2.md).
O [plano de métricas e baseline](../../../docs/fase2-metricas-e-baseline.md) contém os
critérios e a auditoria dos resultados. As lacunas não foram convertidas em zeros,
nem as propostas em decisões fechadas. O acordo do par 1 + 2 está agora registado
por instrução explícita do utilizador para PL2-G4; ver o
[registo coletivo](quality-exploration.md#decision-record--pair-agreement).
O acordo seleciona as áreas QC-06 Segurança/autorização ponta a ponta e QC-05
Eficiência de desempenho/recursos dos uploads; os detalhes e métricas pendentes
mantêm o seu estado.


**Validação individual posterior à revisão:** o utilizador confirmou D3/JWT
(HS256 utilizador e RS256 interno, com transição de sessões antes de renovar o
segredo), D7 (`owner` opcional, único e coincidente) e D6.1 (JWT obrigatório na
ligação Socket.IO, também para anónimos). Posteriormente escolheu D6.2 B + D6.3 A:
consultar projects em cada entrada e retirar ativamente o acesso quando a autorização
efetiva terminar. O assistente confirmou a proporcionalidade com confiança média;
a simplicidade é uma inferência, não uma medição. Validou depois A/A/A: revalidar
inicialmente a cada 1 s, agrupando por projeto com autorização individual/contextual;
critério de corte ≤5 s, meta ≤2 s, local até 5 s desde início da consulta positiva,
limitado por JWT/permissão, sem renovação por falhas ou restauro indevido por respostas
obsoletas; negação efetiva retira já. JWT expirado termina a ligação; frontend trata
reconexão explicitamente com JWT válido e nova autorização por sala. Eventos ficam
como evolução. Critérios/carga ainda por ensaiar; transição/renovação deve preservar
identidade e projetos anónimos. Estas validações de detalhe permanecem individuais;
o restante contrato, corridas e outros pontos mantêm-se em aberto; ver a atualização
seguinte para a escolha de mTLS e dos parâmetros iniciais de timeout/lote.

**Atualização individual D4/WS-C1/WS-C2:** mTLS é a escolha para autenticar serviços
internos; HTTPS + JWT assimétrico de serviço fica substituído, conforme a escolha
anterior agora referida pelo utilizador. D3 mantém HS256 de utilizador/RS256 do
gateway. WS-C1 A valida consulta direta com autenticação específica do WS e
delegação explícita da identidade/expiração verificadas; projects decide permissões.
WS-C2 A valida timeout total inicial 1 s/até 50 avaliações por pedido, configuráveis,
com concorrência limitada e agendamento justo entre lotes; falhas/tentativas não
prolongam autorização. Critérios de corte mantidos; sem capacidade demonstrada.
O restante contrato e operacionalização da PKI continuam para revisão, sem atribuir
aprovação aos restantes elementos, testes executados ou autorização para código.

**Validação individual WS-C3/PKI-C1/ACL-C1:** limites iniciais WS de 4 consultas
HTTP globais/1 por projeto, alternância e 64 KiB por corpo JSON, em conjunto com
50 avaliações/timeout total 1 s incluindo fila. Fila limitada com máximo ainda por
escolher; excesso nunca é truncado em silêncio e falhas não renovam autorizações.
Quatro simultâneas não demonstram 4/s nem capacidade para 20 projetos; testar >20
e um projeto de 500 membros com vários pequenos. PKI: CA por instalação 365 dias,
serviço 30 dias, renovar com 7 dias restantes; script local manual e verificações
na entrega, sem daemon automático. Auditoria Git/build encontrou lacunas, não
proteção demonstrada; revogação/ligações persistentes pendentes. ACL: só dono
elimina projeto inteiro, editor mantém remoção de media; mudança de política
explícita, não restrição DELETE inequívoca herdada dos RF. Restantes decisões e
ensaios mantêm-se pendentes, sem alterações à aplicação. Ver justificação completa
no [documento de decisões](../../../docs/fase2-ideias-1-e-2.md#justificação-das-decisões).

**Resumo ordenado por nota.**

| # | Ideia | Tipo (ISO 25010) | Nota | Origem |
|---|-------|------------------|------|--------|
| 1 | Autorização verificada ponta-a-ponta | Segurança | 9,5 | QC-06 alargada |
| 2 | Upload em streaming com memória limitada | Eficiência de desempenho | 9 | QC-05 + REQ-VID-SUBMIT-008 |
| 3 | Entrega fiável e retoma de trabalhos | Fiabilidade | 9 | QC-01 + prioridade PL1-G4 |
| 4 | Erros das ferramentas e trabalhos órfãos | Fiabilidade | 8 | novo |
| 5 | Integridade do perfil e da subscrição | Segurança | 7,5 | novo |
| 6 | Capacidade de processamento de vídeo | Eficiência de desempenho | 7,5 | QC-02 |
| 7 | Disponibilidade do gateway e supervisão | Fiabilidade | 7,5 | novo |
| 8 | Admissão de uploads antes de os carregar | Segurança / Fiabilidade | 7 | novo |
| 9 | Segredos e superfície de rede interna | Segurança | 7 | prioridade PL1-G4 |
| 10 | Quota diária atómica | Fiabilidade / Segurança | 7 | novo |
| 11 | TLS interno válido | Segurança | 6,5 | prioridade PL1-G4 |
| 12 | Estado e progresso recuperáveis | Usabilidade | 6,5 | QC-04b |
| 13 | Modularidade dos efeitos | Manutenibilidade | 6 | QC-03 |
| 14 | Logs sem segredos e observabilidade | Manutenibilidade / Segurança | 6 | novo |
| 15 | Cancelamento efetivo e prazo global | Eficiência / Fiabilidade | 5,5 | REQ-VID-CANCEL/TIMEOUT |
| 16 | Canal AMQP persistente no orquestrador | Eficiência / Fiabilidade | 5 | novo |
| 17 | Usabilidade da criação do pipeline | Usabilidade | 4,5 | QC-04a |
| 18 | Imagens reprodutíveis e leves | Portabilidade | 4,5 | novo |
| 19 | Exportação ZIP em streaming | Eficiência de desempenho | 4 | QC-05 (extensão) |

**Par acordado — fundamentação.** As três primeiras têm fragilidade demonstrada, métrica própria e
refactoring exigente. O par **1 + 2** corresponde à recomendação histórica da `team-review.md`, agora com evidência
bem mais forte (o problema de autorização está no gateway público e não só na rede interna; o de
memória derruba o gateway). **3** é a alternativa natural se a equipa quiser cobrir a prioridade
do PL1-G4 (ack manual e retoma); fica como alternativa documentada ao par acordado.
As ideias 4, 5, 8 e 10 são pequenas e podem ser absorvidas
como parte de 1, 2 ou 3 sem serem um RNF autónomo.

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

O extrato original reportava **10 admissões em 13 casos**, mas esse total precisa de
revalidação: G02 usa um campo ausente da resposta, D06 não confirma o hash do objeto e D05
começa com uma fixture sem projetos. Os JSON, incluindo o conjunto maior de 22 casos, foram
preservados. O plano de métricas distingue efeito verificado, resposta HTTP e caso inconclusivo.
G03/G04 e W01 sustentam alterações/divulgação indevidas; não usar um total global corrigido
sem voltar a executar a matriz com asserções completas. O controlo de leitura do dono passou.
Os casos diretos usam loopback da stack ARM; a exposição da configuração original e a
alcançabilidade efetiva são medições separadas.

*Mínimo aceitável e alvo:* **0 admitidas** na matriz acordada, com **100% dos controlos
positivos** a passar (dono, partilha de leitura, partilha de edição, worker a guardar
resultados, preview e exportação). Mínimo e alvo coincidem porque um único bypass conhecido
anula o objetivo. Guarda: sobrecarga por pedido medida e ≤ 10 ms em mediana (proposta).

**Solução proposta.**

*Escolhas assinaladas no documento de origem (não confundir com implementação ou aprovação final):*

| # | Decisão | Escolha |
|---|---------|---------|
| D1 | Contra quem nos protegemos | Todos os casos: entrada pública (G, W), rede Docker e portas dos serviços (D), bases de dados e S3 diretos |
| D2 | Quem decide a posse e a partilha | Em camadas: o gateway faz as verificações baratas, a `projects` decide |
| D3 | Como a `projects` sabe quem chama | RS256 na identidade interna do gateway, validado pelo utilizador; JWT de utilizador mantém HS256 com plano prévio de transição de sessões |
| D4 | Autenticação entre serviços internos | mTLS validado individualmente; HTTPS + JWT assimétrico de serviço substituído; D3 mantém as funções dos JWT |
| D5 | Rede e portas publicadas | Publicar só em `127.0.0.1` |
| D6.1 | Autenticação da ligação Socket.IO | JWT válido obrigatório, também para anónimos; validado pelo utilizador |
| D6.2 | Quem entra na sala de um projeto | Consulta à projects por entrada, opção B escolhida pelo utilizador; bilhetes WS adiados |
| D6.3 | Permanência na sala | Revalidação periódica inicial de 1 s, agrupada por projeto e individual por contexto; corte ≤5 s, meta ≤2 s, escolhidos individualmente e ainda por medir |
| D7 | Tratamento de owner | Ausente permitido; se presente, único e igual ao dono no caminho; contraditório recusado; validado pelo utilizador |
| D8 | Modelo de partilha | Links com expiração |
| D9 | Serviços no âmbito | Incluir `users` e `subscriptions` |
| D11 | Token de upload da ideia 2 | Verificação própria e simplificada |

*Como fica cada fronteira:*

1. **Gateway (pedidos de utilizador).** Verifica o JWT como hoje e mantém a verificação barata
   (sem `share`, o utilizador do caminho tem de ser o do JWT). Depois emite uma **identidade
   assinada em RS256** de curta duração, `{ sub, share?, aud, iat, exp }`, com uma chave
   privada própria do gateway e apenas a chave pública nos verificadores; não partilha
   o segredo HS256 dos JWT de utilizador. Envia-a num cabeçalho dedicado. O
   `X-Caller-Id` deixa de existir.
2. **`projects`.** Nos pedidos encaminhados pelo gateway, verifica a assinatura,
   o destinatário (`aud`) e a validade dessa identidade e
   deriva dela o chamador (`getCallerId`). Não precisa do segredo dos JWT de utilizador. É ela
   que decide: sem `share`, exige chamador = dono em todas as rotas, incluindo `GET`, `POST` e
   `DELETE /:user` e `/presence`; com `share`, aplica a regra atual (`checkSharePermission`) e a
   expiração (ponto 8). A rota interna WS autentica o serviço por mTLS e recebe a
   delegação validada em WS-C1; não exige que WS emita identidade RS256 de gateway.
3. **Chamadas entre serviços internos** (incluindo `projects` → `img_storage`,
   `projects` → `users` para a quota e `ws_gateway` → `projects`). mTLS: o serviço chamado só aceita ligações com um
   certificado de cliente emitido por uma CA interna do projeto e com a identidade esperada. Os
   certificados são novos (os atuais estão expirados, ideia 11), com emissão/renovação
   e proteção de chaves fora do repositório. A matriz de pares/operações de D4 limita
   a confiança; mTLS não substitui HS256/RS256 de D3 nem autorização de domínio.
4. **`ws_gateway` — D6.2 B + D6.3 A.** Exige JWT válido na ligação, incluindo sessões
   anónimas. Em cada pedido de entrada, consulta a projects por um canal autenticado;
   a projects verifica o acesso atual do utilizador ao projeto/sala. Só uma autorização
   positiva permite o join. Indisponibilidade/timeout não concede acesso: a entrada é
   recusada temporariamente e pode ser tentada de novo. Não são emitidos bilhetes de
   sala. Para membros já presentes, retirar o acesso quando deixarem de ter autorização
   efetiva, preservando outras salas e vias legítimas. Revalidar inicialmente a cada
   1 s, agrupando por projeto sem agregar a decisão de cada membro/contexto. A
   autorização local não excede 5 s desde o início da consulta positiva, nem a validade
   do JWT/permissão; falhas não a prolongam e respostas obsoletas não restauram acesso.
   Negação efetiva explícita retira imediatamente o acesso afetado. Critério de corte
   ≤5 s, meta ≤2 s, ainda por ensaiar. Ao expirar o JWT, terminar a ligação; o frontend
   trata explicitamente a reconexão válida e a nova autorização das salas.
5. **`users` e `subscriptions`.** Entram na matriz. Autenticam o serviço chamador por
   mTLS e limitam as operações conforme D4; pedidos delegados pelo gateway mantêm a
   identidade RS256 de D3 quando aplicável, com exceções de login/registo explícitas.
   Autenticação de serviço não substitui a autorização de conta/billing. Sobrepõe-se à ideia 5.
6. **Bases de dados e S3.** MongoDB com utilizador e palavra-passe por serviço; SeaweedFS com
   credenciais fora do repositório. Sobrepõe-se à ideia 9.
7. **Portas.** Todas as portas publicadas, exceto a do nginx (8080), passam a
   `127.0.0.1:<porta>`. A rede `elk` mantém-se única. A proteção contra os casos D vem dos
   pontos 2 a 6, não das portas.
8. **Partilha com expiração.** Novo campo `sharedLinks[].expiresAt`; `checkSharePermission`
   responde 410 depois dessa data; o diálogo de partilha permite escolher a validade.

*Em aberto (por decidir):*

- **D7 já validada individualmente:** parâmetro ausente permitido; presente exige valor
  único igual ao dono no caminho. Não voltar a tratá-la como escolha entre validar/ignorar.
  Testar ausência, coincidência, contradição e entradas multivalor, preservando partilha.
  Em `buildQuery`, o cliente principal omite a query sem partilha; não é necessário
  obrigá-lo a acrescentar `owner`.
- **D10, como medir.** Com as portas em `127.0.0.1`, os casos D continuam alcançáveis a partir
  do host, é possível ensaiar o host se a rede/configuração o permitir; rejeições HTTP, TLS e de rede devem ser registadas separadamente. Fica por decidir se se repete a
  matriz a partir de dentro de um contentor da rede `elk`, e que casos novos entram (partilha
  expirada e revogada, leitura vs. edição, consulta de join e autorização indisponível, token de upload da
  ideia 2).
- **D6.1 já validada individualmente:** recusar a ligação Socket.IO sem JWT válido.
- **D6.2 B já escolhida individualmente:** consulta à projects por entrada; WS-C1 A
  e WS-C2 A validam mTLS direto e timeout total inicial 1 s. Rever os payloads e o
  tratamento de uma permissão que mude durante o join.
- **D6.3 A e condições já validadas individualmente:** consultas iniciais a cada 1 s,
  agrupadas por projeto e individualizadas por membro/contexto; corte ≤5 s, meta ≤2 s;
  autorização local limitada desde o início da consulta positiva, sem extensão por
  falha; negação efetiva retira de imediato; JWT expirado termina a ligação. Falta
  rever o restante contrato e ordenação/corridas; 50 avaliações/timeout total inicial
  1 s e WS-C3 (4 globais/1 por projeto/64 KiB) estão validados, sem capacidade medida.
  O tamanho máximo da fila continua por decidir, com recusa e ausência de renovação
  em saturação/espera excessiva.
  Não retirar acesso só porque um dos links terminou se outra via continuar válida.
- **Transição das sessões antes da renovação HS256:** definir utilizadores registados,
  sessões anónimas, projetos associados, reautenticação e comportamento dos sockets.
  O algoritmo foi fechado nesta fase (HS256 utilizador, RS256 identidade interna),
  mas a estratégia de transição e a validade/rotação das chaves não foram escolhidas.
- **Links existentes** (sem `expiresAt`): sem validade, ou com uma validade por omissão.
- **Validades** da identidade interna, sessões e tokens de upload; o desenho atual
  não usa bilhetes WS, pelo que não há TTL de bilhete de sala a escolher nesta fase.

*Onde mexer:*

- `apiGateway/routes/projects.js`: deixar de usar `req.query.owner` como dono sem validação
  (regra de valor único validada em D7); trocar `X-Caller-Id` pela identidade RS256 nas 22 rotas;
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
  que confia no `X-Caller-Id`); disponibilizar autorização de sala ao ws_gateway,
  sem emitir bilhete WS no GET do projeto.
- `projects/utils/imageStorage.js`, `projects/utils/presence.js` e as chamadas à `users`: cliente
  HTTPS com certificado de cliente (mTLS).
- `imageStorageService/server.js`, `users/bin/www`, `subscriptions/bin/www`: servidor HTTPS a
  exigir certificado de cliente; `users` e `subscriptions` aceitam também a identidade assinada
  do gateway.
- `wsGateway/index.js`: JWT conforme D6.1, consulta autenticada à projects antes de
  cada join, recusa temporária em falha e remoção de membros conforme D6.3.
- `frontend/lib/projects.ts` e `frontend/app/dashboard/[pid]/page.tsx`: transmitir o
  contexto necessário ao join e tratar recusa/nova tentativa; não gerir bilhetes WS.
  O diálogo de partilha com validade mantém a revisão funcional/migração pendente.
- `docker-compose.yaml`: portas em `127.0.0.1`; credenciais do MongoDB e do SeaweedFS; chaves
  da identidade assinada e certificados mTLS montados a partir de fora do
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
do processo Node desde o `clear_refs` feito antes do pedido) lido em `/proc` — é uma leitura de high-water mark do processo,
com limitações de contabilização e de janela; não é um pico exato de todos os serviços. Tempo: cliente HTTP que regista o instante em que o último byte é entregue ao
socket e o instante da resposta; «pós-envio» é a diferença.

| Tamanho | Pico RSS gateway | Pico RSS projects | Pico RSS storage | Tempo total | Aceitação pós-envio |
|---------|------------------|-------------------|------------------|-------------|---------------------|
| 10 MiB (n=5, quente) | +0 a +31 MiB | +0 a +21 MiB | +0 a +21 MiB | 0,23–0,27 s | **155–193 ms** |
| 10 MiB (1.º pedido, frio) | +41 MiB | +26 MiB | +23 MiB | 1,52 s | 1447 ms |
| 100 MiB (n=5) | 114→**480 MiB** (+366 no 1.º) | 138→310 MiB (+172) | 118→281 MiB (+163) | 1,35–2,11 s | **665–1320 ms** (mediana 992) |
| 500 MiB (n=3) | 282→**2050 MiB** (+1767 no 1.º) | 355→1114 MiB (+759) | 329→1058 MiB (+729) | 10,2–11,6 s | **6,7–8,0 s** (mediana 6,9) |

Leituras: no primeiro cenário de 500 MiB o incremento observado foi ≈3,5× no gateway e
≈1,5× nos outros serviços. Não é uma lei para todos os tamanhos. Parte da memória ficou
retida durante a observação: depois dos uploads de 500 MiB o gateway ficou com ≈ 1040 MiB de RSS
em repouso (os incrementos seguintes são menores porque reutiliza o que reteve). Um upload de
500 MiB feito a seguir matou o processo do gateway por OOM (2 GiB) e a resposta foi 502.
No marcador de envio do cliente adotado pelo instrumento, os 500 MiB excederam 3 s
(6,7–8,0 s); os 10 MiB cumpriram o MVP, embora o primeiro pedido de 1447 ms não cumprisse
o alvo de 1 s. O evento de envio significa entrega ao SO do cliente, não receção final
no servidor. Esta evidência reduz a lacuna anterior, mas não congela a baseline formal.

*Mínimo aceitável:* pico de RSS adicional por upload ≤ 64 MiB em cada serviço, para qualquer
tamanho até 500 MiB; aceitação pós-envio < 3 s a 500 MiB (valor MVP do requisito).
*Alvo proposto para revisão:* ≤32 MiB adicionais por serviço e cenário, com 3 uploads
simultâneos de 500 MiB sem reinícios. O plano de métricas propõe distinguir <3 s como
mínimo pós-envio e <1 s como meta também a 500 MiB; isso corrige a ambiguidade anterior
de repetir <3 s no mínimo e na meta. Os valores não ficam aprovados por esta revisão. Guardas: mesmo SHA-256
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

O documento de origem assinala a preferência pela alternativa (c), com três ajustes que resolvem as suas desvantagens: validação
em dois momentos, hash fora do caminho crítico e S3 invisível para o cliente. No envio, os bytes do vídeo
passariam pelo nginx para o SeaweedFS, retirando os serviços Node desse percurso. A
`projects` continuaria a ler o objeto se o hash fosse calculado em segundo plano; essa
leitura usa buffers e tem de entrar nas medições de CPU, rede e memória. Abrange os
vídeos, onde está o problema medido. As imagens mantêm o caminho atual, com `limits.fileSize` no
multer (ideia 8), e podem migrar para o mesmo fluxo mais tarde.

*Fluxo:*

1. **Pedido de upload.** O frontend faz `POST /:user/:project/video/uploads` (pelo gateway, com
   JWT) com `{ name, size, type, duration, width, height }`. A duração e a resolução são lidas no
   browser por um elemento `<video preload="metadata">`, sem enviar o ficheiro.
2. **Validação prévia.** A `projects` verifica perfil, quota diária e limites
   (`VIDEO_FREE_*`, `VIDEO_PREMIUM_*`) sobre os valores declarados. A validação real continua no servidor. A pré-condição de
   quota no upload exige uma decisão de preservação funcional: hoje a quota é debitada no
   Apply, não no upload; não chamar «mesmas respostas de hoje» à recusa nova de um upload
   só porque o saldo é zero. Se passar, cria o registo
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
   S3, com a intenção de limitar o tamanho ao valor declarado (suporte a comprovar). O nginx encaminha o corpo para `seaweedfs:9000` em fluxo
   (`proxy_request_buffering off`). O cliente não receberia o destino de escrita; os URLs de leitura atuais continuam a existir.
5. **Confirmação e validação final.** O frontend faz
   `POST /:user/:project/video/uploads/<token>/confirm`. A `projects` correria o `ffprobe` sobre um
   URL interno gerado pelo servidor (`getInternalUrl`). A leitura por HTTP pode usar seeks/
   ranges se o servidor e o formato o permitirem; é uma hipótese medir menos bytes do que o
   ficheiro, não uma garantia de ler apenas o início e o `moov` em todos os formatos. É esta a validação
   que manda, porque os valores do passo 1 podem ser falsos. Compara também o tamanho real
   (`HEAD`) com o declarado. Se falhar, apaga o objeto e o registo e responde 400 como hoje. Se
   passar, marca `status: "ready"` e responde ao utilizador.
6. **Hash em segundo plano.** Depois de responder, a `projects` lê o objeto em fluxo, calcula o
   SHA-256 e grava `og_sha256`. É uma leitura integral posterior à resposta; o
   ffprobe pode também ler uma parte substancial, dependendo do ficheiro. O custo completo
   tem de entrar na avaliação, mesmo fora do tempo até ready. No código inspecionado o hash participa na chave da cache de previews
   (`makePreviewCacheKey` em `projects/utils/cacheKey.js`). Enquanto faltar, é necessário
   contornar tanto a leitura como a escrita da cache, ou usar isolamento equivalente;
   usar uma chave com hash vazio permite confundir media diferentes. A retoma/idempotência
   do hash após reinício também tem de ser definida.
7. **Limpeza.** Uma tarefa periódica na `projects` apaga os objetos e registos `pending` com
   `expires_at` ultrapassado: uploads abandonados ou interrompidos e clientes que declararam
   valores falsos e nunca confirmaram.

*Validação em dois momentos.* A validação prévia pode detetar os erros honestos de
metadados antes de transferir o corpo; o prazo é uma meta a medir. O tratamento da quota
no upload não está fechado, porque pode mudar uma condição funcional existente. A validação final, no servidor, continua a
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
  para o `auth_request` (verifica o JWT e consulta a `projects`). A retirada da rota multipart
  `POST /:user/:project/video` precisa de decisão de compatibilidade/adaptação antes de código.
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

- Se o SeaweedFS 4.47 respeita o tamanho assinado e como processa corpos chunked/interrompidos.
  O `HEAD` deteta uma diferença **depois** de transferir os bytes; o limite global do nginx
  não assegura o limite de cada perfil nem a declaração de cada upload. É preciso um
  mecanismo de admissão/contagem por pedido para a proteção de recursos pretendida.
- A assinatura v4 inclui o `Host`: o nginx tem de enviar a montante o host com que o URL foi
  assinado (`seaweedfs:9000`), e não o `$host` público.
- O tempo do `ffprobe` por URL com o `moov` no fim (mais leituras por *range*) a 500 MiB.
- Que um `PUT` interrompido a meio não deixa no SeaweedFS um objeto parcial visível.

*Como se avalia:* com os mesmos instrumentos e cenários (`uploads.mjs`, `VmHWM`, 10/100/500 MiB).
Hipótese a testar: RSS adicional limitado nos serviços Node e no nginx, contando também
o hash assíncrono, TLS e concorrência. O pós-envio tem de incluir a confirmação e validação
final; não se demonstra independência do tamanho sem medir ranges, formatos e estágios.
A meta <1 s a 500 MiB continua proposta, não resultado. Guardas novas:
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

**Relação com a ideia 7 — hipótese de reduzir o gatilho de OOM.** O ensaio sequencial
registou OOM no gateway após um upload de 500 MiB. Retirar o corpo do gateway poderá
eliminar esse tipo de buffer, mas pedidos simultâneos, TLS, hash e storage continuam a
consumir recursos. Os budgets de memória e a disponibilidade precisam de medições completas;
não se pode garantir ausência de OOM antes dos ensaios. Fica por resolver a supervisão: se
o gateway cair por outro motivo (um bug, um `throw` num *callback*), o `nodemon` continua a
impedir o reinício. Essa parte é barata (`node` em vez de `nodemon`, `healthcheck`) e pode entrar
no mesmo trabalho, que assim cobre as duas ideias.

---

## Ideia 3: Entrega fiável e retoma de trabalhos

**Tipo:** Fiabilidade — tolerância a falhas e recuperabilidade (`REQ-VID-FAIL-004`).

**Ideia:** Garantir que um trabalho aceite («Apply» respondeu 201) chega sempre a um desfecho
visível — resultado ou erro — mesmo que o broker, um worker ou o orquestrador reiniciem a meio:
mensagens persistentes, confirmação de publicação, *ack* manual só depois de o efeito estar
persistido, consumo idempotente e uma fila de mensagens mortas.

**Situação base:** As filas são duráveis mas as mensagens são publicadas como transitórias. As
ferramentas de imagem consomem com `auto_ack=True`. O orquestrador confirma a mensagem antes de
o *callback* assíncrono terminar e apaga o registo `Process` antes de guardar o resultado. Só o
`video_tool` faz *ack* manual no fim. É uma das prioridades deixadas pelo PL1-G4.

**Diagnóstico completo:**

```python
# Tools/utils/rabbit_mq.py — todas as ferramentas de imagem
self._channel.basic_publish(exchange="picturas", routing_key=queue, body=msg)   # sem delivery_mode=2
self._channel.basic_consume(queue=self._queue, on_message_callback=callback, auto_ack=True)
```

```js
// projects/utils/rabbit_mq.js
channel.publish(exchange, queue, Buffer.from(JSON.stringify(msg)));   // sem { persistent: true }, sem confirm
...
channel.consume(q.queue, (msg) => {
    callback(msg);            // async: devolve uma Promise que ninguém espera
    channel.ack(msg);         // confirmado antes de o resultado existir
});

// projects/routes/projects.js — process_msg()
if (!holdsRunCommit) await Process.delete(process.user_id, process.project_id, process._id);
...                           // só depois: upload para o S3 e Result.create(result)
```

```python
# Tools/video/video.py
heartbeat=0,                                              # ligação morta nunca é detetada
self._channel.basic_publish(exchange=EXCHANGE, routing_key=queue, body=json.dumps(msg))  # resposta transitória
```

Janelas de perda: (1) broker reinicia com mensagens em fila → desaparecem; (2) ferramenta de
imagem morre a meio → mensagem já confirmada, perdida; (3) orquestrador morre entre o `ack` e o
`Result.create` → resultado processado mas nunca guardado; (4) a resposta do worker de vídeo é
transitória. Em todos os casos o registo `Process` fica pendente para sempre, a operação diária
já foi debitada e o utilizador vê o ecrã de progresso sem fim. Para o utilizador free isso é
perder 1 das 5 operações do dia sem receber nada; para o operador são trabalhos-fantasma que só
se resolvem à mão na base de dados.

**Quantificação:**

*Cenário R3:* utilizador free, projeto com 1 vídeo de 10 MiB e `brightness`; worker de vídeo
parado, «Apply» aceite (201), `docker restart` do RabbitMQ, worker arrancado, observação de 45 s.
*Instrumento:* `reliability.mjs R3`; contagem de mensagens com `rabbitmqctl list_queues`,
saldo pela API, registos `Process` pelo MongoDB.

| Medida | Antes do reinício | Depois |
|--------|-------------------|--------|
| Mensagens em `video_queue` | 1 | **0** |
| Operações restantes do utilizador | 5 | **4** (debitada) |
| Registos `Process` pendentes | — | **+1**, sem fim |
| Resultados ao fim de 45 s | — | **0** (ZIP vazio) |

Ou seja: **1 trabalho aceite em 1 perdido** nesta janela, com débito de quota. Evidência
anterior que se mantém: `ack-order-2026-11-14.json` mostra o `ack` antes de o *callback*
terminar; `live-recovery-2026-11-14.json` mostra que a morte do **worker de vídeo** a meio já é
recuperada (1 resultado, 1 débito, 26,3 s) — é a única janela coberta hoje. *Cenário R2:*
reinício do broker em repouso: os consumidores estavam presentes na primeira amostra
5 s após o regresso da API de gestão (esta demorou 5609 ms), mas porque `projects`,
`video_tool` e as ferramentas **crasham e são reiniciados** pelo Docker (4 de 5 contentores
reiniciados; só o `ws_gateway` religa sozinho).

*Mínimo aceitável:* em 5 pontos de injeção (broker com mensagem em fila; ferramenta de imagem a
meio; worker de vídeo a meio; orquestrador depois de receber a resposta e antes de guardar;
broker durante a resposta), repetidos 5 vezes cada, **≥ 24 de 25** trabalhos aceites terminam com
resultado correto ou erro explícito ao utilizador, **0** resultados duplicados e **0** débitos
sem desfecho. *Alvo:* 25 de 25, com recuperação ≤ 60 s após o serviço voltar e sem reinício de
contentores quando só o broker reinicia. Guardas: latência de um «Apply» normal não piora mais
de 10%; semântica de `activeToken`/cancelamento preservada.

**Decisões a tomar e onde mexer:**

Decisões: (a) entrega *pelo-menos-uma-vez* + consumidores **idempotentes** (chave = `msg_id`),
em vez de tentar exatamente-uma-vez; (b) *outbox*/estado persistido: o `Process` passa a ter
estados (`dispatched`, `done`, `failed`) e só é fechado depois de `Result.create`; (c) *dead
letter exchange* com limite de reentregas para mensagens venenosas; (d) *publisher confirms* no
orquestrador; (e) varredura de retoma no arranque de `projects` (republicar `Process` sem
resposta há mais de N segundos); (f) caminhos de saída por execução, para a reexecução não
colidir com ficheiros parciais.

- `projects/utils/rabbit_mq.js`: `send_rabbit_msg` (canal de confirmação, `persistent: true`),
  `read_rabbit_msg` (`await callback(msg)`, `ack` no fim, `nack` com reentrega limitada,
  `prefetch`, religação como em `wsGateway/utils/rabbit_mq.js`).
- `projects/utils/project_msg.js`: `send_msg_tool`, `send_msg_client*`, `read_msg`.
- `projects/routes/projects.js`: `process_msg` (ordem: guardar resultado → fechar `Process` →
  `ack`; tornar idempotente por `msg_id`), handler de `POST /:user/:project/process`
  (`startProcessing`), nova função de retoma chamada em `projects/app.js`.
- `projects/utils/processBatch.js`: `dispatchProcessBatch` (marcar `dispatched` após confirm).
- `projects/controllers/process.js` e `projects/models/process.js`: campos de estado e
  tentativas; `getOneByMsgId`, `delete`, novo `markDone`.
- `projects/utils/frameResults.js`: `persistFrameResults` (idempotência por fotograma).
- `Tools/utils/rabbit_mq.py`: `Rabbit_MQ.__init__`, `send_rabbit_msg` (`delivery_mode=2`),
  `read_rabbit_msg` (`auto_ack=False`, `basic_qos`, religação).
- `Tools/utils/tool_msg.py`: `ToolMSG.read_msg`, `send_msg`.
- Cada `Tools/<tool>/<tool>.py` (15 ferramentas): `*_callback` (`basic_ack` no fim) e `exec`.
- `Tools/video/video.py`: `VideoWorker._connect` (heartbeat real, com o processamento fora da
  thread de I/O ou `process_data_events`), `_publish` (persistente), `callback`, `run`.
- `rabbitMQ/definitions.json`: `x-dead-letter-exchange` nas 20 filas, fila de mortas, política
  de limite de entregas (filas *quorum*).

**Avaliação AI: 9 / 10.** *Pertinência* alta: é a prioridade explícita deixada pelo PL1-G4,
corresponde a `REQ-VID-FAIL-004` e a perda é silenciosa e custa quota ao utilizador.
*Complexidade* muito alta: toca o orquestrador, o broker e 16 workers, exige idempotência e
máquina de estados, e a avaliação é injeção de falhas em vários pontos, o que dá muita
profundidade à análise. Não é 10 porque a janela mais provável no dia-a-dia (morte do worker de
vídeo) já funciona, e as restantes dependem de reinícios que, em operação normal, são raros.

---

## Ideia 4: Erros das ferramentas e trabalhos órfãos

**Tipo:** Fiabilidade — tolerância a falhas; secundariamente Usabilidade — proteção contra erros
do utilizador (`REQ-VID-FAIL-003`).

**Ideia:** Fazer com que um erro tratado numa ferramenta de imagem chegue ao utilizador como
mensagem compreensível, validar os parâmetros no servidor antes de aceitar a ferramenta, e
fechar automaticamente (com reembolso) qualquer trabalho que não tenha resposta num prazo.

**Situação base:** O caminho de erro das ferramentas de imagem tem um defeito de contrato que
faz o próprio processo da ferramenta terminar; a mensagem já foi confirmada (`auto_ack`) e
perde-se. O orquestrador não tem prazo para respostas. O servidor aceita parâmetros inválidos.

**Diagnóstico completo:**

```python
# Tools/utils/tool_msg.py
def send_msg(self, msg_id, resp_msg_id, timestamp, status, processingTime, new_img_uri,
             type="image", err_code=None, err_msg=None, og_img_uri=None):
    ...
    case "error":
        if err_code is None or err_msg is None or og_img_uri is None:
            raise Exception("Make sure, in case of error status, ...")
        msg = { "messageId": msg_id, "correlationId": resp_msg_id, ... }   # ids trocados

# Tools/border/border.py — chamada posicional: o código de erro cai em `type`
self._tool_msg.send_msg(msg_id, resp_msg_id, cur_timestamp, 'error', processing_time, None,
                        self._codes['error_processing'], "An error occured ...", img_path)
```

Os argumentos posicionais ficam desalinhados (`type=1201`, `err_code="An error…"`,
`err_msg=img_path`, `og_img_uri=None`), a função lança exceção dentro do *callback*, o processo
sai e o Docker reinicia-o. Mesmo que não lançasse, `messageId`/`correlationId` vêm trocados e o
orquestrador não encontraria o `Process` (`Process.getOneByMsgId(msg_content.correlationId)`).
O mesmo padrão existe em `border`, `binarization`, `rotate`, `resize` e `bg_remove_ai`.
Acresce que `POST /:user/:project/tool` só verifica que existem `procedure` e `params`.

Impacto: o utilizador fica preso no ecrã de processamento sem qualquer mensagem, o projeto fica
com um `Process` pendente e, se a ferramenta for avançada, a operação foi debitada.

**Quantificação:**

*Cenário R1:* utilizador free, 1 imagem PNG, ferramenta `border` com `borderWidth:
"not-a-number"`, «Apply», observação de 30 s com um cliente Socket.IO autenticado.
*Controlo R0:* mesma imagem com `brightness` válido. *Instrumento:* `reliability.mjs R0 R1`.

| Medida | Controlo (válido) | Erro na ferramenta |
|--------|-------------------|--------------------|
| Resposta ao acrescentar a ferramenta | 201 | **201** (parâmetro inválido aceite) |
| Evento recebido pelo cliente | `process-update` aos 229 ms | **nenhum em 30 s** |
| Reinícios do contentor da ferramenta | 0 | **1** |
| Registos `Process` pendentes | 0 | **+1** |
| Mensagem em `border_queue` | — | 0 (perdida) |

Taxa de erros tratados que chegam ao utilizador: **0 de 1**.

*Mínimo aceitável:* 100% dos erros tratados de ferramenta produzem `process-error` no cliente em
≤ 5 s, sem reinício do contentor; 100% dos trabalhos sem resposta são fechados com erro e
reembolso em ≤ 120 s. *Alvo:* além disso, 100% dos parâmetros inválidos de uma lista de casos
(tipo errado, fora de intervalo, em falta) são recusados com 400 **antes** de entrarem no
pipeline, e o erro chega em ≤ 2 s.

**Decisões a tomar e onde mexer:**

Decisões: (a) um único contrato de resposta de erro, construído por argumentos nomeados;
(b) esquema de parâmetros por ferramenta, partilhado entre validação do servidor e frontend;
(c) *watchdog* de `Process` com prazo por tipo (imagem, IA, vídeo proporcional à duração);
(d) política de reembolso em falha (hoje só existe em cancelamento de ferramentas avançadas).

- `Tools/utils/tool_msg.py`: `ToolMSG.send_msg` (ids corretos, incluir `error.msg`, que é o
  campo que o orquestrador lê).
- `Tools/border/border.py` `border_callback`; `Tools/binarization/binarization.py`,
  `Tools/rotate/rotate.py`, `Tools/resize/resize.py`, `Tools/bg_remove_ai/bg_remove_ai.py`
  (`*_callback`: argumentos nomeados); rever as restantes 11.
- `Tools/utils/env.py`: `IMG_STORAGE_URL` lê por engano `RABBITMQ_PASSWORD`.
- `projects/routes/projects.js`: handler `POST /:user/:project/tool` e `PUT` de ferramenta
  (validação por esquema), `process_msg` (ramo `status === "error"`: reembolso; variável `key8`
  usada fora do âmbito no `catch` da cópia de cache), nova função `sweepStaleProcesses`.
- `projects/models/process.js`: `createdAt`/prazo.
- `users/routes/users.js`: `POST /:user/process/refund/:advanced_tools` (reutilizar).
- `frontend/app/dashboard/[pid]/page.tsx`: tratamento de `process-error`.

**Avaliação AI: 8 / 10.** *Pertinência* alta: basta um parâmetro mal escrito para o utilizador
ficar bloqueado sem explicação — é um defeito que se sente na utilização normal, sem precisar
de falhas de infraestrutura. *Complexidade* média: a correção do contrato é pequena, mas o
*watchdog*, o reembolso e a validação por esquema em todas as ferramentas dão-lhe corpo; a
avaliação por casos de erro injetados é simples e convincente. Faz bom par com a ideia 3 ou
pode ser absorvida por ela.

---

## Ideia 5: Integridade do perfil e da subscrição

**Tipo:** Segurança — integridade e autenticidade (controlo de acesso a funções pagas).

**Ideia:** Impedir que o perfil (`free`/`premium`) seja escolhido pelo cliente: o registo cria
sempre `free`, a atualização de perfil ignora `type`, e só o serviço de subscrições, autenticado,
promove ou despromove.

**Situação base:** O registo público aceita `type` no corpo; a atualização de perfil copia
`req.body.type`; as rotas de subscrições no gateway não têm `auth.checkToken`; `GET
/users/:user` também não.

**Diagnóstico completo:**

```js
// users/routes/users.js
type: req.body.type || "free",                 // POST /  (registo)
user.type = req.body.type || user.type;        // PUT /:user

// apiGateway/routes/users.js
router.get("/:user", function (req, res, next) { ... });          // sem checkToken
router.put("/:user", auth.checkToken, ...) → axios.put(usersURL + req.params.user, req.body)

// apiGateway/routes/subscriptions.js — nenhuma das 7 rotas usa auth.checkToken
router.get("/:user/card", function (req, res, next) { ... });
router.put("/:user/cancel", async function (req, res, next) { ... });
```

Impacto: qualquer pessoa obtém premium sem pagar — vídeos de 10 min/1 GB, operações ilimitadas,
colaboração sem limite — o que anula o modelo de negócio e multiplica o custo de recursos
(liga às ideias 2 e 6). Terceiros podem ler o perfil e o email de outro utilizador conhecendo o
id, e (pelo código) consultar o estado/cartão ou cancelar a subscrição alheia.

**Quantificação:**

*Cenário:* pedidos únicos pela entrada pública com contas sintéticas. *Instrumento:*
`security.mjs` (casos G05–G07, D09).

| Caso | Pedido | Resultado medido |
|------|--------|------------------|
| G06 | Registo com `type: "premium"` | 201; perfil guardado = **premium** |
| G07 | Utilizador free faz `PUT /users/<próprio>` com `type: "premium"` | 204; perfil = **premium** |
| G05 | `GET /users/<outro>` sem token | **200**; devolve `name`, `email`, `type`, `operations` |
| D09 | `PUT` direto em `users:10001` sem token | 204; perfil da vítima = **premium** |
| G08/G09 | Rotas de subscrições sem token | **não medido** (serviço fora do stack); ausência de `checkToken` confirmada no código |

**4 de 4** casos medidos admitidos. *Mínimo aceitável e alvo:* 0 admitidos; o fluxo legítimo
(subscrever → premium; cancelar → free) continua a passar. Alvo adicional: 0 campos pessoais
devolvidos a quem não é o próprio.

**Decisões a tomar e onde mexer:**

Decisões: (a) lista branca de campos editáveis pelo utilizador; (b) mudança de perfil só por
chamada de serviço autenticada vinda de `subscriptions` (depende da identidade de serviço da
ideia 1); (c) o que `GET /users/:user` pode expor publicamente (provavelmente só o nome).

- `users/routes/users.js`: `POST /` (forçar `free`, aceitar `anonymous`), `PUT /:user` (ignorar
  `type`), nova rota interna de perfil; `GET /:user` e `removeSensitiveInfo`.
- `apiGateway/routes/users.js`: `GET /:user` (com `checkToken`), `PUT /:user` (filtrar corpo).
- `apiGateway/routes/subscriptions.js`: as 7 rotas (`checkToken` + utilizador do token =
  `:user`), `POST /` (usar o id do token em vez de `req.body.subscription.user_id`).
- `subscriptions/routes/subscriptions.js`: `POST /`, `PUT /:user/cancel` (chamada autenticada
  a `users`).
- `frontend`: remover `type` do pedido de registo, se o enviar.

**Avaliação AI: 7,5 / 10.** *Pertinência* muito alta para o stakeholder «negócio/operador»: é a
fronteira entre grátis e pago. *Complexidade* baixa a média: são poucas funções e a avaliação é
uma matriz curta; sozinha é pequena para um RNF de fase, mas encaixa naturalmente como parte da
ideia 1, reforçando-lhe a pertinência sem lhe aumentar muito o custo.

---

## Ideia 6: Capacidade de processamento de vídeo

**Tipo:** Eficiência de desempenho — capacidade; comportamento temporal como guarda
(`REQ-VID-EDIT-011`, `REQ-VID-EDIT-010`).

**Ideia:** Passar de um único worker de vídeo para um *pool* limitado de consumidores
concorrentes com caminhos de trabalho isolados por execução, para que vídeos de utilizadores
diferentes não esperem uns pelos outros.

**Situação base:** Um contentor `video_tool`, `prefetch_count=1`, sem réplicas; legendagem
(Whisper) e efeitos comuns partilham o mesmo processo. Corresponde à QC-02.

**Diagnóstico completo:**

```python
# Tools/video/video.py
# one video at a time per replica; parallelism comes from replicas
self._channel.basic_qos(prefetch_count=1)
```

```yaml
# docker-compose.yaml — video_tool sem deploy.replicas nem limites
video_tool:
  build: { context: ./Tools, dockerfile: video/Dockerfile }
  restart: on-failure
```

Os caminhos de saída derivam do nome do ficheiro (`./images/users/<u>/projects/<p>/out/<nome>.mp4`),
pelo que duas execuções do mesmo projeto colidem — é o que impede simplesmente subir réplicas.
`REQ-VID-EDIT-011` pede ≥ 2 vídeos em paralelo no MVP; hoje é 1. Impacto: quem submete três
vídeos espera pelo terceiro o triplo; com vários utilizadores, a fila é global e um vídeo de
10 min de um premium atrasa todos os free.

**Quantificação:**

*Não repetido hoje; reutiliza-se a medição de 14/11* (`live-findings.md`, worker com 2 CPU e
1 GiB, stack de 13 serviços, cliente em contentor separado, *tap* AMQP): 3 lotes de 3 vídeos de
10 s com `brightness`.

| Medida | Valor |
|--------|-------|
| Tempo do lote (envio → 3 resultados) | 42,7–45,0 s |
| Débito | 4,0–4,2 vídeos/min |
| Execução por vídeo no worker | 13,2–16,0 s (1,3–1,6× a duração; `REQ-VID-EDIT-010` MVP ≤ 5× cumprido) |
| Espera do último vídeo do lote | 28,3–30,5 s |
| CPU média do worker | 1,95–1,97 de 2 núcleos |
| Vídeos em paralelo | **1** (requisito MVP: ≥ 2) |

*Mínimo aceitável:* 2 vídeos em processamento simultâneo; espera do último vídeo do mesmo lote
≤ 15 s (metade), com os mesmos SHA-256 de saída. *Alvo:* débito ≥ 8 vídeos/min com 2 réplicas de
2 CPU, e espera do último ≤ 10 s. Importante: comparar **com o orçamento de CPU declarado** —
dobrar réplicas com o dobro dos núcleos é capacidade, não eficiência.

**Decisões a tomar e onde mexer:**

Decisões: (a) *competing consumers* sobre a mesma fila (simples, coerente com o padrão atual)
vs. filas separadas para trabalhos pesados (legendas) e leves; (b) isolamento de ficheiros por
execução (`<msg_id>/`), pré-requisito também da ideia 3; (c) limite de recursos por réplica e
quantas réplicas cabem no host; (d) justiça entre utilizadores (uma fila global permite que um
utilizador monopolize o pool).

- `docker-compose.yaml`: `video_tool` (`deploy.replicas`, `cpus`, `mem_limit`; o volume
  `whisper_models` passa a ser partilhado só para leitura).
- `Tools/video/video.py`: `VideoWorker.callback` (diretório de trabalho por mensagem),
  `_progress`.
- `Tools/video/video_processor.py`: `process_video`, `_process_video`, `_start_encoder`
  (saídas temporárias únicas e `rename` atómico).
- `Tools/video/frame_extraction.py` e `subtitles.py`: caminhos temporários.
- `projects/routes/projects.js`: `startProcessing` em `POST /:user/:project/process` (nomes de
  saída por execução) e `process_msg` (ler o caminho devolvido).
- `rabbitMQ/definitions.json`: eventual `video_heavy_queue`.

**Avaliação AI: 7,5 / 10.** *Pertinência* alta: há um requisito MVP escrito que não é cumprido
(2 em paralelo) e o tempo de espera é o que o utilizador de vídeo mais sente. *Complexidade*
média-alta: a mudança de topologia é pequena, mas a concorrência segura (isolamento de ficheiros,
memória do Whisper por réplica) e uma avaliação honesta com orçamento fixo exigem cuidado.
Desce porque o ganho depende do hardware disponível e é fácil apresentar «mais máquinas» como
melhoria arquitetural.

---

## Ideia 7: Disponibilidade do gateway e supervisão dos serviços

**Tipo:** Fiabilidade — disponibilidade e recuperabilidade (RNF56 como referência).

**Ideia:** Garantir que um serviço que morre volta sozinho e que um serviço que não responde é
detetado: processo Node como PID principal (sem `nodemon` em execução normal), `healthcheck` e
limites de memória em todos os serviços, e arranque ordenado por estado de saúde.

**Situação base:** `api_gateway`, `users` e `subscriptions` arrancam com `nodemon`. Quando o
processo Node morre, o `nodemon` fica vivo à espera de alterações de ficheiros; o contentor
continua «running», por isso `restart: on-failure` nunca dispara. Só 5 dos 32 serviços têm
`healthcheck` (RabbitMQ, 3 MongoDB e o mock generativo) e nenhum tem limite de memória.

**Diagnóstico completo:**

```json
// apiGateway/package.json (igual em users e subscriptions)
"start": "nodemon ./bin/www"
```

```yaml
# docker-compose.yaml
api_gateway:
  build: ./apiGateway
  restart: on-failure          # nunca atua: o PID 1 (nodemon) não termina
  volumes: [ ./apiGateway:/app, /app/node_modules ]
```

Há ainda `throw` dentro de *callbacks* AMQP (`if (err_sv) throw err_sv;` em
`projects/utils/rabbit_mq.js`), que derrubam o orquestrador quando o broker falha. Impacto: o
gateway é o ponto único de entrada da API; se cair, ninguém entra, ninguém edita, e o operador
só sabe quando alguém se queixar, porque nada sinaliza o estado.

**Quantificação:**

*Cenário:* depois dos uploads da ideia 2, um upload de 500 MiB excedeu o limite de 2 GiB do
gateway. *Instrumento:* `uploads.mjs` + `docker inspect` + `curl` ao gateway.

| Medida | Valor |
|--------|-------|
| Estado do contentor após o OOM | `running`, `RestartCount` = 0, `OOMKilled` = true |
| Log | `[nodemon] app crashed - waiting for file changes before starting...` |
| Resposta do gateway 20 s depois | **502** (continuava em baixo) |
| Tempo até recuperar sem intervenção | **indefinido** — só voltou com `docker restart` manual |
| Serviços com `healthcheck` | 5 de 32 |
| Serviços com limite de memória | 0 de 32 |

No R2 os consumidores estavam presentes na primeira amostra 5 s após o regresso
da API de gestão; esse marcador não prova recuperação total em ≤5 s desde o início do reinício.

*Mínimo aceitável:* após morte do processo de qualquer serviço Node (5 repetições de `kill -9`
por serviço), o serviço volta a responder em ≤ 30 s sem intervenção, em 100% dos casos.
*Alvo:* ≤ 10 s; 100% dos serviços aplicacionais com `healthcheck` e `mem_limit`; nginx devolve
503 com mensagem clara enquanto o gateway está em baixo.

**Decisões a tomar e onde mexer:**

Decisões: (a) separar perfil de desenvolvimento (`nodemon`, *bind mounts*) do de execução
(`node`, imagem imutável) com um ficheiro *override* do Compose; (b) rota `/health` por serviço
com verificação das dependências; (c) `depends_on: condition: service_healthy` em cadeia;
(d) orçamento de memória por serviço (alimentado pelas medições da ideia 2).

- `apiGateway/package.json`, `users/package.json`, `subscriptions/package.json`: script `start`
  (`node ./bin/www`) e novo `dev`.
- `apiGateway/app.js`, `projects/app.js`, `users/app.js`, `subscriptions/app.js`,
  `imageStorageService/server.js`, `wsGateway/index.js`: rota `/health`.
- `docker-compose.yaml`: `healthcheck`, `mem_limit`, `restart: unless-stopped`, `depends_on`
  com condições; remoção dos *bind mounts* do perfil de execução.
- `projects/utils/rabbit_mq.js`: `send_rabbit_msg`, `read_rabbit_msg` (sem `throw` em
  *callbacks*; religação).
- `nginx/nginx.conf`: `proxy_next_upstream`/página de erro em `location /api-gateway/`.

**Avaliação AI: 7,5 / 10.** *Pertinência* alta: uma queda total e silenciosa do ponto de
entrada, reproduzida na prática, afeta todos os utilizadores e o operador. *Complexidade*
média: as alterações são sobretudo de configuração e pequenas rotas, mas a avaliação por
injeção de falhas com tempo de recuperação é limpa e mensurável. Sozinha fica um pouco curta em
exigência técnica; combina muito bem com a ideia 2 (a causa) ou com a 3.

---

## Ideia 8: Admissão de uploads antes de os carregar

**Tipo:** Segurança — (proteção contra negação de serviço, integridade do serviço);
Fiabilidade — disponibilidade.

**Ideia:** Decidir se um upload é aceitável **antes** de ler o corpo: autenticar primeiro,
aplicar o limite de tamanho do perfil no próprio leitor do multipart, e limitar no nginx o
tamanho e o ritmo de pedidos por cliente.

**Situação base:** No gateway o `multer` corre antes do `checkToken`; o limite de tamanho por
perfil só é verificado em `projects`, depois de o ficheiro já estar inteiro em memória em dois
serviços. Uploads de imagem não têm limite nenhum além dos 1100 MB do nginx. Não há limitação
de ritmo.

**Diagnóstico completo:**

```js
// apiGateway/routes/projects.js
router.post("/:user/:project/video",
  upload.single("video"),      // 1.º: carrega o corpo todo para a RAM
  auth.checkToken,             // 2.º: só agora verifica o token
  function (req, res, next) { ... });

// projects/utils/video.js — só depois do buffer completo
maxSizeMB: num("VIDEO_FREE_MAX_SIZE_MB", 100),
```

```nginx
# nginx/nginx.conf
client_max_body_size 1100m;        # global, sem limit_req nem limit_conn
```

Impacto: quem não tem conta consegue ocupar memória do gateway à vontade; um utilizador free
que envie por engano um ficheiro maior do que o seu limite paga o custo total de memória antes
de receber a recusa — e, como se mediu, pode deitar abaixo o gateway para todos.

**Quantificação:**

*Cenário:* os mesmos ficheiros da ideia 2, enviados sem token e com conta free acima do limite.
*Instrumento:* `uploads.mjs` (casos `no-token-*` e `free-500MiB-over-limit`).

| Pedido | Resposta | Memória do gateway consumida antes de recusar |
|--------|----------|-----------------------------------------------|
| 100 MiB sem token | 401 em 0,98 s | +2 MiB (reutilizou memória já retida) |
| 500 MiB sem token | 401 em 4,28 s | **+500 MiB** (544→1044 MiB) |
| 500 MiB, conta free (limite 100 MB) | **502** — processo do gateway morto por OOM | até ao limite de 2 GiB |

*Mínimo aceitável:* pedido sem token recusado com 401 consumindo ≤ 8 MiB adicionais no gateway,
para qualquer tamanho; ficheiro acima do limite do perfil recusado com 413 sem ser carregado
por inteiro em nenhum serviço. *Alvo:* recusa em ≤ 100 ms após os cabeçalhos; 20 uploads
simultâneos sem token de 500 MiB não alteram a latência mediana de um pedido autenticado normal
em mais de 20%.

**Decisões a tomar e onde mexer:**

Decisões: (a) ordem dos middlewares (autenticar → limitar → ler); (b) onde fica o limite por
perfil — o gateway precisa de conhecer o perfil (pedido a `users` com cache curta, ou *claim*
no JWT); (c) limites no nginx por *location* e `limit_req_zone`; (d) responder `413` cedo
quando o `Content-Length` já excede o limite.

- `apiGateway/routes/projects.js`: rotas `POST /:user/:project/img` e `/video` (ordem dos
  middlewares, `limits.fileSize`), novo middleware `rejectOversize`.
- `apiGateway/auth/auth.js`: `checkToken` (expor o perfil).
- `users/auth/auth.js`: `get_jwt` (incluir `type` como *claim*, se for essa a decisão).
- `projects/routes/projects.js`: `upload` (limites), `addProjectMedia` (tratar
  `LIMIT_FILE_SIZE` → 413).
- `imageStorageService/route/upload.js`: limites.
- `nginx/nginx.conf`: `client_max_body_size` por *location*, `limit_req_zone`, `limit_conn`.

**Avaliação AI: 7 / 10.** *Pertinência* alta: é um vetor de negação de serviço aberto a
anónimos e uma causa direta da queda medida na ideia 7. *Complexidade* baixa-média: poucas
linhas se a ideia 2 (streaming) for feita, porque a ordem certa dos middlewares cai daí
naturalmente; isolada, tem pouca profundidade arquitetural. Recomenda-se como requisito de
guarda da ideia 2 e não como RNF próprio.

---

## Ideia 9: Segredos e superfície de rede interna

**Tipo:** Segurança — confidencialidade (gestão de credenciais e exposição de interfaces).

**Ideia:** Tirar os segredos do `docker-compose.yaml` versionado (ficheiro `.env`/*secrets* não
versionado, sem valores por omissão), dar autenticação às bases de dados, e deixar de publicar
no host as portas dos serviços internos.

**Situação base:** O Compose contém em claro a chave JWT, as chaves de cifra de campos e de
cartões, as credenciais do RabbitMQ e os valores por omissão do S3 e da sua frase de cifra. Os
três MongoDB não têm autenticação. 11 serviços publicam 13 portas em `0.0.0.0`. É uma das
prioridades deixadas pelo PL1-G4.

**Diagnóstico completo:**

```yaml
# docker-compose.yaml
- JWT_SECRET_KEY=lisan_al_gaib
- FIELD_ENCRYPTION_KEY=uma-frase-secreta-bem-grande-ou-64-hex
- SECRET_KEY=card_secret_key
RABBITMQ_DEFAULT_USER: "user"
RABBITMQ_DEFAULT_PASS: "password"
AWS_SECRET_ACCESS_KEY: ${S3_SECRET_KEY:-admin123}
WEED_S3_SSE_KEK_PASSPHRASE: ${S3_KEK_PASSPHRASE:-picturas-kek-passphrase-change-me}
projects:    ports: ["9002:9001"]
img_storage: ports: ["11000:11000"]
users:       ports: ["10001:10001"]
rabbitmq:    ports: ["5672:5672", "15672:15672"]
```

```js
// projects/app.js
const mongoDB = "mongodb://projects_mongoDB:27018/project";      // sem credenciais
```

Impacto: quem tiver acesso de leitura ao repositório consegue **assinar JWT válidos para
qualquer utilizador** (a chave é pública), ler a fila de mensagens, e decifrar os campos e os
*tokens* de cartão guardados. As portas publicadas tornam alcançáveis, a partir da rede local,
todos os atalhos demonstrados na ideia 1. Para o operador é impossível rodar uma credencial sem
alterar código.

**Quantificação:**

*Instrumento:* contagem sobre o `docker-compose.yaml` e dois pedidos de `security.mjs`.

| Medida | Valor |
|--------|-------|
| Linhas com segredo em claro no Compose | 13 |
| Serviços com portas publicadas / portas | 11 / 13 (só a 8080 é necessária) |
| D10: API de gestão do RabbitMQ com `user`/`password` do repositório | **200** |
| D11: leitura do MongoDB de projetos sem credenciais | **permitida** |
| Bases de dados com autenticação | 0 de 3 |

*Mínimo aceitável:* 0 segredos em ficheiros versionados (verificado por `gitleaks` ou `grep` em
CI); arranque falha com mensagem clara se faltar um segredo; só a porta 8080 publicada no perfil
de execução. *Alvo:* além disso, MongoDB e RabbitMQ com credenciais por serviço e privilégio
mínimo, e rotação da chave JWT demonstrada sem alterar código (só o ficheiro de ambiente).

**Decisões a tomar e onde mexer:**

Decisões: (a) `.env` não versionado com `.env.example` vs. *Docker secrets*; (b) duas redes
(`edge` para nginx/gateway, `internal: true` para o resto); (c) portas de depuração num
*override* de desenvolvimento; (d) o que fazer ao histórico git (as chaves atuais ficam
comprometidas e têm de ser trocadas, não apenas movidas).

- `docker-compose.yaml`: todos os blocos `environment` e `ports`; `networks`.
- Novo `.env.example`; `.gitignore`.
- `projects/app.js`, `users/app.js`, `subscriptions/app.js`: URI do MongoDB por variável.
- `projects/utils/rabbit_mq.js`, `wsGateway/utils/rabbit_mq.js`, `Tools/utils/env.py`,
  `Tools/video/video.py` (`_connect`): falhar se a credencial faltar, em vez de usar valor por
  omissão.
- `imageStorageService/services/s3Client.js`: remover `|| "admin"` / `|| "admin123"`.
- `rabbitMQ/rabbitmq.conf` e `definitions.json`: utilizadores e permissões.
- `subscriptions/models/card.js`, `users/utils/fieldCrypto.js`: validar a presença da chave no
  arranque.
- `README.md` / `AGENTS.md`: instruções de arranque.

**Avaliação AI: 7 / 10.** *Pertinência* alta e reconhecida (prioridade do PL1-G4): a chave JWT
pública torna inútil toda a autenticação. *Complexidade* média-baixa: é sobretudo configuração
e disciplina, com pouca decisão arquitetural além da segmentação de rede; a avaliação é
objetiva mas quase binária (há/não há segredos). Vale mais como **pré-requisito** da ideia 1
(a identidade de serviço precisa de uma chave que não esteja no repositório) do que como RNF
isolado.

---

## Ideia 10: Quota diária atómica

**Tipo:** Fiabilidade — maturidade (correção sob concorrência); Segurança — integridade
(`REQ-VID-QUOTA-001/002`, RNF48).

**Ideia:** Tornar a reserva de operações diárias uma operação atómica na base de dados, para
que pedidos simultâneos não ultrapassem o limite nem percam contagens.

**Situação base:** A reserva é um `GET` que lê o utilizador, soma em memória e grava o documento
inteiro. Dois pedidos ao mesmo tempo leem o mesmo valor.

**Diagnóstico completo:**

```js
// users/routes/users.js — GET /:user/process/:advanced_tools
const user = await User.getOne(req.params.user);
let op = user.operations.find(...) || { day: process_date, processed: 0 };
const can_process = check_process(user, op, op_num);
...
op.processed += op_num;
user.operations = user.operations.filter(...); user.operations.push(op);
await User.update(req.params.user, user);          // escreve o documento todo
```

É um ler-modificar-escrever sem bloqueio nem condição. Além disso é um `GET` com efeito
colateral e sem autenticação (ideia 1). Impacto: o limite de 5 operações do perfil free — a
principal alavanca para vender o premium — pode ser contornado abrindo vários separadores ou
com um *script*; e o saldo mostrado ao utilizador (RNF48) fica errado.

**Quantificação:**

*Cenário:* conta free nova (limite `FREE_DAILY_OP=5`), 20 pedidos simultâneos de reserva de
1 operação. *Instrumento:* `security.mjs`, caso Q01 (pedidos diretos a `users`).

| Medida | Esperado | Medido |
|--------|----------|--------|
| Reservas concedidas | 5 | **20** |
| Operações registadas no fim | 5 | **3** (saldo mostrado: 2) |

Ou seja: 15 operações a mais concedidas e 17 atualizações perdidas. *Limitação:* foi medido no
serviço `users`; pelo percurso completo («Apply» em `projects`) o controlo de versão do projeto
reduz a concorrência dentro do mesmo projeto, mas não entre projetos diferentes do mesmo
utilizador.

*Mínimo aceitável e alvo:* em 20 repetições de 20 pedidos simultâneos, concedidas = exatamente
5 e registadas = concedidas, em 100% das repetições. Alvo adicional: reembolso idempotente
(o mesmo reembolso pedido duas vezes só credita uma).

**Decisões a tomar e onde mexer:**

Decisões: (a) atualização condicional atómica (`findOneAndUpdate` com filtro
`processed + n <= limite` e `$inc`) vs. bloqueio otimista por versão; (b) modelo de reserva com
identificador (reserva → confirmação/libertação) para suportar reembolsos idempotentes;
(c) mudar o verbo para `POST`.

- `users/routes/users.js`: `GET /:user/process/:advanced_tools`, `PUT
  /:user/process/:advanced_tools`, `POST /:user/process/refund/:advanced_tools`,
  `check_process`, `getRemainingOperations`.
- `users/controllers/user.js`: novo `reserveOperations`/`refundOperations`; `update`.
- `users/models/user.js`: estrutura de `operations` (documento por dia ou contador).
- `projects/routes/projects.js`: chamadas em `POST /:user/:project/process` e no cancelamento.

**Avaliação AI: 7 / 10.** *Pertinência* média-alta: afeta a regra de negócio que distingue os
perfis e o saldo que o utilizador vê. *Complexidade* média: o código a mudar é pouco, mas a
decisão de modelo (reserva idempotente) e um teste de concorrência reprodutível mostram
profundidade técnica acima do tamanho da alteração. Tem uma métrica muito limpa, o que conta a
favor da solidez da avaliação.

---

## Ideia 11: TLS interno válido

**Tipo:** Segurança — confidencialidade e autenticidade em trânsito (RNF44: «cifrados em
trânsito, TLS 1.2+»).

**Ideia:** Fazer com que as ligações entre serviços sejam cifradas **e verificadas**: uma
autoridade de certificação interna, certificados válidos emitidos no arranque, e remoção de
`rejectUnauthorized: false`.

**Situação base:** Os certificados dos serviços expiraram em janeiro de 2026 e a verificação
está desligada em 7 pontos do código. As chamadas a `img_storage`, ao S3 e ao RabbitMQ vão em
HTTP/AMQP simples. As chaves privadas estão no repositório. Prioridade deixada pelo PL1-G4.

**Diagnóstico completo:**

```js
// apiGateway/routes/projects.js (e mais 6 ficheiros)
const httpsAgent = new https.Agent({
  rejectUnauthorized: false, // (NOTE: this will disable client verification)
  cert: cert, key: key,
});

// projects/utils/imageStorage.js
const img_storage_ms = "http://img_storage:11000";
```

Com a verificação desligada, o TLS interno cifra mas não autentica: qualquer contentor na rede
pode fazer-se passar por `projects` ou `users`. Os ficheiros dos utilizadores e os JWT circulam
em claro entre `projects`, storage e S3. Impacto: o RNF44 é declarado cumprido no relatório
anterior, mas não o é dentro da rede; para o operador, a renovação é manual e já falhou uma vez
(os certificados estão expirados há 10 meses sem que nada o assinalasse).

**Quantificação:**

*Instrumento:* `openssl x509 -enddate` em cada certificado e `grep` no código.

| Medida | Valor |
|--------|-------|
| Certificados de serviço expirados | **5 de 5** (apiGateway 11/01/2026, users 09/01, projects 09/01, subscriptions 17/01, frontend 12/01) |
| Certificado do nginx | válido até 14/09/2027, autoassinado |
| Pontos com `rejectUnauthorized: false` | 7 |
| Ligações internas sem cifra | storage (HTTP), S3 (HTTP), RabbitMQ (AMQP), MongoDB |
| Chaves privadas versionadas | 6 |

*Mínimo aceitável:* 0 ocorrências de `rejectUnauthorized: false`; 100% das chamadas HTTP entre
serviços com certificado válido e verificado; um teste negativo (serviço com certificado de
outra CA) é recusado. *Alvo:* inclui AMQP e S3; emissão automática no arranque e renovação
ensaiada; 0 chaves privadas no repositório. Guarda: latência mediana de um pedido simples pelo
gateway não aumenta mais de 10 ms.

**Decisões a tomar e onde mexer:**

Decisões: (a) CA interna gerada num contentor de arranque (por exemplo `step-ca` ou um
*script* `openssl`) com certificados em volume, vs. terminar TLS só na fronteira e isolar a rede
(mais simples, mas não cumpre «cifrado em trânsito» internamente); (b) mTLS como identidade de
serviço (resolve também a decisão (b) da ideia 1); (c) nomes DNS dos serviços nos SAN.

- `apiGateway/routes/projects.js`, `routes/users.js`, `routes/subscriptions.js`: `httpsAgent`.
- `projects/routes/projects.js`, `projects/utils/httpsAgent.js`, `projects/utils/imageStorage.js`,
  `projects/utils/presence.js` (`getUserType`): agente com `ca`.
- `projects/bin/www`, `users/bin/www`, `subscriptions/bin/www`: carregar certificado do volume.
- `imageStorageService/server.js`: passar a HTTPS; `services/s3Client.js` (`endpoint` https).
- `Tools/utils/rabbit_mq.py`, `Tools/video/video.py`, `projects/utils/rabbit_mq.js`,
  `wsGateway/utils/rabbit_mq.js`: `amqps` com CA.
- `rabbitMQ/rabbitmq.conf`: `listeners.ssl`.
- `docker-compose.yaml`: serviço de emissão, volume de certificados.
- Remover `*/certs/selfsigned.key` do repositório.

**Avaliação AI: 6,5 / 10.** *Pertinência* média: há um requisito escrito (RNF44) e é prioridade
do PL1-G4, mas o atacante tem de estar já dentro da rede Docker, o que reduz o impacto real face
às ideias 1 e 9. *Complexidade* média-alta: PKI interna, distribuição e renovação em ~8
serviços e dois protocolos; a avaliação é sobretudo de conformidade (válido/verificado), com
menos riqueza quantitativa do que as outras. Boa candidata a ser a «forma» da identidade de
serviço na ideia 1.

---

## Ideia 12: Estado e progresso de trabalhos recuperáveis

**Tipo:** Usabilidade — operabilidade (`REQ-VID-STATUS-003`, `REQ-VID-EDIT-002`).

**Ideia:** Guardar no servidor o estado de cada trabalho (em fila, em curso com percentagem,
concluído, falhado) e deixar o cliente consultá-lo, de modo que o progresso sobreviva a um
*refresh*, inclua o tempo em fila e não obrigue a um *overlay* que bloqueia o editor.

**Situação base:** O progresso existe só como eventos Socket.IO efémeros guardados em estado do
browser; não há repetição de eventos nem rota de estado. Um vídeo em fila não emite nada até o
worker lhe pegar. Corresponde à QC-04b.

**Diagnóstico completo:**

```js
// wsGateway/index.js — reencaminha e esquece
if (/update-client-video-progress/.test(msg_id)) {
    io.to(user).emit("video-progress", { projectId, imgId, preview, percent });
}

// frontend/app/dashboard/[pid]/page.tsx
socket.data.on("video-progress", onVideoProgress);     // estado local do componente
```

```python
# Tools/video/video.py — progresso por percentagem, não por tempo
progress_cb=lambda pct: self._progress(progress, preview, pct)
```

Impacto: quem recarrega a página ou muda de dispositivo a meio perde o acompanhamento; quem
tem o 3.º vídeo da fila vê 0% durante meio minuto e não sabe se o sistema está parado. O
requisito pede intervalo entre atualizações ≤ 5 s (MVP) e ≤ 2 s (alvo).

**Quantificação:**

*Reutiliza a medição de 14/11* (cliente Socket.IO, 3 lotes de 3 vídeos de 10 s):

| Medida | Valor | Requisito |
|--------|-------|-----------|
| Intervalo máximo entre eventos de um vídeo **ativo** | < 0,6 s | ≤ 5 s — cumprido |
| Primeiro evento do **último vídeo em fila** | 29,5–31,4 s após o envio | Excede 5 s se o critério incluir fila; fechar essa interpretação antes da aceitação |
| Eventos repetidos a uma ligação nova após o lote | 0 | — |
| Recuo do progresso após reinício do worker | 3% → 1% | — |

Estado após *refresh* durante o processamento num browser real: **não medido**.

*Mínimo aceitável:* qualquer media submetido tem estado visível («em fila, posição n») em ≤ 5 s
e nunca passa mais de 5 s sem atualização; após *refresh*, o estado correto reaparece em ≤ 3 s
em 10 de 10 tentativas. *Alvo:* ≤ 2 s em ambos; editor utilizável durante o processamento.
O alvo de usabilidade propriamente dito (compreensão) exigiria participantes.

**Decisões a tomar e onde mexer:**

Decisões: (a) fonte de verdade no servidor (`Process` com `state`/`percent`) e WebSocket apenas
como notificação; (b) *heartbeat* temporal no worker durante fases longas (Whisper, fila);
(c) se o *overlay* deixa de bloquear — cuidado para não introduzir funcionalidade nova.

- `projects/models/process.js`, `projects/controllers/process.js`: campos de estado/progresso.
- `projects/routes/projects.js`: nova rota `GET /:user/:project/process/status`;
  `process_msg`; `startProcessing` (emitir «em fila»).
- `apiGateway/routes/projects.js`: rota correspondente.
- `Tools/video/video.py`: `_progress` (temporizador), `callback` (evento «iniciado»).
- `Tools/video/video_processor.py`: `process_video` (`progress_cb` com fase).
- `wsGateway/index.js`: `process_msg`.
- `frontend/app/dashboard/[pid]/page.tsx` (`onVideoProgress`, hidratação inicial),
  `frontend/lib/queries/projects.ts` (`useGetSocket`, nova *query* de estado),
  `frontend/lib/mutations/projects.ts` (`useProcessProject`).

**Avaliação AI: 6,5 / 10.** *Pertinência* média-alta: é o que o utilizador vê enquanto espera e
há um requisito com números. *Complexidade* média: mexe em worker, orquestrador, gateway e
frontend, mas sem grande risco técnico. A avaliação da parte temporal é sólida; a parte de
usabilidade «a sério» pede participantes que a equipa pode não ter até dia 20, e há risco de
ser lida como funcionalidade nova em vez de refactoring.

---

## Ideia 13: Modularidade dos efeitos de imagem e vídeo

**Tipo:** Manutenibilidade — modularidade, reutilização e modificabilidade
(`REQ-VID-EDIT-013`).

**Ideia:** Ter uma única implementação de cada efeito, num pacote partilhado usado pelas
ferramentas de imagem e pelo worker de vídeo, e um único registo de ferramentas de onde
derivam as listas do orquestrador e do frontend.

**Situação base:** As 8 operações PIL estão duplicadas em `Tools/video/effects.py` e em cada
`Tools/<tool>/`. A lista de ferramentas existe em pelo menos quatro sítios. Corresponde à QC-03.

**Diagnóstico completo:**

```python
# Tools/video/effects.py
def border(img, borderWidth, r, g, b):  ...   # cópia de Tools/border/border.py: add_border()
```

```js
// projects/utils/video.js
const VIDEO_TOOLS = ["brightness", "contrast", "saturation", "rotate", "resize", ...];
// projects/utils/project_msg.js
const queues = { 'cut': 'cut_queue', 'scale': 'scale_queue', ... };
```

```python
# Tools/utils/tool_msg.py
queues = { 'border': 'border_queue', 'brightness': 'brightness_queue', ... }
```

Corrigir a validação de um efeito obriga a alterar dois ficheiros Python, reconstruir duas
imagens e, se mudar um parâmetro, tocar no orquestrador e no frontend. `projects/routes/projects.js`
tem 2732 linhas e junta HTTP, orquestração, mensagens e armazenamento. Impacto: é sobretudo
para a equipa de desenvolvimento — maior custo e risco de divergência entre imagem e vídeo (o
mesmo efeito a dar resultados diferentes), que o utilizador acabaria por notar.

**Quantificação:**

*Instrumento:* inspeção estática (sem ensaio de tarefa de manutenção).

| Medida | Valor |
|--------|-------|
| Efeitos com implementação duplicada | 8 de 8 comuns |
| Sítios onde se regista uma ferramenta nova | ≥ 6 (ferramenta, `tool_msg.py`, `project_msg.js`, `video.js`, `definitions.json`, Compose) + frontend |
| Ficheiros a alterar para corrigir um parâmetro de `border` | 2 Python + 2 imagens a reconstruir |
| Tamanho de `projects/routes/projects.js` | 2732 linhas |
| Tempo real de uma tarefa de manutenção equivalente | **não medido** |

*Mínimo aceitável:* para a tarefa «corrigir a validação de um parâmetro de um efeito existente»,
1 ficheiro de lógica alterado e os mesmos testes de pixel a passar em imagem e vídeo.
*Alvo:* acrescentar um efeito comum tocando em ≤ 3 ficheiros, com o registo a gerar as listas
do orquestrador; cobertura de testes de equivalência imagem/vídeo para os 8 efeitos.

**Decisões a tomar e onde mexer:**

Decisões: (a) biblioteca interna (`Tools/effects/`) copiada para as imagens na construção, vs.
serviços de efeito independentes também para vídeo (mais I/O, pior desempenho — desaconselhado);
(b) registo declarativo de ferramentas (JSON) como fonte única; (c) separar
`projects/routes/projects.js` em rotas, orquestração e mensageria.

- Novo `Tools/effects/` com as 8 funções; `Tools/video/effects.py` (`apply_frame_effects`,
  `FRAME_EFFECTS`) passa a importar.
- `Tools/border/border.py` (`add_border`), `brightness`, `contrast`, `saturation`, `rotate`,
  `resize`, `binarization`, `cut`: usar o pacote.
- `Tools/*/Dockerfile`, `Tools/video/Dockerfile`: copiar o pacote.
- `Tools/utils/tool_msg.py` (`queues`), `projects/utils/project_msg.js` (`queues`),
  `projects/utils/video.js` (`VIDEO_TOOLS`, `VIDEO_ONLY_TOOLS`, `PER_VIDEO_TOOLS`): derivar do
  registo.
- `projects/routes/projects.js`: extrair `process_msg`, `addProjectMedia`, `buildSuggestions`
  para módulos próprios.
- `Tools/video/tests/`: testes de equivalência.

**Avaliação AI: 6 / 10.** *Pertinência* média: o beneficiário é a equipa de desenvolvimento,
não o utilizador final, e não há um incidente que a duplicação tenha causado. *Complexidade*
média: é um refactoring clássico e limpo, mas a avaliação de manutenibilidade é a mais difícil
de tornar convincente (tarefa equivalente, efeito de aprendizagem), e sem ela fica em contagens
estáticas. Faz sentido se a equipa quiser um RNF de manutenibilidade para diversificar o par.

---

## Ideia 14: Logs sem segredos e observabilidade

**Tipo:** Manutenibilidade — analisabilidade; Segurança — confidencialidade (dados em logs).

**Ideia:** Substituir os `console.log` dispersos por registo estruturado com níveis e um
identificador de correlação que acompanhe o pedido do gateway ao worker, garantindo que
palavras-passe e *tokens* nunca são escritos.

**Situação base:** O serviço `users` escreve o corpo do registo, com a palavra-passe em claro,
três vezes por registo. `projects` escreve o início do cabeçalho `Authorization`. Não há
identificador comum entre serviços, nem métricas, e a pilha ELK do Compose está comentada.

**Diagnóstico completo:**

```js
// users/routes/users.js — POST /
console.log("BODY:", req.body);
console.log("USER OBJECT BEFORE SAVE:", user);
console.log("User object to persist:", user);

// projects/routes/projects.js — GET /:user/:project
console.log("[GET /:user/:project headers]", { authStart: req.headers.authorization?.slice(0, 20), ... });
```

Impacto: quem lê os logs (operador, fornecedor de alojamento, colega) vê as palavras-passe dos
utilizadores — violação direta do RNF44 e do RGPD. E quando algo corre mal (como o trabalho
perdido da ideia 3) não há forma de seguir um pedido entre serviços: o diagnóstico é manual,
serviço a serviço.

**Quantificação:**

*Instrumento:* `docker logs` do serviço `users` após as medições deste documento.

| Medida | Valor |
|--------|-------|
| Registos de utilizador efetuados | 15 |
| Linhas de log com palavra-passe em claro | **45** (3 por registo) |
| Serviços com identificador de correlação | 0 |
| Serviços com métricas expostas | 0 |
| Tempo para localizar um trabalho perdido entre serviços | **não medido** |

*Mínimo aceitável:* 0 ocorrências de palavra-passe, JWT ou URL assinado nos logs após a suíte
de regressão (verificado por `grep` automático); 100% das linhas de `projects`, gateway e
workers com o identificador do pedido/trabalho. *Alvo:* dado um `msg_id`, reconstruir o
percurso completo com uma única pesquisa em ≤ 1 min; métricas de fila e de duração por
ferramenta.

**Decisões a tomar e onde mexer:**

Decisões: (a) biblioteca de registo (por exemplo `pino`) com redação de campos; (b) propagar
`X-Request-Id` por HTTP e nas mensagens AMQP; (c) reativar ou não a pilha ELK (custo de
memória numa máquina já apertada).

- `users/routes/users.js`: `POST /` (remover os três `console.log` e os do `catch`).
- `projects/routes/projects.js`: `GET /:user/:project`, `POST /:user/:project/process`
  (`[CALLER]`), `process_msg`.
- `apiGateway/app.js`, `projects/app.js`, `users/app.js`: middleware de identificador e
  *logger*; `apiGateway/routes/*.js`: propagar o cabeçalho.
- `projects/utils/project_msg.js`: `send_msg_tool` (incluir o identificador).
- `Tools/utils/tool_msg.py`, `Tools/video/video.py`: registar com o identificador.
- `wsGateway/index.js`: `console.log('Received msg:', ...)` escreve mensagens completas.

**Avaliação AI: 6 / 10.** *Pertinência* média-alta na parte das palavras-passe (é grave e
barato de corrigir) e média na observabilidade (beneficia operador e equipa). *Complexidade*
baixa-média: muitas pequenas alterações, pouca decisão arquitetural; a avaliação da parte de
analisabilidade é difícil de quantificar bem. A remoção das palavras-passe dos logs deve ser
feita **em qualquer caso**, mesmo que esta ideia não seja escolhida.

---

## Ideia 15: Cancelamento efetivo e prazo global de trabalhos

**Tipo:** Eficiência de desempenho — utilização de recursos; Fiabilidade — tolerância a falhas
(`REQ-VID-CANCEL-001/002`, `REQ-VID-TIMEOUT-001`).

**Ideia:** Quando o utilizador cancela, o worker deve parar de facto (matar o `ffmpeg`) e as
operações de vídeo devem ser repostas; e nenhum trabalho deve poder correr para além de um
prazo configurável.

**Situação base:** Cancelar apenas muda o `activeToken` do projeto, o que faz o orquestrador
ignorar o resultado; o worker continua a processar até ao fim. As operações de vídeo não são
reembolsadas. Só as fases de legendas e extração têm *timeout*.

**Diagnóstico completo:**

```js
// projects/routes/projects.js — process_msg()
if (active !== tok) {
  console.log(`[RUN-GUARD] IGNORE msg=${msg_id} processTok=${tok} activeTok=${active}`);
  return;                                   // o trabalho já foi feito, só é deitado fora
}
// DELETE /:user/:project/process — reembolsa só adv_ops
users_ms + `${callerId}/process/refund/${adv_ops}`
```

```python
# Tools/video/video.py — o callback bloqueia até ao fim; não há canal de cancelamento
result = process_video(input_uri, output_uri, tools, preview=preview, progress_cb=...)
```

Impacto: com um único worker (ideia 6), um vídeo de 10 minutos cancelado continua a ocupar o
worker e atrasa todos os outros; o utilizador free que cancela perde a operação.

**Quantificação:** **Não medido** em execução. Estimativa a partir de medições existentes: a
1,3–1,6× a duração (ideia 6), um vídeo premium de 600 s cancelado ao fim de 10 s desperdiça
≈ 13–16 minutos de worker. *Mínimo aceitável:* após cancelar, o worker fica livre em ≤ 10 s e as
operações de vídeo são repostas em 100% dos casos. *Alvo:* ≤ 3 s; prazo global configurável
(por exemplo 5× a duração) que termina o trabalho com erro explícito.

**Decisões a tomar e onde mexer:**

Decisões: (a) como o worker fica a saber — fila de controlo por worker, ou consulta periódica
do *token* no `progress_cb`; (b) execução do `ffmpeg` em subprocesso com `terminate`;
(c) política de reembolso de vídeo.

- `Tools/video/video.py`: `VideoWorker.callback`, `_progress` (verificar cancelamento),
  novo consumidor de controlo.
- `Tools/video/video_processor.py`: `process_video`, `_process_video`, `_start_encoder`
  (matar subprocessos, exceção `Cancelled`, prazo global).
- `projects/routes/projects.js`: `DELETE /:user/:project/process` (publicar cancelamento;
  reembolsar `vid_ops`), `process_msg`.
- `projects/utils/project_msg.js`: novo `send_msg_cancel`.
- `docker-compose.yaml`: variável do prazo.

**Avaliação AI: 5,5 / 10.** *Pertinência* média: há requisitos escritos, mas o cenário é menos
frequente e o seu custo só pesa quando a fila está cheia. *Complexidade* média-alta
(sinalização a um consumidor bloqueado e terminação limpa do `ffmpeg`), mas sem medição de base
feita, o que enfraquece a avaliação a quatro dias da entrega. Melhor como complemento da
ideia 6.

---

## Ideia 16: Canal AMQP persistente no orquestrador

**Tipo:** Eficiência de desempenho — utilização de recursos e comportamento temporal;
Fiabilidade — maturidade.

**Ideia:** Reutilizar uma ligação e um canal AMQP por processo no orquestrador (e no
`ws_gateway`), em vez de abrir e fechar uma ligação TCP por cada mensagem publicada.

**Situação base:** Cada `send_rabbit_msg` abre uma ligação, cria um canal, declara a *exchange*,
publica e fecha a ligação 500 ms depois por temporizador, sem confirmar que a publicação saiu.

**Diagnóstico completo:**

```js
// projects/utils/rabbit_mq.js
function send_rabbit_msg(msg, queue) {
    amqp.connect(rabbit_mq_sv, (err_sv, connection) => {
        if (err_sv) throw err_sv;                       // derruba o processo
        connection.createChannel((err_conn, channel) => {
            channel.assertExchange(exchange, 'direct', { durable: true });
            channel.publish(exchange, queue, Buffer.from(JSON.stringify(msg)));
        });
        setTimeout(() => { connection.close(); }, 500); // fecha às cegas
    });
}
```

Um «Apply» sobre N imagens com T ferramentas publica N×T pedidos mais as notificações ao
cliente, cada um com a sua ligação. Se o broker estiver lento, os 500 ms podem não chegar e a
mensagem perde-se sem erro. Impacto: sobretudo para o operador (carga no broker e esgotamento
de sockets em lotes grandes) e, indiretamente, perdas silenciosas para o utilizador.

**Quantificação:**

*Cenário:* 1 «Apply» com 5 imagens e 3 ferramentas (15 passos). *Instrumento:* `churn.mjs`,
contador `connection_created` da API de gestão do RabbitMQ.

| Medida | Valor |
|--------|-------|
| Ligações AMQP abertas por um «Apply» | ≥ 5 observadas (o contador é amostrado a cada 5 s e subestima; pelo código são ≥ 20) |
| Ligações necessárias com canal persistente | 0 novas |
| Latência de publicação e perdas sob carga | **não medido** |

*Mínimo aceitável:* 0 ligações novas por mensagem em regime estável; nenhuma mensagem perdida em
1000 publicações consecutivas. *Alvo:* publicação confirmada (*publisher confirms*) com p95
≤ 20 ms.

**Decisões a tomar e onde mexer:**

Decisões: (a) módulo único de mensageria com ligação partilhada, religação e confirmações —
é o mesmo módulo que a ideia 3 exige; (b) biblioteca com gestão de ligação
(`amqp-connection-manager`) vs. código próprio.

- `projects/utils/rabbit_mq.js`: `send_rabbit_msg`, `read_rabbit_msg`.
- `wsGateway/utils/rabbit_mq.js`: `send_rabbit_msg`.
- `projects/utils/project_msg.js`: todas as funções `send_msg_*` (passam a ser `async`).
- `projects/routes/projects.js`: chamadas a `send_msg_tool` em `process_msg` e
  `startProcessing` (esperar a confirmação).

**Avaliação AI: 5 / 10.** *Pertinência* baixa-média: é ineficiência real, mas sem sintoma
observado pelos utilizadores à escala atual, e a medição de base ficou fraca. *Complexidade*
baixa. Não justifica um RNF próprio; deve ser feita **dentro** da ideia 3, que já reescreve este
módulo.

---

## Ideia 17: Usabilidade da criação do pipeline

**Tipo:** Usabilidade — operabilidade, capacidade de aprendizagem e proteção contra erros
(RNF55, `REQ-VID-FAIL-003`).

**Ideia:** Tornar claro, no editor, que ferramentas se aplicam a quê (imagem, vídeo, um vídeo
específico), porque é que uma ferramenta está indisponível, e validar os parâmetros antes do
«Apply» com mensagens diferenciadas.

**Situação base:** Em projetos com vídeo o frontend esconde as ferramentas só de imagem (IA,
marca de água) e a exportação em PDF sem explicar porquê; `trim` e `speed` pertencem a um vídeo
e as restantes a todos os media, regra que não é visível; os erros de validação chegam como
texto genérico. Corresponde à QC-04a.

**Diagnóstico completo:** Os mecanismos estão descritos no diagnóstico do exercício 6
(EV-22, EV-23): visibilidade dependente do tipo de media, estado de progresso no browser e
*overlay*. O servidor devolve mensagens como `"Effects not available for video: ..."` e
`"Error processing project"`, que o frontend mostra tal e qual. A ideia 4 mostrou que
parâmetros inválidos são aceites sem aviso. Impacto: utilizadores novos (sobretudo anónimos e
free, que são a porta de entrada do produto) podem não perceber por que razão uma ferramenta
desapareceu ou o que correu mal.

**Quantificação:** **Não medido.** Não há ensaio com participantes nem tarefa cronometrada.
Proposta de protocolo: 5 participantes externos à equipa, 3 tarefas (pipeline só de imagem,
projeto misto, corrigir um parâmetro inválido), medindo taxa de sucesso, tempo e número de
erros. *Mínimo aceitável:* ≥ 80% de tarefas concluídas sem ajuda. *Alvo:* ≥ 90% (alinhado com
o critério do RNF55) e tempo mediano por tarefa reduzido em 25% face à base.

**Decisões a tomar e onde mexer:**

Decisões: (a) ferramentas indisponíveis ficam visíveis mas desativadas, com explicação;
(b) catálogo de erros com código e mensagem orientada à ação; (c) validação no cliente a partir
do mesmo esquema do servidor (ideia 4).

- `frontend/app/dashboard/[pid]/page.tsx` e os componentes da barra de ferramentas em
  `frontend/components/`: regras de visibilidade e mensagens.
- `frontend/lib/mutations/projects.ts`: `useProcessProject` e as mutações de ferramentas
  (tratamento de erros).
- `projects/routes/projects.js`: respostas de erro de `POST /:user/:project/tool`, `/reorder`
  e `/process` (códigos estáveis).
- `projects/utils/video.js`: `validateFrameExtraction`, `unsupportedVideoTools` (devolver
  códigos).

**Avaliação AI: 4,5 / 10.** *Pertinência* potencialmente alta, mas **não demonstrada**: não há
evidência de que os utilizadores tenham dificuldade. *Complexidade* técnica baixa; o que é
exigente é a avaliação, que precisa de participantes e de um protocolo controlado — difícil de
montar até dia 20. Sem essa medição, é a ideia com a avaliação menos sólida do catálogo.

---

## Ideia 18: Imagens de contentor reprodutíveis e leves

**Tipo:** Portabilidade — instalabilidade; Manutenibilidade — (reprodutibilidade da construção)
(`REQ-VID-EDIT-014`).

**Ideia:** Fixar as versões das imagens de base, usar variantes *slim* com construção em várias
fases e utilizador sem privilégios, e acrescentar `.dockerignore`, para que a instalação seja
mais rápida, ocupe menos e dê o mesmo resultado daqui a seis meses.

**Situação base:** Cinco serviços usam `FROM node` sem versão; o nginx usa `nginx:latest` e a
marca de água uma imagem pública `:latest`. As imagens Node pesam 1,6–2,5 GB cada. Os
contentores correm como `root`.

**Diagnóstico completo:**

```dockerfile
# projects/Dockerfile
from node
run apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
workdir /app
copy . .
run npm install
```

`FROM node` segue a versão mais recente: uma reconstrução futura pode trazer um Node
incompatível sem ninguém ter mudado código. `copy . .` antes de `npm install` invalida a cache
a cada alteração. O `AGENTS.md` avisa que a primeira construção demora 15–30 min e precisa de
≈ 15 GB. Impacto: docentes e colegas que instalam o projeto para o avaliar, e o operador que
paga disco e tempo de implantação.

**Quantificação:**

*Instrumento:* `docker image ls` após construir o stack isolado.

| Imagem | Tamanho |
|--------|---------|
| projects | 2,45 GB |
| img_storage | 1,98 GB |
| users | 1,87 GB |
| api_gateway | 1,84 GB |
| ws_gateway | 1,60 GB |
| video_tool | 1,56 GB |
| ferramenta PIL (cada) | 256 MB |

Imagens de base sem versão fixa: 7 (5 Node, nginx, marca de água). Tempo de construção a frio:
**não medido** (a construção de hoje aproveitou cache). *Mínimo aceitável:* 100% das imagens de
base com versão fixa; imagens Node ≤ 500 MB. *Alvo:* ≤ 300 MB; todos os serviços a correr sem
`root`; construção a frio dos serviços Node ≤ 5 min.

**Decisões a tomar e onde mexer:**

Decisões: (a) `node:22-slim` vs. `alpine` (o `sharp` e o `bcrypt` têm binários nativos);
(b) construção em duas fases com `npm ci --omit=dev`; (c) fixar por *digest* ou só por versão.

- `apiGateway/Dockerfile`, `projects/Dockerfile`, `users/Dockerfile`,
  `subscriptions/Dockerfile`, `imageStorageService/Dockerfile`, `wsGateway/Dockerfile`,
  `frontend/Dockerfile`.
- Novo `.dockerignore` em cada serviço.
- `docker-compose.yaml`: `nginx`, `watermark_tool_ms` (versões).
- `Tools/requirements.txt`: fixar versões.

**Avaliação AI: 4,5 / 10.** *Pertinência* baixa para os utilizadores finais; real mas modesta
para quem instala e opera. *Complexidade* baixa e bem conhecida. A métrica é muito limpa
(tamanho, tempo), mas a profundidade arquitetural é pouca para um RNF de fase. Bom trabalho de
«arrumação» se sobrar tempo.

---

## Ideia 19: Exportação ZIP em streaming

**Tipo:** Eficiência de desempenho — utilização de recursos.

**Ideia:** Gerar o ZIP de resultados em fluxo, diretamente do S3 para a resposta HTTP, em vez
de o montar inteiro em memória.

**Situação base:** A rota de resultados descarrega cada ficheiro para um *buffer*, junta tudo
num `JSZip` em memória e só depois responde. É a extensão da QC-05 que a `team-review.md`
deixou fora do âmbito inicial.

**Diagnóstico completo:**

```js
// projects/routes/projects.js — GET /:user/:project/process
const zip = new JSZip();
...
const ans = await zip.generateAsync({ type: "blob" });
```

Com vídeos, os resultados podem somar centenas de MB (um projeto premium com vários vídeos de
10 min), e a memória de `projects` cresce com o total. `projects` é também o orquestrador: se
ficar sem memória, param todos os trabalhos em curso. O gateway volta a carregar a resposta em
memória antes de a entregar.

**Quantificação:** **Não medido** (exigiria um projeto com resultados grandes). Por analogia
com a ideia 2, espera-se ≥ 1× o tamanho total dos resultados em `projects` e outro tanto no
gateway. *Mínimo aceitável:* pico de RSS adicional ≤ 64 MiB em `projects` e no gateway ao
exportar 500 MiB de resultados. *Alvo:* ≤ 32 MiB e primeiro byte em ≤ 1 s.

**Decisões a tomar e onde mexer:**

Decisões: (a) biblioteca de ZIP em fluxo (`archiver`) com `store` para vídeo (já comprimido);
(b) o gateway passa a fazer *pipe* da resposta; (c) alternativa: devolver URL assinados
individuais para vídeos.

- `projects/routes/projects.js`: handler `GET /:user/:project/process`.
- `apiGateway/routes/projects.js`: rota correspondente (`responseType: "stream"` e `pipe`).
- `frontend/lib/queries/projects.ts`: descarga do ZIP.

**Avaliação AI: 4 / 10.** *Pertinência* média-baixa: o risco é real mas só se manifesta com
resultados grandes, e não foi medido. *Complexidade* baixa (uma rota e o seu *proxy*). Só faz
sentido como alargamento do âmbito da ideia 2, reutilizando o mesmo instrumento de medição.

---

## Anexo: como repetir as medições

```bash
docker compose -p picturas-nfr -f docker-compose.yaml -f memory-bank/intents/001-phase-2-quality-improvements/evidence/nfr-2026-11-16/override.yaml up -d --build nginx api_gateway ws_gateway projects users img_storage seaweedfs rabbitmq projects_mongoDB users_mongoDB video_tool brightness_tool border_tool
```

Depois, na pasta `evidence/nfr-2026-11-16/`, gerar os ficheiros de teste com
`python3 make_pads.py` (o vídeo `samples/video/sample_10s_720p.mp4` seguido de uma caixa MP4
`free` até exatamente 10, 100 e 500 MiB) e correr, por esta ordem, `node uploads.mjs`,
`node security.mjs`, `node verify.mjs`, `node reliability.mjs R0`, `R1`, `R2`, `R3` e
`node churn.mjs`. O upload de 500 MiB acima do limite deixa o gateway em baixo: é preciso
`docker restart picturas-nfr-api_gateway-1` antes de continuar. Para parar apenas os serviços de ensaio, preservando os volumes:

```bash
docker compose -p picturas-nfr -f docker-compose.yaml -f memory-bank/intents/001-phase-2-quality-improvements/evidence/nfr-2026-11-16/override.yaml stop
```

**Assistência de IA.** Auditoria do código, scripts de medição, execução e redação feitas por
Claude a pedido do Miguel. As medições são reais e os resultados brutos estão na pasta de
evidência; as notas e os valores mínimo/alvo são propostas para a equipa validar, não decisões.


## Justificação das decisões e preparação da defesa

A [secção final das ideias 1 e 2](../../../docs/fase2-ideias-1-e-2.md#justificação-das-decisões)
é a versão canónica: cada escolha indica motivo, alternativa, custo, risco residual e
métricas de prova. Inclui também as decisões em aberto, sem as resolver por omissão.
O [plano de avaliação](../../../docs/fase2-metricas-e-baseline.md) distingue piloto,
baseline formal, métrica principal, guarda e diagnóstico. Para defender A em vez de B,
usar esses argumentos e resultados observados, não as notas qualitativas da AI.

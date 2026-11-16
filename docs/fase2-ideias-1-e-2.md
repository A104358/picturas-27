# PictuRAS — Fase 2: ideias 1 e 2, escolhas comunicadas e decisões em aberto

Extrato das ideias 1 e 2 do catálogo de upgrades não funcionais
(`memory-bank/intents/001-phase-2-quality-improvements/upgrade-ideas.md`), já com as soluções
propostas e as escolhas assinaladas no documento de 16/11/2026. Estas escolhas não equivalem
a uma declaração recebida de aprovação individual dos quatro elementos; os pontos em
aberto continuam por decidir. As medições foram feitas nessa data, num stack
isolado; o ambiente, as limitações e os scripts estão descritos no catálogo («Como ler este
documento») e em `memory-bank/intents/001-phase-2-quality-improvements/evidence/nfr-2026-11-16/`.
As referências a outras ideias (5, 7, 8, 9, 11) remetem para o catálogo.

**Par acordado — PL2-G4:** Segurança, autorização ponta a ponta (QC-06 / ideia 1),
e Eficiência de desempenho, utilização de recursos nos uploads (QC-05 / ideia 2).
O acordo foi registado em 16/11 por instrução explícita do utilizador; a fonte e
o âmbito constam do [registo coletivo do par](../memory-bank/intents/001-phase-2-quality-improvements/quality-exploration.md#decision-record--pair-agreement).
Este acordo não fecha os detalhes pendentes nem aprova todas as métricas.

**Prazo atual de entrega:** 27/11/2026, corrigido explicitamente pelo utilizador
nesta conversa. Substitui 20/11 no planeamento; a data das diretrizes e dos registos
históricos é preservada como fonte anterior, sem a atribuir ao prazo atualizado.

**Cobertura de segurança validada individualmente — opção A:** mTLS nas APIs
internas, incluindo ws_gateway → projects, com autorização específica por serviço
e operação. Nos restantes canais, TLS com validação do certificado do servidor;
em MongoDB, RabbitMQ e S3, credenciais próprias e permissões mínimas por serviço,
onde aplicável. Não se exige mTLS universal nesta entrega. Mantêm-se as decisões
JWT, de autorização e WS já validadas; configuração e cumprimento ainda por provar.

A última secção explica cada decisão: porque foi escolhida, que outras opções havia e porque
foram adiadas. Quando uma alternativa oferece uma garantia diferente, explicam-se essa
garantia, o custo e o risco residual, sem a classificar como superior em todos os contextos.


> **Revisão de 16/11 — estado das decisões e qualidade da evidência.** As escolhas
> assinaladas foram tratadas como escolhas comunicadas no documento, sem atribuir
> aprovação individual não recebida. Os pontos em aberto não foram fechados nesta
> revisão. Os resultados ARM e x86_64 permanecem separados; os totais de segurança
> precisam de asserções corrigidas. A baseline formal ainda não está concluída.
>
> Ver o [plano de 60 métricas, mínimos/metas e baseline](fase2-metricas-e-baseline.md)
> e a [justificação completa no fim deste documento](#justificação-das-decisões).

**Validação individual recebida em 16/11:** o utilizador confirmou as opções A de
D3/JWT, D7 e D6.1, com as condições registadas abaixo. Esta validação **dos detalhes
permanece individual**, sem aprovação global das métricas ou autorização para começar
a implementação. Posteriormente, o utilizador escolheu **D6.2 B + D6.3 A** e o
assistente confirmou a adequação técnica ao âmbito, com confiança média: consultar
projects por entrada e retirar ativamente acesso quando a autorização efetiva
deixar de existir. Numa validação posterior, confirmou D6.2 B e as três opções A
de permanência, falhas/prazos e expiração do JWT, nas condições seguintes. Os
critérios foram escolhidos individualmente; o seu cumprimento ainda não foi medido.

**Atualização individual D4/WS-C1/WS-C2:** mTLS passa a autenticar os serviços
internos, substituindo a escolha anterior HTTPS + JWT assimétrico de serviço
referida pelo utilizador nesta atualização. WS-C1 A e WS-C2 A estão validadas com
as condições abaixo. D3 mantém HS256 de utilizador e RS256 da identidade emitida
pelo gateway; o restante contrato WS continua proposto, sem testes executados ou
autorização para alterar a aplicação.

| Decisão | Validação recebida | Condição / trabalho ainda pendente |
|---------|---------------------|-------------------------------------|
| D3/JWT | Manter JWT de utilizador em HS256 nesta fase; segredo renovado e fora do repositório. Identidade interna emitida pelo gateway em RS256. | Definir a transição de todas as sessões, incluindo as anónimas, **antes** de renovar o segredo. TTL, rotação e restantes detalhes de identidade continuam por fechar. |
| D4 | mTLS para autenticação de serviços internos, em substituição de HTTPS + JWT assimétrico de serviço. | Autenticar a identidade específica e autorizar par/operação; cadeia/CA válida não basta. Proteger chaves e definir emissão/renovação; operacionalização detalhada em revisão. D3 e autorização do domínio mantêm-se. |
| WS-C1 A | Consulta direta ws_gateway → projects por mTLS; WS delega identidade e expiração verificadas no JWT da ligação, associadas aos contextos apresentados. | Projects autentica especificamente WS, autoriza as operações permitidas e decide sempre as permissões. Não aceitar certificado de outro serviço da CA como equivalente. |
| WS-C2 A | Timeout total inicial 1 s (espera/ligação/envio/leitura), até 50 avaliações membro/contexto por pedido, configuráveis e sujeitos a medição. | Vários lotes, concorrência limitada e agendamento justo; falhas/tentativas não prolongam autorizações. Corte ≤5 s/meta ≤2 s mantidos; capacidade não demonstrada. |
| WS-C3 A | Inicialmente 4 consultas HTTP globais, 1 por projeto, alternância de lotes entre projetos e 64 KiB por corpo JSON de pedido/resposta. | Configuráveis, não capacidade medida; 50 avaliações/64 KiB em conjunto, timeout inclui fila, sem truncagem nem renovação em falha. Máximo da fila/corpus final pendentes. |
| PKI-C1 A | CA própria por instalação (365 dias), chave por serviço, certificados de serviço de 30 dias e renovação quando faltarem 7 dias. | Script local de emissão/renovação entra na entrega, iniciado pelo administrador; validar arranque/retorno após >30 dias e recusar emissão além da CA. Revogação/rotação de ligações persistentes ainda por fechar. |
| ACL-C1 A | Eliminar o projeto inteiro fica reservado ao dono; editor mantém edição e remoção de media; leitor não elimina. | Mudança explícita de política: antes, DELETE aceitava partilha edit. Justificar como correção de segurança, verificar UI e preservar limpeza autorizada na eliminação de conta. |
| D7 | `owner` pode estar ausente; quando presente, tem de ser um valor único coincidente com o dono no caminho. Contradições são recusadas. | A projects verifica sempre posse e partilha; a validação do parâmetro não substitui autorização do recurso. |
| D6.1 | Recusar ligações Socket.IO sem JWT válido, incluindo o perfil anónimo; terminar a ligação quando o JWT expirar. | Frontend trata explicitamente a reconexão com JWT válido e nova autorização por sala; não presumir reconexão automática após corte pelo servidor. Transição/renovação preserva identidade e projetos anónimos e ainda precisa de desenho. |
| D6.2 B | Consultar projects para autorizar cada entrada numa sala, considerando identidade, projeto e permissões atuais. | Indisponibilidade recusa nova entrada e permite tentativa posterior. WS-C1 A/WS-C2 A validam mTLS direto e timeout total inicial 1 s; payloads/ordenação/corridas continuam propostos. |
| D6.3 A | Revalidar inicialmente a cada 1 s, agrupando consultas por projeto com autorização individual e contexto de cada membro; retirar acesso sem autorização efetiva. | Critério de corte ≤5 s e meta ≤2 s, por validar experimentalmente. Autorização local até 5 s desde o início da consulta positiva, limitada por JWT/permissão; falhas não renovam. Preservar outras autorizações; recusar respostas atrasadas/fora de ordem que restaurem acesso indevido. Eventos ficam como evolução. |

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


## Justificação das decisões

Esta secção está preenchida para apoiar o relatório e a defesa: apresenta a escolha
**assinalada no documento de origem**, o motivo, alternativas, custos, riscos e prova
necessária. Um parecer técnico não passa automaticamente a decisão da equipa. As notas
AI 9,5/9 são opiniões qualitativas, não avaliação docente nem medições.

A especificação de métricas, mínimos/metas e os números já extraídos estão em
[fase2-metricas-e-baseline.md](fase2-metricas-e-baseline.md). A baseline formal só fica
concluída depois de corrigir as asserções e preencher os gates obrigatórios. Não iniciar
refactoring da aplicação enquanto essas condições e a revisão de requisitos estiverem abertas.

### Estado das escolhas e questões que faltam fechar

| ID | Estado comunicado nos documentos | O que falta para ficar implementável e avaliável |
|----|----------------------------------|--------------------------------------------------|
| D1 | Âmbito alargado: público, rede, portas, dados/S3 | Enumerar interfaces, identidades e ações abrangidas; medir todos os caminhos incluídos. Não significa proteger contra administrador do host comprometido. |
| D2 | Gateway filtra, projects decide posse/partilha | Matriz por rota/verbo e uma regra de domínio consistente. |
| D3/JWT | Validada pelo utilizador: HS256 utilizador; RS256 identidade interna | Definir transição de sessões registadas/anónimas antes de renovar o segredo; fechar aud, TTL, replay e rotação. |
| D4 | Validada individualmente: cobertura A, mTLS nas APIs internas e TLS validado/credenciais/permissões nos restantes canais; JWT assimétrico de serviço substituído | PKI-C1 fixa CA por instalação 365 dias/serviço 30 dias/renovar a 7 dias e script local na entrega; revogação/persistência, guardas Git/build e matriz ainda por implementar/provar. Não exigir mTLS universal; D3 mantida. |
| D5 | Portas internas só em loopback; rede única mantida | Demonstrar alcance do host e da rede Docker separadamente; proteger também localhost. |
| D6.1 | Validada individualmente: JWT válido obrigatório e término da ligação na expiração | Reconexão explícita com JWT válido/nova autorização por sala; fechar renovação/transição preservando identidade e projetos anónimos. |
| D6.2 B | Escolhida pelo utilizador: consulta à projects em cada entrada; sem bilhetes WS | mTLS direto/timeout total inicial 1 s validados em WS-C1/WS-C2; payloads/ordenação/corrida ainda propostos, com recusa temporária em falha. |
| D6.3 A | Validada individualmente: revalidação inicial 1 s, lotes por projeto, autorização individual/contextual; critério ≤5 s, meta ≤2 s | Medir cumprimento/carga; autorização local até 5 s desde início da consulta positiva, limitada por JWT/permissão; falhas não prolongam; negação efetiva retira já; ordenar respostas/corridas. |
| D7 | Validada pelo utilizador: ausência permitida, valor único se presente e coerente com o caminho | Casos de query ambígua e controlo obrigatório de posse/partilha na projects. |
| D8 | Expiração de links proposta como escolha | Rever alteração funcional/migração e definir política para links legados. |
| D9 | Incluir users/subscriptions | Trazer subscriptions para o ambiente e testar login/registo anónimo, billing mock e rotas internas. |
| D11 | Token de upload com verificação própria simplificada | Estado atómico/uso único, retries, revogação entre emissão e uso, e confirmação idempotente. |
| U1–U4 | Upload de vídeo por nginx/S3, validação em dois momentos, hash posterior e limpeza | Contrato de API/compatibilidade, estado/quarentena, hipóteses SeaweedFS e recuperação de cada estágio. |
| D10 e detalhes de D6.2/D6.3 | **Parcialmente em aberto** | Superfícies/casos e restante contrato/ordenação/limites globais. WS-C1 A/WS-C2 A, permanência periódica, prazos/falhas e corte por JWT expirado validados individualmente; falta prova experimental. |
| Sessões/TTL/links legados | **Em aberto** | Transição antes da renovação HS256, validades, rotação e migração dos links; algoritmos de D3 já validados individualmente. |

### Ideia 1 — porquê estas escolhas e não as alternativas

**D1 — Abranger entradas públicas, internas e acesso aos dados.**
A razão é evitar que uma proteção HTTP seja contornada por outra rota que chega aos
mesmos projetos/objetos. As alternativas são um âmbito público menor, ou apenas endurecer
a rede. O âmbito menor é legítimo se declarado, mas não sustenta «0 bypasses» nos caminhos
que deixámos abertos. O custo da escolha alargada é uma matriz maior e inicialização de
credenciais em todas as bases incluídas. A prova é S01–S04 e S14–S20, com fixtures
sintéticas e controlos positivos. Não confundir ausência de credenciais com compromisso
root do host: este último fica fora do modelo e deve ser dito na apresentação.

**D2 — Decisão em camadas, com a projects como autoridade do domínio.**
O gateway rejeita identidade manifestamente inválida; a projects conhece dono e partilha
e faz a decisão final sobre o recurso. Só o gateway deixaria uma dependência forte da
inacessibilidade interna; duplicar a base de permissões no gateway introduziria divergência.
Só a projects é tecnicamente possível, mas transfere os pedidos inválidos até ao serviço
de dados. Não há necessidade de duplicar a regra completa: filtro de identidade no gateway,
regra de domínio na projects. Provar por ataques públicos e diretos e por partilhas válidas;
não basta verificar que o token existe.

**D3 — Identidade interna assinada pelo gateway.**
Mantém o formato do JWT de utilizador e permite limitar destinatário e duração da identidade
interna. A alternativa é verificar diretamente o JWT de utilizador em cada serviço; com
assinaturas assimétricas, os verificadores recebem apenas chaves públicas. Outra alternativa,
confiar num cabeçalho simples após isolar a rede, não elimina a falsificação demonstrada.

O utilizador validou **RS256 para a identidade interna**: a chave privada fica no
gateway e os verificadores usam a pública. HMAC/HS256 interno foi afastado porque
partilhar a chave de verificação permitiria aos verificadores emitir identidades.
O gateway continua emissor de confiança; mTLS não elimina esse poder.

Para os JWT de utilizador, o utilizador validou **manter HS256 nesta fase**, com
segredo renovado fora do repositório, evitando alargar já a migração a todos os
emissores/verificadores. A alternativa RS256 para esses JWT fica adiada, não
classificada como desnecessária. A renovação do segredo não pode avançar sem um
plano de transição para sessões registadas **e anónimas**: não presumir perda de
projetos anónimos, renovação automática segura ou manutenção de tokens antigos
assinados pelo segredo exposto. Esses mecanismos continuam por decidir. Prova:
S06–S07/S20/S21, F04/F06 e controlo de reconexão por perfil.

### D4 — mTLS entre serviços, ciclo de certificados e pares

**Estado:** validada individualmente em 16/11. O utilizador substitui a sua escolha
anterior **HTTPS + JWT assimétrico de serviço** por **mTLS para autenticação entre
serviços internos**. A escolha anterior fica **substituída**, sem inventar a sua
data original; foi identificada como anterior pelo utilizador nesta mensagem.
Os documentos já apresentavam mTLS como proposta/escolha comunicada; esta atualização
regista explicitamente a substituição e o âmbito da validação recebida.

Autentica as duas pontas quando se verificam a cadeia, validade, nomes e identidade do peer.
É compatível com a infraestrutura HTTPS existente, mas storage hoje usa HTTP: não é só
«ligar uma opção». HTTPS + JWT assimétrico de serviço permanece como alternativa
histórica substituída, não como fallback em falha mTLS. Não há comparação de esforço
ou desempenho que prove superioridade universal da solução escolhida.

| Função | Mecanismo mantido/escolhido |
|--------|---------------------------|
| Autenticar o utilizador, incluindo anónimo | JWT HS256, D3; transição antes de renovar o segredo continua por definir. |
| Identidade interna emitida pelo gateway | RS256, D3; não é o JWT de serviço substituído em D4. |
| Autenticar os serviços nas ligações internas | mTLS, D4; autorizar também serviço de origem, destino e operação. |
| Autorizar posse/partilha/ações de projeto | Projects, com identidade/contexto comprovados; certificado não concede posse. |

Correção importante para a defesa: **mTLS usa segredos — as chaves privadas**. Têm de ser
geradas, distribuídas, protegidas e renovadas fora do repositório. Também um JWT de serviço
pode ser assimétrico; não precisa de segredo de assinatura partilhado. Aceitar qualquer
certificado da CA não basta: é necessária uma lista de serviços/operações autorizadas.
Uma chamada da projects autenticada ainda precisa de indicar o contexto/projeto permitido.

**Proteção e ciclo de vida — operacionalização proposta para revisão:**

- CA interna com chave de emissão protegida fora do repositório e dos contentores
  aplicacionais; distribuir aos verificadores apenas os certificados públicos de confiança.
  Cada serviço tem a sua identidade e chave própria, sem chave privada global partilhada.
- Gerar chaves fora do checkout; limitar leitura ao utilizador/processo necessário,
  montar apenas nos serviços titulares em modo de leitura e manter fora de imagens,
  `.env`, logs e artefactos da entrega. Não montar a chave da CA nos serviços.
  O WS não recebe a chave privada RS256 do gateway; projects não recebe o segredo HS256.
- Emitir por script/procedimento reproduzível após conferir a identidade do serviço;
  registar emissor, serial, SAN, finalidade/EKU e validade, sem registar chave privada.
  Verificar também a identidade do servidor no cliente; não usar `rejectUnauthorized: false`.
- Renovar antes de expirar e testar instalação/recarregamento de certificados e
  trust stores, incluindo conexões persistentes. Propor sobreposição controlada de
  confiança para rotação planeada, seguida de retirada explícita da credencial antiga.
  Renovar não invalida automaticamente o certificado anterior ainda válido.
- Definir tratamento de chave comprometida, revogação/rejeição e conexões já abertas;
  não presumir que renovar certificado corta sessões existentes. Duração/antecedência
  são escolhidas em PKI-C1 abaixo; sobreposição, revogação, ligações persistentes e
  procedimento operacional detalhado continuam por fechar.
  Não gerar certificados ou alterar Compose/aplicação nesta fase de documentação.

**PKI-C1 A — modelo e durações escolhidos individualmente:** uma CA por instalação,
**365 dias** de validade da CA, certificados próprios por serviço de **30 dias**,
renovação quando faltarem **7 dias** (aproximadamente aos 23 dias de um certificado
de 30). Valores de engenharia, não requisitos docentes nem prova de operação segura.
Concretizando a condição do utilizador, **o script local de emissão/renovação e os
seus testes entram no âmbito da entrega**; mantém-se a validade de 30 dias. A opção
de aumentar para 90 dias fica não escolhida. Não se prevê um daemon de renovação
automática: o administrador inicia o procedimento local, que deve verificar a
validade antes de colocar os serviços em funcionamento.

Uma instalação desligada por mais de 30 dias precisa de renovar os certificados
antes do regresso ao serviço; não aceitar certificados expirados como atalho. Uma
CA expirada ou com prazo insuficiente para emitir um certificado de 30 dias exige
tratamento explícito da CA/confiança antes dessa emissão. Não emitir validade além
da CA. A chave privada da CA fica fora do Git, dos contextos de build e dos
contentores aplicacionais; os certificados públicos de confiança podem ser distribuídos
aos verificadores. Cada instalação e serviço mantém a sua identidade; nenhuma CA
da equipa é implicitamente confiável por outra instalação.

Revogação, retirada da confiança antiga, recarregamento/reinício e tratamento de
keep-alive/conexões persistentes **continuam por fechar**. Alterar ficheiros ou
renovar certificados não prova que ligações existentes passaram a usar os novos.
Sem esses mecanismos e testes não declarar a PKI completa; o prazo WS de 5 s não
é automaticamente um SLA de revogação de certificados.

**Auditoria dos guardas Git/build — lacuna atual, não proteção já implementada.**
O [registo de inspeção](../memory-bank/intents/001-phase-2-quality-improvements/evidence/security-planning-audit-2026-11-16.json)
mostra três caminhos sintéticos de chaves não cobertos pelo `.gitignore`, seis
chaves antigas já versionadas e sete contextos Node/frontend com cópia do contexto
inteiro, sem exclusão de chaves demonstrada nas regras inspecionadas. Não foram
criados os ficheiros sintéticos, lidas chaves privadas ou construídas imagens.
Ignorar um caminho também não retira um ficheiro já versionado.

Na implementação, incluir exclusões defensivas no Git e nos contextos Docker,
manter a chave real da CA fora deles e testar com **marcadores sintéticos**, nunca
com chaves reais: caminho ignorado, ausente do contexto e ausente das camadas da
imagem produzida. Verificar também a montagem restrita das chaves certas por serviço.
As exclusões devem acompanhar a migração para mounts externos, sem quebrar
silenciosamente o arranque que hoje lê certificados do checkout. Não se alteraram
ignores/build/aplicação nesta revisão anterior à baseline formal.

Ensaios PKI a preparar: emissão/identidade/finalidade corretas e indevidas, outra
CA/instalação, renovação no limiar de 7 dias, regresso após mais de 30 dias, CA
perto de expirar, chave/CA fora de Git/imagem e retirada/rejeição da credencial
antiga em ligações novas/persistentes quando o mecanismo for escolhido. Não foram
executados nesta revisão. A duração não substitui os testes de revogação.

**Matriz inicial de pares e operações — especificação a rever:** negar pares/ações
não previstos. O par WS → projects e as suas restrições estão explicitamente
validados; os restantes detalham as dependências observadas e precisam de revisão
por rota/verbo e controlo positivo. São autorizações limitadas, não acesso geral ao destino.

| Origem autenticada | Destino | Operações permitidas no âmbito e restrições |
|-------------------|---------|--------------------------------------------|
| ws_gateway | projects | Apenas consultas de autorização de entrada/revalidação WS, com identidade/expiração verificadas e contextos do membro; sem mutações de projeto por essa delegação. WS-C1 A validada. |
| api_gateway | projects | Encaminhar operações de projeto permitidas ao chamador; exigir identidade RS256 de D3 e decisão de posse/partilha na projects. |
| api_gateway | users | Rotas de conta/sessão/perfil/presets autorizadas ao chamador; exceções de login/registo/anónimo explícitas. Certificado não permite promoção arbitrária de perfil. |
| api_gateway | subscriptions | Planos e billing mock nas operações autorizadas ao utilizador; sem acesso irrestrito a subscrições alheias. |
| projects | users | Consultar perfil/limites e reservar/devolver quota no fluxo previsto; sem administração geral de contas. |
| projects | img_storage | Ler/escrever/copiar/remover/assinar objetos nos projetos/estágios autorizados, incluindo confirmação/hash/cleanup quando o contrato de upload for fechado. |
| users | projects | Limpeza de projetos ao remover a conta, limitada ao titular. A chamada observada usa endereço/porta diferente da API atual; verificar compatibilidade e controlo legítimo antes de a dar por funcional. |

**Cobertura dos restantes canais internos — desenho ainda pendente:** D4 é a escolha
de autenticação nas APIs internas; a **opção A validada para 27/11** define a
separação abaixo. A configuração concreta continua pendente, não a escolha entre
mTLS universal e esta cobertura.

| Categoria / canais a inventariar | Exigência validada para a entrega | Prova/configuração pendente |
|--------------------------------|---------------------------------|-----------------------------|
| APIs internas da matriz D4, incluindo WS → projects | mTLS; identidade específica e autorização por serviço/operação | Cadeia, validade, identidade/finalidade, pares/rotas e controlos legítimos/indevidos. |
| Browser → nginx e nginx → frontend/api_gateway/ws_gateway | TLS com validação do servidor em cada ligação; JWT onde o fluxo existente exige | Certificados e confiança por salto; login/registo/anónimo mantêm as exceções públicas previstas. |
| nginx/img_storage → SeaweedFS, incluindo o futuro envio se confirmado | TLS com validação do servidor; credenciais próprias/privilégios mínimos onde aplicável; leitura pública por URL assinada preservada | Configuração S3/TLS, permissões por principal/prefixo e casos GET/HEAD/Range. Não exigir credencial de serviço no browser. |
| Serviços e backup → MongoDB | TLS com validação do servidor; credenciais próprias e privilégios mínimos por serviço/função | Verificar separadamente as três BD, a negação entre BD e o backup legítimo. |
| Produtores/consumidores → RabbitMQ | TLS com validação do servidor; credenciais próprias e permissões mínimas | Filas/exchange por serviço, consumidores Python/Node e ferramenta de imagem externa; não assumir suporte/configuração já existentes. |
| Ferramentas → generative-mock e restantes canais no âmbito | TLS com validação do servidor; autenticação/permissões onde aplicável | Fechar terminação/suporte nas versões usadas e preservar o fluxo legítimo. |

**mTLS universal (opção B) não é obrigatório nesta entrega.** Credenciais de
Mongo/S3/broker e permissões por BD/bucket/fila continuam necessárias; TLS não
substitui autorização. Não declarar que passar a HTTPS/AMQPS/TLS já configura
mTLS. Validar suporte e ponto de terminação por versão. Se faltar suporte nativo,
decidir e medir a solução de terminação antes de a contar como cumprida; não
aceitar plaintext nem `rejectUnauthorized: false` como exceção implícita. Lacunas
não podem ser apresentadas como implementação concluída. A escolha não aprova
coletivamente o restante contrato, os detalhes da PKI ou os requisitos completos.

Prova: S08–S09/S19–S21, F06–F07 e o fluxo assíncrono real.

### ACL-C1 — eliminação do projeto reservada ao dono

**Opção A escolhida individualmente:** só o dono elimina o projeto inteiro;
editores continuam a editar e remover media, leitores não podem eliminar projeto
nem media. Gestão/revogação de partilhas continua do dono. A limpeza dos projetos
quando a conta é eliminada mantém o seu fluxo de serviço autorizado, limitado ao
titular e à operação prevista; não abrir DELETE global a editores ou ao WS.

**Antes/depois explícito:** `DELETE /:user/:project` usa atualmente
`checkSharePermission` + `requireEditPermission`, pelo que uma partilha edit pode
passar esse controlo. Depois, o servidor terá de verificar dono efetivo para esta
operação administrativa. Não é uma regra herdada já demonstrada: RF53–RF55 definem
ver/editar e gestão de partilhas pelo proprietário, mas não fecham inequivocamente
a eliminação do projeto inteiro. A escolha é uma política explícita de acesso,
justificada como correção de segurança com mudança de comportamento intencional.
Documentar a compatibilidade com preservação funcional nas guidelines, sem esconder
a diferença ou prometer a sua aceitação académica como se fosse facto verificado.

A inspeção do frontend encontrou a chamada `useDeleteProject` em
`frontend/components/dashboard-sidebar/project-item.tsx`, alimentada pela lista
do próprio utilizador em `project-list.tsx`. Não foi demonstrada em execução uma
dependência da UI partilhada em eliminação por editor. Rever o caminho completo e
ocultar/desativar qualquer ação de eliminar projeto quando o ator não for dono,
com explicação coerente; a UI não substitui a recusa no servidor.

Testar **apenas com projetos descartáveis**: dono elimina; editor não elimina
mesmo por pedido HTTP direto e consegue editar/remover media; leitor não elimina
nenhum dos dois; remoção de conta preserva a limpeza legítima. Manter versão,
presença, quota e isolamento entre utilizadores nos controlos afetados. Não executar
testes destrutivos sobre os dois conjuntos de volumes preservados de Luís.
Prova: S01/S02/S05/S13/F04/F06. Testes de política/UI ainda não executados.

**D5 — Loopback para portas internas, mantendo uma rede.**
Reduz exposição à LAN e preserva depuração local; é a escolha comunicada. A alternativa de
não publicar as portas e separar redes reduz também alcance lateral. Foi adiada no documento
por custo de mapear dependências, não por irrelevância. O risco residual é explícito: um
processo local ou contentor da rede ainda pode alcançar serviços. É por isso que D1–D4 e as
credenciais dos dados continuam necessários. Prova S18, de dentro e de fora das fronteiras;
porta inacessível é controlo de rede, não uma resposta de autorização 401/403.

**D6.1 — JWT obrigatório na ligação Socket.IO, validado individualmente.**
A escolha recusa ligações sem identidade verificada e simplifica o estado de acesso.
A alternativa de permitir sockets sem JWT mas sem salas protegidas foi afastada pelo
utilizador. Isso não elimina o perfil anónimo: ele já recebe JWT de sessão. Validar a
ligação continua insuficiente para autorizar uma sala arbitrária; D6.2 B acrescenta
a consulta à projects por entrada.

O utilizador validou posteriormente **terminar a ligação quando o JWT expirar**.
O frontend deve tratar explicitamente a reconexão, apresentar JWT válido e pedir
nova autorização para cada sala. Não presumir reconexão automática depois de uma
desconexão iniciada pelo servidor. Renovação e transição continuam por desenhar,
preservando identidade e projetos das sessões anónimas. Não há medição que permita
afirmar que a expiração durante uma ligação ativa é rara.

**D7 — owner opcional, único e coerente, validado individualmente.**
O utilizador escolheu detetar e recusar contradições, em vez de ignorar o parâmetro.
O caminho identifica o dono; a query não pode substituí-lo por outro. Sem `owner`, o
pedido segue o caminho normal. Com `owner`, verificar valor único/coincidente e
recusar multivalores ou interpretações ambíguas. A projects mantém a decisão final de
posse/partilha, mesmo em chamadas diretas. Os testes G02–G04 precisam de asserções
completas e controlos de partilha legítima; códigos de erro/normalização são detalhes
a especificar sem alterar esta regra.

**D6.2 B — Consultar projects em cada entrada, escolhida individualmente.**
O utilizador prefere confirmar a autorização atual na autoridade do domínio sem
introduzir um tipo adicional de token: assinatura, distribuição de chaves, TTL,
renovação e invalidação de bilhetes. O assistente confirma esta combinação como
proporcional ao âmbito/prazo, com **confiança média**. A redução de complexidade é
uma inferência técnica; não há benchmark que demonstre a necessidade de evitar
consultas por entrada nem esforço medido de ambas as alternativas.

A alternativa de bilhete com verificação local fica adiada. Poderá ser reconsiderada
se a latência/carga ou um requisito de disponibilidade justificar esse custo. Essa
alternativa também precisaria de impedir nova entrada com um bilhete ainda válido
depois de revogada a permissão. A decisão não altera RS256 da identidade interna
de D3, mTLS de D4 ou JWT obrigatório na ligação de D6.1.

O custo aceite é depender de projects para novos joins. Se estiver indisponível,
recusar temporariamente e permitir nova tentativa; não converter erro/timeout em
autorização ou fingir que é uma negação definitiva de posse. mTLS direto e timeout
total inicial de 1 s estão validados em WS-C1/WS-C2. Dados devolvidos e coordenação
da corrida autorizar→join continuam propostos para revisão.
Prova: S04/S05/S10/S11/S21 e casos de falha/dependência indisponível.

**D6.3 A — Remoção ativa da sala quando termina a autorização efetiva.**
Consultar em cada join não controla a permanência. Quando a permissão efetiva
deixar de existir, retirar o acesso à sala afetada; não desligar desnecessariamente
outras salas válidas. A alternativa de só verificar no próximo join foi afastada
na escolha B/A: deixa sessões já ligadas receberem dados indefinidamente.

O utilizador validou **revalidação periódica**, inicialmente a cada **1 s**, sujeita
a medição de carga e latência. Agrupar consultas por projeto, mas autorizar cada
membro e o seu contexto de acesso individualmente. O agrupamento reduz pedidos
HTTP; o processamento continua a crescer com os membros/contextos avaliados.

O **critério de aceitação é corte ≤5 s**, com **meta ≤2 s**, após revogação confirmada,
nos cenários acordados. São critérios escolhidos individualmente, ainda sem prova
experimental de cumprimento. A autorização local dura no máximo 5 s desde o
**início da consulta que recebeu resposta positiva**, terminando antes se expirar
o JWT ou a permissão efetiva. O atraso da resposta não dá mais 5 s a partir da
receção; falhas não prolongam a autorização.

Respostas atrasadas ou fora de ordem não podem restaurar acesso indevido. Uma
negação explícita da autorização efetiva retira imediatamente o acesso à sala
afetada, preservando outras autorizações válidas. Indisponibilidade nunca permite
novas entradas. Na falha transitória de revalidação, membros existentes só mantêm
acesso até ao limite já definido; findo esse limite, retirar o acesso não revalidado.
Não se afirma que esta política e a remoção na primeira falha ofereçam segurança
igual: têm comportamentos diferentes durante a janela de falha e não foram
comparadas experimentalmente.

Eventos de revogação ficam como **evolução**, a reconsiderar se as consultas criarem
carga relevante ou não cumprirem os critérios. Um evento isolado não garante o
corte. WS-C1 A/WS-C2 A validam mTLS direto, timeout total inicial 1 s, até 50
avaliações por pedido, concorrência limitada e agendamento justo. Restante contrato,
ordenação/gerações, corridas com join e limites globais precisam de revisão e prova.

Autorizar deve considerar vias ainda válidas: propriedade, outro link válido ou
outro acesso reconhecido pelo modelo. Revogar um link não é, por si só, autorização
para remover qualquer socket daquele utilizador; também não se deve descobrir ou
conceder acesso por um link secreto que ele nunca apresentou. Como representar e
provar essas vias é um detalhe de permanência por fechar. Prova: S12/S13/S21/F04,
com revogação durante join, consultas lentas/perdidas/fora de ordem, expiração de
JWT/permissão, falhas de revalidação, vários membros por projeto e pelo menos um
caso de acesso alternativo. Os ensaios ainda não foram executados para o novo mecanismo.

A [proposta de contrato WS](architecture/fase2-contrato-websocket.md) detalha a
representação das vias, resposta individual por lote, geração/sequência e prazo,
tratamento de corridas e casos de prova. **WS-C1 A** (mTLS direto com delegação) e
**WS-C2 A** (timeout total inicial 1 s/50 avaliações por pedido, concorrência limitada
e agendamento justo) estão validadas individualmente, sem capacidade demonstrada.
O restante contrato permanece proposta para revisão.

**D8 — Expiração de links de partilha.**
Reduz exposição temporal de um link, preservando o conceito de partilha por link. As alternativas
são manter a revogação manual ou mudar para convites/lista de membros. Os convites seriam uma
alteração funcional maior, mas um seletor novo de validade e a expiração de links existentes
**também mudam comportamento observável**. Não os chamar automaticamente refactoring puro:
justificar como objeto da melhoria de segurança e rever à luz das guidelines e de RNF52
(persistência até revogação). A política de migração e a validade por omissão continuam abertas.
A expiração de sharedLinks e a validade de um URL S3 já emitido são contratos diferentes.
Prova S13 e F04; a aprovação de D8 não escolhe silenciosamente a migração.

**D9 — Abranger users e subscriptions.**
Evita deixar operações de perfil/pagamento mock contornarem as permissões dos projetos.
A alternativa é limitar o RNF a projetos/storage e declarar esses riscos; é menor, mas não
corresponde ao âmbito alargado descrito no documento. A inclusão exige testes reais de
subscriptions com dados sintéticos, porque um 500 de serviço ausente nada prova. Registo,
login e perfil anónimo precisam de exceções públicas definidas: «tudo exige identidade prévia»
impediria criar uma conta. Prova S14–S17 e F05, com promoção premium pelo percurso legítimo.
Atomicidade da quota é uma questão distinta; não a dar como corrigida apenas por autenticar.

**D11 — Verificação do token de upload sem repetir todo o cálculo de domínio.**
A emissão autoriza o recurso; o porteiro valida uma capacidade curta e delimitada. A alternativa
é consultar posse/partilha atual em cada estágio. Evitar repetição pode reduzir custo, mas
exige decidir o que acontece se a permissão for revogada entre emissão e PUT/confirm.

«Não foi usado» seguido de «marcar usado» não chega: dois PUT simultâneos podem passar na mesma
janela. A reclamação tem de ser atómica, com estados de tentativa, falha e confirmação/retry.
Um URL S3 pré-assinado é reutilizável até expirar; o uso único tem de ser imposto pela aplicação.
Confirmar precisa de ser idempotente, e nenhum token deve autorizar outra chave/projeto/tamanho.
Prova S22–S24/U21/U23/U26. O custo é uma máquina de estados, não só verificar um booleano.

### Estado das decisões de segurança e detalhes ainda em aberto

| Ponto | Alternativas e recomendação fundamentada | Prova e resposta preparada para a defesa |
|-------|-------------------------------------------|-----------------------------------------|
| D7 owner — validada | Ausente permitido; presente exige valor único igual ao dono no caminho. Ignorar silenciosamente foi afastado pelo utilizador. | G02–G04, ausência, coincidência, contradição e multivalor; projects autoriza sempre. |
| D10 medição | Host apenas ou host + contentor não confiável; recomenda-se ambos para o âmbito D1. | S01–S24; separar bloqueio de rede, TLS, identidade e domínio; não contar 500 como proteção. |
| D6.1 — validada | JWT válido obrigatório; ao expirar, terminar ligação; frontend reconecta explicitamente com JWT válido e nova autorização por sala. | Testar perfis registado/anónimo, ausência de reconexão automática e preservação de identidade/projetos; renovação/transição ainda em aberto. |
| D6.2 B — escolhida | Consultar projects por entrada, recusar temporariamente em indisponibilidade e permitir nova tentativa. | WS-C1 A/WS-C2 A validados: mTLS direto/timeout total inicial 1 s; S04/S10/S11/S21 e restante contrato/corridas por rever. Bilhetes só se evidência futura os justificar. |
| D6.3 A — validada | Revalidar inicialmente a cada 1 s, em lotes por projeto mas individual por contexto. Local até 5 s desde início da consulta positiva, limitado por JWT/permissão; falhas não renovam; negação efetiva retira já. | S12/S13/S21/F04; critério ≤5 s/meta ≤2 s escolhidos, ainda por ensaiar; testar carga proporcional aos membros, respostas obsoletas e corridas. Eventos adiados. |
| Sessões/assinatura | HS256 utilizador e RS256 interno já validados; fechar transição de sessões antes de renovar o segredo. | Assinatura errada/algoritmo não permitido, exp/aud/sub, rotação, sessões anónimas e preservação dos seus projetos. |
| TTL | Curto reduz janela de replay; demasiado curto quebra uploads/relógios. | Medir duração máxima, tolerância de relógio e renovação; não inventar TTL «acordado». |
| Links legados | Manter sem expiry, exigir renovação ou aplicar prazo de migração. | F04/S13 e aviso ao utilizador; decidir antes de mexer no schema. |

### Ideia 2 — porquê nginx/S3 e o que ainda precisa de prova

**U1 — Envio pelo nginx para S3, em vez de atravessar os três Node.**
Retira o corpo grande do percurso dos serviços que já têm responsabilidades de autenticação
e domínio. É a preferência assinalada, não uma implementação aprovada. A alternativa de
streaming com um spool controlado na projects tem vantagem de manter o contrato multipart e
validar antes de publicar; a alternativa de URL S3 entregue ao cliente é mais simples, mas
exige CORS/origens apropriadas e um modelo de capacidade temporária explícito.

O custo de nginx/S3 é real: novo protocolo frontend/API, auth_request, coordenação de estado,
URLs internos, limpeza e testes de interrupção. O endereço continuar a ter `/api-gateway/`
não preserva o contrato quando POST multipart passa a pedido JSON + PUT + confirmação.
Retirar a rota antiga ou manter um adaptador é uma decisão de compatibilidade em aberto.
Manter a rota antiga como bypass inseguro também não é aceitável. Prova U01–U13/U17–U26 e F02–F04.

**U2 — Validar duas vezes, só confiar na validação final do servidor.**
Os metadados do browser evitam transferências honestamente inválidas; podem ser falsificados.
O HEAD/ffprobe final tem de verificar o objeto efetivo. O vídeo pending não pode aparecer
em listagens, previews, Apply ou URLs normais antes de pronto; criar o registo no stage src
não o isola por si. Pode usar-se coleção/área de staging ou regras explícitas de visibilidade:
a escolha ainda precisa de ser fechada. Aplicar quota como pré-condição nova de upload
exige justificação, porque hoje a operação é cobrada no Apply. Prova S23–S24/U18/U21–U24.

**U3 — Hash depois da resposta.**
Pode reduzir o tempo até ready, mas adia uma leitura integral que continua a gastar CPU,
rede e memória. Medir `t_ready`, `t_hash` e `max(t_ready,t_hash)` separadamente, incluindo
concorrência. A alternativa de hash síncrono em streaming é mais simples para a consistência,
mas mantém trabalho no tempo de aceitação. Hash do cliente confirmado por checksum no storage
é outra opção dependente do suporte real do SeaweedFS. Um checksum não é universalmente uma
opção «mais forte»: confiança, integridade e custo têm de ser avaliados no mesmo modelo.

Enquanto faltar hash, desativar leitura **e escrita** de cache ou garantir isolamento por
media; caso contrário dois originais podem usar a mesma chave vazia. Definir estado/retoma
após crash e confirmação idempotente. O ETag não substitui automaticamente SHA-256, sobretudo
com multipart. Prova U14–U16/U21. Não declarar ganho total só por mover trabalho para depois.

**U4 — Token opaco, S3 atrás do nginx e cleanup.**
Evita entregar ao cliente o destino de escrita e permite controlo comum de acesso; opacidade
não substitui autenticação, expiração, ligação à chave e uso único. O desenho precisa de
comprovar auth_request na imagem de nginx, resolver DNS, Host de assinatura, limites e
propagação correta dos códigos de erro. O destino de proxy/probe é gerado pelo servidor;
não aceitar arbitrariamente um URL do cliente.

Manter leitura assinada em `/s3/` preserva o produto. Restringir métodos pode reduzir superfície,
mas testar GET, HEAD, Range, URL expirado e o percurso de upload separado. Ocultar bucket/chave
não é a garantia central: URLs pré-assinados entregues ao cliente também podem ser um desenho
válido. O que importa é a autorização limitada e a resistência a replay. Prova S22–S24/U26.

A limpeza de pending deve sobreviver a crash, ter prazo e não apagar ready nem um envio ainda
válido. Multipart/incomplete uploads e objetos completos não confirmados são resíduos
possivelmente diferentes no storage. Medir ambos, bytes/idade e tempo até remoção. Prova U21–U22.

**Hipóteses técnicas que não podem aparecer como garantias.**
O ffprobe pode ler mais do que moov/início; tamanho declarado/assinado pode não ser imposto pelo
SeaweedFS; um PUT interrompido pode ter comportamento específico; o hash posterior pode
saturar a mesma rede. HEAD deteta oversize no fim e não limita bytes recebidos durante o PUT.
O global client_max_body_size também não exprime todos os perfis. São spikes de compatibilidade
ou ensaios sobre o storage/configuração, sem começar já o refactoring do produto.

### Perguntas de defesa e relatório — respostas e limites

| Pergunta | Resposta sustentada | O que ainda não podemos afirmar |
|----------|----------------------|--------------------------------|
| Porquê estas duas áreas e não elasticidade/modularidade? | Há efeitos de autorização observados e memória alta em uploads; medidas e stakeholders claros. | Que a implementação escolhida é a mais barata ou cumpre metas antes de medir. |
| Porque não basta o JWT do gateway? | owner e os acessos diretos demonstram que verificar o token não equivale a autorizar o recurso. | Que mTLS sozinho determina dono/permissão. |
| Porquê consulta em vez de bilhete WS? | Dispensa gestão de um token adicional e consulta a autorização atual na projects. A proporcionalidade é uma inferência, com confiança média. | Menor latência/custo medido, independência da projects para joins ou remoção automática de membros já ligados. |
| Porque retirar ativamente da sala? | A permissão pode desaparecer depois do join. A saída da sala afetada preserva outras salas autorizadas. Critério ≤5 s/meta ≤2 s validados individualmente. | Cumprimento experimental ou aprovação dos quatro; que um evento isolado garante prazo ou que revogar um link invalida todas as outras vias. |
| Porquê revalidar a cada 1 s e agrupar por projeto? | Intervalo inicial escolhido, sujeito a carga/latência. O lote agrupa HTTP; cada membro/contexto continua autorizado individualmente. | Carga constante com mais membros ou que os critérios serão cumpridos antes de ensaiar. |
| Porque não retirar na primeira falha? | A política validada admite apenas o prazo local já fixado; falhas não renovam e negação efetiva retira já. | Segurança igual entre as alternativas durante falhas; essa comparação não foi demonstrada. |
| O que sucede ao expirar o JWT? | Termina a ligação; o frontend trata reconexão explícita com JWT válido e nova autorização por sala, preservando identidade/projetos anónimos na renovação/transição. | Reconexão automática após corte pelo servidor, raridade da expiração ativa ou um mecanismo de renovação já fechado. |
| Porque nginx/S3 em vez de spool? | Retira Node do envio grande; spool preserva API e pode ser mais simples. | Que o contrato se mantém só por usar a mesma origem ou que todos os buffers ficam a zero. |
| Porque hash assíncrono? | Pode melhorar tempo até aceitação; custo completo continua medido. | Melhoria total sem mostrar t_hash, recuperação e isolamento da cache. |
| Quais os números atuais? | Tabelas B14/B16 e bruto com ambiente; 500 MiB B16 teve 6,7–8,0 s pós-envio cliente e gateway até 2049,6 MiB de RSS. | Que tempos Intel e M4 são comparáveis ou que 10/13 e 17/22 são contagens finais validadas. |
| Porque mínimos/metas diferentes? | 64/32 MiB são orçamentos propostos; 3/1 s vêm do requisito no cenário correspondente. Segurança exige zero no corpus. | Que esses números foram impostos pelos docentes ou aprovados por toda a equipa. |
| O que falta antes de programar? | Decisões abertas, requisitos/métricas aprovados, baseline BF reproduzível e guardas preenchidas. | Que pedir análise dos documentos autoriza resolver todas as decisões em nome da equipa. |

### Referências técnicas da revisão

Consultadas em 16/11/2026; não substituem teste nas versões instaladas:
[nginx auth_request](https://nginx.org/en/docs/http/ngx_http_auth_request_module.html),
[proxy/buffering](https://nginx.org/en/docs/http/ngx_http_proxy_module.html),
[FFmpeg HTTP](https://ffmpeg.org/ffmpeg-protocols.html#http),
[Node TLS](https://nodejs.org/api/tls.html),
[nginx TLS para upstream](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_ssl_certificate),
[Socket.IO rooms](https://socket.io/docs/v4/rooms/),
[AWS S3 URLs reutilizáveis](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).
As propriedades genéricas do S3 não certificam o SeaweedFS 4.47.

Revisão e redação apoiadas por Codex/Inception. As medições de origem foram fornecidas nos
artefactos de 16/11; nesta revisão foram auditadas e extraídas, não novamente executadas.

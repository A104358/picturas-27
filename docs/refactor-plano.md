# Fase 2 — Plano de refatoração (fase 0)

[Índice da documentação](README.md) · **Equipa: PL2-G4** · Preparado a 21/11/2026

Este documento é a **única fonte de trabalho para implementar** os dois RNF. Junta,
por ordem de execução, tudo o que as decisões já tomadas exigem. As decisões não se
repetem aqui: cada passo indica a sua origem (ID da decisão) e o documento onde está o
detalhe. Se um passo e a decisão de origem divergirem, vale a decisão, e o plano é
corrigido.

| RNF | Métricas que provam a melhoria | Guardas |
|-----|-------------------------------|---------|
| 1. Segurança — autorização ponta a ponta (QC-06) | S01, S02, S03, S04, S12, S16, S17, S18 | S05, S21 |
| 2. Eficiência — recursos no upload (QC-05) | U01, U20, U19, U18, U04, U08 | U09, U25, U15, U17, U10 |

Fontes das decisões: [ideias 1 e 2](fase2-ideias-1-e-2.md),
[contrato WS](architecture/fase2-contrato-websocket.md),
[sessões e identidade](architecture/fase2-sessoes-identidade-partilhas-ws.md),
[fila WS e revogação PKI](architecture/fase2-fila-ws-e-revogacao.md),
[critérios operacionais](architecture/fase2-criterios-operacionais-seguranca.md),
[recuperação anónima](architecture/fase2-recuperacao-anonima.md),
[inventário de sessões](architecture/fase2-inventario-sessoes.md),
[decisões de upload](architecture/fase2-upload-decisoes-pendentes.md),
[ciclo de vida do upload](architecture/fase2-upload-ciclo-vida.md),
[métricas](metricas.md) e [plano de medição](planoMedicao.md).

---

## 1. Regras de execução

1. **Blocos pela ordem do §3**, salvo quando as dependências de um bloco posterior já
   estão feitas. Cada sessão começa pelo [documento de passagem](refactor-handoff.md),
   retoma a partir do "próximo passo exato" e lê só os documentos de origem do bloco,
   não o histórico inteiro. Ao parar, atualiza esse documento.
2. **Trabalha-se só no branch `fase2-refactor`** e **nunca se abre um pull request para
   o `main` do repositório upstream (prcsousa)** (D-12). Cada bloco termina num estado
   que arranca e passa as suas verificações. Os commits são feitos pelas pessoas, não
   pelos agentes.
3. **Verificação depois de cada bloco**, numa stack isolada do `med.py` com nome
   próprio (`MED_COMPOSE_PROJECT=picturas-nfr-exp`; o `med.py` só aceita
   `picturas-nfr[-sufixo]`). O projeto `picturas-nfr` fica reservado à MF oficial. Para
   desenvolver usa-se outro projeto Compose (por exemplo `picturas-dev`), onde o `med.py`
   não corre:
   - reconstruir os serviços alterados;
   - correr `med.py run --campaign EXP --quick` nas métricas do bloco e na S05;
   - correr os testes de conformidade do bloco (§5) e a regressão existente (F01–F03).
4. **A S05 nunca pode descer de 100%.** Uma melhoria que parta um fluxo legítimo não
   conta: corrige-se antes de passar ao bloco seguinte.
5. **Ferramenta de medição congelada.** O `med.py`, o `medlib/`, os critérios e os casos
   não se alteram, exceto o que §6 autoriza, sempre com `med.py freeze` e um registo.
6. **Sem segredos no Git, nas imagens nem nos logs.** As chaves, certificados e
   palavras-passe ficam num diretório fora do repositório, indicado por variável de
   ambiente (§3, bloco B1). Os logs e os resultados de testes também não guardam JWT,
   URLs assinados, tokens de upload nem `shareId`s.
7. **Proibido:** `rejectUnauthorized: false`; aceitar plaintext como recurso; aceitar
   qualquer certificado da CA sem verificar a identidade do serviço; tratar 5xx ou
   timeout como recusa; um proxy de terminação TLS que deixe um salto de rede sem a
   proteção exigida; nos ensaios, alterar o relógio real do sistema ou usar perfis e
   volumes de dados reais. Uma lacuna que não se consiga fechar fica **declarada**, nunca
   escondida (fontes: D4, opção A, PKI-C5 A).
8. **Reduzir o âmbito só por decisão explícita e registada** (§7), nunca em silêncio.

## 2. Estado de partida

- BF oficial: `evaluation/results/BF-20261121T013224Z` (aplicação igual a `0523102`).
- Não há clientes nem dados reais: a entrega parte de um reset geral, sem migrações
  (D-15).
- Todas as decisões de arquitetura estão escolhidas: D1–D11, D6.1–D6.3, WS-C1–C5,
  PKI-C1–C5, OPS-C1, SESS-C1, JWT-C1, LINK-C1, ACL-C1 e UP-C1–C9.
- Fragilidades observadas na BF que este plano corrige:
  - S01: 12 de 15 casos admitidos;
  - S02: 9 de 10;
  - S03: 4 de 4;
  - S04: 5 de 5;
  - S12: sem corte;
  - S16: todos os casos alcançáveis;
  - S17: 14 de 15;
  - S18: 12 portas;
  - U01: gateway com +1976 MiB e morto 12 vezes em 20 uploads de 500 MiB;
  - U20: 0/3;
  - U18: 15/21;
  - U19: +966 MiB antes do 401;
  - U04: SeaweedFS +585 MiB.

---

## 3. Blocos de implementação (ordem, dependências e critérios)

A ordem segue as dependências técnicas:
1. Primeiro a PKI e os segredos, de que tudo depende.
2. Depois a autenticação entre serviços e a identidade.
3. Depois os canais de dados.
4. Por fim, o upload e o WebSocket, que assentam nessas fundações.

Os blocos operacionais (PKI-C2/C3/C4 e OPS-C1) vêm no fim, porque operam sobre o
sistema já protegido.

### B0 — Preparação e spikes de compatibilidade (sem alterar o produto)

**Objetivo:** confirmar as hipóteses técnicas de que o desenho depende, antes de
construir sobre elas. Cada spike tem um resultado (suportado / não suportado / com
limitações), registado em `docs/refactor-spikes.md`. Se um spike falhar, o bloco
afetado é revisto antes de começar.

| # | Hipótese a confirmar | Bloco afetado | Origem |
|---|---------------------|---------------|--------|
| SP-01 | A imagem `nginx` usada tem `auth_request`, `proxy_request_buffering off` e `proxy_ssl_verify` funcionais | B5, B6, B7 | UP-C9, U4 |
| SP-02 | O SeaweedFS 4.47 com HTTPS no S3 e no filer, credenciais por principal e permissões por bucket/prefixo | B2 | opção A, PKI-C5 |
| SP-03 | O SeaweedFS respeita o tamanho assinado (`ContentLength`), um PUT interrompido não deixa objeto visível, o comportamento com chunked é conhecido e o CopyObject cria uma cópia imutável. **Medir também quanto demora o CopyObject de 500 MiB**, porque esse tempo entra na U09 no adaptador (D-14) | B6, B7 | ideia 2 «a confirmar», UP-C6, D-14 |
| SP-04 | O SigV4 com o `Host` interno (`seaweedfs:9000`) através do nginx | B7 | ideia 2 |
| SP-05 | O `ffprobe` por URL HTTPS interno, com `moov` no início e no fim, a 500 MiB: bytes lidos, tempo e limites de I/O impostos | B6 | UP-C8 A, U13 |
| SP-06 | O MongoDB 4.4 com `requireTLS`, utilizadores por serviço e privilégios mínimos; `mongodump` com TLS | B2 | opção A, PKI-C5 |
| SP-07 | O RabbitMQ com TLS e utilizadores/permissões por fila; clientes `pika` (Tools) e `amqplib` (Node) com verificação do servidor | B2 | opção A |
| SP-08 | A imagem derivada do watermark (patch ao `message_queue_setup.py`) liga por AMQPS com a CA da instalação e processa um pedido | B2 | PKI-C5, D-07 |
| SP-09 | O Next.js (frontend) a servir HTTPS ao nginx, com servidor próprio | B5 | PKI-C5 |
| SP-10 | O Flask (generative-mock) e o `requests` (expand_ai) com mTLS | B5 | PKI-C5 A |
| SP-11 | Os componentes internos do SeaweedFS (master/volume/filer, gRPC) com TLS: inventário e suporte | B2 | PKI-C5 |

**Também em B0:**
- criar o branch;
- **fixar as imagens sem versão às da BF** (comparabilidade BF/MF):
  - `nginx:latest` → o digest da BF (`nginx@sha256:84f7876d21d1…`);
  - a base do watermark (`:latest`) → o digest da BF;
  - os `FROM node` sem tag → a versão que a BF construiu, registada no manifesto da
    BF.

  Uma imagem que mude entre a BF e a MF altera as condições da medição;
- criar `tests/conformance/` para os testes de §5;
- confirmar que a regressão existente corre (`Tools/video` pytest, testes Node) e
  registar o ponto de partida (F01).

### B1 — PKI e segredos fora do repositório

**Origem:** D4, PKI-C1 A, D3, SESS-C1 A (passo 3), S19, guardas Git/build.

1. **Diretório de segredos fora do checkout**, em `PICTURAS_SECRETS_DIR` (variável de
   ambiente). O `docker-compose.yaml` monta daí só o que cada serviço precisa, em modo
   de leitura. Nenhum segredo fica em `.env` versionado nem dentro das imagens.
2. **Script `ops/pki.sh`**, que faz:
   - uma CA por instalação, com 365 dias;
   - uma chave e um certificado por serviço, com 30 dias, SAN igual ao nome Docker do
     serviço e EKU de servidor e/ou de cliente conforme o papel;
   - recusa de emitir para lá da validade da CA e de aceitar certificados expirados como
     atalho;
   - sem daemon de renovação automática: o administrador corre o procedimento;
   - renovação quando faltam 7 dias;
   - verificação da validade antes do arranque (`check`);
   - registo público de emissor, serial, SAN, EKU, validade e fingerprint, sem chaves.

   A chave da CA fica fora dos contentores.
3. **Script `ops/secrets.sh init`**, que gera:
   - o novo segredo HS256 (≥256 bits). Não há clientes reais e a entrega parte de um
     reset geral (D-15): cada instalação começa do zero com o seu segredo, sem sessões a
     preservar nem transição. O segredo antigo (versionado) nunca é aceite (D3,
     SESS-C1 A);
   - o par RS256 do gateway (a chave privada só para o gateway, a pública para os
     verificadores);
   - as palavras-passe Mongo por serviço e de backup;
   - os utilizadores RabbitMQ por principal;
   - as credenciais S3 por principal.
4. **`.gitignore` e `.dockerignore` defensivos** nos 7 contextos Node/frontend e nos
   Python. Hoje os serviços leem certificados do checkout (`certs/`); a passagem para os
   mounts externos não pode partir o arranque. Inclui as chaves `certs/selfsigned.key`
   (montada no nginx) e `frontend/certs/selfsigned.key`, ambas versionadas. As chaves antigas já versionadas (6) e os segredos escritos no Compose
   (`admin123`, `user/password`, `lisan_al_gaib`…) saem dos ficheiros versionados.

   Nota: retirar do Git não apaga o histórico. Isso fica declarado como limitação S19
   e não é reescrito.
5. **Teste com marcadores sintéticos:** um caminho ignorado, ausente do contexto de
   build e ausente das camadas da imagem (S19).

**Critério de aceitação:**
- `ops/pki.sh check` passa;
- `git grep` não encontra nenhum segredo atual;
- nenhuma imagem construída contém os marcadores;
- a stack arranca com os segredos montados.

### B2 — Canais de dados e broker: credenciais, privilégio mínimo e TLS

**Origem:** opção A, D1, D9, PKI-C5 A (matriz), S16, S17.

1. **MongoDB (3 instâncias + `mongo-backup`):**
   - autenticação obrigatória e um utilizador por serviço, só com acesso à sua BD
     (sem `listDatabases` nem acesso a outras BD);
   - um utilizador de backup só de leitura;
   - `requireTLS` com o certificado do servidor e clientes a validar a CA;
   - URIs construídos a partir dos segredos montados.
   - um utilizador administrativo por instância, com credenciais fora do repositório,
     usado só pela operação (`ops/`) e pelas verificações do `med.py` na MF;
2. **RabbitMQ:**
   - um utilizador por principal (`projects`, `ws_gateway` e cada um dos 16 workers);
   - permissões só nas filas e exchange de cada um (`configure/write/read`); o exchange
     `picturas` passa de `direct` a `topic`, com as mesmas routing keys, e cada principal
     recebe permissões de tópico só nas suas routing keys (`set_topic_permissions`); os
     clientes declaram o exchange de forma passiva (D-18);
   - o utilizador `user/password` deixa de existir;
   - o `definitions.json` deixa de levar palavras-passe (passam a ser criadas no init a
     partir dos segredos);
   - a API de gestão fica só para o administrador, com TLS ou desativada; nenhum listener
     plaintext funcional fica como desvio (o mesmo para a administração do SeaweedFS);
   - AMQPS com verificação do servidor em `Tools/utils/rabbit_mq.py` (comum aos workers
     Python), em `projects/utils/rabbit_mq.js` e no `ws_gateway`.
   - Os consumidores sobrevivem ao reinício do broker (regra do AGENTS.md).
3. **SeaweedFS:**
   - credenciais por principal: o `img_storage` lê e escreve só no bucket da
     aplicação, sem criar nem apagar buckets;
   - credencial de administrador fora do repositório;
   - HTTPS no S3 (9000) e no filer (8888), e TLS nos componentes internos conforme
     SP-11;
   - o master, o volume e o filer escutam **só em loopback** (estão no mesmo processo
     `weed server`); da rede ficam só o S3 (9000) e o gRPC do S3 (19000, mTLS). O TLS e
     o mTLS internos mantêm-se como defesa em profundidade (D-19);
   - **retirar a rota `/s3-console/` do nginx**, que hoje publica o filer sem
     autenticação e dá acesso a todos os ficheiros (encontrado no SP-11);
   - o nginx `/s3/` com `limit_except GET HEAD` e `proxy_ssl_verify on`.
4. **Volumes partilhados** (`image_data`, `whisper_models`): são acesso a
   ficheiros, não canais TLS. Montar cada um só nos serviços que o usam, em leitura
   quando basta, e nunca guardar segredos neles (PKI-C5, nota sobre volumes).
5. **Watermark (D-07):** a imagem externa usa o `pika` 1.3.2, que suporta TLS, mas o seu
   `message_queue_setup.py` liga sem `ssl_options`. Cria-se uma **imagem derivada**
   (`Tools/watermark/Dockerfile` com `FROM prcsousa/picturas-watermark-tool-ms` e um
   patch pequeno que lê o TLS e a CA de variáveis de ambiente), com credencial própria
   e permissões mínimas. O SP-08 passa a ser a verificação desse patch.

6. **`med.py` com TLS nos canais de dados (D-13):** antes de verificar este bloco,
   acrescentar ao `med.py` as opções de TLS do §6, ponto 4, com `freeze` e registo.

**Critério de aceitação:**
- S16 = 0 e S17 = 0 em `--quick`, com os ataques a passar pelo TLS (medem credenciais e
  privilégios, não o transporte);
- controlos legítimos a 100%, incluindo o backup e o restauro de uma fixture;
- `/s3/` público: GET, HEAD e Range com URL assinado válido funcionam; URL expirado,
  PUT, POST e DELETE são recusados (ideia 2, U4);
- `/s3-console/` deixou de existir; o filer, o master e o volume não respondem a partir
  da rede Docker;
- um worker não consegue publicar na routing key de outro (403);
- a pipeline de imagem e de vídeo funciona (S05, F02).

### B3 — Superfície exposta e supervisão

**Origem:** D5, S18, ideia 7 (supervisão), F08.

1. **Portas (D-05):** retirar do `docker-compose.yaml` todas as portas publicadas exceto
   a do nginx (8080), o que cumpre o alvo da S18. A administração faz-se por
   `docker exec`. A rede Docker `elk` mantém-se única (D5); a proteção contra quem está
   na rede vem da identidade, do mTLS e das credenciais, não das portas.
2. **Supervisão (D-04):** no `docker-compose.yaml`, os serviços Node (`api_gateway`,
   `projects`, `users`, `subscriptions`, `img_storage`, `ws_gateway`) arrancam com `node`,
   com `restart` e `healthcheck`, para que um processo morto seja reiniciado (F08: retoma
   ≤30 s, alvo ≤10 s). O `nodemon` e os bind-mounts ficam num override de
   desenvolvimento (`docker-compose.dev.yaml`), e o `AGENTS.md` é atualizado.

3. **Limites de memória explícitos** (`mem_limit`) nos serviços Node do
   `docker-compose.yaml` (ideia 2). Os valores são registados; o `med.py` aplica os seus
   próprios limites de medição, iguais na BF e na MF.

**Critério de aceitação:** S18 cumpre o alvo (0 portas internas publicadas) e F08 é
medido.

### B4 — Identidade de utilizador e identidade interna (autorização HTTP)

**Origem:** D1, D2, D3, JWT-C1 A, D7, D9, ACL-C1 A, LINK-C1 A, S01, S02, S06, S07, S13, S14, S15.

0. **Matriz de rotas, antes de mudar código** (D1: "enumerar interfaces, identidades e
   ações"; D2: "matriz por rota/verbo"). Em `docs/refactor-matriz-rotas.md`, uma linha
   por rota e verbo de `api_gateway`, `projects`, `users`, `subscriptions` e
   `img_storage`, com:
   - quem pode chamar (dono, partilha read/edit, serviço da matriz D4, público);
   - a regra aplicada e quem a aplica (gateway ou serviço);
   - o comportamento atual e o novo;
   - o teste que o prova.

   Nenhuma rota fica sem linha. É daqui que saem os controlos legítimos (S05, F04) e as
   recusas (S01, S02, S14, S15), para que nenhuma funcionalidade se perca sem darmos por
   isso (por exemplo, os presets e a sua partilha).
1. **JWT de utilizador:**
   - HS256 com o segredo novo;
   - `typ`, `iss` e `aud` próprios da instalação;
   - algoritmo fixo e verificação de `exp` sem tolerância;
   - `sub` normalizado para `_id`;
   - 7 dias absolutos, sem refresh.

   Emitido pelo `users`; verificado pelo `api_gateway` e pelo `ws_gateway`. O
   `projects` não recebe o segredo HS256.
2. **Identidade interna RS256 (gateway → destino):**
   - `exp = min(iat+30 s, exp da sessão)`;
   - `aud` = serviço destino;
   - `typ` interno;
   - contexto assinado: método, percurso interno canónico, `share` e `requestId`;
   - `sub` derivado da sessão verificada, nunca do corpo nem de um cabeçalho externo;
   - o destino valida a associação ao pedido recebido e ao peer mTLS, e rejeita o token
     noutro serviço, rota ou método;
   - `kid` resolvido num mapa local.

   Enviada num cabeçalho dedicado. Os cabeçalhos internos que venham do browser são
   removidos no gateway.

   - Um token com `aud=projects` nunca é reenviado a `users` nem ao `img_storage`. Nas
     chamadas seguintes, a `projects` delega a identidade pelo seu canal mTLS, limitada
     aos pares e operações da matriz D4 (JWT-C1 A).
   - Os 30 s são de admissão: um job já admitido não é abortado nem duplicado por a
     identidade expirar (JWT-C1 A).
3. **Gateway (`apiGateway`):**
   - `checkToken` antes de qualquer leitura do corpo;
   - verificação barata mantida: sem `share`, o utilizador do caminho tem de ser o do JWT
     (com `share`, quem decide é a `projects`);
   - regra D7 do `owner` (ausente → permitido; presente → valor único igual ao dono do
     caminho; contraditório ou multivalor → recusa);
   - nas 22 rotas, o `X-Caller-Id` é trocado pela identidade RS256;
   - `forwardAxiosError` preserva os códigos;
   - `limits.fileSize` no upload de imagens (ideia 8);
   - sem retries automáticos de mutações com resultado ambíguo (JWT-C1 A).
4. **`projects`:**
   - `getCallerId` só a partir da identidade verificada (sem `X-Caller-Id` nem
     `jwt.decode`);
   - sem `share`, exige chamador = dono em **todas** as rotas, incluindo
     `GET/POST/DELETE /:user` e `/presence`;
   - com `share`: partilha do projeto, não revogada, permissão suficiente;
   - ACL-C1: `DELETE` do projeto só pelo dono; o editor continua a editar e a remover
     media; o leitor não elimina o projeto nem media;
   - a limpeza dos projetos quando uma conta é eliminada continua a funcionar, pelo par
     `users → projects` (B5), limitada ao titular;
   - links sem `expiresAt` (LINK-C1 A).
5. **`users` e `subscriptions` (D9):**
   - identidade interna obrigatória, com exceções públicas explícitas e fechadas: registo,
     login, sessão anónima, validação de sessão e leitura de um preset partilhado por
     `shareId` (`GET /presets/share/:shareId`, pública por desenho, como o link de
     partilha de projeto);
   - presets próprios (`/users/:user/presets…`): o `requireAuth` local passa a usar a
     identidade interna, e só o próprio utilizador lista, cria, altera, apaga ou partilha
     os seus presets;
   - o registo público não aceita `type: premium` (G06);
   - a listagem de todos os utilizadores (`GET /users/`) deixa de estar disponível a
     pedidos de utilizador, e o perfil de outra conta só é lido pelos serviços e
     operações previstos na matriz D4 (G05, S14);
   - `PUT /:user` vindo de um pedido de perfil nunca altera `type` (G07, D09);
   - a mudança de `type` só é aceite na operação interna de subscrição: hoje é o gateway
     que, depois de criar ou cancelar a subscrição, chama `PUT /users/:id {type}`
     (`apiGateway/routes/subscriptions.js`). Essa chamada passa a levar a identidade
     interna com o contexto da rota de subscrição, e a `users` só aceita o `type` nesse
     contexto e para o próprio chamador;
   - criar, ler e cancelar a subscrição só pelo titular (`user_id` = chamador; G08, G09,
     D14).
6. **Frontend:** esconder ou desativar "eliminar projeto" quando quem está a ver não é o
   dono (ACL-C1); os links de partilha `?owner=…&share=…` continuam a funcionar.

7. **Relógios:** deadlines locais com relógio monotónico, para que um recuo do relógio
   não alongue um prazo já calculado; `exp`/`iat` verificados sem tolerância que
   prolongue o acesso (JWT-C1 A).

**Critério de aceitação:**
- S01 = 0 e S02 = 0 (rede e host) em `--quick`;
- fluxo de subscrição legítimo (subscribe → premium → cancel → free) a funcionar (F05);
- S05 a 100%;
- testes S06, S07, S13, S14, S15 e D7 (ausente, igual, contraditório, multivalor).

### B5 — mTLS nas APIs internas e TLS por salto

**Origem:** D4, opção A, WS-C1 A, PKI-C5 A, matriz de pares, S03, S08, S09.

1. **Servidores HTTPS** em `projects`, `users`, `subscriptions`, `img_storage` (hoje
   HTTP) e `generative-mock`:
   - certificado de cliente obrigatório;
   - **lista de permissão por par e operação** (matriz D4), com o resto negado.

   | Origem | Destino | Operações permitidas |
   |---|---|---|
   | ws_gateway | projects | Só a rota interna de autorização WS |
   | api_gateway | projects / users / subscriptions | Operações do chamador, com identidade RS256 |
   | projects | users | Perfil, limites e quota |
   | projects | img_storage | Objetos dos projetos autorizados |
   | users | projects | Limpeza ao eliminar a conta. Hoje aponta para uma porta/URL diferente da API: corrigir e testar |
   | expand_ai | generative-mock | Outpainting |
2. **Clientes:**
   - certificado próprio;
   - verificação do servidor e da identidade esperada;
   - `maxCachedSessions: 0` no Node;
   - nenhum `rejectUnauthorized: false` (hoje existe em todos os clientes).
3. **nginx → frontend/api_gateway/ws_gateway:** TLS com `proxy_ssl_verify` e o nome
   esperado. O browser → nginx continua com o certificado da instalação, agora emitido
   pela CA local.
4. **Guarda de validade em funcionamento:** um processo fecha ou suspende o canal
   quando o seu certificado expira (PKI-C3 A). A verificação no arranque está no B1.
5. **`img_storage` (S03):** só aceita chamadas da `projects` com mTLS. Os URLs
   assinados são emitidos apenas a pedido da `projects`, depois de autorizar.

6. **Healthchecks do B3** passam a usar HTTPS com a CA da instalação (e o certificado
   de cliente onde o servidor o exige). Senão falham e os serviços entram em ciclo de
   reinício.

**Critério de aceitação:**
- S03 = 0;
- S08: certificado de outro serviço da mesma CA recusado, CA errada recusada,
  certificado expirado recusado;
- S09: 0 falhas legítimas;
- S05 a 100%;
- S21 medido (sobrecarga dentro do mínimo de +10 ms).

### B6 — Upload: motor comum, staging e adaptador do POST antigo

**Origem:** UP-C1 A, UP-C2 A, UP-C3 A, UP-C5 A–UP-C9 A, ideia 2, ideia 8, U01, U04,
U08, U09, U15, U16, U17, U18, U19, U20, U25.

1. **Coleção de tentativas `uploads` (UP-C3 A)**, separada dos media. Cada tentativa
   tem estados (`created → receiving → received → validating → committing →
   ready_hash_pending → ready`, os terminais `rejected/expired/cancelled/failed` e
   `reconciling`), `deadline` absoluto, geração e referências de objeto. A limpeza tem
   estado próprio (`cleanup_pending/cleaned/cleanup_failed`) e não transforma um `ready`
   em falha. O journal não guarda JWT, URLs assinados nem segredos. Os IDs de tentativa
   não são credenciais, e nenhum ID ou chave se reutiliza entre tentativas ou gerações.
2. **Área de staging** com chave única por tentativa (novo stage). Os pendentes e os
   candidatos ainda sem commit nunca aparecem em listagens, signers, previews, Apply ou
   export. O prefixo ou o nome secreto da chave não é controlo de acesso: quem decide é o
   estado da tentativa e a associação ao projeto. Os estados terminais não voltam a
   receber nem a publicar.
3. **Rotas novas no `img_storage`** (só por mTLS a partir da `projects`): escrita em
   fluxo para o staging, HEAD, cópia para o candidato, leitura em fluxo (hash e
   `ffprobe`), remoção e URL `PUT` pré-assinado com `ContentLength` (para o B7).
4. **Motor comum de validação e commit**, usado pelos dois transportes:
   - HEAD do tamanho real;
   - candidato imutável criado a partir do staging (UP-C6 A), com CopyObject conforme
     SP-03;
   - `ffprobe` sobre o candidato, por URL interno gerado pelo servidor (sem redirects e
     sem nenhum URL ou host vindo do cliente; S24), com TLS validado e bytes e tempo
     limitados (UP-C8 A: 15 s incluindo a fila, até 2×F+16 MiB). O `ffprobe` não tem
     limite de bytes, por isso lê de um **relé em loopback dentro da `projects`**, que
     reencaminha para o SeaweedFS por HTTPS validado e corta ao atingir o limite (D-17);
   - validação das regras de `projects/utils/video.js`; se falhar, apaga os objetos da
     tentativa e responde 400 como hoje;
   - commit condicional no documento do projeto (barreira, `expectedVersion`,
     permissão atual, marcador idempotente, uma única subida de versão).
   - **Todos os escritores que fazem `$set` de um snapshot do projeto preservam os
     campos de controlo** (barreiras e marcadores). O `updateIfVersion` atual não o
     garante e tem de ser adaptado, senão uma escrita normal pode restaurar uma barreira
     antiga (ciclo de vida, UP-C6).
   - Os campos de controlo não sobem a versão pública do projeto; só o commit visível a
     sobe, uma vez.
   - **Corridas entre commit e limpeza/cancelamento:** se o commit ganhou, o candidato
     nunca é apagado por um estado antigo da tentativa; se a limpeza ou o cancelamento
     ganharam, um worker atrasado não pode publicar. Os escritores atrasados (incluindo
     um CopyObject em curso) têm de estar terminados ou impedidos de escrever antes de se
     apagar um objeto de estado incerto. Não se presume transação entre MongoDB e S3.
5. **Hash depois de `ready` (UP-C7 A):**
   - em fluxo, concorrência 1, estado durável e retoma; só a geração que corresponde ao
     media pode gravar o resultado, e uma retoma não reenvia o corpo nem cobra o Apply;
   - a cache de previews fica **desligada para leitura e escrita** enquanto falta o
     hash (`makePreviewCacheKey`); nunca se usa uma chave com hash vazio nem o hash
     enviado pelo cliente;
   - o schema aceita `og_sha256` em falta só em media de vídeo `ready_hash_pending`,
     sem relaxar as imagens;
   - U14: ≤10 s, alvo ≤5 s.
6. **Limites e prazos (UP-C5 A):**
   - token de 300 s (expirado não concede entrada e nunca se renova o mesmo token);
     tentativa de 900 s absolutos (não se publica depois do prazo, e erros, filas ou
     retries não reiniciam o prazo); corpo de 600 s com 30 s sem dados; validação e
     commit de 180 s (um erro ou timeout não prova que não houve commit: consulta-se o
     estado antes de repetir);
   - 3 vagas de trabalho globais, partilhadas pelos dois transportes desde o claim até
     ao hash e à limpeza (no máximo 3 por sujeito);
   - 16 tentativas com recursos pendentes (no máximo 3 por sujeito; uma falha não
     liberta o orçamento enquanto houver recursos por limpar) e 4096 registos de journal;
   - acima de qualquer teto, recusa explícita **antes** do corpo, sem filas escondidas;
   - as vagas e os contadores são reservados por claim atómico e as reservas de
     trabalhos interrompidos são recuperadas; uma lease expirada só liberta a vaga depois
     de o trabalho real estar terminado ou impedido de escrever (fencing).
7. **Limpeza ativa (UP-C9 A):**
   - a cada 5 s, idempotente, com barreiras; sobrevive a reinícios (retoma pelo estado
     persistido) e nunca apaga um `ready` nem um envio ainda válido;
   - um media publicado nunca é apagado por vencer o prazo de uma tentativa antiga;
   - só remove objetos próprios e não referenciados, distinguindo uploads multipart
     incompletos de objetos completos não confirmados; nunca faz purge por prefixo;
   - tombstones e journal durante ≥24 h depois do resultado reconciliado **e** da limpeza
     verificada; uma referência ainda pendente nunca se apaga só por envelhecer;
   - leituras e varreduras paginadas; ao atingir o teto de 4096 registos, recusam-se
     tentativas novas, sem apagar evidência ainda necessária;
   - U22: TTL+60 s, alvo TTL+10 s.
8. **Adaptador do POST antigo** (`POST /:user/:project/video`; UP-C1 A):
   - o `addProjectMedia` deixa de tratar vídeos (passam ao adaptador e ao motor comum);
     as imagens continuam no caminho atual;
   - autentica e autoriza **antes** do corpo;
   - recusa cedo pelo `Content-Length` acima do limite do perfil (U18) e, durante o
     parsing do multipart, conta os bytes do ficheiro (não do envelope) e corta no
     limite. Clientes com `Transfer-Encoding: chunked` continuam aceites, com o limite
     imposto durante o parsing;
   - no nginx, a localização deste POST tem `proxy_request_buffering off` e
     `client_max_body_size` do maior perfil (1 GiB + envelope); o limite global do nginx
     desce para o tamanho das imagens (ideia 8). Sem isto, o nginx recebe o corpo inteiro
     antes do gateway poder recusar (U19, U08);
   - passa o ficheiro em fluxo, com contrapressão, gateway → projects → staging, sem
     multer em memória;
   - chama o motor comum;
   - responde 204 com `X-Project-Version` como hoje; os códigos novos do fluxo novo não
     se aplicam ao POST antigo sem revisão de compatibilidade.

   Decisão D-02: o ficheiro vai **em fluxo até ao staging**, e o adaptador usa o mesmo
   motor do fluxo novo. Não há spool integral na `projects`.

   Decisão D-14, resolvida pela D-16 depois do SP-03: o adaptador escreve
   **diretamente numa chave de candidato nova e única**, que o cliente nunca pode
   escrever (é isso que a UP-C6 protege); o resto do motor é igual. O CopyObject chegou a
   6,2 s e somava ~100 MiB à U04. Os volumes do SeaweedFS são pré-criados no arranque
   (por exemplo `volume.grow`), para evitar a pausa de ~6 s ao criar volumes, que também
   afeta o PUT do fluxo novo; o efeito mede-se no B6.
9. **Imagens:** mantêm o caminho atual, com `limits.fileSize` (ideia 8).
10. **Memória do SeaweedFS (D-10):** spike curto com `GOMEMLIMIT`/`GOGC` no contentor
   `seaweedfs`, medido com o passo U04 do `med.py` em `EXP`. Se reduzir sem erros,
   aplica-se e regista-se a justificação. Se não, a U04 fica como limitação explicada.

**Critério de aceitação (EXP completo de upload):**
- U01 ≤64 MiB;
- U20 3/3 sem OOM;
- U19 ≤8 MiB e recusa antes do corpo;
- U18 100%;
- U08 ≤F+16 MiB e 0 resíduos;
- U09 <3 s;
- U15, U16 e U17 a 100%;
- U25 sem erros;
- U04 medido: mínimo nginx ≤128 MiB e SeaweedFS ≤256 MiB (alvo ≤64/≤128); se o spike
  D-10 não bastar, fica como limitação declarada (§10);
- U10: mediana do tempo total ≤1,10× a da BF em cada estrato com base (alvo ≤ BF);
- as vagas de upload (que se mantêm ocupadas até ao fim do hash) não recusam os uploads
  que o `med.py` faz: sequenciais nos estratos e 3 em simultâneo na U20/U25;
- testes U21, U22 e U23;
- guardas do adaptador: sem token antes do corpo, respostas inválidas (400) iguais às
  de hoje, nomes duplicados, partilhas (editor sobe, leitor não), conflito 409;
- política de quota (UP-C2 A) com fixtures free com quota 0 e 5, premium, dono, editor,
  leitor e anónimo: o upload não cobra nem recusa por saldo zero; o anónimo continua
  sem vídeo; o leitor não faz upload (U24).

### B7 — Fluxo novo de upload (pedido → PUT pelo nginx → confirmação)

**Origem:** UP-C1 A, UP-C4 A, UP-C9 A, D11, ideia 2 (fluxo), S22, S23, S24, U11, U12,
U13, U26.

1. `POST /:user/:project/video/uploads` com `{name, size, type, duration, width, height}`:
   - valida o perfil e os limites declarados, sem quota (UP-C2 A);
   - cria a tentativa;
   - devolve um token opaco de 256 bits, de uso único, com 300 s de validade.
2. `PUT /api-gateway/uploads/<token>`: o nginx faz `auth_request` a uma rota interna do
   gateway, que verifica o JWT e consulta a `projects`.
   - A `projects` faz a **reclamação atómica** `created→receiving` por CAS: num PUT
     concorrente só um ganha. Uma reclamação nunca volta a `created` para facilitar um
     retry: sem prova de corpo completo, faz-se uma tentativa nova com chave nova.
   - O nginx encaminha em fluxo para o SeaweedFS, com o `Host` assinado, o comprimento
     conhecido (comparado com o autorizado **antes** do corpo), sem retry e com
     `proxy_request_buffering off`. O número de bytes efetivos é imposto durante o envio
     (o HEAD só deteta o excesso no fim) e o tamanho real é confirmado no `confirm`.
   - Configuração nginx: `location /api-gateway/uploads/` com `auth_request` e
     `auth_request_set`; `proxy_pass` com variável (exige `resolver 127.0.0.11`);
     `client_max_body_size` de 1 GiB só nesta localização e na do POST antigo de vídeo
     (B6); o limite global fica baixo; a localização interna de
     autorização com `proxy_pass_request_body off`. Os tokens e URLs não aparecem nos
     logs do nginx.
3. `POST …/uploads/<token>/confirm`: chama o motor comum do B6, de forma idempotente,
   sem permitir contornar o 409 nem ressuscitar tentativas expiradas. Nenhum token
   autoriza outra chave, outro projeto ou outro tamanho além dos da tentativa.
4. **Códigos de resposta:** 401, 403, 404, 409, 410, 411, 413, 429, 503 e 400; o
   `auth_request` tem o seu próprio mapeamento.
5. **Frontend (D-01):** o upload de vídeo passa ao fluxo novo em 3 passos, com
   metadados lidos por `<video>` e progresso por XHR. Só mostra "pronto" depois do commit
   validado (a resposta do PUT não conta). O POST antigo continua disponível pelo
   adaptador.

**Critério de aceitação:** testes S22–S24, U11–U13 e U26, e UL-01 a UL-12 do ciclo de
vida.

### B8 — WebSocket: autenticação, autorização por sala e permanência

**Origem:** D6.1, D6.2 B, D6.3 A, WS-C1 A–WS-C5 B, LINK-C1 A, S04, S10, S11, S12, S13,
S21.

1. **Ligação:**
   - JWT obrigatório, incluindo anónimos, verificado antes de admitir salas;
   - a ligação termina na expiração do JWT;
   - handshake e token até 8 KiB; mensagens até 64 KiB.
2. **`join-project`:**
   - payload `{projectId, access:{kind:"owner"}}` ou `{…kind:"share", shareId}`; o
     sujeito vem sempre da ligação, nunca do payload;
   - `leave-project` retira a pertença e invalida as avaliações pendentes; desligar
     invalida todas as da ligação;
   - um leitor recebe os eventos que o modelo lhe permite (não exigir edição); entrar
     na sala não ocupa um lugar de editor/presença;
   - consulta fresca por cada join; repetir um join já confirmado não duplica estado;
     uma entrada nova nunca usa a autorização de outro membro, de outro contexto ou de
     uma entrada anterior, nem mesmo com a `projects` indisponível;
   - callback com `joined`, `denied`, `unavailable`, `invalid_request`,
     `session_expired` ou `rate_limited`;
   - join até 4 KiB.
3. **Rota interna** `POST /internal/ws/projects/:projectId/authorize`, só para o
   ws_gateway por mTLS (WS-C1 A):
   - lotes de um projeto, até 50 avaliações e 65 536 bytes de JSON UTF-8, em pedido e
     resposta; o lote divide-se **antes** de ultrapassar qualquer dos dois limites; uma
     avaliação que não caiba sozinha é recusada explicitamente; nada é truncado;
   - decisões individuais `allow`, `deny` ou `unavailable`: o resultado de um membro ou
     de um link inválido nunca decide os outros; uma resposta parcial, duplicada, trocada,
     grande demais ou truncada nunca concede acesso por omissão; a resposta também tem de
     caber no seu limite de 64 KiB;
   - lê o estado atual, sem cache; uma falha da BD é `unavailable`, nunca confirmação de
     posse nem de revogação.
4. **Fila e lotes (WS-C2/C3/C4):**
   - timeout total de 1 s, a contar da admissão;
   - 4 consultas ativas globais, 1 por projeto;
   - 16 pendentes, no máximo 1 por projeto, com substituição pelo mais recente sem
     adiar o prazo;
   - alternância entre projetos e cursor de membros;
   - revalidações do mesmo contexto coalescidas, sem ciclos acumulados;
   - sem filas ilimitadas escondidas de joins, callbacks, promessas ou ciclos; fila cheia
     ou prazo expirado → recusa temporária de entradas novas, com a causa registada;
   - a justiça abrange também os projetos que ainda não entraram na fila, e o cursor de
     membros não se torna outra fila ilimitada;
   - todos estes valores são parâmetros configuráveis (WS-C2/C3/C4), não capacidade
     demonstrada.
5. **Permanência (D6.3 A):**
   - revalidação a cada 1 s;
   - autorização local até 5 s desde o início da consulta positiva, limitada ao JWT;
   - falhas não renovam;
   - uma negação retira o membro já;
   - outra via válida **apresentada pelo membro** mantém o acesso; nunca se descobre nem se
     concede acesso por um link que o membro não apresentou;
   - respostas fora de ordem são rejeitadas por geração e sequência;
   - o prazo é verificado também **antes de cada emissão protegida**.
   - Callbacks de joins substituídos recebem uma resposta explícita; revalidações
     retiradas ficam "devidas", sem renovar a autorização nem criar outra fila.
6. **Tetos (WS-C5 B):**
   - 512 ligações e 4096 contextos (reservas incluídas), 32 salas por ligação e 4 vias
     por sala;
   - token buckets de 5/s (burst 10) por sujeito e 100/s (burst 200) por processo,
     com ≤2048 buckets, conservados até 2 s depois do disconnect para a reconexão não
     reiniciar o crédito;
   - acima dos tetos, recusa controlada, sem expulsar outra autorização válida e sem
     alterar os limites para fazer passar um ensaio;
   - o limitador não bloqueia `leave`, `disconnect`, remoções nem revalidações devidas;
   - JWT inválido é recusado antes de admitir salas; as reservas libertam-se também em
     falha de autenticação.
7. **Eventos em salas pessoais** (preview e progresso, `io.to(user)`): a `projects`
   passa a incluir o projeto no payload, e o WS só emite a quem tem autorização atual
   nesse projeto (WS-E1).
8. **Frontend:** enviar o payload novo (owner ou share), tratar as recusas e fazer
   reconexão explícita com JWT válido e nova autorização por sala. Depois de um corte ou
   de um reinício do WS, as pertenças nunca se restauram de memória e nunca se cria uma
   identidade anónima nova como atalho.
9. **`med.py` (D-03):** opção `MED_WS_JOIN_FORMAT=legacy|v2`, com `freeze` e registo
   (ver §6).

**Critério de aceitação:**
- S04 = 0;
- S12 ≤5 s (alvo ≤2 s) sem eventos depois do limite;
- S05 a 100%;
- testes WS-T01–T10, WS-N1, J1, P1, L1, L2, L3, R1, B1 e E1.

### B9 — Sessões: comportamento do frontend e reemissão assistida

**Origem:** SESS-C1 A, JWT-C1 A, D6.1, S06, F06, recuperação anónima, D-15.

1. **Frontend:**
   - um erro de validação ou um token expirado **não cria** outra identidade anónima
     (`lib/mutations/session.ts`, `lib/queries/session.ts`,
     `providers/session-provider.tsx`);
   - uma falha de rede não é logout;
   - um anónimo novo só por ação explícita;
   - quando a sessão guardada no browser é recusada (expirada, ou de antes do reset
     geral, que mudou o segredo), o frontend mostra uma escolha explícita: iniciar
     sessão, criar uma sessão anónima nova ou, para um anónimo, pedir reemissão
     assistida. Nunca substitui a identidade em silêncio.
2. **Emissor administrativo** (`users`, comandos `inspect`, `issue` e `status`):
   - nunca existe uma rota pública que receba um ID e emita um JWT;
   - trabalha sobre um caso privado fora do repositório, com os estados
     `pending_evidence → evidence_verified → approved → issued → import_verified →
     imported → completed` e `conflict/failed/issued_unconfirmed`, e bloqueio por caso;
   - recusa casos sem prova, com `template_only: true` ou que não estejam `approved`;
   - emite com o issuer da instalação, para o mesmo `_id`, sem nunca copiar o segredo
     HS256 para o browser, para a `projects` nem para o ficheiro do caso;
   - grava o resultado com criação exclusiva e permissões 0600;
   - não escreve o token no stdout.
3. **Página `/session-recovery`:**
   - suspende o bootstrap do `SessionProvider` antes de qualquer efeito;
   - lê o ficheiro em memória (≤16 KiB);
   - valida no servidor e confere a identidade, sem confiar em IDs, nomes ou permissões
     escritos no ficheiro; um JWT de outra instalação é recusado;
   - nunca usa o `useLogout` (o caminho atual cria outra identidade);
   - importa com confirmação;
   - reconecta.
4. **Reset geral, sem migração (D-15).** Não há clientes reais: cada stack de
   desenvolvimento, de verificação ou da MF parte do zero, com o `ops/secrets.sh init`.
   Apagar instalações antigas noutros computadores é decisão de cada dono, nunca um
   passo deste plano nem de um agente. Não há inventário de sessões, transição do
   segredo sobre dados reais, recuperação das identidades anónimas antigas nem migração
   de media ou de links antigos (a D-08 fica sem efeito).

   Fica um **runbook curto para uma futura troca do segredo** (por exemplo, por
   suspeita de exposição), como a SESS-C1 A prevê: parar a admissão, trocar o segredo
   sem aceitar o antigo, os registados fazem login e os anónimos recebem reemissão
   assistida pela ferramenta do ponto 2. Em nenhum passo se cria outra conta, se limpam
   projetos ou se reinicia a quota. É documentado e ensaiado com fixtures, não executado
   sobre dados reais.

**Critério de aceitação:** testes AR-01–AR-12, SEC-01 e SEC-02, S06 e F06.

### B10 — Operação da PKI: renovação, retirada e isolamento

**Origem:** PKI-C2 B, PKI-C3 A, PKI-C4 B, PKI-C5 A, S20, F06.

1. **`ops/pki.sh renew`:** renovação normal com a mesma CA, aplicada com reinício
   controlado e fecho das ligações antigas. Não invalida por si o certificado anterior
   ainda válido (isso só acontece com o `retire`).
   - Em `renew` e `retire`: fechar os sockets HTTP keep-alive, as ligações WS afetadas e
     os pools e clientes com estado TLS antigo; eliminar as caches de sessões TLS e as
     chaves de tickets; confirmar sockets e processos reais novos, não só os ficheiros
     novos. Uma retoma TLS antiga não pode contornar a retirada.
2. **`ops/pki.sh retire`** (PKI-C2 B):
   - CA nova;
   - reemissão de **todos** os certificados com chaves novas;
   - retirada da CA antiga de todos os trust stores, incluindo o nginx e a confiança do
     browser.
3. **`ops/maintenance.sh isolate|reopen`** (PKI-C3 A e PKI-C4 B):
   - manutenção planeada: suspende admissões e só corta depois de confirmar que não há
     uploads nem processamentos em curso (senão adia); compromisso: isola logo, sem
     esperar pelos trabalhos, e regista os interrompidos para o B11;
   - corta as ligações novas e as persistentes, os acessos internos e os consumidores
     RabbitMQ;
   - regista as versões de certificados e CA efetivamente carregadas por cada
     participante;
   - regista `t_detectado`, `t_comando`, `t_isolado` e `t_reabertura`; o `t_isolado` só
     conta com o corte observado (nem o fim do comando nem um bloqueio só no nginx
     substituem essa observação);
   - reabre só com o manifesto completo e os controlos positivos e negativos (CA antiga
     recusada em ligação nova e em retoma);
   - uma aplicação parcial fica isolada; testa-se com um participante não atualizado,
     um certificado expirado, um par errado e uma falha de reinício. Os controlos
     negativos cobrem o certificado de cliente e o de servidor nos percursos aplicáveis;
   - nunca se repetem mutações às cegas, nem se recupera uma CA retirada como rollback.
4. **Piloto PKI-C4 B:** probes dos dois lados do perímetro e uma ligação persistente
   prévia de cada tipo; se passar dos 30 s ou faltar prova de algum corte, regista-se
   "isolamento incompleto" e continua-se sem reiniciar o relógio. 3 tentativas,
   isolamento ≤30 s (alvo ≤10 s), substituição
   medida, com um job em curso e um manifesto (instalação, commit, digests, carga, bruto
   por tentativa). Corre assim que B1, B2, B5 e B10 estiverem feitos (D-09).
   O marco anterior de 23/11 às 18:00 fica substituído por esta regra, e a mudança está
   registada.
5. **Matriz PKI-C5 por canal** (`docs/refactor-matriz-canais.md`), preenchida com o
   resultado de cada canal: digest, versões, emissor/SAN, comandos, bruto e asserção.
   Inclui o teste manual no browser com perfil isolado, **sem nunca ultrapassar
   avisos**.

**Critério de aceitação:** S20, isolamento medido e matriz completa, com as lacunas
declaradas.

### B11 — Reconciliação administrativa (OPS-C1 A)

**Origem:** OPS-C1 A.

**Ferramenta `ops/reconcile`:**
- isolar primeiro;
- inventário privado por execução (projeto, token, executor, mensagens,
  Process/Result, objetos, quota);
- classificar cada execução como confirmada, indeterminada ou perdida;
- invalidar a geração das execuções interrompidas antes de reabrir os consumidores;
- pôr em quarentena as mensagens e os outputs antigos;
- acertar a quota com um identificador persistente aplicado na mesma atualização
  atómica, para não reaplicar mesmo depois de um crash; uma resposta perdida obriga a
  reler o estado, nunca a repetir o refund;
- nunca apagar todas as filas ou Process para esconder ambiguidades; nunca inventar
  reembolsos nem cobrar outra vez;
- sem replay automático de uploads, mutações, billing ou ferramentas.

**Critério de aceitação:** os cenários obrigatórios do OPS-C1 (imagem e vídeo
interrompidos, resposta sem commit, débito ambíguo, editor ≠ dono, mudança de dia,
crash da própria reconciliação e mensagem tardia), com 0 débitos ou compensações
indevidos nas fixtures.

### B12 — Verificação final e MF

1. **Regressão completa** (F01–F05), com cada ponto verificado e o resultado guardado:
   - os testes existentes (`Tools/video` pytest e os testes Node);
   - perfis: anónimo (só imagens, com limites), free (5 operações por dia, débito só no
     Apply, devolução no cancelamento) e premium;
   - registo, login, sessão anónima e validação; eliminação de conta com limpeza dos
     projetos (par `users → projects`);
   - upload de imagens e de vídeos, pelo POST antigo e pelo fluxo novo;
   - pipelines de imagem, de vídeo e mista: as 8 ferramentas PIL, o watermark (imagem
     derivada), as 7 ferramentas de IA (incluindo `expand_ai` → `generative-mock` com
     mTLS), trim e speed por vídeo, legendas e extração de frames;
   - preview (3 s nos vídeos), Apply em lote, cancelamento, exportação e exportação PDF
     (só imagens);
   - eventos em tempo real: progresso, `video-progress` e `preview-ready` nas salas de
     projeto e pessoais, para o dono e para membros autorizados;
   - partilhas read/edit (links antigos e novos), revogação, presença, versões e conflito
     409;
   - presets próprios e preset partilhado;
   - fluxo de subscrição (subscribe → premium → cancel → free).
2. **Suíte de conformidade completa** (§5), com o bruto guardado.
3. **`med.py run --campaign EXP` completo**, para confirmar que tudo corre antes da MF.
4. **Congelar o código** e correr a **MF** no Mac oficial, seguindo o §6, e depois o
   `med.py compare`. O `preflight` da MF exige a árvore da aplicação limpa: a MF corre
   sobre um commit, e o manifesto regista-o.

---

## 4. Dependências e marcos

O estado de cada bloco e o ponto onde o trabalho parou estão no
[documento de passagem](refactor-handoff.md).

| Bloco | Depende de |
|-------|-----------|
| B0 | — |
| B1 | B0 |
| B2, B4, B5 | B1 (B4 precisa do par RS256 e do segredo HS256 novo) |
| B3 | — |
| B6 | B0, B4, B5 |
| B7 | B6 |
| B8 | B4, B5 |
| B9 | B4, B8 |
| B10 | B1, B2, B5 |
| B11 | B2, B10 (usa o isolamento do `ops/maintenance.sh`) |
| B12 | B0–B11 |

**Sem datas fixas (decisão D-09, 21/11).** Trabalha-se o mais depressa possível. Cada
bloco começa assim que as suas dependências estão feitas. Cada medição ou ensaio (por
exemplo, o piloto PKI-C4) corre assim que tem tudo o que precisa. A MF corre quando os
blocos B0–B11 estiverem feitos, e sempre antes da entrega de 27/11.

## 5. Testes de conformidade (o que além das métricas prova cada decisão)

As métricas da BF/MF medem o efeito (S01–S18, U01–U25). As decisões exigem também
provas de conformidade que **não estão no `med.py`**. Ficam em `tests/conformance/`,
com o bruto em `tests/conformance/results/<data>/` (fora de `evaluation/`, que guarda a
ferramenta congelada):

| Grupo | Casos | Decisões |
|-------|-------|----------|
| Identidade | S06, S07 (alg/iss/aud/typ/rota/método/peer/sub/exp), D7 | D3, JWT-C1 A, D7 |
| mTLS e PKI | S08, S09, S19, S20, ensaios PKI (limiar 7 dias, regresso depois de >30 dias, CA a expirar, chave fora do Git e da imagem) | D4, PKI-C1–C5 |
| Política | S13 (ACL-C1, links persistentes até revogação, revogação; não há links legados a migrar, D-15), S14, S15, presets (próprios só pelo dono; preset partilhado legível por `shareId`; preset alheio recusado) | ACL-C1, LINK-C1, D9 |
| WebSocket | S10, S11, WS-T01–T10, WS-N1, J1, P1, L1–L3, R1, B1, E1 | D6.x, WS-C1–C5 |
| Sessões | SEC-01–SEC-04 e AR-01–AR-12, sempre com fixtures; o SEC-01 cobre a expiração futura e a reemissão assistida, não uma transição de dados reais (D-15) | SESS-C1, LINK-C1 |
| Upload | S22–S24, U11–U14, U16, U21–U24, U26, UL-01–UL-12; o custo do hash em segundo plano (memória, CPU e rede, `t_hash` e `max(t_ready, t_hash)`) medido à parte, porque fica fora da janela da U01 | UP-C1–C9, D11, ideia 2 (U3) |
| Operação | piloto PKI-C4, cenários OPS-C1 | PKI-C4, OPS-C1 |
| Diagnóstico | F07 (custo do mTLS), F08 (retoma), F09 (extensão), F10 (reprodutibilidade) | — |

## 6. MF: preparação e o que muda no `med.py`

1. **`.env.med` da MF:**
   - URIs Mongo de administração com TLS (`tlsCAFile` montado na sonda);
   - `MED_RABBIT_ADMIN` e `MED_S3_ADMIN`;
   - as credenciais legítimas por serviço para os casos "credencial de outro serviço";
   - `MED_SVC_SCHEME_*=https`;
   - `MED_CLIENT_CERT_DIR` com um certificado legítimo para os controlos;
   - `MED_CACERT` com a CA da instalação.

   Nada disto altera o código. As verificações `EXP` dos blocos (stack
   `picturas-nfr-exp`) usam as mesmas variáveis assim que os blocos correspondentes
   estiverem feitos: TLS e credenciais de administração depois do B2, certificados e
   `MED_SVC_SCHEME_*` depois do B5, `MED_WS_JOIN_FORMAT=v2` depois do B8.
2. **`PICTURAS_SECRETS_DIR`** definido no ambiente do `med.py stack up`.
3. **Alterações de código previstas** (as únicas). Ambas aprovadas, ambas com `freeze` e
   uma nota em `evaluation/IMPLEMENTATION_NOTES.md`, e ambas com o valor por omissão
   igual ao comportamento da BF. A primeira é o **formato do `join-project`** (D-03).

   O `med.py` envia só o ID do projeto. Na MF, o leitor que serve de controlo
   legítimo seria recusado, e isso dava a S04 e a S12 como inconclusivas e a S05 a
   falhar.

   A alteração aprovada é uma opção `MED_WS_JOIN_FORMAT=legacy|v2`:
   - na BF fica `legacy`, com comportamento idêntico ao medido;
   - na MF usa `v2`, que envia `{projectId, access}`.

4. **TLS nos canais de dados** (D-13). O `med.py` congelado usa `http://seaweedfs:9000`
   (no código), AMQP sem `ssl_options`, gestão do RabbitMQ por `http://` e URIs Mongo sem
   TLS. Com o B2, a MF partia:
   - o passo da U04 não arrancava, porque espera o S3 por HTTP;
   - as fixtures da S03 e da S17 ficavam inconclusivas, porque leem a chave do original
     no S3 por HTTP;
   - a S16 e a S17 dariam 0 só por causa do TLS, quando a decisão de 20/11 exige que
     meçam as credenciais e o privilégio mínimo.

   A solução são variáveis `MED_*` vazias por omissão (= BF): o esquema e o CA do S3, a
   porta e o CA do AMQPS, o esquema da gestão do RabbitMQ e as opções TLS do Mongo nos
   URIs de ataque. Na MF, os ataques passam pelo TLS e só falham por credencial ou
   permissão. Implementa-se no B2.
5. **O `med.py` mede o upload pelo POST antigo** (o adaptador), e essas são as métricas
   oficiais comparáveis com a BF (D-06). O fluxo novo (PUT) é provado pelos testes
   U11–U14 e S22–S24, e por uma medição `EXP` de U01/U09 reportada à parte. Nessa
   medição, o tempo pós-envio inclui a confirmação e a validação final (a resposta do PUT
   não conta como aceitação).

## 7. Cortes, se for preciso (por ordem, cada um só com decisão registada)

O objetivo é fazer tudo. Esta tabela só se usa se um spike revelar um bloqueio técnico
ou se a entrega de 27/11 estiver em risco.

| # | Corte proposto | Efeito nas métricas | Fica declarado como |
|---|----------------|--------------------|---------------------|
| K1 | B11 (reconciliação) → limitação | Nenhum | "Recuperação administrativa não demonstrada" (previsto no OPS-C1) |
| K2 | B9, só a parte da ferramenta e da página de recuperação. **A D-15 decidiu mantê-la:** este corte só com uma decisão nova | Nenhum | Limitação SESS-C1 (prevista na recuperação anónima) |
| K3 | B7 frontend (fluxo novo na UI) | Nenhum (o `med.py` mede o adaptador) | Contrato novo disponível na API, UI pelo adaptador |
| K4 | TLS num canal que um spike prove impossível | Nenhum gate (decisão de 20/11) | Lacuna por canal na matriz PKI-C5 |
| K5 | B10, só o piloto | Nenhum | Critério de substituição NM (previsto no PKI-C4 B) |

## 8. Dúvidas para resolver em conjunto

**Todas respondidas a 21/11.** As respostas estão na última coluna e também no
[documento de passagem, §2.6](refactor-handoff.md).

| # | Dúvida | Porque surge | Decisão (21/11) |
|---|--------|-------------|-----------------|
| D-01 | O frontend passa ao fluxo novo de upload (pedido → PUT → confirmação)? | A UP-C1 A diz que sim ("confirmação no frontend"); a 21/11 combinámos deixá-lo opcional | **Sim, no B7** (fluxo novo também no frontend) |
| D-02 | O adaptador do POST antigo passa o ficheiro **em fluxo até ao staging** e usa o motor comum, ou usa um **spool limitado** na `projects`? | As decisões de upload permitem o spool; a UP-C8 A (`ffprobe` sem spool) e o alvo da U08 favorecem o fluxo | **Fluxo até ao staging** e motor comum |
| D-03 | Autorizar a alteração do `med.py` para o formato do join (`MED_WS_JOIN_FORMAT`)? | Sem ela, os controlos do WebSocket falham na MF por causa do protocolo, não da segurança | **Sim**, com `freeze` e registo |
| D-04 | Os serviços Node passam de `nodemon` a `node` + `restart` + `healthcheck`? | Na BF, um OOM deixa a aplicação morta até intervenção manual; o AGENTS.md usa `nodemon` para recarregar em desenvolvimento | **Sim**: `node` + `restart` + `healthcheck` em produção; `nodemon` só no override de desenvolvimento |
| D-05 | Retirar todas as portas internas (alvo da S18) ou publicá-las em `127.0.0.1` (mínimo)? | A D5 dizia loopback; o alvo da S18 é nenhuma publicada | **Retirar todas** as portas internas (alvo da S18) |
| D-06 | O fluxo novo de upload (PUT) também é medido? | O `med.py` mede o POST antigo; as decisões de upload pedem medir a API antiga como guarda, separada do fluxo novo | **Oficiais pelo POST antigo**; fluxo novo provado à parte (testes + EXP) |
| D-07 | O watermark (imagem externa) fica sem TLS se não suportar AMQPS? | Não podemos alterar a imagem; uma terminação por proxy exige desenho próprio | Verificado: o pika suporta TLS, mas o código da imagem não o ativa. **Imagem derivada com patch** (`Tools/watermark/`) |
| D-08 | Quem faz o inventário de sessões das outras instalações (Alexandre, Diogo, José Miguel) e quando? | É condição para trocar o segredo HS256 nas instalações reais | ~~Cada elemento faz a sua instalação até 24/11~~ **Sem efeito (D-15):** não há clientes reais; reset geral |
| D-09 | O piloto PKI-C4 mantém o marco de 23/11 às 18:00? | Exige a PKI e o isolamento prontos; o calendário põe o B10 nesse dia | **Sem datas fixas:** o piloto corre assim que B1, B2, B5 e B10 estiverem feitos; tudo o mais cedo possível |
| D-10 | Tentar reduzir a memória do SeaweedFS (U04) com `GOMEMLIMIT`/`GOGC`? | A memória do SeaweedFS não depende do nosso código (BF: +585 MiB) | **Spike curto**; aplicar se resultar |
| D-11 | Confirmam que se pode começar a implementar? | O documento de ideias diz para não refatorar enquanto houver condições e revisão de requisitos em aberto; a BF já existe e as decisões estão todas escolhidas | **Sim**, começar |
| D-12 | Trabalhar no branch `fase2-refactor` e juntar ao `main` só no fim? | O `main` tem a BF e os documentos; um merge parcial confunde a MF | **Só no branch `fase2-refactor`; nunca um PR para o `main` do upstream (prcsousa)** |
| D-13 | Dar ao `med.py` opções de TLS para os canais de dados (por omissão = BF)? | Encontrado na verificação de 21/11: sem isto a MF parte (U04, S03, S17) ou mede o TLS em vez das credenciais (S16, S17) | **Sim**, com `freeze` e registo (§6, ponto 4) |
| D-14 | No adaptador, copiar o staging para o candidato (UP-C6) ou escrever direto no candidato? | A cópia de 500 MiB entra na U09 (<3 s) | **Decide o SP-03:** se a cópia couber, UP-C6 à letra; senão, escrita direta numa chave de candidato única, sem acesso de escrita do cliente |
| D-15 | Há clientes ou dados reais a preservar? | Várias decisões (SESS-C1, inventário, UP-C3) previam migrar sessões, anónimos e media existentes | **Não: reset geral.** Caem o inventário, a transição sobre dados reais, a recuperação dos anónimos antigos e as migrações. **Mantém-se** a ferramenta de reemissão assistida (emissor e `/session-recovery`), para anónimos que expirem no futuro (SESS-C1 A) |
| D-16 a D-19 | Surgidas no B0 (spikes SP-03, SP-05, SP-07 e SP-11) | Ver o [documento de passagem, §5](refactor-handoff.md) | D-16: escrita direta no candidato + volumes pré-criados; D-17: relé de contagem em loopback para o `ffprobe`; D-18: exchange `topic` com permissões por routing key; D-19: componentes internos do SeaweedFS só em loopback e `/s3-console/` retirado |

## 9. Alternativas rejeitadas (não implementar)

Os documentos de decisão descrevem estas alternativas para justificar a escolha. **Não
fazem parte da solução.** Se uma sessão achar que uma delas é necessária, abre uma
dúvida no documento de passagem.

| Não implementar | Escolhido em vez disso |
|-----------------|------------------------|
| CRL e os seus prazos (PKI-C2 A) | Retirada por CA nova e reemissão completa (PKI-C2 B) |
| Rotação de certificados em funcionamento (PKI-C3 B) | Manutenção com isolamento e reinício (PKI-C3 A) |
| Prazos de substituição de 15/5 min (PKI-C4 A) | Isolamento ≤30 s; substituição medida (PKI-C4 B) |
| Certificados de 90 dias; daemon de renovação automática | 30 dias e renovação pelo administrador (PKI-C1 A) |
| HTTPS + JWT assimétrico de serviço; mTLS universal | mTLS nas APIs internas e TLS validado nos restantes canais (D4, opção A) |
| Rota de autorização WS pelo gateway (WS-C1 B); bilhetes de sala | Consulta direta ws_gateway → projects (WS-C1 A, D6.2 B) |
| Eventos de revogação para cortar salas | Revalidação periódica de 1 s (D6.3 A); eventos ficam como evolução |
| 64 lotes pendentes (WS-C4 B); 1024 ligações/8192 contextos (WS-C5 A) | 16 lotes; 512/4096 (WS-C4 A, WS-C5 B) |
| `expiresAt` nos links, seletor de validade, migração por idade | Links até revogação (LINK-C1 A) |
| Refresh tokens ou sessões persistentes (SESS-C1 B) | Transição e reemissão assistidas, 7 dias absolutos (SESS-C1 A) |
| Registo anti-replay de `jti` (JWT-C1 B) | Identidade de 30 s, contextual; replay residual declarado (JWT-C1 A) |
| RS256 nos JWT de utilizador | HS256 com segredo novo nesta fase (D3) |
| Retirar o POST antigo de vídeo (UP-C1 B) | Adaptador seguro (UP-C1 A) |
| Cobrar ou reservar quota no upload (UP-C2 B) | Quota só no Apply (UP-C2 A) |
| Pendentes na lista normal de media (UP-C3 B) | Coleção de tentativas e staging (UP-C3 A) |
| Retoma por partes/ranges (UP-C4 B) | Uma tentativa por PUT (UP-C4 A) |
| Transações MongoDB com replica set e versionamento S3 (UP-C6 B) | Candidato imutável e commit condicional (UP-C6 A) |
| Hash antes de responder (UP-C7 B) | Hash depois do `ready` (UP-C7 A) |
| Spool em disco para o `ffprobe` (UP-C8 B) | `ffprobe` sobre o candidato, limitado (UP-C8 A) |
| Retry transparente ou reenvio no PUT novo (UP-C9 B) | PUT único, comprimento conhecido (UP-C9 A) |
| Separar a rede Docker em várias redes | Rede única, protegida por identidade e credenciais (D5) |
| Recuperação automática de trabalhos (OPS-C1 B) | Reconciliação administrativa (OPS-C1 A) |
| Automatizar integralmente os testes de browser (PKI-C5 B) | Probes automáticos + browser manual documentado (PKI-C5 A) |

## 10. Limitações a declarar no relatório

Os documentos de decisão exigem que estes pontos sejam ditos, e não escondidos:

| Ponto | Origem |
|-------|--------|
| Um administrador ou root do host comprometido fica fora do modelo de ameaça | D1 |
| Os segredos e chaves antigos continuam no histórico do Git (retirá-los dos ficheiros não os apaga) | S19, guardas Git/build |
| Um link de partilha divulgado continua válido até ser revogado | LINK-C1 A |
| A identidade interna pode ser reutilizada pelo peer autorizado, no mesmo contexto, durante 30 s (não há uso único) | JWT-C1 A |
| O logout e a mudança de password não invalidam um JWT já emitido até ao seu `exp` | SESS-C1 A |
| O ack antecipado das mensagens é um defeito conhecido, não corrigido | OPS-C1 A |
| Os tetos WS (512/4096, filas, taxas) são valores configurados, não capacidade demonstrada | WS-C2–C5 |
| Retirar um certificado interrompe a instalação inteira (PKI-C2 B) | PKI-C2 B |
| A memória do SeaweedFS (U04) e a amostragem a 100 ms da U08 | D-10, revisão da U04, nota 23 |
| Qualquer corte da §7 aplicado, ou um canal sem TLS demonstrado | §7, PKI-C5 A |
| Passar a HTTPS/AMQPS/TLS não é mTLS; só as APIs da matriz D4 têm mTLS | D4, opção A |
| Mover o hash para depois da resposta não é ganho total: o custo continua e é reportado | Ideia 2 (U3) |
| Os relógios de cada critério (WS, PKI, upload), a cobertura de cada principal e as perdas possíveis do ack atual | Critérios operacionais |

## 11. Matriz de rastreabilidade (decisão → bloco)

| Decisão | Bloco(s) | Decisão | Bloco(s) |
|---------|----------|---------|----------|
| D1 | B1, B2, B4, B5 | PKI-C1 A | B1 |
| D2 | B4 | PKI-C2 B | B10 |
| D3 | B1, B4 | PKI-C3 A | B5 (guarda de validade), B10 |
| D4 | B1, B5 | PKI-C4 B | B10 |
| D5 | B3 | PKI-C5 A | B0, B2, B5, B10 |
| D6.1 | B8, B9 | OPS-C1 A | B11 |
| D6.2 B | B8 | SESS-C1 A | B1, B9 |
| D6.3 A | B8 | JWT-C1 A | B4 |
| D7 | B4 | LINK-C1 A | B4, B8 |
| D8 | B4, B8 | ACL-C1 A | B4 |
| D9 | B4, B5 | UP-C1 A | B6, B7 |
| D10 | §5 | UP-C2 A | B6, B7 |
| D11 | B7 | UP-C3 A | B6 |
| WS-C1 A | B5, B8 | UP-C4 A | B7 |
| WS-C2 A | B8 | UP-C5 A | B6 |
| WS-C3 A | B8 | UP-C6 A | B6 |
| WS-C4 A | B8 | UP-C7 A | B6 |
| WS-C5 B | B8 | UP-C8 A | B0, B6 |
| Opção A (TLS/credenciais) | B2, B5 | UP-C9 A | B6, B7 |
| Ideia 7 (supervisão) | B3 | Ideia 8 (limites) | B4, B6 |
| EVAL/`med.py` (D-03, D-13) | §6, B2, B8, B12 | Guardas F01–F10 | B0, B12, §5 |
| D-14 (escrita do adaptador) | B0 (SP-03), B6 | D-15 (reset, sem clientes reais) | B1, B9, §5 |

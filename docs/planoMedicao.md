# Fase 2 — Plano de medição (especificação do `med.py`)

[Índice da documentação](README.md) · [Métricas selecionadas](metricas.md) · **Equipa: PL2-G4**

Este documento é a **especificação de implementação** do script `evaluation/med.py`, que
recolhe todas as métricas escolhidas em [metricas.md](metricas.md). Destina-se a quem o
vai implementar (um agente de IA ou uma pessoa). Diz o que medir, como, com que
repetições, o que guardar e como decidir se o critério foi cumprido. As razões das
métricas e dos valores estão em [metricas.md](metricas.md) e não se repetem aqui.

O mesmo `med.py` corre **duas vezes, com o mesmo método e no mesmo host**:

- **BF** (baseline formal): sobre a solução de base, antes de qualquer alteração ao
  código da aplicação.
- **MF** (medição final): sobre a solução refatorada.

> **Regra para quem implementa.** Onde este plano diz "confirmar no código", lê o
> ficheiro indicado antes de escrever o caso. Não inventes rotas, campos ou nomes de
> contentores. Se algo não existir como aqui descrito, regista a divergência em
> `evaluation/IMPLEMENTATION_NOTES.md` e escolhe a alternativa mais próxima, sem mudar
> o objetivo do caso.

---

## 1. Regras obrigatórias

1. **Isolamento.** O `med.py` só opera sobre o projeto Compose `picturas-nfr` ou
   `picturas-nfr-<sufixo>` (variável `MED_COMPOSE_PROJECT`); qualquer outro nome é
   recusado (lista de permissão, não de proibição). Antes de remover volumes
   (`stack up`, `stack down`, `stack purge`), exige o marcador `.run/stack.json` desse
   mesmo projeto: volumes de outra instalação nunca são apagados, seja qual for o nome.
2. **Nada de alterações à aplicação.** O `med.py` não edita código, `docker-compose.yaml`
   nem `nginx.conf`. A configuração de avaliação é um ficheiro override gerado em
   `evaluation/.run/override.yaml` (§3.2).
3. **Volumes novos por campanha.** Cada campanha começa com `down -v` e `up` do projeto
   isolado. Nunca usa os volumes retidos da equipa.
4. **Sem segredos na saída.** JWT, palavras-passe, chaves S3 e URLs assinadas nunca são
   escritos nos resultados nem no terminal. Guarda-se apenas `sha256(valor)[:12]` quando
   for preciso correlacionar.
5. **Corpus fora do Git.** Os vídeos gerados ficam em `evaluation/.corpus/` (no
   `.gitignore`). No Git ficam só o gerador e o manifesto com os SHA-256.
6. **Pré-condições.** Disco livre ≥60 GiB (EVAL-B1), Docker com pelo menos 8 CPU e 8 GiB
   para a VM, `ffmpeg`/`ffprobe` no PATH e a árvore Git limpa nos caminhos da aplicação.
   Se alguma falhar, o `med.py` termina sem medir.
7. **Falhas contam.** Nenhuma tentativa é descartada. Timeouts, 5xx, OOM e reinícios
   ficam no denominador e no ficheiro bruto.
8. **Um único host para BF e MF.** A BF e a MF oficiais são recolhidas pelo mesmo
   elemento da equipa, no mesmo computador (decisão de 20/11). Execuções noutros
   computadores usam `--campaign EXP`: servem para verificar que o método dá valores da
   mesma ordem de grandeza, nunca se juntam à BF/MF nem entram na comparação. O
   `compare` não classifica nenhuma métrica se os manifestos diferirem em host,
   limites, corpus ou versão do instrumento (§9.3).
9. **Critérios num só sítio.** Os mínimos e alvos são lidos de `evaluation/criteria.yaml`,
   que transcreve [metricas.md](metricas.md). O código não tem valores-limite escritos
   à mão.

## 2. Estrutura de ficheiros

```text
evaluation/
├── med.py                  # CLI principal
├── medlib/                 # módulos (http, ws, memória, disco, docker, casos)
├── criteria.yaml           # mínimos/alvos por métrica (fonte: docs/metricas.md)
├── cases/security.yaml     # matriz congelada de casos S01–S04, S16, S17
├── probe.Dockerfile        # imagem da sonda na rede Docker
├── requirements.txt        # requests, python-socketio[client], websocket-client,
│                           # pymongo, pika, boto3, PyYAML, PyJWT
├── .env.med.example        # variáveis sem valores (credenciais da MF)
├── IMPLEMENTATION_NOTES.md # divergências encontradas no código
├── .corpus/                # (gitignored) vídeos gerados
├── .run/                   # (gitignored) override gerado, ficheiros temporários
└── results/<CAMPANHA>-<UTC>/
    ├── manifest.json
    ├── raw/<METRICA>.jsonl
    ├── summary.json
    └── report.md
```

Python ≥3.11. Uma única dependência de sistema além do Docker: `ffmpeg`/`ffprobe`.

## 3. Interface e ambiente

### 3.1 CLI

```text
python evaluation/med.py preflight
python evaluation/med.py stack up|down|status
python evaluation/med.py corpus
python evaluation/med.py run --campaign BF|MF|EXP [--suite security|upload|all] [--metrics S01,U01,...]
python evaluation/med.py probe --case <id>          # só dentro do contentor de sonda
python evaluation/med.py report <dir> [--resummarise]  # refazer report.md (e resumos a partir de raw/)
python evaluation/med.py freeze <dir_BF> --motivo "..."  # registar a versão do instrumento na BF
python evaluation/med.py compare <dir_BF> <dir_MF>  # tabela BF vs MF vs critérios
```

`run --suite all` executa pela ordem da §6. `--metrics` permite repetir uma métrica sem
correr o resto; o `summary.json` diz quais foram medidas.

### 3.2 Stack isolada (`stack up`)

1. `docker compose -p picturas-nfr down -v --remove-orphans` (só este projeto).
2. Gera `evaluation/.run/override.yaml` a partir de
   `docker compose -f docker-compose.yaml config --format json`:
   - **Portas:** para cada porta publicada no ficheiro entregue, mantém o `host_ip`
     declarado e soma **20000** à porta do host (8080 → 28080). Não acrescenta portas
     que o ficheiro entregue não publica. Assim a superfície da MF é a real e não há
     conflito com a outra instalação.
   - **Limites:** `cpus: 2` e `mem_limit: 2g` em `api_gateway`, `projects`,
     `img_storage` e `video_tool`, iguais na BF e na MF (os mesmos de B16).
3. `docker compose -p picturas-nfr -f docker-compose.yaml -f evaluation/.run/override.yaml up -d --build`.
4. Espera até `https://localhost:28080/api-gateway/` responder e os healthchecks
   passarem (timeout 15 min no primeiro build).
5. Constrói a imagem da sonda `picturas-med-probe` (`probe.Dockerfile`: Python 3.12 slim
   com `requirements.txt` e o diretório `evaluation/` copiado).

Rede da aplicação: `picturas-nfr_elk` (a rede `elk` do Compose; confirmar com
`docker network ls`). Nome dos contentores: `picturas-nfr-<serviço>-1`.

### 3.3 Configuração (`.env.med`, fora do Git)

| Variável | BF | MF |
|----------|----|----|
| `MED_BASE_URL` | `https://localhost:28080` | igual |
| `MED_CACERT` | vazio: verificação TLS do cliente desligada para o nginx autoassinado, registado no manifesto | o mesmo valor que na BF |
| `MED_ADMIN_MONGO_URI_{PROJECTS,USERS,SUBSCRIPTIONS}` | vazio (sem autenticação) | URI de administração, só para fixtures e limpeza |
| `MED_SVC_CRED_<serviço>` | vazio (a base não tem credenciais por serviço) | credenciais legítimas de cada serviço, usadas **só** nos casos "credencial de outro serviço" e nos controlos |
| `MED_RABBIT_ADMIN`, `MED_S3_ADMIN` | `user:password`, `admin:admin123` | credenciais de administração da MF |
| `MED_CLIENT_CERT_DIR` | vazio | certificados de cliente legítimos, se houver mTLS, usados só nos controlos |

Os casos de ataque **nunca** usam credenciais legítimas do serviço alvo. Os controlos
usam-nas sempre.

## 4. Manifesto (`manifest.json`)

Recolhido no início de cada campanha:

- campanha (`BF`/`MF`), início e fim em UTC, versão e SHA-256 do `med.py` e de
  `criteria.yaml`/`cases/security.yaml`;
- `git rev-parse HEAD`, `git status --porcelain` (tem de estar vazio nos caminhos da
  aplicação) e o commit oficial de partida (`MED_BASE_COMMIT`, por omissão
  `0523102`, o topo de `picturas-um/picturas-27` em 20/11) com o resultado de
  `git diff --stat $MED_BASE_COMMIT -- <caminhos da aplicação>` (vazio na BF);
- SHA-256 do `docker-compose.yaml` entregue e do override gerado;
- ID de imagem de cada serviço (`docker compose images --format json`);
- host: `uname -a`, modelo de CPU, RAM, disco livre; `docker info` (CPUs, memória, kernel,
  versão do cgroup, storage driver);
- corpus: nome, tamanho e SHA-256 de cada ficheiro; posição do `moov` (H/T);
- configuração relevante: `client_max_body_size` e `proxy_request_buffering` efetivos do
  nginx (`nginx -T` no contentor) e o caminho do `client_body_temp` (`nginx -V`).

## 5. Instrumentação comum

### 5.1 Cliente HTTP e contas

- Contas por API pública: `POST /api-gateway/users/` com
  `{name, email: med-<uuid>@example.invalid, password, type: "free"}` → 201
  `{user:{_id,type}, jwt}`. Confirmar em `apiGateway/routes/users.js`.
- **Premium por fixture controlada**, igual na BF e na MF: criar a conta como free e
  depois `updateOne({_id}, {$set:{type:"premium"}})` na BD `user`, coleção `users`
  (`users/app.js`, `users/models/user.js`), com `MED_ADMIN_MONGO_URI_USERS`, a partir
  da sonda. **Não** usar `type: "premium"` no registo público: é uma fragilidade medida
  em S01 (G06) e na MF deixará de funcionar.
- Projeto: `POST /api-gateway/projects/<uid>` `{name}` → 201 `{_id, version}`.
  Ler o estado: `GET /api-gateway/projects/<uid>/<pid>` (inclui `version`, `imgs`,
  `tools`). Escritas levam `X-Project-Version: <version atual>`.
- Media: `POST .../projects/<uid>/<pid>/img` (campo `image`) e `.../video` (campo
  `video`), multipart.
- Partilha: `POST .../projects/<uid>/<pid>/share` `{permission:"read"|"edit"}` → 201
  com `id` e `url`; resolver: `GET .../projects/share/<shareId>/project` com o JWT do
  membro; acesso partilhado às rotas do dono com `?share=<shareId>`
  (`projects/middleware/shareAuth.js`); revogar:
  `DELETE .../projects/<uid>/<pid>/share/<shareId>`.
- Sempre que uma escrita devolve 409 por versão, relê a versão e repete uma vez. Fica
  registado.

### 5.2 Upload instrumentado

Implementar com `ssl` + `socket` diretamente (não com `requests`), para controlar o
envio e ler a resposta enquanto se envia:

- Pedido `POST` com `Content-Length` exato e corpo multipart gerado em fluxo a partir do
  ficheiro (blocos de 1 MiB). Nunca carregar o ficheiro inteiro em memória no cliente.
- Marcas monotónicas (`time.monotonic_ns`): `t0` (antes de ligar), `t_headers`
  (cabeçalhos enviados), `t_send` (último byte entregue ao socket, depois de
  `sendall`), `t_first_byte` (primeiro byte da resposta), `t_ready` (resposta
  completa).
- Antes de cada bloco, `select` com timeout 0 sobre o socket: se já houver resposta,
  para de enviar e regista `bytes_sent_at_response`.
- Opção `rate_limit_mib_s` (para U19 e U25).
- Saída por tentativa: `status`, `t_*`, `bytes_sent`, `bytes_sent_at_response`,
  `post_send_ms = t_ready − t_send`, `total_ms = t_ready − t0`, os primeiros 200 bytes do
  corpo da resposta (sem segredos) e o erro de rede, se houver.

### 5.3 Memória dos processos Node (U01, U19)

Por serviço (`api_gateway`, `projects`, `img_storage`), como em
`memory-bank/.../nfr-2026-11-16/lib.mjs`:

1. Encontrar o PID do processo `node` com maior `VmRSS` em `/proc/*/status` do contentor.
2. Imediatamente antes do upload: `echo 5 > /proc/<pid>/clear_refs` (repõe o `VmHWM`) e
   ler `VmRSS` → `rss_pre`.
3. 700 ms depois da resposta: ler `VmHWM` e `VmRSS` → `peak`, `rss_post`.
4. `delta = VmHWM − rss_pre`. Se o PID desapareceu, `process_died = true`.
5. Registar também `RestartCount`, `State.OOMKilled` e o contador `oom_kill` de
   `/sys/fs/cgroup/memory.events`, antes e depois.

### 5.4 Memória do cgroup (U04, U20)

Amostrador em segundo plano, por contentor, iniciado com
`docker exec <c> sh -c '<loop>'` e terminado no fim da janela:

```sh
while :; do
  printf '%s ' "$(cut -d' ' -f1 /proc/uptime)"
  awk '$1=="anon"{a=$2} $1=="file"{f=$2} END{printf "%s %s ", a, f}' /sys/fs/cgroup/memory.stat
  cat /sys/fs/cgroup/memory.current
  sleep 0.05
done
```

- `idle` = mediana de `anon` nos 2 s antes do primeiro byte. `pico` = máximo de `anon`
  na janela. Métrica = `pico − idle` (MiB).
- Se `/sys/fs/cgroup/memory.stat` não existir (cgroup v1), usar a soma do RSS dos
  processos e registar `cgroup: v1` no manifesto.
- Contentores: `nginx`, `seaweedfs`; para U20, também os três Node.

### 5.5 Disco temporário (U08)

Amostrador a cada 200 ms, por contentor, com `du -sk` sobre:

| Componente | Diretório (confirmar) |
|------------|-----------------------|
| `nginx` | `--http-client-body-temp-path` de `nginx -V` (habitualmente `/var/cache/nginx/client_temp`) |
| `api_gateway` | `/tmp` |
| `projects` | `/tmp` (`os.tmpdir()`, ver `projects/utils/video.js`) |
| `img_storage` | `/tmp` |

Resultado: pico de bytes por componente durante a tentativa e, **60 s depois do fim do
estrato**, bytes e nº de ficheiros residuais face ao estado inicial.

### 5.6 WebSocket

`python-socketio` (cliente) sobre `MED_BASE_URL` com path `/socket.io`, transporte
websocket, `auth={"token": jwt}` ou sem `auth`. Eventos emitidos pelo servidor
(`wsGateway/index.js`): `project-op`, `project-updated` (sala `project:<pid>`) e
`process-update`, `video-progress`, `preview-ready`, `preview-error`, `process-error`
(sala pessoal `<uid>`). Entrar numa sala: `emit("join-project", pid)`. Registar para
cada evento recebido o tempo monotónico, o nome e um identificador de correlação (§7.5).
Registar também `disconnect` e o seu motivo.

### 5.7 Sonda na rede Docker

Casos com superfície "rede" correm dentro de
`docker run --rm --network picturas-nfr_elk picturas-med-probe python /med/med.py probe --case <id>`,
que escreve um JSON na stdout. Endereços internos: `projects:9001` (HTTPS),
`users:10001` (HTTPS), `subscriptions:11001`, `img_storage:11000` (HTTP),
`projects_mongoDB:27018`, `users_mongoDB:27019`, `subscriptions_mongoDB:27017`,
`rabbitmq:5672`/`15672`, `seaweedfs:9000`. Confirmar portas e protocolo no
`docker-compose.yaml` e nos `app.js`.

### 5.8 Classificação de cada tentativa de ataque

| Resultado | Condição |
|-----------|----------|
| `ADMITIDO` | A verificação de efeito confirma a leitura, alteração ou receção indevida. |
| `RECUSADO_DOMINIO` | 401/403/404/410 e nenhum efeito. |
| `RECUSADO_TLS` | Handshake TLS recusado (por exemplo, falta de certificado de cliente). |
| `RECUSADO_REDE` | Ligação recusada ou nome/porta inexistente. |
| `INCONCLUSIVO` | 5xx, timeout, serviço em baixo ou verificação de efeito impossível. |

O código HTTP nunca chega para `ADMITIDO`: decide sempre a verificação de efeito. Um
2xx sem efeito confirmado é `INCONCLUSIVO`, com nota.

## 6. Ordem de execução de uma campanha

1. `preflight` → `stack up` → `corpus` (se em falta) → manifesto.
2. **S18** (estático e alcance).
3. **Segurança não destrutiva:** S01, S02, S03, S04, S16, S17 (casos de leitura).
4. **Segurança destrutiva** (cada caso com a sua conta e projeto vítima descartáveis).
5. **S12** (revogação).
6. **S05** (controlos legítimos) e **S21** (latência).
7. `docker compose restart` dos serviços medidos; espera pela prontidão.
8. **Upload:** estratos U01/U08/U09/U10/U15/U17 → U04 → U18 → U19 → U20 → U25.
9. Resíduos finais (U08), `summary.json`, `report.md`.
10. `stack down` (com `-v`), só no fim e só no projeto isolado. Limpeza completa: §12.

A segurança corre antes do upload porque os uploads podem matar serviços.

---

## 7. Procedimentos por métrica — Segurança

Repetições: **3 por caso** (EVAL-C1). Cada repetição usa contas e projetos novos.
Fixture de base por repetição: `owner` (free) com um projeto `victim` que tem 1 imagem
PNG de 64×64 (gerada no momento; guardar o SHA-256) e 1 ferramenta; `outsider` (free);
`reader` e `editor`, com partilhas `read` e `edit` resolvidas.

Os casos ficam em `evaluation/cases/security.yaml`, com:
`id, metrica, superficie, descricao, pedido, verificacao_de_efeito, controlo`.
**A lista abaixo é o mínimo; podem acrescentar-se casos antes da BF, mas depois de
congelada a matriz (SHA-256 no manifesto) não se remove nenhum.**

### 7.1 S01 — Entrada pública (gateway)

Base: `MED_BASE_URL/api-gateway/`.

| ID | Pedido | Efeito verificado (= ADMITIDO) |
|----|--------|--------------------------------|
| G01 | `outsider` JWT, `GET projects/<owner>/<pid>` | o corpo tem `_id == pid` |
| G02 | `outsider` JWT, `GET projects/<outsider>/<pid>?owner=<owner>` | o corpo tem `_id == pid` (asserção corrigida: `_id`, não `user_id`) |
| G03 | `outsider` JWT, `POST projects/<outsider>/<pid>/tool?owner=<owner>` | `len(tools)` do dono aumentou |
| G04 | `outsider` JWT, upload `img` para `projects/<outsider>/<pid>/img?owner=<owner>` | `len(imgs)` do dono aumentou |
| G10 | `outsider` JWT, `GET projects/<outsider>/<pid>/img/<imgId>?owner=<owner>` | devolve `url` e o SHA-256 dos bytes descarregados é o do original |
| G11 | `outsider` JWT, `PUT projects/<outsider>/<pid>?owner=<owner>` `{name:"pwn"}` | o nome do projeto do dono mudou |
| G12 | `outsider` JWT, `DELETE projects/<outsider>/<pid>/img/<imgId>?owner=<owner>` | a imagem desapareceu (destrutivo) |
| G13 | `outsider` JWT, `DELETE projects/<outsider>/<pid>?owner=<owner>` | o projeto desapareceu (destrutivo) |
| G14 | `outsider` JWT, `GET projects/<owner>/<pid>/share` | devolve ids de partilha |
| G15 | `reader` JWT, `POST projects/<owner>/<pid>/tool?share=<readShare>` | `len(tools)` aumentou (permissão insuficiente) |
| G05 | sem token, `GET users/<owner>` | o corpo tem campos do perfil (`email`, `type`) |
| G06 | registo público com `type:"premium"` | o `type` guardado é `premium` |
| G07 | `outsider` JWT, `PUT users/<outsider>` `{type:"premium"}` | o perfil passou a `premium` |
| G08 | sem token, `GET subscriptions/<owner>/status` | devolve dados da subscrição (requer a fixture de subscrição; confirmar em `subscriptions/`) |
| G09 | sem token, `PUT subscriptions/<owner>/cancel` | o estado da subscrição mudou |

Confirmar no gateway (`apiGateway/routes/projects.js`, `users.js`, `subscriptions.js`)
que cada rota existe e se o gateway encaminha `?share`. Se uma rota não existir, o caso
é removido **antes** da BF e isso fica registado.

**Valor:** `admitidos / tentativas` e a lista dos casos admitidos. **Critério:**
`admitidos == 0` e `inconclusivos == 0`.

### 7.2 S02 — Serviços internos diretos

Cada caso corre em **duas superfícies**: `host` (porta publicada + 20000, se existir;
se não existir, `RECUSADO_REDE`) e `rede` (sonda, §5.7).

| ID | Serviço | Pedido | Efeito |
|----|---------|--------|--------|
| D01 | projects | `GET /<owner>/<pid>` sem identidade | `_id == pid` |
| D02 | projects | o mesmo com `X-Caller-Id: <owner>` | `_id == pid` |
| D03 | projects | o mesmo com o JWT do `outsider` | `_id == pid` |
| D04 | projects | o mesmo com um JWT HS256 válido em forma, `id=<owner>`, assinado com uma chave aleatória; e outro não assinado (`alg: none`) | `_id == pid` |
| D05 | projects | `POST /<owner>/<pid>/tool` com `X-Caller-Id: <owner>` | `len(tools)` aumentou |
| D06 | projects | `DELETE /<owner>/<pid>` com `X-Caller-Id: <owner>`, num projeto **não vazio** | o projeto desapareceu (destrutivo) |
| D09 | users | `PUT /<victim>` `{type:"premium"}` sem token | o perfil passou a `premium` |
| D13 | users | `GET /<victim>/process/1` sem token (reserva de quota; confirmar a rota em `users/routes`) | `remaining_operations` da vítima diminuiu |
| D14 | subscriptions | `GET /<owner>/status` sem token | devolve dados |

**Valor:** admitidos / tentativas, por superfície. **Critério:** 0 nas duas superfícies,
0 inconclusivos.

### 7.3 S03 — Storage

Superfícies `host` e `rede`; serviço `img_storage` (HTTP 11000, rotas em
`imageStorageService/server.js`: `/upload`, `/image`, `/delete`, `/copy`).
`og_img_key` obtém-se do estado do projeto do dono (`imgs[0].og_img_key`).

| ID | Pedido | Efeito |
|----|--------|--------|
| D06 | `GET /image/internal/<owner>/<pid>/src/<og_img_key>` | devolve `url`; o SHA-256 dos bytes (descarregados a partir da sonda) é o do original |
| D07 | `POST /upload/<owner>/<pid>/out` multipart `file` | o objeto passa a existir (verificar com `GET /image/internal/...` ou com S3 admin) |
| D08 | `DELETE /delete/<owner>/<pid>/src/<og_img_key>` (vítima descartável) | o original desapareceu |
| D15 | `POST /copy/<owner>/<pid>/src/out/<og_img_key>` | o objeto copiado existe |

**Critério:** 0 admitidos, 0 inconclusivos.

### 7.4 S04 — Admissão WebSocket

Para cada caso: um socket "atacante" entra em `project:<pid>`, um socket do dono
(controlo) também; o dono faz 3 edições espaçadas de 500 ms (`POST .../tool`); janela de
10 s.

| ID | Atacante | Efeito |
|----|----------|--------|
| W01 | sem token | recebeu ≥1 `project-op`/`project-updated` do projeto |
| W02 | JWT válido do `outsider` | idem |
| W03 | JWT com assinatura errada | idem |
| W04 | JWT expirado (gerar com `exp` no passado e a chave errada; na MF usar o perfil real se existir) | idem |
| W05 | `outsider` entra na sala com o `projects` parado (`docker stop`); o `projects` volta; o dono edita | idem |

Controlo: o socket do dono recebe as 3 edições; um `reader` com partilha válida também.
**Valor:** eventos indevidos e entradas concedidas. **Critério:** 0 e controlos a 100%.

### 7.5 S12 — Corte após revogação (QS-07)

Por repetição (3), com janela de 30 s:

1. `owner` cria o projeto; cria a partilha `read` A para `memberA` e a partilha `read` B
   para `memberB`; os dois resolvem a sua partilha.
2. Ligam-se 3 sockets com JWT válido: `owner`, `memberA`, `memberB`. Todos entram em
   `project:<pid>`.
3. **Produtor:** a cada 250 ms o dono faz uma edição que emite `project-op` (por exemplo
   `POST .../tool` com `{procedure:"brightness", params:{brightness: 1 + seq/10000}}`),
   para correlacionar cada evento ao seu `seq`. Guardar `t_emit[seq]` (2xx recebido).
   Confirmar no código que esta operação emite `project-op` com os `params`; se não,
   escolher outra operação que emita um evento correlacionável.
4. Controlo positivo: `memberA` recebeu ≥3 eventos antes da revogação. Senão, a
   repetição é `INCONCLUSIVO`.
5. `DELETE .../share/<A>` → `t_ack` = momento do 2xx.
6. O produtor continua 30 s. Registar os eventos recebidos por cada socket e o
   `disconnect` de `memberA`, se acontecer.
7. Cálculo para `memberA`:
   - `ultimo_recebido` = maior `t_emit[seq] − t_ack` entre os eventos recebidos com
     `t_emit > t_ack`;
   - `primeiro_perdido` = menor `t_emit[seq] − t_ack` entre os não recebidos, a partir do
     qual nenhum outro é recebido;
   - **latência de corte** ∈ [`ultimo_recebido`, `primeiro_perdido`] (incerteza = período
     do produtor); se tudo foi recebido durante os 30 s → `>30000` (censurado);
   - `eventos_apos_limite` = nº de eventos recebidos com `t_emit − t_ack > 5000 ms`.
8. Controlos: `owner` e `memberB` receberam todos os eventos da janela.

**Critério mínimo:** limite superior ≤5000 ms em todas as repetições,
`eventos_apos_limite == 0` e controlos a 100%. **Alvo:** ≤2000 ms.

### 7.6 S16 — Bases de dados (a partir da sonda; e do host se a porta estiver publicada)

Para cada BD (`project`@`projects_mongoDB:27018`, `user`@`users_mongoDB:27019`,
`subscription`@`subscriptions_mongoDB:27017`), com `pymongo` e
`serverSelectionTimeoutMS=3000`:

| Família | Tentativa | Efeito |
|---------|-----------|--------|
| a | sem credenciais: `find_one()` numa coleção da aplicação | devolve documento |
| b | credenciais por omissão ou encontradas em ficheiros versionados (o `med.py` procura `MONGO`/`mongodb://` no Git) | devolve documento |
| c | credencial de **outro** serviço (`MED_SVC_CRED_<x>`): ler a BD de `y` | devolve documento |
| d | credencial do próprio serviço: `insert_one` em `med_canary` noutra BD e `list_database_names()` | operação aceite (limpar com admin) |

Na BF não há credenciais por serviço: as famílias c e d são tentadas sem credenciais
(na base, qualquer cliente tem esse acesso) e contam igual. Controlo: os serviços
funcionam (S05).
**Critério:** 0 admitidos e 0 inconclusivos.

### 7.7 S17 — RabbitMQ e S3

**RabbitMQ** (`pika` e HTTP de gestão):

| ID | Tentativa | Efeito |
|----|-----------|--------|
| R1 | AMQP com `user`/`password` | ligação aberta |
| R2 | `GET :15672/api/overview` com `user`/`password` | 200 |
| R3 | credencial de um worker (`MED_SVC_CRED_brightness_tool`; na BF `user`/`password`): `queue_declare(passive)` + `basic_get` em `ws_queue`; se receber mensagem, `basic_nack(requeue=True)` | operação aceite |
| R4 | a mesma credencial: declarar e apagar uma fila `med_canary_<uuid>` | aceite |
| R5 | credencial de serviço: `GET /api/overview` | 200 |

**S3** (`boto3`, endpoint `seaweedfs:9000`; bucket único, ver
`imageStorageService/services/storage.js`):

| ID | Tentativa | Efeito |
|----|-----------|--------|
| B1 | `admin`/`admin123`: `list_objects_v2` do bucket | lista devolvida |
| B2 | credencial do `img_storage` (`MED_SVC_CRED_img_storage`; na BF `admin`/`admin123`): `create_bucket med-canary-<uuid>` | criado (limpar com admin) |
| B3 | sem assinatura: `GET MED_BASE_URL/s3/<bucket>/<key do original>` | 200 com o SHA-256 do original |

Controlo: uma URL assinada emitida legitimamente (via `GET .../img/<id>` do dono) é
descarregada através de `/s3/`.
**Critério:** 0 admitidos, 0 inconclusivos, controlos a 100%.

### 7.8 S18 — Portas publicadas

1. **Estático:** `docker compose -f docker-compose.yaml config --format json`. Para cada
   serviço ≠ `nginx` e cada porta publicada, classificar o `host_ip` (`""`, `0.0.0.0` ou
   `::` → `todas`; `127.0.0.1` ou `::1` → `loopback`).
2. **Alcance:** na stack isolada, tentar uma ligação TCP (timeout 1 s) a cada porta
   deslocada em `127.0.0.1` e no IP de rede do host (`ipconfig getifaddr en0` no macOS,
   `hostname -I` no Linux). Registar se está acessível.

**Valor:** nº de bindings internos em `todas` e em `loopback`.
**Mínimo:** `todas == 0`. **Alvo:** `todas == 0` e `loopback == 0`.

### 7.9 S05 — Operações legítimas

Lista fixa, 3 repetições, cada operação com a sua verificação:

1. o dono cria um projeto, carrega uma imagem e um vídeo de 10 MiB, adiciona `brightness`
   e aplica (`POST .../process`); recebe `process-update` no WS; o resultado descarrega;
2. o dono faz preview de uma imagem e recebe `preview-ready`;
3. o `reader` lê o projeto com `?share`; o `editor` adiciona uma ferramenta e remove um
   media com `?share`;
4. a quota do dono (free) diminuiu de acordo com o Apply e **não** com o upload (U24);
5. o dono consulta a sua subscrição (se o serviço existir);
6. o dono elimina o seu projeto.

O caso "editor elimina o projeto" é registado à parte como mudança de política
(ACL-C1): esperado permitido na BF e recusado na MF, e não conta como falha de S05.
**Critério:** 100% das operações acima.

### 7.10 S21 — Latência de pedidos leves

Depois de 10 pedidos de aquecimento, 100 pedidos sequenciais de cada tipo:
`GET api-gateway/projects/<uid>/<pid>` e `GET api-gateway/users/<uid>` (com JWT),
ligação HTTP reutilizada (`requests.Session`). Guardar todos os tempos.
**Valor:** mediana por tipo. Na `compare`: `Δ = mediana_MF − mediana_BF`.
**Critério:** Δ ≤ +10 ms (mínimo), ≤ +5 ms (alvo), em cada tipo.

---

## 8. Procedimentos por métrica — Upload

### 8.1 Corpus (`med.py corpus`)

A partir de `samples/video/sample_10s_720p.mp4`:

- **H** (`moov` no início): `ffmpeg -i sample -c copy -movflags +faststart h.mp4`, depois
  acrescentar no fim uma caixa MP4 `free` até ao tamanho exato.
- **T** (`moov` no fim): `ffmpeg -i sample -c copy t.mp4` (confirmar com a ordem das
  caixas que o `moov` fica depois do `mdat`); inserir a caixa `free` **logo a seguir ao
  `ftyp`**, para o `moov` continuar no fim.
- Tamanhos: 10, 100, 500 MiB (exatos: `N × 1048576` bytes); e 1024 MiB + 1 byte (H) para
  U18.
- Validar cada ficheiro com `ffprobe` (duração 10 s, h264) e guardar o SHA-256.
- Reais: `sample_6s.mov`, `speech_mandela_177s_1080p.webm`, `too_long_90s.mp4`,
  `corrupted.mp4`; um ficheiro de 0 bytes; uma PNG.

Limite free: 100 MiB (`VIDEO_FREE_MAX_SIZE_MB × 1024 × 1024`, `projects/utils/video.js`),
por isso 100 MiB exatos são válidos no free.

### 8.2 Estratos principais — U01, U08, U09, U10, U15, U17

Estratos (EVAL: 100 uploads normais):

| Perfil | Tamanhos | Posição | Estado | Tentativas |
|--------|----------|---------|--------|------------|
| free | 10, 100 MiB | H, T | frio, aquecido | 5 cada |
| premium | 10, 100, 500 MiB | H, T | frio, aquecido | 5 cada |

20 estratos × 5 = 100 tentativas. **Frio:** `docker compose restart api_gateway
projects img_storage` e prontidão antes da tentativa. **Aquecido:** um upload de
10 MiB descartado antes do estrato. Cada tentativa usa um projeto novo da mesma conta
(quota: o upload não consome operações; confirmar). Entre tentativas, 1,5 s; depois de
uma falha, 8 s.

Por tentativa, em simultâneo:

- upload instrumentado (§5.2) para `.../projects/<uid>/<pid>/video` com
  `X-Project-Version`;
- memória Node (§5.3) nos três serviços;
- amostrador do cgroup (§5.4) em `nginx` e `seaweedfs`;
- amostrador de disco (§5.5).

Depois de cada tentativa com 2xx:

- **U17:** `GET` do projeto: há exatamente 1 media novo com `media_type: "video"`;
- **U15:** `GET .../img/<mediaId>` → `url`; descarregar e calcular o SHA-256 em fluxo. Se
  o host da URL não for acessível a partir do host, descarregar a partir da sonda.
  Comparar com o SHA-256 do ficheiro enviado.

Valores:

| Métrica | Cálculo | Critério |
|---------|---------|----------|
| U01 | máx. `delta` por serviço e por tamanho (e mediana) | máx. ≤64 MiB (mínimo), ≤32 MiB (alvo) em todos os estratos |
| U08 | pico de disco por componente e resíduos 60 s depois do estrato | pico ≤ F + 16 MiB por componente e 0 resíduos (mínimo); ≤16 MiB e sem spool integral (alvo) |
| U09 | `post_send_ms` de cada tentativa premium de 500 MiB | todas <3000 ms (mínimo), todas <1000 ms (alvo) |
| U10 | mediana de `total_ms` por estrato | `compare`: ≤1,10× BF (mínimo), ≤ BF (alvo) |
| U15 | SHA-256 iguais / aceites | 100% |
| U17 | aceites corretamente / tentativas válidas | 100% |


### 8.2a U04 — memória do nginx e do SeaweedFS (revisão de 21/11)

O SeaweedFS (Go) fica com a memória que ocupou num upload e reutiliza-a nos seguintes.
Medido dentro dos estratos, o `pico − idle` depende do que veio antes: na BF de 21/11
deu +560–582 MiB nos dois uploads feitos com o SeaweedFS acabado de arrancar
(idle ~130 MiB) e ~0 nos restantes (idle 1,1–1,9 GiB). Por isso a U04 tem um passo
próprio, com o mesmo estado inicial em todas as amostras:

1. Reiniciar o `seaweedfs`, depois os serviços Node e o nginx (`restart_app`); esperar
   pela API e mais 5 s.
2. Upload premium de `pad_500MiB_H.mp4` (C=1) com os amostradores de cgroup (§5.4) no
   nginx e no seaweedfs.
3. Só contam amostras com upload aceite (2xx): se o gateway morrer antes, o ficheiro
   não chega ao SeaweedFS.
4. Repetir até 5 amostras válidas (máximo 40 tentativas; na base o gateway só sobrevive
   a uma minoria dos uploads de 500 MiB). Com `--resume`, as amostras já feitas com
   este método contam. Com menos de 5 válidas o resultado é INCONCLUSIVO.

| Métrica | Cálculo | Critério |
|---------|---------|----------|
| U04 | máx. (`pico − idle`) de `anon` no nginx e no seaweedfs, nas amostras válidas | ≤128/≤256 MiB (mínimo), ≤64/≤128 MiB (alvo) |
### 8.3 U18 — Uploads inválidos

3 repetições por caso, aquecido, com memória Node e eventos OOM recolhidos:

| Caso | Conta | Ficheiro | Esperado |
|------|-------|----------|----------|
| I1 | free | PAD H 500 MiB | 4xx (tamanho), nenhum media |
| I2 | free | `too_long_90s.mp4` | 4xx (duração) |
| I3 | free | `corrupted.mp4` | 4xx |
| I4 | free | 0 bytes | 4xx |
| I5 | free | PNG para `/video` | 4xx |
| I6 | premium | PAD H 1024 MiB + 1 byte | 4xx (tamanho) |
| I7 | free | `speech_mandela_177s_1080p.webm` (>60 s) | 4xx |

Verificar: código 4xx, o número de media do projeto não mudou, nenhum OOM/reinício.
**Valor:** recusas corretas / casos. **Critério:** 100% e 0 OOM.

### 8.4 U19 — Upload sem token

5 repetições: PAD H 500 MiB para
`.../projects/000000000000000000000000/000000000000000000000000/video`, sem
`Authorization`, com `rate_limit_mib_s = 50` (~10 s de envio) e leitura da resposta
durante o envio (§5.2). Variante com JWT de assinatura errada (3 repetições).

Recolher: `status`, `t_first_byte − t_headers`, `bytes_sent_at_response`, `delta` do
gateway (§5.3), pico de `anon` e de disco do nginx.
**Mínimo:** 401/403 e `delta` do gateway ≤8 MiB. **Alvo:** `t_first_byte − t_headers`
≤100 ms. Os bytes aceites pelo nginx reportam-se à parte (buffering).

### 8.5 U20 — Concorrência C=3

3 rondas. Em cada ronda: aquecido; 3 contas premium, cada uma com um projeto novo; 3
uploads PAD H 500 MiB iniciados ao mesmo tempo (threads, barreira de arranque).
Amostrador do cgroup em todos os contentores medidos durante a ronda; eventos OOM e
reinícios antes e depois; U15/U17 para cada upload.
**Valor:** sucessos/3 por ronda, OOM, reinícios, pico agregado.
**Mínimo:** 3/3 numa ronda, 0 OOM, 0 reinícios, SHA-256 100%. **Alvo:** 3/3 nas 3 rondas.
Entre rondas, 30 s; depois de uma falha, `restart` dos serviços e prontidão.

### 8.6 U25 — Pedidos leves durante uploads

3 pares (controlo, carga) na mesma campanha:

- **Controlo:** 100 pedidos leves a 10 pedidos/s, alternando `GET users/<uid>` e
  `GET projects/<uid>/<pid>` de uma conta que não está a carregar nada.
- **Carga:** os mesmos 100 pedidos enquanto correm 3 uploads PAD H 500 MiB com
  `rate_limit_mib_s = 40` cada (~12,5 s, igual na BF e na MF), começando 1 s depois do
  início dos uploads. Só contam os pedidos iniciados com pelo menos um upload ativo; se
  forem menos de 100, a repetição é refeita.

Recolher todos os tempos e erros (incluindo ligações recusadas e 5xx).
**Valor:** erros e `mediana_carga / mediana_controlo` por par.
**Mínimo:** 0 erros e razão ≤1,10 em cada par. **Alvo:** razão ≤1,00.

---

## 9. Resultados

### 9.1 Bruto (`raw/<METRICA>.jsonl`)

Uma linha por tentativa, por exemplo:

```json
{"metric":"U01","campaign":"BF","stratum":"premium-500-H-warm","attempt":3,
 "upload":{"status":204,"post_send_ms":6923.1,"total_ms":10525.4,"bytes":524288000},
 "mem":{"api_gateway":{"rss_pre_mib":283.6,"peak_mib":2049.6,"delta_mib":1766.0,
        "oom_killed":false,"restarted":false}},
 "cgroup":{"nginx":{"idle_anon_mib":5.1,"peak_anon_mib":9.8}},
 "disk":{"projects":{"peak_kib":512000,"residual_kib":0}},
 "sha256_ok":true,"t_utc":"2026-11-21T10:00:00Z"}
```

### 9.2 Resumo (`summary.json`)

Por métrica: `id`, `valor` (com o cálculo usado), `n`, `minimo`, `alvo` (lidos de
`criteria.yaml`), `estado ∈ {CUMPRE_ALVO, CUMPRE_MINIMO, NAO_CUMPRE, INCONCLUSIVO,
NAO_MEDIDA}`, `inconclusivos`, `notas`. Métricas comparativas (S21, U10) só recebem
estado em `compare`. Mapear também para o modelo
[`phase2-evaluation-result.template.json`](templates/phase2-evaluation-result.template.json).

### 9.3 Relatório (`report.md`) e `compare`

`report.md`: uma tabela por RNF (métrica, valor, mínimo, alvo, estado) e as notas.
`compare <BF> <MF>`: tabela BF | MF | estado, mais avisos se os manifestos diferirem
em host (CPU, arquitetura, CPUs e memória do Docker), limites, corpus, matriz de casos,
`criteria.yaml` ou **versão do instrumento** (hash de `med.py`, `medlib/`, critérios,
casos, imagem de sonda e dependências). **Qualquer diferença bloqueia a classificação de
todas as métricas** (`COMPARACAO_INVALIDA`): a MF tem de ser repetida nas condições da
BF. Nas matrizes, um número de tentativas diferente entre BF e MF dá INCONCLUSIVO.

**Versão do instrumento da BF.** Se o `med.py` mudar depois da BF sem invalidar os
dados brutos (só resumos/avaliação, ou passos medidos de novo com `--resume`), regista-se
a nova versão com `med.py freeze <BF> --motivo "..."`. O manifesto guarda o histórico
(`instrumento_historico`) e a MF tem de correr exatamente com a versão congelada.
A BF de 21/11 foi congelada depois da correção dos resumos U09/U10, da nova medição da
U04 e das correções de avaliação de 21/11 (notas 17–22 de `IMPLEMENTATION_NOTES.md`).

**Regras de avaliação reforçadas (21/11).** Matriz sem tentativas ou sem controlos →
INCONCLUSIVO. U20 → NAO_CUMPRE com qualquer OOM, mesmo havendo rondas 3/3. S05 na MF →
NAO_CUMPRE se o editor ainda eliminar o projeto (ACL-C1) ou se esse caso não correr.

## 10. `criteria.yaml` (transcrição de metricas.md)

```yaml
S01: {tipo: principal, unidade: admitidos, minimo: 0, alvo: 0}
S02: {tipo: principal, unidade: admitidos, minimo: 0, alvo: 0, por_superficie: true}
S03: {tipo: principal, unidade: admitidos, minimo: 0, alvo: 0}
S04: {tipo: principal, unidade: eventos_ou_entradas, minimo: 0, alvo: 0}
S12: {tipo: principal, unidade: ms, minimo: 5000, alvo: 2000, eventos_apos_limite: 0}
S16: {tipo: principal, unidade: admitidos, minimo: 0, alvo: 0}
S17: {tipo: principal, unidade: admitidos, minimo: 0, alvo: 0}
S18: {tipo: principal, unidade: bindings, minimo: {todas: 0}, alvo: {todas: 0, loopback: 0}}
S05: {tipo: guarda, unidade: fracao, minimo: 1.0, alvo: 1.0}
S21: {tipo: guarda, unidade: delta_ms_mediana, minimo: 10, alvo: 5, comparativa: true}
U01: {tipo: principal, unidade: MiB, minimo: 64, alvo: 32, por_servico: true}
U20: {tipo: principal, unidade: sucessos, minimo: {rondas_3de3: 1, oom: 0}, alvo: {rondas_3de3: 3, oom: 0}}
U19: {tipo: principal, minimo: {status: [401, 403], gateway_delta_mib: 8}, alvo: {resposta_ms: 100}}
U18: {tipo: principal, unidade: fracao, minimo: 1.0, alvo: 1.0, oom: 0}
U04: {tipo: principal, unidade: MiB, minimo: {nginx: 128, seaweedfs: 256}, alvo: {nginx: 64, seaweedfs: 128}}
U08: {tipo: principal, minimo: {pico: "F+16MiB por componente", residuos: 0}, alvo: {pico_mib: 16, residuos: 0}}
U09: {tipo: guarda, unidade: ms, minimo: 3000, alvo: 1000, todas_as_amostras: true}
U25: {tipo: guarda, minimo: {erros: 0, razao: 1.10}, alvo: {erros: 0, razao: 1.00}}
U15: {tipo: guarda, unidade: fracao, minimo: 1.0, alvo: 1.0}
U17: {tipo: guarda, unidade: fracao, minimo: 1.0, alvo: 1.0}
U10: {tipo: guarda, unidade: razao_mediana_BF, minimo: 1.10, alvo: 1.00, comparativa: true}
```

## 11. Aceitação do `med.py` (antes de correr a BF)

1. `preflight` falha se o projeto não for `picturas-nfr[-<sufixo>]` ou se o disco tiver
   <60 GiB.
2. Um ensaio rápido (`--metrics S01,U01 --quick`: 1 repetição, só 10 MiB) corre do
   início ao fim e produz `manifest.json`, `raw/`, `summary.json` e `report.md`.
3. Uma pesquisa nos resultados por partes conhecidas de segredos (`lisan_al_gaib`,
   `admin123`, `password`, prefixos de JWT `eyJ`) não encontra nada.
4. Na base, o ensaio rápido reproduz os efeitos já conhecidos: G03/G04 `ADMITIDO`, W01
   `ADMITIDO`, U01 do gateway a 10 MiB claramente acima de 0. Se não reproduzir,
   corrigir o instrumento antes da BF, e não os critérios.
5. Tempo estimado de uma campanha completa: ~2–3 h (o upload domina). Registar a duração
   real no manifesto.

## 12. Espaço em disco e limpeza

**Os 60 GiB são um mínimo de espaço livre antes de começar, não o consumo do teste.**
Servem de margem para que o disco cheio nunca seja a causa de uma falha medida (um
upload que falha por falta de disco estragaria U17/U20 sem relação com o código).
Consumo estimado de uma campanha:

| Item | Tamanho aproximado | Quando apagar |
|------|--------------------|---------------|
| Imagens Docker da stack `picturas-nfr` (todas as ferramentas, IA e Whisper) | ~15 GB | Imagens da BF: depois de a BF estar validada. Imagens da MF: no fim do projeto |
| Volumes da stack (S3 com os uploads aceites, Mongo, RabbitMQ) | ~25 GiB (100 uploads normais ≈ 14 GiB, U20 ≈ 4,5 GiB, U25 ≈ 4,5 GiB, resto) | No fim de cada campanha (`stack down` já usa `-v`) |
| Corpus (`evaluation/.corpus/`) | ~2,5 GiB | **Só depois da MF**: a MF tem de usar exatamente os mesmos ficheiros (SHA-256 no manifesto) |
| Temporários do nginx e do `projects` durante os uploads | até ~3 × 500 MiB em simultâneo | Libertados pela aplicação; medidos em U08 |
| Resultados (`evaluation/results/`) | poucos MiB | **Nunca**: são a evidência entregue |

Comando `python evaluation/med.py stack purge` (depois de `stack down`):

1. remove os volumes e as redes com a etiqueta `com.docker.compose.project=picturas-nfr`;
2. remove as imagens construídas por esse projeto (`picturas-nfr-*`) e a imagem
   `picturas-med-probe`;
3. com `--corpus`, apaga também `evaluation/.corpus/` (pede confirmação e recusa se
   ainda não existir uma campanha MF em `results/`);
4. mostra o espaço livre antes e depois.

**Proibido:** `docker system prune`, `docker volume prune`, `docker image prune -a` ou
`docker builder prune` sem filtro. Apagam também os contentores, imagens e volumes da
outra instalação `picturas` desta máquina. Limpar a cache de build global só com
autorização explícita de quem administra a máquina.

**Docker Desktop (macOS):** apagar volumes liberta espaço dentro da VM, mas o ficheiro
`Docker.raw` do host pode não encolher logo. Se o espaço livre do macOS não voltar,
usar *Settings → Resources → Disk usage limit* ou *Troubleshoot → Clean / Purge data*,
**só** com a confirmação de que não há dados da outra instalação a preservar.

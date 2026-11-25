# Fase 2 — Resultados dos spikes do B0

[Índice da documentação](README.md) · [Plano](refactor-plano.md) · [Passagem](refactor-handoff.md) · **Equipa: PL2-G4**

Cada spike confirma uma hipótese técnica de que o desenho depende ([plano, B0](refactor-plano.md#b0--preparação-e-spikes-de-compatibilidade-sem-alterar-o-produto)).
O resultado é um de: **suportado**, **suportado com limitações** ou **não suportado**.
As limitações que mudam um bloco abrem uma dúvida na §5 do
[handoff](refactor-handoff.md#5-dúvidas-surgidas-durante-a-implementação).

Regras dos ensaios:
- correm num projeto Compose próprio (`picturas-spike`), nunca no `picturas-nfr`;
- usam uma PKI descartável gerada por script (as chaves ficam fora do Git);
- os harness e o bruto ficam em `tests/spikes/SP-xx/` (`results/` com as saídas).

| # | Hipótese | Resultado | Blocos afetados |
|---|----------|-----------|-----------------|
| SP-01 | nginx: `auth_request`, `proxy_request_buffering off`, `proxy_ssl_verify` | **Suportado**, com 4 notas de configuração | B5, B6, B7 |
| SP-02 | SeaweedFS: HTTPS no S3 e no filer, credenciais e permissões por principal | **Suportado com limitações** (variáveis `AWS_*` criam um admin; `Write` inclui `DELETE`) | B2 |
| SP-03 | SeaweedFS: tamanho assinado, PUT interrompido, chunked, CopyObject (tempo de 500 MiB) | **Suportado**; a escolha do D-14 ficou ambígua → **D-16** | B6, B7 |
| SP-04 | SigV4 com o `Host` interno através do nginx | **Suportado** | B7 |
| SP-05 | `ffprobe` por URL HTTPS interno, `moov` no início/fim, 500 MiB | **Suportado com limitações**: o `ffprobe` não limita os bytes totais → **D-17** | B6 |
| SP-06 | MongoDB 4.4: `requireTLS`, utilizadores por serviço, `mongodump` com TLS | **Suportado** | B2 |
| SP-07 | RabbitMQ: TLS, utilizadores/permissões por fila, `pika` e `amqplib` | **Suportado com limitações**: com o exchange `direct` não se limita a publicação por fila → **D-18** | B2 |
| SP-08 | Watermark derivado por AMQPS | **Suportado** | B2 |
| SP-09 | Next.js a servir HTTPS ao nginx | **Suportado** (com `proxy_ssl_session_reuse off`) | B5, B10 |
| SP-10 | Flask (generative-mock) e `requests` (expand_ai) com mTLS | **Suportado** | B5 |
| SP-11 | Componentes internos do SeaweedFS com TLS | **Suportado com limitações**: o HTTPS do master/volume/filer aceita qualquer certificado da CA → **D-19** | B2 |

Outras tarefas do B0 (imagens fixadas, `tests/conformance/`, F01): [no fim](#outras-tarefas-do-b0).

---

## SP-01 — nginx: `auth_request`, `proxy_request_buffering off`, `proxy_ssl_verify`

**Resultado: suportado**, com quatro notas de configuração que o B5, o B6 e o B7 têm de seguir.

- **Data:** 2026-11-21, no Mac das medições (Docker Desktop 28.5.1, arm64).
- **Imagem:** `nginx@sha256:84f7876d21d154885f99554d7ae325d8c2213f9169726ea7ab60642f2573a787`
  (a mesma da BF), `nginx/1.31.9`, compilada com `--with-http_auth_request_module` e
  `--with-http_ssl_module`.
- **Harness:** `tests/spikes/SP-01/`, com o `compose.yaml` (projeto `picturas-spike`) e o
  `nginx.conf` do ensaio. O `srv.py` faz três papéis: serviço de autorização, recetor
  que regista quando chegam os cabeçalhos e os bytes, e backend HTTPS com mTLS
  obrigatório. A PKI vem do `gen-pki.sh`: uma CA da instalação e uma CA estranha.
- **Para repetir:** `./gen-pki.sh && docker compose up -d && bash run-1-auth-stream-tls.sh`
  (e `run-2…4`). O bruto está em `results/run-1..4.out`.

### Evidência

Os corpos de teste têm 20 MiB e são enviados a 2 MiB/s (`curl --limit-rate 2M`), o que
dá cerca de 10 s por envio. `t` é o tempo total visto pelo cliente; `up` são os bytes
que o cliente chegou a enviar.

| Caso | Configuração | Resultado |
|------|--------------|-----------|
| A1–A3 | `auth_request` com o JWT bom, mau ou ausente | 201 / 401 / 401 |
| A4 | Autorização recusada, corpo de 20 MiB | **401 em 0,032 s, `up`=65 KiB**: recusa antes do corpo |
| B1 | Autorização aceite, `proxy_request_buffering off` | O recetor recebe os cabeçalhos **0,019 s** depois do início e o último byte aos 10 s: streaming |
| B2 | Controlo com buffering por omissão | O recetor só recebe os cabeçalhos aos **10,0 s** (o nginx guardou o corpo antes) |
| B3 | Cliente `Transfer-Encoding: chunked`, sem buffering | 201; o corpo passa em fluxo; o `$content_length` que chega à autorização vem vazio |
| B4 | `Content-Length` de 1200 MiB, acima do `client_max_body_size 1100m` da localização | 413 imediato, com o JWT bom ou mau (o 413 é decidido antes do `auth_request`) |
| D3 | Ficheiros em `client_temp`, aos 3 s do envio (por `/proc/*/fd` do worker) | Sem buffering: **0** (também com chunked). Controlo com buffering: **1 ficheiro com 6,6 MB** |
| D2 | Serviço de autorização lento (5 s > `proxy_read_timeout 2s`) | 500 aos 2,0 s; o pedido **não** chega ao recetor |
| D5 | Serviço de autorização parado | 500 (`auth request unexpected status: 504`); o pedido não chega ao recetor |
| D1 | Recusa com outro código (403 + `X-Deny-Status`, `error_page 403 = @named`), named location com `proxy_pass` | Códigos certos (403/404/409/410/411/413/429/503), **mas só aos 10 s, com os 20 MiB lidos** |
| D1' | A mesma recusa, mas a named location usa `if ($deny_status = N) { return N …; }` | Códigos certos em **0,033 s, `up`=65 KiB** |
| C1 | `proxy_ssl_verify on`, CA da instalação, `proxy_ssl_name backend`, certificado de cliente | 200; o backend vê `peer=nginx-client` (mTLS) |
| C2 | Nome esperado errado (`proxy_ssl_name projects`) | 502 (`upstream SSL certificate does not match "projects"`) |
| C3 | Upstream com um certificado de outra CA | 502 (`unable to verify the first certificate`) |
| C4 | Upstream com mTLS obrigatório, mas o nginx sem certificado de cliente | 502 |
| C5 | Controlo com a verificação desligada, contra o upstream da outra CA | 200: sem `proxy_ssl_verify on` o nginx aceita qualquer servidor |
| D4 | Streaming (`proxy_request_buffering off`) para um upstream HTTPS verificado, com mTLS | 200; o backend recebe os cabeçalhos 0,04 s depois do início e os 20 MiB em fluxo |
| — | `proxy_pass` com variável e `resolver 127.0.0.11` (`/uploads/`) | Funciona |

### Notas para os blocos

1. **A localização interna de autorização precisa do mesmo `client_max_body_size` que a
   localização de upload.** A subrequest herda o limite do servidor e compara-o com o
   `Content-Length` do pedido original. Com o limite global baixo (1 MiB no ensaio), um
   PUT de 20 MiB dava **500** (`client intended to send too large body … subrequest:
   "/_auth"` e `auth request unexpected status: 413`). Corrige-se pondo
   `client_max_body_size` na `location = /_auth` (B6, B7).
2. **A subrequest do `auth_request` é sempre um `GET`.** O método original passa-se por
   cabeçalho (`X-Original-Method $request_method`), tal como o URI e o comprimento
   (`X-Original-URI`, `X-Original-Length $content_length`). A rota interna do gateway não
   pode decidir pelo método da linha de pedido (B7).
3. **O `auth_request` só propaga 401 e 403; qualquer outro código dá 500.** Os códigos
   409/410/411/413/429/503 do B7 ("o `auth_request` tem o seu próprio mapeamento")
   fazem-se assim: a autorização responde 403 com `X-Deny-Status`, e um `error_page 403
   = @auth_denied` faz o mapeamento com `return` literais. **Não** se usa `proxy_pass`
   nessa named location: o nginx lê o corpo inteiro antes de responder (caso D1, 10 s).
   Uma falha ou timeout da autorização dá 500 e nunca encaminha o pedido (fail-closed,
   sem confundir 5xx com recusa). O pedido chunked chega à autorização com
   `X-Original-Length` vazio, e a autorização recusa-o com 411 por este mapeamento
   (o B7 exige comprimento conhecido).
4. **O 413 do `client_max_body_size` vem antes do `auth_request`.** Um pedido acima de
   1 GiB recebe 413 mesmo sem JWT. A recusa continua a ser feita antes do corpo, por
   isso é aceitável, mas a ordem fica registada para os testes do B7 (o caso "sem JWT e
   acima do limite" espera 413, não 401).

Armadilha do ensaio, sem efeito no produto: num bind mount de um só ficheiro, um editor
que substitui o inode (por exemplo `perl -i`) deixa o contentor com a versão antiga. Para
recarregar, recria-se o contentor.

---

## SP-02 — SeaweedFS: HTTPS no S3 e no filer, credenciais e permissões por principal

**Resultado: suportado com limitações.**

- **Imagem:** `chrislusf/seaweedfs@sha256:ce9e796f…` (a da BF, `4.47 c50733600`).
- **Configuração:** `weed server` com `-s3.cert.file/-s3.key.file`, `-s3.config=s3.json`
  (identidades por ação e bucket/prefixo) e `security.toml` com `[https.filer]`,
  `[https.volume]`, `[https.master]` e `[https.client]`.
- **Harness:** `tests/spikes/SP-02/` (`compose.yaml`, `s3.json`, `security.toml`,
  `matrix.py`). Bruto em `results/matrix-1..3`.

| Caso | Resultado |
|------|-----------|
| S3 em HTTPS com a CA da instalação | Funciona. HTTP simples na 9000: 400. CA errada: falha de verificação |
| Filer em HTTPS (8888) | Exige certificado de cliente: sem certificado, o handshake falha; com um certificado da CA, 200. HTTP simples: 400 |
| `img_storage` (`Read/Write/List/Tagging:picturas`) | PUT, GET, HEAD, List, Copy e Delete em `picturas`: aceites. CreateBucket (o B2 do `med.py`), DeleteBucket, PutBucketPolicy, PutBucketAcl e acesso a outro bucket: **403**. `ListBuckets` só mostra `picturas` |
| `uploader` (`Write:picturas/staging/*`) | PUT em `staging/`: aceite. PUT fora de `staging/`: 403. GET e List: 403. **DELETE em `staging/`: aceite** |
| `reader_src` (`Read:picturas/users/*`) | GET em `users/`: aceite. GET em `staging/` e PUT: 403 |
| URL assinado GET (`img_storage`) e PUT (`uploader`) | 200. PUT assinado fora do prefixo: 403. GET/PUT anónimos: 403 |
| `admin/admin123` (credencial do Git, o B1 do `med.py`) | **Aceite enquanto o contentor tiver `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`**; sem essas variáveis: `InvalidAccessKeyId` |

Notas para o B2:
1. **As variáveis `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` acrescentam uma identidade
   admin**, mesmo com `-s3.config` (log: `Added admin identity from AWS environment
   variables`). Têm de sair do serviço `seaweedfs`; o admin passa a estar só no `s3.json`,
   montado a partir dos segredos.
2. **A ação `Write` inclui o `DELETE`** (e o multipart); não há uma ação só de PUT nas
   identidades simples. Um URL assinado fica preso ao método (ver SP-04), por isso o
   risco é o vazamento da credencial do principal, que fica só no servidor.
3. **Ativar o `[https.client]` obriga a HTTPS também no volume e no master.** Com o volume
   em HTTP, todos os PUT davam 500 (`server gave HTTP response to HTTPS client`).
4. O arranque regista `Failed to load IAM configuration: no signing key found for STS
   service`. É o IAM avançado (STS), que não usamos; as identidades do `s3.json` funcionam.
5. Observação: a variável `WEED_S3_SSE_KEK_PASSPHRASE` do compose atual não é reconhecida
   pela 4.47 (`SSE-S3 encryption is disabled`). O `-s3.encryptVolumeData` é outra coisa e
   continua ativo. Não altera os RNF; fica registado.
6. Observação: o `nginx/nginx.conf` atual publica o filer em `/s3-console/` sem
   autenticação. O B2/B3 tem de o retirar (D1).

## SP-03 — SeaweedFS: tamanho assinado, PUT interrompido, chunked e CopyObject

**Resultado: suportado.** O tempo e a memória do CopyObject de 500 MiB deixam a decisão
do D-14 ambígua: aberta a **D-16**.

- **Configuração:** a do SP-02 (TLS em todos os componentes, `-s3.encryptVolumeData`),
  ou seja, a configuração prevista para a MF.
- **Harness:** `tests/spikes/SP-03/`. Bruto em `results/sp03-1..5`.

| Caso | Resultado |
|------|-----------|
| URL assinado **SigV4** com `ContentLength=1000` (`X-Amz-SignedHeaders=content-length;host`) | 1000 bytes: 200. 2000 bytes: **403**. 500 bytes: **403**. Corpo chunked sem `Content-Length`: **403**. Nenhum objeto fica criado |
| URL assinado SigV4 sem `ContentLength` | Aceita qualquer tamanho (2000 bytes: 200). **O comprimento só é imposto se estiver assinado** |
| URL assinado com SigV2 (o boto3 por omissão, sem `s3v4`) | O comprimento não é assinado: aceita qualquer tamanho. Usar sempre SigV4 |
| URL expirado, chave alterada, PUT usado como DELETE | 403 |
| PUT interrompido (CL=100 MiB, 10 MiB enviados, ligação fechada) | **Nenhum objeto visível** (1 s, 5 s, 15 s). Se a chave já existia, o objeto anterior fica intacto |
| Chunked interrompido | Nenhum objeto visível |
| Chunked completo, sem comprimento assinado | Aceite |
| CopyObject → depois alterar a origem → depois apagar a origem | A cópia mantém o SHA-256 original nas duas situações: **cópia imutável** |
| CopyObject de 500 MiB (12 medições) | 330–613 ms em 10 medições; **6206 ms e 6333 ms** em 2 |
| Memória anónima do SeaweedFS, reiniciado antes de cada amostra (3 amostras) | O **PUT direto** de 500 MiB já sobe **+428 a +483 MiB**; o CopyObject seguinte leva o pico a +506 a +603 MiB (**+78 a +120 MiB** acima do pico do PUT) |

Os dois valores de cerca de 6 s coincidem com o crescimento de volumes do SeaweedFS: os
volumes ficam `crowded` e o master cria volumes novos 6 s depois
(`results/sp03-5-volume-growth.log`). Não é um efeito próprio da cópia, mas a cópia
duplica os bytes escritos e, com isso, a frequência destes crescimentos. Também afeta o
PUT direto.

Leitura para o D-14: no caso típico, a cópia cabe no mínimo da U09 (<3000 ms), mas gasta
até 61% do alvo (<1000 ms). Nos crescimentos de volume, a U09 falha. Acrescenta ainda
cerca de 100 MiB ao pico do SeaweedFS na janela da U04. Ver a D-16.

Observação para o D-10 e o B6: sem a cópia, o PUT direto de 500 MiB nesta configuração
já sobe a memória do SeaweedFS **+428 a +483 MiB**, acima do mínimo da U04 (≤256 MiB). A
U04 depende do spike de `GOMEMLIMIT`/`GOGC` (D-10).

## SP-04 — SigV4 com o `Host` interno através do nginx

**Resultado: suportado.**

- **Harness:** `tests/spikes/SP-04/`. Um `signer.py` faz o papel da rota de autorização: devolve o
  caminho do URL assinado para `seaweedfs:9000`, o nginx recebe-o por `auth_request_set`
  e encaminha com `proxy_pass https://seaweedfs:9000$s3_uri`. Bruto em `results/sp04.out`.

| Caso | Resultado |
|------|-----------|
| `proxy_set_header Host seaweedfs:9000`, `Authorization` limpo, 1000 bytes | 200; objeto criado |
| Chave com espaços, `+`, `ç` e parênteses | 200; a chave fica exata (o URL assinado passa sem ser normalizado, porque o `proxy_pass` usa uma variável) |
| Comprimento assinado 1000, cliente envia 2000 | 403 `SignatureDoesNotMatch` |
| 20 MiB em fluxo (`proxy_request_buffering off`) | 200 |
| `Host` público encaminhado (`$host`) | 403 `SignatureDoesNotMatch` |
| `Authorization: Bearer <JWT>` do cliente encaminhado ao S3 | 200 (o SeaweedFS usa a assinatura da query), mas o JWT não deve chegar ao S3: limpa-se |
| `/s3/` com `limit_except GET HEAD`: GET / Range / PUT | 200 / 206 (100 bytes) / 403 |
| HEAD com um URL assinado para GET; HEAD com um URL assinado para HEAD | 403; 200 (a assinatura SigV4 inclui o método) |

Notas para o B2 e o B7: o `Host` encaminhado tem de ser o assinado (`seaweedfs:9000`) e o
`Authorization` do cliente limpa-se. O critério do B2 "HEAD com URL assinado válido"
usa um URL assinado para HEAD.

## SP-05 — `ffprobe` por URL HTTPS interno

**Resultado: suportado com limitações.** O `ffprobe` impõe tempo, mas não um limite de
bytes totais: aberta a **D-17**.

- **Binário:** o `ffprobe` da imagem `projects` da BF (`7.1.5-0+deb13u1`), num contentor
  descartável na rede do spike.
- **Corpus:** `pad_500MiB_H.mp4` e `pad_500MiB_T.mp4` do `med.py` (`moov` no início / no
  fim) e `sample_6s.mov`, num URL assinado SigV4 servido pelo SeaweedFS em HTTPS.
- **Opções:** `-protocol_whitelist https,tls,tcp -tls_verify 1 -ca_file <CA>
  -max_redirects 0 -rw_timeout 5000000 -reconnect 0`, dentro de `timeout 20`.
- **Medição:** bytes pelo `rx_bytes` da interface do contentor (inclui o overhead TLS).
- **Harness:** `tests/spikes/SP-05/`. Bruto em `results/sp05.out` (assinaturas redigidas).

| Caso | Resultado |
|------|-----------|
| 500 MiB, `moov` no início (3×) | rc=0; **185–291 ms; 380–687 KB lidos**; h264/aac 1280×720, 10 s |
| 500 MiB, `moov` no fim (3×) | rc=0; **234–247 ms; 398–584 KB lidos** |
| `sample_6s.mov` (3×) | rc=0; 136–141 ms; 134 KB |
| CA errada / nome errado (`-verifyhost projects`) | rc=1 (`Peer certificate failed verification` / `owner does not match hostname`) |
| URL `http://` | rc=1 (`Protocol 'http' not on whitelist`) |
| Redirect com `-max_redirects 0` | rc=1. Controlo com o valor por omissão (8): segue o redirect |
| Servidor que pára de enviar | rc=1 aos 5,35 s (`rw_timeout`) |
| URL com a assinatura alterada | rc=1 (403) |

Notas para o B6:
1. **Limite de leitura (UP-C8: até 2×F+16 MiB):** o `ffprobe` não tem nenhuma opção de
   bytes totais. O `-probesize` limita a análise de streams, não a leitura do `moov`, e o
   `rw_timeout`/`timeout` limitam o tempo. A ~1 GB/s do SeaweedFS, o tempo não limita os
   bytes. Ver a D-17.
2. **Nos erros, o `ffprobe` escreve no stderr o URL assinado inteiro** (assinatura e
   credencial incluídas). A `projects` não pode registar o stderr tal como vem: redige-o
   ou descarta-o (plano §1, regra 6).

## SP-06 — MongoDB 4.4: `requireTLS`, utilizadores por serviço, `mongodump` com TLS

**Resultado: suportado.**

- **Imagem:** `mongo@sha256:4be76f67…` (a da BF, `4.4.30`, OpenSSL 1.1.1f).
- **Arranque:** `--tlsMode requireTLS --tlsCertificateKeyFile --tlsCAFile
  --tlsAllowConnectionsWithoutCertificates` (os clientes validam o servidor; não há mTLS,
  conforme a opção A). O `docker-entrypoint-initdb.d` funciona com `requireTLS`.
- **Harness:** `tests/spikes/SP-06/` (`init.js` cria `projects_svc` com `readWrite` em
  `projects` e `backup_ro` com `read` em `projects`). Bruto em `results/sp06-1..3`.

| Caso | Resultado |
|------|-----------|
| Sem TLS (com ou sem credenciais) | Ligação fechada pelo servidor |
| CA errada / ligação por IP (nome fora do SAN) | `CERTIFICATE_VERIFY_FAILED` / `IP address mismatch` |
| TLS sem credenciais (o caso a do `med.py`) | `requires authentication` |
| `projects_svc`: find/insert na sua BD | Aceites |
| `projects_svc`: `listDatabases` | Aceite, mas só devolve `['projects']` (o caso d2 do `med.py` classifica como "só vê a sua BD") |
| `projects_svc`: insert noutra BD, `admin.system.users`, `createUser`, `dropDatabase`, `serverStatus` | Todos `not authorized` |
| `backup_ro`: find / insert | Aceite / `not authorized` |
| `mongodump` 100.10.0 com `tls=true&tlsCAFile=…` | Funciona; sem TLS ou com a CA errada, falha |
| `mongorestore` de uma fixture (admin, TLS) para outra BD | 2 documentos restaurados e conferidos; com `backup_ro`: 0 restaurados |

Notas para o B2:
1. **Quando falha, o `mongodump` escreve o URI completo, com a palavra-passe.** Com a
   palavra-passe num ficheiro `--config` (`password: …`, modo 600) e o URI sem
   palavra-passe, a mensagem de erro já não a mostra (`results/sp06-3.out`). O serviço de
   backup usa esta forma.
2. O utilizador de backup é um por instância, com `read` na sua BD. O `mongodump --db`
   não precisa de mais.
3. No bruto, os `rc=0` do `sp06-2.out` vêm do `| tail`. O texto mostra as falhas.

## SP-07 — RabbitMQ: TLS, utilizadores e permissões por fila, `pika` e `amqplib`

**Resultado: suportado com limitações.** Com o exchange `direct` atual, a permissão
`write` não se consegue limitar por fila de destino: aberta a **D-18**.

- **Imagem:** `rabbitmq:4.0.5-management` (a base do `rabbitMQ/Dockerfile`).
- **Clientes:** `pika` 1.3.2 (o dos Tools) e `amqplib` 0.10.9 com Node 26.13.1 (a imagem
  `projects` da BF).
- **Harness:** `tests/spikes/SP-07/` (`rabbitmq.conf`, `definitions.json`, `users.sh`,
  `sp07.py`, `sp07.js`). Bruto em `results/sp07-1..3`.

| Caso | Resultado |
|------|-----------|
| AMQP simples (5672) com `listeners.tcp = none` | Recusado (porta fechada) |
| AMQPS com a CA errada / nome fora do SAN | Recusado no `pika` e no `amqplib` (`servername` verificado) |
| `user/password` (Git) e `guest/guest` | `ACCESS_REFUSED` |
| Worker: consumir a sua fila; `queue_declare`/`exchange_declare` passivos | Aceites |
| Worker: `exchange_declare` **ativo** de `picturas` (o que o `Tools/utils/rabbit_mq.py` faz hoje) | **403** sem `configure` no exchange |
| R3 (worker lê `ws_queue`), R4 (declarar e apagar uma fila canário), apagar o exchange | 403 |
| R5 (worker na API de gestão HTTPS) | 401 |
| Worker com `configure` na sua fila: apagar a própria fila | Aceite. Com `configure "^$"` e declarações passivas: recusado |
| **Worker publica em `picturas` (direct) com routing key `video_queue` / `ws_queue`** | **Aceite** (a permissão `write` aplica-se ao exchange, não à routing key) |
| Worker publica no exchange por omissão para `ws_queue` | 403 |
| Exchange **`topic`** com `set_topic_permissions … "^project_queue$"`: publica para `project_queue` / `video_queue` | Aceite / **403** |
| `amqplib`: 403 num canal sem handler `error` | **O processo Node termina** (`Unhandled 'error' event`); com handlers, a ligação continua utilizável |

Endurecimento dos listeners (configuração final em `rabbitmq.conf` e `compose.yaml`):
- `management.tcp.port = 0` **não desliga** a API HTTP: abre-a em HTTP simples numa porta
  efémera (encontrada na 33927, com resposta 401). Basta configurar só o
  `management.ssl.*` para ficar apenas a 15671 em HTTPS.
- `prometheus.tcp.ip = 127.0.0.1`, e `ERL_EPMD_ADDRESS=127.0.0.1` com
  `inet_dist_use_interface {127,0,0,1}` e `RABBITMQ_NODENAME=rabbit@localhost`. Assim,
  4369, 25672 e 15692 ficam só em loopback. Da rede só se alcançam a 5671 (AMQPS) e a
  15671 (HTTPS de gestão). O `rabbitmqctl status` (healthcheck) continua a funcionar.

Notas para o B2:
1. Os clientes passam a declarações passivas (`exchange_declare/queue_declare
   passive=True`, `checkExchange/checkQueue`), e os workers ficam com `configure "^$"`.
   As filas e o exchange vêm do `definitions.json`.
2. O `projects/utils/rabbit_mq.js` e o `ws_gateway` precisam de handlers `error` na
   ligação e nos canais. Hoje um 403 ou uma queda do broker matam o processo.
3. O `rabbitmqctl` corre como utilizador `rabbitmq`. Como root, antes de o servidor
   arrancar, cria um `.erlang.cookie` do root e o broker deixa de arrancar (`eacces`).

## SP-08 — Watermark derivado por AMQPS

**Resultado: suportado.**

- **Imagem derivada:** `FROM prcsousa/picturas-watermark-tool-ms@sha256:534007b3…`, com o
  `core/message_queue_setup.py` substituído (`tests/spikes/SP-08/`). Lê
  `RABBITMQ_TLS_CA_FILE` e `RABBITMQ_TLS_SERVER_NAME`, verifica a cadeia e o nome
  (`ssl.create_default_context`) e passa a porta a `int`. **Sem CA, não arranca**: não
  há recurso a plaintext.
- O watermark não declara filas nem exchanges: só consome e publica em
  `RABBITMQ_RESULTS_EXCHANGE`. Funciona com `configure "^$"` e com o exchange `topic`
  da D-18 só por variável de ambiente.

| Caso | Resultado |
|------|-----------|
| Sem `RABBITMQ_TLS_CA_FILE` | Termina: `RABBITMQ_TLS_CA_FILE is required (AMQPS only)` |
| CA errada / nome errado | Termina: `CERTIFICATE_VERIFY_FAILED` / `Hostname mismatch` |
| CA da instalação, utilizador `watermark_tool` com privilégio mínimo | Processou um pedido: `out.png` criado e resultado `success` em `project_queue` |

## SP-09 — Next.js (frontend) a servir HTTPS ao nginx

**Resultado: suportado.** Exige `proxy_ssl_session_reuse off` no nginx (ver as notas).

- **Servidor:** `server-https.js` com `https.createServer` e o handler do Next
  (`next({dev:false})`), dentro da imagem `frontend` da BF (Next 15.1.3, Node 18.20.8).
  Usa `requestCert`/`rejectUnauthorized` e uma lista de pares por CN (`nginx`).
- **Harness:** `tests/spikes/SP-09/`. Bruto em `results/sp09-1..2`.

| Caso | Resultado |
|------|-----------|
| nginx com `proxy_ssl_verify`, nome `frontend` e certificado de cliente: `/`, um chunk estático, `/login` | 200 / 200 / 200; latência mediana 6–8 ms |
| nginx à espera de outro nome (`api_gateway`) | 502 (`certificate does not match`) |
| Direto de outro contentor: HTTP / sem certificado / certificado de outra CA | Recusado |
| Certificado válido da CA com CN=projects (fora da lista) | 403 da aplicação |
| **nginx sem certificado de cliente, depois de outra localização ter aberto sessão com certificado** | **200**: o nginx retomou a sessão TLS e o servidor aceitou-a como o par `nginx` |
| O mesmo com `proxy_ssl_session_reuse off` | 502 (`certificate required`); latência mediana 7,8 ms (contra 6,2 ms) |

Notas para o B5 e o B10:
1. **`proxy_ssl_session_reuse off` em todas as localizações com upstream TLS.** Com a
   retoma de sessão, a identidade apresentada numa ligação passa para outras, e uma
   identidade retirada (PKI-C2/C3) pode continuar a ser aceite enquanto a sessão durar.
   O mesmo motivo justifica o `maxCachedSessions: 0` nos clientes Node (já no plano). Nos
   servidores Node convém também desligar a retoma; fica para verificar no B5.
2. O `next start` avisa que não funciona com `output: "standalone"`. O servidor próprio
   usa o build normal (`.next`) e o `node_modules` da imagem, e funcionou.
3. O repositório tem `frontend/certs/selfsigned.key` commitado: é um segredo no Git, a
   retirar no B1.

## SP-10 — Flask (generative-mock) e `requests` (expand_ai) com mTLS

**Resultado: suportado.**

- **Servidor:** `server_tls.py` importa a app de `generative-mock/server.py` sem a
  alterar e serve-a com um `ssl.SSLContext` (`CERT_REQUIRED`, CA da instalação). Um
  `before_request` verifica o CN do par (`request.environ["werkzeug.socket"].getpeercert()`)
  contra uma lista (`expand_ai_tool`).
- **Cliente:** o `requests` 2.32.3 da imagem `expand_ai` da BF, com `cert=` e
  `verify=<CA>`.
- **Harness:** `tests/spikes/SP-10/`. Bruto em `results/sp10.out`. O healthcheck em HTTPS
  com certificado de cliente também funcionou.

| Caso | Resultado |
|------|-----------|
| mTLS `expand_ai_tool` → `/outpaint` | 200, `image/png` |
| HTTP simples / sem certificado / certificado de outra CA | Recusado no TLS |
| Certificado válido da CA com CN=projects | 403 |
| Servidor verificado com outra CA / por IP | `SSLError` |
| `verify=False` (controlo do padrão proibido) | 200: é por isso que a regra 7 o proíbe |

## SP-11 — Componentes internos do SeaweedFS com TLS: inventário e suporte

**Resultado: suportado com limitações.** O HTTPS do master, do volume e do filer aceita
qualquer certificado da CA da instalação: aberta a **D-19**.

- **Configuração:** a do SP-02, mais `[grpc]`, com CA e
  `[grpc.master|volume|filer|s3|client]`, todos com `allowed_commonNames = "seaweedfs"`,
  e `-s3.port.iceberg=0 -s3.port.lance=0`.
- **Harness:** `tests/spikes/SP-11/`. Bruto em `results/sp11-1..3`.

Inventário das portas do `weed server`:

| Porta | Componente | Com `-ip=seaweedfs` (todas as interfaces) | Com `-ip=localhost -ip.bind=127.0.0.1 -s3.ip.bind=0.0.0.0` |
|-------|-----------|-------------------------------------------|-------------------------------------------------------------|
| 9333 / 19333 | master HTTP / gRPC | Alcançáveis; HTTPS exige certificado de cliente, mas **qualquer certificado da CA** (o do `img_storage` recebe 200) | Só loopback |
| 8080 / 18080 | volume HTTP / gRPC | Alcançáveis; o mesmo no HTTP | Só loopback |
| 8888 / 18888 | filer HTTP / gRPC | Alcançáveis; **o certificado do `img_storage` recebe 200 na API do filer**, que dá acesso a todos os ficheiros por fora das identidades S3 | Só loopback |
| 9000 | S3 HTTPS | Alcançável (TLS de servidor + SigV4) | Alcançável |
| 19000 | S3 gRPC | Alcançável | Alcançável; mTLS com `allowed_commonNames`: sem certificado ou com o do `img_storage`, recusado; com CN=seaweedfs, `grpc-status: 0` |
| 8181 / 9101 | Iceberg / Lance (HTTP simples) | Abertas por omissão | Desligadas com `-s3.port.iceberg=0 -s3.port.lance=0` |

No modo loopback, o S3 continua a funcionar por inteiro (a matriz do SP-02 repetida:
PUT, GET, Copy, URLs assinados e as recusas). Notas:
1. O `[https.*]` só aceita `cert/key/ca`: não há lista de CN para o HTTP do master, do
   volume e do filer. O `allowed_commonNames` existe só no gRPC.
2. Sem `[jwt.signing]`, as escritas no volume só ficam protegidas pelo mTLS (que aceita
   qualquer certificado da CA). No modo loopback, isto deixa de estar na rede.

---

## Outras tarefas do B0

### Imagens fixadas às da BF

Comparadas por camadas (`RootFS.Layers`) com as imagens do manifesto da BF
(`evaluation/results/BF-20261121T013224Z/manifest.json`):

| Onde | Antes | Depois | Prova |
|------|-------|--------|-------|
| `docker-compose.yaml` (nginx) | `nginx:latest` | `nginx@sha256:84f7876d21d154885f99554d7ae325d8c2213f9169726ea7ab60642f2573a787` | É o ID da imagem `picturas-nfr-nginx-1` no manifesto da BF |
| `docker-compose.yaml` (watermark) | `prcsousa/picturas-watermark-tool-ms:latest` | `…@sha256:534007b3904257e877f6246578a3df65e1875b477b92d9627b29e35e60c35835` | É o ID de `picturas-nfr-watermark_tool_ms-1` |
| `users`, `apiGateway`, `subscriptions` (`FROM node`) e `projects`, `imageStorageService` (`from node`) | `node` sem tag | `node:26.13.1-trixie@sha256:e18c3ccdf7d71619990b0e85639f506e2028a95410999cab24cc373cbd10e0ac` | As imagens da BF têm `NODE_VERSION=26.13.1` (Debian trixie), e as 7 camadas base de `node:26.13.1-trixie` são as primeiras camadas das 5 imagens da BF |

- O build dos 5 serviços Node com a base fixada passou (`docker compose -p picturas-dev
  build`), e o nginx e o watermark resolvem pelo digest.
- O `wsGateway` e o `frontend` usam `node:18`. Hoje é o mesmo `18.20.8` bookworm da BF
  (camadas iguais), e a linha 18 terminou, por isso não foram alterados (o plano só pede
  as imagens sem versão).
- **Limitação:** fixar a base não fixa os pacotes instalados no build (`apt-get install
  ffmpeg` no `projects`, `npm`/`bun`/`pip` sem lockfile em vários serviços). Uma
  reconstrução mais tarde pode trazer versões diferentes. Fica para a F10
  (reprodutibilidade).

### `tests/conformance/`

Criado com o `README.md` (organização pelos grupos do plano §5, regras e local dos
resultados) e o `run-f01.sh` (regressão existente).

### F01 — regressão existente (ponto de partida)

`tests/conformance/run-f01.sh picturas-nfr`, que corre nas imagens da BF com o código
atual montado só para leitura:
`tests/conformance/results/2026-11-21/F01-202134.txt`.

| Suite | Resultado |
|-------|-----------|
| `projects` (`node --test`, Node 26.13.1) | **8/8** |
| `Tools/video` (`pytest`, imagem `video_tool`, ffmpeg 7.1.5 com `libass`) | **74/74** |

No host (Python 3.13.9, ffmpeg 9.0.2 do Homebrew), o `Tools/video` dá 68/74. As 6 falhas
são todas de legendas, porque o ffmpeg do Homebrew não tem `libass` (falta o filtro
`subtitles`). É o ambiente, não o código: na imagem do produto passam todas. Os outros
serviços Node não têm testes.

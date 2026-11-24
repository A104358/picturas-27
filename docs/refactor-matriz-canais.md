# Matriz PKI-C5 por canal — B10

Snapshot executado em 24/11/2026, `fase2-refactor`, base `cb1e028` + B10 sem commit. Cada linha remete para os IDs de imagem/versões e o perfil de certificado completos abaixo. Resultados refletem probes e operações reais; não são uma inferência de configuração do fornecedor.

## Comandos e bruto

- **P**: `run-b10.sh begin|replace|resume 1|2|3` → [trial 1](../tests/conformance/results/2026-11-24/B10-trial-1.json), [trial 2](../tests/conformance/results/2026-11-24/B10-trial-2.json), [trial 3](../tests/conformance/results/2026-11-24/B10-trial-3.json). 121 controlos por tentativa, manifestos reais e retomas antigas; [operação adicional](../tests/conformance/results/2026-11-24/B10-fault-operation.json) inclui as três portas Rabbit locais.
- **D4**: `in-network.sh picturas-dev mtls-pki/b5-mtls.py` → [B10-b5-mtls-dev.txt](../tests/conformance/results/2026-11-24/B10-b5-mtls-dev.txt). Matriz por par, sem certificado/outra CA/expirado/EKU errado, plaintext e sem retoma nos servidores internos.
- **FUNC**: `in-network.sh picturas-dev b4-identity.py|b4-routes.py|b4-functional.py|mtls-pki/b5-functional.py|websocket/b8-functional.py` → [B4](../tests/conformance/results/2026-11-24/B10-b4-routes-dev.txt), [B5](../tests/conformance/results/2026-11-24/B10-b5-functional-dev.txt), [B8](../tests/conformance/results/2026-11-24/B10-b8-functional-dev.txt). Guardar/leitura/mutações/cleanup/expand real/owner WSS. A guarda de validade e os clientes são testados por [b5-guard.sh](../tests/conformance/results/2026-11-24/B10-b5-guard-dev.txt).
- **F02**: `evaluation/.venv/bin/python tests/conformance/data-channels/b2-functional.py` → [imagem/vídeo](../tests/conformance/results/2026-11-24/B10-F02-dev.txt); [smoke](../tests/conformance/results/2026-11-24/B10-smoke-dev.txt).
- **S16/S3/S18**: `med.py run --campaign EXP --quick --metrics S01,S02,S03,S04,S05,S12,S16,S17,S18,S21`, de `evaluation/` com `.venv/bin/python`, `MED_WS_JOIN_FORMAT=v2`, projeto `picturas-nfr-exp`; [registo](../tests/conformance/results/2026-11-24/B10-EXP-run.txt). S16 verifica canais de dados/ACL; S17 e S05/F02 cobrem S3 e URLs legítimos. Instrumento congelado intacto.
- **BROWSER**: `run-b10.sh browser n`, inspeção visual separada e `browser-live` → [Firefox aplicação/WSS](../tests/conformance/results/2026-11-24/B10-browser-live.json) e recibos nos trials. Ator Codex, sem atribuir confirmação humana; NSS isolado, sem bypass. Capturas privadas com hashes públicos.
- **LOOPBACK**: `run-b10.sh channels` → [28 controlos reais](../tests/conformance/results/2026-11-24/B10-seaweed-internal.json). Namespace de rede do SeaweedFS só para o harness de confiança; não abre os listeners aos serviços.

## Canais e asserções

| Canal | Imagens/versões e certificado | Asserção | Prova / resultado |
|---|---|---|---|
| api_gateway → projects | [api_gateway](#i-api_gateway), [projects](#i-projects); [C-projects](#c-projects) | mTLS e par/operação D4; leitura/mutação legítimas, RS256 contextual, posse/partilha. Sem certificado, par errado, CA antiga e nome errado recusados. | P + D4 + FUNC; PASS |
| api_gateway → users | [api_gateway](#i-api_gateway), [users](#i-users); [C-users](#c-users) | mTLS e par/operação D4; registo/login/anónimo e perfil; identidade e sujeito. Sem certificado, par errado, CA antiga e nome errado recusados. | P + D4 + FUNC; PASS |
| api_gateway → subscriptions | [api_gateway](#i-api_gateway), [subscriptions](#i-subscriptions); [C-subscriptions](#c-subscriptions) | mTLS e par/operação D4; plano/billing mock e titular autorizado. Sem certificado, par errado, CA antiga e nome errado recusados. | P + D4 + FUNC; PASS |
| projects → users | [projects](#i-projects), [users](#i-users); [C-users](#c-users) | mTLS e par/operação D4; presença/quota no contexto permitido. Sem certificado, par errado, CA antiga e nome errado recusados. | P + D4 + FUNC; PASS |
| projects → img_storage | [projects](#i-projects), [img_storage](#i-img_storage); [C-img_storage](#c-img_storage) | mTLS e par/operação D4; operações storage no projeto. Sem certificado, par errado, CA antiga e nome errado recusados. | P + D4 + FUNC; PASS |
| users → projects | [users](#i-users), [projects](#i-projects); [C-projects](#c-projects) | mTLS e par/operação D4; limpeza restrita à conta removida. Sem certificado, par errado, CA antiga e nome errado recusados. | P + D4 + FUNC; PASS |
| ws_gateway → projects | [ws_gateway](#i-ws_gateway), [projects](#i-projects); [C-projects](#c-projects) | mTLS e par/operação D4; join/revalidação com autorização fresca. Sem certificado, par errado, CA antiga e nome errado recusados. | P + D4 + FUNC; PASS |
| expand_ai_tool → generative-mock | [expand_ai_tool](#i-expand_ai_tool), [generative-mock](#i-generative-mock); [C-generative-mock](#c-generative-mock) | mTLS e par/operação D4; outpainting real por requests/mTLS. Sem certificado, par errado, CA antiga e nome errado recusados. | P + D4 + FUNC; PASS |
| Browser → nginx | [frontend](#i-frontend), [nginx](#i-nginx); [C-nginx](#c-nginx) | NSS isolado; nova CA válida, CA retirada/expirado/nome errado recusados; aplicação e WSS owner frescos. | BROWSER + P; PASS |
| nginx → frontend | [nginx](#i-nginx), [frontend](#i-frontend); [C-frontend](#c-frontend) | Upstream HTTPS validado, SNI próprio, cliente nginx. Conteúdo/API/polling/upgrade legítimos; sockets antigos cortados; novo contexto sem CA retirada. | P + D4 + FUNC + BROWSER; PASS |
| nginx → api_gateway | [nginx](#i-nginx), [api_gateway](#i-api_gateway); [C-api_gateway](#c-api_gateway) | Upstream HTTPS validado, SNI próprio, cliente nginx. Conteúdo/API/polling/upgrade legítimos; sockets antigos cortados; novo contexto sem CA retirada. | P + D4 + FUNC + BROWSER; PASS |
| nginx → ws_gateway | [nginx](#i-nginx), [ws_gateway](#i-ws_gateway); [C-ws_gateway](#c-ws_gateway) | Upstream HTTPS validado, SNI próprio, cliente nginx. Conteúdo/API/polling/upgrade legítimos; sockets antigos cortados; novo contexto sem CA retirada. | P + D4 + FUNC + BROWSER; PASS |
| nginx → SeaweedFS S3 | [nginx](#i-nginx), [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | HTTPS 9000, GET/HEAD/Range de URL assinada; métodos/permissões indevidos recusados. | P + S3 + F02; PASS |
| img_storage → SeaweedFS S3 | [img_storage](#i-img_storage), [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | AWS SDK sobre HTTPS; HEAD nativo por reabertura, PUT/GET/remoção reais pelo pipeline; scope próprio. | P native_s3_head + S3 + F02; PASS |
| s3-bootstrap → SeaweedFS S3 | [s3-bootstrap](#i-s3-bootstrap), [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | Job Node de arranque com CA validada e identidade admin só nele; headBucket termina com exit 0 a cada recriação. | P participants_loaded + I-s3-bootstrap; PASS |
| nginx → SeaweedFS filer (percurso removido) | [nginx](#i-nginx), [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | Não existe proxy de acesso ao filer; 8888/18888 inacessíveis da rede e /s3-console/ recusado. Não há um salto HTTP escondido. | P bypass + S3; PASS (percurso fechado) |
| users → users_mongoDB | [users](#i-users), [users_mongoDB](#i-users_mongodb); [C-users_mongoDB](#c-users_mongodb) | TLS de servidor, principal users_svc; leitura nativa e escrita só em user. Credencial inválida/outra BD/nome errado/CA antiga recusados; pool antigo cortado. | P + S16 + FUNC; PASS |
| mongo-backup → users_mongoDB | [mongo-backup](#i-mongo-backup), [users_mongoDB](#i-users_mongodb); [C-users_mongoDB](#c-users_mongodb) | mongodump --ssl --sslCAFile, backup_ro só leitura em user; processo recriado e CA nova montada. Leitura/role nativas verificadas; escrita indevida recusada. | P backup role + I-mongo-backup + S16; PASS |
| administrador → users_mongoDB | [users_mongoDB](#i-users_mongodb); [C-users_mongoDB](#c-users_mongodb) | Admin apenas por exec/harness de confiança, TLS e credencial fora do repositório; sem porta no host; fixture/cleanup de segurança por principal admin. | P + S16 + S18; PASS |
| projects → projects_mongoDB | [projects](#i-projects), [projects_mongoDB](#i-projects_mongodb); [C-projects_mongoDB](#c-projects_mongodb) | TLS de servidor, principal projects_svc; leitura nativa e escrita só em project. Credencial inválida/outra BD/nome errado/CA antiga recusados; pool antigo cortado. | P + S16 + FUNC; PASS |
| mongo-backup → projects_mongoDB | [mongo-backup](#i-mongo-backup), [projects_mongoDB](#i-projects_mongodb); [C-projects_mongoDB](#c-projects_mongodb) | mongodump --ssl --sslCAFile, backup_ro só leitura em project; processo recriado e CA nova montada. Leitura/role nativas verificadas; escrita indevida recusada. | P backup role + I-mongo-backup + S16; PASS |
| administrador → projects_mongoDB | [projects_mongoDB](#i-projects_mongodb); [C-projects_mongoDB](#c-projects_mongodb) | Admin apenas por exec/harness de confiança, TLS e credencial fora do repositório; sem porta no host; fixture/cleanup de segurança por principal admin. | P + S16 + S18; PASS |
| subscriptions → subscriptions_mongoDB | [subscriptions](#i-subscriptions), [subscriptions_mongoDB](#i-subscriptions_mongodb); [C-subscriptions_mongoDB](#c-subscriptions_mongodb) | TLS de servidor, principal subscriptions_svc; leitura nativa e escrita só em subscription. Credencial inválida/outra BD/nome errado/CA antiga recusados; pool antigo cortado. | P + S16 + FUNC; PASS |
| mongo-backup → subscriptions_mongoDB | [mongo-backup](#i-mongo-backup), [subscriptions_mongoDB](#i-subscriptions_mongodb); [C-subscriptions_mongoDB](#c-subscriptions_mongodb) | mongodump --ssl --sslCAFile, backup_ro só leitura em subscription; processo recriado e CA nova montada. Leitura/role nativas verificadas; escrita indevida recusada. | P backup role + I-mongo-backup + S16; PASS |
| administrador → subscriptions_mongoDB | [subscriptions_mongoDB](#i-subscriptions_mongodb); [C-subscriptions_mongoDB](#c-subscriptions_mongodb) | Admin apenas por exec/harness de confiança, TLS e credencial fora do repositório; sem porta no host; fixture/cleanup de segurança por principal admin. | P + S16 + S18; PASS |
| bg_remove_ai_tool → RabbitMQ | [bg_remove_ai_tool](#i-bg_remove_ai_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| binarization_tool → RabbitMQ | [binarization_tool](#i-binarization_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| border_tool → RabbitMQ | [border_tool](#i-border_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| brightness_tool → RabbitMQ | [brightness_tool](#i-brightness_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| contrast_tool → RabbitMQ | [contrast_tool](#i-contrast_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| cut_ai_tool → RabbitMQ | [cut_ai_tool](#i-cut_ai_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| cut_tool → RabbitMQ | [cut_tool](#i-cut_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| expand_ai_tool → RabbitMQ | [expand_ai_tool](#i-expand_ai_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| obj_ai_tool → RabbitMQ | [obj_ai_tool](#i-obj_ai_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| people_ai_tool → RabbitMQ | [people_ai_tool](#i-people_ai_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| projects → RabbitMQ | [projects](#i-projects), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| resize_tool → RabbitMQ | [resize_tool](#i-resize_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| rotate_tool → RabbitMQ | [rotate_tool](#i-rotate_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| saturation_tool → RabbitMQ | [saturation_tool](#i-saturation_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| text_ai_tool → RabbitMQ | [text_ai_tool](#i-text_ai_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| upgrade_ai_tool → RabbitMQ | [upgrade_ai_tool](#i-upgrade_ai_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| video_tool → RabbitMQ | [video_tool](#i-video_tool), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| watermark_tool_ms → RabbitMQ | [watermark_tool_ms](#i-watermark_tool_ms), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| ws_gateway → RabbitMQ | [ws_gateway](#i-ws_gateway), [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | AMQPS com CA/nome validados, credencial própria, declaração passiva da fila própria e consumer efetivamente registado. Contexto antigo terminado; ACL por principal/routing key. | P native AMQPS + registered_consumers + S16 + F02; PASS |
| administrador → RabbitMQ management | [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | HTTPS 15671 com credencial admin; principal de worker recusado, 5672/15672 fechados e sem portas host. | P + S16 + S18; PASS |
| RabbitMQ CLI/epmd/distribution/Prometheus locais | [rabbitmq](#i-rabbitmq); [C-rabbitmq](#c-rabbitmq) | 4369/25672/15692 só em loopback, inacessíveis do elk. CLI local usa cookie privado; esses listeners locais não são apresentados como TLS. | P adicional B10-fault-operation + config; PASS (rede fechada) |
| SeaweedFS interno → master HTTPS :9333 | [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | Mesmo processo/namespace; TLS/mTLS real, folha servida atual, ausência de cliente e CA antiga (cliente/servidor) recusadas. Listener só loopback; inacessível a outros serviços. | LOOPBACK (4 controlos por listener) + P bypass; PASS |
| SeaweedFS interno → volume HTTPS :8080 | [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | Mesmo processo/namespace; TLS/mTLS real, folha servida atual, ausência de cliente e CA antiga (cliente/servidor) recusadas. Listener só loopback; inacessível a outros serviços. | LOOPBACK (4 controlos por listener) + P bypass; PASS |
| SeaweedFS interno → filer HTTPS :8888 | [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | Mesmo processo/namespace; TLS/mTLS real, folha servida atual, ausência de cliente e CA antiga (cliente/servidor) recusadas. Listener só loopback; inacessível a outros serviços. | LOOPBACK (4 controlos por listener) + P bypass; PASS |
| SeaweedFS interno → master gRPC :19333 | [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | Mesmo processo/namespace; TLS/mTLS real, folha servida atual, ausência de cliente e CA antiga (cliente/servidor) recusadas. Listener só loopback; inacessível a outros serviços. | LOOPBACK (4 controlos por listener) + P bypass; PASS |
| SeaweedFS interno → volume gRPC :18080 | [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | Mesmo processo/namespace; TLS/mTLS real, folha servida atual, ausência de cliente e CA antiga (cliente/servidor) recusadas. Listener só loopback; inacessível a outros serviços. | LOOPBACK (4 controlos por listener) + P bypass; PASS |
| SeaweedFS interno → filer gRPC :18888 | [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | Mesmo processo/namespace; TLS/mTLS real, folha servida atual, ausência de cliente e CA antiga (cliente/servidor) recusadas. Listener só loopback; inacessível a outros serviços. | LOOPBACK (4 controlos por listener) + P bypass; PASS |
| SeaweedFS interno → S3 gRPC :19000 | [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | Mesmo processo/namespace; TLS/mTLS real, folha servida atual, ausência de cliente e CA antiga (cliente/servidor) recusadas. 19000 acessível só no elk com CN seaweedfs; HTTP/2 SETTINGS observado. | LOOPBACK (4 controlos por listener) + P bypass; PASS |
| administrador → SeaweedFS | [seaweedfs](#i-seaweedfs); [C-seaweedfs](#c-seaweedfs) | Administração pelo namespace local; master/volume/filer fora do alcance do elk; APIs HTTPS com certificado de cliente. | LOOPBACK + P; PASS (fronteira loopback) |

Os volumes `image_data`, `whisper_models` e dados persistentes são acessos a ficheiros, sem handshake TLS. Não contêm segredos da instalação por desenho; só o worker/serviço autorizado recebe os mounts necessários. A CA privada nunca é montada nos serviços. Os HTTPS internos do SeaweedFS aceitam clientes da CA sem allowlist de CN; a fronteira validada na decisão 20 é loopback, comprovada nos probes de rede, e não se declara aí uma allowlist inexistente. Os gRPC usam `allowed_commonNames=seaweedfs`.

## Imagens e versões efetivas

[Manifesto integral](../tests/conformance/results/2026-11-24/B10-runtime-manifest.json): `image_id` é o identificador SHA-256 imutável local; `repo_digests` preserva os digests de registo quando existem. Imagens construídas localmente podem não ter RepoDigest; não se inventa um digest de registo. O mesmo image_id foi usado na dev/EXP. As bibliotecas e OpenSSL completos constam do JSON por serviço.

### I-api_gateway

`sha256:4323b6f198e10901776f4becfb3fb5131dfde86b242f23ab633eeb0af800022b`; Node 26.13.1 / OpenSSL 3.5.9. express 4.16.4, axios 1.21.1

### I-bg_remove_ai_tool

`sha256:32124ee2c9776c43b3f75ad663329808d3dc01c74a778d452c88bd1d0d5b50ad`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0, requests 2.34.2

### I-binarization_tool

`sha256:85cfd4ecb56f9c69b1cee35cc4a5ea06b9c19ef2237408f478bd9a62257c5059`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0

### I-border_tool

`sha256:bba9d4a9c748632763cff38094df4a876d745f26f4411ebcec71a3c266c439af`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0

### I-brightness_tool

`sha256:21e6b410453469235c25e0619d74e80813d18d0a58542d0d0e1c712eb94d0649`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0

### I-contrast_tool

`sha256:a5ab2de0d721f61a8bc31b1b0e7dcad37b629caa94d4cb690b771a4a4a243fdf`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0

### I-cut_ai_tool

`sha256:643fb40b4abcf681f5372f5b243a724c8f1a4c696abd64cf5c1be94168200012`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0, requests 2.34.2

### I-cut_tool

`sha256:68d8ef35c853ea32c3220e4237bfd0cea6fb5f85b332041501e9c4e728e63326`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0

### I-expand_ai_tool

`sha256:8832fb5c0bbb999553e418a4137715f7c8ff3a905e4d120dbdbcb5f58c98d628`; Python 3.10.22 / OpenSSL 3.5.7 9 Jun 2026. pika 1.3.2, Pillow 10.3.0, requests 2.32.3

### I-frontend

`sha256:086d7f20cc9ca22be1653f4eaf5a4d37e18d5c6437fb797561e4a578e3c094c4`; Node 18.20.8 / OpenSSL 3.0.16. axios 1.21.0, mongoose 8.24.7, next 15.1.3, socket.io 4.8.4, socket.io-client 4.8.4

### I-generative-mock

`sha256:8146819cca31a7f7aa0428bdd54e36f4892d3d84dde5f30c2a7539f7170a07ba`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. Pillow 13.0.0, Flask 3.1.3, Werkzeug 3.1.9

### I-img_storage

`sha256:ecdc83a0df46eb4aee401d3b87cedec3e8487c05d41563827cc13a80321da852`; Node 26.13.1 / OpenSSL 3.5.9. express 4.22.3, aws-sdk 2.1693.0

### I-mongo-backup

`sha256:0010f63d26952bd3960fac5513c64a1cf7d6299f31fa7b54ac1b36633ee04333`; mongodump version: 100.10.0. Versão completa no manifesto.
Registo: `mongo@sha256:4be76f674fc4b27859816811b8baa3c51830eb1dbf4ca81a51e26b79edd662ef`.

### I-nginx

`sha256:14fb90841494b84ec6f9ea2de7562ae28ccdb6e74c660d48f7b565c389ffe590`; nginx version: nginx/1.31.9. Versão completa no manifesto.
Registo: `nginx@sha256:84f7876d21d154885f99554d7ae325d8c2213f9169726ea7ab60642f2573a787`.

### I-obj_ai_tool

`sha256:9ad57aceac673a132820c5588ef9ec5955ea42ce7941488b3df3f4dd76c96861`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0, requests 2.34.2

### I-people_ai_tool

`sha256:2f88a8fec5d7e29fe96bb03e82d33dbbe1dbc0640e216bff26c22acbe349eacd`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0, requests 2.34.2

### I-projects

`sha256:7ba8631e37fb0d8d83b82dc2686c56ee8c139f4a92451f789eddde4686f0a4eb`; Node 26.13.1 / OpenSSL 3.5.9. express 4.16.4, axios 1.21.1, amqplib 0.10.9, mongoose 8.24.11

### I-projects_mongoDB

`sha256:0010f63d26952bd3960fac5513c64a1cf7d6299f31fa7b54ac1b36633ee04333`; db version v4.4.30. Versão completa no manifesto.
Registo: `mongo@sha256:4be76f674fc4b27859816811b8baa3c51830eb1dbf4ca81a51e26b79edd662ef`.

### I-rabbitmq

`sha256:9887bbea3ca1594eb1340b3cb8ce3a27b7e367ccb6d8bd2c246e389d3d1bf049`; 4.0.5. Versão completa no manifesto.

### I-resize_tool

`sha256:dc31a712123d3120b1e57ee3c891f7ed84bf4006f43defcc127f36e55d0bcb48`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0

### I-rotate_tool

`sha256:1e7ba7763ad05d4f4e25c05691df830dae157c40ae2a218b1bed28f0c438b101`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0

### I-s3-bootstrap

`sha256:d46de30de68e273d8598e1d684809af75c51076e496d39ea9bc09076ca53e431`; Node 26.13.1 / OpenSSL 3.5.9. express 4.22.3, aws-sdk 2.1693.0

### I-saturation_tool

`sha256:74a896f4c1704de6188b1d639e7d1a00e8a0ca546bd4f2233d9ca4e88d66e3fe`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0

### I-seaweedfs

`sha256:31d61f5e8771cbd5993912cd051be0c7bcdc207faaa12c50e1a3b8371631c927`; version 30GB 4.47 c50733600 linux amd64. Versão completa no manifesto.
Registo: `chrislusf/seaweedfs@sha256:ce9e796f1fe6f06968f4c04bdaf8f678dad9c8acdfef3d244133d71bfa6bf882`.

### I-subscriptions

`sha256:fce84c34a434dcbce77328e67b0c442830456baa4afb7be9ecec107caedc450e`; Node 26.13.1 / OpenSSL 3.5.9. express 4.16.4, mongoose 8.24.11

### I-subscriptions_mongoDB

`sha256:0010f63d26952bd3960fac5513c64a1cf7d6299f31fa7b54ac1b36633ee04333`; db version v4.4.30. Versão completa no manifesto.
Registo: `mongo@sha256:4be76f674fc4b27859816811b8baa3c51830eb1dbf4ca81a51e26b79edd662ef`.

### I-text_ai_tool

`sha256:65d166fdc6efab1532dc507cfc6602bc6aa7dda77c3533e1701e859702a7d1c3`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0

### I-upgrade_ai_tool

`sha256:3635a3465c1b87c2b90dada81dca2a2d5e8868dc93d97837e0e491056c7b19e4`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0

### I-users

`sha256:e342ad7ab1bee06ca0fefe3f688ca87d7993c5155e2bfe4594864b61f6bebdb9`; Node 26.13.1 / OpenSSL 3.5.9. express 4.16.4, axios 1.21.1, mongoose 8.24.11

### I-users_mongoDB

`sha256:0010f63d26952bd3960fac5513c64a1cf7d6299f31fa7b54ac1b36633ee04333`; db version v4.4.30. Versão completa no manifesto.
Registo: `mongo@sha256:4be76f674fc4b27859816811b8baa3c51830eb1dbf4ca81a51e26b79edd662ef`.

### I-video_tool

`sha256:319ecbbd1bec4a996a33da1626e4428adea81539a210dd09587008755f4f0f59`; Python 3.11.18 / OpenSSL 3.5.9 29 Sep 2026. pika 1.3.2, Pillow 11.0.0, faster-whisper 1.2.1

### I-watermark_tool_ms

`sha256:f4e598cdd50f416ee2aea913e6d7b02546b65ae69d37a3e5af6c57461a3665b2`; Python 3.13.1 / OpenSSL 3.0.15 3 Sep 2024. pika 1.3.2, Pillow 11.0.0

### I-ws_gateway

`sha256:9c5acb25cc330152a6e44ad4261e8defa711545d7291bf136b1a075a4943c660`; Node 18.20.8 / OpenSSL 3.0.16. express 4.22.3, amqplib 0.10.9, socket.io 4.8.4

## Certificados efetivamente servidos/carregados

Todos pertencem à CA nova cujo fingerprint DER SHA-256 é `c51110ee652b4c5b26156750a5f6c2cd1787142c4aa6826ae58d84f6f1443550`. Emissor, SAN, EKU, validade e serial abaixo são públicos. Os fingerprints anteriores e novos, contextos vivos e respetivos testes estão no bruto de cada tentativa.

### C-api_gateway

`33e77ed9a40bc86872f33a99e4307c08e158d4f02d6ec4517800150ef0bcdd3c`

```text
serial=9EC5446B01141D30395A5EB2120EC821
subject=CN=api_gateway,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:18 2026 GMT
notAfter=Dec 24 19:17:18 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication, TLS Web Client Authentication
X509v3 Subject Alternative Name: 
    DNS:api_gateway
```

### C-expand_ai_tool

`25823ae330c96b152b7f39a86d1949cad4639b1a9ac617f4f7ae3ddda8911332`

```text
serial=C1AC5B46B7A84AC93C94BC503760EB2C
subject=CN=expand_ai_tool,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:19 2026 GMT
notAfter=Dec 24 19:17:19 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Client Authentication
X509v3 Subject Alternative Name: 
    DNS:expand_ai_tool
```

### C-frontend

`3c31c39cc027717709fcfeae6ef4cebbaf61f99758b5bea410dd15fad1c1cbd0`

```text
serial=39694058DDBC61E3EFFFBFD206A4B522
subject=CN=frontend,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:18 2026 GMT
notAfter=Dec 24 19:17:18 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication, TLS Web Client Authentication
X509v3 Subject Alternative Name: 
    DNS:frontend
```

### C-generative-mock

`38834cecc5af2b98fb31737de9f04e55632de6878f97f11eec3c3ca266b7173d`

```text
serial=31CC8BD5822D8271B072ACCED1629F99
subject=CN=generative-mock,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:19 2026 GMT
notAfter=Dec 24 19:17:19 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication, TLS Web Client Authentication
X509v3 Subject Alternative Name: 
    DNS:generative-mock
```

### C-img_storage

`a65c453f8797593b7ab6894236fa330ecfd162b3ef44d34dd021de9501b875bd`

```text
serial=DAF87411D6C2E9CFAD05BAB1211D503F
subject=CN=img_storage,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:19 2026 GMT
notAfter=Dec 24 19:17:19 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication, TLS Web Client Authentication
X509v3 Subject Alternative Name: 
    DNS:img_storage
```

### C-nginx

`376903a77148cd9a553424a6457b858bed2c6414c69b33ca2058cc558d4b2764`

```text
serial=CF92D7C4A1435001A32EF36109B6772C
subject=CN=nginx,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:18 2026 GMT
notAfter=Dec 24 19:17:18 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication, TLS Web Client Authentication
X509v3 Subject Alternative Name: 
    DNS:nginx, DNS:localhost, IP Address:127.0.0.1
```

### C-projects

`abe70d5af5f0683fbe74488656fd5d29ca3bdc89311c8d1124f0c6cb6822f0be`

```text
serial=1E4F64527FBD290C053E47266B3C1772
subject=CN=projects,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:18 2026 GMT
notAfter=Dec 24 19:17:18 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication, TLS Web Client Authentication
X509v3 Subject Alternative Name: 
    DNS:projects
```

### C-projects_mongoDB

`3be42efc05e49eff24f5d66fdedd492a11b421e3dcc4eb621c33c25120eba478`

```text
serial=FA20CE219ECC47D0E9F24D654CD54CC5
subject=CN=projects_mongoDB,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:19 2026 GMT
notAfter=Dec 24 19:17:19 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication
X509v3 Subject Alternative Name: 
    DNS:projects_mongoDB
```

### C-rabbitmq

`2203421f3ed6eb8d791b07cf563e6a58801f669c93a6cf2b0188bd5e90c33e3c`

```text
serial=037BFBE4ED56A90A66BD9CFDD0F69A54
subject=CN=rabbitmq,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:19 2026 GMT
notAfter=Dec 24 19:17:19 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication
X509v3 Subject Alternative Name: 
    DNS:rabbitmq
```

### C-seaweedfs

`abab94c611425bf073c4f474d354c7f3dc598ae6ff589d16f1c29d5b0df2d2ef`

```text
serial=BB252A031F09EFB117F508EC3C495504
subject=CN=seaweedfs,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:19 2026 GMT
notAfter=Dec 24 19:17:19 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication, TLS Web Client Authentication
X509v3 Subject Alternative Name: 
    DNS:seaweedfs, DNS:localhost
```

### C-subscriptions

`81e8b58bf2855248605ad0b42a3d11d8b12a1db95a0a0cce7f297976a36faa2d`

```text
serial=8B45DEA62D63D46A29E5B9F18116E3D0
subject=CN=subscriptions,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:19 2026 GMT
notAfter=Dec 24 19:17:19 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication, TLS Web Client Authentication
X509v3 Subject Alternative Name: 
    DNS:subscriptions
```

### C-subscriptions_mongoDB

`232fc47f41769a9c551e20c0dc5db9adb2b6a5828e60c79b92692ba2aa927392`

```text
serial=D6417B5DFD3EB663F7A4ED572A6E1DAB
subject=CN=subscriptions_mongoDB,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:19 2026 GMT
notAfter=Dec 24 19:17:19 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication
X509v3 Subject Alternative Name: 
    DNS:subscriptions_mongoDB
```

### C-users

`443c21e325c316156f1b45e9907365b3869db9b25ad66e6347e55fe65fd728ca`

```text
serial=7F481AE8B0141AC83CC3C9174E913764
subject=CN=users,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:19 2026 GMT
notAfter=Dec 24 19:17:19 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication, TLS Web Client Authentication
X509v3 Subject Alternative Name: 
    DNS:users
```

### C-users_mongoDB

`ac6c859b20a061b732ce709c2c4f583696acbeade6e95dc32820f5c4e32fdf36`

```text
serial=4E005F38189515C34E5A04B1C6DB5333
subject=CN=users_mongoDB,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:19 2026 GMT
notAfter=Dec 24 19:17:19 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication
X509v3 Subject Alternative Name: 
    DNS:users_mongoDB
```

### C-ws_gateway

`ac9f5e67b11ad048a2ac864f510de3231a85c8009cef0397badf2187d98d965e`

```text
serial=E4A17E1A4FCE838115D6678150954943
subject=CN=ws_gateway,O=PictuRAS
issuer=CN=PictuRAS installation CA 20261124191718,O=PictuRAS
notBefore=Nov 24 19:17:18 2026 GMT
notAfter=Dec 24 19:17:18 2026 GMT
X509v3 Extended Key Usage: 
    TLS Web Server Authentication, TLS Web Client Authentication
X509v3 Subject Alternative Name: 
    DNS:ws_gateway
```

## Limites e conclusão

A cobertura de canais não equivale a reconciliação de domínio. O B11 continua necessário para reabrir uma instalação normal com trabalhos interrompidos. A fixture D-33 é técnica e exclusiva. Limites de carga, tentativas de preparação/diagnóstico, tempos de operador e critério contextual da substituição estão no [relatório do piloto](refactor-piloto-pki.md). Sem CRL/OCSP: retirada significa nova CA e todas as chaves novas. Não houve rollback da CA retirada.

# Notas de implementação do `med.py`

Divergências entre o [plano](../docs/planoMedicao.md) e o código da aplicação,
encontradas durante a implementação, e a alternativa escolhida (regra do plano: manter o
objetivo do caso).

| # | Plano | Código real | Decisão |
|---|-------|-------------|---------|
| 1 | Fixture `owner` free | `GET /:user/:project` regista o visitante como editor (`ensureEditorSlot`) e um dono free tem só 2 lugares (`PRESENCE_LIMIT_NON_PREMIUM`). Os ataques do outsider ocupariam o lugar do editor e dariam 429. | Nas matrizes de segurança o dono é **premium** (sem limite de presença). Em S05 o dono é free (para verificar a quota) e só tem um editor. |
| 2 | `og_img_key` obtido do estado do projeto | A resposta de `GET /:user/:project` não inclui `og_img_key` (só `_id`, `name`, `media_type`, `url`). | A chave do original obtém-se pelo canal de verificação: listagem S3 com credenciais de administração, prefixo `users/<owner>/projects/<pid>/src/` (layout de `imageStorageService/services/storage.js`). |
| 3 | Correlacionar eventos S12 por `params` | O gateway não reencaminha `X-Op-Id`; o `project-op` traz `op.newVersion`. | Correlação pela versão: `X-Project-Version` da resposta 2xx do produtor ↔ `op.newVersion` do evento (ou `version` de `project-updated`). |
| 4 | IDs `D06` em S02 e S03 | O plano usa `D06` em duas métricas. | Os IDs são únicos dentro de cada métrica (`S02.D06` = eliminar projeto, `S03.D06` = URL assinado). A matriz congelada está em `cases/security.yaml`. |
| 5 | D04 "JWT não assinado" | — | Dois casos: `D04a` (HS256 com chave aleatória) e `D04b` (`alg: none`). |
| 6 | "2xx sem efeito = INCONCLUSIVO" | G06/G07/D09: a refatoração pode responder 2xx ignorando o campo `type` (despromover em vez de recusar). | Nesses três casos, 2xx com o perfil verificado como não premium conta como recusa (`allow_2xx_no_effect`). Nos restantes mantém-se INCONCLUSIVO. |
| 7 | Premium por fixture | O `projects` lê o tipo de utilizador ao `users` em cada pedido (`/:user/type`). | A fixture altera `type` na BD `user`, coleção `users`, e faz novo login; não usa o registo público (G06). |
| 8 | Subscrição G08/G09/D14 | Criar subscrição pelo gateway também promove a conta a premium. | A subscrição é criada numa conta dedicada (não na vítima dos outros casos). Cartão de teste `4242…`, validade `12/30`. |
| 9 | S16 d2 "list_database_names" | Com privilégio mínimo o MongoDB 4.4 devolve só as BD autorizadas, sem erro. | Admitido só se a lista incluir BD de **outro** serviço. |
| 10 | Override de portas | `img_storage` gera URLs públicas com `FRONTEND_URL=https://localhost:8080` (a outra instalação). | O override define `FRONTEND_URL` com `MED_BASE_URL` (igual em BF e MF). |
| 11 | Corpus T | Inserir a caixa `free` antes do `mdat` deslocaria os offsets absolutos do `moov`. | H: `ftyp, moov, mdat, free`; T: `ftyp, mdat, free, moov`. Os dois descodificam sem erros. |
| 13 | U08 com `du` sobre o diretório temporário | O nginx cria o temporário do corpo em `client_temp` e apaga-o logo (fica aberto); o `du` não o vê. Os workers correm como `nginx`, e o root do contentor não lê os seus `/proc/*/fd`. | O amostrador soma `du` + ficheiros apagados mas abertos sob o diretório (`/proc/*/fd`, `stat -L`), a cada 100 ms, e no nginx corre como utilizador `nginx`. Ensaio (EXP, 21/11): 10 MiB → nginx 10 MiB + projects 10 MiB; 100 MiB → 100 + 100 MiB. |
| 14 | Esperar pela API após `restart` | Logo após reiniciar os serviços Node, o nginx responde 502 durante alguns segundos. | `wait_api` repete tudo (incluindo criar a conta) e, se o 502 durar mais de 60 s, reinicia também o nginx do projeto isolado. |
| 15 | Recuperar após falha se o contentor não estiver a correr | `api_gateway`, `projects`, `users` e `subscriptions` correm sob `nodemon`. Depois de um OOM o processo Node morre, mas o contentor fica "Up" (`app crashed - waiting for file changes`) e o Docker não o reinicia: **na base, um upload grande deixa a aplicação indisponível até intervenção manual** (observado no ensaio EXP de 21/11, U18-I6 e U25). | Depois de qualquer falha, `restart_app()` reinicia sempre os três serviços Node e o nginx (que pode ficar com o IP antigo do upstream). Antes de cada passo de upload verifica-se a saúde da API. |
| 16 | U25: 100 pedidos durante os uploads | Parar aos 100 pedidos (~10 s) deixava de fora a fase depois do envio, quando a memória atinge o pico e o gateway morre. | Os pedidos leves continuam durante toda a vida dos uploads (envio e espera pela resposta), com mínimo de 100. O registo inclui o estado dos uploads, o OOM do gateway e se a aplicação ficou indisponível. |
| 17 | U09/U10 "por amostra válida" | Na BF de 21/11, 14 dos 20 uploads premium de 500 MiB falharam (12× 502 por OOM do gateway, 2× 501 `Error storing image`). Uma resposta 502 chega em ~1 s e entrava como se fosse um tempo de aceitação. | U09 e U10 usam só uploads aceites (2xx); as falhas contam-se à parte (`falhas_500`, `aceites_por_estrato`). Estratos sem nenhum aceite ficam sem base no `compare`. `med.py report <dir> --resummarise` recalcula os resumos a partir de `raw/`, sem nova medição. |
| 18 | U04 medida nos estratos de 500 MiB | O SeaweedFS (Go) retém a memória de uploads anteriores: na BF, idle entre 130 MiB e 1,9 GiB, e `pico − idle` de +582 MiB só quando tinha acabado de arrancar (~0 nos restantes). | Passo próprio `U04` (`Uploader.seaweed_cold`): reinicia o SeaweedFS, os serviços Node e o nginx antes de cada upload premium de 500 MiB (H); 5 amostras aceites, até 40 tentativas no total (com `--resume` as já feitas contam). Também espera que o S3 responda depois de reiniciar: a primeira tentativa, sem essa espera, deu 501 e foi descartada. A U04 da BF foi medida de novo com este passo (`raw/U04.jsonl`); os estratos continuam a guardar os dados de cgroup antigos em `raw/U_strata.jsonl`. |
| 12 | Cliente TLS | O nginx usa um certificado autoassinado. | Verificação do cliente desligada (ou `MED_CACERT`), registada no manifesto; o mesmo nas duas campanhas. |

## Instrumentos

- **Memória Node:** `VmHWM` reposto com `clear_refs` (requer root no contentor; o
  resultado indica `hwm_reset`). Se a reposição falhar, o valor reportado é o pico desde
  o arranque do processo, o que só é fiável nos estratos "frio".
- **cgroup:** `memory.stat` → `anon` a cada 50 ms (v2), com recurso a `total_rss` (v1).
- **Disco:** `du -sk` a cada 200 ms nos diretórios temporários; resíduos medidos 60 s
  depois de cada estrato, por diferença face ao início do estrato.
- **Amostradores:** correm dentro do contentor e param por ficheiro-sinal ou por prazo
  máximo; matar o cliente `docker exec` não termina o ciclo no contentor.

# Fase 2 — Passagem de trabalho da refatoração (pausa e retoma)

[Índice da documentação](README.md) · [Plano](refactor-plano.md) · **Equipa: PL2-G4**

Este ficheiro diz **onde o trabalho parou, o que fazer a seguir e que contexto já
está decidido**. Quem retoma, seja uma pessoa ou um agente, não precisa de saber quem
trabalhou antes nem de ler conversas anteriores: lê a §1 (ponto atual) e a §2
(contexto), faz o próximo passo e, ao parar, atualiza a §1 e a §3 e acrescenta uma
entrada à §4.

O **o quê** e o **porquê** estão no [plano](refactor-plano.md). Aqui só está o **onde
estamos**.

> **Regra:** ao parar, por qualquer motivo, atualiza a §1 e a §3, acrescenta a entrada
> na §4 e regista na §2.6 qualquer decisão nova. Esta atualização vai no mesmo commit
> que o código.

---

## 1. Ponto atual (atualizar sempre ao parar)

| Campo | Valor |
|-------|-------|
| Bloco em curso | **B5 — FEITO** (sem commit). B3 com commit `7c476a3`. Próximo: B6 (depende de B0, B4, B5) ou B8 (B4, B5) |
| Passo do bloco | Todos os critérios de aceitação do B5 cumpridos |
| Estado deixado | B5 no working tree, sem commit. Dev (`tests/conformance/results/2026-11-23/B5-dev.txt`): mTLS 147/147 (S08, matriz D4 por par, S09 por par, sem retoma de sessão, estático); guarda de validade e identidade do servidor nos clientes 14/14; funcional 9/9 (wss pelo nginx, `expand_ai`→`generative-mock`, eliminação de conta `users`→`projects`); quota 10/10; matriz 112/112; identidade 92/92; rotas 552/552; smoke 12/12; F02; F08 6/6; F01 8/8 e 74/74 (`F01-194817.txt`). `EXP --quick` (`evaluation/results/EXP-20261123T195259Z/report.md`): S03 0/8, S21 10,48/6,41 ms (BF 6,12/3,46; +4,4/+3,0 ms), S05 100%, S01 0/15, S02 0/20, S16 0/24, S17 0/15, S18 0. A `picturas-nfr-exp` ficou ativa; a `picturas-dev` está desmontada, com volumes |
| **Próximo passo exato** | Commit do B5 pelas pessoas (`docker-compose.yaml`, `nginx/nginx.conf`, `ops/pki.sh`, `*/tls/pkiTls.js` (7 cópias: `users`, `subscriptions`, `projects`, `apiGateway`, `imageStorageService`, `wsGateway`, `frontend`), `users/bin/www`, `subscriptions/bin/www`, `projects/bin/www`, `apiGateway/bin/www`, `imageStorageService/server.js`, `imageStorageService/services/{s3Client,bootstrapBucket}.js`, `wsGateway/index.js`, `apiGateway/routes/{projects,subscriptions,users}.js`, `projects/routes/projects.js`, `projects/utils/{httpsAgent,imageStorage}.js`, `users/routes/users.js`, `frontend/server-https.js`, `frontend/Dockerfile`, `frontend/lib/queries/projects.ts`, `generative-mock/server_tls.py`, `generative-mock/Dockerfile`, `Tools/expand_ai/expand_ai.py`, `tests/conformance/runner.Dockerfile`, `tests/conformance/README.md`, `tests/conformance/mtls-pki/{b5-mtls.py,b5-guard.sh,b5-functional.py}`, `tests/conformance/results/2026-11-23/{B5-dev.txt,F01-194817.txt}`, `evaluation/results/EXP-20261123T195259Z/`, `README.md`, `AGENTS.md`, `docs/refactor-handoff.md`). **Noutras instalações:** depois do pull, correr `ops/pki.sh issue frontend` e `ops/pki.sh issue generative-mock` (decisão 27), senão o healthcheck destes dois falha e o nginx não arranca. Depois: parar a `picturas-nfr-exp` sem `-v` e seguir para o B6 ou o B8 |
| Coisas meio feitas | Nenhuma |
| Testes a falhar neste momento | Nenhum |
| Último commit com o trabalho | `7c476a3` (B3); B5 sem commit |
| Atualizado em | 2026-11-23 |

## 2. Contexto comum (o que já está decidido)

Tudo o que está nesta secção está **fechado**. Uma sessão não o volta a discutir nem o
altera por iniciativa própria. Se encontrar um problema real com uma decisão, abre uma
dúvida na §5 e pára esse ponto até haver resposta.

### 2.1 O projeto e o objetivo

- **PictuRAS:** editor de imagem e vídeo em microserviços Docker Compose (ver
  `AGENTS.md`).
- **Fase 2:** melhorar dois requisitos não funcionais por refatoração, sem perder
  funcionalidade, e provar a melhoria com uma medição antes (BF) e depois (MF).
  - **RNF 1 — Segurança, autorização ponta a ponta (QC-06):** cenários QS-01 e QS-07.
  - **RNF 2 — Eficiência, recursos no upload (QC-05):** cenário QS-02.
- **Entrega:** 27/11/2026. **Base oficial:** commit `0523102`.
- **Não há clientes nem dados reais.** A entrega parte de um reset geral (§2.6, decisão
  15): nada de migrações nem preservação de sessões, contas ou volumes antigos.
- **Métricas, mínimos e alvos:** [metricas.md](metricas.md).
  - Principais de segurança: S01, S02, S03, S04, S12, S16, S17, S18.
  - Principais de upload: U01, U20, U19, U18, U04, U08.
  - Guardas: S05, S21, U09, U25, U15, U17, U10.
  - Uma guarda que falhe invalida a melhoria.

### 2.2 Medição

- **BF oficial:** `evaluation/results/BF-20261121T013224Z`, medida a 21/11 no Mac
  (Apple M4 Pro) de quem faz as medições. Todos os principais da BF falham, como era
  esperado; a S05 e a U15 estão a 100%.
- **Ferramenta `evaluation/med.py` congelada** (versão `638516104ae9`, registada na
  BF com `med.py freeze`):
  - qualquer alteração ao `med.py`, ao `medlib/`, ao `criteria.yaml` ou aos `cases/`
    invalida o `compare`;
  - o plano §6 prevê só duas alterações: o formato do join WS (§2.6, decisão 3) e as
    opções de TLS dos canais de dados (§2.6, decisão 13). Ambas mantêm o comportamento
    da BF por omissão e levam `freeze` e registo.
- **A MF corre no mesmo Mac**, com `--campaign MF`, na stack isolada `picturas-nfr`.
  Medições noutros computadores são sempre `EXP` e não entram no `compare`.
- **O `compare` só classifica** se o host, os limites, o corpus, os critérios, os casos
  e a versão da ferramenta forem iguais aos da BF.
- **A U04 mede o SeaweedFS reiniciado antes de cada amostra** (revisão de 21/11). O
  nginx já cumpre o alvo na BF e funciona como guarda; a melhoria vê-se no SeaweedFS.
- **Limitação conhecida da U08:** a amostragem é a cada 100 ms, e os ficheiros que
  existem menos tempo podem escapar. Decide pelos uploads de 500 MiB.
- **TLS de servidor nos canais de dados** (Mongo, RabbitMQ, S3): faz parte da opção A e
  implementa-se no B2, mas **não conta** para o gate da S16/S17 (decisão de 20/11). A
  S16/S17 medem as credenciais e o privilégio mínimo; por isso os ataques do `med.py`
  passam pelo TLS (§2.6, decisão 13). O TLS regista-se como evidência adicional.

### 2.3 Decisões de arquitetura (todas escolhidas)

O detalhe de cada uma está no documento indicado no plano. Resumo de uma linha:

| ID | Decisão |
|----|---------|
| D1 | Proteger todas as superfícies: entrada pública, rede Docker/portas, BD e S3 |
| D2 | O gateway faz as verificações baratas; a `projects` decide a posse e a partilha |
| D3 / JWT-C1 A | JWT de utilizador HS256 (segredo novo, 7 dias absolutos, sem refresh). Identidade interna RS256 emitida pelo gateway, ≤30 s, com `aud`/contexto/peer; sem anti-replay |
| D4 | mTLS entre serviços internos, com identidade específica e lista de pares/operações; CA válida não basta |
| Opção A | mTLS nas APIs internas; TLS validado nos outros canais; credenciais próprias e privilégio mínimo em Mongo/RabbitMQ/S3; não é mTLS universal |
| D5 | Portas internas só em loopback (mínimo da S18). Concretizado com o alvo: nenhuma porta interna publicada (§2.6, decisão 5) |
| D6.1 | WebSocket exige JWT válido, incluindo anónimos; a ligação termina quando o JWT expira |
| D6.2 B | Cada entrada numa sala consulta a `projects`; sem bilhetes WS; falha → recusa temporária |
| D6.3 A | Revalidação a cada 1 s; corte ≤5 s (alvo ≤2 s); autorização local ≤5 s desde o início da consulta positiva; falhas não renovam |
| D7 | `?owner=` ausente → permitido; presente → valor único igual ao dono do caminho; senão → recusa |
| D8 / LINK-C1 A | Links de partilha válidos até serem revogados; sem `expiresAt` |
| D9 | `users` e `subscriptions` no âmbito |
| D10 | Testes no host e num contentor não confiável na rede, separando rede/TLS/identidade/domínio |
| D11 | Token de upload com verificação própria simplificada, reclamação atómica |
| WS-C1 A | ws_gateway → projects por mTLS, delegando a identidade verificada |
| WS-C2 A | Timeout total de 1 s; até 50 avaliações por pedido |
| WS-C3 A | 4 consultas globais, 1 por projeto, 64 KiB por corpo |
| WS-C4 A | 16 lotes pendentes, 1 por projeto; o mais recente substitui sem adiar o prazo |
| WS-C5 B | 512 ligações e 4096 contextos por processo; 32 salas por ligação; 4 vias por sala; limites de taxa e de bytes |
| PKI-C1 A | CA por instalação (365 dias), certificado por serviço (30 dias), renovação a 7 dias; o script entra na entrega |
| PKI-C2 B | Retirar confiança = CA nova e reemissão de todos os certificados; sem CRL |
| PKI-C3 A | Manutenção com isolamento e reinício controlado; uma aplicação parcial fica isolada |
| PKI-C4 B | Isolamento ≤30 s (alvo ≤10 s) desde o comando; substituição medida num piloto |
| PKI-C5 A | Matriz completa de canais, testes automáticos e no browser (sem ultrapassar avisos); generative-mock com mTLS |
| OPS-C1 A | Ferramenta administrativa de reconciliação, ensaiada; sem replay automático |
| SESS-C1 A | Transição do segredo e recuperação de anónimos assistidas pelo administrador; nunca criar outra identidade em silêncio |
| ACL-C1 A | Só o dono elimina o projeto; o editor edita e remove media; o leitor não elimina |
| UP-C1 A | Fluxo novo de upload (pedido → PUT pelo nginx → confirmação) **e** o POST antigo mantido por um adaptador seguro (autenticação antes do corpo, streaming, motor comum) |
| UP-C2 A | O upload não cobra nem reserva quota; a quota só se cobra no Apply |
| UP-C3 A | Tentativas numa coleção própria e staging controlado; pendentes nunca visíveis |
| UP-C4 A | Um PUT por tentativa, sem retoma; se for interrompido, faz-se uma tentativa nova |
| UP-C5 A | Token 300 s, tentativa 900 s, corpo 600 s com 30 s sem dados, 3 vagas globais, 16 pendentes, 4096 registos |
| UP-C6 A | Candidato imutável e commit condicional no documento do projeto |
| UP-C7 A | Hash depois do `ready`, em segundo plano; cache desligada enquanto falta o hash; **dúvida de segurança registada, com 5 condições** no [ciclo de vida](architecture/fase2-upload-ciclo-vida.md#seleção-de-21112026) |
| UP-C8 A | `ffprobe` sobre o candidato, com leitura e tempo limitados, sem spool |
| UP-C9 A | PUT autenticado antes do corpo, com comprimento conhecido; limpeza ativa a cada 5 s; journal de 24 h |

### 2.4 O que já aconteceu (não repetir)

| Data | Facto |
|------|-------|
| 20/11 | Métricas e plano de medição escolhidos; o `med.py` foi implementado |
| 21/11 | BF oficial medida; U09/U10 recalculadas só com uploads aceites; U04 medida de novo com o SeaweedFS reiniciado |
| 21/11 | Ferramenta corrigida depois da revisão de um colega: proteção de outras instalações, `compare` bloqueante, U20 com OOM, cobertura das matrizes, ACL na S05. Versão congelada na BF |
| 21/11 | UP-C4 a UP-C9 escolhidas (A em todas) |
| 21/11 | No Mac das medições, o projeto Docker antigo `picturas` (volumes da Fase 1) e a pasta `picturas-27-extension` foram apagados. O commit não enviado e um ficheiro foram guardados em `~/Documents/GitHub/picturas-27-extension-salvado` |
| 21/11 | Plano de refatoração (fase 0) e este documento criados; dúvidas D-01 a D-12 respondidas (§2.6) |
| 21/11 | Plano verificado contra todas as decisões, em 3 rondas: acrescentados a promoção premium pela subscrição, o `$set` que preserva as barreiras, o nginx sem buffering no POST de vídeo, as rotas novas do `img_storage`, o utilizador administrativo dos dados, os testes do adaptador e da quota, e as regras WS de leave, leitor e limitador. Notas de atualização postas nos documentos de origem afetados pelas respostas D-01/02/05/06/07/09/11 |
| 21/11 | Segunda verificação ("estamos mesmo prontos?"): corrigidos os blocos afetados por cada spike, as dependências (B4←B1, B6←B4, B9←B8), as stacks de verificação (`picturas-nfr-exp`) e o local dos resultados de conformidade. Encontrado e decidido o D-13 (o `med.py` precisa de opções de TLS nos canais de dados) |
| 21/11 | Terceira verificação: imagens sem versão fixa (nginx, watermark, `FROM node`) passam a ser fixadas às da BF (B0); risco das vagas de upload acrescentado ao critério do B6; textos do handoff atualizados |
| 21/11 | Quarta verificação, sobre a compatibilidade do plano com o `med.py`: a deteção do processo Node funciona com `node`; o adaptador mantém o campo `video`, o 204 e o `X-Project-Version`; os media `ready_hash_pending` aparecem na listagem com `media_type: video`. Encontrado e decidido o D-14 (a cópia de 500 MiB para o candidato conta na U09) |
| 21/11 | Quinta verificação, sistemática: 122 requisitos extraídos dos documentos de decisão, procurados um a um no plano; 4 em falta e 4 valores incompletos, todos corrigidos (`/s3/` com GET/HEAD/Range e URL expirado, configuração nginx do `auth_request`, limite de 3 tentativas pendentes por sujeito, `ffprobe` sem redirects, geração do hash, limpeza de multipart incompletos). Sem contradições restantes |
| 21/11 | Sexta verificação, a pedido ("só sair quando tudo a 100%"), em cinco rondas até uma ronda limpa. **A:** releitura integral, 22 falhas. **B:** todas as frases normativas dos 9 documentos (≈230) e as 227 linhas de tabela, conferidas uma a uma; 40 pontos acrescentados ao plano. **C:** alternativas rejeitadas listadas como "não implementar" (§9). **D:** presets e a sua partilha em falta, o que revelou a falta de uma matriz de rotas; acrescentada ao B4 (exigida por D1/D2). **E:** regressão do B12 comparada com as funcionalidades do `AGENTS.md`; acrescentados perfis, quota, IA/generative-mock, watermark, preview, trim/speed, PDF, eventos, presets e eliminação de conta. **F:** volumes partilhados (`image_data`, `whisper_models`) e as métricas U04/U10 em falta no critério do B6. **G:** cada uma das 21 métricas tem critério de aceitação num bloco; termos e referências conferidos; ronda limpa |
| 21/11 | Indicação do utilizador: não há clientes reais e a entrega parte de um reset geral (D-15). Retirados do plano o inventário, a transição do segredo sobre dados reais, a recuperação dos anónimos antigos e as migrações; mantida a ferramenta de reemissão assistida para expirações futuras. Notas de atualização no inventário e na recuperação anónima |
| 21/11 | Check geral depois do D-15: corrigida a frase do B9 que podia ser lida como ordem para apagar instalações de outros computadores; retirado o "inventário" da origem do B9; testes de sessões explicitamente só com fixtures. Verificações automáticas (termos, referências, links) limpas; `main` igual ao `origin/main`; o branch `fase2-refactor` ainda não existe. **Pronto para avançar** |
| 21/11 | Recheck por iterações, com o reset em conta. **1:** healthchecks do B3 têm de passar a HTTPS no B5; depois do reset, o frontend tem de dar uma escolha explícita quando a sessão guardada é recusada; o estado de partida passa a referir o reset. **2:** limites de corpo do nginx coerentes entre B6 e B7; B11 depende do B10; título e formatação do B9; `PICTURAS_SECRETS_DIR` antes do `stack up`. **3:** corte K2 coerente com o D-15. **4:** §6 (alteração aprovada, variáveis do `.env.med` nas verificações EXP) e D-14/D-15 na matriz. **5:** verificação automática (termos, referências, links, dependências, números das decisões): limpa |

### 2.5 Convenções de trabalho

- **Os agentes nunca fazem commit nem push.** As pessoas fazem os commits.
- Código, comentários e mensagens ao utilizador em inglês; documentação da Fase 2 em
  português (`AGENTS.md`).
- Respeitar os fins de linha existentes de cada ficheiro (alguns são CRLF). Não
  reformatar código que não está a ser alterado.
- Não fazer `docker system/volume/image prune`. Não usar o projeto `picturas-nfr` para
  desenvolver.
- Sem segredos no Git, nas imagens, nos logs ou nos relatórios (JWT, chaves, palavras-
  passe, URLs assinados, shareIds).
- Uma lacuna que não se consiga fechar fica declarada, nunca escondida.

### 2.6 Decisões tomadas durante a implementação

Inclui as respostas às dúvidas D-01 a D-15 do plano e as decisões das sessões
seguintes. **Só se acrescenta.** Cada linha indica a data, a decisão, o motivo e quem
decidiu (pessoa ou "equipa").

| # | Data | Decisão | Motivo | Decidido por |
|---|------|---------|--------|--------------|
| 1 | 21/11 | D-01: o frontend passa ao fluxo novo de upload (B7) | Cumprir a UP-C1 A por inteiro | Utilizador |
| 2 | 21/11 | D-02: o adaptador do POST antigo leva o ficheiro em fluxo até ao staging e usa o motor comum | Um só motor de validação; a U08 pode cumprir o alvo | Utilizador |
| 3 | 21/11 | D-03: o `med.py` ganha `MED_WS_JOIN_FORMAT=legacy|v2` (BF legacy, MF v2), com `freeze` e registo | Sem isto, os controlos WS falham na MF por causa do protocolo | Utilizador |
| 4 | 21/11 | D-04: os serviços Node correm com `node` + `restart` + `healthcheck`; `nodemon` só no override de desenvolvimento | Na BF, um OOM deixou a app morta até intervenção manual | Utilizador |
| 5 | 21/11 | D-05: retirar todas as portas internas publicadas (só fica o nginx 8080) | Alvo da S18 | Utilizador |
| 6 | 21/11 | D-06: métricas oficiais de upload pelo POST antigo; o fluxo novo é provado à parte (testes + EXP) | Manter a comparação com a BF | Utilizador |
| 7 | 21/11 | D-07: watermark com imagem derivada (`Tools/watermark/`) e patch que ativa o TLS | O pika suporta TLS, mas o código da imagem não o ativa (verificado na imagem) | Utilizador |
| 8 | 21/11 | D-08: cada elemento faz o inventário de sessões da sua instalação até 24/11. **Sem efeito pela decisão 15** | Condição para trocar o segredo HS256 nas instalações reais | Utilizador |
| 9 | 21/11 | D-09: sem datas fixas; cada bloco e cada ensaio (incluindo o piloto PKI-C4) avança assim que as dependências estiverem prontas; o marco de 23/11 às 18:00 fica substituído | Trabalhar o mais depressa possível | Utilizador |
| 10 | 21/11 | D-10: spike curto com `GOMEMLIMIT`/`GOGC` no SeaweedFS; aplicar se reduzir a U04 | A memória do SeaweedFS não depende do nosso código | Utilizador |
| 11 | 21/11 | D-11: pode começar-se a implementar | A BF existe e as decisões estão todas tomadas | Utilizador |
| 12 | 21/11 | D-12: trabalhar só no branch `fase2-refactor`; nunca abrir um PR para o `main` do upstream (prcsousa) | Instrução do utilizador | Utilizador |
| 13 | 21/11 | D-13: o `med.py` ganha opções de TLS por variável de ambiente para S3, AMQP, gestão do RabbitMQ e Mongo (por omissão = BF), com `freeze` e registo; faz-se no B2 | Sem isto a MF parte (U04, S03, S17) ou mede o TLS em vez das credenciais (S16, S17) | Utilizador |
| 14 | 21/11 | D-14: no adaptador do POST antigo, decide o SP-03. Se o CopyObject de 500 MiB couber na U09, staging → candidato (UP-C6 à letra); senão, escrita direta numa chave de candidato nova e única, que o cliente nunca pode escrever | A cópia entra no tempo da U09 (<3 s) | Utilizador |
| 15 | 21/11 | D-15: não há clientes reais; reset geral. Caem o inventário de sessões (D-08 sem efeito), a transição do segredo sobre dados reais, a recuperação dos anónimos antigos e as migrações de media e links. Mantém-se a ferramenta de reemissão assistida (emissor e `/session-recovery`) para anónimos que expirem no futuro | Indicação do utilizador; a SESS-C1 A cobre também a expiração futura | Utilizador |
| 16 | 21/11 | B0, execução: as imagens fixam-se com tag e digest (`node:26.13.1-trixie@sha256:e18c…`, `nginx@sha256:84f7…`, `…watermark…@sha256:5340…`); o `node:18` do `wsGateway`/`frontend` fica igual (é o mesmo 18.20.8 da BF e a linha terminou); os harness dos spikes ficam em `tests/spikes/SP-xx/`; a F01 corre nas imagens do produto (`tests/conformance/run-f01.sh`), porque o ffmpeg do host pode não ter `libass` | Comparabilidade BF/MF e repetibilidade dos ensaios, dentro do que o plano (B0) pede | Agente (sessão B0), dentro do plano; a confirmar no commit |
| 17 | 22/11 | D-16: no adaptador, escrita direta numa chave de candidato nova e única, que o cliente nunca pode escrever (alternativa prevista no D-14); e volumes do SeaweedFS pré-criados no arranque, para evitar a pausa de ~6 s que também afeta o PUT | O CopyObject de 500 MiB chegou a 6,2 s (U09 falha) e soma ~100 MiB à U04 (SP-03) | Utilizador |
| 18 | 22/11 | D-17: o `ffprobe` lê por um relé em loopback dentro da `projects`, que reencaminha para o SeaweedFS por HTTPS validado e corta ao atingir 2×F+16 MiB | O `ffprobe` não tem limite de bytes, só de tempo (SP-05); o relé não é um salto de rede | Utilizador |
| 19 | 22/11 | D-18: o exchange `picturas` passa de `direct` a `topic`, com as mesmas routing keys e permissões por routing key para cada principal; clientes com declarações passivas; o watermark muda só por variável | Com `direct`, a permissão de escrita vale para o exchange inteiro (SP-07); com `topic`, o destino não autorizado dá 403 | Utilizador |
| 20 | 22/11 | D-19: o master, o volume e o filer do SeaweedFS ficam só em loopback; da rede ficam o S3 (9000) e o gRPC do S3 com mTLS; o TLS/mTLS internos mantêm-se. A rota `/s3-console/` do nginx (filer sem autenticação) é retirada | O HTTPS interno do SeaweedFS aceita qualquer certificado da CA (SP-11), contra o D4; o filer publicado em `/s3-console/` dá acesso a todos os ficheiros | Utilizador |
| 21 | 22/11 | B1, execução: os segredos escalares chegam a cada serviço por `env_file: $PICTURAS_SECRETS_DIR/env/<serviço>.env` (gerado por `ops/secrets.sh render`, só com o que esse serviço usa) e as chaves/certificados por diretório montado só para leitura (`/run/secrets/pki`, nginx em `/etc/nginx/pki`). Os utilizadores do broker vão para um `definitions.json` gerado (topologia do repositório + `password_hash`), porque o RabbitMQ ignora `RABBITMQ_DEFAULT_USER` quando importa definições (provado). **Interinos até ao B2:** um admin S3 (SeaweedFS por `AWS_*`, usado pelo `img_storage`) e um admin do broker partilhado pelos clientes; o B2 passa a uma credencial por principal (já geradas) | Retirar os segredos do Git sem mudar o código dos serviços que leem variáveis de ambiente; o B2 já prevê o privilégio mínimo | Agente (sessão B1), dentro do plano; **confirmada pelo utilizador a 23/11** |
| 22 | 22/11 | B1, execução: CA e certificados ECDSA P-256 (CA 365 d, serviço 30 d, renovação a 7 d), SAN = nome Docker do serviço (nginx também `localhost`/`127.0.0.1`), EKU por papel; par RS256 de 3072 bits; sem valores por omissão com credenciais no código (`Tools/utils/env.py`, `imageStorageService/services/s3Client.js`), e o `IMG_STORAGE_URL` do `env.py`, que lia `RABBITMQ_PASSWORD`, passa a ler `IMG_STORAGE_URL` | Os spikes provaram ECDSA em todos os clientes (Node, pika, Mongo, Go, nginx); um valor por omissão com credencial é um segredo publicado | Agente (sessão B1), dentro do plano; **confirmada pelo utilizador a 23/11** |
| 23 | 23/11 | D-20: criar o bucket `picturas` num job Compose de arranque único, idempotente; `img_storage` espera por `service_completed_successfully`. A credencial admin é montada só no job e não aparece em logs. O job apenas cria o bucket quando falta; não apaga nem altera outros objetos ou buckets | O `img_storage` precisa de privilégio mínimo sem `CreateBucket`, e o `med.py` monta a stack só com `docker compose up`, sem passo manual | Utilizador |
| 24 | 23/11 | D-21: `limits.fileSize` das imagens no gateway = 25 MiB (variável `IMAGE_MAX_BYTES`), resposta 413 sem chegar à `projects` | O plano (B4, ideia 8) pede o limite sem fixar o valor; cobre fotografias de 24 MP em PNG e reduz o buffer do multer | Utilizador |
| 25 | 23/11 | Defeito da quota: `PUT /users/:user/process/:n` deixa de chamar `operations.remove()` sobre o objeto `toJSON()` e filtra o registo do dia atual | Dava 701 na 2.ª operação do dia; corrigido antes do B3 | Utilizador |
| 26 | 23/11 | B3, execução: os 6 serviços Node correm `node` com `init: true` (o `docker-init` reencaminha sinais e recolhe filhos, p. ex. o `ffprobe`), `restart: on-failure` e `healthcheck` (um pedido ao próprio serviço; HTTPS com a CA e o certificado do próprio serviço onde o servidor exige cliente; qualquer resposta <500, incluindo a recusa de autorização, conta como viva). `mem_limit`: `api_gateway`, `projects`, `img_storage` 2g (iguais aos do `med.py`), `users` e `ws_gateway` 512m, `subscriptions` 256m (uso em repouso 35–100 MiB). O nginx espera `api_gateway`/`ws_gateway` *healthy*, e o `api_gateway` espera `projects`/`users`/`subscriptions` *healthy*. O bind mount morto do `frontend` (`./frontend:/app`; a imagem serve `/usr/src/app`) foi retirado. Override `docker-compose.dev.yaml` com nodemon e bind mounts para `users`/`subscriptions`/`api_gateway`, sem portas | Plano B3 (D-04, D-05, ideia 2); o `med.py` lê só o `docker-compose.yaml` | Agente (sessão B3), dentro do plano; a confirmar no commit |
| 27 | 23/11 | B5, execução: módulo `tls/pkiTls.js` idêntico em cada serviço Node (servidor mTLS com `SSL_OP_NO_TICKET`, agente cliente com o próprio certificado e `maxCachedSessions: 0`, lista de pares por CN, guarda de validade que recusa arrancar e termina o processo quando o próprio certificado expira; com `restart` fica suspenso até à renovação). `api_gateway`, `ws_gateway` (via `allowRequest`) e `frontend` (servidor HTTPS próprio, SP-09) só aceitam o par `nginx`; `generative-mock` só `expand_ai_tool`, em TLS 1.3 sem tickets. O nginx apresenta o seu certificado de cliente, verifica nome e CA e não retoma sessões em nenhum upstream. Para os healthchecks em HTTPS com certificado de cliente, o `frontend` e o `generative-mock` passam a ter EKU `serverAuth,clientAuth` em `ops/pki.sh` (reemitidos; a lista de pares recusa-os com 403). Sem keep-alive entre saltos (a S21 ficou dentro do alvo sem isso). O `.env.med` não muda: os esquemas por omissão já são `https` e o `med.py` não usa o certificado de cliente | Plano B5 (D4, opção A, PKI-C3 A, PKI-C5 A; SP-09, SP-10) | Agente (sessão B5), dentro do plano; a confirmar no commit |
| 28 | 23/11 | S21: o keep-alive no upstream do nginx (com `keepalive_timeout` abaixo dos 5 s do Node) só se aplica se uma `EXP` do B6 ou do B8 der S21 > +5 ms; aplica-se nesse bloco | A S21 cumpre o alvo depois do B5 (+4,4/+3,0 ms, `EXP --quick`); não se mexe no que cumpre | Utilizador |
| 29 | 23/11 | Sem cortes: os blocos K1–K5 da §7 do plano não se aplicam; fazem-se todos os blocos. Um corte só com nova decisão do utilizador | O objetivo é fazer tudo | Utilizador |
| 30 | 23/11 | Divisão B6/B8 em duas máquinas, as duas no branch `fase2-refactor`. Cada bloco só vai para commit depois de verificado (dev + `EXP`) na sua máquina; antes de cada push, `git pull --rebase origin fase2-refactor`; se houver conflito, quem o resolve repete a conformidade antes do push. A verificação conjunta é feita no B12, na máquina da BF. Regras de não-conflito: ver §6.2 | Duas pessoas, cada uma com a sua stack; poucos commits, todos verificados, por isso os conflitos aparecem cedo e pequenos, em vez de um merge final | Utilizador |

## 3. Estado dos blocos

Estados: `POR FAZER`, `EM CURSO`, `BLOQUEADO` (com motivo), `EM VERIFICAÇÃO`, `FEITO`.
`FEITO` quer dizer que o critério de aceitação do bloco passou e o resultado ficou
guardado.

A ordem do plano é a recomendada. Um bloco pode começar antes da sua vez se as
dependências estiverem `FEITO`.

| Bloco | Depende de | Estado | Verificação (link para o resultado) | Notas |
|-------|-----------|--------|-------------------------------------|-------|
| B0 — Spikes e preparação | — | FEITO | [`refactor-spikes.md`](refactor-spikes.md); bruto em `tests/spikes/SP-xx/results/`; F01 em `tests/conformance/results/2026-11-21/` | 11 spikes: 6 suportados, 5 suportados com limitações (D-16 a D-19) |
| B1 — PKI e segredos | B0 | FEITO | `tests/conformance/results/2026-11-22/` (`B1-pki-secrets-check`, `B1-S19-git-grep`, `B1-S19-markers`, `B1-smoke`, `B1-old-credentials`, `F01-033956`); `med.py` EXP S05 `--quick` = 100% | Commit `1ab09fa`; S19: o histórico Git mantém as chaves antigas e as palavras-passe do spike SP-06 do commit B0 (contentores descartáveis), limitação declarada sem reescrever histórico |
| B2 — Mongo/RabbitMQ/S3 | B1 | FEITO | `tests/conformance/results/2026-11-23/B2-dev.txt`; `F01-144716.txt`; `evaluation/results/EXP-20261123T152036Z/report.md` (S16); `EXP-20261123T145611Z/report.md` (S17/S05); BF `med.py freeze` `2dfe2a7ad06c` | D-20 implementada com job Compose idempotente; Mongo, broker, watermark, S3 TLS e D-13. Dev: backup/restauro, permissões, URLs assinados, S05/F02 e F01. EXP `--quick`: S16 0/24, família b `NAO_APLICAVEL`; S17 0/15; S05 100%. Commit `4653219` |
| B3 — Portas e supervisão | — | FEITO (commit `7c476a3`) | `tests/conformance/results/2026-11-23/B3-dev.txt`, `quota-dev.txt`, `F01-192508.txt`; `evaluation/results/EXP-20261123T193037Z/report.md` (S18 = 0, S05 100%) | Só o nginx publicado (12 portas retiradas); `node` + `init` + `restart` + `healthcheck` + `mem_limit` (§2.6, decisão 26); F08 6/6 ≤2,5 s; override de desenvolvimento. Correção da quota incluída (decisão 25). Sem commit |
| B4 — Identidade e autorização HTTP | B1 | FEITO | `tests/conformance/results/2026-11-23/B4-dev.txt`, `B4-exp.txt`, `F01-172145.txt`; `evaluation/results/EXP-20261123T184517Z/report.md` (S01 0/15, S02 0/20, S05 100%) | Matriz `docs/refactor-matriz-rotas.md` (112 rotas/verbo); sessão HS256 com typ/iss/aud; identidade RS256 gateway→destino com peer mTLS, rota, método, share, ≤30 s; D7; ACL-C1; D9; `img_storage` só aceita o certificado da `projects`; D-21 (25 MiB). Commit `56328df` |
| B5 — mTLS e TLS por salto | B1 | FEITO | `tests/conformance/results/2026-11-23/B5-dev.txt`, `F01-194817.txt`; `evaluation/results/EXP-20261123T195259Z/report.md` (S03 0/8, S21 +4,4/+3,0 ms, S05 100%; S01/S02/S16/S17/S18 sem regressão) | Todos os saltos em TLS validado; mTLS com lista de pares (matriz D4); sem retoma de sessão; guarda de validade; healthchecks em HTTPS (decisão 27). Sem commit |
| B6 — Upload: motor e adaptador | B0, B4, B5 | POR FAZER | — | A escrita do adaptador (cópia ou direta) ficou na **D-16**, e o limite de leitura do `ffprobe` na **D-17**. Notas do SP-01, SP-03 e SP-05 |
| B7 — Upload: fluxo novo | B6 | POR FAZER | — | Inclui o frontend (§2.6, decisão 1). Configuração do `auth_request` (SP-01, notas 1–4) e do `Host` assinado (SP-04) |
| B8 — WebSocket | B4, B5 | POR FAZER | — | Inclui o formato do join no `med.py` (§2.6, decisão 3) |
| B9 — Sessões e recuperação | B4, B8 | POR FAZER | — | Sem migração (reset, §2.6, decisão 15); mantém a ferramenta de reemissão assistida |
| B10 — Operação da PKI | B1, B2, B5 | POR FAZER | — | O piloto corre assim que estiver pronto (§2.6, decisão 9) |
| B11 — Reconciliação (OPS-C1) | B2, B10 | POR FAZER | — | Usa o isolamento do B10 |
| §5 — Testes de conformidade | cresce com cada bloco | EM CURSO | `tests/conformance/results/2026-11-21/F01-202134.txt`, `…/2026-11-22/` | F01 registado; grupo `mtls-pki/` com `s19-markers.sh`, `s19-git-grep.sh` e `b1-smoke.py` |
| B12 — Verificação final e MF | B0–B11 | POR FAZER | — | |

## 4. Diário (só se acrescenta; nunca se apaga)

Uma entrada por sessão, no fim da lista, ao parar.

```
### <AAAA-MM-DD HH:MM> — <bloco> — <estado ao parar>
- Feito: <passos do bloco concluídos, com ficheiros>
- Verificado: <comandos corridos e resultado; link para o bruto>
- Parei em: <passo exato e ficheiro/linha, ou "bloco concluído">
- Próximo passo: <a primeira coisa a fazer ao retomar; igual à §1>
- Cuidado: <armadilhas, decisões tomadas, coisas meio feitas, testes que falham>
- Decisões novas: <número na §2.6, ou "nenhuma">
- Dúvidas novas: <número na §5, ou "nenhuma">
```

### 2026-11-21 20:30 — B0 — FEITO (dúvidas D-16 a D-19 abertas)
- Feito: branch `fase2-refactor` criado a partir do `main` (`4cacb55`). Spikes SP-01 a SP-11, com harness e bruto em `tests/spikes/SP-01..SP-11/`, e resultados em `docs/refactor-spikes.md`. Imagens fixadas às da BF em `docker-compose.yaml` (nginx, watermark) e no `FROM` de `users/`, `apiGateway/`, `subscriptions/`, `projects/` e `imageStorageService/` (os dois últimos usam `from` em minúsculas; mantidos o estilo e o CRLF). Criado `tests/conformance/` (`README.md`, `run-f01.sh`) e registada a F01. Link para os spikes acrescentado ao índice `docs/README.md`.
- Verificado: cada spike no projeto Compose `picturas-spike` (já desmontado, sem volumes restantes). `docker compose -p picturas-dev build` dos 5 serviços Node com a base fixada: passou. `tests/conformance/run-f01.sh picturas-nfr`: Node 8/8 e vídeo 74/74 (`tests/conformance/results/2026-11-21/F01-202134.txt`). Nenhuma alteração ao `picturas-nfr` (só se correram contentores descartáveis a partir das suas imagens) nem a `evaluation/`.
- Parei em: bloco concluído.
- Próximo passo: o da §1 (commit do B0, respostas D-16 a D-19, começar o B1).
- Cuidado: (1) As variáveis `AWS_*` no `seaweedfs` criam um admin S3 (SP-02). (2) O `management.tcp.port = 0` do RabbitMQ abre a API em HTTP numa porta aleatória (SP-07). (3) O `rabbitmqctl` como root antes do arranque parte o broker (cookie). (4) O `ffprobe` e o `mongodump` escrevem URLs/URIs com segredos nos erros. (5) `proxy_ssl_session_reuse` tem de estar `off` (SP-09). (6) A `location = /_auth` do nginx precisa do mesmo `client_max_body_size` do upload (SP-01). (7) Num bind mount de um só ficheiro, um editor que substitui o inode deixa o contentor com a versão antiga. (8) Os harness usam PKIs descartáveis geradas por script; não há chaves no Git (`tests/spikes/.gitignore`).
- Decisões novas: 16.
- Dúvidas novas: D-16, D-17, D-18, D-19.

### 2026-11-22 04:00 — B1 — FEITO (falta a verificação `med.py` EXP)
- Feito: `ops/pki.sh` (`init`/`issue`/`renew`/`check`/`list`, registo `pki/registry.tsv`) e `ops/secrets.sh` (`init`/`render`/`check`/`med-env`). `docker-compose.yaml`: sem segredos escritos; `env_file` por serviço; certificados montados de `$PICTURAS_SECRETS_DIR`; `definitions.json` do broker gerado. Código: os 9 ficheiros que liam `certs/selfsigned.*` (`projects/bin/www`, `projects/routes/projects.js`, `projects/utils/imageStorage.js`, `projects/utils/httpsAgent.js`, `users/bin/www`, `users/routes/users.js`, `subscriptions/bin/www`, `apiGateway/routes/projects.js`, `apiGateway/routes/subscriptions.js`) leem `/run/secrets/pki/service.{key,crt}`; `nginx/nginx.conf` usa `/etc/nginx/pki`; sem valores por omissão com credenciais (`Tools/utils/env.py`, `imageStorageService/services/s3Client.js`). Retiradas as 6 chaves versionadas e os certificados que as acompanhavam (`certs/`, `apiGateway/`, `frontend/`, `projects/`, `subscriptions/`, `users/`). `rabbitMQ/definitions.json` sem utilizadores (CRLF mantido). `.gitignore` e 10 `.dockerignore` defensivos. Testes em `tests/conformance/mtls-pki/`. Atualizados `README.md`, `AGENTS.md` e `.env.example`.
- Verificado: `ops/pki.sh` com casos negativos (diretório dentro do repositório, `init` repetido, certificado expirado, de outra CA, CA a menos de 30 dias): todos recusados. Os 4 critérios do B1: `ops/pki.sh check` passou; `s19-git-grep.sh` sem nenhum dos 56 segredos atuais (com controlo negativo); `s19-markers.sh picturas-dev` com 44 marcadores ignorados, 10 contextos limpos (com controlo negativo) e 25 imagens limpas; stack `picturas-dev` a arrancar com os segredos montados (32 contentores, smoke 12/12: sessão, upload, URL assinado, pipeline pelo broker; token assinado com `lisan_al_gaib` recusado). Na rede Docker, `user/password`, `guest/guest` e `admin/admin123` recusados. F01 8/8 e 74/74. Nenhum segredo nos resultados.
- Parei em: bloco concluído, exceto a verificação `med.py` EXP S05 `--quick`. A `picturas-nfr` está montada (marcador `evaluation/.run/stack.json`), e montar a `picturas-nfr-exp` exige `med.py stack down` nela: decisão de quem faz as medições.
- Próximo passo: o da §1.
- Cuidado: (1) Sem `PICTURAS_SECRETS_DIR` exportado, o `docker compose` recusa arrancar (é intencional). (2) Nesta máquina, a porta 9090 do host está ocupada por outro processo; a verificação usou um override (no scratchpad) que retira as portas internas, que é o alvo do B3. (3) O `ops/pki.sh check` não corre sozinho no arranque: corre-se antes do `up` (o README e o AGENTS.md mostram a ordem); a guarda em funcionamento é do B5. (4) Para a verificação usei um diretório de segredos descartável no scratchpad; cada pessoa cria o seu. (5) `scale_queue` sem consumidor é igual na BF (não há worker `scale`). (6) Correção ao diário do B0: o `.venv/` já estava no `.gitignore`; o `Tools/video/.venv` não ia aparecer no Git.
- Decisões novas: 21, 22.
- Dúvidas novas: nenhuma.

### 2026-11-22 04:34 — B2 — BLOQUEADO na D-20 (bootstrap S3)
- Feito: B1 confirmado no commit `1ab09fa`. `ops/secrets.sh render` gera 20 utilizadores Rabbit com hashes e permissões de tópico, três pares de utilizadores Mongo por instância, ficheiros privados para o backup e `s3.json` por principal. `rabbitMQ/` usa exchange `topic`, AMQPS e gestão HTTPS; `projects`, `ws_gateway`, workers Python, vídeo e imagem derivada do watermark usam AMQPS com CA validada. As três instâncias Mongo usam `requireTLS`, autenticação e chave privada copiada só para tmpfs dentro do contentor; `projects/users/subscriptions` usam URI por serviço e o backup usa credencial só de leitura sem palavra-passe nos erros. O SeaweedFS usa HTTPS/SigV4 e o master, volume e filer só em loopback; o nginx valida a CA, limita `/s3/` a GET/HEAD e devolve 404 em `/s3-console/`. `img_storage` usa a credencial limitada por HTTPS. A D-13 acrescentou opções TLS ao instrumento com valores por omissão da BF; nota 24 em `evaluation/IMPLEMENTATION_NOTES.md` e `med.py freeze` na BF (`2dfe2a7ad06c`).
- Verificado: `picturas-dev` arrancou antes das alterações; os Mongo passaram TLS/autenticação/escopo e backup só de leitura (`tests/conformance/data-channels/b2-mongo.py`), com dump e restauro administrativo de uma fixture; o broker passou plaintext fechado, credencial antiga recusada, escopo de worker e gestão só para admin (`b2-broker.py`), e após reinício voltaram cinco principais; o watermark processou um pedido AMQPS. S3 passou HTTPS validado, credencial antiga recusada e `img_storage` sem `CreateBucket` (`b2-s3-auth.py`); da rede Docker só 9000 e 19000 respondem, e `/s3-console/` dá 404. Resumo em `tests/conformance/results/2026-11-22/B2-core-partial.txt`. F01 passou (Node e vídeo 74/74, `F01-042446.txt`). `ops/secrets.sh check`, verificação de sintaxe e `git diff --check` com CRLF passaram; 17 logs da stack dev foram varridos sem encontrar valores de segredos.
- Parei em: bootstrap do bucket `picturas`, ainda sem implementação porque a D-20 (§5) aguarda resposta. O caminho `createBucket` de `imageStorageService/services/storage.js` ainda existe; não há bucket da aplicação nesta stack dev. Não correram ainda S05/F02 nem `med.py` EXP do B2.
- Próximo passo: o da §1 (responder à D-20; implementar e verificar antes de usar `picturas-nfr-exp`).
- Cuidado: a `picturas-nfr` estava inesperadamente ativa no início; foi parada sem apagar volumes e a sonda avulsa removida. A `picturas-dev` é a única stack da aplicação ativa. A porta 9090 do host é usada por outra aplicação; antes das alterações B2 foi usado um override temporário fora do repositório. O `mongo:4.4` contém `mongodump` antigo: usa `--ssl/--sslCAFile`, não `--tls/--tlsCAFile`. O `docker cp` para `/tmp` tmpfs do Mongo não persistiu; no ensaio de restauro usou-se `/var/tmp` e limpou-se depois. Os resultados do B2 ainda não cobrem as verificações integradas nem a matriz PKI-C5.
- Decisões novas: nenhuma; o mecanismo de bootstrap S3 continua aberto.
- Dúvidas novas: D-20.

### 2026-11-23 15:00 — B2 — FEITO
- Feito: aplicada a D-20 com `s3-bootstrap` em `docker-compose.yaml`, credencial admin montada só no job e `img_storage` dependente de `service_completed_successfully`; `bootstrapBucket.js` só verifica/cria `picturas` e aceita o bucket existente. Retirada a tentativa de `CreateBucket` do `img_storage`. `ops/secrets.sh med-render` gerou a configuração EXP fora do repositório. Corrigida a validação da CA nos downloads S3 e nas chamadas `projects` → `users`; retirados dos logs do nginx os URLs assinados e do `wsGateway` o corpo das mensagens. B2 inteiro continua sem commit.
- Verificado: `picturas-dev` completa, bootstrap em bucket novo e rerun idempotente com fixture intacta; Mongo TLS/ACL e backup/restauro, Rabbit AMQPS/ACL e reconexão, S3 HTTPS/ACL, GET/HEAD/Range assinado, URL expirado e métodos inseguros recusados, `/s3-console/` 404, smoke 12/12, F02 imagem+vídeo e F01 (Node e vídeo 74/74). Resumo em `tests/conformance/results/2026-11-23/B2-dev.txt`. A `picturas-dev` foi desmontada antes da `picturas-nfr-exp`. `med.py run --campaign EXP --quick --metrics S16,S17,S05`: S16 0/54, S17 0/15, S05 100% (`evaluation/results/EXP-20261123T145611Z/report.md`); a matriz S16/S17 não tem casos em falta. `ops/secrets.sh check`, `ops/pki.sh check` e varrimento de valores de segredos no relatório final e logs dos contentores passaram.
- Parei em: bloco concluído. A `picturas-nfr-exp` ficou ativa; a `picturas-dev` está desmontada sem apagar volumes.
- Próximo passo: o da §1 (B3; parar primeiro a `picturas-nfr-exp`, sem `-v`).
- Cuidado: `git diff --check` acusa os CRLF preservados em três ficheiros (`Tools/utils/rabbit_mq.py`, `rabbitMQ/Dockerfile`, `rabbitMQ/definitions.json`); não são espaços introduzidos. Os resultados EXP preliminares `EXP-20261123T145126Z` e `EXP-20261123T145352Z` foram substituídos pelo ensaio final; nenhum contém segredos atuais. `evaluation/.env.med` é ligação ignorada para ficheiro privado externo. A matriz completa PKI-C5 continua no B10, depois do B5.
- Decisões novas: 23 (D-20, §2.6).
- Dúvidas novas: nenhuma.

### 2026-11-23 15:22 — B2 — FEITO (correção da S16 antes do commit)
- Feito: `tests/spikes/SP-06/sp06.py` lê as palavras-passe das variáveis `SP06_SERVICE_PASSWORD`, `SP06_BACKUP_PASSWORD` e `SP06_WRONG_PASSWORD`, constrói os URI em execução e oculta credenciais em erros; `tests/spikes/SP-06/results/sp06-2.out` tem os URI antigos substituídos por `***`; `ops/secrets.sh` constrói o URI Mongo em partes, sem um padrão de credencial literal. O `med.py` não foi alterado.
- Verificado: `git grep -E 'mongodb://[^:/@" ]+:[^@/" ]+@'` sem resultados; sintaxe Bash/Python e `s19-git-grep.sh` passaram. `med.py run --campaign EXP --quick --metrics S16` na `picturas-nfr-exp`: `credenciais_git_encontradas = 0`, seis casos b como `NAO_APLICAVEL`, 24 tentativas e zero admitidos (`evaluation/results/EXP-20261123T152036Z/`). Esta medição substitui a S16 de 54 tentativas da entrada anterior; S17 e S05 dessa entrada permanecem válidas.
- Parei em: B2 concluído, sem commit. A `picturas-nfr-exp` está ativa e a `picturas-dev` desmontada.
- Próximo passo: o da §1 (B3; parar primeiro a `picturas-nfr-exp`, sem `-v`).
- Cuidado: as palavras-passe do SP-06 ficam no histórico do commit B0; pertenciam apenas a contentores descartáveis, não à instalação. A limitação S19 está declarada no plano §10 e aqui na §3. Não reescrever o histórico.
- Decisões novas: nenhuma.
- Dúvidas novas: nenhuma.

### 2026-11-23 17:40 — B4 — EM VERIFICAÇÃO (falta EXP S01/S02/S05)
- Feito: revisto o B4 deixado sem nota pela sessão anterior, contra o plano e a matriz. Estava certo: sessão HS256 (typ/iss/aud, algoritmo fixo, sem tolerância, 7 dias, `sub`=`_id`), identidade RS256 (`apiGateway/auth/internal.js`, verificadores `*/internalIdentity.js` idênticos), `checkToken` antes do corpo, D7, `getCallerId` só da identidade, ACL-C1, registo sem premium, `type` só pela subscrição, limpeza de conta pelo par users→projects, `img_storage` só para o CN `projects`, frontend sem "eliminar" para não-donos. **Corrigido:** (1) a `users` recusava todos os presets do próprio dono (sujeito lido do segmento errado de `/users/:user/presets`); (2) o frontend não enviava o JWT nas subscrições (F05 partia com 401) — interceptor em `frontend/lib/axios.ts`; (3) o `ws_gateway` verificava a sessão sem fixar alg/iss/aud/typ; (4) o gateway transformava as recusas 4xx de users/subscriptions em 500; (5) as operações de tipo/quota/reembolso da `users` aceitavam a identidade do gateway (agora só o peer `projects`); (6) o contexto `share` assinado vinha do pedido do browser e não do pedido reencaminhado (um editor numa rota só do dono recebia 401 em vez de 403); (7) a matriz tinha as ligações de código desatualizadas e a presença marcada como read/edit (o código exige edit; R079/R080 são inalcançáveis). **Acrescentado:** `limits.fileSize` 25 MiB nas imagens (D-21, 413); testes `b4_common.py`, `b4-identity.py` (S06/S07/D7), `b4-routes.py` (todas as linhas B4-Rnnn, S13/S14/S15/F05/presets); `b4-route-matrix.py` verifica verbo e caminho e tem `--fix`; README dos testes.
- Verificado: a `picturas-nfr-exp` foi parada com `docker compose down` **sem** `-v` (o `med.py stack down` usa `-v`) e a sonda do `med.py` parada; `picturas-dev` com `--build --renew-anon-volumes`. `ops/pki.sh check` passou. Resultados em `tests/conformance/results/2026-11-23/B4-dev.txt`: matriz 112/112; identidade 92/92; rotas 552/552; `b4-functional.py`; smoke 12/12; F02 imagem+vídeo. F01 Node 8/8 e vídeo 74/74 (`F01-172145.txt`). Varrimento dos resultados e de 6436 linhas de logs da dev: zero valores de segredos e zero JWT.
- Parei em: `med.py stack up` da `picturas-nfr-exp`, antes de `EXP --quick` S01/S02/S05.
- Próximo passo: o da §1.
- Cuidado: (1) **Defeito anterior ao B4, não corrigido:** `users/routes/users.js` `PUT /:user/process/:n` faz `user.operations.remove(op)` sobre o objeto de `User.getOne` (`toJSON()`), o que lança e devolve 701 em qualquer segunda operação do mesmo dia; a linha é igual em `0523102`. A quota diária de contas free não é registada a partir da 2.ª aplicação do dia. É uma lacuna funcional fora do B4; decidir onde se corrige. (2) Com bind mount e `node_modules` em volume anónimo, a `subscriptions` precisa de `--renew-anon-volumes` para ver o `jsonwebtoken`. (3) As chamadas diretas dos testes usam as portas publicadas; depois do B3 têm de correr a partir de um contentor na rede da stack. (4) O `.env.med` já tem `MED_SVC_SCHEME_IMG_STORAGE=https` (o `img_storage` passou a HTTPS com mTLS). (5) O ponto 7 do B4 (relógios): o B4 não introduz prazos locais; a sessão e a identidade são verificadas sem tolerância; os prazos WS ficam no B8.
- Decisões novas: 24 (D-21).
- Dúvidas novas: D-21 (resolvida).

### 2026-11-23 19:00 — B4 — FEITO
- Feito: a primeira `EXP --quick` (`EXP-20261123T172424Z`) deu S02 0/20 e S05 100%, mas S01 INCONCLUSIVO num caso: G06 (registo público com `type: premium`) recusado com **400**, que o `med.py` congelado não conta como recusa (só 401/403/404/410 ou 2xx sem efeito). A `users` passa a responder **403** (`users/routes/users.js`, POST `/`), o código das restantes recusas de política; testes atualizados (`b4-routes.py`, `b4-functional.py`). O `med.py` não foi alterado.
- Verificado: `med.py run --campaign EXP --quick --metrics S01,S02,S05` na `picturas-nfr-exp` → S01 0/15 (pública, todos `RECUSADO_DOMINIO`), S02 0/20 (rede 10 + host 10, `RECUSADO_TLS`), S05 100% (`evaluation/results/EXP-20261123T184517Z/report.md`); varrimento do resultado: zero valores de segredos e zero JWT. Conformidade repetida na EXP com o código final (`tests/conformance/results/2026-11-23/B4-exp.txt`): matriz 112/112, identidade 92/92, rotas 552/552. Critérios do B4: S01 = 0 e S02 = 0 (rede e host) ✓; F05 subscribe → premium → cancel → free ✓ (`b4-routes.py`); S05 100% ✓; S06, S07, S13, S14, S15 e D7 (ausente, igual, contraditório, multivalor, vazio) ✓.
- Parei em: bloco concluído. A `picturas-nfr-exp` ficou ativa; a `picturas-dev` desmontada, com volumes.
- Próximo passo: o da §1.
- Cuidado: o `B4-dev.txt` foi registado antes da troca 400 → 403 da G06 (esperava 400); o `B4-exp.txt` é o resultado com o código final. O defeito da quota (701) continua por decidir, tal como na entrada anterior.
- Decisões novas: nenhuma (o 403 aplica o "não aceita" do plano, B4 ponto 5).
- Dúvidas novas: nenhuma.

### 2026-11-23 19:35 — B3 — FEITO (parado para o commit antes do B5)
- Feito: **quota** — `users/routes/users.js` filtra o registo do dia em vez de `operations.remove()` (decisão 25); `tests/conformance/users-quota.py`. **B3** — inventário: 12 portas internas publicadas (S3 9000, `img_storage` 11000, AMQPS 5671, gestão 15671, Mongo 27017/27018/27019, `projects` 9002, `users` 10001, `subscriptions` 11001, `generative-mock` 7860, `ws_gateway` 4000) e healthchecks só no RabbitMQ, nos 3 Mongo e no `generative-mock`. `docker-compose.yaml`: retiradas as 12 portas (fica o nginx 8080); os 6 serviços Node com `command: node …`, `init`, `restart`, `healthcheck` partilhado (âncoras `x-node-health-*`) e `mem_limit`; dependências `service_healthy` (decisão 26). `docker-compose.dev.yaml` novo (nodemon + bind mounts). Testes: `in-network.sh` + `runner.Dockerfile` (testes na rede da stack), `b4_common.py`/`b4-functional.py` com `B4_DIRECT=network`, `diagnostics/f08-restart.py`. Matriz de rotas com os números de linha atualizados (`--fix`). `README.md`, `AGENTS.md` e README dos testes atualizados.
- Verificado: a `picturas-nfr-exp` foi parada com `docker compose down` **sem** `-v` e a sonda parada. Na `picturas-dev` (`B3-dev.txt`): só `8080` publicado, as 12 portas antigas fechadas no host; os 6 serviços `healthy` com `node` sob `docker-init`; healthcheck com controlos negativos (porta errada, nome TLS errado, plaintext → falha); quota 10/10 (duas operações seguidas → 204/204; 5 no total; a 6.ª recusada por `PUT` 799 e por `GET` 701; restantes = 0); matriz 112/112, identidade 92/92, rotas 552/552, B4 funcional (todos na rede, `in-network.sh`); smoke 12/12; F02 imagem+vídeo; F08 6/6 dentro de 30 s e do alvo de 10 s (servido de novo em 0,4–0,7 s; `img_storage` *healthy* em 2,5 s); override dev com nodemon testado e reposto; F01 Node e vídeo 74/74. `med.py stack up` + `run --campaign EXP --quick --metrics S18,S05`: S18 `todas=0, loopback=0` CUMPRE_ALVO, S05 100% (`EXP-20261123T193037Z`). Varrimento: 41 valores de segredos e padrões JWT/assinaturas, zero ocorrências nos resultados.
- Parei em: bloco concluído; parado a pedido para o commit do B3 antes do B5.
- Próximo passo: o da §1.
- Cuidado: (1) O Docker Compose não reinicia um contentor *unhealthy*: o reinício automático cobre o processo que morre (OOM, crash), não um processo vivo mas bloqueado; o healthcheck serve para as dependências e para a visibilidade. Limitação a declarar na F08. (2) O `comm` do processo principal do Node 26 é `MainThread`, não `node` (o `med.py` já trata os dois). (3) Os testes `data-channels/b2-*.py` que usavam as portas 9000/5671/27017–27019 do host já não correm assim; a evidência do B2 fica a dos resultados de 22–23/11 e a S16/S17 do `med.py` corre pela rede. (4) No B5 o `api_gateway` e o `ws_gateway` passam a HTTPS: mudar `http` → `https` nos seus healthchecks e montar a PKI do `ws_gateway`.
- Decisões novas: 25, 26.
- Dúvidas novas: nenhuma.

### 2026-11-23 20:00 — B5 — FEITO
- Feito: a `picturas-nfr-exp` foi parada com `docker compose down` **sem** `-v` e a sonda parada. `*/tls/pkiTls.js` (7 cópias idênticas). Servidores: `users`, `subscriptions`, `projects`, `img_storage` usam `serverOptions()` + `guardValidity()` (a lista por par/operação continua no `internalIdentity.js` do B4 e no `img_storage` só `projects`); `api_gateway` e `ws_gateway` passam de HTTP a HTTPS só para o `nginx`; o frontend corre `frontend/server-https.js` (Next com o build normal) só para o `nginx`; o `generative-mock` corre `server_tls.py` (TLS 1.3 sem tickets, só `expand_ai_tool`). Clientes: todos os `https.Agent` com `maxCachedSessions: 0` (`clientAgent()` nos clientes internos); `expand_ai` com `cert=`/`verify=`; retirado o `rejectUnauthorized: false` do Socket.IO do frontend. nginx: `proxy_pass https://` com `proxy_ssl_verify`, `proxy_ssl_name`, certificado de cliente e `proxy_ssl_session_reuse off`. Compose: PKI própria montada no `ws_gateway`, `frontend`, `generative-mock` e `expand_ai_tool`; `GEN_EXPAND_URL` em HTTPS; healthchecks do `api_gateway`, `ws_gateway`, `frontend` e `generative-mock` em HTTPS com certificado de cliente; `restart` no `frontend` e no `generative-mock`; o nginx espera o frontend *healthy*. `ops/pki.sh`: EKU `clientAuth` no `frontend` e no `generative-mock`, reemitidos nesta instalação (decisão 27). Testes novos em `tests/conformance/mtls-pki/` (`b5-mtls.py`, `b5-guard.sh`, `b5-functional.py`); runner com `python-socketio`. `README.md` e `AGENTS.md` atualizados.
- Verificado (dev, `B5-dev.txt`): **S08** — em cada um dos 8 servidores, sem certificado, CA errada, certificado expirado da CA da instalação e certificado só de servidor (EKU) recusados no TLS; plaintext sem resposta HTTP. **Matriz D4** — cada um dos 11 certificados de serviço só é aceite pelos servidores que o listam (os outros dão 403). **S09** — o par permitido recebe resposta de domínio em todos os servidores; regressão B4 completa (matriz, identidade, rotas, funcional), quota, smoke 12/12, F02, wss pelo nginx com eventos de processamento, `expand_ai` generativo (outpainting por mTLS, PNG 64×40), eliminação de conta com limpeza dos projetos, F08 6/6 e F01. **Retoma** — nenhum servidor retoma a sessão; o controlo positivo (entrada pública do nginx) retoma, o que prova o detetor. **Guarda** — Node e Python: certificado expirado ou ainda não válido → não arranca; válido → continua; certificado de 12 s → termina na expiração (±3 s). **Identidade do servidor nos clientes** — o agente da `projects` recusa o servidor `users` com outro nome (`ERR_TLS_CERT_ALTNAME_INVALID`); o `requests` do `expand_ai` recusa o `generative-mock` pelo IP. **Estático** — nenhum `rejectUnauthorized: false`/`verify=False`/`CERT_NONE` no código do produto; todos os `https.Agent` sem sessões em cache; nginx sem upstream em plaintext. Logs da dev (3803 linhas): zero JWT, zero URLs assinados, zero de 41 valores de segredos. **EXP `--quick`** (`EXP-20261123T195259Z`): S03 0/8 (`RECUSADO_TLS` na rede, `RECUSADO_REDE` no host; controlo do dono OK), S21 mediana 10,48 ms (`get_project`) e 6,41 ms (`get_user`), +4,4 e +3,0 ms sobre a BF, 0 erros (mínimo +10 ms, alvo +5 ms; a classificação final é no `compare` da MF), S05 15/15, S01 0/15, S02 0/20, S16 0/24, S17 0/15, S18 0. Varrimento do resultado: zero segredos e zero JWT.
- Parei em: bloco concluído. A `picturas-nfr-exp` ficou ativa; a `picturas-dev` desmontada, com volumes.
- Próximo passo: o da §1.
- Cuidado: (1) **Instalações existentes:** `ops/pki.sh issue frontend` e `ops/pki.sh issue generative-mock` depois do pull (EKU novo); o `ops/pki.sh check` não deteta o EKU antigo. (2) O `ws_gateway` → `projects` (rota interna de autorização WS) ainda não existe: entra no B8, e a `projects` tem de acrescentar o par `ws_gateway` à lista nessa altura. (3) Sem keep-alive entre saltos, cada pedido faz um handshake completo por salto (sem retoma, por desenho); se a S21 da MF ficar acima do alvo, o keep-alive no upstream do nginx (com `keepalive_timeout` abaixo dos 5 s do Node) é a primeira medida. (4) A matriz PKI-C5 completa (rotação, retirada, isolamento) continua no B10.
- Decisões novas: 27.
- Dúvidas novas: nenhuma.

## 5. Dúvidas surgidas durante a implementação

As dúvidas D-01 a D-15 estão no [plano, §8](refactor-plano.md#8-dúvidas-para-resolver-em-conjunto).
As que surgirem a implementar ficam aqui, a partir de D-16 (a próxima é a D-22). Uma dúvida por resolver que
impeça avançar põe o bloco em `BLOQUEADO`. Quando for resolvida, a resposta passa
para a §2.6 (e para o plano, se mudar um bloco).

| # | Data | Bloco | Dúvida | Estado | Decisão |
|---|------|-------|--------|--------|---------|
| D-16 | 21/11 | B6 (D-14) | **Escrita do adaptador: copiar staging → candidato ou escrever direto no candidato?** O D-14 manda decidir pelo SP-03, "se o CopyObject de 500 MiB couber na U09". Resultado (SP-03, configuração da MF): 330–613 ms em 10 de 12 cópias (cabe no mínimo <3000 ms, mas gasta até 61% do alvo <1000 ms); **6206 e 6333 ms** em 2 de 12, quando o SeaweedFS cria volumes novos (aí a U09 falha); a cópia junta **+78 a +120 MiB** ao pico de memória do SeaweedFS na janela da U04. **A:** cópia (UP-C6 à letra), aceitando estes valores. **B:** escrita direta numa chave de candidato nova e única, que o cliente nunca pode escrever (a alternativa já prevista no D-14). **Recomendo B:** tira 0,3–6 s da U09 e cerca de 100 MiB da U04. Pergunta ligada: **pré-criar volumes do SeaweedFS no arranque** (por exemplo `volume.grow`) para evitar a pausa de cerca de 6 s, que também atinge o PUT direto? Recomendo que sim, medido no B6 | Resolvida (22/11) | Escrita direta numa chave de candidato nova e única (B) + volumes do SeaweedFS pré-criados no arranque, medido no B6 (§2.6, decisão 17) |
| D-17 | 21/11 | B6 (UP-C8) | **Como impor o limite de leitura do `ffprobe` (UP-C8: até 2×F+16 MiB)?** O SP-05 mostra que o `ffprobe` lê só 0,4–0,7 MB num ficheiro de 500 MiB, mas não tem nenhuma opção de bytes totais: só o tempo fica imposto (`rw_timeout`, `timeout`). **A:** relé de contagem dentro da `projects`, só em loopback: o `ffprobe` lê de `127.0.0.1`, e a `projects` reencaminha para o SeaweedFS por HTTPS validado e corta ao atingir o limite. Não é um salto de rede, por isso não viola a regra 7. **B:** sem limite de bytes imposto, só os tempos (15 s no total, `rw_timeout`), e declarar a lacuna com as leituras medidas. **C:** protocolo `subfile` do ffmpeg para restringir as leituras a `[0, F)`: limita cada leitura ao objeto, mas não o total. **Recomendo A** | Resolvida (22/11) | Relé de contagem em loopback dentro da `projects` (A) (§2.6, decisão 18) |
| D-18 | 21/11 | B2 (opção A) | **Como limitar a publicação de cada principal às suas filas?** O critério operacional exige "publicar … apenas nas filas/exchange do principal". O SP-07 mostra que, com o exchange `picturas` do tipo `direct`, a permissão `write` vale para o exchange inteiro: um worker publica em `video_queue` e `ws_queue`. **A:** passar o `picturas` a `topic`, com as mesmas routing keys (sem curingas, o comportamento é igual ao `direct`), e `set_topic_permissions` por principal (provado: o destino não autorizado dá 403). Os clientes passam a declarações passivas. O watermark só muda por variável de ambiente (SP-08). **B:** manter o `direct` e declarar a lacuna. **Recomendo A** | Resolvida (22/11) | Exchange `picturas` passa a `topic` com permissões por routing key (A) (§2.6, decisão 19) |
| D-19 | 21/11 | B2 (PKI-C5, D4) | **Como proteger os componentes internos do SeaweedFS?** O SP-11 mostra que o HTTPS do master, do volume e do filer exige certificado de cliente mas aceita **qualquer certificado da CA da instalação**: o `[https.*]` não tem lista de CN. Com o certificado do `img_storage`, a API do filer dá acesso a todos os ficheiros por fora das identidades S3. Isto contradiz o D4 ("CA válida não basta"). **A:** ligar o master, o volume e o filer só a loopback (`-ip=localhost -ip.bind=127.0.0.1 -s3.ip.bind=0.0.0.0`; estão no mesmo processo `weed server`), mantendo o TLS/mTLS internos como defesa em profundidade. Da rede ficam só a 9000 (S3) e a 19000 (gRPC do S3, mTLS com CN=seaweedfs); o S3 funciona por inteiro (provado). **B:** CA própria para os componentes do SeaweedFS (afasta-se da CA única do PKI-C1). **C:** manter na rede e declarar a lacuna. **Recomendo A** | Resolvida (22/11) | Master, volume e filer só em loopback (A); TLS/mTLS internos mantidos (§2.6, decisão 20) |
| D-20 | 22/11 | B2 (S3) | **Como criar o bucket `picturas` antes de o `img_storage` arrancar com uma credencial sem `CreateBucket`?** O código atual cria-o no primeiro pedido, o que falhará com `Read/Write/List/Tagging:picturas`. **A:** job Compose de arranque único com credencial admin montada só nele; cria o bucket por HTTPS validado e termina; `img_storage` espera pela sua conclusão. **B:** comando explícito em `ops/` após iniciar o SeaweedFS, antes de subir o resto; menos automatismo no arranque. **Recomendo A**, com credencial admin isolada e sem logs de segredos. | Resolvida (23/11) | A: job idempotente, `service_completed_successfully`, admin só no job e sem logs, só cria bucket (§2.6, decisão 23) |
| D-21 | 23/11 | B4 (ideia 8) | **Que valor para o `limits.fileSize` das imagens no gateway?** O plano pede o limite mas não o fixa; não existia nenhum limite de imagem (frontend nem `projects`); as imagens do `med.py` são PNG pequenos. **A:** 25 MiB. **B:** 50 MiB. **C:** 10 MiB. **Recomendei A**, configurável por `IMAGE_MAX_BYTES`, com 413 | Resolvida (23/11) | A: 25 MiB, `IMAGE_MAX_BYTES`, 413 (§2.6, decisão 24) |

## 6. Como retomar

1. `git switch fase2-refactor && git pull`. Na primeira vez, o branch ainda não existe:
   cria-o com `git switch -c fase2-refactor` a partir do `main` atualizado.
2. Lê a §1 (ponto atual), a §2 (contexto) e a última entrada da §4. No
   [plano](refactor-plano.md), lê o bloco indicado e as regras (§1), e só os documentos
   de origem desse bloco.
3. Prepara o ambiente (§7) e confirma que a stack arranca **antes** de mexer no código.
4. Faz o **próximo passo exato** da §1. Ao parar, atualiza a §1 e a §3, acrescenta a
   entrada na §4 e regista as decisões novas na §2.6.
5. Pedido inicial para um agente (Claude Code ou outro):

   > Lê `docs/refactor-handoff.md` (sobretudo §1 e §2) e `docs/refactor-plano.md`.
   > Retoma a partir do "Próximo passo exato". Trata as decisões da §2 como fechadas:
   > não as reabras sem perguntar. Respeita as regras do plano (§1). Não faças commits.
   > Antes de parar, atualiza a §1 e a §3, acrescenta uma entrada à §4 e regista na §2.6
   > as decisões novas.

### 6.1 Passar o trabalho a outra pessoa (por exemplo, quando acabam os tokens)

**Quem para:**

1. Se a sessão ainda responde, pedir ao agente: *"Vamos parar. Atualiza o handoff
   (§1, §3, entrada na §4 e decisões na §2.6) com o estado exato, incluindo o que
   ficou a meio."*
2. Se a sessão acabou de repente, sem atualizar o handoff: escrever à mão na §1 pelo
   menos o bloco, o que se estava a fazer e que o estado ficou **por confirmar**.
3. Guardar tudo e publicar, mesmo que fique a meio:
   ```bash
   git add -A && git status        # confirmar que não entra nenhum segredo nem .env
   git commit -m "[Bx] WIP: <o que ficou a meio>"
   git push
   ```

**Quem retoma (noutro computador):**

1. A primeira vez:
   ```bash
   git clone https://github.com/A104358/picturas-27.git && cd picturas-27
   git switch fase2-refactor
   cd evaluation && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
   cp .env.med.example .env.med    # pôr MED_COMPOSE_PROJECT=picturas-nfr-exp
   .venv/bin/python med.py corpus  # vídeos de teste (vários GB, fora do Git)
   cd ..
   ```
   Depois do B1: gerar os segredos e certificados da sua própria instalação (§7,
   "Segredos"). As chaves nunca se copiam de outro computador.
2. Sempre:
   ```bash
   git switch fase2-refactor && git pull
   ```
3. Abrir uma sessão nova do agente com o pedido do ponto 5 acima. Se a última entrada
   do diário disser "por confirmar" ou o commit for `WIP`, acrescentar ao pedido:
   *"A sessão anterior parou de repente. Antes de continuar, compara o handoff com o
   `git log` e o `git diff` do último commit, corrige a §1 e só depois avança."*

### 6.2 Dois blocos em paralelo em máquinas diferentes (B6 e B8, §2.6 decisão 30)

- **Branch:** as duas máquinas trabalham no `fase2-refactor`. Cada bloco só vai para commit
  depois de verificado (dev + `EXP`) na sua máquina. Antes de cada push:
  `git pull --rebase origin fase2-refactor`. Se houver conflito, quem o resolve repete a
  conformidade (B4/B5 e a do seu bloco) antes do push. Nunca `push --force`.
- **Zonas exclusivas:**
  - **B6:** upload (rotas de upload, adaptador, staging, `ffprobe`, `imageStorageService`
    de upload, `location` de upload no nginx).
  - **B8:** `wsGateway/`, cliente Socket.IO do frontend e `evaluation/med.py` (só o
    `MED_WS_JOIN_FORMAT`, com `freeze` e nota em `evaluation/IMPLEMENTATION_NOTES.md`).
    O B6 não mexe no `med.py`.
- **Ficheiros partilhados, com toque mínimo:**
  - `projects/routes/projects.js`: o B8 não lhe mexe; a rota interna de autorização do
    WebSocket fica num ficheiro novo (p. ex. `projects/routes/wsAuth.js`), montado com uma
    linha em `projects/app.js`.
  - Lista de pares mTLS da `projects`: o B8 só acrescenta o par `ws_gateway`.
  - `docker-compose.yaml` e `nginx/nginx.conf`: cada bloco só altera os blocos dos seus
    serviços e `location`s. Não se reformata nem se reordena nada.
- **Handoff:**
  - o §1 é do B6;
  - o B8 escreve só na sua linha do §3 e numa entrada própria do §4, com título "B8";
  - dúvidas novas: o B6 usa D-22, D-24, …; o B8 usa D-23, D-25, …;
  - decisões novas na §2.6: o B6 usa 31, 33, …; o B8 usa 32, 34, …
- **Métricas comparativas noutra máquina:** a S21 e as métricas U comparam com a BF, que foi
  medida noutra máquina. Na máquina do B8, mede-se uma `EXP` S21 antes de mudar código e
  outra no fim, e regista-se o delta entre as duas. O valor oficial sai da verificação
  conjunta (B12), na máquina da BF.
- **Preparar a máquina nova (uma vez):**

  ```bash
  git clone <origin> && cd <repo> && git switch fase2-refactor
  export PICTURAS_SECRETS_DIR=<dir fora do repo>
  ops/secrets.sh init && ops/pki.sh init && ops/pki.sh check
  cd evaluation && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
  cp .env.med.example .env.med   # MED_COMPOSE_PROJECT=picturas-nfr-exp
  ../ops/secrets.sh med-env >> .env.med
  ```

## 7. Ambiente

| Item | Valor / comando |
|------|-----------------|
| Branch | Só `fase2-refactor`, criado a partir de `main` depois da BF e publicado no `origin` (`A104358/picturas-27`). Noutro computador: `git fetch origin && git switch fase2-refactor`. O `main` só recebe o trabalho depois da MF. **Nunca abrir um PR para o repositório upstream (`picturas-um/picturas-27`)** (§2.6, decisão 12) |
| Stack de desenvolvimento | Projeto Compose `picturas-dev` (ou outro nome); o `med.py` não corre aqui |
| Stack de verificação (`med.py` EXP) | `MED_COMPOSE_PROJECT=picturas-nfr-exp` no `evaluation/.env.med` (o `med.py` só aceita `picturas-nfr[-sufixo]`) |
| Stack da MF oficial | `picturas-nfr`, só para a MF, no Mac da BF |
| Uma stack do `med.py` de cada vez | O `med.py` usa um único marcador (`evaluation/.run/stack.json`) e a porta 28080. **Antes de trocar de projeto no mesmo computador, faz `med.py stack down` no anterior**; senão, a ferramenta deixa de reconhecer o outro projeto como seu e recusa montá-lo |
| Computador novo (só `EXP`) | `cd evaluation && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`; copiar `.env.med.example` para `.env.med` e pôr `MED_COMPOSE_PROJECT=picturas-nfr-exp`; `med.py corpus` (gera os vídeos de teste, vários GB, fora do Git). Se o disco ou a memória do Docker ficarem abaixo do `preflight`, usar `--force`, que só é aceite em `EXP` |
| Segredos | `PICTURAS_SECRETS_DIR=<diretório fora do repositório>`; gerar com `ops/secrets.sh init` e `ops/pki.sh init` (depois do B1). Cada computador tem a sua CA (PKI-C1 A): as chaves nunca se copiam entre computadores |
| Verificação rápida | `cd evaluation && .venv/bin/python med.py stack up && .venv/bin/python med.py run --campaign EXP --quick --metrics <métricas do bloco>,S05` (com `picturas-nfr-exp`). O `stack up` apaga e reconstrói a stack de verificação inteira, o que pode levar 15–30 min. **Depois do B1**, antes do `stack up`: `export PICTURAS_SECRETS_DIR=…` e gerar os segredos e certificados dessa stack (`ops/secrets.sh init`, `ops/pki.sh`); sem isso o `docker compose config` do `med.py` falha. O `evaluation/.env.med` da stack de verificação vai recebendo as mesmas variáveis da MF à medida que os blocos ficam feitos (plano §6, ponto 1) |
| Regressão existente | `cd Tools/video && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/python -m pytest -q tests` (precisa de `ffmpeg`), e os testes Node de cada serviço |
| Conformidade | `tests/conformance/`, com resultados em `tests/conformance/results/` (ver plano §5) |
| Ferramenta de medição | **Congelada** (versão `638516104ae9`). Não alterar `evaluation/med.py`, `medlib/`, `criteria.yaml` nem `cases/`, exceto o previsto no plano §6 |
| BF e MF oficiais | Só no Mac onde foi feita a BF, com `--campaign BF/MF`. Noutros computadores usar sempre `EXP` |

## 8. Armadilhas conhecidas

- **Depois de reconstruir o frontend, reinicia o nginx** (`docker compose restart nginx`);
  senão dá 502.
- **Com `nodemon` (só no `docker-compose.dev.yaml`, desde o B3), depois de um OOM o
  contentor fica "Up" mas a app está morta.** Reinicia o serviço. A configuração entregue
  corre `node` e reinicia sozinha.
- **Desde o B3 só o nginx tem porta no host.** Os testes com chamadas diretas aos serviços
  correm com `tests/conformance/in-network.sh <projeto> <teste.py>`.
- **O nginx fica com o IP antigo do upstream** depois de reiniciar um serviço Node.
  Reinicia também o nginx.
- **`GET /:user/:project` ocupa um lugar de editor**, e um dono free só tem 2 lugares
  (dá 429). Usa um dono premium nos testes.
- **O SeaweedFS retém memória entre uploads.** Para medir a U04 tem de ser reiniciado
  antes (o `med.py` já o faz).
- **`picturas-nfr` é só para a MF oficial.** As verificações usam `picturas-nfr-exp`, e
  o desenvolvimento usa outro projeto Compose.
- **Não ter duas stacks do `med.py` ao mesmo tempo** (`picturas-nfr` e
  `picturas-nfr-exp`): partilham a porta 28080 e o marcador. Fazer `stack down` antes de
  trocar.

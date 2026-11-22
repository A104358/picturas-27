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
| Bloco em curso | B0 concluído; nenhum bloco começado depois dele |
| Passo do bloco | — |
| Estado deixado | B0 feito no branch `fase2-refactor` (ainda sem commit): SP-01 a SP-11 registados em [`refactor-spikes.md`](refactor-spikes.md), imagens fixadas às da BF, `tests/conformance/` criado, F01 registado. Abertas as dúvidas **D-16 a D-19** (§5), que bloqueiam pontos do B2 e do B6 |
| **Próximo passo exato** | 1) Uma pessoa revê e faz commit do B0 no `fase2-refactor` (ficheiros na entrada da §4). 2) Começar o **B1** (PKI e segredos); o B3 pode avançar em paralelo. As dúvidas D-16 a D-19 estão resolvidas (§2.6, decisões 17 a 20) e o plano foi atualizado (B1, B2, B6) |
| Coisas meio feitas | Nenhuma. As notas dos spikes para cada bloco estão em `refactor-spikes.md` (secções "Notas para o Bx") |
| Testes a falhar neste momento | Nenhum no ambiente do produto (F01: 8/8 Node, 74/74 vídeo nas imagens). No host, o `Tools/video` dá 68/74 porque o ffmpeg do Homebrew não tem `libass` (ambiente, não código) |
| Último commit com o trabalho | — (B0 por commitar) |
| Atualizado em | 2026-11-21 |

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

## 3. Estado dos blocos

Estados: `POR FAZER`, `EM CURSO`, `BLOQUEADO` (com motivo), `EM VERIFICAÇÃO`, `FEITO`.
`FEITO` quer dizer que o critério de aceitação do bloco passou e o resultado ficou
guardado.

A ordem do plano é a recomendada. Um bloco pode começar antes da sua vez se as
dependências estiverem `FEITO`.

| Bloco | Depende de | Estado | Verificação (link para o resultado) | Notas |
|-------|-----------|--------|-------------------------------------|-------|
| B0 — Spikes e preparação | — | FEITO | [`refactor-spikes.md`](refactor-spikes.md); bruto em `tests/spikes/SP-xx/results/`; F01 em `tests/conformance/results/2026-11-21/` | 11 spikes: 6 suportados, 5 suportados com limitações (D-16 a D-19) |
| B1 — PKI e segredos | B0 | POR FAZER | — | Pode começar. Retirar também `frontend/certs/selfsigned.key` do Git (SP-09) |
| B2 — Mongo/RabbitMQ/S3 | B1 | POR FAZER | — | Inclui as opções de TLS no `med.py` (§2.6, decisão 13). **O RabbitMQ espera pela D-18 e o SeaweedFS pela D-19.** Notas do SP-02, SP-06, SP-07, SP-08 e SP-11 |
| B3 — Portas e supervisão | — | POR FAZER | — | Retirar todas as portas internas; `node` + `healthcheck` (§2.6, decisões 4 e 5) |
| B4 — Identidade e autorização HTTP | B1 | POR FAZER | — | Precisa do par RS256 e do segredo HS256 novo; começa pela matriz de rotas (`docs/refactor-matriz-rotas.md`) |
| B5 — mTLS e TLS por salto | B1 | POR FAZER | — | `proxy_ssl_session_reuse off` (SP-09); servidor HTTPS próprio do Next (SP-09); Flask/`requests` com mTLS (SP-10) |
| B6 — Upload: motor e adaptador | B0, B4, B5 | POR FAZER | — | A escrita do adaptador (cópia ou direta) ficou na **D-16**, e o limite de leitura do `ffprobe` na **D-17**. Notas do SP-01, SP-03 e SP-05 |
| B7 — Upload: fluxo novo | B6 | POR FAZER | — | Inclui o frontend (§2.6, decisão 1). Configuração do `auth_request` (SP-01, notas 1–4) e do `Host` assinado (SP-04) |
| B8 — WebSocket | B4, B5 | POR FAZER | — | Inclui o formato do join no `med.py` (§2.6, decisão 3) |
| B9 — Sessões e recuperação | B4, B8 | POR FAZER | — | Sem migração (reset, §2.6, decisão 15); mantém a ferramenta de reemissão assistida |
| B10 — Operação da PKI | B1, B2, B5 | POR FAZER | — | O piloto corre assim que estiver pronto (§2.6, decisão 9) |
| B11 — Reconciliação (OPS-C1) | B2, B10 | POR FAZER | — | Usa o isolamento do B10 |
| §5 — Testes de conformidade | cresce com cada bloco | EM CURSO | `tests/conformance/results/2026-11-21/F01-202134.txt` | `tests/conformance/` criado (README + `run-f01.sh`); F01 registado |
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

## 5. Dúvidas surgidas durante a implementação

As dúvidas D-01 a D-15 estão no [plano, §8](refactor-plano.md#8-dúvidas-para-resolver-em-conjunto).
As que surgirem a implementar ficam aqui, a partir de D-16 (a próxima é a D-20). Uma dúvida por resolver que
impeça avançar põe o bloco em `BLOQUEADO`. Quando for resolvida, a resposta passa
para a §2.6 (e para o plano, se mudar um bloco).

| # | Data | Bloco | Dúvida | Estado | Decisão |
|---|------|-------|--------|--------|---------|
| D-16 | 21/11 | B6 (D-14) | **Escrita do adaptador: copiar staging → candidato ou escrever direto no candidato?** O D-14 manda decidir pelo SP-03, "se o CopyObject de 500 MiB couber na U09". Resultado (SP-03, configuração da MF): 330–613 ms em 10 de 12 cópias (cabe no mínimo <3000 ms, mas gasta até 61% do alvo <1000 ms); **6206 e 6333 ms** em 2 de 12, quando o SeaweedFS cria volumes novos (aí a U09 falha); a cópia junta **+78 a +120 MiB** ao pico de memória do SeaweedFS na janela da U04. **A:** cópia (UP-C6 à letra), aceitando estes valores. **B:** escrita direta numa chave de candidato nova e única, que o cliente nunca pode escrever (a alternativa já prevista no D-14). **Recomendo B:** tira 0,3–6 s da U09 e cerca de 100 MiB da U04. Pergunta ligada: **pré-criar volumes do SeaweedFS no arranque** (por exemplo `volume.grow`) para evitar a pausa de cerca de 6 s, que também atinge o PUT direto? Recomendo que sim, medido no B6 | Resolvida (22/11) | Escrita direta numa chave de candidato nova e única (B) + volumes do SeaweedFS pré-criados no arranque, medido no B6 (§2.6, decisão 17) |
| D-17 | 21/11 | B6 (UP-C8) | **Como impor o limite de leitura do `ffprobe` (UP-C8: até 2×F+16 MiB)?** O SP-05 mostra que o `ffprobe` lê só 0,4–0,7 MB num ficheiro de 500 MiB, mas não tem nenhuma opção de bytes totais: só o tempo fica imposto (`rw_timeout`, `timeout`). **A:** relé de contagem dentro da `projects`, só em loopback: o `ffprobe` lê de `127.0.0.1`, e a `projects` reencaminha para o SeaweedFS por HTTPS validado e corta ao atingir o limite. Não é um salto de rede, por isso não viola a regra 7. **B:** sem limite de bytes imposto, só os tempos (15 s no total, `rw_timeout`), e declarar a lacuna com as leituras medidas. **C:** protocolo `subfile` do ffmpeg para restringir as leituras a `[0, F)`: limita cada leitura ao objeto, mas não o total. **Recomendo A** | Resolvida (22/11) | Relé de contagem em loopback dentro da `projects` (A) (§2.6, decisão 18) |
| D-18 | 21/11 | B2 (opção A) | **Como limitar a publicação de cada principal às suas filas?** O critério operacional exige "publicar … apenas nas filas/exchange do principal". O SP-07 mostra que, com o exchange `picturas` do tipo `direct`, a permissão `write` vale para o exchange inteiro: um worker publica em `video_queue` e `ws_queue`. **A:** passar o `picturas` a `topic`, com as mesmas routing keys (sem curingas, o comportamento é igual ao `direct`), e `set_topic_permissions` por principal (provado: o destino não autorizado dá 403). Os clientes passam a declarações passivas. O watermark só muda por variável de ambiente (SP-08). **B:** manter o `direct` e declarar a lacuna. **Recomendo A** | Resolvida (22/11) | Exchange `picturas` passa a `topic` com permissões por routing key (A) (§2.6, decisão 19) |
| D-19 | 21/11 | B2 (PKI-C5, D4) | **Como proteger os componentes internos do SeaweedFS?** O SP-11 mostra que o HTTPS do master, do volume e do filer exige certificado de cliente mas aceita **qualquer certificado da CA da instalação**: o `[https.*]` não tem lista de CN. Com o certificado do `img_storage`, a API do filer dá acesso a todos os ficheiros por fora das identidades S3. Isto contradiz o D4 ("CA válida não basta"). **A:** ligar o master, o volume e o filer só a loopback (`-ip=localhost -ip.bind=127.0.0.1 -s3.ip.bind=0.0.0.0`; estão no mesmo processo `weed server`), mantendo o TLS/mTLS internos como defesa em profundidade. Da rede ficam só a 9000 (S3) e a 19000 (gRPC do S3, mTLS com CN=seaweedfs); o S3 funciona por inteiro (provado). **B:** CA própria para os componentes do SeaweedFS (afasta-se da CA única do PKI-C1). **C:** manter na rede e declarar a lacuna. **Recomendo A** | Resolvida (22/11) | Master, volume e filer só em loopback (A); TLS/mTLS internos mantidos (§2.6, decisão 20) |

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
- **Com `nodemon`, depois de um OOM o contentor fica "Up" mas a app está morta.**
  Reinicia o serviço (até o B3 estar feito).
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

# Fase 2 — Métricas selecionadas, mínimos e alvos

[Índice da documentação](README.md) · **Equipa: PL2-G4**

Este documento fixa o **subconjunto de métricas** com que a equipa avalia os dois
requisitos não funcionais (RNF) da Fase 2. Para cada métrica explica o que mede, por que
foi escolhida, qual é o valor mínimo aceitável e o valor-alvo, e de onde vêm esses
valores. O procedimento de recolha está no [plano de medição](planoMedicao.md).

| RNF | ISO/IEC 25010:2011 | Cenários (Ex. 6, Bloco 2) | Candidato |
|-----|--------------------|---------------------------|-----------|
| **1. Segurança — autorização ponta a ponta** | Segurança → Confidencialidade, Integridade, Autenticidade | QS-01 (admissão) + QS-07 (revogação, complementar) | CAND-1 / QC-06 |
| **2. Eficiência de desempenho — carregamento de ficheiros** | Eficiência de desempenho → Utilização de recursos e Capacidade; Comportamento temporal como guarda | QS-02 | CAND-2 / QC-05 |

## Estado e regras

- **Seleção de 20/11/2026.** Os IDs (S.., U..) são os do [catálogo de 60 métricas](fase2-metricas-e-baseline.md).
  O catálogo continua a ser a decomposição completa; este documento escolhe as que
  contam para a avaliação e diz porquê. As restantes ficam como diagnóstico (§4).
  A seleção ainda tem de ser confirmada pela equipa.
- **Os valores "base" indicados são exploratórios** (B16, 16/11, Apple M4/ARM64, estado
  reutilizado) ou estimativas. **Não são a baseline formal.** A baseline formal (BF) é
  a primeira execução do [plano de medição](planoMedicao.md) sobre a solução de base,
  antes de qualquer alteração ao código. A medição final (MF) repete-a com o mesmo
  método, no mesmo host.
- **Os mínimos e alvos são fixados antes da BF** e revistos uma única vez depois dela
  (calibração), com registo da alteração. **Nunca se ajustam para fazer passar a MF.**
- **Quem mede e onde (decisão de 20/11).** A BF e a MF oficiais são recolhidas por um
  único elemento da equipa, no mesmo computador, com o `med.py`. Medições feitas
  noutros computadores servem apenas para confirmar que o método dá valores da mesma
  ordem de grandeza; não se juntam à BF/MF.
- **Commit de partida:** `0523102` de `picturas-um/picturas-27` (04/11/2026). Até 20/11
  a equipa não alterou código da aplicação, só documentação.
- **Tipos de métrica.** As **principais** demonstram a melhoria do RNF; as **guardas**
  garantem que a melhoria não foi conseguida à custa de outra coisa (funcionalidade,
  tempo, outros utilizadores). Uma guarda que falhe invalida a melhoria.
- **Origem dos valores.** **R** = requisito escrito (documento PL1-G4); **D** = decisão
  da equipa já registada (EVAL-M1, S12/WS, opção A de segurança); **E** = valor de
  engenharia justificado neste documento; **P** = política (o único valor aceitável é 0).

### Critérios usados na seleção

1. Mede a **fragilidade diagnosticada** (o efeito para os stakeholders) e não apenas a
   existência de um mecanismo.
2. **Mostra a diferença** entre a base e o final. Métricas que não existem na base (NA)
   ou que já passam na base servem apenas de guarda.
3. Os valores têm **origem identificável**.
4. É **objetiva e repetível** com o plano de avaliação já selecionado (EVAL-B1/C1/R1/M1).
5. **Pode ser implementada e medida** no prazo da entrega.

## Resumo

| ID | Tipo | Métrica | Base (exploratória) | Mínimo | Alvo | Origem |
|----|------|---------|---------------------|--------|------|--------|
| S01 | Principal | Efeitos indevidos sobre recursos de outra conta, pela entrada pública | ≥5 confirmados (G03–G07) | 0 | 0 | P |
| S02 | Principal | Efeitos indevidos por chamada direta aos serviços internos com API (host e rede Docker) | D02/D03 → 200; D09 confirmado | 0 | 0 | P |
| S03 | Principal | Operações indevidas no storage/signer (originais e resultados) | D07/D08 → 201 | 0 | 0 | P |
| S04 | Principal | Eventos protegidos ou entradas em sala WS sem autorização | ≥1 (W01) | 0 | 0 | P |
| S12 | Principal | Tempo de corte da receção WS após revogação | sem corte (>30 s) | ≤5 s | ≤2 s | D |
| S16 | Principal | Acessos indevidos às bases de dados Mongo | D11: leitura sem credenciais | 0 | 0 | P / D |
| S17 | Principal | Acessos indevidos ao broker RabbitMQ e ao S3 | D10: credencial publicada funciona | 0 | 0 | P / D |
| S18 | Principal | Portas de serviços internos publicadas no host | 12 em 10 serviços, todas as interfaces | 0 fora do loopback | 0 publicadas | E / diretrizes |
| S05 | Guarda | Operações legítimas concluídas | 100% | 100% | 100% | P |
| S21 | Guarda | Sobrecarga de latência em pedidos leves (Δ da mediana) | 0 | ≤ +10 ms | ≤ +5 ms | E |
| U01 | Principal | Pico de memória adicional por serviço Node no upload | 1767 / 759 / 729 MiB (500 MiB) | ≤64 MiB | ≤32 MiB | D (EVAL-M1) |
| U20 | Principal | 3 uploads simultâneos de 500 MiB | não medido (previsão: falha) | 3/3 sem OOM | 3/3 em 3 rondas | D (EVAL-M1) |
| U19 | Principal | Recurso gasto antes de recusar um upload sem token | +500 MiB, 401 após 3,6 s | ≤8 MiB | ≤100 ms após cabeçalhos | E |
| U18 | Principal | Recusa correta de uploads inválidos | free 500 MiB → 502 + OOM | 100% | 100% | P / R |
| U04 | Principal | Memória do nginx e do SeaweedFS no upload | não medido | +≤128 / +≤256 MiB | +≤64 / +≤128 MiB | D (EVAL-M1) / E |
| U08 | Principal | Disco temporário por componente e resíduos | não medido | ≤C×(F+16 MiB); 0 resíduos | ≤16 MiB por upload, sem spool integral | E |
| U09 | Guarda | Aceitação após o fim do envio | mediana 6923 ms (500 MiB) | <3000 ms | <1000 ms | **R** |
| U25 | Guarda | Pedidos leves durante uploads | não medido | 0 falhas; ≤1,10× controlo | ≤ controlo | D (EVAL-M1) |
| U15 | Guarda | Integridade SHA-256 do original | não verificada em todos | 100% | 100% | P |
| U17 | Guarda | Uploads válidos aceites | 14/14 | 100% | 100% | P |
| U10 | Guarda | Tempo total do upload | mediana 10 525 ms (500 MiB) | ≤1,10× BF | ≤ BF | D (EVAL-M1) |

---

## 1. RNF 1 — Segurança: autorização ponta a ponta

**Fragilidade (diagnóstico).** A autorização existe só em parte do percurso. O gateway
aceita `?owner=<outro>` e passa a identidade ao `projects` num cabeçalho (`X-Caller-Id`)
em que os serviços internos confiam sem verificação. Vários serviços internos estão
publicados no host e aceitam pedidos diretos. O WebSocket deixa qualquer socket, mesmo
sem token, entrar na sala de qualquer projeto (`join-project`). As bases de dados, o
broker e o S3 usam credenciais por omissão escritas no `docker-compose.yaml`, ou nenhuma.
Os stakeholders afetados são os donos e os colaboradores dos projetos
(confidencialidade e integridade dos vídeos, pipelines e perfis) e o operador da
instalação.

**Regra comum às métricas S01–S04, S16 e S17.** Cada métrica é uma **matriz finita de
casos**, congelada antes da BF. Cada caso tem um ataque concreto e um **controlo
legítimo** correspondente. O resultado conta **efeitos indevidos verificados**,
confirmados pelo estado ou pelos bytes antes e depois, e não apenas pelo código HTTP:

- **Admitido**: o ataque produziu o efeito (leu dados, alterou estado, recebeu evento).
- **Recusado**: recusa explícita (401/403/404/410, TLS ou rede recusada) **e** nenhum
  efeito observado.
- **Inconclusivo**: 5xx, timeout ou serviço ausente. **Não conta como proteção** (QS-01).
  Uma campanha com casos inconclusivos não cumpre a métrica.

**Por que mínimo = alvo = 0.** Uma admissão indevida é uma fuga de dados ou uma
alteração não autorizada; não existe uma quantidade aceitável. O que distingue um bom
resultado de um mau é a **cobertura**: o relatório indica o número de casos por
fronteira (pública, host, rede Docker, WS, dados) e esse denominador é o mesmo na BF e
na MF.

### S01 — Acessos cruzados pela entrada pública (inclui S14)

- **Escala.** Nº de efeitos indevidos verificados / nº de tentativas, na entrada pública
  `https://<host>/api-gateway/`, sobre projeto, media, pipeline, partilhas, perfil e
  quota de **outra conta**. Tentativas com JWT de outro utilizador, sem token, com
  `?owner=` adulterado e com permissão de partilha insuficiente (leitor a editar).
- **Por que foi escolhida.** É o núcleo do RNF e a fragilidade com efeito confirmado:
  G03 (adicionar ferramenta ao pipeline da vítima), G04 (carregar media para o projeto
  da vítima), G05 (ler o perfil de outro sem token), G06/G07 (tornar-se premium sem
  pagar). Afeta imagem e vídeo.
- **Base.** ≥5 efeitos confirmados (G03, G04, G05, G06, G07). G02 e outros casos
  precisam de asserções corrigidas antes de contarem.
- **Mínimo / alvo:** 0 / 0 (P).
- **Cuidados.** G06 (registo público com `type=premium`) e G07 dizem respeito ao perfil
  e não a um projeto, mas pertencem ao QS-01 (rotas de `users`). A regra D7 (`owner`
  ausente ou igual ao dono) define o que é legítimo.

### S02 — Chamadas diretas aos serviços internos (bypass do gateway)

- **Escala.** Nº de efeitos indevidos / nº de tentativas sobre os serviços internos com
  API (`projects`, `users`, `subscriptions`), medido em **duas superfícies separadas**:
  (a) host, através das portas publicadas; (b) rede Docker, a partir de um contentor de
  sonda ligado à rede da aplicação. Tentativas sem identidade, com `X-Caller-Id`
  forjado, com JWT de outro utilizador, com JWT assinado com outra chave e com JWT não
  assinado.
- **Por que foi escolhida.** Mostra que proteger só o gateway não basta, que é a
  essência do "ponta a ponta". Medir também na rede Docker impede que o problema
  pareça resolvido apenas por se fecharem portas (S18): um serviço comprometido dentro
  da rede continuaria a ter acesso total.
- **Base.** D02/D03 → 200 com o projeto da vítima (efeito a confirmar com asserção de
  conteúdo na BF). D09: `PUT` direto ao `users` sem token mudou o perfil da vítima para
  premium (efeito confirmado). Na rede Docker: não medido, mas o código não verifica
  nada.
- **Mínimo / alvo:** 0 / 0 (P), nas duas superfícies.

### S03 — Storage e emissão de URLs assinadas

- **Escala.** Nº de leituras, escritas, cópias ou eliminações indevidas no
  `imageStorageService` e de URLs assinadas emitidas sem identidade autorizada. O
  efeito verifica-se com HEAD/SHA-256 do objeto antes e depois.
- **Por que foi escolhida.** Os originais e os resultados (vídeos) são o ativo mais
  valioso do utilizador. Hoje o serviço de storage não tem autenticação.
- **Base.** D07 (escrita sem token → 201) e D08 (eliminação sem token → 2xx); D06
  (pedir URL assinado do original) tem de ser repetido com o campo certo (`og_img_key`
  obtido do estado do projeto).
- **Mínimo / alvo:** 0 / 0 (P).

### S04 — Admissão no WebSocket (inclui S10)

- **Escala.** Nº de eventos protegidos (`project-op`, `project-updated`, `process-update`,
  `video-progress`, `preview-ready`) recebidos por um socket sem JWT válido ou sem
  permissão no projeto; nº de entradas em sala concedidas nessas condições. Inclui a
  variante "o `projects` está indisponível" (não pode conceder entradas novas).
- **Por que foi escolhida.** Fuga confirmada (W01: um socket sem token recebeu o
  pipeline de outro utilizador). Os eventos de progresso também revelam atividade e
  nomes de ficheiros.
- **Base.** ≥1 (W01). Na base, `join-project` aceita qualquer `projectId` sem verificar.
- **Mínimo / alvo:** 0 / 0 (P).

### S12 — Tempo de corte após revogação (QS-07)

- **Escala.** Milissegundos entre o ACK observado da revogação (resposta 2xx ao
  `DELETE .../share/:shareId`) e o corte verificado da receção desse membro na sala do
  projeto, com a incerteza da medição. Complementos: nº de eventos protegidos entregues
  depois do limite e nº de controlos legítimos preservados (o dono e outro membro
  continuam a receber).
- **Por que foi escolhida.** É o cenário QS-07 acrescentado na revisão de 20/11:
  retirar uma partilha tem de retirar a receção que dela depende. É a única métrica
  temporal de segurança e a de maior exigência técnica (revalidação periódica, falhas,
  corridas), o que pesa na classificação.
- **Base.** Na base o socket nunca é cortado, porque a sala não depende da partilha.
  Regista-se como **"sem corte durante a janela de 30 s"** (valor censurado: >30 000 ms)
  e conta-se o número de eventos recebidos depois da revogação.
- **Mínimo / alvo:** ≤5 s / ≤2 s, e 0 eventos depois do limite (D: critério e meta
  validados individualmente; revalidação inicial a cada 1 s).
- **Por que estes valores.** Com revalidação a cada 1 s e um timeout total de 1 s
  (WS-C2 A), o pior caso teórico é ~2 s em condições normais, que é o alvo. O mínimo de
  5 s dá margem para carga e para atraso do `projects`, mantendo a janela de exposição
  curta face à duração típica de uma sessão de edição. Uma falha do autorizador nunca
  prolonga a autorização.
- **Cuidados.** Confirmar primeiro que o membro estava a receber eventos (controlo
  positivo) e que o produtor continuou a emitir depois da revogação: a ausência de
  eventos, por si só, não prova o corte.

### S16 — Acessos indevidos às bases de dados

- **Escala.** Nº de ligações ou operações admitidas indevidamente nas três instâncias
  Mongo (`projects_mongoDB`, `users_mongoDB`, `subscriptions_mongoDB`). Famílias de
  casos: (a) sem credenciais; (b) com credenciais por omissão ou presentes no Git;
  (c) com a credencial de **outro** serviço (por exemplo, a do `projects` a ler a BD
  `user`); (d) operação fora do privilégio do serviço (por exemplo, `dropDatabase`).
  Controlo legítimo: cada serviço e o `mongo-backup` funcionam com a sua credencial.
- **Por que foi escolhida.** Hoje qualquer processo na rede, ou no host através das
  portas publicadas, lê e altera diretamente todos os projetos e utilizadores, o que
  anula qualquer autorização feita acima. É parte da opção A de segurança (credenciais
  próprias e privilégio mínimo por serviço) e é fácil de medir de forma objetiva.
- **Base.** D11: leitura do `projects_mongoDB` sem credenciais aceite. As outras duas
  instâncias não foram medidas, mas não têm autenticação configurada.
- **Mínimo / alvo:** 0 / 0 (P), com 100% dos controlos legítimos (D: opção A).
- **Fora desta métrica (decisão de 20/11).** O TLS com validação do certificado do
  servidor nas ligações às BD, ao RabbitMQ e ao S3 (a outra metade da opção A) não é
  gate de S16/S17. As métricas medem o que impede o acesso indevido aos dados:
  credenciais e privilégio mínimo. O TLS protege contra quem escuta a rede interna do
  Docker, um ataque menos provável numa instalação local, e exige configurar
  certificados em cinco componentes. Se for implementado, regista-se como evidência
  adicional e não como cumprimento da métrica.

### S17 — Acessos indevidos ao broker e ao armazenamento S3

- **Escala.** Nº de operações admitidas indevidamente:
  - **RabbitMQ**: (a) AMQP e API de gestão com `user`/`password` (credencial publicada);
    (b) a credencial de um worker a consumir ou publicar numa fila que não é sua (por
    exemplo, `brightness_tool` a consumir `ws_queue` ou a apagar `project_queue`);
    (c) uma credencial de serviço a aceder à API de gestão.
  - **SeaweedFS/S3**: (a) operações com `admin`/`admin123` (valores por omissão
    versionados); (b) credencial com privilégio a mais (por exemplo, apagar o bucket);
    (c) acesso direto ao S3 sem assinatura. Controlo legítimo: o `img_storage` lê e
    escreve, e as URLs assinadas emitidas legitimamente funcionam através de `/s3/`.
- **Por que foi escolhida.** Com a credencial partilhada, qualquer componente
  comprometido pode ler, apagar ou injetar mensagens de processamento (e assim alterar
  resultados de outros utilizadores) ou ler os objetos de todos. Também faz parte da
  opção A.
- **Base.** D10: a API de gestão aceita a credencial publicada (200). S3 com a
  credencial por omissão: não medido.
- **Mínimo / alvo:** 0 / 0 (P), com 100% dos controlos legítimos (D: opção A).

### S18 — Superfície exposta: portas internas publicadas

- **Escala.** Nº de bindings de portas de serviços internos (todos exceto o nginx)
  publicados no host, separados por interface: todas as interfaces (`0.0.0.0`/`::`)
  vs. loopback. Medição estática sobre o `docker-compose.yaml` entregue
  (`docker compose config`) e confirmação em execução (portas realmente abertas).
- **Por que foi escolhida.** As diretrizes referem explicitamente "alguns [serviços]
  estão acessíveis diretamente a partir do exterior". É objetiva, barata e mostra um
  ganho claro. Por si só não chega (ver S02 na rede Docker), por isso entra ao lado das
  métricas de efeito e não em vez delas.
- **Base.** 12 bindings em 10 serviços, todos em todas as interfaces: `seaweedfs`
  (9000, 9090), `img_storage` (11000), `rabbitmq` (5672, 15672), `projects_mongoDB`
  (27018), `users_mongoDB` (27019), `projects` (9002), `users` (10001), `subscriptions`
  (11001), `generative-mock` (7860), `ws_gateway` (4000). Só o nginx (8080) devia estar
  exposto.
- **Mínimo:** 0 bindings internos fora do loopback. **Alvo:** 0 bindings internos (só o
  nginx 8080).
- **Por que estes valores.** O mínimo mantém o acesso de administração local (por
  exemplo, a gestão do RabbitMQ em `127.0.0.1`) sem expor nada à rede. O alvo é o
  desenho de referência: uma única entrada, a do nginx.

### S05 — Guarda: operações legítimas concluídas (inclui S09)

- **Escala.** Nº de operações legítimas concluídas com o resultado correto / total,
  numa lista fixa: o dono lê, edita, carrega imagem e vídeo, aplica o pipeline, faz
  preview e descarrega o resultado; o leitor lê; o editor edita e remove media; os
  workers processam; a quota é debitada; o dono e um membro autorizado recebem os
  eventos WS; o dono consulta a sua subscrição.
- **Por que foi escolhida.** Sem esta guarda, "0 admissões" poderia ser conseguido
  partindo a aplicação. É também a evidência de preservação funcional que as diretrizes
  pedem para este RNF.
- **Mínimo / alvo:** 100% / 100% (P). Exceção declarada: a política ACL-C1 (só o dono
  elimina o projeto) altera de propósito um comportamento da base. O caso "editor
  elimina o projeto" passa de permitido a recusado e é justificado como objeto da
  melhoria.

### S21 — Guarda: sobrecarga de latência

- **Escala.** Diferença entre as medianas da latência de pedidos leves pela entrada
  pública (`GET /projects/:user/:project`, `GET /users/:id`) na MF e na BF, em ms;
  100 pedidos de cada tipo, na mesma máquina. O `join-project` não entra, porque na base
  não tem ACK e não haveria valor comparável.
- **Por que foi escolhida.** O Ex. 7 regista o conflito DA-1 vs DA-2: mTLS, assinatura
  da identidade interna e a consulta de autorização acrescentam trabalho a cada pedido.
  Esta guarda mostra que a segurança não degradou a utilização normal.
- **Mínimo / alvo:** ≤ +10 ms / ≤ +5 ms (E).
- **Por que estes valores.** Com ligações reutilizadas (keep-alive), o handshake mTLS é
  amortizado e o custo por pedido reduz-se a uma assinatura/verificação RS256 e a uma
  consulta interna, da ordem de 1–5 ms. 10 ms ficam uma ordem de grandeza abaixo do
  limiar de 100 ms em que um utilizador percebe atraso numa interação (Nielsen, 1993).
  São valores de engenharia; o relatório deve apresentá-los como tal.

---

## 2. RNF 2 — Eficiência de desempenho: carregamento de ficheiros

**Fragilidade (diagnóstico).** Um vídeo (até 1 GiB no perfil premium) atravessa
nginx → `api_gateway` → `projects` → `img_storage` → S3. Nos três serviços Node é
mantido **inteiro em memória** (`multer.memoryStorage()`), e o `projects` grava-o ainda
num ficheiro temporário para o `ffprobe`. O gateway lê o corpo **antes** de verificar o
JWT, e os limites do perfil (tamanho, duração) só são verificados no fim. Com limites
de 2 GiB por contentor, um upload de 500 MiB leva o gateway a ~1,8 GiB e um segundo
upload provoca OOM, que derruba o gateway para **todos** os utilizadores. A aceitação
após o envio demora ~7 s a 500 MiB, contra os <3 s do `REQ-VID-SUBMIT-008`. Os
stakeholders afetados são os utilizadores que carregam vídeos, todos os outros
utilizadores ligados (o gateway é partilhado) e o operador.

**Regras comuns.** Corpus fixo: vídeos PAD (a amostra de 10 s com uma caixa MP4 `free`
até ao tamanho exato) e vídeos reais de `samples/video/`. Limites por contentor iguais
na BF e na MF. Cada estrato (perfil × tamanho) tem 5 tentativas, com o processo
reiniciado e também aquecido. Todas as falhas ficam no denominador.

### U01 — Pico de memória adicional por serviço Node

- **Escala.** MiB: pico de RSS do processo do serviço (`VmHWM`, com reposição
  imediatamente antes do upload) menos o RSS antes do upload, em `api_gateway`,
  `projects` e `img_storage`; para 10, 100 e 500 MiB. Reporta-se também o RSS absoluto.
- **Por que foi escolhida.** É a medida direta da fragilidade que as diretrizes
  descrevem ("cada vídeo é mantido inteiro em memória em cada serviço que atravessa").
  Medida em três tamanhos com o mesmo teto, prova também que a memória deixa de
  depender do tamanho do ficheiro, pelo que dispensa a métrica U05 (inclinação).
- **Base.** A 500 MiB: +1767 MiB (gateway), +759 MiB (projects), +729 MiB (storage). A
  100 MiB: +366 / +172 / +163 MiB.
- **Mínimo / alvo:** ≤64 MiB / ≤32 MiB em cada serviço e em cada tamanho
  (D: EVAL-M1).
- **Por que estes valores.** Em streaming, a memória fica limitada pelos buffers (os
  streams Node usam buffers de dezenas de KiB; uma parte multipart S3 tem pelo menos
  5 MiB e tipicamente 8–16 MiB) e não pelo ficheiro.
  64 MiB cobre uma parte de 16 MiB com uma margem de 4× para o runtime e é ~3% do limite
  de 2 GiB do contentor, o que permite dezenas de uploads em simultâneo. 32 MiB é o
  valor esperado de um desenho com partes de 8 MiB.

### U20 — Capacidade: 3 uploads simultâneos de 500 MiB (inclui U03)

- **Escala.** Nº de uploads concluídos com sucesso / 3, em 3 rondas, mais o nº de
  eventos OOM (`State.OOMKilled`, eventos do cgroup) e de reinícios de contentor.
- **Por que foi escolhida.** É o efeito que os stakeholders sentem: hoje, uploads
  grandes em simultâneo derrubam o serviço. Deve ser a diferença mais visível entre BF e
  MF.
- **Base.** Não medida. Previsão: falha, porque 3 × ~1,7 GiB excede os 2 GiB do gateway.
  B16 já registou um OOM do gateway num único upload de 500 MiB feito depois de outros.
- **Mínimo:** 3/3 numa ronda, 0 OOM, 0 reinícios, conteúdo íntegro. **Alvo:** 3/3 nas 3
  rondas (D: EVAL-M1).
- **Por que estes valores.** 3 é a concorrência C=3 escolhida no plano de avaliação:
  representa vários membros de uma equipa a carregar material ao mesmo tempo numa
  instalação local, e já excede o que a base aguenta. A memória do grupo nunca se
  divide por 3.

### U19 — Recusa de upload sem token antes de ler o corpo

- **Escala.** Para um upload de 500 MiB sem token: incremento de memória do gateway
  (MiB), bytes aceites pelo servidor antes da resposta e tempo entre o envio dos
  cabeçalhos e a resposta (ms). O cliente envia lentamente para que estes valores sejam
  observáveis.
- **Por que foi escolhida.** Liga os dois RNF (§5.2 do Bloco 2): autenticar antes do
  corpo é pré-requisito da eficiência e, ao mesmo tempo, impede que qualquer pessoa sem
  conta esgote a memória do gateway (negação de serviço barata).
- **Base.** 401 só depois de transferir os 500 MiB (3579 ms de envio), +500,1 MiB no
  gateway.
- **Mínimo:** recusa 401/403 com ≤8 MiB de incremento no gateway. **Alvo:** resposta
  ≤100 ms após os cabeçalhos (E).
- **Por que estes valores.** 8 MiB é o que o gateway pode precisar de ler para analisar
  os cabeçalhos e o início do multipart, sem nunca reter o ficheiro. 100 ms é o custo de
  verificar um JWT localmente com uma ida e volta na rede local, sem esperar pelo corpo.
- **Cuidado.** O nginx faz buffering do corpo por omissão (`proxy_request_buffering on`):
  mesmo que o gateway recuse cedo, o nginx pode receber o ficheiro inteiro primeiro.
  Medem-se em separado os bytes aceites pelo nginx e pelo gateway.

### U18 — Recusa correta de uploads inválidos

- **Escala.** Nº de uploads inválidos recusados com uma resposta 4xx definida e sem
  objeto/media criado / total de casos: free acima de 100 MiB (500 MiB), free com mais
  de 60 s (`too_long_90s.mp4`), corrompido (`corrupted.mp4`), vazio (0 bytes), imagem
  enviada ao endpoint de vídeo, premium com 1024 MiB + 1 byte.
- **Por que foi escolhida.** Na base, um upload free de 500 MiB, que devia ser recusado
  por exceder o limite do perfil, deu **502 e matou o gateway por OOM**. É uma falha real
  causada pelo buffering integral. Esta métrica mostra a melhoria e preserva as regras
  de validação existentes.
- **Base.** free 500 MiB → 502 + OOM; os outros casos não foram medidos (os pequenos são
  recusados pela validação existente).
- **Mínimo / alvo:** 100% / 100% (P/R: as regras de validação vêm do documento PL1-G4 e
  de `projects/utils/video.js`), e 0 OOM durante as recusas.

### U04 — Memória do nginx e do SeaweedFS

- **Escala.** MiB: pico da memória anónima do cgroup (`memory.stat` → `anon`, amostrada
  a cada 50 ms) acima do repouso, nos contentores `nginx` e `seaweedfs`, a 500 MiB com
  C=1; reportado também para C=3.
- **Por que foi escolhida.** O QS-02 exige "não esconder o custo no storage": retirar o
  ficheiro dos serviços Node pode simplesmente empurrar a memória para o proxy ou para o
  S3. Sem esta métrica, U01 poderia melhorar sem que a instalação gastasse menos.
- **Base.** Não medida em B16; no ambiente B14 houve amostras do nginx.
- **Mínimo:** +≤128 MiB (nginx) e +≤256 MiB (SeaweedFS). **Alvo:** +≤64 / +≤128 MiB
  (D: EVAL-M1, a calibrar com a BF).
- **Por que estes valores.** O nginx faz buffering para disco e não para memória, por
  isso o seu custo em RAM deve ser pequeno e constante. O SeaweedFS mantém em memória
  os chunks que está a receber e os índices (o tamanho dos chunks depende da
  configuração do filer/S3 e fica registado no manifesto da BF), por isso tem um teto
  maior. Os valores são tetos de engenharia: depois da BF só podem ser apertados ou
  mantidos, com registo.
- **Cuidado.** Usa-se `anon` e não a memória total do cgroup, porque esta inclui a page
  cache dos ficheiros escritos, que o kernel liberta sob pressão. Se o cgroup v2 não
  estiver disponível, usa-se o RSS dos processos.

### U08 — Disco temporário e resíduos

- **Escala.** Pico de bytes em ficheiros temporários por componente durante o upload
  (nginx `client_body_temp`, `/tmp` do `projects`, `/tmp` do `img_storage` e do gateway)
  e bytes/ficheiros residuais 60 s depois de terminar (sucesso, recusa e falha).
- **Por que foi escolhida.** É a outra forma de esconder o custo: trocar RAM por disco.
  Na base o ficheiro é gravado em disco duas vezes (o spool do nginx e o temporário do
  `ffprobe` no `projects`), além do armazenamento final. Resíduos acumulados esgotam o
  disco do host ao longo do tempo.
- **Base.** Não medida. Previsão: ~F no nginx e ~F no `projects` por upload.
- **Mínimo:** em cada componente, pico ≤ C×(F + 16 MiB), com F o tamanho do ficheiro e C
  a concorrência, e 0 resíduos 60 s depois. **Alvo:** sem spool integral no caminho
  nginx → S3, e ≤16 MiB de disco temporário por upload (E).
- **Por que estes valores.** O mínimo é um teto de segurança: garante que a refatoração
  não acrescenta cópias além de uma por upload, e pode já ser cumprido pela base (é uma
  guarda contra regressões). A melhoria demonstra-se pelo alvo: em streaming de ponta a
  ponta, o único disco temporário legítimo é o de uma parte multipart (≤16 MiB) ou o de
  uma leitura limitada para o `ffprobe`.

### U09 — Guarda: aceitação após o fim do envio

- **Escala.** `t_ready − t_send` em ms: do último byte entregue pelo cliente à resposta
  de aceitação, por amostra válida de 500 MiB premium. Reporta-se também a 10 e 100 MiB.
- **Por que foi escolhida.** É o único valor com **requisito escrito**: o
  `REQ-VID-SUBMIT-008` do documento PL1-G4, que a base falha. No QS-02 o tempo é guarda
  (o objeto principal são os recursos), mas uma guarda com origem externa e que mostra
  uma melhoria.
- **Base.** Mediana 6923 ms (mín. 6704, máx. 7977).
- **Mínimo / alvo:** <3000 ms / <1000 ms em cada amostra (R: MVP / alvo do requisito).
- **Cuidado.** O buffering do nginx pode dominar este tempo. O cliente regista
  `t_send` depois de entregar o último byte ao socket, como em B16.

### U25 — Guarda: impacto nos outros utilizadores

- **Escala.** Nº de erros e mediana da latência de 100 pedidos leves
  (`GET /users/:id`, `GET /projects/:user/:project`) feitos durante 3 uploads de
  500 MiB em simultâneo, comparados com uma janela de controlo sem uploads na mesma
  campanha; 3 pares.
- **Por que foi escolhida.** O gateway é partilhado: o pior efeito da base é que um
  upload grande degrada ou derruba o serviço para quem nem está a carregar nada. Esta
  guarda mostra a relevância para todos os stakeholders.
- **Base.** Não medida. Em B16, um OOM do gateway afetou todos os clientes.
- **Mínimo:** 0 falhas e mediana ≤1,10× o controlo. **Alvo:** mediana ≤ controlo
  (D: EVAL-M1, U25 promovida a guarda em 18/11).

### U15 — Guarda: integridade do original

- **Escala.** Nº de originais cujo SHA-256 descarregado do armazenamento é igual ao do
  ficheiro enviado / total de uploads aceites.
- **Por que foi escolhida.** O streaming e as partes multipart introduzem novas formas
  de corromper ou truncar ficheiros; o ETag do S3 não é um hash do conteúdo em
  multipart.
- **Mínimo / alvo:** 100% / 100% (P).

### U17 — Guarda: uploads válidos aceites

- **Escala.** Nº de uploads válidos aceites (204) e associados ao projeto com
  `media_type: "video"` / total, por perfil (free/premium), tamanho (10/100/500 MiB) e
  formato (MP4, MOV, WebM real).
- **Por que foi escolhida.** É a preservação funcional do próprio fluxo melhorado,
  incluindo o adaptador de compatibilidade multipart (UP-C1 A).
- **Base.** 14/14 em B16.
- **Mínimo / alvo:** 100% / 100% (P).

### U10 — Guarda: tempo total do upload

- **Escala.** Mediana de `t_ready − t0` (ms) por estrato.
- **Por que foi escolhida.** Impede que a redução de memória seja conseguida tornando o
  upload mais lento (por exemplo, com buffers minúsculos ou um hash síncrono adicional).
- **Base.** Mediana 10 525 ms a 500 MiB.
- **Mínimo:** ≤1,10× a mediana BF do mesmo estrato. **Alvo:** ≤ a mediana BF
  (D: EVAL-M1).
- **Por que estes valores.** 10% de tolerância cobre o ruído típico entre campanhas no
  mesmo host; acima disso a perda é real.

---

## 3. Relações entre as métricas dos dois RNF

- **U19 é pré-requisito comum.** Autenticar antes do corpo serve a eficiência e a
  segurança.
- **S21 e U25/U10 vigiam o conflito DA-1 vs DA-2.** A segurança acrescenta CPU e
  latência; o streaming muda I/O e estados. Cada RNF é avaliado por si; o efeito
  combinado aparece nas guardas.
- **S18 e S02 complementam-se.** Fechar portas reduz a superfície (S18), mas só a
  verificação de identidade no serviço resolve o acesso a partir da rede interna (S02).
- **U04 e U08 complementam U01.** Garantem que a memória retirada dos serviços Node não
  reaparece no proxy, no S3 ou no disco.

## 4. Métricas do catálogo não selecionadas

| IDs | Motivo |
|-----|--------|
| S06 | Provavelmente já passa na base (G01 → 401). Mantida como teste, não como métrica. |
| S07, S22–S24, U14, U16, U21, U23, U26 | Medem mecanismos que não existem na base (NA), por isso não demonstram melhoria. Ficam como testes de verificação se o mecanismo for implementado. |
| S08 | Testa a robustez do mTLS. Fica de fora a menos que o mTLS entre no âmbito; o efeito na rede interna já é medido em S02. |
| S11 | Coberta por S04 (entradas) e S12 (eventos depois do limite). |
| S13 | É uma política (ACL-C1); verificada nos controlos de S05. |
| S19, S20 | Segredos no Git e retirada da CA: relevantes, mas fora da autorização e com custo alto para o prazo. |
| U02, U05, U06, U07 | Diagnóstico: retenção, inclinação, CPU e amplificação de rede são reportados se forem recolhidos, sem gate. |
| U22, U24 | Dependem do ciclo de vida (UP-C4–C9) ainda não escolhido; U24 é verificada como controlo de S05 (a quota só é debitada no Apply). |

## Referências

- [Diretrizes da Fase 2](guidelines/fase-2-guidelines-1.pdf), §"O que se espera para cada requisito".
- [Catálogo de 60 métricas e baseline exploratória](fase2-metricas-e-baseline.md).
- [Plano de avaliação](fase2-plano-avaliacao.md) e [revisão](fase2-revisao-plano-avaliacao.md) (EVAL-B1/C1/R1/M1).
- [Ex. 6, Bloco 2](exercises/06-architectural-patterns/resolution-block-2.md) (QS-01, QS-02, QS-07, CAND-1/2) e [Ex. 7](exercises/07-architectural-tactics/resolution.md) (DA-1/DA-2).
- [Evidência B16](../memory-bank/intents/001-phase-2-quality-improvements/evidence/nfr-2026-11-16/README.md).
- Documento de requisitos PL1-G4: [doc-ext-requisitos-2627.pdf](requirements/doc-ext-requisitos-2627.pdf) (`REQ-VID-SUBMIT-008`).
- Nielsen, J. (1993). *Usability Engineering*, cap. 5 (limiares de 0,1 s / 1 s / 10 s).

# Fase 2 — Inventário para a transição das sessões

**Equipa:** PL2-G4. **Preparado em:** 16/11/2026.
**Estado:** âmbito e retenção declarados; metadados Docker e contagens agregadas
de contas/projetos recolhidos numa máquina. Browsers e restantes computadores por levantar.
Entrega de referência: 27/11/2026.

## Âmbito confirmado e limites da informação

Em 2026-11-16T18:25:38Z foi registada a informação do utilizador:

> Usamos o PictuRAS apenas localmente, nos computadores da equipa, através de Docker
> Compose. Cada elemento administra a sua instalação. Não temos uma instalação
> partilhada nem utilizadores externos. Ainda não existe uma lista formal dos ambientes.

Esta declaração resolve a dúvida sobre utilização externa/partilhada no âmbito
comunicado. Não é uma contagem técnica de instalações, identidades ou browsers.
Um elemento pode ter vários checkouts/projetos Compose, volumes ou perfis de browser;
não se infere que existem exatamente quatro instâncias ou uma identidade por pessoa.

**Clarificação posterior do utilizador, registada em 2026-11-16T19:18:54Z:** Luís
é responsável por esta máquina (`LOCAL-HOST-01` / `ADM-01`). Preservar **ambos** os
conjuntos de volumes, `picturas` e `picturas-quality-20261114`. A escolha da instalação
para desenvolvimento e avaliação fica para uma decisão posterior. A contagem foi
pedida sem alterar os dados; não implica autorização de limpeza, migração ou rotação.

O inventário prepara a escolha da migração antes de renovar o segredo HS256,
preservando identidade e projetos anónimos. SESS-C1 A foi posteriormente
selecionada individualmente com confirmação técnica: transição/reemissão assistidas
e 7 dias absolutos sem refresh. O inventário/prova ainda condicionam a execução. As decisões de JWT, WS e cobertura TLS/mTLS
continuam as registadas nos [requisitos](../../memory-bank/intents/001-phase-2-quality-improvements/requirements.md).

## Responsáveis e instalações a identificar

Cada responsável lista as suas instalações atuais e dados retidos, inclusive
instalações paradas que se pretenda voltar a usar. As referências abaixo identificam
responsáveis; não representam instalações já descobertas ou contagens concluídas.

| Referência | Responsável pela instalação local | Máquina(s), projeto(s) Compose e volumes | Estado da recolha |
|------------|------------------------------------|------------------------------------------|-------------------|
| ADM-01 | Luís Miguel Coelho — PG64000 | LOCAL-HOST-01: `picturas` e `picturas-quality-20261114`; ambos a preservar | Metadados/contagens recolhidos; browsers e outros ambientes pessoais por confirmar |
| ADM-02 | Alexandre de Oliveira Monsanto — PG65397 | Por listar | Pendente |
| ADM-03 | Diogo Alexandre Gomes Silva — PG63941 | Por listar | Pendente |
| ADM-04 | José Miguel da Silva Santos — PG63522 | Por listar | Pendente |

## Registos a preencher

Usar referências locais opacas (`ENV-…`, `BROWSER-…`, `ANON-…`, `PROJECT-…`) no
documento partilhado. A correspondência com IDs reais fica sob controlo de cada
administrador fora do Git. Não copiar JWT, segredos, chaves, credenciais ou URLs
assinados. **NM** significa não medido/não recolhido, nunca zero.

| Registo | Campos a recolher | Fonte e limite |
|---------|-------------------|----------------|
| Instalação | Referência, responsável, máquina, checkout/commit, projeto Compose, ficheiros de configuração usados, estado observado e instante UTC | Operador e metadados Docker/checkout; existência de configuração não prova que a instalação esteja ativa. |
| PKI local a preparar | Referência pública da CA por instalação, validade CA/certificados de serviço, responsável pela renovação, versão/localização do script e última verificação de arranque/renovação | PKI-C1 A: CA 365 dias, serviço 30 dias, renovar com 7 dias restantes; script local manual incluído na entrega. Campos ainda NM: não foi emitida CA nem executado script nesta revisão. Chave CA fora do Git/build/contentores aplicacionais; não partilhar chaves nem confiar implicitamente noutra instalação. |
| Dados retidos | Volumes/BD/buckets associados, fixtures vs. dados a preservar, cópia de segurança existente e localização protegida | Administrador e metadados; existência de backup não prova recuperação ensaiada. Não criar/apagar volumes neste levantamento. |
| Origem do frontend | Protocolo, hostname e porta usados por cada perfil de browser | Informação do responsável/browser; não guardar caminhos com tokens. |
| Browser/perfil | Referência, responsável, origem, acessível/indisponível/desconhecido, sessão presente/ausente/desconhecida, data da observação | Observação do perfil existente; não inferir de contas na BD ou de um browser instalado. |
| Identidade anónima | Referência por instalação, correspondência privada com `_id`, tipo observado no servidor, contexto/fixture conhecido e evidência disponível | Users/administrador; valor guardado no cliente não é prova de titularidade. |
| Associação browser↔identidade | Referências, correspondência confirmada/por confirmar, data e quem a confirmou | Comparar estado do browser com instalação e registos de domínio, sem publicar JWT. Não presumir associação única: várias sessões podem referir a mesma identidade. |
| Projetos/media | Referências dos projetos por `user_id`, quantidade de projetos e media, integridade/objetos ainda por verificar, dados a preservar | Projects e storage da mesma instalação; não somar IDs de instalações distintas como se fossem uma única conta. |
| Validade atual | Expiração conhecida ou NM, cliente disponível para transição e eventuais casos já expirados | Metadados locais lidos sem divulgar token; claims antigas não são prova independente de identidade. Sete dias no código não determina a expiração de cada sessão retida. |
| Recuperação/estado | Evidência independente/associação administrativamente conhecida, dúvidas, perfil inacessível, identidade sem browser e decisão ainda necessária | Administrador; não escolher recuperação ou emitir credenciais durante a recolha. |
| Proveniência | Fonte, responsável, instante UTC, limitação e referência do registo anterior | Toda a observação deve ser distinguível de declaração, inferência ou campo pendente. |

O frontend guarda a sessão em `localStorage`. A origem precisa de constar do registo:
o armazenamento não deve ser tratado como uma sessão global da máquina. Referência:
[WHATWG — localStorage](https://html.spec.whatwg.org/multipage/webstorage.html#the-localstorage-attribute).
O [código consultado](../../frontend/lib/mutations/session.ts) pode criar outra
identidade ao fazer logout após erro de validação; abrir/recarregar a aplicação
não é um método neutro de recolher o estado antigo.

## Roteiro de recolha local antes de executar a transição

1. **Listar ambientes com cada responsável.** Conferir os checkouts/projetos Compose
   e volumes atuais, incluindo os parados. `docker compose ls -a` e, no projeto
   correto, `docker compose ps -a` são entradas de consulta de metadados. Registar
   a data e não tratar um resultado numa máquina como inventário da equipa inteira.
2. **Observar dados sem alterá-los.** Usar acesso administrativo de leitura às BD
   identificadas, com projeções restritas: anónimos por `type` e projetos por
   `user_id`, depois referências de media. Não usar rotas públicas vulneráveis para
   listar todas as contas nem recolher nomes, emails ou hashes de passwords.
3. **Conferir browsers existentes com o respetivo responsável.** Consultar apenas
   metadados necessários no armazenamento do perfil/origem, sem logout, registo,
   reload ou validação de sessão que possa substituir a identidade. Se não for
   possível observar sem alterar o estado, marcar pendente e definir a recolha
   antes de prosseguir. Não exportar o objeto `session` completo para o relatório.
4. **Reconciliar identidades e projetos.** Identificar browsers sem correspondência,
   anónimos sem browser conhecido, dados sem associação verificada e fixtures.
   Sem registo central de sessões/tokens no schema consultado, contar contas
   anónimas não é contar sessões ativas. Não inventar última atividade ou login.
5. **Consolidar apenas informação necessária.** Partilhar referências e totais
   agregados, dúvidas e fontes; manter a correspondência real protegida localmente.
   Separar instalações e datas, sem misturar experiências históricas com uso atual.

Os passos descrevem o procedimento completo. Primeiro foram recolhidos metadados
Docker e a presença do ficheiro Compose histórico; depois, por pedido explícito,
foram contadas contas/projetos em cópias temporárias dos volumes MongoDB. Os volumes
originais só foram montados em leitura; MongoDB arrancou apenas nas cópias isoladas.
Não foram alterados dados originais, utilizadores, projetos ou segredos, nem
consultados browsers. Os contentores originais permaneceram parados.

## Recolha local parcial — 2026-11-16T19:03:51Z

Fonte: consultas de leitura ao daemon Docker local, filtradas para PictuRAS; ver
o [registo normalizado](../../memory-bank/intents/001-phase-2-quality-improvements/evidence/session-inventory-local-2026-11-16.json).
A máquina é referida como `LOCAL-HOST-01`; o responsável foi posteriormente
confirmado como Luís (`ADM-01`). Nomes de outros projetos Docker foram excluídos.

| Referência | Observação atual | Pendências |
|------------|------------------|------------|
| ENV-LOCAL-01 | `picturas-quality-20261114`: 13 contentores, todos `exited`, e 6 volumes etiquetados retidos; Luís, preservar | Associações a browsers e eventual uso futuro. O ficheiro Compose temporário indicado nas etiquetas já não existe. Não reconstruir a stack com outra configuração sem avaliar compatibilidade. |
| ENV-LOCAL-02 | Projeto `picturas`: 8 volumes etiquetados, nenhum contentor com essa etiqueta encontrado; Luís, preservar | Browsers e eventual uso futuro. Entre os nomes existe `picturas_minio_data`; não foi verificado o conteúdo/compatibilidade do storage. |

Total observado nesses conjuntos: **13 contentores parados e 14 volumes**. São
metadados locais, não contagens de contas, projetos ou sessões e não um inventário
dos computadores de toda a equipa. Um conjunto de volumes sem contentores não
equivale a uma instalação ativa. Não inferir a inexistência de outros ambientes
sem completar o levantamento com os responsáveis.

Nesta primeira observação as contagens de identidades/projetos ficaram NM por não
haver MongoDB original em execução. A recolha seguinte resolveu essa parte por
cópias temporárias, mantendo os originais parados e os dois conjuntos preservados.

## Contagens nas cópias — 2026-11-16T19:17:57Z

Fonte: [resultado agregado](../../memory-bank/intents/001-phase-2-quality-improvements/evidence/session-counts-local-2026-11-16.json),
recolhido pelo [coletor](../../memory-bank/intents/001-phase-2-quality-improvements/evidence/collect-session-counts.py).

| Conjunto | Contas totais | Anónimas | Gratuitas | Premium | Projetos | Projetos de anónimos | Referências de media |
|----------|---------------|----------|-----------|---------|----------|---------------------|---------------------|
| `picturas` | 4 | 2 | 2 | 0 | 2 | 0 | 3 |
| `picturas-quality-20261114` | 13 | 0 | 13 | 0 | 10 | 0 | 28 |

Todos os projetos contados pertencem a contas gratuitas; nenhum dono ficou sem
correspondência na coleção de contas da respetiva cópia. As contagens são por
conjunto, não pessoas únicas nem sessões ativas. Zero projetos de anónimos não
autoriza descartar as suas identidades; presets, browsers e objetos no storage
não foram verificados nesta recolha. Media são referências na BD, não ficheiros
cuja existência/integridade tenha sido validada.

**Método e preservação:** verificação prévia de ausência de contentores ativos
nos quatro volumes de BD, montagens originais apenas em leitura e cópias privadas
temporárias. MongoDB usou a imagem local identificada no relatório, sem rede externa
ou portas publicadas, apenas sobre as cópias. Foram guardados agregados, sem IDs
reais de contas/projetos, nomes, emails, passwords ou JWT. Os hashes dos manifestos
de ficheiros dos quatro originais ficaram iguais antes/depois; cópias e contentores
temporários foram removidos. Os restantes volumes não foram alterados.

A [documentação MongoDB sobre cópias de ficheiros/snapshots](https://www.mongodb.com/docs/manual/tutorial/backup-with-filesystem-snapshots/)
descreve as condições de consistência do estado copiado. Aqui a recolha foi feita
com os originais parados, sem executar recuperação ou consultas sobre eles;
eventuais escritas de recuperação ficaram limitadas às cópias temporárias.

A [primeira tentativa](../../memory-bank/intents/001-phase-2-quality-improvements/evidence/session-counts-local-attempt-1-2026-11-16.json)
falhou durante a cópia, sem contagens; os originais também ficaram com hashes iguais
e as cópias foram limpas. Após ajustar as permissões do auxiliar para as cópias,
a segunda tentativa concluiu. Não confundir essa falha de recolha com um teste de
fiabilidade da aplicação. Esta operação é inventário, não migração nem escolha da
instalação de desenvolvimento/avaliação.

## Ambientes históricos a reconciliar com os responsáveis

| Candidato documental | Evidência existente | O que falta confirmar agora |
|----------------------|--------------------|----------------------------|
| Checkout atual / configuração principal | [Compose](../../docker-compose.yaml), entrada prevista `https://localhost:8080`; Luís identificado como responsável desta máquina | Escolha de utilização futura e browsers associados. Não prova de instalação ativa. |
| Experiência Intel/Linux de 14/11 | [Registo de ciclo de vida](../../memory-bank/intents/001-phase-2-quality-improvements/evidence/live-lifecycle-2026-11-14.json): parada nessa data. ENV-LOCAL-01 confirmada, Luís responsável e preservação escolhida | Origem da configuração a recuperar e escolha de utilização futura, sem confundir contagens atuais com resultados históricos. |
| Experiência ARM de 16/11 | [Evidências fornecidas](../../memory-bank/intents/001-phase-2-quality-improvements/evidence/nfr-2026-11-16/README.md): stack isolada declarada `picturas-nfr` | Responsável, máquina atual, existência dos dados e eventual relação com instalações pessoais. Não inferir utilizadores externos dessa experiência. |

## Síntese e critérios para escolher a migração

| Informação | Estado atual |
|------------|--------------|
| Uso apenas local nos computadores da equipa | Declarado pelo utilizador |
| Administração por cada elemento | Declarado pelo utilizador |
| Instalação partilhada / utilizadores externos | Não existem, conforme declaração do utilizador; não é contagem técnica |
| Lista formal de instalações/volumes | Parcial: ENV-LOCAL-01/02 numa máquina; restantes responsáveis por levantar |
| Responsável/retensão nesta máquina | Luís / preservar ambos os conjuntos |
| Contas/projetos nesta máquina | Recolhidos por conjunto na tabela acima; restantes computadores pendentes |
| Browsers/sessões ativas e existência dos objetos de media | NM; referências de media contadas na BD não provam objetos existentes |
| Instalação para desenvolvimento e avaliação | Por decidir; nenhuma selecionada nesta recolha |
| Associações browser↔identidade↔projetos e casos inacessíveis | Pendentes |
| Procedimento de migração, recuperação e renovação | SESS-C1 A selecionada individualmente com confirmação técnica; prova concreta/ferramenta de emissão/importação e ensaio ainda pendentes |

- [ ] Cada responsável listou as instalações e dados retidos relevantes, com data.
- [x] Metadados e contagens de contas/projetos numa máquina recolhidos, com fonte,
  responsabilidade/retensão e prova de preservação dos originais. Browsers pendentes.
- [ ] Identidades/projetos a preservar e respetivos browsers estão reconciliados;
  lacunas e casos inacessíveis têm tratamento explícito a decidir.
- [ ] Fixtures estão distinguidas dos dados a preservar; nada é considerado
  descartável só por ser local, estar parado ou ter JWT expirado.
- [ ] A proposta de migração preserva IDs e associações e não usa apenas JWT/ID
  antigo como prova de titularidade, dado o segredo exposto.
- [ ] Antes/depois permitem avaliar F06: preservação de identidade/projetos,
  autenticação válida e reconexão WS, incluindo falhas e recuperação.

O contexto local fundamenta SESS-C1 A, selecionada individualmente pelo utilizador
e confirmada tecnicamente pelo assistente em 17/11. O [contrato de sessões](fase2-sessoes-identidade-partilhas-ws.md)
exige prova independente e reemissão para a mesma identidade, incluindo expiração
anónima futura; JWT de 7 dias absolutos, sem refresh automático. Sem prova, dados
preservados/caso pendente. A escolha não prova associação nem executa a ferramenta.
Não emitir credenciais com base só no ID/JWT antigo, não presumir que os dois
conjuntos locais estão descartáveis e não os selecionar para avaliação por omissão.
Prova e ferramenta/procedimento de emissão/importação devem ficar implementados e
ensaiados. Nenhuma credencial foi emitida ou browser inspecionado nesta revisão.
As dúvidas de inventário não impedem continuar requisitos independentes de uploads,
certificados e medição; fontes/declarações/observações mantêm proveniência distinta.

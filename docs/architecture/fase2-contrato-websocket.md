# Fase 2 — Contrato de autorização WebSocket

**Equipa:** PL2-G4. **Estado:** WS-C1 A/WS-C2 A/WS-C3 A/WS-C4 A validadas individualmente;
WS-C5 B selecionada individualmente e confirmada tecnicamente em 17/11/2026.
Especificação de trabalho para implementação/testes, sem aprovação integral dos requisitos.
Complementa as [decisões](../fase2-ideias-1-e-2.md) e o
[protocolo de métricas WS](../fase2-metricas-e-baseline.md#41-protocolo-de-permanência-ws--condições-validadas-e-prova-pendente).
Não é uma implementação, uma medição ou a aprovação do conjunto dos requisitos.

**Cobertura para a entrega de 27/11 — opção A validada individualmente:** mTLS
nas APIs internas, incluindo este canal WS → projects, com autorização específica
por serviço/operação. Nos restantes canais exige-se TLS com validação do servidor;
MongoDB/RabbitMQ/S3 usam credenciais próprias e permissões mínimas onde aplicável.
mTLS universal não é requisito desta entrega. As decisões JWT e WS mantêm-se.
O detalhe por canal está na [matriz D4](../fase2-ideias-1-e-2.md#d4--mtls-entre-serviços-ciclo-de-certificados-e-pares).

## Condições selecionadas e concretização por demonstrar

D6.2 B exige consulta à projects em cada entrada. D6.3 usa revalidação inicialmente
a cada 1 s, agrupada por projeto com autorização individual por membro/contexto.
Critério de corte ≤5 s e meta ≤2 s, ambos por demonstrar experimentalmente.
Autorização local até 5 s desde o início da consulta positiva, limitada pelo JWT e
pela permissão efetiva; falhas não renovam. Negação efetiva retira imediatamente
o acesso afetado, preservando outros acessos válidos. JWT expirado termina a ligação;
o frontend trata reconexão explicitamente com JWT válido e nova autorização por sala.

O par QC-06 + QC-05 está acordado. As validações de detalhe anteriores são
individuais. Em 16/11, o utilizador validou explicitamente WS-C1 A e WS-C2 A e
escolheu D4 mTLS, substituindo HTTPS + JWT assimétrico de serviço. O registo não
atribui aprovação aos restantes elementos, execução de testes ou autorização para
alterar a aplicação. D3 mantém HS256 de utilizador e identidade RS256 do gateway.

| ID | Escolha validada individualmente | Alternativa / trabalho pendente |
|-------------------|--------------------------|----------------------|
| WS-C1 A | Consulta direta ws_gateway → projects por mTLS; projects autentica especificamente WS e autoriza as operações; WS delega identidade/expiração verificadas no JWT e os contextos apresentados; projects decide permissões | Percurso via gateway adiado; cadeia, identidade e pares/ações precisam de implementação e prova. Qualquer certificado da CA não basta. |
| WS-C2 A | Timeout total inicial 1 s, incluindo espera/ligação/envio/leitura, até 50 avaliações membro/contexto por pedido; configuráveis e sujeitos a medição | Vários lotes para projetos maiores. WS-C3 fixa 4 globais/1 por projeto/64 KiB; WS-C4 fixa 16 pendentes; restante dimensionamento pendente, sem capacidade demonstrada. |
| WS-C3 A | Limites iniciais configuráveis: 4 consultas HTTP globais, no máximo 1 por projeto, lotes alternados entre projetos e 64 KiB por corpo JSON de pedido/resposta | Sem capacidade/prazos demonstrados. WS-C4 fixa 16 pendentes; corpus final pendente; timeout inclui espera e não reinicia no envio; fila cheia/espera excessiva não renovam autorização nem concedem novos joins. |
| WS-C4 A | 16 lotes pendentes por processo, além de 4 ativos, até 1 pendente por projeto; mais recente substitui pendente sem reiniciar o deadline; remover expirados | Concluir callbacks substituídos explicitamente e preservar outros contextos; sem fila oculta ou renovação em falha. Limites do estado/corpus e justiça por medir. |
| WS-C5 B | 512 ligações/4096 contextos por processo com reservas, 32 salas/ligação e 4 vias/sala; taxas/buckets/entradas 4–8–64 KiB conforme contrato de 17/11 | Tetos configuráveis, não capacidade demonstrada. Excesso 513/4097 mede recusa controlada; corpus com mais admissões exige revisão explícita antes de congelar. |

WS-C5 B toma payload/ordenação/limites abaixo como especificação de trabalho
confirmada tecnicamente para concretizar a seleção individual, sem declarar
algoritmo implementado ou ensaios passados.
WS-C3/WS-C4 fixam os limites iniciais e a alternância/substituição; o algoritmo
concreto e a prova dos limites de estado ainda precisam de implementação/teste. A revisão integral de requisitos
e prova de implementação continuam pendentes. PKI-C1/ACL-C1 são tratados nas decisões de certificados/permissões.

## Situação observada no código

**Seleção de 17/11 A/A/A/B:** [SESS-C1/JWT-C1/LINK-C1/WS-C5](fase2-sessoes-identidade-partilhas-ws.md)
regista recomendação individual do utilizador e confirmação técnica: sessões
assistidas, 7 dias HS256/30 s identidade interna, risco residual de reutilização
contextual, links até revogação e WS-C5 B (512 ligações/4096 contextos). Contrato/
ordenação e cenários lógicos v1 fixados para ensaio; não são implementação/capacidade
comprovadas. Eventos pessoais de projeto também precisam de autorização/corte.

**Validação posterior A/B/A:** [WS-C4/PKI-C2/PKI-C3](fase2-fila-ws-e-revogacao.md)
fixa individualmente 16 lotes pendentes por processo WS, além das 4 consultas
ativas, até 1 pendente por projeto; substituição pelo mais recente sem reiniciar
prazo e remoção de expirados. Retirada de confiança usa nova CA/reemissão completa,
sem CRL, e manutenção/reinício com isolamento até prova de todos os participantes.
Chamadas completas WS → projects e projects → armazenamento e recusa da CA antiga
são testes obrigatórios na retirada; ligações/retomas antigas não podem sobreviver.
Mecanismo escolhido, sem implementação, ensaios ou acordo coletivo destes detalhes.

- O [frontend](../../frontend/app/dashboard/[pid]/page.tsx) emite `join-project`
  apenas com `pid`. O [ws_gateway](../../wsGateway/index.js) aceita essa string e
  entra em `project:<pid>` sem consulta de autorização.
- O JWT é verificado uma vez no handler de ligação quando existe token; não existe
  término agendado na sua expiração nem contexto de autorização por membro de sala.
- [Partilhas](../../projects/models/project.js) têm `id`, `permission`, `createdAt`
  e `revoked`. `expiresAt` não existe no schema atual; LINK-C1 A/D8 mantém
  legados e novos até revogação e adia expiry nesta entrega. Não criar prazo oculto.
- [Criar/revogar links](../../projects/controllers/project.js) incrementa `version`;
  a versão também é usada noutras alterações. Não representa, sozinha, uma prova
  completa de autorização atual ou de ordem das respostas de rede.
- O [servidor projects](../../projects/bin/www) usa HTTPS com certificados atuais,
  sem configurar autenticação mTLS de clientes. O canal da proposta WS-C1 precisa
  de implementação e ensaio; não existe por já haver TLS.
- Preview/progresso também seguem `io.to(user)`; [mensagens da projects](../../projects/utils/project_msg.js)
  nem sempre transportam projeto. A condição de verificar autorização antes da
  emissão protegida tem de cobrir esses percursos, não apenas `project:<id>`.
  Sala pessoal/JWT não demonstram permissão atual de projeto. A migração de
  payloads e a asserção de corte nesse percurso são propostas de revisão, sem
  divulgação após revogação demonstrada em execução nesta análise.

## Identidade e fronteira de confiança — WS-C1 A validada

**Opção A, validada individualmente:** projects autentica e autoriza especificamente o certificado
de cliente de ws_gateway na rota interna de avaliação. Validar cadeia/validade e
identidade do serviço; possuir outro certificado da mesma CA não basta. O WS deriva
o sujeito e a expiração do JWT verificado da ligação, e transmite-os com os
contextos apresentados. Não aceita `sub`, expiração ou permissões escolhidos pelo
browser como identidade comprovada.

Isto é **delegação confiada ao WS**: projects verifica o serviço por mTLS e confia
na sua declaração sobre o utilizador; não verifica a assinatura HS256 original
nessa opção. O WS não recebe a chave privada RS256 do gateway e projects não recebe
o segredo HS256. Projects mantém a decisão de domínio para cada membro/contexto.
Uma falha do WS ao associar sujeito e contexto é um risco desta fronteira e tem de
ser testada. Um cabeçalho `X-Caller-Id` enviado diretamente por outro cliente não
pode ter o mesmo efeito. Restringir esta delegação à rota e ações previstas.

**Opção B, adiada:** acrescentar o percurso pelo api_gateway, que valida a credencial de
cada membro e emite a identidade RS256 apropriada à consulta de projects. Reutiliza
o emissor de identidade escolhido em D3, mas exige adaptar o contrato a vários
membros/contextos e acrescenta um salto, verificações e dependência. O contrato não
pode assinar uma lista de sujeitos arbitrária só porque a chamada é interna.

A simplicidade/custo relativo é uma inferência de desenho, não um benchmark.
Ambas as alternativas consideradas consultam projects por entrada; a escolhida é
a direta. Não introduz bilhetes de sala. WS-C1 não altera HS256/RS256 de D3 nem a
decisão de permissões pela projects. O [registo D4](../fase2-ideias-1-e-2.md#d4--mtls-entre-serviços-ciclo-de-certificados-e-pares)
explicita a proteção das chaves, emissão/renovação e matriz de pares autorizados.

## Contrato funcional proposto

### Browser → ws_gateway

O evento `join-project` apresenta o projeto e uma via de acesso: propriedade ou
um `shareId`. O formato de trabalho é `{ projectId, access: { kind: "owner" } }` ou
`{ projectId, access: { kind: "share", shareId } }`, com callback de confirmação.
O sujeito vem sempre da ligação autenticada. Não pedir ao cliente para declarar
`allowed`, a permissão efetiva ou o dono como prova de acesso.

Cada pedido de entrada exige consulta fresca. Não usar a autorização local de
outro membro/contexto ou uma entrada anterior para conceder uma entrada nova em
indisponibilidade. O join só se confirma depois da decisão positiva ainda válida
e da entrada efetiva. O callback distingue `joined`, `denied`, `unavailable`,
`invalid_request` e `session_expired`; nomes da especificação de trabalho, ainda sem implementação. Timeout do callback
não é autorização. Repetir uma entrada já confirmada não deve duplicar estado,
mas mantém a exigência de consulta por pedido de entrada.

Um membro pode apresentar outra via para o mesmo projeto. Conservar separadamente
as vias apresentadas e verificadas, sem descobrir links secretos não apresentados.
Revogar uma delas não retira a sala se outra continuar a autorizar o acesso. Pedir
`leave-project` retira o membro daquela sala e invalida as avaliações pendentes
para essa pertença. Desligar invalida todas as pertenças dessa ligação.

Não acrescentar uma exigência de edição para receber eventos que o modelo permite
ao leitor. Entrada na sala não concede autorização para mutações HTTP nem ocupa,
por si só, um lugar de editor/presença. Rever os payloads recebidos por read/edit
para preservar o comportamento legítimo sem expor conteúdo fora dessa permissão.
ACL-C1 A reserva a eliminação do projeto inteiro ao dono; editores continuam a
editar/remover media. A autorização de leitura da sala não é autorização para
administrar o projeto ou mutar recursos HTTP.

### Canal interno → projects

Rota interna especificada: `POST /internal/ws/projects/:projectId/authorize`.
Disponível apenas ao serviço autorizado segundo WS-C1, sem encaminhamento público
que transforme dados do browser em identidade interna confiável.

O pedido agrupa **um projeto**, com um `requestId` e uma lista de avaliações.
Cada avaliação contém uma referência opaca gerada no WS, a geração da pertença,
sequência da consulta, sujeito/expiração comprovados no canal escolhido e um único
contexto de acesso apresentado. Referências não são credenciais nem bilhetes.

Projects carrega o estado do projeto para o lote e avalia cada membro/contexto:
propriedade compara sujeito com o dono real; partilha verifica associação ao
projeto, estado revogado e permissão; LINK-C1 A não introduz expiry dos links
nesta entrega. A validade do JWT e o prazo local continuam obrigatórios. Um link inválido de um membro não deve conceder ou negar automaticamente
as avaliações dos restantes. Uma decisão deve refletir a leitura atual do estado;
não consultar cache/replica desatualizada como se fornecesse a autorização atual.

Resposta proposta: `{ requestId, projectId, projectVersion, decisions: [...] }`.
Cada elemento identifica a avaliação e devolve `allow`, `deny` ou `unavailable`,
a permissão e validade quando aplicáveis. Não devolver listas de links secretos,
dados do projeto, originais ou JWT. `projectVersion` é auxiliar de consistência e
observabilidade; não substitui os controlos de geração, prazo e ordem.

| Resultado | Tratamento no WS |
|-----------|------------------|
| Serviço não autenticado/autorizado | Recusar no canal/rota; nunca avaliar o sujeito como confiável. |
| Pedido malformado | Erro de contrato; nenhuma nova autorização. |
| Resposta válida com `allow` individual | Só aplicar se pertença, geração, sequência e prazo ainda corresponderem. |
| `deny` individual | Invalidar a via; se não subsistir autorização efetiva válida, retirar imediatamente a sala afetada. |
| Falha da consulta, timeout ou resultado individual ausente/inválido | Não renovar o contexto afetado; nova entrada recusada temporariamente; pertença existente só até ao prazo anterior. |
| Resposta parcial | Tratar individualmente apenas os resultados completos e corretamente correlacionados; ausência nunca significa autorização nem negação definitiva. |

O envelope HTTP bem sucedido não autoriza todo o lote. Uma falha da BD deve ser
indisponibilidade, sem converter desconhecimento em confirmação de posse ou
revogação. Os códigos HTTP internos concretos ficam ligados ao transporte escolhido;
a classificação observável acima deve manter-se distinta.

### Estado local, prazo e respostas fora de ordem

Manter estado por ligação, projeto e contexto apresentado. Para cada avaliação,
registar geração da pertença, sequência e instante monotónico de início da consulta.
Um resultado só se aplica à geração viva e à consulta ainda elegível. Cancelamento,
timeout, saída ou desligação invalidam o resultado pendente, mesmo se chegar depois.
Uma resposta positiva antiga não substitui uma negação mais recente nem uma nova
ligação. Resultados de outros membros, projetos ou contextos não são intercambiáveis.

Para cada contexto positivo, calcular o limite usando o início da respetiva
consulta e a validade efetiva do JWT/permissão. Nunca usar a receção da resposta
para iniciar mais 5 s. Na combinação de vias, acesso ao projeto subsiste enquanto
existir uma via efetivamente válida; expirar uma via não antecipa o fim de outra.
Expirar o JWT termina toda a ligação independentemente das vias.

Consultar o prazo antes de efetivar um join e antes de emitir conteúdo protegido
ao membro; não depender apenas de um timer que pode executar tarde. Ao retirar a
pertença por falta de revalidação, nova entrada requer nova consulta. Capturar relógios
e desvios no manifesto; definir conversão conservadora das expirações absolutas
para o controlo local de duração antes de implementar a contagem temporal.

Revogação entre leitura e join é um caso em corrida, separado de consultas
iniciadas após confirmação da revogação. O desenho não promete atomicidade
distribuída entre MongoDB e Socket.IO. Tem de demonstrar o limite de corte de 5 s,
sem estender uma leitura anterior nem aceitar respostas obsoletas para o contornar.

### Lotes, timeout e agendamento — WS-C2 A validada; detalhes propostos

Adotar timeout **total** inicial de 1 s, incluindo espera, ligação, envio e leitura
da resposta. O WS não prolonga a validade por falhas ou tentativas adicionais. No máximo
50 avaliações membro/contexto por pedido; um membro com duas vias consome duas
avaliações. Projetos maiores são divididos em lotes, sem limitar participantes a 50.

Os valores são parâmetros iniciais configuráveis, validados individualmente e
sujeitos a medição, não capacidade demonstrada nem limites impostos pelos docentes.
Projetos maiores usam vários lotes, **com concorrência limitada e agendamento justo**.
Um ciclo inicial de 1 s exige medir
a cadência efetiva, duração do ciclo e atrasos: não basta configurar `setInterval`.
Evitar acumular ciclos repetidos para o mesmo contexto e impedir que um projeto
grande ocupe todo o agendamento. Não sobrepor avaliações do mesmo contexto sem
invalidar e correlacionar as anteriores. Novos joins também precisam de orçamento
de execução, sem usar os resultados de revalidação como autorização de entrada.

WS-C3 A fixa inicialmente **4 consultas HTTP globais** para joins/revalidações,
**1 por projeto**, com alternância de lotes entre projetos, e **64 KiB por corpo JSON**
de pedido/resposta. São parâmetros configuráveis, não capacidade demonstrada.
WS-C4 A acrescenta inicialmente **16 lotes pendentes** por processo WS, até
**1 pendente por projeto**; estado guardado por contexto e corpus final ainda
precisam de dimensionamento. Não se declara capacidade ilimitada:
se os lotes não forem processados a tempo, o prazo existente expira e o resultado
de disponibilidade/carga é reportado, sem abrir acesso para esconder a falha.
Agrupar reduz pedidos HTTP; CPU/trabalho de autorização continuam a depender das
avaliações individuais. Medir também leituras e latência da BD por lote.

**Relógio e fila:** o timeout total de 1 s inclui a espera desde a aceitação do
pedido de autorização. Iniciar HTTP, estabelecer outra ligação ou tentar de novo
não reinicia o prazo da mesma operação. A fila tem limite inicial de 16 lotes pendentes,
até 1 pendente por projeto, além dos 4 ativos. Um novo plano pendente do mesmo
projeto substitui o anterior no mesmo slot, preservando instante original/deadline
e concluindo explicitamente callbacks substituídos, sem negar outros contextos.
Remover expirados e cancelar/inutilizar avaliações obsoletas; ver WS-C4 no contrato
operacional para tratamento dos joins e cursores. Coalescer ciclos do mesmo contexto sem renovar o instante
de entrada ou acumular trabalho equivalente. Ao encher ou expirar, registar a causa
e recusar temporariamente novas entradas; membros existentes só conservam a última
autorização até ao prazo já fixado. Só uma nova decisão positiva atual e elegível
pode renovar uma autorização; falhas/tentativas não o fazem.

**Bytes e lotes:** 64 KiB = **65 536 bytes** do corpo JSON serializado em UTF-8,
incluindo o envelope; não é contagem de caracteres, cabeçalhos ou tráfego TLS.
Aplicar conjuntamente até 50 avaliações e até 64 KiB: dividir o lote antes de
ultrapassar qualquer limite. Uma avaliação que não caiba sozinha deve ser recusada
explicitamente. Excesso recebido deve ter erro/métrica próprios, nunca truncagem
silenciosa. Resposta oversized/truncada não pode conceder autorização a partir de
um prefixo; mantém-se a regra de falha sem renovação. Testar exatamente o limite,
um byte acima e texto multibyte. A resposta tem de caber no seu próprio limite.

**Capacidade: correção da conta proposta.** Concorrência 4 não significa um máximo
fixo de 4 consultas/s. Num modelo ideal, o débito é aproximadamente `4 / L`, com
`L` a duração média ocupada por consulta em segundos, condicionado por projetos,
cadência, fila e outros recursos. `L=0,1 s` permitiria teoricamente cerca de 40/s;
não é uma medição. Cerca de 4/s corresponde à hipótese de ocupação próxima de 1 s;
se todas as consultas esgotarem o timeout, pode haver **zero revalidações positivas**.
20 consultas/5 s é apenas uma estimativa nessa hipótese, não capacidade garantida
de 20 projetos. O timeout já inclui fila, e cada projeto pode precisar de vários
lotes. Não registar 20 como limite conhecido nem afirmar que abaixo dele os prazos
estão garantidos. Recolher espera, ocupação, recusas, cadência e corte por cenário.

**Justiça/corpus:** incluir um projeto de **500 membros**, com vários pequenos,
medindo o atraso dos pequenos e quantas revalidações/joins terminam, falham ou
expiram. Incluir carga com mais de 20 projetos ativos — por exemplo 40 como caso
proposto, não como nova capacidade aprovada — e diferentes latências/falhas da
projects. Não confundir alternância entre projetos com justiça entre membros de
um projeto grande; observar ambos. Critério ≤5 s/meta ≤2 s permanecem, sem prova
experimental nem declaração de resultados nesta revisão.

## Verificação antes de declarar o contrato cumprido

Estender os cenários acordados no plano de métricas; os seguintes são propostos
para congelamento antes dos ensaios. Não foram executados para este novo desenho.

| Caso | Asserção | Métricas |
|------|----------|----------|
| WS-T01 | Dono e partilhas read/edit válidas entram; sujeitos/contextos adulterados não entram. | S04/S05/S10/S13 |
| WS-T02 | Projects indisponível/timeout recusa novos joins; recuperação permite nova tentativa autorizada. | S10/S21 |
| WS-T03 | Revogação com ligação ativa cumpre corte ≤5 s; reportar meta ≤2 s. Cobrir conteúdo protegido de projeto emitido em salas de projeto e pessoais, incluindo preview/progresso, sem assumir contexto ausente como autorização. | S12 |
| WS-T04 | Falhas não estendem prazo; resposta positiva após timeout/prazo ou fora de ordem não restaura acesso indevido. | S12/S13 |
| WS-T05 | Revogar entre leitura e join, sair/voltar a entrar, desligar/reconectar e trocar contextos não reutiliza avaliação antiga. | S10–S13 |
| WS-T06 | Negação de uma via preserva outra válida apresentada e outras salas; negar todas retira o acesso efetivo. | S12/S13/F04 |
| WS-T07 | JWT expirado termina ligação; frontend reconecta explicitamente com JWT válido e autoriza novamente todas as salas pretendidas; identidade/projetos anónimos preservados. | S06/F06 |
| WS-T08 | Lote com membros/contextos mistos não partilha decisões; resposta incompleta, duplicada ou trocada nunca concede acesso por omissão. | S10/S13 |
| WS-T09 | Certificado de outro serviço da mesma CA, operação fora do par permitido, cabeçalho forjado e acesso direto são recusados; verificar no WS a associação entre JWT e identidade/expiração/contextos delegados. Projects decide com base nessa delegação confiada, sem prova independente do JWT original. | S02/S08/S10 |
| WS-T10 | Variar projetos/membros/contextos, latências e lotes; incluir 500 membros num projeto + vários pequenos e mais de 20 projetos ativos; medir justiça/espera, recusas/timeout de fila, 4 ativos +16 pendentes/17.º recusado, substituições sem reiniciar deadline/callbacks concluídos, limites conjuntos 50/64 KiB, HTTP/s, avaliações/s, cadência, CPU/RSS, BD e impacto nos pedidos leves. | S12/S21/F07/F09 |

Distinguir corte/última emissão no servidor de chegada de pacotes já em trânsito.
Registar razões e tempos com referências de ensaio sem guardar JWT, chaves ou
shareIds secretos nos logs/artefactos. O endpoint/agrupamento novo é NA na baseline
literal; o efeito observável de acesso indevido tem comparador na aplicação atual.

## Justificação e documentação técnica

A proposta usa a autoridade existente de projetos/partilhas e evita bilhetes WS.
A alternativa com gateway centraliza a emissão RS256; a direta reduz saltos mas
confia explicitamente no WS como delegado. WS-C1 A e WS-C2 A estão validadas
individualmente, com as condições registadas; o restante contrato continua proposto.
Não se afirma segurança igual em falhas nem raridade de expiração.
Eventos de revogação continuam evolução se a carga ou os critérios o justificarem.

O [Node TLS](https://nodejs.org/api/tls.html#tlscreateserveroptions-secureconnectionlistener)
explica autenticação TLS de clientes; o certificado de serviço não determina
sozinho a posse de um projeto. O [Socket.IO](https://socket.io/docs/v4/emitting-events/#acknowledgements)
suporta callbacks de confirmação de eventos. A
[API de desconexão do cliente](https://socket.io/docs/v4/client-api/#event-disconnect)
explica que uma desconexão iniciada pelo servidor não dispara a reconexão automática.
Referências consultadas em 16/11/2026; não certificam o desenho sem ensaio nas
versões instaladas. Proposta preparada com Codex/Inception, com validação humana
dos pontos já assinalados e sem atribuir aprovação aos restantes.

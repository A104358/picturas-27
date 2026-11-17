# Fase 2 — Sessões, identidade interna, partilhas e contrato WS

**Equipa:** PL2-G4. **Preparado:** 17/11/2026. **Código observado:** `089acc5`.
**Estado:** SESS-C1 A, JWT-C1 A, LINK-C1 A e WS-C5 B selecionadas individualmente
pelo utilizador e confirmadas tecnicamente pelo assistente, em
2026-11-17T11:53:34Z, com as condições abaixo. A fonte é uma recomendação individual
para confirmação técnica; não representa acordo dos quatro, declaração de ensaio,
aprovação integral dos requisitos ou autorização para alterar a aplicação.
Mantêm-se as validações anteriores, ambos os conjuntos de volumes preservados e a
escolha da instalação de desenvolvimento/avaliação ainda pendente.

## Escolhas comunicadas, confirmação técnica e alternativas

| Ponto | Escolha individual tecnicamente confirmada | Alternativa e custo |
|-------|-------------------------------------------|---------------------|
| SESS-C1 A | Transição/reemissão assistidas, mesma identidade, JWT de utilizador 7 dias absolutos e sem refresh automático | B acrescentaria credenciais/sessões persistentes. A exige intervenção administrativa também após expiração futura de anónimo; prova independente e ferramenta/procedimento ensaiado são obrigatórios. |
| JWT-C1 A | Identidade RS256 por pedido até 30 s, limitada pela sessão/contexto/destino/peer; sem armazenamento anti-replay geral | B acrescentaria admissão jti atómica/persistente. A aceita reutilização pelo peer autorizado no mesmo contexto durante validade; não é uso único nem exactly-once. |
| LINK-C1 A / D8 | Links antigos e novos persistem até revogação; `expiresAt` fora desta entrega | B/expiry opcional exigiria schema/UI/política adicionais. A preserva RNF52 e substitui a preferência anterior D8, não a revogação/revalidação. |
| WS-C5 B | Até 512 ligações e 4096 contextos globais por processo; restantes limites/contrato abaixo | A permitiria 1024/8192. B é teto inicial conservador, não capacidade demonstrada; acima dos tetos testar recusa controlada, sem alegar suporte integral. |

**Confiança:** alta na preservação dos links, média na adequação das restantes
escolhas. Limites/TTL não são resultados medidos. Segurança igual, menor esforço
ou capacidade não foram demonstrados. O motivo de B é uma inferência de engenharia.
Prazos de piloto/entrega e as 60 métricas mantêm-se.

## SESS-C1 A — transição e renovação assistidas

### O que foi observado

[users/auth/auth.js](../../users/auth/auth.js) emite HS256 de 7 dias com `id`;
[validateSession](../../frontend/lib/session.ts) recebe o mesmo token na validação,
não uma renovação. O [frontend](../../frontend/lib/mutations/session.ts) faz logout
e cria outro anónimo perante erro. O schema consultado não fornece credencial
independente de recuperação anónima. O inventário é parcial: uma máquina, browsers
por reconciliar, 2 anónimos sem projetos contados num conjunto, nenhum no outro.
Zero projetos observados não autoriza descartar identidades/presets não levantados.

### Procedimento selecionado para implementar/ensaiar, não executado

1. Completar o [inventário](fase2-inventario-sessoes.md) por instalação/browser e
   responsável, incluindo dados/presets a preservar e casos inacessíveis. Guardar
   correspondências reais e evidência de titularidade protegidas fora do Git;
   não pedir JWT/IDs privados na conversa nem testar por reload que crie outro anónimo.
2. Preparar backup verificável e fixtures descartáveis. Isolar segundo a política
   validada, sem apagar volumes. Parar admissão/consumidores e manter o controlo
   sobre perfis antigos antes de substituir o segredo ou executar novo frontend.
3. Renovar HS256 fora do repositório com uma chave aleatória própria da instalação,
   pelo menos 256 bits. Distribuir só a users/api_gateway/ws_gateway nos papéis já
   previstos. Remover confiança no segredo anterior, sem período de aceitação dupla
   do segredo exposto. RS256 e chaves de certificados são materiais distintos.
4. Registados fazem login com credenciais existentes e conservam `_id`, perfil,
   quota e associações. Não criar outra conta, limpar projetos ou reiniciar quota.
5. Para cada anónimo, o administrador confirma a associação por evidência
   independente do JWT antigo/ID declarado e reemite uma credencial nova para a
   **mesma** identidade. O operador local é uma fronteira de confiança explícita:
   não é uma recuperação pública baseada em conhecer um identificador. Sem prova
   suficiente, conservar dados e caso pendente; não emitir nem substituir identidade.
6. Entregar/aplicar a credencial no perfil confirmado por procedimento local
   protegido, sem stdout/logs/Git, screenshots de tokens ou endpoint público de
   impersonação. A ferramenta/procedimento de emissão/importação tem de ser
   implementado e ensaiado; o script de contagens não executa esta função.
7. Verificar antes/depois identidade, projetos/presets, quota, referências/bytes
   e relações de partilha; testar rejeição de JWT antigo e adulterado. Só reabrir
   após migração elegível e condições de manutenção; browser inacessível mantém
   tratamento pendente explícito, não um «sucesso» por omissão.

### Sessões depois da transição

Manter **7 dias absolutos** desde emissão, sem prolongamento em validate,
upload ou reconexão. Ao expirar: registado volta a autenticar-se; anónimo usa
reemissão assistida para o mesmo `_id`. Falha de rede não é logout nem invalidação
definitiva: preservar o estado local e permitir nova tentativa. Um token rejeitado/
expirado não pode gerar silenciosamente outra identidade. Criar um novo anónimo
continua possível por ação explícita, sem se apresentar como recuperação do antigo.

Usar tipos/issuer/audience de utilizador próprios da instalação; API e WS são
destinatários previstos do JWT de utilizador. Assinatura/algoritmo/claims são
verificados antes de confiar em `id/sub`; normalizar `sub` para o mesmo `_id`,
sem manter o perfil antigo de validação após a transição. Não enviar HS256 à projects.
Recusar após `exp`, sem tolerância que acrescente acesso para lá desse prazo.

Rotação HS256 posterior a suspeita/exposição segue transição assistida/reautenticação;
nesta entrega não se propõe rotação periódica automática ou um novo refresh token.
A não acrescenta revogação individual de sessões: logout fecha a ligação local e
remove a credencial desse perfil, mas uma cópia do JWT pode continuar válida até
`exp`, salvo retirada global do segredo. Mudança de password não deve ser descrita
como invalidação automática de todos os JWT sem mecanismo que o demonstre.
As permissões de domínio/partilha continuam verificadas independentemente disto.
A necessidade de revogar sessões individualmente justificaria B ou um mecanismo
adicional explícito, com âmbito/esforço revistos; não fingir que mTLS o fornece.
A opção B poderia reduzir intervenção, com credencial de renovação independente,
armazenamento seguro, revogação e proteção contra reutilização a definir antes.

## JWT-C1 A — perfil e fronteiras de identidade interna

- **Emissão:** gateway verifica o JWT do utilizador e emite RS256 por pedido.
  Usar `exp = min(iat + 30 s, exp_da_sessão)`, issuer específico da instalação,
  `aud` igual ao serviço destinatário direto e `sub` derivado da sessão, nunca
  do corpo/cabeçalho externo. `typ` interno distinto do token de utilizador;
  rejeitar algoritmos diferentes dos explicitamente configurados para cada tipo.
- **Contexto:** assinar método, percurso interno canónico após reescrita, contexto
  de partilha apresentado e identificador de pedido. Destino valida a associação
  ao pedido recebido e o peer mTLS especificamente autorizado; não aceitar o token
  num outro serviço/rota/método. Rejeitar cabeçalhos internos vindos do browser.
- **Chaves:** `kid` seleciona apenas um mapa local previamente distribuído; não
  seguir URLs/chaves recebidas num JWT. Privada só no gateway; verificadores só
  públicas. Emissão/retirada planeada em manutenção com manifesto; em exposição,
  retirar logo a chave comprometida e isolar, sem fallback. Não interpretar a
  duração da CA como duração da chave RS256 ou assumir que mTLS a renovou.
- **Chamadas seguintes:** não reenviar um token com `aud=projects` para users/
  storage como se fosse válido nesses destinos. A opção A confia na delegação da
  projects, autenticada pelo seu mTLS e limitada aos pares/ações/contexto de projeto
  de D4, à semelhança da delegação WS já escolhida. Isto acrescenta confiança no
  serviço projects para declarar contexto/identidade nessas operações: não é uma
  prova independente do JWT original nem uma chave RS256 atribuída à projects.
- **Replay em A:** TTL/contexto/peer limitam reutilização, mas não implementam uso
  único. A repetição pelo mesmo peer autorizado no mesmo contexto dentro de `exp`
  não é genericamente impedida. `jti`/requestId sozinho não elimina esse risco.
  Proibir retries automáticos de mutações com resultado ambíguo; quotas, versões,
  pagamentos e resultados precisam dos seus próprios controlos/reconciliação.
  S07 deve separar substituição/replay fora do contexto desse caso residual.
- **B:** requer registo atómico persistente de `jti` admitido por destinatário,
  com validade/limites e falha fechada quando não se possa consultar/gravar.
  Testar duas admissões concorrentes e restart; cache volátil perdida não prova
  rejeição de replay. O custo adicional tem de entrar na estimativa e S21.

O prazo de 30 s é de **admissão da identidade**, não limite de duração de upload,
processamento de vídeo ou tarefa já autorizada. A expiração não autoriza novos
pedidos/salas; os resultados só são recebidos sob a autorização atual do destinatário.
Não abortar/duplicar jobs admitidos só porque expirou o token que autenticou o POST.

**Relógios:** validar `exp/iat` e registar desvios no manifesto. Para deadlines
locais usar relógio monotónico, convertendo a expiração absoluta na admissão e
verificando também a hora UTC; um recuo do relógio não pode alongar o deadline
já calculado. Não aplicar leeway que viole término no `exp` ou os 5 s WS.
Desvio/ordem temporal inválidos recusam admissão e exigem diagnóstico.

Os valores exatos de issuer/audience/typ/percurso serão configuração/documentação
de contrato, não segredos escolhidos pelo cliente. As regras de algoritmo, audiência
e tipos distintos seguem práticas JWT; as durações e a escolha A/B são engenharia.
Fontes: [RFC 8725, secções 3.1/3.9/3.11/3.12](https://www.rfc-editor.org/rfc/rfc8725.html),
[RFC 7519, exp/aud/jti](https://www.rfc-editor.org/rfc/rfc7519.html).

## LINK-C1 A — persistência até revogação

O [PDF anterior](../requirements/doc-ext-requisitos.pdf), RNF52, exige persistência
de partilha entre sessões até revogação explícita. RF53–RF57 contemplam acesso,
gestão, revogação e erro de link, mas não fornecem um TTL numérico. O código atual
tem `createdAt/revoked`, sem `expiresAt`. A indicação D8 de links com expiração foi
uma preferência comunicada. LINK-C1 A substitui-a nesta entrega: não implementar
expiração nem migrar links para uma validade por omissão. RNF52 confirmado na
página 27 do PDF (numeração física do documento).

**Escolha LINK-C1 A:** preservar sem expiry, tanto legados como novos; não inferir
expiração da idade/createdAt, renovar/revogar silenciosamente links, nem ligar a
validade do link à sessão de quem o criou. O visitante continua a precisar de JWT
válido e permissões atuais; ao revogar, aplicam-se HTTP/WS e corte já escolhidos.
Adiar expiração reduz alterações funcionais nesta entrega. Risco residual: link
divulgado mantém a permissão enquanto não for revogado; não o declarar resolvido.

**B:** `expiresAt` opcional, definido conscientemente pelo dono; ausência/null
mantém sem expiry para todos os legados/consumidores anteriores. Sem prazo por
omissão escondido. Exige UI, schema/contrato, critérios de validação de data,
tratamento de erro e teste HTTP/WS/duas vias, com justificação de alteração funcional
face ao RNF52; não alegar aprovação docente ou compatibilidade inequívoca. O dono
sempre conserva revogação antecipada. Expiração não elimina projetos/media.

## WS-C5 B — contrato e tetos iniciais selecionados, por demonstrar

Confirmar tecnicamente o [contrato WS](fase2-contrato-websocket.md) com os
seguintes critérios de implementação/avaliação, sem os declarar executados. Não reabrir consulta por join, revalidação, fila, falha, corte ou JWT
expirado já escolhidos. Não há bilhete WS nem uso do segredo HS256 na projects.

1. Join `{projectId, access:{kind:"owner"}}` ou `{projectId, access:{kind:"share",
   shareId}}`; sujeito/expiração vêm da ligação. Callback explícito joined/denied/
   unavailable/invalid_request/session_expired/rate_limited; nomes são contrato
   selecionado, não mensagens já implementadas. Repetição exige consulta fresca.
2. `POST /internal/ws/projects/:projectId/authorize`, um projeto por lote, com
   requestId e avaliações correlacionadas por ligação/geração/contexto/sequência.
   Resultado individual nunca se transfere a outro membro. Ausente/inválido é
   indisponibilidade, sem concessão/renovação; HTTP 2xx não autoriza todo o lote.
3. Uma resposta só vale para a geração e consulta ainda vivas, dentro de 1 s
   desde admissão original, e conserva o limite de 5 s desde início da consulta
   positiva, nunca além da sessão/permissão. Leave/disconnect/timeout/substituição
   invalidam pendentes; depois de negação mais recente, resposta anterior não
   restaura acesso. Verificar deadline no join **e na emissão protegida**, além
   dos timers. Não reutilizar recuperação automática de salas como autorização.
4. Revogação entre leitura e join pode ocorrer; não prometer transação distribuída
   Mongo/Socket.IO. Uma leitura positiva anterior só subsiste até ao limite já
   fixado; consulta posterior à revogação confirmada não deve conceder acesso.
   Sob duas vias, negar uma não retira outra atualmente válida apresentada.
   A condição de verificar autorização/prazo antes da emissão de conteúdo protegido
   abrange também **salas pessoais**: o código envia preview/progresso para
   `io.to(user)`, não apenas `project:<id>`. O produtor/WS precisam de contexto de
   projeto suficiente para autorizar cada destinatário; preview atual nem sempre
   o transporta. Não tratar ter JWT/sala pessoal como permissão para todo o projeto,
   nem parar/duplicar o job só por perder autorização de receção. Contrato de eventos,
   migração dos payloads e testes devem cobrir esse percurso, sem inventar uma
   permissão de receção independente. Fonte: [WS](../../wsGateway/index.js) e
   [mensagens da projects](../../projects/utils/project_msg.js). A observação é
   estática; a implementação e a asserção de corte ainda precisam de prova.
5. **Estado B escolhido:** até **512 ligações** e **4096 contextos globais** por
   processo, 32 salas por ligação e 4 vias por sala. A (1024/8192) não foi escolhida.
   Contar também slots reservados a admissões pendentes, não só salas confirmadas.
   Contextos repetidos não multiplicam estado. Negação/timeout/saída libertam o
   que lhes corresponde; ao atingir limite, recusar explicitamente, sem expulsar
   outra autorização válida ou remover limites para fazer passar o ensaio.
6. **Taxa inicial escolhida:** 5 joins/s por sujeito, burst 10 partilhado pelas suas
   ligações, e 100/s por processo, burst 200. Token buckets monotónicos; excesso
   recusa antes da fila de autorização, sem «retry» escondido. Conservar buckets
   após disconnect até reencherem (até 2 s), para reconexão não reiniciar crédito;
   limitar a 2048 entradas, sem expulsar buckets ativos para contornar o limite.
   Falta de espaço recusa nova admissão, não cria mapa ilimitado.
7. Join de controlo até 4 KiB de JSON UTF-8; token/handshake até 8 KiB;
   limite inicial escolhido de mensagem recebida do transporte 64 KiB, separado dos 64 KiB de cada
   corpo HTTP interno. Não limitar silenciosamente eventos de saída de projeto
   nem truncar payloads. Provar que os formatos legítimos cabem e rejeitar excesso.

O limitador de joins não bloqueia leave/disconnect, expiração, remoção por negação
ou revalidações já devidas. Libertar reservas também em falha/timeout de autenticação
antes de uma ligação ser aceite; não depender só do evento disconnect. Recusar JWT
inválido antes de admitir salas. Estes controlos concretizam as condições já
validadas; não substituir autenticação/revalidação por contagem de ligações.

Todos os números são **iniciais/configuráveis/por medir**, não capacidade para
512 utilizadores nem garantia contra qualquer DoS. Saturação preserva os limites
de autorização anteriores: não renova, não entra, não adia expiração. Os tetos
não tornam automaticamente todo o RSS Node/Socket.IO limitado. Medir mapas,
callbacks, buffers, filas e justiça, incluindo projeto de 500 membros e pequenos.

Socket.IO documenta middleware por ligação e limites de mensagens; não substituem
revalidação/permissões/timers definidos pela aplicação. Fonte:
[Socket.IO middlewares](https://socket.io/docs/v4/middlewares/),
[opções do servidor](https://socket.io/docs/v4/server-options/).

## Cenários lógicos D10/segurança v1 — fixados para avaliação

D10 concretiza o âmbito D1/PKI-C5 no host **e** contentor não confiável da rede de
ensaio, sem credenciais privilegiadas. Separar rede/TLS/identidade/domínio e usar
controlo positivo/estado/bytes; erro 500 ou serviço ausente não comprova proteção.
Estes são cenários lógicos v1 fixados nesta revisão, não execuções. O congelamento
da campanha física ainda exige instalação, hardware/digests, dados/artefactos,
instrumentos e disponibilidade, sem escolher nenhum conjunto retido como fixture.

| Caso | Classe e dados de ensaio fixados | Asserção / limite da conclusão |
|------|----------------------------------|-------------------------------|
| SEC-01 | Registado e anónimo, associação administrativa independente válida/incerta e perfil inacessível; transição e futura expiração | Mesmo ID/projetos/presets/quota nos casos elegíveis; JWT antigo recusado; sem prova, pendente/dados preservados; não criar outro anónimo por erro. Procedimento de emissão/importação implementado e ensaiado, não só descrito. |
| SEC-02 | JWT de utilizador válido/expirado, erro de rede, logout e mudança de password; relógio de teste isolado | 7 dias absolutos, não refresh; reconexão/receção expiram conforme decisão. Registar limitação de cópia de bearer válida até exp, sem inventar revogação individual. Nunca alterar relógio real ou perfis retidos para o ensaio. |
| SEC-03 | RS256 correto e alg/issuer/aud/tipo/rota/método/peer/sub adulterados; igualdade/ultrapassagem de exp e requisição longa já admitida | Recusar substituição/uso fora do contexto e depois de exp; observar separadamente repetição no mesmo contexto autorizado durante validade, permitida por JWT-C1 A. jti sem estado não é uso único; não abortar/duplicar job legitimamente admitido porque passaram 30 s. |
| SEC-04 | Links legados/novos, read/edit/dono, logout/login, revogação e duas vias legítimas | Sem expiresAt nem migração temporal; persistência RNF52 e revogação HTTP/WS; negar uma via não elimina outra válida. |
| WS-N1 | Carga normal de referência: 50 ligações/sujeitos, 10 projetos com 5 membros, 1 contexto por membro | Pré-carga gradual e steady-state; medir cadência/latência/CPU/RSS/BD e corte ≤5 s/meta ≤2 s. Dentro dos tetos, sem alegar antecipadamente taxa de sucesso/capacidade demonstrada. |
| WS-J1 | Justiça sob stress: 500 membros num projeto e 2 projetos pequenos com 5 cada = 510 ligações/contextos | Cabe nos tetos de B; medir espera/corte dos pequenos e cursor de membros. Não contar interrupções por atraso como recusa por cap excedido; registar falha de disponibilidade/cadência se ocorrer. |
| WS-P1 | Muitos projetos: 40 projetos ×5 membros = 200 ligações/contextos | Mais de 20 projetos sem exceder B; não existe limite de capacidade demonstrado de 20. Medir distribuição/recusas e separar causa de rejeição. |
| WS-L1 | 512 ligações admitidas/reservadas; tentativa de 513.ª com credencial válida | Excesso avalia **recusa controlada**, não 513 suportadas. Conservar autorizações existentes até os seus prazos, sem expulso indevido, filas ocultas ou renovação em falha. |
| WS-L2 | 512 ligações com 8 salas/vias válidas distintas cada =4096 contextos; tentar 4097.º contexto sem exceder 32 salas/4 vias | Confirmar ocupação viva+reservas no instante da tentativa; recusar excesso e medir memória/limpeza. Se contextos expiraram e a pré-condição não existe, não chamar ao teste de teto um sucesso; registar preparação/capacidade inconclusiva ou falha. |
| WS-L3 | Teto por ligação/sala, 32→33 salas e 4→5 vias; contexto repetido e várias ligações do mesmo sujeito | Recusa específica, sem duplicar estado de contexto igual nem perder outras autorizações; libertar em deny/leave/timeout/disconnect/handshake falhado. |
| WS-R1 | Taxas no limite/+1, bursts 10/sujeito e 200/processo, reconexão e mapa de 2048 buckets | Excessos recebem recusa explícita; não recomeçar crédito por reconexão nem bloquear remoções/revalidações. Não contar cada tentativa rate-limited como HTTP autorizado. |
| WS-B1 | 4 KiB join, 8 KiB token/handshake, 64 KiB mensagem recebida e 64 KiB corpo HTTP interno, UTF-8/limite/+1 | Aplicar a cada entrada correta, distinguir envelope/transporte/schema e nunca truncar eventos legítimos de saída. Formato inválido não é controlo positivo só porque cabe em bytes. |
| WS-E1 | Resposta atrasada/fora de ordem, leave/rejoin, revogação entre leitura e join, contexto ausente e eventos em salas pessoais/project rooms | Corte/expiração em toda emissão protegida de projeto, incluindo preview/progresso; outra via válida preservada. Contrato e implementação do contexto de eventos ainda precisam de teste. |

Pré-carga de N1/J1/P1 gradual, aguardando resultados e sem confundir flood de joins
com desempenho de revalidação: limite instrumental inicial 5 pedidos/s do gerador,
sem ultrapassar limites individuais. Propor três repetições/janela steady-state de
30 s como instrumento inicial, guardando todas as tentativas/falhas; não são três
sucessos já obtidos ou percentis generalizáveis. O manifesto final fecha instrumento
antes da campanha, sem alterar os tetos para esconder resultados.

**Acima de 512 ligações ou 4096 contextos**, a asserção é recusa controlada e
preservação da autorização existente, não carga integralmente suportada. Se o
corpus acordado exigir mais admissões simultâneas, rever explicitamente A/valores
**antes** de congelar esse corpus; não aumentar em silêncio nem chamar ao excesso
«sucesso de escala». N1/J1/P1 dentro dos tetos também não provam capacidade sem
resultados. Distinguir limite de admissão de falha do backend/revalidação.

Mapeamento nos IDs existentes **S01–S13/S19–S21/F04/F06/F09/F10**, com U24/F05
nos fluxos de quota/billing afetados. S07 separa rejeições indevidas de reutilização
contextual residual de A. Métricas de upload/uso único de D11 não são alteradas por
esta escolha de identidade interna. Os 60 IDs e a necessidade de baseline mantêm-se.

## Para a defesa e o relatório

Razão da seleção A/A/A/B e confirmação técnica: preservar identidades e links conforme o uso local/base,
evitar refresh/recuperação automática geral sem prova, delimitar a confiança de
cada salto e recusar excesso de estado. Custos: intervenção humana anónima, janela
de reutilização contextual da identidade interna em JWT-C1 A, links sem expiry
até revogação e indisponibilidade sob limites. São escolhas individuais tecnicamente confirmadas, não ganhos
medidos, segurança equivalente entre opções ou funcionalidades já presentes.

**Por concretizar:** prova administrativa independente de recuperação anónima e
procedimento de emissão/importação ensaiado; manifesto/carga física; implementação
dos controlos/payloads de emissão e prova do corte; terminação por canal, reconciliação,
uploads e revisão integral. Os mecanismos A/A/A/B estão selecionados no âmbito
individual, sem confirmar capacidade, aprovação dos quatro ou construção pronta.
Não foram alterados código, segredo, token, browser, certificados, volumes ou dados;
apenas documentação. Nenhuma migração ou execução destes ensaios foi feita.

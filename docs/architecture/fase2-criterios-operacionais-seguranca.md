# Fase 2 — Critérios operacionais de segurança

**Equipa:** PL2-G4. **Preparado:** 16/11/2026. **Fonte de código:** `3d31003`.
**Estado:** PKI-C4 B, PKI-C5 A e OPS-C1 A validadas individualmente pelo
utilizador, registadas em 2026-11-16T20:33:46Z, com as condições abaixo.
Mantêm-se [WS-C4 A/PKI-C2 B/PKI-C3 A](fase2-fila-ws-e-revogacao.md). A recomendação
inicial PKI-C4 A (15/5 min) foi substituída pela escolha B; não é critério vigente.
Validação de requisitos operacionais, sem acordo atribuído aos outros elementos,
resultados de execução, requisitos completos aprovados ou autorização para código.

## Decisões, alternativas e confiança

| Ponto | Escolha individual validada | Alternativa e custo |
|-------|----------------------------|---------------------|
| PKI-C4 B | Isolamento ≤30 s/meta ≤10 s desde comando; medir substituição sem prazo imposto antes do piloto; marcar piloto e calibrar critério com dados | A propunha 15/5 min para substituição, sem suporte experimental. B evita esse número arbitrário, mas exige marco de recolha e conclusão registada; não pode ficar indefinidamente em aberto. |
| PKI-C5 A | Matriz completa, probes automatizados e browser manual reproduzível; expand_ai_tool → generative-mock é API interna com mTLS, com implementação real contabilizada | B exigia automação integral também do browser, sem reduzir a cobertura. A mantém intervenção manual documentada e todos os canais obrigatórios. |
| OPS-C1 A | Reconciliação administrativa por execução, com ferramenta/procedimento implementado e ensaiado, evidência prévia e correção de quota não reaplicável; sem replay automático | B/recuperação automática fica como evolução futura. A tem esforço real, custo humano e possível indisponibilidade; documento não é capacidade de recuperação. Ack antecipado permanece defeito conhecido. |

**Confiança:** média no desenho/adequação, baixa nos prazos ainda não ensaiados.
Valores escolhidos não demonstram cumprimento; continuam por verificar isolamento,
terminação por canal, integridade e reconciliação. Não há mudança de par QC-06/QC-05.

## PKI-C4 — relógios, falha e cenário de avaliação

- `t_detectado`: instante documentado da observação/declaração do incidente.
- `t_comando`: início aceite do procedimento pelo administrador; nunca reiniciar
  o relógio numa tentativa adicional da mesma operação. Incluir validações e
  esperas internas ao script, sem escolher retroativamente um início favorável.
- `t_isolado`: todos os participantes/canais relevantes deixam de aceitar tráfego
  de aplicação ou trabalho antigo. Bloquear só nginx não prova isolamento perante
  portas publicadas, ligações Docker diretas, sessões existentes ou consumidores.
  Verificar negações por probes externos e internos ao perímetro da instalação.
- `t_reabertura`: primeiro instante elegível para tráfego após manifesto completo,
  retirada da CA antiga, fecho de ligações/retomas e todos os controlos positivos/
  negativos satisfeitos. Uma nova CA no disco não basta.

**B validada:** `t_isolado − t_comando ≤30 s`, meta ≤10 s. A contagem começa
na entrada do procedimento administrativo, antes das validações/esperas internas,
e termina apenas depois de demonstrar corte de **ligações novas, persistentes,
acessos internos e consumidores RabbitMQ**, incluindo publicações/consumos em curso.
Manter probes ativos de ambos os lados do perímetro e uma conexão persistente
prévia por tipo aplicável; não usar o fim de um comando ou bloqueio só do nginx
como substituto desta observação.

Registar consumidores/conexões antes e depois por principal e comprovar que os
workers já em execução deixaram de produzir efeitos. Desligar o broker ou observar
zero consumidores não demonstra, por si, que um worker parou o trabalho local.
No ensaio, incluir um job em curso e sonda correlacionada de novas entregas/efeitos,
com bruto temporal; filas duráveis podem conservar mensagens sem invalidar o corte.

A substituição da CA é **medida sem limite prévio de reabertura**. Registar emissão,
distribuição, reinício, reconciliação quando aplicável e todos os controlos até à
reabertura elegível; não medir apenas geração criptográfica. A máquina/origem de
desenvolvimento e avaliação **ainda não foi escolhida** pelo utilizador. O piloto
não autoriza selecionar ou alterar qualquer dos dois conjuntos preservados.

Medir também `t_comando − t_detectado` e indisponibilidade total; não esconder
tempo humano, mas não inventar escala de prevenção/operador 24 h ou SLA para esse
intervalo. Compromisso inicia isolamento sem esperar pelos trabalhos. O prazo de
30 s escolhido é para o procedimento técnico, não uma promessa desde o compromisso
real, potencialmente desconhecido, nem prova de substituição completa em 30 s.

Se ultrapassar 30 s ou não houver prova de corte de todos os participantes,
reportar **isolamento incompleto/falha do critério**, continuar a ação e nunca
reiniciar a contagem. Falha na substituição/testes mantém a instalação isolada.
Não existe um limite de 15 min vigente nem autorização temporal de reabertura.
Incidente, investigação e reconciliação de trabalhos são cronometrados separadamente;
≤5 s/meta ≤2 s WS e F08 de recuperação isolada têm relógios/cenários distintos.

### Marco do piloto e registo que não pode ficar em aberto

> **Atualização de 21/11 (D-09):** o utilizador substituiu a data fixa por uma regra: o
> piloto corre assim que a PKI, os canais protegidos e o script de isolamento estiverem
> feitos, o mais cedo possível e sempre antes da MF. O manifesto e os registos abaixo
> mantêm-se. Ver [refactor-handoff.md, §2.6](../refactor-handoff.md).

**Data-limite de planeamento fixada nesta revisão:** **23/11/2026 às 18:00,
Europe/Lisbon (2026-11-23T18:00:00Z)**. Reserva os dias seguintes para corrigir e
concluir o relatório antes da entrega de 27/11. É um marco de trabalho, não uma
medição, confirmação de disponibilidade da equipa ou escolha de instalação.

Antes do piloto preencher o manifesto; após o piloto anexar resultados e conclusão:

| Campo obrigatório | Estado nesta revisão |
|-------------------|----------------------|
| Instalação/dataset, responsável e isolamento dos dados de ensaio | Por escolher; preservar picturas e picturas-quality-20261114 |
| Commit, imagens/digests, CPU/RAM/arquitetura, configuração e participantes | Por congelar; versões do Compose não bastam como manifesto executado |
| Carga: projetos/membros/consumidores, filas, uploads/jobs ativos e contexto idle ou emergência | Por fixar; não apresentar ensaio idle como carga real de incidente |
| t_detectado/comando/isolado, provas de conexões novas/persistentes e consumers cortados | NM |
| Durações reais de emissão/distribuição/reinício/testes/reconciliação/reabertura | NM; distinguir substituição técnica de tempo humano e investigação |
| Bruto por tentativa, sucessos/falhas, contagem de repetições e limitações | NM; proposta de instrumento: três tentativas comparáveis, sem omitir falhas |
| Conclusão do piloto, critério empírico contextual e data de registo | Pendente de execução, até ao marco; nunca preencher com 15/5 min por omissão |

Se o piloto terminar antes de 27/11, registar o tempo medido como **critério
empírico de comparação da substituição no cenário documentado**, conforme pedido
pelo utilizador. Reportar cada tentativa e min/mediana/máximo dos sucessos; usar
como referência contextual o máximo observado das execuções válidas comparáveis,
sem o converter em SLA universal ou apagar tentativas falhadas. O valor só passa
a existir com bruto, instalação, carga, n e resultado dos controlos. Se houver
falhas, o critério de conclusão regista-as e a instalação continua isolada até
satisfazer os controlos; não derivar um prazo de sucesso de tentativas incompletas.

Se o marco for perdido, registar em 23/11 o estado/causa e plano revisto explícito,
sem marcar o piloto concluído ou prorrogar silenciosamente. À entrega, sem piloto
válido, o tempo fica NM e a falta de calibração é uma limitação aberta. A ausência
de piloto não dispensa os controlos de isolamento/cobertura para declarar segurança.

## PKI-C5 — matriz de verificação por canal

As linhas já separam os pares/principais conhecidos, incluindo cada worker e
cada BD/backup. Completar rota/operação/versão efetiva por linha; a topologia
interna efetiva do SeaweedFS continua explicitamente por inventariar, sem exclusão.
Registar digest da imagem, versão runtime/bibliotecas, configuração sanitizada,
emissor/SAN/finalidade/fingerprint público, trust store carregado, dados de ensaio,
comandos, bruto e asserção. Não arquivar chaves, passwords, JWT ou URLs assinados.
As linhas são um inventário de prova, não uma afirmação de TLS já existente.

| Canal/principais | Estado atual — inspeção estática | Estado-alvo e controlo positivo | Controlo negativo / prova pendente |
|------------------|---------------------------------|-------------------------------|-----------------------------------|
| api_gateway → projects | HTTPS com verificação do servidor desativada no cliente; autenticação mTLS/RS256 nova não implementada. | mTLS, identidade RS256 D3 e posse/partilha; leitura e mutação legítimas por rota/verbo | Sem certificado, outro serviço da mesma CA, ação fora da matriz, CA antiga; não confundir mTLS com autorização de utilizador |
| api_gateway → users | Cliente HTTPS com verificação desativada; novo controlo por serviço/operação NM. | mTLS e rotas limitadas; login/registo/anónimo e perfil/quota legítimos | Certificado indevido, promoção/consulta alheia e identidade interna forjada; preservar exceções públicas previstas |
| api_gateway → subscriptions | Cliente HTTPS com verificação desativada; identidade específica de cliente por implementar. | mTLS; plano/billing mock legítimos com sujeito autorizado | Alteração de subscrição alheia, par/operação indevidos e CA antiga |
| projects → users | Cliente HTTPS com verificação desativada; quota/refund com lacunas descritas abaixo. | mTLS; perfil, admissão/devolução de quota no contexto permitido | Identidade/ação/titular indevidos; incluir controlo de quota no fluxo real |
| projects → img_storage | HTTP; o agente HTTPS declarado não é usado nestas chamadas. | mTLS; guardar/ler/copiar/remover objeto descartável autorizado | Certificado/par errado e projeto alheio. Hoje usa HTTP; um handshake isolado não valida a operação de storage |
| users → projects | Cliente HTTPS com verificação desativada; URL/porta da limpeza divergem da API atual. | mTLS; limpeza restrita à conta removida, com fixture descartável | Sem identidade users ou limpeza de outro titular. Endereço/porta observados divergem da API atual: não dar o fluxo por funcional |
| ws_gateway → projects | Consulta interna de autorização ainda inexistente; join atual entra sem a consulta prevista. | mTLS direto, delegação verificada/contextual e consulta por join/revalidação | Outro serviço, identidade/contexto adulterados, falhas/CA antiga. Exigir chamada completa e critérios WS já validados |
| expand_ai_tool → generative-mock | GEN_EXPAND_URL HTTP, requests.post e servidor Flask sem TLS; mudança exige implementação real. | API interna com mTLS validada individualmente; autorizar especificamente expand_ai no outpainting e preservar operação legítima. | Outro principal/certificado da mesma CA, CA antiga, nome/finalidade errados; cliente/servidor/terminação e testes entram na estimativa e plano de recuo. |
| Browser → nginx | HTTPS com certificado local; confiança dos perfis/validação real não levantadas. | TLS com servidor validado, origem habitual e fluxos de sessão registada/anónima | CA retirada, expirado/nome errado devem falhar num perfil com confiança controlada. Aceitar manualmente o certificado antigo não é teste positivo de validação |
| nginx → frontend | Upstream HTTP no nginx.conf; TLS por salto não configurado. | TLS validado no salto; página/assets e sessão registada/anónima legítimos, sem introduzir certificado de cliente obrigatório no browser. | Certificado de servidor inválido/antigo/nome errado; hoje os upstreams são HTTP. Verificar as três ligações e fecho do WS persistente |
| nginx → api_gateway | Upstream HTTP no nginx.conf; TLS por salto não configurado. | TLS validado no salto; API pública com JWT/exceções previstas, sem confundir proxy com credencial mTLS de domínio. | Certificado de servidor inválido/antigo/nome errado; hoje os upstreams são HTTP. Verificar as três ligações e fecho do WS persistente |
| nginx → ws_gateway | Upstream HTTP no nginx.conf; TLS por salto não configurado. | TLS validado no salto; polling e upgrade Socket.IO legítimos, sessão válida, autorização de sala e reconexão explícita preservadas. | Certificado de servidor inválido/antigo/nome errado; hoje os upstreams são HTTP. Verificar as três ligações e fecho do WS persistente |
| nginx → SeaweedFS S3 | Upstreams/SDK configurados para HTTP; distinguir S3 9000 e filer 8888. | TLS validado e credenciais/permissões por principal onde aplicável; PUT/GET/HEAD/Range/remoção legítimos e URL pública assinada preservada | TLS inválido/CA antiga, credenciais antigas e acesso a outro objeto/prefixo; hoje HTTP. Distinguir portas S3 e filer; não tratar todas as interfaces como S3 |
| nginx → SeaweedFS filer | Upstreams/SDK configurados para HTTP; distinguir S3 9000 e filer 8888. | TLS validado e credenciais/permissões por principal onde aplicável; PUT/GET/HEAD/Range/remoção legítimos e URL pública assinada preservada | TLS inválido/CA antiga, credenciais antigas e acesso a outro objeto/prefixo; hoje HTTP. Distinguir portas S3 e filer; não tratar todas as interfaces como S3 |
| img_storage → SeaweedFS S3 | Upstreams/SDK configurados para HTTP; distinguir S3 9000 e filer 8888. | TLS validado e credenciais/permissões por principal onde aplicável; PUT/GET/HEAD/Range/remoção legítimos e URL pública assinada preservada | TLS inválido/CA antiga, credenciais antigas e acesso a outro objeto/prefixo; hoje HTTP. Distinguir portas S3 e filer; não tratar todas as interfaces como S3 |
| users → users_mongoDB | Compose/URIs/backup sem TLS configurado; contas/permissões novas por definir/verificar. | TLS de servidor, credencial própria e permissões mínimas; CRUD e fluxo de aplicação legítimos só na BD identificada. | Sem credenciais, outra BD, certificado inválido/nome errado/CA antiga e pool antigo; controlo positivo novo, sem exigir mTLS no cliente de BD. |
| projects → projects_mongoDB | Compose/URIs/backup sem TLS configurado; contas/permissões novas por definir/verificar. | TLS de servidor, credencial própria e permissões mínimas; CRUD e fluxo de aplicação legítimos só na BD identificada. | Sem credenciais, outra BD, certificado inválido/nome errado/CA antiga e pool antigo; controlo positivo novo, sem exigir mTLS no cliente de BD. |
| subscriptions → subscriptions_mongoDB | Compose/URIs/backup sem TLS configurado; contas/permissões novas por definir/verificar. | TLS de servidor, credencial própria e permissões mínimas; CRUD e fluxo de aplicação legítimos só na BD identificada. | Sem credenciais, outra BD, certificado inválido/nome errado/CA antiga e pool antigo; controlo positivo novo, sem exigir mTLS no cliente de BD. |
| mongo-backup → users_mongoDB | Compose/URIs/backup sem TLS configurado; contas/permissões novas por definir/verificar. | TLS de servidor, credencial própria e permissões mínimas; backup de fixture e recuperação verificada do destino identificado. | Sem credenciais, outra BD, certificado inválido/nome errado/CA antiga e pool antigo; controlo positivo novo, sem exigir mTLS no cliente de BD. |
| mongo-backup → projects_mongoDB | Compose/URIs/backup sem TLS configurado; contas/permissões novas por definir/verificar. | TLS de servidor, credencial própria e permissões mínimas; backup de fixture e recuperação verificada do destino identificado. | Sem credenciais, outra BD, certificado inválido/nome errado/CA antiga e pool antigo; controlo positivo novo, sem exigir mTLS no cliente de BD. |
| mongo-backup → subscriptions_mongoDB | Compose/URIs/backup sem TLS configurado; contas/permissões novas por definir/verificar. | TLS de servidor, credencial própria e permissões mínimas; backup de fixture e recuperação verificada do destino identificado. | Sem credenciais, outra BD, certificado inválido/nome errado/CA antiga e pool antigo; controlo positivo novo, sem exigir mTLS no cliente de BD. |
| projects → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| ws_gateway → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| bg_remove_ai_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| binarization_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| video_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| border_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| brightness_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| contrast_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| cut_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| cut_ai_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| people_ai_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| obj_ai_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| resize_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| rotate_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| saturation_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| text_ai_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| upgrade_ai_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| expand_ai_tool → RabbitMQ | Cliente/broker configurados para AMQP, sem TLS na configuração observada; credencial por serviço ainda por implementar. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| watermark_tool_ms → RabbitMQ | Compose aponta ao broker AMQP. Verificado a 21/11: a imagem usa `pika` 1.3.2 (suporta TLS), mas o `message_queue_setup.py` liga sem `ssl_options`; decisão D-07: imagem derivada com patch em `Tools/watermark/`. | TLS com servidor validado e credenciais próprias/privilégios mínimos; publicar/consumir/reconectar apenas nas filas/exchange do principal. | TLS/CA antiga, credencial inválida e fila/ação não permitida recusados; provar fecho da ligação/consumer antigo e novo fluxo legítimo. Sem mTLS obrigatório no broker. |
| administrador → RabbitMQ management | Listeners administrativos publicados e componentes usados por inventariar/fixar; cobertura TLS não demonstrada. | Inventariar os listeners/canais ativos, TLS validado onde há comunicação de rede no âmbito e acesso administrativo restrito | Não deixar um listener plaintext funcional como desvio do canal protegido. Configuração por versão/terminação por fechar; interfaces desativadas precisam de prova de inacessibilidade |
| administrador → SeaweedFS administração | Listeners administrativos publicados e componentes usados por inventariar/fixar; cobertura TLS não demonstrada. | Inventariar os listeners/canais ativos, TLS validado onde há comunicação de rede no âmbito e acesso administrativo restrito | Não deixar um listener plaintext funcional como desvio do canal protegido. Configuração por versão/terminação por fechar; interfaces desativadas precisam de prova de inacessibilidade |
| SeaweedFS componentes internos ↔ componentes efetivamente usados — inventário pendente | Listeners administrativos publicados e componentes usados por inventariar/fixar; cobertura TLS não demonstrada. | Inventariar os listeners/canais ativos, TLS validado onde há comunicação de rede no âmbito e acesso administrativo restrito | Não deixar um listener plaintext funcional como desvio do canal protegido. Configuração por versão/terminação por fechar; interfaces desativadas precisam de prova de inacessibilidade |

**Resultados dos ensaios novos:** NM/não executados; a coluna de estado atual
identifica observações de código/configuração, não testes passados. Não preencher com
zero nem inferir implementação a partir de documentação do fornecedor. Shared
volumes `image_data`/modelos são acesso a ficheiros, não canais TLS: avaliar
permissões/segredos aplicáveis, sem inventar handshake num volume.

Um serviço ausente, erro 5xx ou timeout não demonstra rejeição de uma credencial.
Correlacionar a causa TLS/autorização, ausência do efeito indevido e controlo
positivo na mesma configuração; classificar falha de preparação como inconclusiva.
Conservar o resultado de cada caso obrigatório, incluindo falhas/skips, sem
substituir a matriz por uma percentagem cujo denominador omita canais difíceis.

A matriz distingue APIs internas e canais de dados/broker: a classificação
validada do mock não transforma Mongo/Rabbit/S3 em mTLS obrigatório. Qualquer
canal sem configuração/suporte demonstrado mantém a lacuna aberta e impede declarar
cobertura completa; não aprovar exceção plaintext ou proxy que deixe um salto
de rede desprotegido. Terminação TLS por proxy, se necessária, exige desenho e
medição próprios antes de satisfazer a política por salto.

**Browser manual reproduzível:** usar perfil de teste isolado com confiança
conhecida; registar browser/versão, origem, fingerprint da CA inicial, passos e
resultados. Fazer controlo positivo com a CA/certificado previstos e negativos
CA antiga, expirado e nome errado; verificar também sessão/reconexão legítimas.
**Nunca ultrapassar um aviso de certificado para contar o caso como aprovado.**
Não usar perfis antigos de Luís como fixtures nem instalar/apagar confiança global
nesta revisão documental. Uma nova identidade anónima não equivale a preservação.

**Fontes técnicas e limites:** nginx documenta verificação TLS do upstream; a
configuração atual do projeto não a usa. O código do tag SeaweedFS 4.47 declara
opções HTTPS/certificado S3, mas isso não comprova a configuração das restantes
interfaces ou o binário implantado. Os links pedidos para Mongo 4.4/Rabbit 4.0
redirecionaram para manuais atuais; não servem como prova das versões da campanha.
Fixar/verificar as imagens e os clientes antes da implementação/avaliação.
Fontes primárias: [nginx proxy SSL](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_ssl_verify),
[SeaweedFS 4.47 server](https://github.com/seaweedfs/seaweedfs/blob/4.47/weed/command/server.go),
[MongoDB TLS](https://www.mongodb.com/docs/manual/tutorial/configure-ssl/),
[RabbitMQ TLS](https://www.rabbitmq.com/docs/ssl),
[Requests — validação TLS/certificado de cliente](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification).

## OPS-C1 — recuperação administrativa, sem repetição cega

### Evidência do código e limites

- [Tools/utils/rabbit_mq.py](../../Tools/utils/rabbit_mq.py) usa `auto_ack=True`:
  não há promessa de nova entrega se o processamento morrer depois da entrega.
- [projects/utils/rabbit_mq.js](../../projects/utils/rabbit_mq.js) chama o callback
  e confirma a mensagem sem aguardar a sua conclusão assíncrona. Fila vazia não
  prova que o resultado chegou a commit.
- [Tools/video/video.py](../../Tools/video/video.py) confirma no fim, mas a entrega
  e confirmação de uma resposta não são o commit transacional do resultado/quota.
  Podem existir respostas publicadas antes de uma interrupção/retoma.
- [Project](../../projects/models/project.js), [Process](../../projects/models/process.js)
  e [Result](../../projects/models/result.js) têm tokens/estado de execução, mas não
  demonstram um registo transacional completo de débito/compensação por run.
- O [cancelamento atual](../../projects/routes/projects.js) tenta refund antes da
  atualização versionada e continua após erro de refund. `pendingAdvancedOps`
  recebe `adv_ops`, enquanto a admissão pode debitar `adv_ops + vid_ops`.
  O [refund users](../../users/routes/users.js) atua sobre o dia corrente. Não
  assumir que esta rota já reconcilia vídeo, mudança de dia, editor vs dono ou
  repetição/crash sem duplicar compensações.

São observações estáticas, não novos ensaios. RabbitMQ distingue confirmação da
entrega de processamento e confirmação ao publisher; nenhuma dessas operações,
sozinha, prova commit de domínio. Fonte: [RabbitMQ — acknowledgements](https://www.rabbitmq.com/docs/confirms).

### Procedimento A proposto

1. **Isolar primeiro.** Suspender produtores/consumidores e mutações antes da
   reconciliação; não esperar pelos trabalhos perante compromisso. Preservar
   volumes, fontes, último commit e evidência de filas/execuções. Não fazer purge
   global nem restaurar snapshots por cima de dados posteriores não afetados.
2. **Inventário privado por execução.** Relacionar projeto/token, executor real,
   mensagens, Process/Result, objetos/temporários e quota antes/depois; os IDs reais
   ficam no registo protegido do administrador, fora do Git. Exportar apenas
   referências opacas e agregados. Separar falta de prova de prova de perda.
3. **Classificar antes de corrigir.** Resultado completo confirmado permanece;
   execução incompleta/indeterminada não é promovida a sucesso. Preservar originais
   e último resultado confirmado; outputs parciais ficam fora das leituras/exports.
   Se o serviço comprometido pode ter alterado dados, investigar integridade:
   substituir certificados não demonstra que os dados são fiáveis.
4. **Impedir execução obsoleta antes de reabrir consumidores.** Invalidar a geração
   das execuções interrompidas com controlo de versão; correlacionar e colocar em
   quarentena mensagens/outputs antigos, preservando evidência e trabalho legítimo.
   Provar que a retoma/redelivery não publica resultados ou sobrescreve objetos de
   uma nova execução. Tokens ajudam, mas não substituem prova de isolamento de
   ficheiros, mensagens e commit. Não apagar todas as filas/Process para esconder
   ambiguidades. A ferramenta administrativa concreta ainda precisa de desenho.
5. **Acertar quota com evidência.** Identificar o executor debitado e o dia original,
   custo imagem/vídeo e resultado efetivamente confirmado. Corrigir apenas o valor
   comprovado da execução afetada, com identificador de reconciliação persistente,
   pré-condições, antes/depois e verificação de reaplicação. Uma resposta perdida
   exige reler o estado/registo, não repetir o refund. Sem prova suficiente,
   manter isolamento e o caso pendente; não inventar reembolso nem cobrar outra vez.
   Registar a correção depois de um refund não prova idempotência: o mecanismo
   tem de impedir duplicação mesmo se morrer entre mutação e journal, por exemplo
   associando identificador/efeito na mesma atualização atómica do domínio de quota.
   A concretização é de implementação e exige teste em cada ponto de interrupção;
   não presumir que o endpoint atual ou um ficheiro de log já o resolvem.
6. **Repetição depende do utilizador.** Apenas após classificar/concluir o run antigo
   e reconciliar efeitos, permitir nova tentativa autorizada, com token novo e
   quota conforme a política existente. Não repetir automaticamente uploads,
   mutações, billing ou ferramentas. Não prometer exactly-once nem criar uma
   recuperação automática geral como terceiro RNF nesta entrega.
7. **Reabrir com prova.** Concluir também o procedimento PKI, os testes por canal,
   estado/quota/objetos e exclusão de efeitos antigos. Se algum caso não estiver
   suficientemente contido/reconciliado, manter isolamento; o prazo de demonstração
   não prevalece sobre a evidência de integridade. Registar ações/resultado/limitações.

**B** exigiria mecanismos de idempotência/retoma e evidência adicional em vários
limites de commit. Não é considerado implementado por já existirem tokens ou
reentrega AMQP. A evita esse alargamento, mas tem custo manual e pode prolongar
indisponibilidade; não satisfaz uma promessa de recuperação automática.

### Implementação, ensaio e limite de capacidade declarada

OPS-C1 A **inclui implementar e ensaiar uma ferramenta ou procedimento executável
administrativo** até à entrega de 27/11. Os passos descritos não recuperam dados por
si. Exigir preservação da evidência antes da primeira correção, classificação
explícita de indeterminados e registo persistente da correção de quota que impeça
reaplicação, incluindo crash/resposta perdida. Um caso sem evidência suficiente
continua pendente; reinício dos consumidores não prova sucesso do trabalho.

Sem ferramenta/procedimento ensaiado até à entrega, registar **limitação: recuperação
administrativa não demonstrada**, com casos/efeitos ainda pendentes. Não a listar
como capacidade existente nem marcar o gate satisfeito. Recuperação automática
fica como evolução futura; ack antecipado continua defeito conhecido, sem exigir
uma reescrita geral da mensageria por associação a esta escolha.

### Cenários obrigatórios propostos antes de afirmar preservação

Usar apenas fixtures descartáveis e bruto antes/depois: imagem confirmada cedo e
worker interrompido; vídeo antes de terminar e depois de publicar resposta; resposta
recebida mas commit pendente; débito com envio/HTTP ambíguo; imagem/vídeo/misto;
executor editor distinto do dono; passagem de dia; reaplicação e crash da própria
reconciliação; mensagem tardia após token novo; falha na limpeza de temporários.

Condições propostas: zero fontes/últimos commits perdidos, zero outputs parciais
visíveis, zero commits obsoletos/duplicados e zero débitos/compensações indevidos
**nos casos com estado conhecido da fixture**. Casos reais sem evidência permanecem
pendentes/isolados, não contam como recuperação bem-sucedida. Registar todas as
ações, duração da análise e perdas/ambiguidades observadas, mesmo que herdadas.

## Esforço e plano de recuo — planeamento, não implementação

As horas abaixo são **estimativas iniciais de engenharia/pessoa**, não medições,
aprovação da disponibilidade ou orçamento total do par. Dependem de definir a
terminação TLS, congelar a instalação e dispor do script PKI; confiança baixa.

| Trabalho incluído | Estimativa preliminar | Dependências / saída verificável |
|-------------------|----------------------|----------------------------------|
| mTLS expand_ai → generative-mock | 4–8 h/pessoa | Cliente, servidor ou terminação segura, identidade/operação restritas, Docker/mounts e testes positivo/negativo/outpainting; reestimar após escolher terminação |
| Ferramenta/procedimento de reconciliação e ensaios | 12–24 h/pessoa | Tokens/filas/objetos, executor/dia/quota, journal protegido contra reaplicação e fixtures de crash/ambiguidades; não é replay automático |
| Preparar/executar/documentar piloto PKI | 2–4 h/pessoa | Script PKI e matriz implementados antes; não inclui implementar todas as APIs/TLS/segredos nem investigação de incidente real |

Os restantes canais e o script PKI têm esforço adicional a estimar no plano global;
não somar esta tabela e apresentá-la como estimativa do projeto inteiro. Horas da
equipa continuam desconhecidas. Em 18/11 o utilizador escolheu esta máquina/Luís
como anfitrião de avaliação; a instalação isolada, carga física e budget continuam
propostos no [plano de avaliação](../fase2-plano-avaliacao.md), sem reutilizar por
inferência os volumes retidos ou declarar o piloto PKI executado.

**Recuo:** desenvolver/ensaiar em contexto e dados descartáveis; preservar a baseline
identificada e os volumes retidos. Se o mTLS do mock não passar o controlo de
identidade/fluxo, reverter a alteração experimental, manter isolamento e escolher
outra terminação segura; não declarar entrega protegida voltando ao HTTP, eliminando
outpainting ou aceitando qualquer certificado. Proxy, se escolhido, não pode deixar
um salto de rede sem a proteção exigida. Se a reconciliação falhar, não aplicar novas
correções sobre dados reais: conservar a evidência, caso pendente/isolado e a
limitação registada. Não restaurar CA retirada como rollback nem compensar quota
por tentativas cegas. Uma redução do âmbito exige decisão explícita; não é recuo
implícito autorizado.

## Métricas, relatório e estado de conclusão

Usar os IDs existentes: **S08/S09/S16/S17/S19/S20/S21** para transporte/identidades,
custos e retirada; **U21/U22/U24/F04/F06/F08/F09/F10** onde aplicáveis à quota, limpeza,
manutenção e reprodutibilidade. Os 60 IDs mantêm-se; dimensões/fixtures não são
novos RNF. Não confundir propostas quantitativas com gates já validados.

O relatório deve explicar os relógios, a cobertura de cada principal e as perdas
potenciais do ack atual. A justificação de B/A/A é obter critérios verificáveis
com manutenção e reconciliação administrativa, aceitando custo humano e interrupção;
não uma demonstração de menor esforço, suporte universal ou recuperação automática.

**Por fechar:** instalação/carga e concretização do piloto até 23/11 às 18:00;
configuração/terminação TLS/mTLS e prova por versão/canal; ferramenta/procedimento
ensaiado de reconciliação até à entrega, estado/abuso WS, corpus, sessões/uploads e
revisão integral. B/A/A está validada individualmente, não executada; não confundir
estes detalhes de implementação/medição com uma escolha A/B ainda pendente.
Aplicação, Compose, volumes e credenciais não foram alterados; nenhum novo ensaio
de execução ou commit foi realizado nesta revisão.

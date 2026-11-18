# Fase 2 — Métricas, critérios de aceitação e baseline antes do código

**Equipa:** PL2-G4. **Estado:** especificação proposta para revisão, 16/11/2026.
**Entrega:** 27/11/2026, por correção explícita posterior do utilizador; substitui
20/11 como prazo de planeamento. As diretrizes originais mantêm a data anterior.
**Código observado:** `7d994d8`; os resultados novos declaram
o checkout de aplicação `66bc6f9`. O diff da aplicação deve ser confirmado no manifesto
de cada execução. Nenhum alvo deste plano constitui aprovação presumida da equipa.

Este documento complementa as [ideias 1 e 2](fase2-ideias-1-e-2.md) e o
[catálogo](../memory-bank/intents/001-phase-2-quality-improvements/upgrade-ideas.md).
Define o que recolher para segurança e eficiência dos uploads, incluindo efeitos
colaterais e preservação funcional. As 60 métricas são dimensões de avaliação dos
dois RNF e suas guardas; não são 60 RNF nem autorização para implementar as 19 ideias.

**Preparação da campanha, 18/11:** o utilizador escolheu esta máquina, administrada
pelo Luís, como anfitrião da avaliação. O [plano antes/depois](fase2-plano-avaliacao.md)
detalha instalação isolada proposta, recursos observados, budgets, corpus, cargas,
repetições, relógios e modelos de manifesto/resultado. O host está escolhido;
projeto Compose, volumes de teste/configuração, critérios E e corpus físico ainda
não estão congelados. Ambos os conjuntos retidos continuam preservados. A leitura
de recursos do host não é uma nova medição da aplicação nem conclusão de BF.
A [revisão do plano](fase2-revisao-plano-avaliacao.md) regista EVAL-B1/C1/R1/M1 A
individualmente selecionadas, com calibração antes do congelamento: disco ≥60 GiB,
recursos/cargas e critérios explicitamente enumerados. **U25 passa de D a G**.
Não aprova implicitamente todos os valores das 60 métricas nem demonstra capacidade.

**Acordo do par registado:** QC-06 Segurança — autorização ponta a ponta + QC-05
Eficiência de desempenho — utilização de recursos nos uploads, por instrução
explícita do utilizador em 16/11. Ver [fonte e âmbito do acordo](../memory-bank/intents/001-phase-2-quality-improvements/quality-exploration.md#decision-record--pair-agreement).
O acordo seleciona o par; a revisão das restantes métricas e a prova experimental
mantêm o seu estado anterior.

**Atualização de decisões:** o utilizador validou individualmente D3/JWT (HS256 de
utilizador, RS256 interno), D7 (`owner` opcional/único/coincidente) e D6.1 (JWT válido
obrigatório em Socket.IO). Posteriormente escolheu **D6.2 B + D6.3 A**: consulta à
projects em cada entrada e remoção ativa quando deixar de existir autorização
efetiva. A indisponibilidade da projects recusa temporariamente novas entradas,
com nova tentativa. Validou depois as três opções A: revalidação inicial a cada
1 s, agrupada por projeto com autorização individual/contextual; critério de corte
≤5 s e meta ≤2 s; autorização local no máximo 5 s desde o início da consulta
positiva, limitada pelo JWT/permissão; falhas não renovam, respostas obsoletas não
restauram acesso e negação efetiva retira de imediato. Ao expirar o JWT, terminar a
ligação e exigir reconexão explícita com JWT válido/nova autorização das salas.
Estes critérios estão **validados individualmente e por demonstrar experimentalmente**.
As restantes metas não foram aprovadas por associação. SESS-C1 A/JWT-C1 A/WS-C5 B fecham posteriormente o modelo de sessões/identidade
e a especificação de trabalho WS; prova concreta, ferramentas e outros TTL de
upload/S3 continuam pendentes. A transição preserva identidade
e projetos anónimos e deve ficar definida antes de renovar HS256. O acordo do par
está registado separadamente; não aprova coletivamente todos estes detalhes.
Nenhum bilhete WS faz parte da solução atual.

**Atualização D4/WS-C1/WS-C2:** o utilizador escolheu individualmente mTLS para
autenticação entre serviços, substituindo HTTPS + JWT assimétrico de serviço.
D3 mantém HS256 de utilizador e identidade RS256 emitida pelo gateway. WS-C1 A
valida mTLS direto com autenticação específica/autorizações do WS e delegação da
identidade/expiração verificadas, mantendo a decisão de permissões na projects.
WS-C2 A valida timeout total inicial de 1 s (espera, ligação, envio e leitura) e
até 50 avaliações membro/contexto por pedido, configuráveis e sujeitos a medição.
Projetos maiores têm vários lotes, concorrência limitada e agendamento justo;
falhas/tentativas não prolongam autorizações. O restante contrato continua proposto,
sem testes executados, aprovação dos restantes membros ou autorização para código.

**Cobertura validada para 27/11 — opção A:** mTLS nas APIs internas com identidade
e autorização específicas por serviço/operação; nos restantes canais TLS com
validação do servidor. MongoDB, RabbitMQ e S3 exigem credenciais próprias e
permissões mínimas por serviço onde aplicável. A escolha mantém D3 e as decisões
WS; mTLS universal não é obrigatório. Configuração/suporte por canal continuam por
provar na matriz D4. S08/S09 cobrem mTLS aplicacional; S16/S17 incluem TLS validado,
credenciais e permissões nos dados/broker. Testar certificado inválido/expirado,
identidade de servidor incorreta e controlos positivos por canal; nos canais
sem mTLS não inventar um requisito de certificado de cliente. S19/S20 continuam
a cobrir segredos/rotação. Nenhum teste novo foi executado nesta atualização.

**Validação individual WS-C3/PKI-C1/ACL-C1:** 4 consultas HTTP globais, 1 por
projeto, lotes alternados e 64 KiB (65 536 bytes UTF-8) por corpo JSON; CA por
instalação 365 dias, certificados de serviço 30 dias, renovar com 7 dias restantes;
script local de emissão/renovação executado pelo administrador incluído na entrega,
sem renovação automática em fundo. Eliminar o projeto inteiro passa a ser exclusivo
do dono; editor mantém edição/remoção de media. São escolhas de engenharia e
política, não capacidade ou testes demonstrados. A auditoria Git/build identificou
lacunas atuais; proteções e ensaios continuam por implementar. Não atribuir aprovação
aos outros membros nem alterar as restantes metas por associação.

**Validação individual posterior A/B/A:** WS-C4 fixa 16 lotes pendentes, além de
4 ativos, 1 pendente por projeto; substituir pelo mais recente sem reiniciar prazo
original/remover expirados. PKI-C2 B substitui CRL pela troca da CA e reemissão
completa para retirar confiança. PKI-C3 A mantém isolamento/reinício, incluindo
recusa da CA antiga e testes completos WS → projects e projects → armazenamento.
Renovação normal é distinta. O custo da interrupção está aceite; duração e prazo
operacional não estão demonstrados nem definidos pelo cutoff WS.

## 1. Estados, prioridades e origem dos números

- **P:** métrica principal, necessária para afirmar melhoria do respetivo RNF.
- **G:** guarda, necessária quando o percurso/componente é afetado.
- **D:** diagnóstico adicional, recolher quando útil e suportado pelo instrumento.
- **NM:** não medido; não substituir por zero. **NA:** mecanismo novo, sem equivalente
  literal na base; avaliar o efeito funcional equivalente e a nova conformidade à parte.
- **E:** proposta de engenharia deste plano; justificar pelo orçamento/risco e aprovar
  antes da avaliação final. **F:** valor das fontes, com o seu cenário original.
- **C:** decisão de arquitetura comunicada nos novos documentos; não significa que a
  implementação exista, que o teste passe ou que os quatro membros tenham aprovado.
- **V:** critério/condição explicitamente validado pelo utilizador nesta conversa;
  validação individual, sem acordo dos quatro nem prova experimental presumidos.

Os limites absolutos de 64/32 MiB substituíram a antiga proposta de redução de
50%/75% e estão agora individualmente validados no âmbito U01/U02 de EVAL-M1.
A origem continua a ser engenharia; não combinar os dois critérios nem aprovar
os restantes limiares por associação.
Tempos inferiores a 3 s (MVP) e 1 s (alvo) vêm de `REQ-VID-SUBMIT-008`; a forma de
observar «pós-envio» tem de ficar fixa. As diretrizes não impõem os restantes números.

## 2. O que a baseline já permite dizer

### 2.1. Ambientes separados

| Código | Ambiente e instrumento | Utilização correta |
|--------|-----------------------|--------------------|
| B14 | Ensaios de 14/11, Intel/Linux x86_64; stack de 13 serviços, worker 2 CPU/1 GiB; RSS amostrado a ~50 ms; gerador separado | Evidência histórica e comparação futura só nas mesmas condições; não agregar com B16. |
| B16 | Ensaios entregues de 16/11, Apple M4 Pro/Docker Desktop ARM64; 12 CPU/7,65 GiB na VM; gateway/projects/storage/video limitados a 2 CPU/2 GiB; cliente Node 22 no host | Piloto mais amplo; frontend/subscriptions/IA ausentes; manifesto completo e hashes dos contentores não acompanham os novos JSON. |
| BF | Campanha inicial congelada, ainda por executar/validar após fechar as decisões | Será o comparador formal da medição final. Escolher uma máquina/arquitetura e o mesmo método antes/depois. |

As séries B14 e B16 têm utilidade, mas não demonstram ganho/perda entre máquinas.
Nesta revisão os números foram extraídos dos JSON existentes, sem repetir pedidos
nem arrancar serviços. A stack `picturas-nfr` não apareceu na consulta Docker local;
a configuração temporária antiga de B14 já não existe em `/tmp`.

### 2.2. Uploads B16 — valores extraídos, não metas

O ficheiro tem 14 uploads válidos concluídos (HTTP 204), mais 2 recusas sem token e
1 falha acima do limite free. Conteúdo: MP4/H.264/AAC de 10 s, 720p, preenchido por
caixa `free`; identifica tamanho transferido, não um corpus variado de codecs.

| Cenário | n | Pós-envio cliente: mín./mediana/máx. (ms) | Tempo total: mín./mediana/máx. (ms) |
|---------|---|---------------------------------------------|------------------------------------|
| 10 MiB, primeiro pedido observado | 1 | 1447,4 / 1447,4 / 1447,4 | 1523,3 / 1523,3 / 1523,3 |
| 10 MiB, restantes pedidos observados | 5 | 154,7 / 161,8 / 192,9 | 234,9 / 238,2 / 266,6 |
| 100 MiB, mistura free/premium | 5 | 664,6 / 991,6 / 1319,8 | 1354,8 / 1687,7 / 2107,8 |
| 500 MiB, premium | 3 | 6704,0 / 6923,1 / 7976,6 | 10249,6 / 10525,4 / 11564,2 |

| Cenário | Gateway: pico RSS absoluto / incremento máximo (MiB) | Projects: pico / incremento máximo (MiB) | Storage: pico / incremento máximo (MiB) |
|---------|------------------------------------------------------|-----------------------------------------|----------------------------------------|
| 10 MiB, primeiro pedido | 122,2 / 41,1 | 126,0 / 25,7 | 100,6 / 22,9 |
| 10 MiB, restantes | 283,6 / 30,8 | 355,9 / 20,8 | 303,3 / 20,7 |
| 100 MiB | 483,2 / 366,3 | 355,4 / 171,6 | 328,9 / 163,0 |
| 500 MiB | 2049,6 / 1767,5 | 1114,2 / 758,8 | 1073,7 / 729,1 |

Picos absolutos e incrementos máximos podem pertencer a repetições diferentes.
Não somar máximos independentes como pico simultâneo. O RSS retido após um pedido
faz o incremento do seguinte parecer pequeno: reportar sempre os dois valores.
«Primeiro pedido» não prova cache/modelo/VM completamente frios.

O ensaio free de 500 MiB, já depois de outros pedidos, devolveu 502 e registou
`process_died=true`, `oom_killed=true` no gateway. Não extrapolar que todo o upload
premium de 500 MiB falha: os três premium anteriores passaram. Nos pedidos sem token,
100 MiB e 500 MiB devolveram 401 **depois de transferir o corpo**; o segundo teve
incremento de RSS do gateway de 500,1 MiB.

### 2.3. Segurança B16 — auditar as asserções antes de contar

O JSON original reporta 22 casos negativos e 17 admitidos; o extrato das ideias
usa um subconjunto de 13 e afirma 10. Não usar esses totais como baseline final:

- **G03/G04:** alterações de ferramenta/media verificadas no projeto da vítima.
- **G05/G06/G07/D09:** exposição de perfil ou mudança de perfil observada.
- **W01:** socket sem token recebeu evento com pipeline, evidência de divulgação.
- **G02:** há HTTP 200, mas o teste usa `user_id`, campo ausente da resposta pública.
  O `verify.mjs` tenta confirmar `_id` e bytes, mas o stdout não foi preservado.
- **D06:** a URL foi emitida, mas o teste usa `og_img_key`, também ausente da resposta;
  `bytes match=false` não comprova leitura desse original. B14 tem uma leitura
  verificada por hash, mas deve manter a sua data, ambiente e referência próprios.
- **D05/D07/D08:** os 2xx são observações; verificar projetos/objetos antes e depois
  para comprovar o efeito. D05 usa inicialmente uma conta sem projetos.
- **G08/G09:** subscriptions ausente, resposta 500; resultado **inconclusivo**, não
  bloqueio de autorização nem cancelamento indevido demonstrado.
- **D04:** token `x.payload.x` não é prova de rejeição de um JWT estruturalmente válido
  com assinatura errada. **D10/D11:** credenciais conhecidas/BD sem autenticação são
  controlos de configuração distintos. **Q01:** corrida de quota é cenário separado.

A [auditoria reproduzível](../memory-bank/intents/001-phase-2-quality-improvements/evidence/baseline-audit-2026-11-16.json)
preserva observações e limitações por caso. Não inventa uma percentagem «corrigida».

### 2.4. Outras guardas já observadas

| Cenário | Número existente | Limite da conclusão |
|---------|-------------------|---------------------|
| R0 B16, imagem/brilho | `process-update` 229 ms, 0 `Process` pendentes | Um controlo positivo. |
| R1 B16, border inválido | 201 ao inserir/aplicar; 0 eventos em 30 s; +1 pendente; 1 reinício | Uma janela de erro tratado, não taxa operacional. |
| R2 B16, broker reiniciado | API de gestão volta em 5609 ms; consumidores presentes na primeira amostra +5 s; 4/5 serviços reiniciados | Não dizer «recupera em ≤5 s desde o início»: a origem temporal não é essa. |
| R3 B16, pedido na fila/broker reiniciado | fila 1→0; quota 5→4; +1 pendente; ZIP vazio após 45 s | Uma perda observada; fechar a observação e confirmar estado por projeto na nova campanha. |
| B14, 3×3 vídeos | 9 resultados; lotes 42,665–45,001 s; áudio/codec conferidos em 1 saída/lote | Outro ambiente; não atribuir os tempos ao M4. |
| B14, worker morto/reiniciado | 1 resultado, 1 débito, 0 pendentes; ~26,3 s após reinício | Não cobre broker/orquestrador nem todos os efeitos. |

O [inventário estático recolhido nesta revisão](../memory-bank/intents/001-phase-2-quality-improvements/evidence/static-inventory-2026-11-16.json)
confirmou **32 serviços**, **11 serviços com 13 bindings de portas**, **5 healthchecks**,
**0 limites de memória explícitos no Compose base**, **6 ficheiros de chave privada**
versionados, **5 certificados expirados em 6** e **8 ocorrências** de
`rejectUnauthorized: false` no código de aplicação inspecionado. O catálogo dizia 7
ocorrências; esta contagem tem universo e caminhos guardados, sem divulgar valores secretos.
Configuração de portas não prova, por si só, alcance externo no ambiente de execução.
O diff de aplicação entre `66bc6f9` e `7d994d8` é vazio.

## 3. Contrato de medição comum

1. **Manifesto:** commit/diff, hashes de scripts e dados, SO/CPU/arquitetura, limites
   da VM/contentores, versões Node/nginx/FFmpeg/SeaweedFS, digests das imagens,
   volumes frescos/reutilizados, serviços presentes, tráfego concorrente e instante UTC.
2. **Dados:** 10/100 MiB free+premium; 500 MiB premium; 500 MiB free negativo;
   MP4/MOV/WebM, áudio/sem áudio, metadados iniciais/finais, ficheiro corrompido,
   extensão/tipo falsos, limites de duração/resolução e corpo maior/menor que declarado.
   Os 1024 MiB premium são cobertura de limite opcional separada, não já medida.
3. **Carga:** concorrência 1 como base, 3 uploads premium simultâneos como teste de
   capacidade de ingestão; conta/projeto próprio por pedido. Uma rodada não deve
   reutilizar perfil indevidamente promovido pela vulnerabilidade a corrigir:
   preparar premium por fixture controlada ou pagamento mock legítimo e verificar.
4. **Repetições propostas:** 5 por combinação tamanho/perfil/estado; 3 rodadas a
   concorrência 3; 3 repetições por caso de segurança, com controlos positivos.
   São parâmetros de ensaio E, não amostra populacional. Publicar cada valor,
   mediana e máximo; não anunciar p95/p99 com 3–5 amostras. Para latência de pedidos
   leves usar 100 pares antes/depois se houver intenção de publicar p95 exploratório.
5. **Estado:** separar processo reiniciado (cache/allocator especificados) de serviço
   aquecido; 1 warm-up fixo excluído, mesma sequência antes/depois. Não forçar GC só
   de um lado. Não excluir falhas do denominador; timeout é falha/censura explícita.
6. **Memória:** `VmRSS` antes/depois e `VmHWM` resetado, PID/início do processo, RSS dos
   subprocessos relevantes, `memory.current`/pico/`memory.events` do cgroup, CPU e I/O.
   Verificar se `clear_refs=5` foi autorizado e o PID não mudou. O reset e as leituras
   sequenciais por `docker exec` não são simultâneos. Campos VmRSS/VmHWM têm limitações
   de contabilização; não chamar «pico exato de toda a memória». Amostragem de 50 ms
   complementa, mas também pode perder picos curtos. [Referência do kernel](https://www.kernel.org/doc/html/latest/filesystems/proc.html).
7. **Tempos comparáveis:** `t0` antes do primeiro pedido, `t_send` evento de envio
   cliente, `t_put` resposta do corpo, `t_confirm` início da confirmação, `t_ready`
   resposta de validação final, `t_hash` hash persistido e `t_cleanup` fim da limpeza.
   Na base há uma só resposta; no desenho novo, **pós-envio = t_ready − t_send**,
   incluindo PUT, ida-volta de confirmação e validação. Não comparar o fim do PUT
   novo com a validação completa antiga. `t_complete = max(t_ready,t_hash)` é outra
   métrica obrigatória para mostrar trabalho adiado. O callback de envio do Node
   assinala entrega ao SO, não chegada ao servidor. [Node HTTP](https://nodejs.org/download/release/latest-v24.x/docs/api/http.html).
8. **Segurança:** clientes públicos, host e cliente não confiável na rede Docker;
   resultados por superfície, sem misturar 401/403, falha TLS e porta inacessível.
   Registar tentativas, recusas e efeitos por ID; 500/timeout não é proteção válida.
   Credenciais, JWT, chaves e URLs assinados não entram em logs/artefactos.

## 4. Catálogo de métricas de segurança

Mínimos e metas nesta tabela mantêm o estado por cláusula; **V** identifica
validação individual, incluindo o âmbito enumerado de EVAL-M1. Os restantes
valores propostos não ficam aprovados por associação.
Em particular, S12 tem critério ≤5 s e meta ≤2 s validados individualmente, ainda
por ensaiar. «100%» significa todos os casos da matriz finita acordada, com
estado/payload verificado, não segurança universal.

| ID / prioridade | Métrica, unidade e método | Base disponível | Mínimo / critério (estado na origem) | Meta / origem e estado |
|-----------------|--------------------------|-----------------|----------------------------|-------------------------|
| S01 P | Leituras/escritas indevidas por `owner`, nº; G02–G04, ausência, valor único coincidente, contradição e multivalor; verificar bytes/estado | G03/G04 alteraram o projeto; G02 precisa de asserção corrigida | 0 admissões indevidas; ausência/coincidência legítimas preservadas | 0; E, objetivo de confidencialidade/integridade; regra D7 validada individualmente |
| S02 P | Bypass direto em projects, nº, cabeçalho/JWT/DELETE com projeto não vazio | D02/D03 200; D05 204 em fixture vazia | 0 efeitos indevidos | 0; E |
| S03 P | Signer/storage read/write/delete sem identidade autorizada, nº, HEAD/hash antes/depois | D06 URL emitida, leitura inválida; D07/D08 201; hash B14 separado | 0 emissões/operações indevidas | 0; E |
| S04 P | Eventos recebidos por socket não autorizado, nº, JWT ausente/inválido ou join sem autorização positiva da projects | W01 recebeu TOOL_ADDED | 0 eventos protegidos | 0; E |
| S05 G | Operações legítimas concluídas, nº/total, dono/partilha/workers/previews/export | C00 dono passou; resto NM neste pacote | 100% | 100%; E, evita «segurança» por desligar o produto |
| S06 G | Tokens ausentes/expirados/adulterados/contexto errado, término WS em exp e preservação da identidade, nº/caso | G01 401; restante cobertura a ampliar, nova transição NM | Expiração termina ligação/reconexão válida V; SESS-C1 A C: 7 dias absolutos sem refresh, relogin registado/reemissão anónima assistida; não trocar identidade por erro | 100% dos casos previstos E; futura expiração anónima exige administrador e prova independente. Logout não invalida genericamente cópia do JWT; reportar essa limitação, não falso bloqueio |
| S07 G | Identidade interna com assinatura/alg/iss/aud/sub/tipo/método/percurso/peer/exp incorretos aceite, nº; reutilização contextual medida à parte | NA; base usa cabeçalho sem este perfil; implementação NM | 0 admissões fora do perfil C/E; JWT-C1 A: RS256 por pedido até 30 s/exp da sessão, só admissão; não interromper job autorizado por vencer 30 s | Reutilização pelo peer autorizado no mesmo contexto durante validade é residual aceite em A, não incluída num falso «zero replay». jti sem persistência não é uso único nem exactly-once. Distribuição/rotina de chaves e delegação por par precisam de prova |
| S08 G | Pares/operações mTLS indevidos aceites, nº; CA errada, expirado, SAN/EKU/serviço errado e certificado de outro serviço da mesma CA | mTLS NA; certificados antigos não verificados; escolha D4 V, implementação/testes NM | Só identidades específicas e operações previstas; WS → projects limitado às consultas (V); 0 aceitações indevidas na matriz E | 0 E; PKI-C1 V: CA local 365 dias, serviço 30 dias, renovar a 7 dias; verificar arranque, retorno após >30 dias, emissão limitada pela CA e rejeições; parâmetros não são prova de cumprimento |
| S09 G | Falhas em chamadas de serviço legítimas, nº/total, incluindo quota e billing | NM com PKI nova | 0 | 0; E |
| S10 G | Joins sem permissão atual ou com contexto sub/projeto/perm adulterado admitidos, nº; consulta autenticada à projects por entrada | Consulta autorizadora NA; W01 mostra join sem autorização | 0; em falha/timeout da projects, 0 novas entradas concedidas | 0; E; controlos positivos incluem nova tentativa após recuperação; sem bilhetes WS |
| S11 G | Joins admitidos após revogação confirmada, nº, consultas iniciadas depois do ACK da revogação; capturar pedidos em corrida separadamente | NM com asserções temporais completas | 0 permissões concedidas nas consultas posteriores ao corte confirmado | 0; E; sem janela de validade de bilhete. Corridas entre consulta e join entram em S12/S13 |
| S12 G | Atraso de corte após revogação confirmada, ms; eventos indevidos após limite; prazo local e respostas obsoletas, §4.1 | NM para o novo mecanismo periódico | ≤5 s, local até 5 s desde início da consulta positiva e nunca além do JWT/permissão; falhas não prolongam; negação efetiva retira imediatamente, preservando outras autorizações | ≤2 s; V, critério/meta escolhidos individualmente e ainda por validar experimentalmente; intervalo inicial 1 s sujeito a carga/latência |
| S13 G | Permissões read/edit/revoked/legadas e eliminação de projeto/media, nº/total | DELETE atual aceita edit; novo ACL-C1 NM; links atuais sem expiresAt | ACL-C1 V: só dono elimina projeto, editor mantém media/edição, leitor não elimina; LINK-C1 A C: legados/novos até revogação | 100% política escolhida C/E; testar fixtures e persistência entre sessões. Expiry/schema/UI de partilhas fora da entrega, não implementação concluída nem perdas temporais presumidas |
| S14 G | Mudanças indevidas de perfil/consulta de dados pessoais, nº, G05–G07/D09 | 4 casos reportam efeito/exposição | 0 nos casos abrangidos | 0; E, distinguir hardening de regra nova |
| S15 G | Operações de subscrição legítimas e indevidas, nº/caso | Serviço ausente; G08/G09=500, inconclusivo | 0 indevidas e 100% legítimas | Igual; E; baseline com subscriptions presente |
| S16 G | TLS de servidor inválido aceite, ligações de BD sem credenciais ou a outra BD de serviço admitidas, nº | D11 leitura local sem credenciais; outros Mongo/TLS NM | TLS validado, credenciais próprias e permissões mínimas onde aplicável (opção A V); 0 admissões indevidas E | 0; testar três Mongo e backup legítimo separadamente, sem exigir mTLS nos clientes de BD |
| S17 G | TLS de servidor inválido aceite e operações S3/broker com credenciais ausentes/antigas/privilégios excessivos, nº | D10 credencial conhecida funciona; S3 direto/TLS NM | TLS validado, credenciais próprias e permissões mínimas onde aplicável (opção A V); 0 admissões indevidas E | Menor privilégio demonstrado; testar consumidores/produtores e leituras S3 assinadas legítimas; não basta mudar .env nem exigir mTLS universal |
| S18 D | Portas internas publicadas por interface e alcançáveis por superfície, nº/lista | Original publica serviços; contagem congelar por configuração | Só loopback nas internas, nginx 8080 conforme D5 | Mesmo limite C; remover portas/segmentar é alternativa, não escolha nova |
| S19 G | Segredos/chaves privadas nos ficheiros entregues, contextos/imagens/montagens indevidas e leaks em logs, nº | Auditoria estática: 3 caminhos sintéticos sem ignore, 6 chaves antigas seguidas pelo Git, 7 contextos com COPY amplo sem exclusão demonstrada; imagens NM | Proteção D4/PKI-C1: CA fora Git/build/contentores aplicacionais; chaves por serviço, montagens restritas; 0 novos segredos expostos E | 0 ativos expostos no âmbito E; testar marcadores sintéticos ausentes do Git/contexto/camadas; ignorar não retira chaves já seguidas. WS sem chave RS256 do gateway, projects sem segredo HS256 e serviços sem chave CA |
| S20 G | Retirada de confiança e renovação normal separadas, nº/cenário; fecho de ligações/retomas e uso de nova identidade | NM | PKI-C2 B/PKI-C3 A V: após retirada/reabertura, 0 aceitações da CA antiga e 100% controlos legítimos; aplicação parcial isolada, dois percursos completos e restantes participantes verificados | PKI-C4 B V: isolamento desde comando até corte de novos/persistentes/consumers ≤30 s/meta ≤10 s; falha reportada sem reiniciar relógio. Duração da substituição NM, a calibrar no piloto até 23/11 às 18:00; sem 15/5 min vigentes. Renovação sob mesma CA não revoga por si certificado anterior; não confundir com retirada. Demais cenários E; preservar histórico |
| S21 G | Sobrecarga em pedidos leves, ms pareados; WS por projeto/membro/contexto: HTTP/s, avaliações/s, fila, bytes JSON, espera/ligação/envio/leitura, CPU/RSS, recusas e justiça | NM para novo mTLS/consultas agrupadas; 4 simultâneas não provam 4/s nem limite de 20 projetos | Mediana +≤10 ms E; revalidação inicial 1 s; timeout total 1 s incluindo fila; até 50 avaliações e 64 KiB por corpo; 4 globais/1 por projeto, alternância V; fila inicial de 16 lotes pendentes/1 por projeto V; WS-C5 B C: 512 ligações/4096 contextos com reservas | ≤5 ms E em pedidos leves; parâmetros V configuráveis, não capacidade medida; medir normal 50, justiça 510, 40 projetos/200 ligações, saturação 513/4097 e fila cheia, bytes exatos/+1 e multibyte; sem truncagem/renovação em falha; corte ≤5 s/meta ≤2 s V |
| S22 G | Tokens de upload reutilizados/roubados/expirados aceites, nº, 2 PUT concorrentes | NA | 0; exatamente uma reclamação atómica por token | 0; E; token opaco/URL assinado não asseguram uso único sozinhos |
| S23 G | Metadados/corpo/key/Host manipulados ou TOCTOU aceites, nº, revalidar objeto real | Base valida o ficheiro, não o novo protocolo | 0 objetos inválidos visíveis/acionáveis | 0; E; testar revogação entre emissão e confirmação |
| S24 G | Exposição de dados pending/URLs internas/SSRF de probe, nº | Pending e probe por URL NA | 0 acessos/leaks; destinos internos fixados pelo servidor | 0; E; não passar URLs arbitrários do cliente ao ffprobe |

### 4.1. Protocolo de permanência WS — condições validadas e prova pendente

1. **Estado da decisão:** D6.2 B está reconfirmada; cada entrada consulta projects.
   D6.3 usa inicialmente revalidação a cada 1 s, por projeto, com decisão individual
   por membro e contexto de acesso. Acordar os cenários/fixtures antes da campanha;
   esta especificação não regista um ensaio executado nem aprovação coletiva destes
   detalhes por associação ao acordo do par.
2. **Prazo local:** registar o início `t_inicio` da consulta e o resultado por
   membro/contexto. Uma resposta positiva só autoriza até, no máximo,
   `t_inicio + 5 s`, terminando antes se expirar JWT ou permissão efetiva. Registar
   expirações de cada via apresentada; uma via válida alternativa pode preservar
   acesso. Não usar o momento de receção para reiniciar o prazo. Uma resposta já
   ultrapassada não permite join nem reposição de acesso; falhas/timeout não renovam.
3. **Corte:** definir `t_rev` como confirmação da revogação pelo servidor e
   correlacionar o ACK no cliente de ensaio. Medir tempo até retirar acesso e até
   cessar emissão protegida ao membro afetado. Critério ≤5 s; meta ≤2 s. Registar
   eventos emitidos após o limite e verificar ausência de acesso restaurado por
   respostas antigas. Distinguir emissão no servidor e receção no cliente: pacotes
   já enviados/em trânsito são observados separadamente, com latência e sequência.
   Expiração conhecida do JWT/permissão pode impor corte anterior ao prazo de 5 s.
4. **Falhas/negação:** simular projects indisponível, timeout, recuperação e negação
   explícita da autorização efetiva. Nenhuma falha concede novas entradas. Para
   membros existentes, falhas só conservam a autorização até ao prazo já fixado;
   negação efetiva retira imediatamente o acesso afetado. Registar atrasos de
   execução/remoção e provar preservação de outras autorizações válidas.
5. **Corridas/ordem:** revogar entre consulta e join; atrasar resposta positiva até
   depois do prazo; entregar respostas fora de ordem e uma positiva antiga após
   negação/revogação; sair/voltar a entrar enquanto há consultas pendentes. Não
   aceitar decisões obsoletas que restaurem acesso indevido. O mecanismo concreto
   de ordenação/coordenação permanece proposto. Timeout total inicial 1 s está
   validado individualmente; incluir espera, ligação, envio e leitura.
6. **Lotes/carga:** variar projetos, membros por projeto e contextos por membro.
   Recolher pedidos HTTP/s, verificações individuais/s, tamanho/tempo dos lotes,
   intervalo efetivo e atraso da revalidação, latência/erros/timeout, CPU/RSS da
   projects e ws_gateway, trabalho/latência na BD e impacto nos pedidos leves.
   Comparar com o mesmo workload sem o novo mecanismo. Agrupar reduz pedidos HTTP;
   não elimina crescimento do processamento por membros/contextos. WS-C2/WS-C3 A
   fixam inicialmente até 50 avaliações e 64 KiB por corpo JSON, 4 consultas HTTP
   globais/1 por projeto e alternância de lotes entre projetos. Dividir antes de
   exceder avaliações ou bytes; recusar/registar excesso indivisível, sem truncagem.
   Testar limite exato, +1 byte, UTF-8 multibyte e resposta demasiado grande. Timeout
   total de 1 s inclui fila e não reinicia no envio HTTP. Limitar fila a 16 lotes pendentes/1 por projeto V, além dos 4 ativos;
   manter o plano pendente mais recente sem reiniciar prazo e remover expirados;
   concluir callbacks substituídos, coalescer ciclos sem adiar prazos; fila cheia/espera excessiva
   não concedem novos joins nem renovam autorização. Medir espera por projeto/contexto,
   recusas, cadência e justiça com 1 projeto de 500 membros e vários pequenos, e
   mais de 20 projetos ativos (por exemplo 40, corpus final por fechar). Quatro
   simultâneas não significam máximo 4/s: com ocupação L segundos, 4/L é apenas uma
   aproximação ideal; timeouts podem dar zero renovações. Vinte projetos não são um
   limite demonstrado. Medir distribuição/caudas e corte ≤5 s/meta ≤2 s; falhas e
   tentativas não renovam prazo. Budgets adicionais e capacidade continuam por medir.
7. **JWT/frontend:** testar expiração durante ligação ativa em perfis registados e
   anónimos; terminar a ligação e verificar que o frontend trata explicitamente a
   reconexão, apresenta JWT válido e pede nova autorização de cada sala. Não assumir
   reconexão automática após desconexão pelo servidor. Renovação/transição precisam
   de preservar identidade e projetos anónimos; SESS-C1 A escolhe assistência
   administrativa sem refresh, com prova concreta/emissão-importação ainda pendentes.
8. **Limites e evolução:** não há demonstração de segurança igual entre tolerar uma
   falha até ao prazo e retirar na primeira falha; também não há medição de raridade
   da expiração ativa. Eventos de revogação ficam como evolução, a reconsiderar se
   as consultas criarem carga relevante ou não cumprirem os critérios. Sem resultados,
   não marcar S06/S12/S21/F04/F06 como concluídos.

O [contrato WS proposto](architecture/fase2-contrato-websocket.md) concretiza o
protocolo §4.1 e propõe os casos WS-T01–WS-T10. WS-C1 A, WS-C2 A e WS-C3 A estão validadas
individualmente com as condições acima; o restante contrato continua proposto.
Os parâmetros não contam como capacidade ou conformidade medidas. O
[ciclo/matriz D4](fase2-ideias-1-e-2.md#d4--mtls-entre-serviços-ciclo-de-certificados-e-pares)
orienta S08/S09/S19/S20/F06/F07: testar script manual de emissão/renovação, validade
no arranque/retorno após >30 dias, limite da CA, chave/certificado correspondente,
renovação e retirada da confiança anterior, certificado expirado/outro serviço da
mesma CA, permissões de montagem/leitura e rotação em conexões persistentes.
Observar erros/latência e fluxos legítimos, sem assumir que renovar invalida o antigo
ou que HTTPS já fornece mTLS. Asserções e cobertura dos canais de infraestrutura
ainda precisam de congelamento; nenhum ensaio novo é declarado.

### 4.2. Fila, retirada de confiança e manutenção — validação individual A/B/A

[WS-C4 A/PKI-C2 B/PKI-C3 A](architecture/fase2-fila-ws-e-revogacao.md) estão
validadas individualmente com as condições do utilizador, não executadas. A
recomendação CRL foi substituída: prazos/ensaios de CRL não são gates vigentes.
Mantêm-se os 60 IDs existentes e as restantes propostas no seu estado anterior.

| Decisão | Condições e evidência necessária | Métricas existentes |
|---------|--------------------------------|---------------------|
| WS-C4 A — 16 lotes pendentes, além de 4 ativos, 1 pendente por projeto | Ensaiar 4 ativos +16 pendentes e tentativa de 17.º; substituição pelo mais recente no mesmo slot sem reiniciar prazo, remoção de expirados, cancelamento de obsoletos e callbacks concluídos. Justiça também para membros/projetos não admitidos, 500 membros + pequenos e >20 projetos. Até 1 MiB de JSON pendente não limita memória total. | S10/S12/S21/F07/F09 |
| PKI-C2 B — nova CA para retirar confiança | Reemitir todas as identidades, retirar CA antiga de todos os trust stores e registar aplicação por participante. Após reabertura: 0 aceitações de certificados da CA antiga em ligação nova, conexões persistentes úteis ou retomas antigas; controlo positivo novo. Renovação normal pode manter CA e não revoga por si o certificado anterior. | S08/S09/S19/S20/F06; S16/S17 nos canais afetados |
| PKI-C3 A — manutenção/reinício | Medir deteção→isolamento, aplicação/fecho por participante e duração da interrupção. Testar chamadas completas WS → projects e projects → armazenamento, restantes canais e CA antiga recusada na retirada. Aplicação parcial mantém isolamento. Planeada espera ausência de trabalhos; compromisso isola logo e exige reconciliação. Testar falha/reinício e validade vencida com ligação aberta, preservação de dados/quota/identidade. | S08/S09/S20/F06/F07 |

Não foi validado um prazo operacional PKI; ≤5 s/meta ≤2 s continuam a referir-se
à autorização de salas WS. Nova CA/ficheiros no disco não provam aplicação em todos
os verificadores nem eliminação de sessões antigas. O custo de parar toda a
instalação para retirar um certificado é conhecido; a duração é NM, não «curta»
demonstrada. Ensaios apenas com fixtures/PKI descartáveis; nenhum foi executado.

### 4.3. Critérios operacionais — validação individual B/A/A

[PKI-C4 B/PKI-C5 A/OPS-C1 A](architecture/fase2-criterios-operacionais-seguranca.md)
foram validadas individualmente com condições. Os critérios são escolhas, não
resultados; não aprovam as restantes metas por associação. Mantêm-se os 60 IDs.

| Decisão | Critério, registo e evidência necessários | IDs existentes |
|---------|----------------------------------------|----------------|
| PKI-C4 B | Comando administrativo (incluindo preflight/esperas) → corte demonstrado de ligações novas/persistentes/internas e consumidores RabbitMQ: ≤30 s/meta ≤10 s V, por medir. Sem corte completo, falha/isolamento incompleto e ação continua sem reiniciar relógio. Substituição medida sem 15/5 min impostos; piloto planeado até 23/11/2026 às 18:00 Europe/Lisbon, com instalação/carga/bruto/n/tentativas. Se válido antes de 27/11, tempo observado é critério empírico contextual, não SLA universal. Falha mantém isolamento. | S20/F06/F08/F09/F10 |
| PKI-C5 A | Matriz completa com estado atual/alvo por canal/principal/versão e controlos legítimos/indevidos; probes automatizados e browser manual reproduzível. Perfil de teste com confiança conhecida e sem ultrapassar aviso de certificado para aprovar. API expand_ai → generative-mock com mTLS exige implementação/testes reais; esforço/recuo registados, resultados NM. | S08/S09/S16/S17/S19/S20/S21/F06/F07/F10 |
| OPS-C1 A | Ferramenta/procedimento administrativo implementado e ensaiado até à entrega; evidência antes de corrigir, indeterminados fora de confirmados e correção de quota protegida contra reaplicação/crash. Fixtures imagem/vídeo/débito ambíguo/editor/mudança de dia/mensagem tardia/limpeza. Sem prova suficiente: pendente/isolado. Sem ferramenta/ensaio até 27/11: limitação, não capacidade existente. Recuperação automática futura; ack antecipado defeito conhecido. | U21/U22/U24/F04/F06/F08/F09/F10 |

O manifesto do piloto regista instalação, carga real, tempos por fase e falhas,
com o marco de planeamento acima; não adiar silenciosamente. Se o piloto faltar,
tempo NM/critério por calibrar é limitação explícita. Máximo observado e distribuição
só são registados com bruto e cenário, sem inventar um limite de sucesso a partir
de execuções falhadas. As três tentativas comparáveis são proposta instrumental,
não três sucessos já obtidos nem carga/instalação já acordadas.

Os 30/10 s de isolamento não validam F08 nem redefinem WS ≤5 s/meta ≤2 s.
Documentação e reinício de consumidores não demonstram conclusão correta, quota
ou cobertura TLS. Falta de suporte/ensaio não passa por zero ou por NA sem prova.

### 4.4. Seleção individual A/A/A/B — sessões, replay, links e estado WS

O utilizador recomendou **SESS-C1 A/JWT-C1 A/LINK-C1 A/WS-C5 B** para confirmação;
o assistente confirmou tecnicamente a adequação com as condições registadas no
[contrato e cenários v1](architecture/fase2-sessoes-identidade-partilhas-ws.md).
É seleção individual comunicada/confirmada tecnicamente (**C**), não nova declaração
de acordo dos quatro, execução ou aprovação global de metas. Os 60 IDs mantêm-se.

| Ponto | Escolha, critério e prova necessária | Métricas existentes |
|-------|-------------------------------------|---------------------|
| SESS-C1 A | Transição/reemissão assistida e JWT de utilizador 7 dias absolutos, sem refresh; intervenção administrativa também na futura expiração anónima. Mesmo ID/projetos/presets/quota; prova independente do JWT/ID antigo, ou caso pendente/dados preservados. Emissão/importação implementada/ensaiada, sem segredos em logs/Git. Logout não é revogação individual de cópia de bearer. | S06/S19/S20/F06/F09/F10 |
| JWT-C1 A | RS256 até 30 s/exp da sessão, só admissão, contexto/aud/peer corretos; não limita job/upload já autorizado. Rejeições fora do perfil separadas de reutilização pelo mesmo peer/contexto válido, residual aceite. Sem uso único geral ou exactly-once; não contar jti como registo de utilização. Delegação projects restrita, sem aceitar aud de outro serviço. | S02/S07/S08/S09/S20/S21/F05/F06/F10 |
| LINK-C1 A / D8 | Legados e novos persistem entre sessões até revogação; expiresAt fora da entrega. Testar read/edit/dono, revogação HTTP/WS e duas vias. Não inventar prazo por idade nem eliminar projetos/media. RNF52 confirmado na p.27 do PDF; expiry de URL S3 continua contrato separado. | S01/S05/S11–S13/F04/F06 |
| WS-C5 B | Tetos iniciais por processo 512 ligações/4096 contextos, incluindo reservas, 32 salas/ligação e 4 vias/sala. Taxa/buckets/4–8–64 KiB aplicados nas entradas corretas, sem truncagem de saída. Libertação em erro/timeout/saída; saturação recusa sem remover indevidamente acesso já válido. Acima dos tetos é teste de recusa, não suporte integral. | S04–S06/S10–S13/S21/F04/F06/F09/F10 |

**Cenários lógicos v1 fixados:** normal N1 50 ligações/10 projetos; justiça J1
500+5+5=510 ligações; muitos projetos P1 40×5=200 ligações; limites 512→513 e
4096→4097, mais tetos por sala, taxa, bytes e falhas. A pré-condição de ocupação
viva/reservada deve existir antes do teste do limite. Se o corpus exigir mais
admissões, rever A/tetos explicitamente antes do congelamento físico. Estar abaixo
do teto não prova capacidade: falhas de cadência/corte/BD não são escondidas como
recusa por excesso. Manifesto, instalação e corpus físico continuam por congelar.

Projetos protegidos emitidos por salas pessoais também exigem autorização atual;
preview/progresso não escapam ao corte só por não usarem `project:<id>`. Implementar
contexto/payload e medir; a inspeção estática não prova divulgação em execução.
D10 cobre host/contentor não confiável, separando rede/TLS/identidade/domínio, com
controlos positivos. Todos os novos resultados são NM; sem migração ou ensaio feito.

### 4.5. Recuperação anónima detalhada — prova real desconhecida

O [procedimento de emissão/importação](architecture/fase2-recuperacao-anonima.md)
concretiza SESS-C1 A, sem introduzir refresh/credencial de uso único. O utilizador
declarou desconhecer se existe fonte independente de associação aos browsers.
Registar estado **desconhecido/pending_evidence**, sem marcar «prova ausente»,
«caso elegível» ou «recuperado» por omissão. Não foram consultados browsers/dados.

| Grupo de casos | Evidência e critério antes de afirmar recuperação | IDs existentes |
|----------------|-------------------------------------------------|----------------|
| AR-01–AR-04 | Prova insuficiente impede emissão; aprovação fundamentada preserva mesmo sub/conta/perfil/dados. Conta apagada/registada, conflito, concorrência e crash não geram substituição ou duplicação cega. Template público vazio não aprova caso; artefacto privado/journal separados. | S06/S19/S20/F06/F09/F10 |
| AR-05–AR-08 | Credencial candidata só é gravada após validação no servidor e comparação com caso aprovado; issuer/dataset/sub/tipo errados, old-secret JWT, ficheiro inválido/excessivo e falhas de rede/storage mantêm estado seguro. JWT 7 dias desde emissão, não desde importação. Ficheiro até 16 KiB é proposta instrumental; token/handshake mantém 8 KiB selecionados. | S06/S19/S20/F06/F10 |
| AR-09–AR-12 | Bootstrap suspenso antes de criar/validar/logar sessão antiga; zero registos automáticos no modo recuperação. Tabs/callbacks não sobrescrevem a nova identidade; reconexão explícita e dados/quota preservados. Nenhum bearer/chave nos entregáveis/logs; apagar ficheiro não revoga JWT nem o torna de uso único. | S06/S19/F04/F06/F09/F10/U24 |

Recolher tentativas, estados/causas, igualdade de identidade/dados/quota e tempos
de aprovação/emissão/validação/importação sem segredos. N/durações de execução
continuam NM; não medir segurança real por validar este documento/template. Os 12
casos detalham SEC-01/SEC-02 e os 60 IDs, não acrescentam RNF ou ensaios executados.
Ferramenta/procedimento e testes continuam obrigação da entrega; sem eles, limitação
explícita. Estimativa preliminar de implementação 8–16 h/pessoa, não medida nem
aprovação de recursos/horas da equipa.

## 5. Catálogo de métricas de upload e recursos

Recolher gateway, projects, storage **e** nginx/SeaweedFS. Um valor Node pequeno não
é melhoria se apenas deslocar memória ilimitada, disco ou trabalho para outro serviço.

| ID / prioridade | Métrica, unidade e método | Base disponível | Mínimo / estado por cláusula | Meta / origem e estado |
|-----------------|--------------------------|-----------------|----------------------------|-------------------------|
| U01 P | Pico RSS adicional por serviço Node, MiB, VmHWM/RSS/cgroup e PID | B16 tabela §2.2 | ≤64 MiB em cada serviço, por cenário até 500 MiB | ≤32 MiB; E dos novos documentos; V EVAL-M1 no âmbito enumerado da revisão |
| U02 G | RSS absoluto/retido antes/depois e após hash/trabalho/limpeza normal +10 s sem carga, MiB | RSS pré/pós no JSON; pós-10 s NM | Sem OOM; aumento retido ≤64 MiB face ao estado inicial equivalente | ≤32 MiB; E; reportar casos sem plateau; V EVAL-M1 no âmbito enumerado da revisão |
| U03 G | Pico cgroup e eventos `oom`/`oom_kill` por serviço/VM, bytes/nº | B14 amostras; B16 flag final de OOM no gateway | 0 OOM em uploads válidos/negativos | 0; E; falha não pode passar como baixo RSS; V EVAL-M1 no âmbito enumerado da revisão |
| U04 G | Pico memória nginx/SeaweedFS e agregado simultâneo, MiB | B14 nginx; B16 NM | Incremento ≤128 MiB nginx e ≤256 MiB SeaweedFS a concorrência 1, sem OOM | ≤64/128 MiB; E, calibrar com BF e declarar budget total para concorrência 3; V EVAL-M1 no âmbito enumerado da revisão |
| U05 D | Relação tamanho→memória, MiB/MiB, 10/100/500 com mesmo estado | Pilotos com reutilização, regressão ainda inválida | Diagnóstico, não gate isolado | Inclinação próxima de zero, tolerância a fixar após ruído; E |
| U06 D | CPU user/system e CPU-segundos por upload/serviço, s | B16 NM para upload | Reportar consumo completo até hash | Reduzir/explicar custos; sem meta artificial |
| U07 D | Bytes de rede por fronteira e amplificação total, bytes/byte útil | B16 NM | Reportar até hash e limpeza | Explicar leitura adicional; não esconder custo de hash assíncrono |
| U08 G | Bytes/ficheiros de disco temporário e pico, MiB/nº | NM | Por componente, ≤C×(F+16 MiB), F tamanho do ficheiro e C concorrência; 0 resíduos depois da limpeza | Sem spool integral no caminho nginx/S3; ≤16 MiB por upload de overhead temporário; E, compatibilidade por testar |
| U09 P | Aceitação após envio `t_ready−t_send`, ms, incluindo confirmação | B16 500: 6704–7976,6 ms | <3000 ms para cada amostra válida de 500 MiB | <1000 ms; F do requisito, não medir só PUT; V EVAL-M1 no âmbito enumerado da revisão |
| U10 G | Tempo total `t_ready−t0`, ms e débito útil bytes/s | B16 §2.2 | Mediana ≤1,10× baseline equivalente por cenário | ≤baseline; E, evitar aceleração obtida por mudar origem do relógio; V EVAL-M1 no âmbito enumerado da revisão |
| U11 D | Pedido inicial de autorização/preflight, ms | NA | Referência ≤500 ms; D, sem gate independente | Referência ≤200 ms; E, só se escolhido protocolo novo; gates temporais U09/U10 |
| U12 D | Confirmação/HEAD/ffprobe/Mongo separados, ms | Base não separa etapas; NM | Total respeita U09 | Reportar decomposição, meta por etapa só após BF |
| U13 G | Bytes/ranges/tempo de ffprobe remoto, bytes/nº/ms; moov início/fim e formatos | NM | Valida metadados reais, limites de I/O/timeout definidos | Menos bytes que o ficheiro nos casos seekable; hipótese, não promessa universal |
| U14 G | Tempo até hash completo `t_hash−t_send` e atraso após ready, ms | Base calcula antes da resposta; separado NM | Hash correto; se assíncrono ≤10 s após ready por ficheiro até 500 MiB em C=1/C=3, incluindo fila | ≤5 s; origem E, âmbito precisado e validado individualmente; registar t_complete e custo integral; V EVAL-M1 no âmbito enumerado da revisão |
| U15 G | Integridade SHA-256 do original após upload e processamento, nº/total; outputs transformados seguem F02 | Uploads B16 não verificam todos os bytes; B14 verificações limitadas | 100% originais iguais | 100%; E; ETag não substitui hash multipart; V EVAL-M1 no âmbito enumerado da revisão |
| U16 G | Preview correto antes/depois do hash/cache, nº e trocas entre ficheiros | Base exige og_sha256; novo estado NA | 0 colisões/trocas; 100% resultados corretos | Igual; E; desativar leitura **e escrita** de cache enquanto hash falta; V EVAL-M1 no âmbito enumerado da revisão |
| U17 G | Sucesso válido por tamanho/perfil/formato, nº/total | B16 14/14 nos uploads válidos medidos | 100% dos casos do corpus | 100%; E, não suprimir perfis/formatos existentes |
| U18 G | Rejeição correta de tamanho/duração/codec/tipo/zero/corrupção, nº/caso | Free-500 falhou 502; demais NM neste conjunto | 100% recusados com resposta definida; 0 objetos ready inválidos | 100%; F/E; manter diferenças de erro relevantes |
| U19 G | Recusa sem token antes do corpo e memória/bytes lidos, ms/MiB/bytes | Sem token 500: 401, 3578,7 ms de envio, +500,1 MiB gateway | 401/403, ≤8 MiB adicionais no gateway | ≤100 ms após cabeçalhos; E, usar cliente lento/controlado |
| U20 G | Três uploads premium simultâneos 500 MiB, nº de sucessos/reinícios/tempo | NM | 3/3 sem OOM/reinício, conteúdo íntegro | 3/3 em 3 rodadas; E, medir budget total e recusa de excesso; V EVAL-M1 no âmbito enumerado da revisão |
| U21 G | Recuperação de interrupção de PUT/confirm/hash/serviço, objetos/estados/tempo | Novo protocolo NA; cenários equivalentes BF pendentes | 0 ready inválidos/pendentes sem prazo; erro/repetição definida | Igual; E; não pressupor atomicidade SeaweedFS |
| U22 G | Limpeza após expiração, idade s, nº e bytes órfãos | Baseline de abandono NM | 0 órfãos após TTL +60 s | TTL +10 s; E; TTL em aberto, retenção nunca infinita; V EVAL-M1 no âmbito enumerado da revisão |
| U23 G | Integridade de versão/associação ao projeto após confirmar duas vezes, nº | Base usa versão; novo confirm NA | Um media por upload, sem perdas/duplicados; 409 tratado | Igual; E, confirmação idempotente |
| U24 G | Quota/limites antes/depois de upload e Apply, nº/caso | Upload não reserva operações; Apply cobra por efeito/vídeo | Nenhuma cobrança/reserva nova ou recusa por saldo zero no upload; cálculo Apply preservado | Igual; política UP-C2 A selecionada individualmente; demais cobertura por validar |
| U25 G | Pedidos leves durante upload, ms, erros e throughput | NM; OOM B16 afetou gateway | 0 falhas; mediana ≤1,10× controlo sem carga na mesma campanha, por par | ≤controlo; origem E, V EVAL-M1; 100 pedidos/janela e todas as tentativas/erros preservados |
| U26 G | Uso único/retry/expiry/cleanup após falha de auth_request, nº e códigos | NA | 0 replay/duplo consumo; retry e erro documentados | Igual; E; 401/403/2xx/erro interno distinguidos |

**Âmbito preservado:** U11/U12 continuam D sem gate próprio; a referência de
preflight não é aprovada como mínimo independente. A precisão F02 validada em
EVAL-M1 distingue original íntegro de output transformado, sem aprovar toda a
cobertura funcional. U22 seleciona os prazos relativos, não o TTL. S12/S20 retêm
a validação anterior; demais limiares conservam o estado anterior.

### 5.1. Seleção do primeiro grupo de upload e ciclo por decidir

UP-C1 A/UP-C2 A/UP-C3 A foram selecionadas individualmente com confirmação
técnica: adaptador multipart limitado e seguro antes do corpo, quota só no Apply,
tentativas/staging controlados; validação/autorização final e commit comuns, sem
duplicar upload/débito. Não é prova de compatibilidade, memória ou isolamento.
A política de U24 fica selecionada; outros números não ficam aprovados por isso.

O [ciclo de vida](architecture/fase2-upload-ciclo-vida.md) propõe UP-C4–C9 e
**UL-01–UL-12** para S22–S24/U01–U04/U08–U26/F04/F06/F10, sem novos IDs de
métricas. Token 300 s, tentativa 900 s, corpo 600 s/idle 30 s, limites de vagas,
probe 15 s/2×F+16 MiB, hash 1 ativo, limpeza 5 s e journal 24 h são **propostas
não selecionadas**; não derivam de EVAL-M1. Preservam-se os prazos relativos U22
e U14 já selecionados. Testar CAS do projeto/barreira vs journal/S3 e atualizações
por snapshot: versão isolada não autoriza e uma lease não cancela escritor antigo.
Cópias/candidatos aumentam disco/rede/latência; recalcular piso ≥60 GiB antes de BF.
Nenhum novo ensaio ou suporte SeaweedFS foi demonstrado.

## 6. Guardas funcionais e de implantação

| ID / prioridade | Métrica e método | Base | Mínimo / meta proposta |
|-----------------|-------------------|------|-------------------------|
| F01 G | Testes existentes de orquestração e vídeo, nº e ambiente | B14: 8 Node e 74 vídeo; Whisper simulado | 100% antes/depois no mesmo ambiente; falhas explicadas, não esconder skips |
| F02 G | Efeitos, ordem, MP4/H.264/AAC, duração e áudio, casos imagem/vídeo/misto | B14 controlos; B16 R0 imagem | 100% corpus, comparar pixels/áudio conforme contrato; não exigir MP4 binariamente igual sem necessidade |
| F03 G | Legendas com/sem fala e extração terminal/única/manifests, nº/total | Suites existentes, fala real NM | 100% regras; pelo menos um teste real de fala se percurso de storage afetado; não trocar reconhecimento por mock no relatório |
| F04 G | Partilha, presença, versões, cancelamento, exportação e duas vias de autorização, nº/total; projeto vs media | Inspeção/alguns testes, cobertura ampliada NM; UI de DELETE encontrada na lista do próprio utilizador, sem ensaio renderizado | 100% controlos afetados; preservar outra via legítima e outras salas. ACL-C1 V: dono elimina projeto, editor remove media mas não projeto; verificar/ajustar UI não-dono e limpeza autorizada da conta; mudança de política justificada, sem alegar restrição DELETE inequívoca nos RF |
| F05 G | Fluxo mock subscribe→premium→cancel→free, nº | Subscriptions fora de B16 | 100% antes/depois; criar fixture legítima e nunca usar promoção pública vulnerável como requisito positivo |
| F06 G | Certificados/segredos/init, transição/renovação de sessões e reconexão WS registada/anónima, upgrade de volumes, nº/caso | Certificados expirados documentados; auditoria Git/build disponível, novo script PKI e transição/reconexão NM | Antes de renovar HS256, definir transição; preservar identidade/projetos anónimos e reconexão explícita V. PKI-C1 V: script local na entrega, validar arranque e renovação com ≤7 dias; recuperar >30 dias offline antes de servir, sem emissão além da CA. PKI-C2 B/PKI-C3 A V: nova CA/reemissão completa para retirar confiança, manutenção/reinício e testes de conexões/retomas; PKI-C4 B fixa isolamento 30/10 s; substituição por medir no piloto, configuração por canal e reconciliação administrativa OPS-C1 a implementar/ensaiar; não apagar volumes para corrigir migração |
| F07 D | Overhead de mTLS frio/quente, handshake e pedidos reutilizados, ms | NM | Reportar separadamente; guardas S21/U10 mantidas |
| F08 G | Disponibilidade durante/fim de falha isolada, ms/restarts | B16 OOM sem retoma no intervalo observado | 0 quedas no corpus válido; se supervisor alterado, retoma ≤30 s, alvo ≤10 s E |
| F09 D | Código/configuração afetados, contratos novos e passos operacionais, nº/lista | Inventário atual e listas nos documentos | Reportar extensão/complexidade; sem meta de «menos linhas» |
| F10 G | Reprodutibilidade dos artefactos, nº de execuções repetíveis/previstas | Scripts/JSON B16 presentes, manifesto incompleto | 100% dos gates com comando, dados/hashes, ambiente, bruto e análise; 0 segredos nos entregáveis |

## 7. Matriz de cenários e critérios de saída

Para F06, o [inventário de sessões](architecture/fase2-inventario-sessoes.md) prepara
as fixtures de preservação por instalação/browser/identidade/projeto. O utilizador
confirmou uso apenas local pela equipa, sem instalação partilhada nem utilizadores
externos. Essa declaração define o âmbito. Luís confirmou responsabilidade nesta
máquina e preservação de ambos os conjuntos. Após os metadados Docker (13
contentores parados/14 volumes), foram recolhidas contagens em cópias isoladas:
`picturas` tem 4 contas/2 projetos (2 contas anónimas, 0 projetos de anónimos) e a
experiência de 14/11 tem 13 contas gratuitas/10 projetos. Os hashes dos quatro
volumes originais mantiveram-se iguais; cópias/contentores temporários removidos.
Isto fornece fixtures agregadas de inventário, não resultados da migração ou
cumprimento de F06. Browsers/associações, outros computadores e ensaios de transição
continuam pendentes. Em 18/11 o utilizador escolheu esta máquina/Luís como host de
avaliação; configuração/instalação experimental e eventual fonte de desenvolvimento
continuam por definir, sem escolher nenhum dos conjuntos retidos como fixture.
Não confundir contagem de contas anónimas com sessões ativas nem recarregar o frontend como
observação neutra, dado o comportamento atual de substituição da identidade em erro.

| Grupo | Cenários a congelar | Métricas |
|-------|---------------------|----------|
| AUTH-PUBLIC | G01–G07, dono/outro, owner conflitante, partilha read/edit/revoked; perfil e billing separados | S01, S05–S07, S13–S15, S21 |
| AUTH-INTERNAL | Mesmo ataque do host e de contentor não confiável; direct projects/storage/users/subscriptions; Mongo/S3/broker | S02–S03, S08–S09, S14–S20 |
| AUTH-WS | JWT ausente/inválido/expirado em ligação ativa e reconexão explícita; consulta por join; revalidação inicial 1 s por projeto/membro/contexto; indisponibilidade/timeout/recuperação; revogação, respostas tardias/fora de ordem, corrida e acesso alternativo válido; §4.1 | S04–S06, S10–S13, S21, F04/F06 |
| UPLOAD-NORMAL | 10/100/500 MiB, perfis certos, MP4/MOV/WebM, moov início/fim | U01–U18, U23–U24 |
| UPLOAD-NEGATIVE | Ausência de auth, token/boundary/corpo inválidos, limite, replay/race e alteração de permissão | S22–S24, U18–U19, U21–U24, U26 |
| UPLOAD-LOAD | Concorrência 1/3, pedidos leves concorrentes; hash e cleanup incluídos | U01–U10, U14, U20, U25 |
| REGRESSION | Imagem/vídeo/misto, previews, legendas, extração, partilha, subscrição e implantação | F01–F10 |

**Antes de código de aplicação:**

- [ ] Registar as escolhas finais ainda abertas, incluindo compatibilidade da API,
  persistência/revogação de links (expiry adiado por LINK-C1 A), hash pendente,
  validade/revogação de tokens de upload e estado atómico do token.
- [x] Registar o acordo do par QC-06 + QC-05, comunicado pelo utilizador para PL2-G4;
  fonte no registo coletivo, sem atribuir declarações nominais não recebidas.
- [ ] Completar e rever o âmbito detalhado e os requisitos quantitativos do par.
- [ ] Aprovar métricas P/G, mínimos, metas e budgets; D não precisa de alvo inventado.
  S12 tem critério ≤5 s/meta ≤2 s individualmente validados; completar acordo da
  equipa e prova experimental sem voltar a classificá-los como ainda não escolhidos.
- [ ] Congelar a matriz por ID/asserção/fixture e manifesto BF; incluir subscriptions
  e os componentes de dados que D1/D9 abrangem.
- [ ] Executar BF com instrumentos corrigidos, sem alterar comportamento da aplicação;
  preencher cada P/G com valor bruto e resumo, ou NA justificado para mecanismo novo.
- [ ] Registar limitações e decisões sobre todas as falhas; um NM num gate impede
  declarar a baseline concluída. Não escolher depois o cenário que melhora mais.
- [ ] Apresentar os requisitos completos para revisão, antes de unidades/bolts/código.

**Na avaliação final:** repetir o mesmo corpus, budgets e método; apresentar
`baseline / mínimo / meta / final / diferença absoluta e relativa / resultado` por ID.
Um novo mecanismo NA tem teste de conformidade próprio e uma comparação do efeito
equivalente; não fabricar uma baseline zero. Uma falha de mínimo é reportada como
tal, mesmo se a mediana ou outro indicador melhorar.

## 8. Evidências e documentação técnica consultada

Os valores foram extraídos por
[audit-new-baselines.py](../memory-bank/intents/001-phase-2-quality-improvements/evidence/audit-new-baselines.py)
dos JSON originais em
[nfr-2026-11-16](../memory-bank/intents/001-phase-2-quality-improvements/evidence/nfr-2026-11-16/).
O [resultado da auditoria](../memory-bank/intents/001-phase-2-quality-improvements/evidence/baseline-audit-2026-11-16.json)
inclui hashes de origem e revisão por caso. Não constitui nova execução dos ensaios.
O [coletor estático](../memory-bank/intents/001-phase-2-quality-improvements/evidence/collect-static-baseline.py)
permite repetir o inventário de configuração/certificados; não emite conteúdo das chaves.

A [documentação oficial nginx auth_request](https://nginx.org/en/docs/http/ngx_http_auth_request_module.html)
define autorização por subpedido e tratamento distinto de 2xx/401/403/outros códigos.
A [documentação de proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
é a referência para buffering; isso não prova limites medidos na nossa configuração.
O [FFmpeg HTTP](https://ffmpeg.org/ffmpeg-protocols.html#http) permite seekability e
timeouts, mas não promete ler sempre só o início/moov de todos os formatos.
URLs S3 pré-assinados [podem ser reutilizados até expirar](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html):
uso único exige estado nosso. O comportamento específico do SeaweedFS 4.47 tem de
ser ensaiado e não herdado por analogia com AWS. Referências consultadas em 16/11/2026.

Análise/redação e extração de números apoiadas por Codex com a skill Inception;
os ensaios B16 foram fornecidos no novo commit e atribuídos no catálogo a Claude.
Nenhuma aprovação humana nem medição em falta foi inventada.

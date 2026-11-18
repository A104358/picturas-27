# Exercício 6 (Bloco 2) — Trade-offs, cenários de qualidade e candidatos a RNF

### Fase 2 — Melhoria de requisitos não funcionais do PictuRAS

**Equipa:** PL2-G4.  
**Elementos:** PG64000 — Luís Miguel Coelho; PG65397 — Alexandre de Oliveira
Monsanto; PG63941 — Diogo Alexandre Gomes Silva; PG63522 — José Miguel da Silva Santos.  
**Commit de partida:** `484be13b4c8e96c70e7e694a2c368d5601749438`, o mesmo do Bloco 1;
base oficial da aplicação `0523102`.  
**Checkout consultado nesta continuação:** `1d7103b`; comparação estática de
aplicação sem diferenças no âmbito registado em EV-40.  
**Data da análise:** 2026-11-18, Europe/Lisbon. **Versão deste documento:** 1.0.  
**Versões usadas:** enunciado 1.1 e template 1.1, de 2026-11-04.  
**Versão do Bloco 1 usada como entrada:** 1.2, que acrescenta o registo da continuação
sem alterar os IDs antigos nem a matriz 3.3. (EV-01, EV-38, EV-40)

Este ficheiro continua as secções 0–3 da [resolução do Bloco 1](resolution.md).
O registo único de EV/H fica na sua secção 2.6; aqui não se renumeram evidências,
hipóteses ou ALT-1/ALT-2. Os cenários QS-01–QS-06 são caracterizados **neste**
documento; o [Exercício 7](../07-architectural-tactics/resolution.md) referencia-os
sem redefinir os seis elementos. (EV-38, EV-39)

**Estado temporal:** o par QC-06+QC-05 já foi acordado como comunicado pelo
utilizador. As decisões técnicas têm o âmbito individual registado, não uma
aprovação dos quatro. BF/MF e refactoring ainda não começaram; UP-C4–C9 permanecem
propostas. O pedido de resolver exercícios não as seleciona. A entrega de 27/11
é a correção do utilizador; enunciados/diretrizes originais continuam a indicar
20/11. (EV-44, EV-45)

## 4. Trade-offs, cenários de qualidade e prioridades

### 4.1 Justificação detalhada das avaliações da matriz

Mantêm-se os juízos Alto/Médio/Baixo do Bloco 1, não pontuações medidas. G = padrão
global, V = realização local do vídeo; as alternativas continuam condicionais.
A observação posterior de um problema não demonstra o efeito de uma alternativa.
(EV-05, EV-38; H-01–H-04)

| Atributo | Justificação da matriz 3.3 e atualização de evidência | Depende sobretudo de | Evidência / hipótese |
|----------|----------------------------------------------------|---------------------|----------------------|
| Eficiência — comportamento temporal | G=M: filas desacoplam pedido/execução, mas preparação S3 e saltos permanecem. V=M: os efeitos comuns partilham uma passagem, mas fila única e estágios extra criam espera. ALT-1=B estimado: materializar vídeo entre efeitos pode acrescentar I/O/recodificação; ALT-2=M estimado: reduz espera com recursos livres, não o custo intrínseco de um vídeo. Os tempos de upload posteriores são outro percurso, não prova de velocidade das ALT. | Ambos: entrada/orquestração global e processamento local | EV-14–EV-20, EV-31, EV-36, EV-42; H-01/H-02/H-08 |
| Eficiência — capacidade/elasticidade | G=M: serviços separados permitem distribuir carga, sem autoscaling configurado. V=B: uma instância/prefetch 1. ALT-1=A estimado permite recursos por efeito, ALT-2=A condicionado permite vídeos concorrentes; ambos dependem do host/volume/CPU/modelo. O host escolhido para avaliar não demonstra capacidade. | Ambos, com limitação visível no worker | EV-09/EV-16/EV-19/EV-45; H-02/H-08/H-12 |
| Eficiência — utilização de recursos, aprofundamento | A matriz não dá uma nota autónoma a recursos; aprofunda-se o compromisso temporal/capacidade: há buffers integrais em três Node, ao passo que o caminho ordinário do worker lê frames incrementalmente. O benefício local não elimina o custo global do upload. O OOM observado sustenta priorizar esta fragilidade sem escolher ALT-1/ALT-2. | Sobretudo global, com ficheiros de vídeo a amplificar o custo | EV-08/EV-11/EV-12/EV-17/EV-42; H-05/H-15 |
| Fiabilidade — tolerância/recuperabilidade | G=B: confirmação antecipada e auto-ack deixam janelas. V=M: ack manual/ficheiro temporário ajudam, sem transação broker/S3/Mongo. ALT-1=M: repetir etapa exigiria estado/idempotência; ALT-2=M: reentrega noutra réplica mantém janelas e somaria concorrência de ficheiros. Não se promove a nota por um único teste de recuperação bem-sucedido. | Ambos | EV-15–EV-17/EV-21/EV-28/EV-30/EV-41; H-03/H-12 |
| Manutenibilidade — modularidade/modificabilidade/testabilidade | G=M: implantação separada, mas orquestrador e contratos concentram responsabilidades. V=M: há módulos/testes, embora efeitos/Whisper/extração partilhem processo e PIL esteja duplicado. ALT-1=A estimado separa implantação ao custo de contratos/testes; ALT-2=M mantém a estrutura interna e acrescenta configuração operacional. Linhas de código e quantidade de serviços não medem esforço de alteração. | Ambos | EV-10/EV-18–EV-20/EV-27/EV-46; H-04 |
| Segurança — confidencialidade/integridade/autenticidade | G=B e V=B: JWT no gateway não estabelece confiança de cada serviço, permissões de projeto ou autorização de receção em salas; portas e TLS agravam a fronteira. ALT-1=B/ALT-2=B: decompor ou replicar não implementa a política de segurança. Ataques verificados posteriores apoiam a prioridade, sem contar casos inconclusivos como efeitos provados. | Global, herdado pelo vídeo e eventos | EV-08/EV-11/EV-24/EV-43/EV-46; H-07/H-14 |
| Usabilidade — operabilidade | G=B e V=B: overlay/estado local e cancelamento parcial permanecem. ALT-1=B: novos workers não resolvem o cliente; ALT-2=B: menor espera hipotética não garante interação livre ou histórico após refresh. O novo envio deve preservar o fluxo de carregar/editar; não se acrescenta retoma ou biblioteca. | Ambos, sobretudo frontend/estado da tarefa | EV-22/EV-23/EV-25/EV-33; H-06/H-10 |

### 4.2 Cenários de qualidade para a extensão de vídeo

Esta é a definição canónica dos seis elementos. As medidas são variáveis e
procedimentos observáveis; não se inventam valores de aceitação. QS-01 e QS-02
alimentam os dois candidatos escolhidos; os restantes contextualizam trade-offs,
sem alargar o âmbito de implementação a outros RNF. (EV-38, EV-44)

| ID | Característica ISO/IEC 25010:2011 | Fonte do estímulo | Estímulo | Artefacto | Ambiente | Resposta | Medida da resposta |
|----|---------------------------------|-------------------|----------|-----------|----------|----------|-------------------|
| QS-01 | Segurança — confidencialidade, integridade e autenticidade | Cliente de outra conta ou peer interno sem a identidade/permissão exigida | Tentar ler/alterar media ou projeto alheio, entrar numa sala não autorizada ou continuar a receber eventos após revogação | Fronteiras nginx/gateways, projects, users/subscriptions, storage/S3 e WS usadas pelo vídeo | Instalação de teste isolada, fixtures dono/editor/leitor/outro, superfícies pública/host/rede Docker; normalidade e falha do autorizador em casos separados | Verificar identidade e autorização efetiva, recusar efeitos/receção indevidos e preservar operações legítimas; retirar receção quando deixar de existir via autorizada | Por caso: tentativas, admissões, efeitos de domínio/bytes/eventos verificados e sucessos legítimos; intervalo entre ACK de revogação e corte, recusas TLS separadas de domínio/erro interno. EV-24/EV-43; H-14 |
| QS-02 | Eficiência de desempenho — utilização de recursos; comportamento temporal como guarda | Utilizador free/premium legitimamente autorizado | Enviar um vídeo válido de tamanho crescente, isolado ou com outros uploads | Percurso nginx → gateway → projects → storage/S3, incluindo validação, hash e limpeza, com adaptador legado preservado | Mesmo host, recursos e corpus de teste BF/MF; C=1 e C=3 separados, posições de metadados e estado do processo identificados | Aceitar e disponibilizar apenas o ficheiro validado/associado corretamente, limitando recursos e mantendo pedidos leves utilizáveis | Por serviço/janela: RSS absoluto/adicional/retido, memória cgroup/agregada, CPU/rede/disco, OOM/reinícios; t_ready−t_send, t_ready−t0, t_hash e cleanup; SHA-256 do original e respostas corretas, coexistência pareada. EV-08/EV-11/EV-42; H-15/H-17/H-18 |
| QS-03 | Eficiência de desempenho — capacidade/comportamento temporal | Dois utilizadores com projetos distintos | Submeter reconhecimento de fala e, durante esse trabalho, um vídeo curto com efeito comum | video_queue, video_tool e orquestrador | Budget fixo, fala real/modelo identificado, carga mista; sem ativar réplicas por este exercício | Concluir corretamente os trabalhos e tornar observável a espera/consumo dos dois tipos | Tempos de fila/execução/commit por vídeo, conclusões válidas por minuto, CPU/RSS e integridade de áudio; cenário para avaliar H-02/H-08, sem meta numérica criada aqui. EV-16/EV-19 |
| QS-04 | Fiabilidade — tolerância a falhas/recuperabilidade | Falha controlada do worker/broker/orquestrador experimental | Interromper numa fronteira de execução/persistência identificada | Filas, Process/Result, fontes, saídas e quota de um lote | Fixtures descartáveis com estados antes/depois conhecidos, controlo sem interrupção | Manter originais/último resultado confirmado e classificar recuperado/falhado/indeterminado sem duplicar efeitos | Pedidos aceites, resultados corretos/duplicados/parciais/pendentes, diferenças de quota, tempo observado de recuperação e evidência de cada fronteira; sem prometer recuperação automática. EV-15/EV-21/EV-41; H-03/H-12 |
| QS-05 | Manutenibilidade — modificabilidade/testabilidade | Programador em tarefa controlada | Corrigir uma regra já existente de parâmetro/validação comum a imagem e vídeo | Efeitos PIL, validação/orquestração e testes | Mesmo requisito/correção em base e protótipo, sem novo efeito funcional | Alterar a regra coerentemente sem regressões fora do âmbito | Tempo da tarefa, módulos/serviços/contratos alterados, reconstruções e resultados de regressão; medir esforço, não apenas linhas. EV-18/EV-27; H-04 |
| QS-06 | Usabilidade — operabilidade | Utilizador com processamento já submetido | Tentar acompanhar e continuar a operar o editor durante o trabalho | Frontend, estado de tarefa e eventos WS existentes | Projeto imagem/vídeo/misto, tarefa e corpus iguais; prova por utilizadores ainda não recolhida | Tornar compreensíveis estado/erros e preservar as operações já existentes | Sucesso/erros/tempo de tarefas e compreensão do estado, cadência dos eventos; overlay e reload são observados, não dados como resolvidos. EV-22/EV-23/EV-25; H-06/H-10 |

**Priorização dos cenários — juízo argumentado, não votação inventada**

| ID | Importância para os stakeholders | Dificuldade / risco técnico | Prioridade |
|----|---------------------------------|----------------------------|------------|
| QS-01 | Alta: donos/colaboradores dependem de confidencialidade e integridade; há efeitos indevidos verificados | Alta: atravessa identidades, APIs, dados e permanência WS sem impedir clientes legítimos | 1 |
| QS-02 | Alta: carregar vídeo é entrada do fluxo central; RAM/OOM afeta todos os clientes do gateway | Alta: dois transportes, estado/storage, validação e custo adiado, preservando contratos | 2 |
| QS-04 | Alta: perda/duplicação/quota comprometem confiança | Alta: várias fronteiras de falha; tratamento operacional é guarda do âmbito escolhido, recuperação geral não é terceiro RNF | 3 |
| QS-06 | Média-alta: impacto direto na operação, porém faltam ensaios com participantes | Média-alta: cliente/estado/eventos e delimitação de alterações visíveis | 4 |
| QS-05 | Média: sustentabilidade da evolução | Média-alta: esforço empírico comparável e compatibilidade dos contratos | 5 |
| QS-03 | Média-alta: espera de trabalhos concorrentes, condicionada pelo uso local | Alta: competição CPU/RAM/Whisper e colisões sob réplicas; não selecionada para implementação | 6 |

### 4.3 Atributos de qualidade por ordem de prioridade

1. **Segurança** — QS-01, CAND-1: proteger efeitos/receção no domínio que já existe;
   prioridade do par comunicado, não conclusão de que todos os casos passaram.
2. **Eficiência de desempenho** — QS-02, CAND-2: utilização de recursos no upload;
   QS-03 é contexto de capacidade, não outro requisito incluído na entrega.
3. **Fiabilidade** — QS-04: preservar resultados/quota e tratar falhas dos percursos
   alterados; não confundir com recuperação automática geral.
4. **Usabilidade** — QS-06: não obter ganhos à custa de bloquear interação ou
   tornar erros/reconexão inexplicáveis.
5. **Manutenibilidade/testabilidade** — QS-05: limitar duplicação de regras e tornar
   as mudanças auditáveis. Portabilidade/instalabilidade permanecem guardas.

Esta ordem é a síntese documental coerente com a escolha QC-06/QC-05; a fonte
do acordo do par está em EV-44. Não houve nova reunião ou ordenação nominal dos
quatro elementos nesta tarefa. (EV-44, EV-45)

### 4.4 Pré-requisitos e efeitos colaterais entre atributos

| Atributo A | Atributo B | Efeito | Razão / evidência |
|------------|------------|--------|-------------------|
| Segurança | Eficiência | Pré-requisito e conflito | Autorização antes do corpo evita trabalho indevido; TLS, assinatura e revalidações consomem recursos e podem aumentar latência. Medir ambos, não assumir custo nulo. EV-08/EV-24/EV-44; H-14/H-18 |
| Eficiência do upload | Segurança | Pré-requisito | Retirar Node do corpo exige que o acesso S3 não contorne a autorização e que pending não seja utilizável. EV-11/EV-44; H-15 |
| Segurança | Disponibilidade | Conflito | Falha de projects impede novas entradas WS; leases não se renovam em erro. É política escolhida, não igualdade de segurança/disponibilidade provada. EV-44; H-14 |
| Streaming/hash posterior | Fiabilidade | Conflito a controlar | Erros/respostas perdidas podem deixar objetos/journals ambíguos; hash em falta exige tratamento de cache. O mecanismo completo continua por selecionar. EV-11/EV-26/EV-44; H-16 |
| Manutenibilidade | Desempenho | Sinergia e conflito | Regras comuns evitam divergência entre adaptador e transporte novo; mais intermediação/contratos pode aumentar custo. EV-10/EV-18/EV-44; H-04/H-17 |
| Fiabilidade | Usabilidade | Sinergia | Estados/erros/reconexão explícitos ajudam a compreender a tarefa, mas não criam biblioteca, novos efeitos ou refresh automático. EV-23/EV-44; H-06 |
| Capacidade por réplicas | Recursos/fiabilidade | Conflito | Mais consumidores replicam modelos e disputam ficheiros; ganho precisa de isolamento e recursos. EV-16/EV-19; H-02/H-12 |

### 4.5 Recomendações de melhoria à solução atual

| Recomendação | Atributos | Padrão referido | Esforço / risco de regressão |
|--------------|-----------|----------------|----------------------------|
| Realizar as fronteiras de identidade/autorizações e permanência WS já selecionadas, com controlos positivos e proteção das chaves | Segurança, com guardas temporais/disponibilidade | Global; vídeo herda APIs/eventos/storage | Alto / alto, estimativa: todos os callers legítimos precisam de ser preservados; H-14/H-17 |
| Realizar o percurso nginx/S3 e adaptador limitado com domínio/commit comuns, preservando quota e staging controlado | Eficiência, segurança e fiabilidade | Global/entrada do vídeo, sem distribuir frames | Alto / alto: fechar UP-C4–C9 antes da aplicação; H-15–H-18 |
| Calibrar e congelar BF, corpus/instrumentos e critérios aplicáveis antes do refactoring | Testabilidade e ambos os RNF | Global e integração | Médio / médio na preparação; não é melhoria já medida; EV-45 |
| Manter ALT-1/ALT-2 como alternativas documentadas, sem as implantar nesta seleção | Modularidade/capacidade | Vídeo dentro do padrão global | Alto / alto para ALT-1; médio / alto para ALT-2, estimativas herdadas; H-01–H-04/H-12 |

## 5. Candidatos a requisitos não funcionais da Fase 2

Há **exatamente dois candidatos**, correspondentes ao par já acordado. Os IDs
CAND são académicos; QC mantém os IDs do planeamento. Nenhum cenário auxiliar
se transforma num terceiro requisito de implementação. (EV-38, EV-44)

| ID | Característica / subcaracterística ISO/IEC 25010:2011 | Fragilidade na base | Origem | Impacto / pertinência | Exigência técnica / complexidade | Escala e método | Pré-requisitos / efeitos |
|----|-----------------------------------------------------|--------------------|--------|----------------------|----------------------------------|-----------------|-------------------------|
| CAND-1 = QC-06; QS-01 | Segurança — confidencialidade, integridade e autenticidade | Proteção do gateway não cobre todas as identidades/rotas/storage/WS; alguns efeitos indevidos verificados | Padrão global, herdado pelas operações de vídeo | Protege projetos, originais, resultados e colaboradores; relevante para imagem e vídeo | Coordenar verificação de ator, autorização de domínio, mTLS/TLS, identidade delegada e revogação, preservando rotas legítimas | Casos finitos por fronteira, efeitos/bytes/eventos antes/depois e latência/recusa/corte, segundo §5.1 | PKI/sessões/migração e dados legítimos; overhead/disponibilidade/manutenibilidade. EV-24/EV-43/EV-44; H-14 |
| CAND-2 = QC-05; QS-02 | Eficiência de desempenho — utilização de recursos; comportamento temporal como guarda | Buffers integrais em três Node; pressão/retenção/OOM e aceitação lenta em pilotos | Interação entre entrada global e tamanho do vídeo; não um defeito dos efeitos PIL | Viabiliza o carregamento existente sem esgotar o gateway/host ou impedir outros pedidos | Streaming limitado nos dois transportes, validação/estado/S3, métricas até trabalho completo e compatibilidade | Memória/CPU/rede/disco, tempos até ready/hash/cleanup, falhas/integridade, segundo §5.1 | Autorização antes do corpo, staging, quota preservada, cache/hash coerentes; não esconder custo no storage. EV-08/EV-11/EV-42/EV-44; H-15/H-18 |

### 5.1 Esboço de quantificação

| Campo | CAND-1 / QS-01 | CAND-2 / QS-02 |
|-------|----------------|----------------|
| Escala | Tentativas/efeitos indevidos e sucessos legítimos por caso; bytes/eventos e tempo de corte/latência em ms | RSS/cgroup/pico agregado em MiB, CPU-s, bytes por fronteira/disco, OOM/reinícios, tempos em ms, integridade e sucesso por tentativa |
| Cenário de medição | Clientes público, host e peer Docker controlado; dono/editor/leitor/outro; chamadas válidas e adulteradas, revogação/falha e salas pessoais/projeto | Corpus de vídeo PAD e real, transportes novo/legado separados, validação/hash/cleanup e pedidos leves pareados |
| Carga | Casos materializados com controlo positivo; WS-N1/J1/P1 e fronteiras L/R/B/E do contrato; não testar só credencial errada | 10/100 MiB free/premium e 500 MiB premium, H/T e processo reiniciado/aquecido; C=1/C=3; 1024 MiB/+1 byte como fronteira funcional separada |
| Ambiente | Esta máquina/Luís, instalação experimental isolada por concretizar, mesmo budget/configuração por cenário antes/depois; não usar volumes retidos | Mesmo host; EVAL-B1 e todos os serviços necessários por fase, imagens/dependências fixadas, gerador fora dos Node medidos; manifesto ainda não congelado |
| Instrumento | Adaptar probes históricos com asserções corrigidas, verificação de estado/bytes/eventos, TLS/peer/domínio separados e logs sanitizados | Gerador em fluxo, timestamps monotónicos, RSS/cgroup/CPU/rede/disco e verificação SHA-256; scripts históricos são ponto de partida, não runner final pronto |
| Valor medido na base / alvo / mínimo aceitável | **Baseline formal NM; valores finais a fixar/rever após BF.** Políticas/condições já escolhidas continuam registadas em EV-44/EV-45, sem se tornarem resultados | **Baseline formal NM; valores finais a fixar/rever após BF.** EV-42 é exploração histórica; EVAL-M1 contém critérios de planeamento já selecionados no seu âmbito, não uma nova medição |

**Regra de quantificação:** o enunciado/template pede que valores finais se fixem
após a medição inicial. Não se apagam as decisões de engenharia individuais
anteriores, nem se inventa uma BF para as justificar. Elas mantêm a proveniência
no [plano/revisão](../../fase2-revisao-plano-avaliacao.md); a consolidação final
exige BF, calibração e revisão. A lista de 60 métricas é decomposição dos dois
candidatos/guardas; U25 é G e nem todos os limiares estão aprovados. (EV-38, EV-45)

### 5.2 Relação entre os dois candidatos

Autorização antes do corpo é pré-requisito para reduzir trabalho de pedidos
indevidos. Por outro lado, retirar o corpo dos Node exige controlar a escrita/leitura
S3 e o estado de pending. TLS/assinatura/consultas acrescentam CPU/latência;
streaming/hash posterior alteram I/O, estados e risco de falha. Os dois RNF são
avaliados separadamente, com U25/funcionalidade como guardas e sem inferir causa
isolada só de um resultado final conjunto. (EV-44, EV-45; H-14–H-18)

### 5.3 Evidência exploratória existente

| Descrição | Localização | Como repetir / limite |
|-----------|-------------|-----------------------|
| Bloco 1: processamento misto, extração, testes existentes | [Registo](evidence/validacao-2026-11-09.txt) e [script](evidence/preparacao.cjs) | Seguir o registo em instalação descartável, revendo alvos. Histórico 8/74 testes e ensaio funcional; não foi repetido aqui. EV-28 |
| B14: carga e acessos internos com asserções de bytes, uma falha de worker | [Índice com scripts/brutos/comandos](../../../memory-bank/intents/001-phase-2-quality-improvements/evidence/README.md) | Preparação/corpus/gerador/coletores identificados no índice; nomes fixos e ações mutantes exigem adaptação/isolar. Não executar nos volumes retidos. EV-41 |
| B16: uploads e matriz de segurança auditada | [Originais/scripts/limitações](../../../memory-bank/intents/001-phase-2-quality-improvements/evidence/nfr-2026-11-16/README.md) | Gerador PAD e probes arquivados; corrigir premium/asserções/serviços ausentes antes de reutilizar. Separar Mac/ARM de Linux. EV-42/EV-43 |
| Comparação de fonte e organização dos novos materiais | [Manifesto](evidence/continuation-sources-2026-11-18.json) | Git diff limitado aos caminhos de aplicação e SHA-256 dos quatro originais; verificação estática, não ensaio de RNF. EV-40 |

## 6. Conclusões e recomendações

**Adequação do padrão atual:** microserviços/orquestração/filas e pipeline local
de vídeo continuam coerentes com projeto/pipeline/lote. A passagem incremental
ordinária não deve ser distribuída por efeito só para se parecer com imagem.
As fragilidades selecionadas estão sobretudo nas fronteiras de confiança e na
entrada de ficheiros grandes; não exigem alterar a semântica dos efeitos nem
implantar ALT-1/ALT-2. (EV-14–EV-20/EV-36/EV-44; H-01/H-02)

**Otimização:** realizar as escolhas de segurança e upload já selecionadas,
fechar os mecanismos ainda abertos, calibrar e medir antes de mudar. O adaptador
é parte do compromisso de compatibilidade e precisa de resolver memória; não
serve deixar o caminho antigo vulnerável. Preservar quota só no Apply e dados
reais; o zero projetos anónimos observado não permite descartar identidades.
(EV-44, EV-45; H-15/H-17)

**Evolução futura:** modularidade por efeitos, pool/isolamento de workers,
feedback persistente e recuperação automática ficam como investigação própria,
com cenários e medições, não como entregas implícitas. TTL/retoma/hash/probe de
UP-C4–C9 não são fechados por preencher este exercício. (EV-44; H-01–H-04/H-08)

| Risco | Funcionalidade afetada | Mitigação | Regressão existente / prova a acrescentar |
|-------|------------------------|-----------|-----------------------------------------|
| Novo controlo recusa callers legítimos/partilhas/limpeza de conta | Imagem e vídeo | Matriz por serviço/operação/identidade e controlo positivo; autorização de domínio preservada | Suites atuais de `projects/tests` não cobrem toda a matriz; acrescentar cenários integrados S01–S20/F04–F06 |
| Adaptador ou transporte novo altera API, versão ou quota | Vídeo e projetos mistos | 204/X-Project-Version legado, CAS/conflito definido, nenhuma cobrança no upload, domínio/commit comum | `video-pipeline.test.js`, `process-batch.test.js`; acrescentar HTTP/recursos/erro de ambos os transportes e U24 |
| Bytes pendentes/errados entram em preview/Apply/export | Imagem e vídeo | Isolamento efetivo, confirmação idempotente e teste de cada fronteira de falha; não presumir transação S3/Mongo | `frame-extraction.test.js` e testes de processador cobrem resultados; faltam testes integrados S23/S24/U15/U16/U21–U23 |
| Hash em falta confunde cache ou oculta trabalho posterior | Preview e vídeo | Leitura/escrita de cache suspensas ou isolamento provado; medir t_hash e consumo completo | Testes de vídeo não provam cache/hash assíncronos; UL-09 proposto, não executado |
| Alterar efeitos, ordem, áudio, legendas ou extração | Imagem/vídeo/misto | Manter pipeline por projeto, trim/speed por vídeo e extração terminal/única, sem novos efeitos | `Tools/video/tests/test_video_processor.py`, `test_frame_extraction.py`, `test_subtitles.py`; incluir fala real, pois recognizer da suite é simulado |
| Cortar WS deixa frontend incoerente ou troca anónimo | Sessões/progresso de ambos | Reconexão explícita, nova autorização por sala, preservar identidade/duas vias válidas; prova real de recuperação ainda desconhecida | Faltam testes integrados WS/expiração/importação; WS-T/AR são planos, não testes passados |

ACL owner-only para eliminar projeto é uma mudança de política já escolhida
individualmente, não comportamento herdado demonstrado; deve ser justificada e
testada, não escondida como refactoring puro. Preservar remoção de media pelo
editor. A revisão académica não é inferida da escolha individual. (EV-44)

## 7. Utilização de IA

| Ferramenta / skill | Tarefa apoiada | Validação feita pela equipa / estado | Onde está documentado |
|-------------------|----------------|-------------------------------------|------------------------|
| Codex; contexto da skill local specsmd-inception-agent previamente usada | Ler materiais/código, continuar IDs, cruzar decisões/pilotos, formular QS/CAND e redigir trade-offs | Utilizador forneceu equipa, par e escolhas com âmbito registado; esta resolução ainda requer revisão académica dos quatro. Não atribuir ao grupo a verificação estática feita pelo agente | §4–§6; EV-38–EV-48; histórico de Inception |
| Codex e verificações estáticas locais | Organizar quatro originais preservando hash, comparar caminhos de aplicação, verificar referências/tabelas/IDs e coerência entre exercícios | Resultado automático reportado separadamente; não substitui ensaios BF/MF nem aprovação humana | EV-40; índices e registo de verificação da continuação |

### Lista de verificação do Bloco 2

- [x] Reutilizados IDs/diagnóstico/matriz do Bloco 1; novas EV/H no registo único.
- [x] Todos os atributos da matriz justificados, com origem global/vídeo.
- [x] Cenários com seis elementos e medidas observáveis, priorizados.
- [x] Atributos ordenados e relações/efeitos colaterais explicitados.
- [x] Exatamente dois candidatos, classificados e alinhados com QC-06/QC-05.
- [x] Método/carga/ambiente descritos; BF e valores finais não inventados.
- [x] Pilotos e reprodução localizados, com limites e ambientes separados.
- [x] Riscos funcionais associados a testes existentes e lacunas concretas.
- [x] IA e versões registadas, sem inventar leitura/ensaio/aprovação.
- [ ] Revisão académica nominal pela equipa e consolidação de quantificação após BF.

O histórico dos templates originais fica em `sources/`; não se copia como
histórico da resolução nem se declara esta resolução uma medição final.

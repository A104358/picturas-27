# Fase 2 — Revisão do orçamento, cargas, mínimos e metas

**Equipa:** PL2-G4. **Data:** 18/11/2026. **Estado:** A/A/A/A selecionadas
individualmente, com confirmação técnica e condições; não acordo dos quatro nem
campanha executada. O utilizador pediu a revisão e depois comunicou que a proposta
técnica fica validada, sujeita a calibração. Ver [plano de avaliação](fase2-plano-avaliacao.md).
A máquina/Luís e as escolhas anteriores de segurança mantêm o seu estado; não
pedir novamente a seleção do host nem reabrir WS/PKI por associação.

## Opções consideradas — A/A/A/A selecionadas individualmente

| Ponto | A — seleção individual | B — alternativa e custo | Confiança |
|-------|------------------|-------------------------|-----------|
| EVAL-B1 — recursos | Manter 10 GiB agregados e 4 GiB nominais fora do teto; 2 CPU/2 GiB por Node medido; calibrar dependências por fase. Elevar a proposta de disco inicial de 20 para **pelo menos 60 GiB**, mais se o inventário de retenção exigir | Reduzir RAM para 8 GiB ou manter 20 GiB de disco com limpeza por tentativa. RAM inferior pode condicionar artificialmente BF; limpeza mais frequente exige outro protocolo de estado/I/O, validado antes/depois | Média na adequação; baixa na capacidade sem piloto |
| EVAL-C1 — corpus | Manter 10/100/500 MiB, H/T, formatos/codecs discretos e fronteiras; incluir **1024 MiB/+1 byte como guarda funcional separada**, sem alegar o gate de recursos de 500 MiB nesse tamanho | Deixar 1024 MiB como cobertura não executada explicitamente. Reduz trabalho, mas não demonstra o máximo premium; não reduzir o limite funcional da aplicação | Média; custo físico por medir |
| EVAL-R1 — cargas/repetições | Manter **100 uploads normais e 9 concorrentes por campanha**, coexistência e WS separados; três repetições dos casos negativos materializados | Reduzir para 50 normais escolhendo uma posição H/T no grupo primário e testar a outra só funcionalmente. Poupa ensaios, mas perde comparação temporal/recursos por posição dos metadados | Média; horas da equipa desconhecidas |
| EVAL-M1 — critérios | Manter propostas 64/32 MiB, <3/<1 s, 0 OOM, 3 uploads válidos, integridade/autorizações corretas, com as precisões abaixo. Promover a guarda de coexistência U25 a **G** | U25 fica apenas diagnóstico D, sem condicionar aprovação global; ou propor outros valores justificados antes de congelar. Não mudar alvos depois de observar MF | Média nos budgets/metas; alta na necessidade de critérios e relógios inequívocos |

A validação técnica individual mantém a calibração **antes** de congelar BF,
contenção/consumo por fase, inventário físico de disco e condições idênticas em
BF/MF. O utilizador confirmou a conta de 41,2305 GiB. Os 60 GiB são piso: após
essas entradas e reserva de 10 GiB restam cerca de **8,77 GiB**, não um orçamento
garantido para os restantes formatos, resultados e overhead. Aumentar se necessário.
OOM/timeout efetivo da base é resultado quando instrumento/ambiente funcionam;
não aumentar recursos só para esconder a fragilidade. Uma alteração indispensável
de recursos/método tem revisão e condições comparáveis nas duas campanhas.

### Âmbito exato de EVAL-M1

A validação abrange **apenas os critérios descritos na tabela EVAL-M1 abaixo**:

- U01/U02: 64/32 MiB, respetivas janelas C=1 até 500 MiB e repouso após trabalho.
- U03/U20: zero OOM/reinícios e 3/3 íntegros em cada uma das três rodadas C=3.
- U04: incrementos nginx 128/64 MiB e SeaweedFS 256/128 MiB em C=1.
- U09: pós-envio <3000/<1000 ms por amostra válida de 500 MiB, até ready.
- U10: mediana ≤1,10× BF válido, meta ≤BF, sem rácio quando falta comparador.
- U14: se hash posterior, ≤10/≤5 s após ready por ficheiro até 500 MiB em C=1/C=3,
  incluindo fila, e custo completo registado.
- U15/U16 e a precisão F02: original íntegro, cache correta e distinção entre
  original e output transformado; isto não aprova toda a cobertura F02 por omissão.
- U22: zero órfãos após TTL+60 s/meta TTL+10 s; **o TTL concreto não é escolhido**.
- U25: promoção D→G, zero erros e mediana sob carga ≤1,10× controlo da mesma
  campanha/meta ≤controlo, por par, com todas as tentativas/erros preservados.

U11/U12 permanecem D; 500/200 ms de preflight são referências, não mínimos/metas
aprovados como gates independentes. S12/S20 conservam a validação anterior de
5/2 s e 30/10 s, sem prazo novo para substituição da CA. **Os restantes valores
ou cláusulas das 60 métricas mantêm os estados anteriores**; em particular não
ficam aprovados por associação S21, U08/U13/U17–U19/U21/U23/U24/U26 ou F08/F10.
A regra de não admitir operações indevidas segue os contratos já selecionados,
sem validar automaticamente todos os limiares de todas as superfícies.

## EVAL-B1 — conta dos recursos e limites da conclusão

### RAM

O host observado tem cerca de 15,32 GiB. Os limites candidatos dos três Node,
nginx, SeaweedFS e WS somam **7,625 GiB**, sobrando **2,375 GiB dentro de 10 GiB**
para os três MongoDB, RabbitMQ, users/subscriptions, frontend, gerador e coletores.
Essa diferença é aritmética entre tetos, não uma distribuição implementada nem
prova de que as dependências cabem. Limites de CPU também não são cores reservados.

Os **4 GiB fora do teto** são uma margem nominal de planeamento para SO/outros
processos, não memória livre reservada ou garantida. Os 9,53 GiB de MemAvailable
registados antes são uma observação, não capacidade constante. Não é necessário
que toda a stack consuma o teto para iniciar; também não se pode permitir pressão
no host só porque o cgroup tem limite. Fontes: [MemAvailable no kernel](https://docs.kernel.org/filesystems/proc.html),
[limites cgroup](https://docs.kernel.org/admin-guide/cgroup-v2.html),
[recursos Docker](https://docs.docker.com/engine/containers/resource_constraints/).

Antes de BF, completar uma tabela por fase com conjunto de serviços, tetos,
memória residente/retida, consumo do gerador, política de swap e limite agregado
efetivo. Calibrar a preparação sem alterar a aplicação; repetir as mesmas condições
em MF. Se o perfil não couber ou o host ficar sob pressão, registar a preparação
inconclusiva, rever o orçamento e repetir a calibração. Não iniciar BF com limite
agregado apenas declarado no JSON, nem retirar subscriptions/IA para contar
cobertura que não foi executada. Os perfis separados têm dependências explícitas.

Não recomendo descer logo para 8 GiB: restariam apenas 0,375 GiB se os tetos
citados fossem usados em simultâneo. Isso não prova falha inevitável — os serviços
podem usar menos —, mas é pouca margem para adotar sem medição. A capacidade real
da ingestão e de Whisper/IA continua por demonstrar.

### Disco e retenção

A conta usa apenas os tamanhos e repetições propostos, não uma medição de I/O:

| Parcela | GiB de bytes lógicos de entrada |
|---------|--------------------------------|
| 100 normais por campanha | 14,0625 |
| 9 concorrentes de 500 MiB por campanha | 4,3945 |
| 3 coexistências de 500 MiB por campanha | 1,4648 |
| Total sem warm-ups por campanha | **19,9219** |
| BF + MF, incluindo os 10 warm-ups de 10 MiB de cada campanha | **40,0391** |
| Corpus PAD H/T separado, uma cópia de cada tamanho/posição | 1,1914 |
| Total das parcelas anteriores | **41,2305** |

Se cada tentativa criar um objeto retido, estes bytes lógicos já superam os
20 GiB inicialmente propostos. Não confundir tráfego transferido com ocupação
física medida: deduplicação, versões, alocação SeaweedFS, snapshots e limpeza
podem alterar a ocupação. A conta conservadora não pressupõe deduplicação.

Recomendo **60 GiB livres no início como piso**, conservando o limiar proposto
de 10 GiB para parar novas submissões. Os 60 GiB não garantem o pior caso:
1024 MiB/fronteiras, codecs reais, resultados, temporários, logs e backups ainda
acrescem. Inventariar tudo, incluir pelo menos a reserva de 10 GiB e aumentar o
piso se o cálculo ultrapassar 60. Uma cópia integral adicional das campanhas
pode obrigar a mais espaço. A leitura histórica de 103,63 GiB livres não reserva
esse espaço nem prova que continue disponível.

É possível limpar objetos experimentais entre tentativas após conferir estado,
hash e bruto. Se a equipa escolher essa alternativa, fixar o procedimento e a
retenção de prova antes de BF/MF e recalcular o pico; não apagar evidência de uma
falha nem tocar nos dois conjuntos retidos para libertar espaço.

## EVAL-C1/R1 — cobertura proporcional e sem produto cartesiano artificial

Manter o núcleo de 100 tentativas permite comparar perfis, tamanhos, H/T e estado
do processo com cinco repetições por estrato. Não demonstra percentis extremos
ou sucesso populacional. A carga C=3 tem nove tentativas próprias; os três pares
de coexistência acrescentam **três uploads e 600 pedidos leves** por campanha,
não estão incluídos nos 109 uploads principais. O total de casos de segurança,
fronteiras, regressão e warm-ups será contado no manifesto físico, não é 109.

O protocolo de coexistência deve ficar concreto: em cada par, 100 pedidos no
controlo sem upload e 100 durante o upload, mesma rota/payload/keep-alive e 5/s.
O corpo de 500 MiB a 10 MiB/s demora aproximadamente 50 s de envio; iniciar a
janela de 20 s de pedidos leves depois de confirmar fluxo de bytes, por exemplo
5 s após t0 do corpo, com a mesma regra antes/depois. Se o upload terminar ou
falhar antes da janela acabar, registar sobreposição efetiva e falha; não chamar
ao conjunto uma janela completa sob carga. Não comparar U09 deste pacing com
o grupo primário sem pacing.

H/T é uma propriedade verificada dos ficheiros, não deduzida do nome. FFprobe
remoto deve ser avaliado nos dois casos e em formatos reais. Validar os seis
codecs aceites em contentores compatíveis; não multiplicar todos os formatos por
todos os perfis, tamanhos e estados. O caso funcional de 1024 MiB preserva o
limite premium; não torna a carga C=3 de 1024 MiB parte do requisito proposto.

Os cenários WS já selecionados mantêm 50/510/200 ligações dentro dos tetos e
513/4097 como tentativas de recusa. Para cada janela, materializar o instante
de revogação, alvo e eventos sequenciados; os pequenos no ensaio de justiça não
podem ficar sem observação própria. Não contar uma sessão já expulsa na preparação
como teste válido de corte posterior. Não aumentar tetos para completar a fixture.

## EVAL-M1 — critérios individualmente validados no âmbito acima

| Métrica | Critério selecionado / condição antes de congelar |
|---------|-----------------------------------------------|
| U01 — memória adicional | ≤64 MiB mínimo / ≤32 MiB meta por Node, tentativa C=1 e janela de trabalho completa, até 500 MiB. Incluir hash/leitura posterior. Medir absoluto e incremento; C=3 usa pico do grupo, sem divisão por três |
| U02 — memória retida | Mesmos 64/32 MiB face ao estado inicial equivalente, medidos após terminar hash/trabalho/limpeza normal e mais 10 s sem nova carga. Dez segundos após ready com hash ainda ativo não são repouso |
| U03/U20 — falhas e concorrência | 0 OOM/reinícios; 3/3 íntegros em cada uma das três rodadas previstas. Guardar todas: uma rodada falhada não desaparece porque a última passou |
| U04 — nginx/S3 | Manter incrementos 128/256 MiB mínimo e 64/128 MiB meta C=1; são valores de engenharia agora validados individualmente, ainda não medidos. Teto de contentor é outro número: uma morte por limite não passa como pico baixo |
| U09 — pós-envio | <3000 ms mínimo / <1000 ms meta **por amostra válida**, incluindo confirmação e validação. A aplicação base responde num só passo; PUT finalizado não equivale a ready. Justificação documental e bytes do cenário continuam explícitos |
| U10 — total | Mediana ≤1,10× BF equivalente como guarda, meta ≤BF; somar preflight desde t0. Se BF tiver só falhas/timeout, não há mediana válida para calcular um rácio: reportar a melhoria de sucesso/resultado sem inventar comparador temporal |
| U11/U12 — preflight/fases | Manter como diagnóstico D, com 500/200 ms de U11 apenas referência de engenharia, sem gate independente. O gate temporal é U09/U10; não promover fases a novos requisitos por terem números na tabela |
| U14 — hash posterior | Manter ≤10 s após ready / meta ≤5 s até 500 MiB, em C=1 e C=3. São prazos por ficheiro que incluem espera na fila. Medir também t_hash−t_send e t_complete; esclarecer cobertura no catálogo. Não assumir débito ou retoma garantidos |
| U15/U16/F02 — integridade/cache | SHA-256 do **original** mantém-se após upload e processamento; um resultado transformado é comparado segundo pixels/áudio/semântica de F02, não exigido igual ao original. Preview sem hash não lê nem escreve cache partilhada sem isolamento provado |
| U22 — limpeza | Manter TTL+60 s mínimo / TTL+10 s meta; TTL e política de retry continuam por decidir nos uploads. Falha de limpeza, objeto órfão e idade observados ficam no bruto, sem declarar este gate pronto só pela fórmula |
| U25 — coexistência | G: 0 erros e mediana sob carga ≤1,10× controlo da **mesma campanha**, meta ≤controlo, por par. Mesmo limiar anterior, agora com prioridade G e validação individual; controlo/carga na mesma campanha, sem esconder erros |
| S12/S20 — prazos de segurança | Manter exatamente os critérios já validados: corte WS ≤5 s/meta ≤2 s e isolamento PKI ≤30 s/meta ≤10 s. Não adaptar ao resultado de desempenho nem transformar duração de substituição da CA em SLA |

Se a leitura de 500 MiB para hash só começar em ready, completar em 10/5 s
corresponde nominalmente a 50/100 MiB/s; para três leituras completas no mesmo
intervalo, a soma seria 150/300 MiB/s. Isto é **conta de planeamento condicionada**,
não débito demonstrado: início real, CPU, fila e bytes já lidos têm de ser medidos.
Não usar a conta como garantia de cumprir U14 nem ocultar o custo depois de ready.

Para RSS, calibrar a variabilidade em repouso e o overhead de recolha antes de BF;
isso não prova erro absoluto de memória. Medidas RSS/cgroup e amostragem têm
universos/limitações distintos. Se a resolução ou o ruído impedirem separar o
limiar do resultado, o caso é inconclusivo, não aprovado por arredondamento.
Em tempos remotos, guardar limites de observação e incerteza; só afirmar cumprimento
se o limite superior respeitar o critério. Não arredondar 1000 ms para «<1 s».
Uma amostra cujo intervalo cruza o limiar precisa de medição melhor ou conclusão
inconclusiva; não é prova automática de falha da aplicação.

## O que fica preparado e o que ainda falta

A revisão e a validação individual ficam registadas; **U25 é G**. A seleção
A/A/A/A fecha estes pontos técnicos, com calibração/condições por demonstrar.
Não é aprovação integral dos 60 limiares nem dos requisitos completos, prontidão,
capacidade ou acordo dos quatro elementos. Os 60 IDs são preservados.

Falta escolher o contrato de uploads, materializar matriz/ficheiros, verificar
runtime/controladores e calibrar os instrumentos antes de congelar BF/MF. Não há
novos valores de baseline, ensaios de carga, mudança da aplicação, consulta aos
volumes, emissão de tokens ou PKI executada. IA: revisão apoiada por Codex com a
skill Inception; fonte da seleção e condições é a mensagem do utilizador de 18/11.

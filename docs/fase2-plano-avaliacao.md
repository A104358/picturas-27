# Fase 2 — Plano de avaliação antes e depois do refactoring

> **Leitura na entrega (27/11/2026):** este documento preserva o diagnóstico/planeamento
> da data indicada. A implementação B0–B12 está concluída; estados «pendente» ou
> «por executar» no texto não descrevem o fecho da fase. Consultar o
> [relatório final](src-doc-fase2-template/README.md), os
> [resultados oficiais](README.md#resultados-oficiais) e as decisões posteriores no
> [handoff](refactor-handoff.md). O original é mantido para rastreabilidade.


**Equipa:** PL2-G4. **Preparado:** 18/11/2026. **Entrega:** 27/11/2026, por
correção do utilizador; as diretrizes originais mantêm 20/11 como fonte histórica.
**Estado:** plano de trabalho para revisão, não campanha executada nem requisitos
integralmente aprovados. O utilizador escolheu **esta máquina, administrada pelo
Luís**, como anfitrião. Projeto Compose e corpus físico ainda não estão congelados; EVAL-B1/C1/R1/M1 A
ficam individualmente selecionadas com as condições e âmbito da revisão. Não há autorização implícita para
iniciar a stack, reutilizar volumes retidos ou alterar a aplicação.

O par acordado mantém-se **QC-06 — segurança/autorização ponta a ponta** e
**QC-05 — eficiência de desempenho/utilização de recursos nos uploads**. Este
plano operacionaliza as [60 métricas existentes](fase2-metricas-e-baseline.md);
não cria outro catálogo nem transforma todas as guardas em novos RNF.

**Revisão técnica de 18/11:** as [quatro recomendações EVAL-B1/C1/R1/M1](fase2-revisao-plano-avaliacao.md)
detalham alternativas, contas e condições. O utilizador selecionou A nas quatro,
com confirmação técnica e calibração obrigatória antes de BF. O piso de disco
fica ≥60 GiB, por aumentar se o inventário exigir, e **U25 passa a G**. A validação
é individual e limitada aos critérios enumerados em EVAL-M1, não aos 60 por omissão.

## 1. O que está decidido e o que ainda falta congelar

| Elemento | Estado e fonte | Consequência para a avaliação |
|----------|----------------|------------------------------|
| Máquina e administrador | **Atualizado em 20/11:** Mac (Apple M4 Pro) de um único elemento da equipa, que recolhe a BF e a MF. A escolha de 18/11 (esta máquina / Luís, LOCAL-HOST-01 / ADM-01) passou a exploratória (EXP) | BF e MF no mesmo host; medições noutros computadores não se juntam às oficiais |
| Dados existentes | **Atualizado em 21/11:** no host oficial, o projeto antigo `picturas` (volumes da Fase 1) foi apagado por decisão do utilizador. `picturas-quality-20261114` não existe nesse host | O `med.py` só opera em `picturas-nfr` / `picturas-nfr-<sufixo>` criados por ele; nunca apaga volumes de outra instalação |
| Instalação de ensaio | **Atualizado em 21/11:** projeto isolado `picturas-nfr` criado pelo `med.py` (proposta inicial EVAL-I1: `picturas-eval-20261118`) | Portas +20000, limites de 2 CPU / 2 GiB nos serviços medidos; ver [plano de medição](planoMedicao.md) |
| Segurança | Escolhas individuais D3/D4/D7, WS/PKI/ACL/SESS/JWT/LINK preservadas nos contratos | Critérios já validados não voltam a ficar por escolher; implementação e resultados são outra coisa |
| Uploads | UP-C1/C2/C3 A individualmente selecionadas: adaptador multipart seguro, quota só no Apply, staging controlado; UP-C4–C9 A selecionadas em 21/11 | Fechar estado/token/TTL/retry/commit/hash/probe/cleanup no ciclo de vida; nenhum mecanismo comprovado por documentação |
| Limites/metas de engenharia | Critérios enumerados em EVAL-M1 individualmente validados; restantes valores mantêm estado anterior | Calibrar antes de BF e congelar a configuração física sem escolher alvos depois de observar MF |
| Recuperação anónima real | Existência de associação independente desconhecida | Usar casos sintéticos; recuperação das duas identidades reais continua pendente |
| Baseline formal BF e medição final MF | Não executadas nesta preparação | B14/B16 são pilotos históricos; metadados do host não são uma baseline da aplicação |

As [diretrizes, pp. 1–3](guidelines/fase-2-guidelines-1.pdf) pedem quantificação,
medição inicial, refactoring e repetição nas mesmas condições, com preservação
funcional e IA documentada. Não fixam os budgets ou valores de engenharia aqui
propostos. O prazo de 27/11 provém da correção posterior do utilizador.

## 2. Instalação e orçamento propostos

### Observação de leitura do anfitrião

A [ficha de recursos](../memory-bank/intents/001-phase-2-quality-improvements/evidence/evaluation-host-2026-11-18.json)
regista Linux x86_64, kernel 6.8.0-149-generic, Intel Core i7-13700H,
20 processadores lógicos e 16 066 840 KiB de RAM, aproximadamente **15,32 GiB**.
Havia cerca de **9,53 GiB disponíveis** e **103,63 GiB livres** no filesystem do
workspace naquele instante; estes dois valores variam. Não foram consultados
Docker, bases de dados, browsers ou volumes. A presença de ferramentas no PATH
não verifica as versões, o daemon, o suporte cgroup ou a capacidade da stack.
O HEAD observado é `662af7322d1884f2cf53a86be06c88cd6b5920c2`, não o commit BF já congelado.

### Isolamento a verificar antes do arranque

- Usar um projeto Compose distinto e volumes/redes próprios, com dados sintéticos;
  conferir a configuração resolvida, nomes explícitos, volumes externos e mounts.
  O Compose base declara `name: picturas`; não executar comandos sem identificar
  explicitamente o projeto experimental. Nome diferente não separa bind mounts,
  portas fixas, diretórios de backups ou perfis de browser.
- Manter `https://localhost:8080` para os fluxos públicos; nunca parar outra
  instalação para libertar a porta por inferência. Conflito de porta é preparação
  pendente. Internas publicadas para os ensaios ficam contidas em loopback e numa
  rede de teste, sem ligar clientes aos volumes reais. Preservar a topologia de
  domínio de cada cenário, sem acrescentar uma segunda stack concorrente.
- Identificar a contenção experimental imposta também a BF: uma publicação em
  loopback por proteção do laboratório não demonstra que a aplicação base já
  satisfazia D5. S18 reporta separadamente configuração original, configuração
  efetiva e alcance host/rede Docker; não alegar alcance LAN/Internet não medido.
- Backups, cache de modelos, diretório de media e artefactos de teste têm caminhos
  próprios. Perfis de browser são dedicados, com confiança conhecida e sem sessões
  reais. CA/chaves/credenciais sintéticas privadas ficam fora de Git e do build;
  não copiar os valores versionados para o relatório. Configuração de fixtures e
  eventual substituição de material criptográfico são diferenças explícitas no
  manifesto; não alterar a política de validação de BF para fabricar um controlo.
- Executar BF e MF sequencialmente, com estado inicial equivalente recriado a
  partir da mesma definição de fixtures; preservar os brutos de ambas. Só limpar
  recursos identificados do projeto de ensaio após conferir a lista de alvos.
  Este documento não fornece nem executa um comando de destruição de volumes.

### EVAL-B1 A — orçamento selecionado, a calibrar, não capacidade demonstrada

| Recurso | Seleção individual / parâmetros ainda por concretizar | Verificação antes de congelar |
|---------|----------------------|-------------------------------|
| Campanha completa, incluindo gerador e coletores | Teto agregado de 10 GiB, com pelo menos 4 GiB nominais fora desse teto para SO/outros processos | Implementar/verificar limite agregado e completar preflight por fase; não é memória reservada. MemAvailable é uma observação, não consumo futuro ou prontidão; pressão do host continua a ser verificada |
| api_gateway, projects e img_storage | 2 CPU / 2 GiB por serviço, dentro do teto agregado | Mesmos limites antes/depois, PID/cgroup/imagem identificados; são limites, não memória reservada |
| nginx / SeaweedFS / ws_gateway | 128 MiB / 1 GiB / 512 MiB, respetivamente, como limites candidatos | Confirmar no piloto que o controlo legítimo inicia e progride; estes limites não são as metas de incremento de RSS |
| Dependências, frontend e gerador | Partilham o restante teto; declarar limites efetivos por serviço e CPU do gerador no manifesto | Se não couberem ou houver pressão, rever o budget **antes** de BF; não omitir subscriptions ou esconder o custo do cliente |
| Disco livre no início | Pelo menos **60 GiB**, selecionado em 18/11, para corpus/objetos/temporários/brutos e reserva | BF+MF com warm-ups e corpus PAD somam cerca de 41,23 GiB de entradas se retidas, sem formatos/fronteiras/outputs/overhead/backups. Inventariar pior caso e somar reserva de 10 GiB; aumentar acima de 60 se necessário |
| Reserva de disco durante o ensaio | Interromper novas submissões abaixo de 10 GiB livres, proposta | Guardar o estado da tentativa e os recursos consumidos; não excluir a falha do denominador |

O limite agregado é proposta de contenção para este host, não uma propriedade do
Compose atual. Sem suporte/configuração demonstrados, EVAL-B1 fica pendente.
Os 4 GiB são distribuição nominal fora do teto, não garantia de memória livre.
Os limites Node/nginx/SeaweedFS/WS somam 7,625 GiB; as restantes dependências e
instrumentos têm só 2,375 GiB se todos esses tetos forem usados. Calibrar antes de
BF, sem reduzir serviços para declarar uma cobertura que não foi exercitada.
Não desativar o OOM killer, alterar swap do host ou encerrar processos alheios.
Registar swap, CPU, pressão e tráfego externo; uma campanha com paginação/pressão
desigual exige análise e eventual repetição documentada, não exclusão seletiva.

**Perfis de serviços:** o perfil de ingestão inclui nginx, frontend, api_gateway,
projects, img_storage, ws_gateway, users, subscriptions, os três MongoDB, RabbitMQ
e SeaweedFS. As fases funcionais e por canal acrescentam os workers/IA/mock/backup
necessários ao caso. Congelar cada conjunto antes/depois; todos os participantes
da matriz PKI-C5 têm de ter probe positivo/negativo, mesmo que ativados por fases.
Um serviço omitido ou parado não conta como canal protegido. Real Whisper e IA
podem exigir budget/arranque próprios; se não couberem, registar bloqueio de
cobertura, sem substituir silenciosamente por mocks ou eliminar funcionalidades.

## 3. Corpus e cargas a materializar

### EVAL-C1 A — cobertura selecionada; ficheiros por materializar

Cada ficheiro tem ID, bytes exatos, SHA-256, origem/licença, comando de geração,
versão do gerador/FFmpeg e saída ffprobe sanitizada. Os bytes gerados ficam fora
do Git. **MiB = 1 048 576 bytes.** O código atual multiplica os limites em MB por
1024²; usar esse comportamento no ensaio e explicitar a diferença de nomenclatura
do PDF. Os perfis são fixtures verificadas; premium por preparação administrativa
controlada ou pagamento mock legítimo, nunca pelo bypass de registo público.

| Família / IDs propostos | Construção e casos | Utilização |
|-------------------------|--------------------|------------|
| PAD-10/100/500-H/T | MP4/H.264/AAC, 10 s, 1280×720/30 fps, tamanho exato 10/100/500 MiB por padding estrutural válido; variantes com metadados no início/fim verificadas | Comparação primária tamanho→recursos; padding não representa distribuição de bitrate real |
| REAL-MP4/MOV/WEBM | Pelo menos um vídeo válido por contentor; cobrir h264/hevc/vp8/vp9/av1/mpeg4 em contentores compatíveis, com/sem áudio e tamanhos reais registados | Guarda de formatos/ffprobe, sem exigir combinações inválidas de todos os codecs/contentores; não atribuir-lhes os tempos dos PAD |
| BOUNDARY | Tamanho de 100/1024 MiB e +1 byte; duração 60/600 s e excedente; resolução limite e excedente; orientações horizontal/vertical | Cobertura funcional dos limites free/premium. Propor ensaio de fronteira 1024 MiB separado; não estender o gate primário de memória de 500 para 1024 MiB por associação |
| BAD | Vazio, truncado/corrompido, sem stream vídeo, codec não aceite, extensão/MIME falsos, metadados declarados diferentes e corpo menor/maior | Erros definidos, integridade/quarentena/limpeza. O resultado esperado distingue o comportamento atual de decisões novas |
| REG-IMAGE/VIDEO/MIXED | PNG/JPEG conhecidos; vídeos com áudio e fala curta de proveniência conhecida; projetos só imagem, só vídeo e mistos | Pixels/semântica, ordem, trim/speed, previews, legendas reais, extração e exportação |
| IDENTITIES | Dono, editor, leitor, outro utilizador; free com quota 0/5, premium e anónimo; duas vias válidas; certificados por principal/casos inválidos | Autorização e preservação de quota/sessões; apenas identidades sintéticas |

Preencher o resultado esperado de extensão/MIME/codec a partir do validador atual
e das decisões aprovadas, não presumir que toda a divergência de MIME é hoje
rejeitada. Upload com saldo zero não deve ser confundido com Apply: a política
atual não debita operações no upload. Uma nova recusa exige decisão explícita.

### EVAL-R1 A — repetições e estados selecionados

| Grupo | Carga e repetições por campanha BF/MF | Denominador e relatório |
|-------|-------------------------------------|------------------------|
| UP-NORMAL | 5 combinações: free 10/100 e premium 10/100/500 MiB; duas posições H/T; dois estados; 5 tentativas por estrato | **100 tentativas**, aproximadamente 14,06 GiB de corpos por campanha, excluindo warm-ups; publicar todas, mediana/máximo por estrato |
| UP-LOAD | 3 premium distintos, projetos distintos, 500 MiB em simultâneo; 3 rodadas, alternância H/T fixada no manifesto | **9 tentativas** por campanha; pico simultâneo do grupo, tempos individuais e makespan. Não dividir o pico da rodada por 3 e chamá-lo pico individual |
| UP-COEXIST | Controlo sem upload e carga 500 MiB a 10 MiB/s, com 100 pedidos leves a 5/s por janela; 3 pares de janelas | Mesma rota/payload/keep-alive; pacing idêntico BF/MF; cenário separado dos tempos UP-NORMAL não limitados |
| AUTH/UPLOAD-NEGATIVE | 3 repetições de cada caso materializado, com controlo positivo da mesma operação e fixture reposta | Tentativas previstas/executadas/negadas/efeito observado; timeout/500/instrumento falhado não contam como proteção |
| WS | Cenários v1 já definidos; 3 janelas de 30 s steady-state por caso de carga, pré-carga fora da janela | Todos os joins, recusas, contextos vivos/reservados e eventos; sem p95/p99 a partir de 3 janelas |
| PKI/OPS/AR | 3 repetições por cenário de estado/falha automatizável; browser manual com passos e observação reproduzíveis | Datas/etapas/resultado por tentativa; não fabricar automação, aprovação ou recuperação real |
| REGRESSION | Suites existentes uma vez em BF e MF; cada fluxo integrado materializado 3 vezes, fala real pelo menos uma vez em cada campanha | Resultados por teste e skips/limitações explícitos; se houver nova falha/correção, repetir apenas o afetado e dependências relevantes |

UP-COEXIST acrescenta três uploads e 600 pedidos leves por campanha: em cada
par, 100 no controlo e 100 sob carga. Propor início dessa janela 5 s após o início
do corpo e conferir sobreposição efetiva; falha/fim antecipado do upload não é
janela completa sob carga. O total 100+9 não inclui coexistência, warm-ups,
segurança, fronteiras ou regressões; fechar o denominador completo no manifesto.

**Estados UP-NORMAL:** `process_restart` reinicia/recria os três serviços Node
medidos antes de cada tentativa, com prontidão confirmada fora do relógio;
`warm` usa um warm-up fixo de 10 MiB excluído e depois cinco tentativas consecutivas
por estrato. Dependências e caches do SO/SeaweedFS são identificados, não declarados
frios por reiniciar Node. Fixar ordem/reinicializações/keep-alive antes de BF e
repetir em MF; não limpar caches ou forçar GC só num lado. Contas/projetos e versões
ficam preparados antes de t0, com reposição equivalente entre casos.

Formatos/limites/falhas não são todos multiplicados pelo produto cartesiano de
UP-NORMAL; cada um tem um caso explícito no manifesto. A cobertura de 1024 MiB é
guarda funcional adicional à cobertura opcional anterior do catálogo, agora
selecionada individualmente; o seu esforço físico continua por verificar. Sem a executar, reportar precisamente
esse limite não avaliado, nunca suporte demonstrado a todo o máximo premium.

O [ciclo de vida dos uploads](architecture/fase2-upload-ciclo-vida.md) acrescenta
UL-01–UL-12 como casos planeados, não resultados. UP-C1/C2/C3 A estão selecionadas;
UP-C4–C9, números e mecanismos por verificar. Ambos os transportes precisam de
ensaios de recursos/falhas/compatibilidade; snapshots/candidatos podem aumentar
retenção acima do piso de 60 GiB, que tem de ser recalculado.

## 4. Cenários de segurança e falha

Os casos lógicos SEC-01–04 e WS-N1/J1/P1/L1–3/R1/B1/E1 mantêm o
[contrato v1](architecture/fase2-sessoes-identidade-partilhas-ws.md).
Os 10 WS-T e 12 AR são verificações complementares, não resultados já obtidos.

| Grupo | Preparação / estímulo | Evidência e métricas |
|-------|-----------------------|---------------------|
| EV-AUTH-PUBLIC | Dono/outro, owner ausente/único/coincidente/contraditório/multivalor, partilhas read/edit/revoked, conta/billing e ACL DELETE projeto vs media | Estado e bytes antes/depois, não só status; S01/S05/S06/S13–S15/U24/F04/F05 |
| EV-AUTH-INTERNAL | Cliente host e contentor não confiável; chamadas diretas projects/storage/users/subscriptions; par autorizado e par errado da mesma CA; Mongo/S3/broker | Separar rede, TLS, identidade de serviço e permissão de domínio. Cada célula PKI-C5 e cada principal, sem reduzir a um único worker; S02/S03/S07–S09/S14–S20 |
| EV-WS-NORMAL | WS-N1: 50 ligações/10 projetos×5; joins graduais até 5/s no gerador, 30 s estáveis após admissão | Cadência/filas/HTTP/s/avaliações/s/CPU/RSS/BD e cortes; S04/S10–S12/S21 |
| EV-WS-FAIR | WS-J1: 500 membros num projeto e dois de 5 =510; WS-P1: 40 projetos×5=200 | Separar espera/corte dos pequenos, grandes e por projeto. 4 concorrentes não provam 4/s nem limite de 20 projetos |
| EV-WS-LIMITS | 512→513 ligações; 4096→4097 contextos; 32→33 salas, 4→5 vias; 2048 buckets; taxas/bursts; fila 16 pendentes+4 ativos e novo pedido do mesmo projeto | Confirmar pré-condição viva+reservas no instante da tentativa. Excesso testa recusa controlada; não alegar carga admitida acima dos tetos. Preservar autorizações existentes; S10/S12/S21 |
| EV-WS-RACES | Revogação, acesso alternativo, JWT a expirar, projects indisponível/lento, respostas fora de ordem, leave/rejoin e eventos pessoais/de projeto | Atraso desde ACK da revogação, eventos após corte, prazo local desde início da consulta positiva; nunca renovar em falha. Emissão protegida também nas salas pessoais; S04/S06/S11–S13/S21/F04/F06 |
| EV-PKI | Renovação normal, retorno após >30 dias, retirada por nova CA, atualização parcial e compromisso com sockets/keep-alive/retomas e consumidores ativos | S20/F06: isolamento desde comando administrativo, não só reinício; recusa CA antiga e fluxos completos, incluindo WS→projects e projects→storage, antes de reabrir |
| EV-OPS | Trabalho imagem/vídeo/misto interrompido, débito ambíguo, editor executor, mudança de dia, crash/reaplicação da reconciliação e mensagem tardia | Evidência preservada antes de corrigir, zero duplicação de correção de quota, indeterminados fora dos confirmados; ferramenta executável por demonstrar; U21/U22/U24/F04/F06/F08/F10 |
| EV-SESS | SEC-01/02 e AR-01–12 com prova artificial de teste válida/incerta, destino errado, emissão ambígua e erro de importação/bootstrap | Mesma identidade/dados nas fixtures elegíveis; caso real sem prova continua pendente. Não consultar perfis reais ou alterar relógio do host; S06/S19/S20/F06 |
| EV-UP-STATE | Se adotado nginx/S3: PUT concorrente/replay, expiração, tamanho/key/Host falsos, revogação após emissão, confirmação repetida, falha PUT/confirm/hash/cleanup | Confirmar objeto/versionamento/visibilidade/associação e efeitos; 0 ready inválidos, hash/cache íntegros. Os TTL/códigos/retry esperados dependem das decisões abertas; S22–S24/U13–U16/U21–U26 |

Saturação pode causar recusa ou perda de disponibilidade; isso não dispensa corte
em ≤5 s nem permite estender autorizações. Se uma carga dentro dos tetos não for
sustentável, reportar falha de capacidade/cadência, não recusa por excesso fictícia.
Se nem se conseguir preparar 4096 contextos vivos, o teste de fronteira fica
inconclusivo ou com falha de preparação, não aprovado.

## 5. Recolha e relógios

1. Cada tentativa tem ID, fase BF/MF, cenário/fixture, repetição, commit/diff,
   hashes dos instrumentos, configuração efetiva sanitizada, digests/versões,
   PIDs/cgroups/início dos processos e perfil/quota inicial. TLS no cliente de
   medição usa confiança de teste conhecida; qualquer bypass necessário para
   caracterizar a base é separado e impede alegar validação TLS nesse controlo.
2. O cliente lê o ficheiro **em fluxo**. Os scripts históricos carregam cenários
   específicos e têm nomes fixos, promoção premium vulnerável e asserções incompletas;
   são fontes para adaptação, não um runner pronto. Gerador e coletor entram no
   budget e não devem alocar uma cópia integral de cada ficheiro em RAM.
3. Amostrar a cada 50 ms como proposta: RSS dos processos, subprocessos ffprobe,
   cgroup memória/CPU/I/O, nginx/SeaweedFS e memória agregada simultânea. Recolher
   `VmHWM` e `memory.peak` apenas com janela comprovada: cgroup novo ou reset
   suportado/verificado. Se não for possível, guardar pico de vida e amostragem
   como medidas distintas, com limitação. Verificar a versão cgroup/ficheiros
   disponíveis; não presumir que um kernel antigo oferece o reset atual.
4. CPU em segundos, bytes por fronteira, requests/ranges de ffprobe, temporários,
   sockets e filas são medidos até **hash e limpeza**. Cgroup pode incluir memória
   de ficheiros/cache; RSS Node não representa toda a RAM. Não somar máximos de
   instantes diferentes nem chamar à amostragem um pico exato. Incremento U01 é
   `max(RSS na janela) − RSS inicial`, por serviço e tentativa C=1; U20 regista
   o pico da rodada C=3. Reportar sempre RSS absoluto e retido após terminar
   hash/trabalho/limpeza normal e mais 10 s sem nova carga; ready com hash ainda
   ativo não é início de repouso para U02.
5. Usar relógio monotónico num mesmo observador para intervalos; UTC para
   correlação/proveniência. Se t_hash/corte vierem de outro processo, registar
   correlação e incerteza de transporte/amostragem. Se o observador só verificar
   periodicamente, reportar o intervalo possível e usar o limite superior ao
   decidir cumprimento. Uma medição que não distingue 2 s de 5 s não prova S12.
6. Para uploads: t0 antes do primeiro pedido de autorização/envio; t_send no envio
   completo do corpo pelo cliente; t_put na resposta ao corpo; t_ready na resposta
   após validação final; t_hash no hash persistido; t_cleanup no fim da limpeza.
   **U09 = t_ready − t_send**, incluindo confirmação; **U10 = t_ready − t0**;
   `t_complete = max(t_ready,t_hash)`. O finish do Node indica entrega ao sistema
   operativo, não receção no servidor. Se a resposta chegar antes do envio acabar,
   registar recusa antecipada/bytes efetivos, sem inventar pós-envio negativo.
7. Para S12, revogar por pedido com ACK observado e enviar eventos de teste
   sequenciados antes/depois. Distinguir decisão efetiva, última entrega, acesso
   alternativo e expiração local desde início da consulta positiva. Para S20,
   t0 é o comando administrativo antes de preflight/fila; fim só quando novos,
   persistentes, retomas e consumidores/efeitos estejam cortados. Falha não reinicia
   relógio: isolamento incompleto continua registado e a ação prossegue.
8. Timeouts e janelas são configuração do instrumento a congelar, não SLA da
   aplicação: proposta de 180 s por upload/validação normal, 180 s para observar
   falhas/recuperação e limpeza até TTL+60 s após fechar o TTL. Interromper novas
   submissões perante risco de recursos, preservar evidência e isolar apenas o
   ensaio. Tentativa interrompida/timeout não desaparece do denominador.

Referências de método: [kernel — cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html),
[kernel — proc](https://docs.kernel.org/filesystems/proc.html),
[Docker — limites de recursos](https://docs.docker.com/engine/containers/resource_constraints/),
[Compose — nome do projeto](https://docs.docker.com/compose/how-tos/project-name/),
[Node — ClientRequest finish](https://nodejs.org/api/http.html#event-finish).
Suporte efetivo das versões locais ainda por verificar; consultar a documentação
da versão congelada antes de executar os instrumentos.

## 6. Mínimos, metas e cobertura das 60 métricas

Os valores por ID no [catálogo](fase2-metricas-e-baseline.md) são a fonte
canónica. **V** é escolha individual já validada; **E** é proposta a rever; **F**
é origem documental com o cenário original. O manifesto fixa a revisão/hash do
catálogo e a aprovação de cada critério misto. Os mínimos de zero/100% referem-se
ao corpus finito, não a segurança universal ou taxas populacionais.

| Dimensão / IDs | Mínimo de trabalho | Meta de trabalho | Estado |
|---------------|-------------------|------------------|--------|
| Autorização S01–S04/S10/S11/S14/S15/S22–S24 | 0 efeitos/eventos indevidos; 100% controlos legítimos correspondentes | Mesmo limite | E; políticas individuais aplicáveis preservadas. D11/upload depende de contrato final |
| Perfil JWT/mTLS/dados S06–S09/S16/S17/S19 | 0 admissões fora do perfil/matriz e 0 novos segredos expostos; chamadas legítimas sem falha | Mesmo limite | Políticas C/V, asserções E. S07 aceita reutilização pelo mesmo peer/contexto dentro da validade; não é um gate zero replay geral |
| Corte WS S12 | ≤5 s; local ≤5 s desde início de consulta positiva, limitado por JWT/permissão; falhas não renovam | ≤2 s | **V**, ainda sem resultado experimental |
| ACL/links S13 e funcionais S05/F01–F06 | 100% dos casos afetados, incluindo dono elimina projeto/editor remove media e links até revogação | Mesmo limite | Políticas selecionadas; cobertura finita proposta, sem inventar concordância coletiva |
| PKI S20/F06 | Isolamento ≤30 s; 0 aceitações CA retirada e todos os controlos legítimos antes de reabrir | Isolamento ≤10 s | **V**; duração da substituição por medir, sem prazo 15/5 min presumido |
| Sobrecarga S21/F07 | Mediana adicional em pedido leve ≤10 ms | ≤5 ms | **E**; parâmetros WS de timeout/fila/estado são escolhas anteriores, não capacidade demonstrada |
| Memória Node U01/U02 | Incremento e retenção ≤64 MiB por serviço em C=1 até 500 MiB | ≤32 MiB | **V em EVAL-M1**, origem E; por amostra/estrato, sem esconder falhas na média |
| Memória total U03/U04 | 0 OOM; nginx +≤128 MiB / SeaweedFS +≤256 MiB em C=1 | +≤64 / +≤128 MiB | **V em EVAL-M1**, origem E; reportar agregado/C=3, sem herdar o incremento C=1 |
| Pós-envio U09 | <3000 ms por amostra válida de 500 MiB, não só a mediana | <1000 ms | **V em EVAL-M1**, origem F/ensaio selecionado; até ready, sem mudança de relógio. PAD usa MiB, explicitar bytes face a MB do PDF |
| Total U10 / coexistência U25 | Mediana ≤1,10× controlo equivalente; 0 falhas nos pedidos leves | ≤controlo | **V em EVAL-M1**, origem E; U10 compara BF/MF válidos. U25 agora G compara pares na mesma fase; falha de BF não cria rácio fictício |
| Preflight/validação U11–U13 | Preflight ≤500 ms; validação real e U09 cumpridos; I/O/timeout do probe limitados e declarados | Preflight ≤200 ms; decompor fases | **E**; U11/U12 são D, valores de preflight são referências, não gates próprios; U13 G exige limites do probe ainda por fechar |
| Hash/cache U14–U16 | Mesmo SHA-256/0 trocas; se assíncrono, hash até 10 s após ready | Até 5 s após ready | **V em EVAL-M1**, origem E; prazo por ficheiro até 500 MiB C=1/C=3 inclui fila. Original mantém SHA; output segue F02. Cache desativada ou isolada |
| Válidos/negativos U17–U19 | 100% casos corretos; sem token recusar com ≤8 MiB adicionais no gateway | Recusa ≤100 ms após cabeçalhos | **E/F** conforme catálogo; medir cliente lento sem permitir body buffer oculto |
| Concorrência U20 | 3/3 premium 500 MiB sem OOM/reinício e íntegros | Cumprir nas 3 rodadas | **V em EVAL-M1**, origem E; registar todas as rodadas, não parar no primeiro sucesso |
| Temporários/estado U08/U21–U24/U26 | Limpeza 0 órfãos após TTL+60 s; associação/confirm/quota corretas e falhas/retry definidos; disco ≤C×(F+16 MiB) por componente | TTL+10 s; sem spool integral no percurso nginx/S3 e overhead ≤16 MiB por upload | **V só U22 em EVAL-M1**; demais E mantidos. F é tamanho nesta fórmula; TTL/uso único/compatibilidade ainda abertos |
| Disponibilidade F08 | 0 quedas no corpus válido; se supervisor alterado, retoma ≤30 s | Retoma ≤10 s | **E**; não confundir com prazo PKI nem recuperação correta de jobs |
| Diagnóstico S18/U05–U07/F07/F09 | Configuração/alcance, inclinação memória, CPU, rede, overhead e extensão reportados | Explicar custos e efeitos colaterais | Sem alvo artificial; manter restrição D5 conforme seleção |
| Reprodutibilidade F10 | Cada gate com cenário, instrumento, fixture/hash, ambiente, bruto e asserção; 0 segredos nos entregáveis | Mesmo limite | E; NM impede fecho e NA exige mecanismo novo/justificação |

Um NM num gate P/G impede o respetivo fecho. Diagnósticos D sem observação recebem
NM e justificação, sem inventar um limiar de aprovação; isso não dispensa a recolha
explicitamente necessária para explicar custos adiados e os efeitos colaterais.
A inclusão de F07 em sobrecarga e diagnóstico é intencional: o gate temporal é
S21/U10; o handshake frio/quente de F07 é decomposição, sem novo limite próprio.
Para U01 C=3, não aprovar por inferência um limite de 64 MiB por upload baseado
em dividir a memória do grupo; reportar agregado e U20 separadamente.

Não há limiar numérico obrigatório para CPU-segundos/bytes de rede se ainda não
existe justificação. Recolher e analisar esses custos é obrigatório ao explicar
o hash adiado; uma melhoria só de RSS Node que aumenta o pico total pode falhar
as guardas mesmo cumprindo U01.

## 7. Artefactos, aprovação e execução futura

O [manifesto vazio](templates/phase2-evaluation-manifest.template.json) contém
os 60 IDs e separa anfitrião escolhido de runtime/corpus/criterios ainda não
congelados. O [modelo de resultado](templates/phase2-evaluation-result.template.json)
tem valores nulos; não é um ensaio, schema validador ou relatório preenchido.
Completar cópias por campanha. Um runner futuro deve recusar `template_only: true`,
manifesto não congelado, gates sem critério aprovado ou hash de fixture ausente.

Cada cenário concreto tem estímulo, estado inicial, operação/rota/verbo/canal,
controlo positivo, efeito esperado, método de observação, métricas e preparação/
reposição. Uma lista de nomes de cenários sem estas condições não congela a matriz.
Guardar dados privados em diretório protegido, fora de Git/build e perfis reais;
publicar apenas manifestos sanitizados e brutos sem credenciais, URLs assinados,
dados de contas reais ou chaves. Hashes de fixtures são de ficheiros públicos de
teste, não de segredos de baixa entropia.

**Sequência proposta:**

1. Concretizar instalação EVAL-I1, as condições de EVAL-B1/C1/R1/M1 A já
   selecionadas e os pontos de upload ainda abertos; preencher os casos/manifesto.
   Não pedir novamente host ou A/A/A/A; seleção não congela o runtime.
2. Preparar configuração isolada e instrumentos, corrigir asserções históricas
   G02/D05/D06/G08/G09 e fixtures premium. Verificar preparação e orçamento com
   um piloto de instrumento; resultados de calibração não entram em BF.
3. Congelar BF: commit inicial de aplicação, diff permitido só de preparação/
   instrumentação declarado, digests, dependências, configuração, corpus, ordem,
   relógios, amostras e critérios. O HEAD de documentação não substitui a revisão
   de aplicação identificada no relatório. Congelar também o protocolo MF.
4. Executar BF **antes de refactoring de aplicação**. Cada P/G tem valor/falha
   observada ou NA justificado para mecanismo inexistente; o efeito equivalente
   continua a ser medido. Uma falha medida da base é evidência, não NM. Serviço
   ausente/instrumento sem asserção suficiente deixam o caso inconclusivo.
5. Apresentar requisitos completos e revisão do Inception nos checkpoints
   aplicáveis. Este plano não os aprova nem gera unidades, histórias ou bolts.
6. Após autorização da fase apropriada, implementar e executar MF com o protocolo
   congelado. Se uma necessidade obrigar a mudar hardware/budget/corpus/método,
   justificar a versão nova e repetir BF/MF comparáveis; não escolher apenas o
   melhor subconjunto final. Aceitar resultados negativos no relatório.

| Marco de planeamento | Data proposta / condição |
|----------------------|--------------------------|
| Plano, recursos e revisão de propostas | 18–20/11, disponibilidade da equipa ainda desconhecida |
| Instrumentos/manifesto e BF | 20–21/11, antes de aplicação alterada e após decisões/critério congelados |
| Piloto operacional PKI | **Até 23/11 às 18:00 Europe/Lisbon/UTC**, marco anterior mantido; requer ferramentas/canais prontos |
| Repetição final e regressões | 24–25/11, se implementação e pré-condições estiverem prontas |
| Análise/reprodutibilidade/relatório | 26/11; entrega 27/11, hora ainda desconhecida |

O calendário é proposta dependente de esforço/implementação, não compromisso dos
quatro elementos. Se o piloto PKI não estiver pronto até ao marco, registar atraso
e a capacidade não demonstrada. Se houver piloto válido antes de 27/11, registar
instalação/carga/duração da substituição e o critério contextual medido; não
inventar SLA geral nem reabrir sem os controlos. Não reduzir silenciosamente
cobertura, ocultar falhas ou usar os dados reais para cumprir o calendário.

## 8. Análise, relatório e apresentação

Por ID/cenário publicar **baseline / mínimo / meta / final / diferença absoluta /
diferença relativa / resultado / limitação / referência do bruto**. Menor é melhor
para memória/tempos: `redução % = 100×(BF−MF)/BF`, só com BF válido e não zero.
Zero→zero ou mecanismos novos recebem diferença absoluta/NA justificado, sem
percentagem infinita. Agregar por estrato equivalente; nunca misturar B14/B16/BF
ou estados quentes/reiniciados. Denominador inclui falhas e tentativas previstas
não executadas identificadas à parte.

Estados de conclusão: **cumpre mínimo e meta**, **cumpre mínimo**, **falha mínimo**,
**inconclusivo/NM** ou **NA justificado**. Intervalo de medição que cruza o limiar
fica inconclusivo; não arredondar para o aprovar ou imputar falha à aplicação. Meta falhada não apaga um mínimo cumprido;
mínimo falhado não é aprovado por uma boa média. Não publicar p95/p99 dos pequenos
grupos de 3–5; para pedidos leves com 100 amostras, um p95 é apenas exploratório,
com n/erros e valores brutos. Não tirar conclusão estatística populacional.

Avaliar os RNF separadamente: QC-06 usa casos de acesso/eventos/PKI e controlos
legítimos; QC-05 usa recursos/tempos e preservação dos uploads. Como ambos mudam
na MF, o ganho global não identifica sozinho a contribuição causal de cada
refactoring. Medir overhead mTLS/WS e decomposição de uploads; uma campanha
intermédia de ablação só entra mediante plano/baseline próprios, não é condição
implícita nem prova já feita.

Respostas a preparar para a defesa: porquê este host e budget; porquê 64/32 MiB;
porquê t_ready em vez de PUT; quanto custa o hash posterior; como foi detetado um
falso 2xx ou serviço ausente; porque 513 é recusa e 510 pode ser falha de capacidade;
como se preservaram funcionalidades/dados; que metas não foram atingidas. Citar
as alternativas e custos nos [documentos de decisões](fase2-ideias-1-e-2.md), sem
afirmar igualdade de segurança em falha nem factos sem medição.

**IA e validação:** preparação apoiada por Codex com a skill Inception; leitura de
fontes/PDF e metadados do host, elaboração de protocolo/modelos e verificação
documental. A equipa continua responsável pela revisão. Nesta tarefa não houve
upload, ataque, falha induzida, arranque Docker, alteração da aplicação, sessão,
PKI ou volume. Métricas de aplicação novas continuam NM.

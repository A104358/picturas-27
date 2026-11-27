#import "../template.typ": *

= Alternativas e Matriz de Comparação

== Alternativas consideradas

#tab([Alternativas consideradas],
  tabela(
    colunas: (1.6cm, 3.4cm, 1fr, 3cm, 2.4cm),
    tamanho: 8.5pt,
    [ID], [Nome / padrão], [Descrição breve], [Mantém ou altera o padrão global?], [Fonte],
    [ALT-1], [Microserviços por efeito de vídeo / _Pipes and Filters_ distribuído], [`projects` passa a coordenar etapas de vídeo em serviços e filas separados, à semelhança das imagens. Cada etapa recebe uma referência para o vídeo completo. Não se enviam fotogramas pelas filas existentes.], [Mantém microserviços, RabbitMQ, _gateways_ e S3, altera granularidade/orquestração. Com ficheiros completos entre serviços, a execução é também *Batch Sequential* na terminologia dos slides.], [EV-03, EV-15, EV-31, EV-36, H-01, H-03, H-04],
    [ALT-2], [_Competing Consumers_ / _pool_ replicado de workers de vídeo], [Várias instâncias consomem `video_queue`, cada uma executando um _pipeline_ completo com _prefetch_ 1. Réplicas e recursos ajustam-se à carga.], [Mantém o padrão global e a organização interna do vídeo, altera a topologia/capacidade operacional.], [EV-03, EV-09, EV-16, EV-31, H-02, H-08, H-12],
  ),
)

== Análise de cada alternativa

*ALT-1: Microserviços por efeito de vídeo / _Pipes and Filters_ distribuído*

#tabela-campos(
  [Coerência com o padrão global], [Reproduz a decomposição das ferramentas de imagem e a coordenação central de `projects`. Continua a usar mensagens com referências para ficheiros. Não exige alterar o modelo de projeto nem transformar o sistema em coreografia. Com saída materializada entre efeitos, é um _pipeline_ distribuído de execução Batch Sequential, não um _stream_ incremental entre serviços. (EV-14, EV-15, EV-31, EV-36)],
  [Efeito nos atributos de qualidade], [Modularidade de implantação potencialmente superior e escalabilidade por efeito, latência/I\/O potencialmente piores. Recuperação por etapa é possível se houver estado persistente/idempotência. Mais serviços não melhoram automaticamente segurança ou usabilidade. São previsões, não resultados medidos. (H-01, H-03–H-08)],
  [Vantagens potenciais], [Dependências de Whisper separáveis das dos filtros simples. Alteração e recursos de cada etapa isoláveis. Uma falha pode repetir só a etapa se o seu _input_ estiver preservado. (H-03, H-04, H-08)],
  [Desvantagens ou riscos], [Formatos intermédios comprimidos podem alterar os fotogramas por recodificação sucessiva, formatos sem perdas aumentam I\/O/armazenamento. Exige preservar áudio e semântica temporal, sobretudo nas fronteiras de legendagem e extração. Introduz novos contratos, pontos de falha, limpeza e agregação de progresso. (EV-17–EV-21, H-01, H-03)],
  [Custo e risco de migração (a funcionalidade existente tem de ser preservada)], [*Elevados, estimativa qualitativa.* Extrair funções puras, definir contratos de entrada/saída e intermediários, criar serviços/filas, adaptar `projects`/tokens/progresso e regressão. Tratar a extração como saída de cardinalidade variável e preservar o _no-op_ da legendagem. Medir primeiro o caminho atual. (EV-05, EV-12, EV-14, EV-17–EV-21, H-01, H-03, H-04)],
)

*ALT-2: _Competing Consumers_ com _pipeline_ completo por worker*

#tabela-campos(
  [Coerência com o padrão global], [Aproveita a fila e o consumidor já existentes. O comentário do worker prevê paralelismo por réplicas. O RabbitMQ distribui os trabalhos pelos consumidores da mesma fila. Cada vídeo continua a ter um só _pipeline_ e não passa a ser executado em paralelo entre efeitos dependentes. (EV-03, EV-16, EV-31)],
  [Efeito nos atributos de qualidade], [Capacidade/débito potencialmente melhores com recursos livres. Não reduz necessariamente o tempo de execução de um vídeo. Não elimina custo de Whisper nem modifica a modularidade interna. Fiabilidade continua dependente das janelas de _ack_/publicação/persistência, há novos riscos de concorrência. (H-02–H-04, H-08, H-12)],
  [Vantagens potenciais], [Mantém a passagem ordinária única e reutiliza os testes do processador. Vários vídeos de projetos distintos podem avançar sem aguardar pelo mesmo consumidor, respeitando um orçamento de CPU/RAM. Menor mudança de contratos do que ALT-1. (EV-16–EV-18, H-02, H-08)],
  [Desvantagens ou riscos], [Cada processo carrega o seu modelo na RAM. Mais processos competem por CPU, disco e _broker_. Os caminhos atuais são por projeto/_media_, não por execução: dois _Apply_ podem colidir. A fila única continua sem isolamento de tarefas pesadas/_previews_, e segurança/estado do cliente ficam iguais. (EV-09, EV-14, EV-19, EV-23, EV-24, H-02, H-08, H-12)],
  [Custo e risco de migração], [*Médios, estimativa qualitativa.* Aumentar réplicas é simples. Torná-las seguras exige isolamento por execução, idempotência, testes de concorrência e recursos limitados. _Autoscaling_ exige política, métricas e controlo adicional. O risco não se reduz a executar `--scale video_tool=2`. (EV-09, EV-14–EV-16, H-02, H-03, H-12)],
)

== Matriz de comparação de padrões

#paisagem[
#tab([Matriz de comparação de padrões],
  tabela(
    colunas: (5.6cm, 4.2cm, 4cm, 4cm, 4cm),
    tamanho: 8.5pt,
    [Atributo de qualidade (ISO/IEC 25010)], [Padrão global atual (referência)], [Padrão atual do vídeo], [ALT-1], [ALT-2],
    [Relação com o padrão global], [Referência: microserviços + REST/mensagens + orquestração. (EV-03, EV-07–EV-10, EV-14)], [Segue transporte/domínio, afasta-se da granularidade de imagens. (EV-12, EV-15, EV-16)], [Mantém, aproximando a granularidade de vídeo da de imagens. (EV-15, EV-31, H-04)], [Mantém, mudando número/gestão de instâncias. (EV-09, EV-16, EV-31, H-02)],
    [Eficiência de desempenho: comportamento temporal], [M: filas desacoplam o pedido, mas múltiplos saltos e preparação S3 permanecem. Sem latência medida. (EV-14, EV-15)], [M: passagem ordinária única, mas serialização e estágios adicionais criam espera. (EV-16–EV-20, H-08)], [B, estimado: etapas Batch Sequential materializam intermediários, aumentando potencialmente a latência individual. (EV-17, EV-31, H-01)], [M, estimado: preserva execução por vídeo. Pode reduzir espera de fila, sem prometer aceleração individual. (EV-16, EV-17, H-02, H-08)],
    [Eficiência de desempenho: capacidade / elasticidade], [M: serviços separados permitem decompor carga. Não há _autoscaling_ nem partilha de _host_. (EV-09, EV-33)], [B: um trabalho ativo por instância, CPU de reconhecimento partilhada. (EV-09, EV-16, EV-19)], [A, estimado: recursos/réplicas ajustáveis por efeito, sujeitos a custo de intermediários e capacidade do _host_. (H-01, H-08)], [A, condicionado: vários vídeos em paralelo com recursos e política de escala, efeito pode desaparecer por saturação. (EV-09, EV-16, H-02, H-12)],
    [Fiabilidade: tolerância a falhas / recuperabilidade], [B: _auto-ack_ de imagens e confirmação antecipada, filas duráveis não bastam. (EV-15, EV-30, H-03)], [M: _ack_ manual e saída local temporária, mas erros tratados não são repetidos e falta garantia distribuída. (EV-16, EV-17, EV-21, H-03)], [M, estimado: repetir etapa pode limitar retrabalho, mais transições exigem estado/idempotência. (EV-15, EV-21, H-03)], [M, estimado: outra réplica pode receber pedido não confirmado, somam-se conflitos de ficheiros. (EV-16, EV-21, H-03, H-12)],
    [Manutenibilidade: modularidade / modificabilidade], [M: serviços independentes, mas orquestrador concentrado e contratos partilhados. (EV-09, EV-10, EV-15)], [M: funções/módulos internos existem. Implantação conjunta e PIL duplicado limitam autonomia. (EV-18–EV-20)], [A, estimado: implantação/dependências por efeito, em troca de maior esforço em contratos e orquestração. (H-04)], [M, estimado: processador e duplicação mantêm-se, topologia operacional ganha complexidade. (H-04)],
    [Segurança: confidencialidade / integridade / autenticidade], [B: JWT/cifra no percurso normal coexistem com portas internas publicadas, _headers_ internos confiados e TLS sem validação. (EV-08, EV-11, EV-24)], [B: herda essas fronteiras. Validação local não substitui autenticação entre serviços. (EV-16, EV-21, EV-24)], [B, estimado: novos serviços ampliam contratos/superfície sem medidas próprias. (EV-24, H-07)], [B, estimado: replicar distribui acesso ao mesmo volume e modelos, requer controlo independente. (EV-09, EV-24, H-07, H-12)],
    [Usabilidade: operabilidade], [B: _overlay_, acompanhamento local e erros de algumas ferramentas limitam operação. (EV-15, EV-23)], [B: percentagem visível, mas sem retoma no _browser_ ou interrupção real ao cancelar. (EV-16, EV-23, EV-25, H-10)], [B, estimado: mudar o _backend_ não resolve _overlay_/_refresh_. Agregar progresso de etapas acrescenta trabalho. (EV-22, EV-23, H-06)], [B, estimado: espera pode melhorar, mas interface, cancelamento e persistência de progresso ficam iguais. (EV-23, EV-25, H-02, H-06)],
  ),
)
]

== Adequação do padrão atual

O padrão global é adequado para preservar a génese do PictuRAS: projetos, filtros encadeados, lote e serviços de negócio já integrados. 

O worker concentrado é uma escolha plausível para o MVP de vídeos curtos, porque evita distribuir fotogramas e recodificar entre efeitos comuns. A adequação diminui para vários vídeos concorrentes e cargas de reconhecimento: a implantação tem um único consumidor e estágios com custos diferentes. 

A ALT-1 interessa sobretudo à modularidade e ao isolamento de dependências, com risco elevado para latência e equivalência dos resultados. A ALT-2 é uma candidata mais próxima da organização atual para capacidade, mas exige demonstrar recursos disponíveis, concorrência segura e melhoria de espera/débito.  

Nenhuma das duas resolve automaticamente os problemas de segurança, progresso persistente, _overlay_ ou cancelamento. A equipa selecionou segurança ponta a ponta e recursos no _upload_ (capítulo 6), pelo que ALT-1 e ALT-2 permaneceram alternativas de evolução, sem implementação nesta fase.

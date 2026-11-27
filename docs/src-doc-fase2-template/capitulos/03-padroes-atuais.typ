#import "../template.typ": *

= Padrões Arquiteturais da Solução de Base

A análise seguinte descreve a realização dos padrões em `0523102`. Os riscos de segurança e de memória motivaram os dois RNF; a sua resolução na fase 2 é avaliada nos capítulos 8–10. A organização do processamento de vídeo mantém-se na entrega final.

== Padrão global da solução

#tabela-campos(
  [Nome(s) do padrão / estilo], [*Microservices com API Gateway*, comunicação *REST + Event-Driven*, orquestração centralizada em `projects` e *Pipes and Filters* como composição de transformações, realizada em parte como *Batch Sequential*. Organização interna parcialmente *Layered* e relações *Client–Server/N-Tier* na vista de _runtime_. (EV-03, EV-07–EV-10, EV-14, EV-15, EV-35, EV-36)],
  [Descrição], [O nginx encaminha os pedidos para o _frontend_ e os _gateways_. Os serviços de negócio mantêm dados próprios e comunicam por REST. O RabbitMQ transporta comandos de processamento, respostas e eventos, com `projects` como coordenador. Dentro dos serviços existem rotas, controladores e modelos, mas o grande módulo de rotas de `projects` também executa lógica de negócio e infraestrutura: não é uma separação estrita de camadas.],
)

#tab([Decisões globais que condicionam o vídeo],
  tabela(
    colunas: (4.5cm, 2.6cm, 1fr),
    [Decisão global], [Evidência], [Efeito no vídeo],
    [Entrada normal por nginx, JWT no gateway], [EV-07, EV-08], [O vídeo reutiliza autenticação e encaminhamento. O corpo pode atingir 1100 MiB no nginx e é integralmente recebido nos serviços com `memoryStorage`.],
    [Dados de negócio separados por serviço], [EV-09, EV-10], [Perfil/quota exigem chamada a `users`, projeto/execução/resultado pertencem a `projects`. Não existe uma transação única entre quota, broker, S3 e MongoDB.],
    [Mensagens com IDs de correlação], [EV-14, EV-16, EV-33], [O _pipeline_ não ocupa um pedido HTTP durante toda a edição. As respostas devem ser correlacionadas com um `Process` existente.],
    [_Pipeline_ e processamento em lote por projeto], [EV-10, EV-12, EV-14], [Vídeos e imagens partilham efeitos comuns. Só `trim` e `speed` são selecionados por vídeo. Alterar este modelo seria uma mudança funcional.],
    [S3 persistente e volume de trabalho partilhado], [EV-09, EV-11, EV-14], [Originais/resultados vivem em S3. Os workers recebem caminhos em `image_data`. Replicar entre _hosts_ exigiria disponibilizar esses ficheiros sem presumir que um volume local é distribuído.],
    [Compose numa rede _bridge_, sem política de autoscaling], [EV-09], [O vídeo é um serviço com uma instância por omissão. Escalar implica também capacidade física e tratamento de concorrência.],
    [Progresso encaminhado por `wsGateway`], [EV-22, EV-23], [O vídeo herda a entrega de eventos, mas o cliente mantém o acompanhamento em memória e não recebe histórico após _refresh_.],
  ),
)

#tab([Benefícios e desafios do padrão global],
  tabela(
    colunas: (2cm, 1fr, 4.2cm, 2.4cm),
    tamanho: 8.5pt,
    [Tipo], [Descrição], [Característica / subcaracterística (ISO/IEC 25010)], [Facto / hipótese],
    [Benefício], [Serviços e ferramentas com implantação separada permitem alterar uma ferramenta sem reconstruir todos os serviços. A independência real é limitada pelos contratos e pelo volume comuns.], [Manutenibilidade: modularidade/modificabilidade], [EV-09, EV-15, EV-33, inferência estrutural.],
    [Benefício], [Pedidos de processamento usam filas e conclusão assíncrona, evitando manter a ligação HTTP durante toda a transformação.], [Eficiência de desempenho: utilização de recursos, usabilidade: operabilidade], [EV-14, EV-22, não implica que a interface esteja livre.],
    [Benefício], [Separação `src`/`out`, persistência de projetos e resultados por execução favorecem a preservação do original e a apresentação de resultados identificáveis.], [Fiabilidade: recuperabilidade, adequação funcional: correção funcional], [EV-10, EV-11, EV-21, EV-28.],
    [Desafio], [`projects` concentra validação, quotas, encadeamento, S3, _cache_, partilha e tokens num ficheiro de rotas com 2732 linhas. O número de linhas evidencia concentração, não mede por si só a manutenibilidade.], [Manutenibilidade: modularidade/analisabilidade], [EV-10, EV-14, EV-15, esforço de alteração a avaliar em H-04.],
    [Desafio], [Ferramentas Python de imagem usam `auto_ack=True`. A correlação dos erros é inconsistente. O consumidor de respostas de `projects` confirma a mensagem sem aguardar a conclusão do _callback_ assíncrono.], [Fiabilidade: tolerância a falhas/recuperabilidade], [EV-15, EV-30, risco de perda a reproduzir em H-03.],
    [Desafio], [Receção integral de _uploads_ em três serviços e composição de ZIP em memória podem pressionar a RAM com ficheiros grandes.], [Eficiência de desempenho: utilização de recursos/capacidade], [EV-08, EV-11, EV-12, EV-21. Dimensão do impacto por medir em H-05.],
    [Desafio], [Há portas internas publicadas, confiança em _headers_ internos e validação TLS desativada. A proteção do _gateway_ não cobre todos os percursos possíveis.], [Segurança: confidencialidade/integridade/autenticidade], [EV-24, extensão explorável a verificar em H-07.],
  ),
)

== Padrão do processamento de vídeo

#tabela-campos(
  [Nome do padrão], [*Work Queue com consumidor único por implantação e _pipeline_ monolítico local*: um _Pipeline Monolith_ dentro dos microserviços. O caminho ordinário processa _frames_ incrementalmente. As fronteiras que materializam ficheiros completos entre estágios são *Batch Sequential*. Tem módulos internos, mas uma única unidade de implantação. (EV-03, EV-09, EV-16–EV-20, EV-36)],
  [Descrição], [`video_queue` entrega um vídeo e a sua sequência ao `video_tool`. `prefetch_count=1` e execução bloqueante limitam cada instância a um trabalho de cada vez. O worker lê ficheiros partilhados, processa estágios ordenados, publica progresso/resposta e só depois confirma o consumo. O Compose não configura réplicas nem _autoscaling_. (EV-09, EV-16)],
  [Contraste com o caminho de imagens], [Nas imagens, a sequência atravessa serviços por ferramenta e volta a `projects` entre etapas. No vídeo, a sequência é executada no interior do worker, sem mensagens por efeito/fotograma. Isto não torna toda a aplicação monolítica. (EV-14–EV-20)],
)

#tab([Benefícios e desafios do padrão do vídeo],
  tabela(
    colunas: (2cm, 1fr, 4.2cm, 2.4cm),
    tamanho: 8.5pt,
    [Tipo], [Descrição], [Característica / subcaracterística (ISO/IEC 25010)], [Facto / hipótese],
    [Benefício], [No caminho ordinário, uma passagem de descodificação alimenta todos os efeitos PIL e uma codificação produz o MP4. Não há intermediários de vídeo por efeito comum.], [Eficiência de desempenho: comportamento temporal/utilização de recursos], [EV-17, EV-18, vantagem temporal face a ALT-1 ainda em H-01.],
    [Benefício], [`trim` limita a janela lida. `speed` reescala os tempos e ajusta o áudio com `atempo`, entrada e saída ficam separadas.], [Eficiência de desempenho: utilização de recursos, adequação funcional: correção funcional], [EV-17, EV-27.],
    [Benefício], [Escrita temporária e `os.replace` só publicam a saída local completa em execuções normais. Exceções tratadas limpam temporários e preservam o original.], [Fiabilidade: tolerância a falhas], [EV-17, EV-19, EV-20, EV-27. Não é garantia contra SIGKILL nem transação S3/MongoDB.],
    [Benefício], [_Ack_ manual permite a reentrega de pedido não confirmado quando a ligação/worker cai. É mais apropriado para trabalhos demorados do que _auto-ack_.], [Fiabilidade: recuperabilidade], [EV-16, EV-30, recuperação de ponta a ponta por validar em H-03.],
    [Desafio], [Um vídeo ou uma transcrição ocupa o único consumidor. Novos vídeos e _previews_ partilham a mesma fila. A espera sob carga é hipótese de impacto, embora a serialização por instância seja verificável.], [Eficiência de desempenho: capacidade/comportamento temporal], [EV-09, EV-16, EV-19, H-02 e H-08.],
    [Desafio], [Efeitos comuns, legendagem e extração partilham dependências, processo e implantação, `effects.py` duplica operações PIL dos serviços de imagem.], [Manutenibilidade: modularidade/modificabilidade], [EV-18–EV-20, impacto no esforço em H-04.],
    [Desafio], [Erros tratados também terminam com _ack_, sem retentativa automática, `heartbeat=0`, publicação sem confirmações nem marca de persistência explícita. _Callback_ de respostas não aguardado pelo consumidor Node.], [Fiabilidade: tolerância a falhas/recuperabilidade], [EV-15, EV-16, EV-30, H-03.],
    [Desafio], [Cancelar invalida a execução em `projects`, mas não interrompe o FFmpeg/Whisper. Só há reembolso de operações avançadas de imagem.], [Usabilidade: operabilidade, eficiência de desempenho: utilização de recursos], [EV-25.],
  ),
)

== Relação entre o padrão global e o padrão do vídeo

#tab([Relação entre o padrão global e o padrão do vídeo],
  tabela(
    colunas: (2.4cm, 3cm, 3cm, 1.9cm, 2.6cm, 1.8cm),
    tamanho: 8pt,
    [Aspeto], [O que o padrão global prescreve], [O que o vídeo faz], [Segue / afasta-se], [Consequência], [Evidência],
    [Entrada e domínio], [_Gateways_ e _pipeline_ por projeto], [Reutiliza os mesmos projetos, identidade, versão e quota], [Segue], [Preserva o processamento em lote e o modelo de partilha/presets.], [EV-08, EV-10, EV-12, EV-25],
    [Transporte de trabalhos], [Filas e IDs de correlação], [Acrescenta `video_queue`, responde em `project_queue`], [Segue], [Integração no mecanismo assíncrono existente.], [EV-14, EV-16, EV-33],
    [Granularidade dos filtros], [Nas imagens, um serviço por ferramenta], [Todos os efeitos de vídeo no mesmo serviço], [Afasta-se], [Menos comunicação por etapa. Menor isolamento de implantação entre efeitos de vídeo.], [EV-15, EV-17–EV-20],
    [Orquestração], [`projects` coordena cada etapa de imagem], [`projects` coordena o lote. Worker coordena os estágios do vídeo], [Segue no lote, afasta-se nas etapas], [A lógica de progressão está dividida entre dois níveis. Novos tipos de saída exigem cuidados em ambos.], [EV-14, EV-15, EV-17, EV-21],
    [Ficheiros], [S3 persistente + volume de trabalho], [Lê/escreve caminhos em `image_data`], [Segue], [Replicação no mesmo _host_ reutiliza o volume. Múltiplos _hosts_ exigem outra garantia de acesso.], [EV-09, EV-11, EV-14],
    [Fiabilidade de consumo], [Imagens com _auto-ack_ nos _helpers_ comuns], [Vídeo com _ack_ manual e _prefetch_ 1], [Afasta-se, com intenção de maior recuperabilidade], [Reentrega torna-se possível, mas duplicação, persistência de mensagens e confirmação final ainda exigem análise.], [EV-15, EV-16, EV-30],
    [Progresso], [Eventos de conclusão/etapa para WS], [Acrescenta percentagem por vídeo], [Segue e estende], [Mantém o _gateway_, o estado visual continua dependente da sessão do _browser_.], [EV-22, EV-23],
  ),
)

O vídeo herda autenticação no acesso normal, quotas, projetos persistentes, armazenamento e distribuição de eventos. O domínio impõe efeitos comuns por projeto e compatibilidade com imagens. O volume partilhado restringe a liberdade de distribuição física. O desvio na granularidade evita uma troca de mensagens e ficheiros por efeito, mas reúne tarefas heterogéneas no mesmo consumidor. Daqui resultam oportunidades de melhoria de capacidade e modularidade. Os ganhos quantitativos de uma alternativa permanecem hipóteses, não propriedades automáticas de um padrão.

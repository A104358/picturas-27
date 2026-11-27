#import "../template.typ": *

#paisagem[
= Trade-offs, Cenários de Qualidade e Prioridades

== Cenários de qualidade para a extensão de vídeo


#tab([Cenários de qualidade],
  tabela(
    colunas: (1.2cm, 3.4cm, 2.6cm, 2.2cm, 2.2cm, 2.4cm, 2.2cm, 2.6cm, 3cm),
    tamanho: 7.5pt,
    [ID], [Fragilidade na base (EV-nn)], [Característica (ISO/IEC 25010)], [Fonte do estímulo], [Estímulo], [Artefacto], [Ambiente], [Resposta], [Medida da resposta],
    [QS-01], [Proteção do _gateway_ não cobre todas as identidades/rotas/armazenamento/WS, efeitos indevidos verificados (EV-24, EV-43)], [Segurança: confidencialidade, integridade e autenticidade], [Cliente de outra conta ou _peer_ interno sem identidade/permissão exigida], [Apresentar pedido de acesso/operação sobre recurso de projeto sem autorização efetiva, incluindo entrada numa sala de projeto], [Fronteiras nginx/_gateways_, `projects`, `users`/`subscriptions`, _storage_/S3 e admissão WS], [Instalação isolada, _fixtures_ dono/editor/leitor/outro. Uma operação/rota/contexto por caso, com controlo legítimo correspondente], [Verificar identidade e autorização, recusar acesso/efeito/entrada indevidos e preservar a operação legítima do controlo], [Por caso: tentativas, admissões e efeitos de domínio/bytes/eventos verificados. Fração de efeitos indevidos sobre tentativas e sucessos legítimos sobre controlos. Recusas de rede/TLS/domínio e erros internos separados, sem contar 500/_timeout_ como proteção. EV-24/EV-43, H-14],
    [QS-02], [Buffers integrais em três Node. Pressão/retenção/OOM e aceitação lenta em pilotos (EV-08, EV-11, EV-42)], [Eficiência de desempenho: utilização de recursos, comportamento temporal como guarda], [Utilizador _free_/premium legitimamente autorizado], [Enviar vídeo válido de tamanho crescente, isolado ou com outros _uploads_], [Percurso nginx → _gateway_ → `projects` → _storage_/S3, incluindo validação, _hash_ e limpeza], [Mesmo _host_, recursos e corpus de teste BF/MF, C=1 e C=3 separados], [Aceitar e disponibilizar apenas o ficheiro validado/associado corretamente, limitando recursos e mantendo pedidos leves utilizáveis], [Por serviço/janela: RSS absoluto/adicional/retido, memória _cgroup_/agregada, CPU/rede/disco, OOM/reinícios. $t_"ready" − t_"send"$, $t_"ready" − t_0$, $t_"hash"$ e _cleanup_. SHA-256 do original e respostas corretas. EV-08/EV-11/EV-42, H-15/H-17/H-18],
    [QS-03], [Único consumidor de vídeo. CPU de reconhecimento partilhada (EV-16, EV-19)], [Eficiência de desempenho: capacidade/comportamento temporal], [Dois utilizadores com projetos distintos], [Submeter reconhecimento de fala e, durante esse trabalho, um vídeo curto com efeito comum], [`video_queue`, `video_tool` e orquestrador], [_Budget_ fixo, fala real/modelo identificado, carga mista], [Concluir corretamente os trabalhos e tornar observável a espera/consumo], [Tempos de fila/execução/_commit_ por vídeo, conclusões válidas por minuto, CPU/RSS e integridade de áudio. Cenário para avaliar H-02/H-08, sem meta numérica criada aqui.],
    [QS-04], [Janelas de _ack_/publicação/persistência sem garantia distribuída (EV-15, EV-21, H-03)], [Fiabilidade: tolerância a falhas/recuperabilidade], [Falha controlada do worker/_broker_/orquestrador], [Interromper numa fronteira de execução/persistência identificada], [Filas, `Process`/`Result`, fontes, saídas e quota de um lote], [_Fixtures_ descartáveis com estados antes/depois conhecidos, controlo sem interrupção], [Manter originais/último resultado confirmado e classificar recuperado/falhado/indeterminado sem duplicar efeitos], [Pedidos aceites, resultados corretos/duplicados/parciais/pendentes, diferenças de quota, tempo observado de recuperação.],
    [QS-05], [PIL duplicado em `effects.py`, regras comuns espalhadas (EV-18, EV-27, H-04)], [Manutenibilidade: modificabilidade/testabilidade], [Programador em tarefa controlada], [Corrigir uma regra já existente de parâmetro/validação comum a imagem e vídeo], [Efeitos PIL, validação/orquestração e testes], [Mesmo requisito/correção em base e protótipo, sem novo efeito funcional], [Alterar a regra coerentemente sem regressões fora do âmbito], [Tempo da tarefa, módulos/serviços/contratos alterados, reconstruções e resultados de regressão.],
    [QS-06], [_Overlay_ local sem retoma. Cancelamento sem interrupção real (EV-22, EV-23, EV-25, H-06)], [Usabilidade: operabilidade], [Utilizador com processamento já submetido], [Tentar acompanhar e continuar a operar o editor durante o trabalho], [_Frontend_, estado de tarefa e eventos WS existentes], [Projeto imagem/vídeo/misto, tarefa e corpus iguais], [Tornar compreensíveis estado/erros e preservar as operações já existentes], [Sucesso/erros/tempo de tarefas e compreensão do estado. _Overlay_ e _reload_ observados, não dados como resolvidos.],
    [QS-07], [Permanência WS não segue o contrato de revogação proposto (EV-22, EV-44, EV-46, H-14, H-18)], [Segurança: confidencialidade e integridade], [Proprietário autorizado do projeto], [Revogar a última via de partilha que autoriza um membro já ligado a receber eventos do projeto], [Autorização de domínio em `projects` e emissão de eventos no `wsGateway`], [Instalação isolada, membro previamente admitido com JWT ainda válido, fluxo de eventos sequenciados], [Retirar receção protegida do projeto afetado quando a autorização efetiva cessar], [Intervalo em ms entre ACK da revogação e corte verificado. Eventos protegidos entregues após o limite aplicável. Novas entradas indevidas e controlos preservados.],
  ),
)
]

#tab([Priorização dos cenários],
  tabela(
    colunas: (1.6cm, 4.8cm, 4.8cm, 2cm),
    [ID], [Importância para os _stakeholders_], [Dificuldade / risco técnico], [Prioridade],
    [QS-01], [Alta: donos/colaboradores dependem de confidencialidade e integridade, há efeitos indevidos verificados], [Alta: atravessa identidades/APIs/dados/admissão WS sem impedir clientes legítimos], [1],
    [QS-07], [Alta: retirar uma partilha deve retirar a receção que dela depende. É política já selecionada, não terceiro RNF], [Alta: permanência, corridas, falhas e eventos pessoais precisam de observação temporal], [1 (complemento de CAND-1)],
    [QS-02], [Alta: carregar vídeo é entrada do fluxo central. RAM/OOM afeta todos os clientes do _gateway_], [Alta: dois transportes, estado/_storage_, validação e custo adiado, preservando contratos], [2],
    [QS-04], [Alta: perda/duplicação/quota comprometem a confiança], [Alta: várias fronteiras de falha], [3],
    [QS-06], [Média-alta: impacto direto na operação, faltam ensaios com participantes], [Média-alta: cliente/estado/eventos e delimitação de alterações visíveis], [4],
    [QS-05], [Média: sustentabilidade da evolução], [Média-alta: esforço empírico comparável e compatibilidade dos contratos], [5],
    [QS-03], [Média-alta: espera de trabalhos concorrentes, condicionada pelo uso local], [Alta: competição CPU/RAM/Whisper e colisões sob réplicas, não selecionada para implementação], [6],
  ),
)

== Atributos de qualidade por ordem de prioridade

+ *Segurança*: QS-01 e complemento QS-07, CAND-1: proteger acesso e permanência no domínio existente, prioridade do par comunicado.
+ *Eficiência de desempenho*: QS-02, CAND-2: utilização de recursos no _upload_, QS-03 é contexto de capacidade, não requisito incluído na entrega.
+ *Fiabilidade*: QS-04: preservar resultados/quota e tratar falhas dos percursos alterados.
+ *Usabilidade*: QS-06: não obter ganhos à custa de bloquear a interação ou tornar erros/reconexão inexplicáveis.
+ *Manutenibilidade/testabilidade*: QS-05: limitar duplicação de regras e tornar as mudanças auditáveis.

== Pré-requisitos e efeitos colaterais entre atributos

#tab([Pré-requisitos e efeitos colaterais entre atributos],
  tabela(
    colunas: (2.8cm, 2.8cm, 4cm, 1fr),
    [Atributo A], [Atributo B], [Efeito (pré-requisito, sinergia ou conflito)], [Razão / evidência],
    [Segurança], [Eficiência de desempenho], [Pré-requisito e conflito], [Autorização antes do corpo evita trabalho indevido. TLS, assinatura e revalidações consomem recursos e podem aumentar latência. Medir ambos. EV-08/EV-24/EV-44, H-14/H-18],
    [Eficiência do _upload_], [Segurança], [Pré-requisito], [Retirar o corpo dos Node exige que o acesso S3 não contorne a autorização e que _pending_ não seja utilizável. EV-11/EV-44, H-15],
    [Segurança], [Disponibilidade], [Conflito], [Falha de `projects` impede novas entradas WS. _Leases_ não se renovam em erro. É política escolhida, não igualdade de segurança/disponibilidade provada. EV-44, H-14],
    [_Streaming_/hash posterior], [Fiabilidade], [Conflito a controlar], [Erros/respostas perdidas podem deixar objetos/_journals_ ambíguos. _Hash_ em falta exige tratamento de _cache_. EV-11/EV-26/EV-44, H-16],
    [Manutenibilidade], [Desempenho], [Sinergia e conflito], [Regras comuns evitam divergência entre adaptador e transporte novo, mais intermediação/contratos pode aumentar custo. EV-10/EV-18/EV-44, H-04/H-17],
    [Fiabilidade], [Usabilidade], [Sinergia], [Estados/erros/reconexão explícitos ajudam a compreender a tarefa, mas não criam biblioteca nem _refresh_ automático. EV-23/EV-44, H-06],
    [Capacidade por réplicas], [Recursos/fiabilidade], [Conflito], [Mais consumidores replicam modelos e disputam ficheiros. Ganho precisa de isolamento e recursos. EV-16/EV-19, H-02/H-12],
  ),
)

== Recomendações de melhoria à solução atual



#tab([Recomendações de melhoria],
  tabela(
    colunas: (1fr, 2.6cm, 3cm, 1.8cm, 2.2cm),
    tamanho: 8.5pt,
    [Recomendação], [Atributo(s)], [Padrão a que se refere], [Esforço], [Risco de regressão],
    [Realizar as fronteiras de identidade/autorizações e permanência WS já selecionadas, com controlos positivos e proteção das chaves], [Segurança, com guardas temporais/disponibilidade], [Global, vídeo herda APIs/eventos/_storage_], [Alto], [Alto: todos os callers legítimos precisam de ser preservados, H-14/H-17],
    [Realizar o percurso nginx/S3 e adaptador limitado, preservando quota e _staging_ controlado], [Eficiência, segurança e fiabilidade], [Global/entrada do vídeo, sem distribuir _frames_], [Alto], [Alto: UP-C4–C9 fechadas a 21/11 antes de implementar (EV-50), H-15–H-18],
    [Calibrar e congelar BF, corpus/instrumentos e critérios aplicáveis antes do _refactoring_], [Testabilidade e ambos os RNF], [Global e integração], [Médio], [Médio: preparação, não melhoria já medida, EV-45],
    [Manter ALT-1/ALT-2 como alternativas documentadas, sem as implantar nesta seleção], [Modularidade/capacidade], [Vídeo dentro do padrão global], [Alto/médio], [Alto/alto: estimativas herdadas, H-01–H-04/H-12],
  ),
)

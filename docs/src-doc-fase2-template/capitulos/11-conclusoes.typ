#import "../template.typ": *

= Conclusões e Recomendações

#orientacao[
  *Origem:* Exercício 6, Bloco 2, secção 6 do _template_.

  Sintetizem os contributos do relatório, sem repetir o conteúdo dos capítulos anteriores: o que o diagnóstico concluiu
  sobre a adequação do padrão atual, que otimizações sugerem e que considerações ficam para a evolução futura.

  Terminem com o que ficou por fazer e porquê (e.g., valores-alvo não atingidos, hipóteses por confirmar) e com a
  ligação à Fase 3: de que forma o _refactoring_ facilita, ou não, a integração de novas funcionalidades. Sejam realistas e honestos quanto às limitações da
  análise e às hipóteses que ficaram por confirmar.
]

== Adequação do padrão atual (global e do vídeo)

O padrão global (microserviços com _gateway_, REST mais mensagens e orquestração em `projects`) mostrou-se adequado aos dois RNF escolhidos. Ambos foram cumpridos sem mudar o padrão: na MF oficial todas as métricas principais e guardas cumprem, a maior parte no alvo e a U01 e a U04 no mínimo (capítulo 10, EV-55). As fragilidades estavam na *realização* do padrão, não na sua forma. Na segurança, o _gateway_ era o único ponto de verificação e o resto da rede confiava em portas publicadas, _headers_ e TLS sem validação. No _upload_, o corpo atravessava três serviços Node em memória. A correção foi verificar em cada fronteira e separar o caminho dos bytes do caminho de controlo, mantendo os mesmos serviços, filas e contratos públicos.

O padrão do vídeo (consumidor único com _pipeline_ completo por mensagem) não foi alterado nem precisou de o ser para estes RNF: as melhorias atuam antes dele (entrada do ficheiro) e à volta dele (identidade, credenciais e eventos). Continuam válidas as conclusões do diagnóstico sobre o que este padrão não resolve: um único consumidor, custos heterogéneos na mesma fila (QS-03), confirmação antecipada nas ferramentas de imagem (QS-04) e concentração de lógica em `projects` (QS-05). ALT-1 e ALT-2 continuam alternativas documentadas, sem evidência nova a favor de uma delas.

== Sugestões de otimização

- *Memória do SeaweedFS (U04 no mínimo).* O pico restante é memória viva do SeaweedFS 4.47, não do nosso código. Vale a pena medir uma versão mais recente ou outro servidor S3 com o mesmo passo U04 antes de aceitar o valor como definitivo.
- *Memória do `img_storage` (U01 no mínimo).* O adaptador do POST antigo ainda passa por _buffers_ por parte _multipart_ no `img_storage`. Escrever o candidato diretamente a partir da `projects`, ou reduzir o tamanho das partes, pode aproximar a U01 do alvo de 32 MiB. A medir, porque partes menores aumentam pedidos ao S3.
- *Corte absoluto do PUT direto.* A limitação da decisão 39 pode fechar-se com um relé de contagem também no PUT (como o do `ffprobe`) ou com um módulo do nginx que limite a duração total, trocando parte do ganho de memória por controlo.
- *Fluxo novo como único caminho.* O _frontend_ já usa o PUT direto. O POST antigo mantém-se por compatibilidade e para a comparação com a BF (D-06). Retirá-lo, depois de um período de transição, elimina um transporte e os estados de que depende.
- *Bomba de _hash_.* Hoje trata uma tentativa por segundo, a mais antiga. Com mais carga, processar várias tentativas dentro das vagas existentes reduz o tempo até o _hash_ ficar disponível, sem mudar o contrato.
- *Confirmação antecipada (OPS-C1).* O defeito conhecido do _auto-ack_ das ferramentas de imagem não foi corrigido nesta fase. É a otimização de fiabilidade com maior impacto que fica por fazer.

== Considerações para evolução futura

- *O custo de acrescentar um serviço subiu.* Um serviço ou chamada interna nova precisa de certificado da PKI, de uma entrada na matriz D4 (mTLS por par), de uma linha na matriz de rotas (verificada por `b4-route-matrix.py`) e, se usar dados, de um principal com privilégio mínimo em MongoDB, RabbitMQ ou S3. É mais trabalho, mas é explícito e testado.
- *Eventos WS exigem contexto de projeto.* Qualquer evento novo para o cliente tem de levar o `projectId`, ou é descartado pela autorização da sala.
- *Operação da PKI.* Os certificados de serviço duram 30 dias e a CA 365, a renovação (`ops/pki.sh renew`, aos 7 dias) passa a ser uma tarefa recorrente, e retirar um certificado interrompe a instalação inteira (PKI-C2 B).
- *Escala do vídeo.* As réplicas do `video_tool` (ALT-2) não dependem do motor de _upload_, mas cada evento de progresso que emitam tem de levar o contexto do projeto e passa pelos limites do `ws_gateway`. Distribuir por vários _hosts_ continua a exigir substituir o volume partilhado `image_data`.
- *Medição como rede de segurança.* O `med.py` e a suíte de conformidade (`tests/conformance/run-b12.sh`) ficam no repositório e repetem-se a cada alteração relevante. A experiência das duas MF mostra que, com 5 amostras por estrato num portátil, as guardas de tempo em ficheiros pequenos são sensíveis ao ruído do _host_: campanhas futuras devem correr com o _host_ em repouso ou com mais repetições.

== Trabalho futuro

*O que ficou por fazer e porquê:*
- *Alvos não atingidos.* A U01 (45,4 MiB, alvo 32) e a U04 (SeaweedFS +142,6 MiB, alvo 128) cumprem só o mínimo. As causas e as pistas estão na secção anterior.
- *Limitações declaradas.* Ficam declaradas, e não escondidas:
  - o PUT direto sem corte absoluto de 600 s (decisão 39, com compensações)
  - os tetos WS (512/4096, filas e taxas) e as 3 vagas de _upload_, que são valores configurados e ensaiados, não capacidade demonstrada
  - o `mem_limit` de 512 MiB do `ws_gateway`, sem medição acima do corpus de carga
  - as chaves antigas no histórico Git
  - o logout e a mudança de _password_, que não invalidam um JWT já emitido até ao `exp` (SESS-C1)
  - a identidade interna, reutilizável pelo _peer_ autorizado durante 30 s (JWT-C1)
  - um _link_ de partilha divulgado, válido até ser revogado
  - o _ack_ antecipado (OPS-C1)
  - a amostragem a 100 ms da U08.
- *Não repetido na verificação final.* Os três pilotos de PKI (B10), que correm numa instalação separada, e os testes de acesso direto do B2, que usavam portas entretanto retiradas. As suas aceitações e as métricas S16/S17 da MF cobrem esses pontos.
- *Fora das métricas oficiais.* O fluxo novo (PUT direto) é provado pela conformidade e por medições EXP, não pela comparação BF/MF (D-06).
- *Observação sem causa determinada.* Numa EXP completa, um de três _uploads_ concorrentes de 500 MiB recebeu 500 aos 111 s, sem OOM nem reinício. Não se reproduziu em 24 ensaios na stack de desenvolvimento nem nas duas MF (3/3 rondas em ambas).
- *Hipóteses por confirmar.* H-01 a H-13 dizem respeito a cenários e alternativas fora do âmbito desta fase (QS-03 a QS-06, ALT-1, ALT-2) e continuam por confirmar.

*Ligação à Fase 3.* O _refactoring_ facilita a integração de funcionalidades novas em dois pontos. As regras de segurança passaram a ser explícitas e verificáveis por fronteira (matrizes de rotas e de pares, testes de conformidade), o que reduz o risco de uma funcionalidade nova abrir um acesso indevido sem que os testes o detetem. O motor de _upload_ (tentativas, vagas, candidato imutável e limpeza) é reutilizável para outros tipos de _media_ grandes. Em contrapartida, cada funcionalidade nova paga o custo de entrar nessas matrizes. Funcionalidades pesadas de vídeo (mais IA, transcrição) continuam limitadas pelo consumidor único do `video_tool`, que esta fase não alterou: é aí que a ALT-2 e o cenário QS-03 voltam a ser relevantes.

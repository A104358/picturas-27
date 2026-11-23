#import "../template.typ": *

= Vista Arquitetural Antes e Depois

#orientacao[
  *Origem:* Exercício 7, secção 4 do _template_.

  Duas vistas do mesmo diagrama: *antes* e *depois* das decisões. Usem o tipo de diagrama que melhor mostrar a alteração
  (componentes, implantação ou sequência). Destaquem os elementos ou as interações introduzidos ou alterados pelas
  táticas (com um estereótipo `«tática: …»` ou uma cor) e incluam uma *legenda*.

  As duas vistas devem ser comparáveis: mesma notação, mesma escala e os mesmos elementos de contexto, de modo a que a
  diferença se perceba a olho. A legenda e as notas explicam o que mudou entre elas e porquê.
]

== Antes

#figure(kind: image,
  image("../images/vista_antes.png", width: 100%),
  caption: [Vista arquitetural da base `0523102`, antes das decisões DA-1 e DA-2 (Mermaid, `before.mmd`, revista a 23/11; EV-07–EV-12, EV-22, EV-24, EV-40, EV-46, EV-49)],
)

Vista parcial dos percursos de _upload_, identidade e mensagens da base. O gateway recebe o ficheiro inteiro antes de verificar o JWT; `projects` e `img_storage` também usam _buffers_ integrais. O nginx pode usar disco para o corpo do pedido, e o `ffprobe` da `projects` usa um temporário. HTTPS interno sem validar servidor significa certificado remoto não verificado, mantendo a cifra. A quota é debitada no _Apply_, não no _upload_.

O RabbitMQ está separado dos workers: encaminha pedidos pelas filas de imagem/`video_queue`, resultados por `project_queue` para `projects` e eventos por `ws_queue` para `ws_gateway`. A própria `projects` também publica eventos. Ligações e eventos Socket.IO passam pelo nginx nos dois sentidos; não há consulta WS → `projects` nesta base. O caminho público `/s3/` também passa pelo nginx e não é o percurso do _upload_ multipart. Frontend, MongoDB/backup, volumes e canais IA ficam na vista global do Bloco 1. A revisão e os comandos de renderização estão em `docs/exercises/07-architectural-tactics/evidence/before-view-review-2026-11-23.md`.

== Depois

#figure(kind: image,
  image("../images/vista_depois.png", width: 100%),
  caption: [Vista arquitetural depois das decisões DA-1 e DA-2 (Mermaid, `diagrams/after.mmd`; EV-44, EV-45, EV-50; H-14–H-18)],
)

A vista «depois» representa o *desenho selecionado*, ainda não implementado. Os elementos a verde são as realizações das táticas escolhidas, previstas mas não em execução. Os elementos a cinzento/tracejado são os mecanismos UP-C4–C9 (estado, tentativa, candidato, _hash_ e limpeza), selecionados a 21/11 (EV-50) e ainda por implementar.

== Legenda e notas

#tab([Legenda das vistas antes/depois],
  tabela(
    colunas: (4cm, 1fr),
    [Cor / estilo], [Significado],
    [Vermelho (vista antes)], [Fragilidade do percurso: _buffer_ integral/temporários, certificado interno não validado, storage sem autenticação e WS com JWT opcional e sem autorização/permanência de projeto. Não significa falha de cada pedido.],
    [Verde sólido (vista depois)], [Realização das táticas TAT-01–04 (fronteiras/WS) e TAT-08/09 (percurso de bytes/adaptador); *previsão*, não em execução.],
    [Cinzento/tracejado (vista depois)], [UP-C4–C9: estado, tentativa, candidato, _hash_ e limpeza — selecionados (opção A em todos), por implementar.],
    [`«tática: …»` (anotação)], [Indica qual tática introduz ou altera o elemento/interação representados.],
  ),
)

As duas vistas usam Mermaid para os percursos de _upload_, controlo e mensagens; a vista antes tem disposição vertical para manter a legibilidade no relatório e explicita separadamente o broker e os workers. A comparação mostra: (1) substituição do _buffer_ integral por _proxy_ nginx/S3 com adaptador de compatibilidade (TAT-08/09); (2) autenticação mTLS/RS256 nas APIs internas e TLS validado nos restantes canais (TAT-01/03); (3) autorização de domínio em `projects` e consulta de _join_/revalidação no WS (TAT-02/04). O _payload_/contexto dos eventos WS tem de ser adequado para autorizar emissões em salas pessoais e de projeto; o tracejado não demonstra esse mecanismo pronto. Certificados/identidade não substituem autorização de operação ou objeto. EV-44/EV-45; H-14–H-18.

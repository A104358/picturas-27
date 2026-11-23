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
  caption: [Vista arquitetural antes das decisões DA-1 e DA-2 (Mermaid, `diagrams/before.mmd`; EV-07–EV-12, EV-22, EV-24, EV-40, EV-46, EV-49)],
)

Vista parcial das interações relevantes para as duas decisões. Mantém-se a vista global do Bloco 1 (`arquitetura_global_plantuml.svg`) para os restantes serviços/volume. Os elementos assinalados a vermelho têm fragilidades de código sem afirmar falha de cada pedido.

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
    [Vermelho (vista antes)], [Fragilidade identificada: _buffer_ integral, TLS sem validação, WS sem autorização de projeto.],
    [Verde sólido (vista depois)], [Realização das táticas TAT-01–04 (fronteiras/WS) e TAT-08/09 (percurso de bytes/adaptador); *previsão*, não em execução.],
    [Cinzento/tracejado (vista depois)], [UP-C4–C9: estado, tentativa, candidato, _hash_ e limpeza — selecionados (opção A em todos), por implementar.],
    [`«tática: …»` (anotação)], [Indica qual tática introduz ou altera o elemento/interação representados.],
  ),
)

As duas vistas usam a mesma notação Mermaid (_flowchart LR_) e os mesmos serviços de contexto. A diferença visual mostra: (1) substituição do _buffer_ integral por _proxy_ nginx/S3 com adaptador de compatibilidade (TAT-08/09); (2) autenticação mTLS/RS256 nas APIs internas e TLS validado nos restantes canais (TAT-01/03); (3) autorização de domínio em `projects` e consulta de _join_/revalidação no WS (TAT-02/04). O _payload_/contexto dos eventos WS tem de ser adequado para autorizar emissões em salas pessoais e de projeto; o tracejado não demonstra esse mecanismo pronto. Certificados/identidade não substituem autorização de operação ou objeto. EV-44/EV-45; H-14–H-18.

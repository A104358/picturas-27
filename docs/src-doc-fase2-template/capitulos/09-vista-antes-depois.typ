#import "../template.typ": *

= Vista Arquitetural Antes e Depois

== Antes

#figure(kind: image,
  image("../images/vista-antes-final.svg", width: 100%),
  caption: [Vista arquitetural da base, antes das decisões DA-1 e DA-2],
)

As setas indicam relações lógicas; pedidos/respostas e notificações Socket.IO regressam através do nginx.

Vista parcial dos percursos de _upload_, identidade e mensagens da base. O gateway recebe o ficheiro inteiro antes de verificar o JWT. `projects` e `img_storage` também usam _buffers_ integrais. O nginx pode usar disco para o corpo do pedido, e o `ffprobe` da `projects` usa um temporário. HTTPS interno sem validar servidor significa certificado remoto não verificado, mantendo a cifra. A quota é debitada no _Apply_, não no _upload_.

O RabbitMQ está separado dos workers: encaminha pedidos pelas filas de imagem/`video_queue`, resultados por `project_queue` para `projects` e eventos por `ws_queue` para `ws_gateway`. A própria `projects` também publica eventos. Ligações e eventos Socket.IO passam pelo nginx nos dois sentidos. Não há consulta WS → `projects` nesta base. O caminho público `/s3/` também passa pelo nginx e não é o percurso do _upload_ multipart. Frontend, MongoDB/backup, volumes e canais IA ficam na vista global do Bloco 1. A revisão e os comandos de renderização estão em `docs/exercises/07-architectural-tactics/evidence/before-view-review-2026-11-23.md`.

== Depois

#figure(kind: image,
  image("../images/vista-depois-final.svg", width: 100%),
  caption: [Vista arquitetural depois das decisões DA-1 e DA-2, tal como implementada (SVG, EV-52, EV-55)],
)

A vista «depois» representa o que foi *implementado* e medido na MF (capítulo 10), e não apenas o desenho selecionado a 21/11. Os elementos a verde foram introduzidos ou alterados pelas táticas e pertencem à versão medida. Os elementos cinzentos mantêm a função principal; o tracejado representa a consulta WS → `projects`. O estado do _upload_ (UP-C4–C9, opção A) é uma coleção e um motor dentro da `projects`, não um serviço novo. Face ao desenho selecionado, a vista acrescenta o que a implementação concretizou ou alterou (capítulo 8, desvios): o PUT direto passa pelo nginx com `auth_request` e URL assinado, sem corpo em nenhum serviço Node. O adaptador do POST antigo grava diretamente uma chave de candidato nova (D-16). A `projects` lê o objeto em janelas de 4 MiB para o `ffprobe` e o _hash_ (D-17, D-24). O _master_, o _volume_ e o _filer_ do SeaweedFS ficam só em _loopback_ (D-19). O exchange passa a `topic` com permissões por _routing key_ (D-18), e os eventos em `ws_queue` levam o `projectId` (D-25), o que permite ao `ws_gateway` autorizar cada emissão.

== Legenda e notas

#tab([Legenda das vistas antes/depois],
  tabela(
    colunas: (4cm, 1fr),
    [Cor / estilo], [Significado],
    [Vermelho (vista antes)], [Fragilidade do percurso: _buffer_ integral/temporários, certificado interno não validado, storage sem autenticação e WS com JWT opcional e sem autorização/permanência de projeto. Não significa falha de cada pedido.],
    [Verde sólido (vista depois)], [Elementos introduzidos ou alterados pelas táticas TAT-01–04 (fronteiras/WS) e TAT-08/09 (percurso de bytes/adaptador). Implementados (EV-52) e medidos na MF (EV-55).],
    [Cinzento / seta tracejada], [Cinza: contexto funcional preservado; tracejado: autorização WS por consulta à `projects`. As tentativas, as vagas, o hash posterior e a limpeza pertencem ao motor dentro da `projects` (TAT-10/TAT-12).],
  ),
)

As duas vistas são SVG vetoriais com a mesma escala, disposição e elementos de contexto. Explicitam separadamente broker e workers. O caminho novo do corpo é nginx → S3; o POST legado segue nginx → gateway → projects → storage → S3 em fluxo. Os acessos a users/subscriptions desenhados são um resumo das integrações do gateway e da projects. A comparação mostra: (1) substituição do _buffer_ integral por _proxy_ nginx/S3 com adaptador de compatibilidade (TAT-08/09). (2) autenticação mTLS/RS256 nas APIs internas e TLS validado nos restantes canais (TAT-01/03). (3) autorização de domínio em `projects` e consulta de _join_/revalidação no WS (TAT-02/04), com os eventos a levar o contexto do projeto. Só o nginx publica uma porta. Certificados e identidade não substituem a autorização de operação ou objeto, que continua na `projects`. Ficam declaradas as limitações do capítulo 8: o PUT direto sem corte absoluto de 600 s (decisão 39) e os tetos WS, que são configurados e não capacidade demonstrada. EV-52/EV-55, H-14–H-18.

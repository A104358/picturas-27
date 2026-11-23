#import "../template.typ": *

= Decisões Arquiteturais

#orientacao[
  *Origem:* Exercício 7, secção 3 do _template_.

  Uma decisão por cenário (`DA-1` para `QS-01`, `DA-2` para `QS-02`). Cada decisão é um pequeno registo, ao estilo ADR: o
  contexto, a tática escolhida, a estrutura ou padrão que a realiza, as alternativas consideradas e a razão da sua
  rejeição, as consequências positivas e negativas, e os elementos arquiteturais afetados.

  Só vale a pena registar uma decisão se havia *alternativas reais* (as táticas do capítulo 7 que não foram escolhidas).
  Justifiquem a escolha pelo cenário e pelas restrições da fase: rejeitem as táticas de classe C, porque a fase é de
  _refactoring_, e avaliem o risco de regressão do âmbito da alteração.

  *Depois de implementada*, completem cada decisão com as referências da implementação (_commits_ ou _pull requests_ no
  repositório entregue) e com os desvios face ao que foi decidido, explicando porquê. A vista «depois» do capítulo 9
  deve corresponder ao que foi efetivamente implementado.
]

== DA-1 — Verificar confiança e autorização em cada fronteira (cenário QS-01; QS-07 complementar)

#tab([Decisão arquitetural DA-1],
  tabela-campos(
    [Contexto], [CAND-1/QS-01: portas/_headers_/TLS e WS permitem contornar verificações; efeitos conhecidos em EV-43. Preservar edição, partilha, imagem/vídeo, quota e _billing_, sem tratar a presença de serviços como prova de proteção. EV-24/EV-43; H-14],
    [Tática(s) escolhida(s)], [TAT-01 + TAT-02 + TAT-03 + TAT-04, como síntese das decisões existentes D3/D4/D6/D7 e ACL; não nova aprovação da equipa. Cadeia: EV-24/EV-43 → CAND-1 → QS-01/QS-07 → TAT-01–04 → DA-1 → S01–S21/guardas → BF/MF. EV-44],
    [Estrutura / padrão que a realiza], [_Gateway_ como fachada e `projects` como autoridade de domínio; mTLS nas APIs internas com autorização de serviço/operação; TLS validado/credenciais mínimas nos restantes canais. JWT HS256 utilizador e RS256 contextual interno têm funções distintas. WS consulta `projects` por _join_/revalidação; PKI local/retirada de confiança conforme contratos selecionados.],
    [Alternativas consideradas e razão de rejeição], [*TAT-05 isolada:* menor intervenção, mas _gateway_/_loopback_ não impedem impersonação/ação indevida do _peer_ interno. *TAT-06:* pode retirar consultas do caminho de entrada, mas acrescenta emissão/validade/invalidação de credenciais de sala; a consulta atual foi escolhida em D6.2 B. *TAT-07:* rejeitada C, pois biblioteca nova não é _refactoring_ desta fragilidade. EV-24/EV-43/EV-44; H-14],
    [Consequências positivas], [Cobrir pedidos diretos, identificar _peer_/contexto, autorizar operação e retirar receção quando a permissão cessar. São previsões H-14/H-18, não resultados. EV-44],
    [Consequências negativas / riscos], [Mais configuração, certificados/chaves e consultas; novos _joins_ indisponíveis em falha; intervenção na renovação de sessões anónimas; custo de revogação/isolamento e risco de recusar _caller_ legítimo. _Claims_ curtas não dão _exactly-once_ nem uso único; cópias de JWT têm residual registado. Prova anónima real continua desconhecida. EV-44/EV-45; H-14/H-17/H-18],
    [Elementos arquiteturais afetados], [nginx, `apiGateway`/auth/rotas, `wsGateway`, `projects`/_caller_/_middleware_/rotas, `users`, `subscriptions`, `imageStorageService`, clientes Mongo/S3/_broker_, `Tools/expand_ai` e `generative-mock`, Compose/PKI/segredos e _frontend_ de sessão/reconexão. É cobertura por canal, não só trocar um algoritmo.],
    [Origem e âmbito do _refactoring_], [Global/interação: vídeo herda as mesmas APIs, dados, quota e eventos. Não muda efeitos nem formato de vídeo; alto risco de regressão nas operações legítimas. Testar imagem, vídeo, mistos e duas vias de acesso. EV-09/EV-14/EV-21/EV-44],
    [Classe (A/B/C)], [*B no conjunto; núcleo interno A.* Corrigir _owner-only_ para eliminar projeto e explicitar corte/reconexão muda comportamento visível como objeto da segurança, sem criar nova capacidade de edição. A restrição DELETE não é regra herdada inequívoca; está explicitamente escolhida e precisa de justificação/teste. O editor continua a remover _media_. EV-39/EV-44],
    [Implementação (_commits_ / _pull requests_)], [Branch `fase2-refactor`: `02623a4` (B0 — _spikes_ SP-01 a SP-11, imagens fixadas às da BF) e `1ab09fa` (B1 — PKI por instalação e segredos fora do Git). Blocos B2–B5 e B8–B11 por implementar à data desta versão. EV-51. #preencher[completar com os _commits_ finais]],
    [Desvios face à decisão], [Até ao B1, sem desvio à DA-1. Concretizações decididas depois dos _spikes_ (EV-51): o exchange `picturas` passa de `direct` a `topic`, para limitar a publicação de cada principal por _routing key_ (D-18); _master_, _volume_ e _filer_ do SeaweedFS só em _loopback_ e retirada da rota `/s3-console/` (D-19), porque o mTLS interno do SeaweedFS aceita qualquer certificado da CA. Limitação declarada: o histórico Git mantém as chaves antigas (não foi reescrito). Sem migração de sessões (_reset_ geral, EV-50). #preencher[completar no fim da implementação]],
  ),
)

== DA-2 — Separar controlo de bytes e limitar recursos mantendo o contrato (cenário QS-02)

#tab([Decisão arquitetural DA-2],
  tabela-campos(
    [Contexto], [CAND-2/QS-02: _buffers_ integrais e validação/_hash_ provocam picos/retenção e pós-envio elevado em alguns pilotos. Preservar limites/perfis, conteúdo, nome/versão, edição/_preview_/_export_ e quota. EV-08/EV-11/EV-42; H-15],
    [Tática(s) escolhida(s)], [*Núcleo TAT-08 + TAT-09*, conforme preferência nginx/S3 e UP-C1 A, com UP-C2 A e UP-C3 A como condições: adaptador seguro, quota só no _Apply_ e _pending_ isolado. TAT-10/TAT-12 realizam-se pelas escolhas UP-C4–C9 A, fechadas a 21/11 antes de implementar (EV-50). Cadeia: EV-08/EV-11/EV-42 → CAND-2 → QS-02 → TAT-08/09 → DA-2 → U01–U26/guardas → BF/MF],
    [Estrutura / padrão que a realiza], [_Proxy_ de dados nginx/S3 com controlo autenticado separado; fachada/adaptador para o POST _multipart_, que leva o corpo em fluxo até ao S3 sem _spool_ integral (D-02, UP-C8 A); regras/validação/autorização final/_commit_ comuns. Coleção de tentativas e _staging_ controlados até _media_ válido; candidato imutável e _commit_ condicional no documento do projeto (UP-C6 A); `ffprobe` sobre o candidato com leitura limitada; _hash_ depois do _ready_ (UP-C7 A); limpeza ativa e _journal_ (UP-C9 A). Não é uma transação distribuída. EV-44/EV-50],
    [Alternativas consideradas e razão de rejeição], [*TAT-11 isolada:* pode adiar OOM, mas não resolve custo proporcional aos bytes e viola a comparação BF/MF se só o MF ganhar RAM. *TAT-09 como percurso primário único por todos os Node:* é alternativa válida e mais conservadora, mas mantém bytes em todos os saltos; a escolha comunicada privilegia nginx/S3 com adaptador de compatibilidade. *TAT-10 síncrona:* rejeitada em UP-C7 A, porque soma a leitura integral do ficheiro ao tempo até _ready_ (U09); fica registada a dúvida de segurança e as cinco condições da _cache_ sem _hash_. *TAT-13:* C, capacidade nova não necessária. EV-42/EV-44; H-15–H-17],
    [Consequências positivas], [Menos _buffers_ nos serviços Node e autenticação antes do corpo também no legado; compatibilidade HTTP preservada; tentativa inválida não entra nos _media_ normais. São H-15/H-17/H-18, por medir.],
    [Consequências negativas / riscos], [Dois transportes, mais estados e caminhos de falha; _staging_/cópias/_hash_ podem aumentar disco/rede/tempo e complexidade. _Backpressure_/temporários precisam de limites reais; 2xx ao PUT não é _ready_ nem _commit_. Uma coleção separada não garante isolamento/idempotência. Manter ambos os percursos exige testes de recursos. EV-44; H-15–H-18],
    [Elementos arquiteturais afetados], [_frontend_/`lib/projects.ts` e tratamento de _upload_; nginx; `apiGateway/routes/projects.js`; `projects`/rotas/modelos/validação/_storage_/_cache_; `imageStorageService`; Compose/credenciais. Worker de vídeo, fila e semântica dos efeitos mantidos; guardas de regressão atravessam imagem/vídeo.],
    [Origem e âmbito do _refactoring_], [Interação: transporte global mais volume do vídeo, não granularidade dos efeitos. Não escolhe ALT-1/ALT-2. Alto risco de _orphan_/associação/versionamento, _cache_ sem _hash_ e discrepância entre adaptador e fluxo novo. EV-12/EV-26/EV-42/EV-44],
    [Classe (A/B/C)], [*A no núcleo:* mesma capacidade de carregar e editar, mantendo POST _multipart_/204/`X-Project-Version`, limites/perfis e quota. Novo protocolo interno não é pausa/retoma ou biblioteca. EV-39/EV-44],
    [Implementação (_commits_ / _pull requests_)], [Branch `fase2-refactor`: `02623a4` (B0 — _spikes_ SP-01, SP-03 e SP-05). Motor e adaptador (B6) e fluxo novo com _frontend_ (B7) por implementar à data desta versão. EV-51. #preencher[completar com os _commits_ finais]],
    [Desvios face à decisão], [O adaptador escreve diretamente numa chave de candidato nova e única, que o cliente nunca pode escrever, em vez de copiar _staging_ → candidato (UP-C6 à letra): o CopyObject de 500 MiB chegou a 6,2 s e somava cerca de 100 MiB à U04 (SP-03, D-16); os volumes do SeaweedFS passam a ser pré-criados no arranque. O limite de leitura do `ffprobe` (2×F+16 MiB) impõe-se por um relé em _loopback_ dentro da `projects`, porque o `ffprobe` só limita o tempo (SP-05, D-17). EV-51. #preencher[completar no fim da implementação]],
  ),
)

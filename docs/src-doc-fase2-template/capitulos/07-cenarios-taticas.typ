#import "../template.typ": *

// Capítulo inteiro na horizontal (tabelas largas). Para voltar ao vertical, retirar o #paisagem[ ].
#paisagem[
= Cenários de Entrada e Táticas Candidatas

== Candidatos e cenários de entrada

#tab([Candidatos e cenários de entrada],
  tabela(
    colunas: (1.8cm, 2.2cm, 3cm, 1.8cm, 2.8cm, 3cm, 3.4cm, 3.4cm),
    tamanho: 8pt,
    [Candidato], [Cenário (`QS-nn`)], [Característica / subcaracterística (ISO/IEC 25010)], [Evidência], [Origem (padrão global / vídeo / interação)], [Estímulo a que a tática reage], [Resposta e medida (resumo)], [Escala e método (cap. 6)],
    [CAND-1], [QS-01, QS-07 complementar], [Segurança: confidencialidade, integridade e autenticidade], [EV-24/EV-43, H-14], [Padrão global, herdado pelas operações de vídeo], [Apresentar pedido de acesso/operação sobre recurso de projeto sem autorização efetiva, incluindo entrada numa sala de projeto], [Verificar identidade e autorização, recusar acesso/efeito/entrada indevidos e preservar a operação legítima: por caso: tentativas, admissões e efeitos verificados, fração de efeitos indevidos e sucessos legítimos. EV-24/EV-43, H-14], [Capítulo 6 (quantificação) e capítulo 10 (protocolo e resultados)],
    [CAND-2], [QS-02], [Eficiência de desempenho: utilização de recursos, comportamento temporal como guarda], [EV-08/EV-11/EV-42, H-15/H-17/H-18], [Interação entrada global/tamanho do vídeo], [Enviar vídeo válido de tamanho crescente, isolado ou com outros _uploads_], [Aceitar e disponibilizar apenas o ficheiro validado/associado corretamente, limitando recursos e mantendo pedidos leves utilizáveis: por serviço/janela: RSS/cgroup/pico, CPU/rede/disco, OOM/reinícios, $t_"ready"$, $t_"hash"$, _cleanup_, SHA-256 e respostas corretas. EV-08/EV-11/EV-42, H-15/H-17/H-18], [Capítulo 6 (quantificação) e capítulo 10 (protocolo e resultados)],
  ),
)

== Alterações feitas ao capítulo 5

#tab([Alterações aos cenários],
  tabela(
    colunas: (2cm, 1fr, 4cm),
    [Cenário], [O que mudou e porquê], [Onde foi atualizado],
    [QS-01 → QS-01 + QS-07 complementar], [Revisão 1.1 em 20/11 separa tentativa de acesso de revogação de uma autorização existente, porque têm fontes/estímulos/relógios distintos. QS-01 mantém o ID para admissão, QS-07 é novo ID, sem reutilizar qualquer eliminado. CAND-1 permanece a mesma.], [Capítulos 5–6, priorização e âmbito de CAND-1; TAT-04 referencia o complemento. EV-49],
    [QS-02], [Texto canónico inalterado, não se altera o cenário para o adequar à tática escolhida.], [Capítulo 5, cenário QS-02],
  ),
)

== Táticas candidatas

#tab([Táticas candidatas],
  tabela(
    colunas: (1.6cm, 1.8cm, 3.6cm, 3.4cm, 5cm, 3.4cm, 1.8cm),
    tamanho: 8pt,
    [ID], [Cenário], [Atributo → categoria], [Tática], [Como produz a resposta (estímulo → tática → resposta)], [Já existe na base? (evidência)], [Classe (A/B/C)],
    [TAT-01], [QS-01 / CAND-1], [Segurança → resistir], [Identificar/autenticar atores em cada fronteira], [Pedido de _peer_/cliente → verificar perfil de identidade e _peer_ autorizado → rejeitar impersonação em vez de confiar num _header_], [Parcial: JWT no _gateway_, _caller_ interno decodifica e _header_ é confiado. EV-08/EV-24/EV-46, H-14], [A],
    [TAT-02], [QS-01 / CAND-1], [Segurança → resistir], [Autorizar atores/operações no domínio], [Leitura/mutação/_join_ → `projects` decide posse/contexto/_read_/_edit_ → só efeito/receção permitidos], [Parcial: partilha/versionamento existem, sem matriz transversal e autorização de sala prevista. EV-24/EV-37/EV-46, H-14], [B na correção _owner-only_ da eliminação, A no núcleo interno],
    [TAT-03], [QS-01 / CAND-1], [Segurança → resistir], [Limitar acesso/exposição e cifrar comunicação com validação], [Caminho direto/certificado indevido → TLS/mTLS, credenciais próprias e identidade/operação específicas → reduzir superfície e confiança indevida], [Parcial: HTTPS/portas e cifra de campos existem. Não há validação completa do servidor/_peer_ nem gestão de chaves implementada. EV-07/EV-09/EV-24, H-14], [A],
    [TAT-04], [QS-01, complemento QS-07 / CAND-1], [Segurança → reagir], [Revogar acesso e limitar autorização local], [Permissão/JWT deixa de valer → consulta por entrada e revalidação/corte da sala afetada → não manter receção indevida], [Parcial: _links_ revogados no HTTP. Permanência WS não segue o contrato. EV-22/EV-37/EV-44/EV-46, H-14/H-18], [A no mecanismo, B nos erros/reconexão visíveis necessários à melhoria],
    [TAT-05], [QS-01 / CAND-1], [Segurança → resistir], [Limitar exposição apenas no perímetro], [Pedido externo → filtro da fachada/rede → bloquear parte das entradas], [Parcial: `checkToken` já existe, mas acessos internos e efeitos verificados mostram cobertura insuficiente. EV-08/EV-24/EV-43], [A, alternativa insuficiente para o cenário completo],
    [TAT-06], [QS-01 / CAND-1], [Segurança → resistir], [Autorizar entrada WS por credencial de sala localmente verificada], [_Join_ → bilhete assinado/contextual → verificação local sem consulta por entrada], [Não, era alternativa D6.2 A, substituída pela consulta B. Continua a exigir revogação/invalidação. EV-44, H-14], [A, não selecionada],
    [TAT-07], [QS-01 / CAND-1], [Segurança → resistir], [Separar entidades através de nova biblioteca/pastas privadas no produto], [Utilizador organiza vídeos em capacidade nova → dados separados pela nova interface], [Não, a biblioteca do requisito histórico não está implementada. EV-04/EV-10/EV-23], [*C: rejeitada*, separar internamente permissões não exige criar biblioteca],
    [TAT-08], [QS-02 / CAND-2], [Desempenho → controlar procura], [Reduzir a sobrecarga do transporte do corpo, separando-o do controlo], [Corpo grande → nginx encaminha bytes autorizados para S3, Node mantém controlo → menor _buffer_/cópia nos Node], [Não no percurso novo. Na base, o corpo passa pelos três Node. EV-08/EV-11/EV-12/EV-42, H-15], [A],
    [TAT-09], [QS-02 / CAND-2], [Desempenho → controlar procura/gerir recursos], [Aumentar eficiência por _streaming_/contrapressão e temporários limitados], [Produtor rápido/ficheiro grande → consumo limitado e _backpressure_ → não acumular corpo integral em RAM], [Parcial: S3/worker têm processamento incremental, mas _multer_ usa memória no _upload_. EV-11/EV-12/EV-17/EV-46, H-15], [A, obrigatória também no adaptador selecionado],
    [TAT-10], [QS-02 / CAND-2], [Desempenho → gerir recursos], [Escalonar cálculo do _hash_ depois de _ready_, com estado/_cache_ coerentes], [Validação concluída → adiar leitura integral e controlar execução → reduzir caminho até _ready_ sem fingir reduzir custo total], [Não: na base, o _hash_ é síncrono e _required_. Mecanismo selecionado a 21/11 (UP-C7 A: _hash_ depois do _ready_, em segundo plano, _cache_ desligada enquanto falta). EV-12/EV-26/EV-44/EV-50, H-16], [A, selecionada como realização de DA-2],
    [TAT-11], [QS-02 / CAND-2], [Desempenho → gerir recursos], [Aumentar recursos sem alterar _buffering_], [_Upload_ → mais RAM disponível → adiar OOM], [Compose original não fixa limites de RAM. Estratégia não elimina a dependência do tamanho observada. EV-09/EV-42], [A, mas não escolhida como solução principal],
    [TAT-12], [QS-02 / CAND-2], [Desempenho → gerir recursos], [Limitar filas e arbitrar recursos de _upload_/validação/_hash_], [Concorrência → admissão/filas finitas → limitar estado e espera, recusando excesso], [Parcial noutros percursos, sem limites de _upload_ na base. Limites fixados a 21/11 (UP-C5 A: 3 vagas globais, 16 pendentes, 4096 registos, UP-C9 A). EV-16/EV-44/EV-45/EV-50, H-17], [A, selecionada como realização de DA-2],
    [TAT-13], [QS-02 / CAND-2], [Usabilidade/desempenho → iniciativa do utilizador], [Adicionar pausa/retoma por partes como capacidade visível], [Interrupção → guardar partes e permitir retoma na interface → nova operação de utilizador], [Não na base nem na seleção UP-C1/C2/C3. É evolução distinta, não requisito para corrigir RAM. EV-23/EV-44], [*C: rejeitada para este exercício/entrega*],
  ),
)
]

# Fase 2 — Recuperação anónima, emissão e importação assistidas

**Equipa:** PL2-G4. **Preparado:** 17/11/2026. **Código observado:** `5749bb2`.
**Estado:** especificação de trabalho para concretizar SESS-C1 A. Não é ferramenta
implementada, recuperação executada, nova validação coletiva ou autorização para
alterar dados. Mantêm-se JWT HS256 de sete dias absolutos, ausência de refresh e
as restantes [escolhas de sessões/identidade](fase2-sessoes-identidade-partilhas-ws.md).

## Informação fornecida agora e consequência

O utilizador respondeu em 17/11: **ainda não sabe se existe registo independente
que associe as duas identidades anónimas aos browsers certos**. A existência de
evidência é **desconhecida**, não confirmada como existente nem como ausente.
As duas identidades referem-se à contagem histórica de `picturas`, não a uma
nova consulta a dados ou browsers. Não inferir uma conta por perfil nem mapear IDs.

| Campo | Estado atual |
|-------|--------------|
| Administrador desta máquina | Luís / ADM-01, já confirmado |
| Conjuntos retidos | `picturas` e `picturas-quality-20261114`, ambos a preservar |
| Prova independente de associação anónima | Desconhecida, por resposta do utilizador |
| Elegibilidade dos casos reais | Por determinar; nenhum caso com prova registada nesta revisão |
| Emissão/importação reais | Não iniciadas; não emitir com base apenas em ID/JWT antigo |
| Instalação de desenvolvimento/avaliação | Continua por escolher |

## Fronteira de confiança e prova de elegibilidade

O administrador local já controla a instalação, a base de dados e o emissor. Essa
autoridade é explícita; o procedimento não transforma uma alegação do browser em
prova de titularidade. Operador/host comprometidos ficam fora desta garantia.
Não criar uma rota pública que aceite um ID e emita um JWT para essa identidade.

Um caso só passa a elegível quando o administrador consegue fundamentar e registar:

1. **Instalação e conta:** identificação inequívoca do dataset/issuer alvo, conta
   existente de tipo anonymous e dados a preservar. Não escolher uma conta pela
   ordem da coleção, por ter zero projetos ou pela instalação que estiver ligada.
2. **Associação independente:** fonte de proveniência confiável que associe a
   conta ao perfil/destinatário, sem depender apenas de verificar a assinatura do
   JWT antigo ou de conhecer um ID. Exemplos a investigar são um registo
   administrativo de criação/associação ou um backup de perfil com proveniência
   verificável e associação documentada. A existência/autenticidade desses exemplos
   **não está demonstrada**. Um backup que só reproduza uma alegação não autenticada
   não passa automaticamente a prova.
3. **Destino controlado:** o administrador confirma o perfil de browser e a origem
   corretos para a entrega. Duas instalações podem usar `https://localhost:8080`:
   a origem, sozinha, não identifica o dataset nem a conta. Não mudar a porta.
4. **Decisão por caso:** registo datado de quem verificou, em que fonte e por que
   motivo a associação foi aceite. Criar agora um registo a partir só do JWT/ID
   antigo não cria retroativamente prova independente. O novo caso não contém JWT,
   passwords ou chaves; a correspondência privada fica fora do Git.

São insuficientes isoladamente: token antigo mesmo ainda válido, ID/campos de
localStorage, lista de contas, conhecimento de uma URL partilhada, controlo físico
de um computador sem associação à conta, número de projetos ou mera declaração
«o ficheiro está no browser». Recusar reemissão não elimina os dados.

Se não se conseguir fundamentar a associação, o estado é `pending_evidence` ou
`conflict`; preservar conta/projetos/presets e reportar recuperação não concluída.
Não transferir titularidade, criar outra identidade, fazer logout/reload para
«descobrir» a associação ou gerar primeiro uma credencial e verificar depois.

## Registo administrativo privado e estados

O [modelo JSON](../templates/anonymous-session-recovery-case.template.json) tem
valores vazios, sem credencial. Preencher uma cópia **fora do repositório**, sob
permissões do administrador; o modelo preenchido pode conter IDs e referências
de evidência privados. App/contentores não recebem escrita nesse registo. O
modelo não é prova, aprovação ou comando executável por si só.
A implementação deve recusar emissão com `template_only: true`, campos de prova
vazios ou estado diferente de approved, mesmo que o operador tente chamar issue.

| Estado | Condição de entrada / ação permitida |
|--------|-------------------------------------|
| pending_evidence | Evidência desconhecida/insuficiente; apenas investigar/registar, sem emissão |
| evidence_verified | Fonte e associação verificadas, conta/instalação/perfil elegíveis; ainda sem JWT |
| approved | Administrador aprovou o caso e o destino concreto; emissor pode executar as verificações finais |
| issued | Credencial foi gravada no artefacto privado e emissão identificada; não significa importação |
| import_verified | Servidor validou a credencial e o operador comparou a identidade com o caso aprovado |
| imported | Sessão local gravada após validação/confirmação; ainda falta conferir dados/reconexão |
| completed | Identidade/dados preservados, verificação e reconexão concluídas, resultado registado |
| conflict / failed / issued_unconfirmed | Parar, preservar evidência e reconciliar; não repetir emissão cegamente |

Nenhum caso real foi movido para evidence_verified/approved nesta revisão.
O administrador preenche dados/decisão efetivos; não inferir aprovação do facto de
um JSON ter `status: approved`. A ferramenta verifica origem/permissões do registo
e que o operador tem autoridade de emissão local.

## Emissor administrativo a implementar

**Interface lógica**, não comandos já disponíveis: `inspect`, `issue` e `status`
sobre um caso privado. `inspect/status` devolvem apenas referências/estado/erros;
`issue` só aceita caso aprovado, mantém a conta e grava uma credencial em ficheiro
privado. Não expor funções de criação de utilizador, alteração de tipo/quota ou
reaproveitamento automático de um ID indicado pelo browser.

Antes de assinar, o emissor deve verificar:

- instalação/dataset/issuer esperados, conta ainda existente e anonymous, caso e
  destino aprovados sem conflito; revisão dos dados se a conta mudou desde a prova;
- a transição do segredo já preparada/validada na instalação, sem usar o segredo
  antigo exposto nem aceitar old/new em simultâneo como atalho;
- acesso administrativo local ao emissor users e ao segredo HS256 de runtime;
  nunca copiar esse segredo para o browser, projects ou um ficheiro de caso;
- saída fora de Git/build/logs, sem sobrescrever artefacto ou seguir caminho não
  controlado. Usar criação exclusiva, permissões restritas (0600/ACL equivalente)
  e diretório privado, verificadas antes da emissão. Sem token em argumentos,
  stdout, histórico de shell, URL, clipboard partilhado ou relatório.

O JWT é o **JWT normal de sessão anónima**, emitido para o mesmo `_id/sub`, com
algoritmo/issuer/audience/tipo selecionados e `exp = iat + 7 dias`. Não é bilhete
de sala, refresh token ou código de recuperação de uso único. Ler o tipo/perfil
na users; não aceitar privilégios do pedido. Assinar no domínio administrativo
users ou num emissor local equivalente protegido; o contrato concreto deve
preservar que apenas os serviços previstos recebem HS256.
Reutilizar a mesma rotina de perfil que login/emissão normal e os verificadores
adotarem na transição; não assinar manualmente um JWT num perfil incompatível nem
chamar o get_jwt atual e presumir que já contém issuer/audience/tipo selecionados.

Guardar no registo administrativo apenas ID de emissão, caso, sujeito/instalação
privados, instante/expiração, resultado e referência protegida da saída — não o
bearer. Usar bloqueio por caso e criação exclusiva para impedir duplicação trivial.
Se ocorrer crash entre assinar/gravar/registar, marcar issued_unconfirmed e
reconciliar o artefacto privado; não presumir emissão única nem gerar outro token
automaticamente. Sem estado de revogação individual, reemitir não invalida cópias
anteriores: suspeita de fuga exige tratar a exposição, não prometer que apagar o
ficheiro revogou o JWT. Reemissões futuras seguem novo caso/instante/prova válida.

## Artefacto de entrega e limites

Especificação de ficheiro local JSON, versão 1, contendo apenas schema_version,
case_ref, installation_ref, intended_origin, issued_at, expires_at e token.
Propor limite de **16 KiB UTF-8** no ficheiro, mantendo o limite selecionado de
**8 KiB no token/handshake**; são entradas distintas. São limites de implementação
para testar, não capacidade medida ou nova duração do JWT.

Os metadados do envelope são indicações de encaminhamento, não prova assinada.
Alterar `installation_ref`, destino ou datas no JSON não muda o issuer/sub/exp
assinados. Confirmar sempre o resultado validado no servidor e a associação no
registo administrativo independente; não aceitar o mesmo JWT noutro dataset
só porque ambos têm a mesma origem local. O ficheiro é uma credencial bearer:
quem o obtiver pode usá-lo até expiração/retirada global aplicável.

O ficheiro privado de entrega **não é** o modelo público do caso administrativo;
não acrescentar token ao template nem ao journal. Apagar cópias dispensáveis após
entrega verificada reduz exposição, sem declarar revogação criptográfica, uso único
ou remoção física garantida de backups/SSD. A validade conta desde emissão,
**não** desde importação, retry ou reconexão.

## Importação no frontend — percurso de trabalho

Propor uma entrada dedicada de recuperação em `https://localhost:8080/session-recovery`,
sem token em query/fragmento, destinada ao operador/perfil confirmado. A rota e
o importador ainda não existem. A entrada seleciona um ficheiro local; não há
pedido público para obter JWT a partir de ID, email ou caso.

1. **Preparar o perfil:** manter o modo de manutenção previsto e uma única tab de
   recuperação controlada; fechar outras tabs PictuRAS, impedir JS antigo de
   escrever a sessão e usar o frontend atualizado. Se o operador não consegue
   garantir o perfil/ausência de sessões concorrentes, parar em conflito. Não abrir
   o cliente antigo no percurso normal como primeiro passo da recuperação.
2. **Suspender o arranque antes dos efeitos:** o root layout envolve todas as
   páginas no SessionProvider; este chama useGetSession e valida no mount, enquanto
   useGetSession regista anónimo se faltar sessão. O modo de recuperação tem de
   impedir esses efeitos **antes** de se executarem, incluindo chamadas existentes
   em providers/componentes. Apenas adicionar uma página dentro do provider atual
   não cumpre. Não ligar socket, auto-register, validate da credencial antiga ou
   callbacks de logout enquanto a importação estiver pendente.
3. **Ler sem efeitos:** validar tamanho, JSON/schema/versão e campos esperados em
   memória. Rejeitar token ausente, entrada excessiva, tipo/estrutura incompatível
   e origem errada sem escrever localStorage nem enviar os metadados como prova.
4. **Validar no servidor:** enviar apenas a credencial candidata em Authorization
   para a validação de sessão própria, por TLS validado, sem persistir primeiro.
   Reaproveitar o fluxo `/users/validate/:user` após implementar o perfil selecionado,
   em vez de uma rota de impersonação. O ID usado no encaminhamento é candidato,
   nunca autorização. Gateway/users verificam assinatura, HS256 explícito, issuer,
   audience/tipo, iat/exp, conta existente e vínculo entre caminho e sub. O
   frontend não recebe o segredo HS256 para «verificar localmente».
5. **Conferir a identidade:** servidor devolve o perfil real sanitizado. Exigir
   anonymous, instalação/issuer esperados e mesmo `_id/sub` do caso aprovado,
   confirmado pelo operador através do registo independente. Não confiar em
   `user`, IDs, nomes ou permissões fornecidos no ficheiro. Conta registada usa
   login. Se houver sessão de outro sujeito no destino, parar em conflito, não
   sobrescrever silenciosamente. Metadados de envelope/old JWT não são prova.
6. **Importar conscientemente:** com confirmação do operador após a conferência,
   gravar a estrutura SessionData existente com token validado e utilizador devolvido
   pelo servidor; nunca criar outra conta ou alterar quota/projetos. Só depois
   atualizar caches/estado, fechar a ligação antiga e emitir session-updated/reiniciar
   o ciclo normal. Escrita falhada mantém estado anterior e importação não concluída.
7. **Verificar:** reler a sessão, validar mesma identidade/dados e testar reconexão
   explícita com JWT válido e autorização fresca por sala. Falha de rede posterior
   conserva a identidade, mostra estado pendente e permite retry; não regista
   outro anónimo, não reinicia exp e não restaura segredo antigo. Confirmar a
   importação no journal sem recolher a sessão/token para o relatório.

É necessário controlar callbacks em curso e outras tabs para um validate antigo
não voltar a gravar a sessão anterior. A implementação deve testar gerações/
cancelamento e conflitos; um evento personalizado numa tab não prova coordenação
de todas as janelas. Se não houver garantia de quiescência/versão do cliente,
não declarar importação segura. Nunca chamar useLogout como mecanismo de migração:
o caminho atual cria outra identidade.

## Fontes estáticas e implicações da implementação

| Fonte | Observação atual | Alteração necessária para satisfazer o contrato |
|-------|------------------|------------------------------------------------|
| [users auth](../../users/auth/auth.js) | Emissão de 7 dias; validação atual não é o perfil completo da proposta e regista claims/utilizador | Emissor administrativo restrito e validação do perfil/conta; sanitizar logs e testar negativa/positiva |
| [users routes](../../users/routes/users.js) | validate devolve sessão/token existente | Validação sem mutação de domínio e sem aceitar tokens/IDs como recuperação pública; manter payload sanitizado |
| [root layout](../../frontend/app/layout.tsx) | SessionProvider envolve todas as páginas | Isolar o percurso de recuperação do bootstrap que produz efeitos |
| [query session](../../frontend/lib/queries/session.ts) | Ausência de session chama register anonymous | Ausência em modo recuperação não cria conta; falhas são estados explícitos |
| [session provider](../../frontend/providers/session-provider.tsx) | Valida no mount e reage a session-updated | Suspensão antes dos efeitos, controlo de callbacks e retoma só após importação |
| [mutations session](../../frontend/lib/mutations/session.ts) | Erro de validação faz logout; logout regista outro anónimo | Sem substituição automática de identidade em erro/expiração; separar logout voluntário e recuperação |

Web Storage é associado à origem e partilhado entre janelas do mesmo contexto;
o evento storage não dispara na janela que fez a alteração. Estas propriedades
não provam um lock transacional entre tabs. Validar/gravar a credencial é aplicação,
não uma garantia fornecida por localStorage. Fontes:
[WHATWG Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html),
[MDN storage event](https://developer.mozilla.org/en-US/docs/Web/API/Window/storage_event).
A validação de algoritmo/issuer/audience deve seguir o perfil fixado, sem aceitar
claims como verdade antes da verificação. Fonte: [RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html).

## Aceitação e cenários a implementar/ensaiar

Os grupos seguintes detalham SEC-01/SEC-02, sem novos RNF ou testes executados.
Usar só fixtures descartáveis com evidência artificial explicitamente de teste;
nenhuma conta real adquire prova por reproduzir uma fixture.

| Caso | Pré-condição / falha | Asserção |
|------|---------------------|----------|
| AR-01 | Prova desconhecida, só ID/JWT antigo ou fonte contraditória | Sem emissão; estado pending/conflict e dados preservados; nem «ausente» nem «recuperado» por omissão |
| AR-02 | Caso aprovado, conta anonymous e perfil/dataset corretos | Mesmo sub/_id, contagens/quota/projetos/presets/referências/bytes preservados; artefacto privado e emissão registada |
| AR-03 | Conta apagada/registada, alteração após prova ou destino divergente | Recusar sem criar conta, promover perfil ou corrigir automaticamente o caso |
| AR-04 | Emissão concorrente/repetida, crash ou ficheiro de saída já existente | Sem overwrite/duplicação automática; journal reconciliável, issued_unconfirmed em ambiguidade; não prometer uso único do JWT |
| AR-05 | Bundle adulterado, issuer/dataset errado, old-secret JWT, assinatura/alg/aud/tipo/sub inválidos | Servidor recusa; nenhum token/utilizador não validado gravado no browser |
| AR-06 | Expirado ou importação tardia após emissão; nova expiração anónima futura | Exp continua desde emissão; caso pendente/nova assistência com prova, sem refresh automático/nova identidade |
| AR-07 | JSON inválido, tamanho exato/+1, token excessivo ou tipo de ficheiro inesperado | Erro definido sem truncagem, registo de conta, leaks ou alteração da sessão |
| AR-08 | Rede/TLS indisponível, recusa de storage ou falha após gravação | Não gravar antes de validar; escrita falhada preserva anterior; falha posterior conserva identidade e não reinicia exp |
| AR-09 | Mount do importador sem sessão e com sessão antiga inválida | Zero POST de registo automático, logout, socket ou validação antiga antes da conferência; importador não fica bloqueado pelo loading do provider |
| AR-10 | Outra tab/callback antigo em curso, reimportação ou sujeito diferente | Estado antigo não sobrescreve novo; conflito explícito, caches/sockets coerentes e sem perda silenciosa de outra identidade |
| AR-11 | Importação validada, dados completos e sala autorizada/negada | Reconexão explícita, consulta por sala e autorização atual de eventos pessoais/de projeto; retorno positivo não deriva apenas do ficheiro importado |
| AR-12 | stdout, argumentos, artefactos entregues, imagens e journal | Nenhum JWT/chave/PII exposto; template/export público sem IDs reais; ficheiro privado não equivale a credencial de uso único nem revogação após apagar |

Métricas: S06/S19/S20, F04/F06/F09/F10 e U24 se quota for observada. Recolher n,
estados/erros, contas antes/depois, igualdade de identidade/dados e tempos de
aprovação/emissão/validação/importação, incluindo falhas. Gates funcionais: nenhuma
identidade substituída sem decisão explícita, nenhum registo extra/mutação de quota
e nenhum caso sem prova reportado como recuperado. Capacidade/tempos da ferramenta
são NM, sem prazo inventado para aprovação humana.

## Entrega, esforço e resultado desta revisão

Inclui implementar o emissor/procedimento privado, isolamento do bootstrap,
importador/validação, journal/erros e os ensaios acima. Confiança média no desenho;
estimativa preliminar **8–16 h/pessoa**, sujeita à prova, fluxo de tabs e contexto
TLS/segredos implementados. Não é medição, disponibilidade aprovada ou total do RNF.
Recuo: conservar perfil/conta/dados e caso pendente, suspender importação/emissão em
conflito, não voltar a aceitar segredo antigo ou criar outro anónimo como correção.

Se não estiver implementado/ensaiado até à entrega de 27/11, registar limitação de
recuperação anónima, mesmo com a especificação completa. O desconhecimento da prova
real permanece um bloqueio por caso; não uma razão para inventar evidência ou apagar
dados. Nesta revisão foi concretizado o procedimento e registada a resposta do
utilizador. Não foram lidos browsers/BD/volumes, emitidos tokens, alterada a aplicação
ou criados casos preenchidos com IDs reais.

# Fase 2 — Ciclo de vida dos uploads: proposta para revisão

**Equipa:** PL2-G4. **Preparado:** 18/11/2026. **Estado (21/11/2026):** UP-C4 A,
UP-C5 A, UP-C6 A, UP-C7 A, UP-C8 A e UP-C9 A **selecionadas** individualmente pelo
utilizador; ver [seleção de 21/11](#seleção-de-21112026). Continua a ser desenho, não
implementação. **UP-C1 A/UP-C2 A/UP-C3 A**
estão selecionadas individualmente com confirmação técnica e condições no
[registo de decisões](fase2-upload-decisoes-pendentes.md). Mantêm-se adaptador
multipart limitado, cobrança só no Apply e tentativas/staging separados dos
media normais. Os dois transportes usam as mesmas regras e commit.

## Seleção de 21/11/2026

| Ponto | Escolha | Nota |
|-------|---------|------|
| UP-C4 | **A** — uma tentativa por PUT, sem retoma | Interrupção obriga a nova tentativa e nova chave. |
| UP-C5 | **A** — parâmetros da tabela abaixo | Valores iniciais; calibração registada antes de os congelar. As 3 vagas globais coincidem com a concorrência C=3 da U20. |
| UP-C6 | **A** — candidato imutável e commit condicional no projeto | A alternativa B não é viável: MongoDB 4.4 sem replica set nesta instalação. |
| UP-C7 | **A** — hash depois de ready, em segundo plano | A alternativa B leria o ficheiro inteiro antes de aceitar e falharia a U09 (<3 s). **Dúvida de segurança registada** (abaixo). |
| UP-C8 | **A** — `ffprobe` sobre o candidato, com leitura e tempo limitados | Único caminho compatível com o alvo da U08 (sem spool integral). Se o `ffprobe` não conseguir ler do SeaweedFS com estes limites, a decisão é revista com registo (B, spool limitado), e a U08 fica no mínimo. |
| UP-C9 | **A** — PUT com comprimento conhecido, autenticado antes do corpo; limpeza ativa a cada 5 s | Sem retry transparente; journal/tombstones durante 24 h. |

**Dúvida de segurança em UP-C7 A (janela `ready_hash_pending`).** Entre o commit e o
fim do cálculo do hash, o vídeo já é utilizável sem hash do servidor. Condições para
que essa janela não seja uma falha de integridade:

1. O candidato é imutável depois de selado (UP-C6 A): nenhum caminho o reescreve, por
   isso o hash calculado depois corresponde aos bytes publicados.
2. A cache que depende do hash fica **desativada** para media sem hash; nunca se usa
   uma chave vazia ou o hash enviado pelo cliente.
3. O hash é sempre calculado pelo servidor a partir do objeto guardado.
4. A janela é limitada pelo prazo do hash (U14: 10/5 s) e uma falha fica visível no
   estado, sem inventar hash nem apagar o original.
5. A U15 (SHA-256 do original) continua a verificar a integridade em todos os uploads
   aceites.

Se alguma destas condições não puder ser implementada, a UP-C7 volta a decisão.

## Opções consideradas

| Ponto | A — recomendação de trabalho | B — alternativa e custo |
|-------|-----------------------------|-------------------------|
| UP-C4 — estado/uso único/retry | Um PUT autorizado por tentativa, claim atómica; estado/status e confirmação idempotentes; corpo interrompido exige nova tentativa e chave, sem retoma automática | Retoma por partes/ranges com ledger de partes, checksums, abort e conclusão; melhora uso de rede, mas acrescenta outro protocolo |
| UP-C5 — prazos/admissão | Parâmetros iniciais da tabela seguinte: token para iniciar 5 min, tentativa 15 min absolutos; corpo até 10 min/idle 30 s, três vagas globais de trabalho, no máximo 16 tentativas com recursos pendentes e 4096 registos de journal; calibração antes de congelar | Outros valores justificados ou fila de corpos. Mais concorrência/fila aumenta recursos e espera; não escolher limites só para fazer passar o ensaio |
| UP-C6 — objeto/commit | Criar candidato final de chave única, privado, **antes** de validar; nunca o reescrever. Commit e barreira de cancelamento/limpeza no documento do projeto, com marcador idempotente; coleção Upload é journal/controlo de transporte | Versionamento S3 com versão imutável fixada e transações MongoDB se suportadas/configuradas; pode simplificar algumas corridas, mas não há suporte/versionamento/replica set demonstrados nesta instalação |
| UP-C7 — hash/cache | Depois de ready, hash em fluxo com estado durável, concorrência inicial 1 e vagas já reservadas; retoma/repetição apenas deste cálculo, sem repetir PUT/Apply; cache desativada para hash ausente | Calcular sempre antes de ready; simplifica disponibilidade do hash, mas mantém leitura integral no caminho temporal de aceitação |
| UP-C8 — probe | FFprobe sobre candidato interno fixado, TLS validado e I/O/tempo efetivamente limitados; proposta 15 s totais incluindo fila e até 2×F+16 MiB de leitura | Um spool limitado para ffprobe local; mais disco/I/O integral, porém pode ser mais previsível. Exige revisão explícita do percurso e da guarda U08, sem declarar a meta sem spool cumprida |
| UP-C9 — transporte/limpeza | PUT novo com comprimento conhecido e autenticado antes do corpo, sem retry transparente; limpeza ativa a cada 5 s, idempotente e com barreiras; tombstones/journal por pelo menos 24 h após estado reconciliado e limpeza | Mais tolerância a chunked/reenvio ou retenção diferente; precisa de contrato de framing, deduplicação e evidência próprios. TTL Mongo isolado não limpa S3 |

Confiança: média no modelo de estados/isolamento; média-baixa nos custos de
cópia, prazos e limites. As alternativas B são independentes por ponto. Selecionar
A não demonstra que nginx/SDK/SeaweedFS/FFprobe implementem as garantias; testes
de suporte e interleavings continuam obrigatórios. Se uma condição falhar, rever
o desenho e registar o impacto, sem baixar silenciosamente critérios EVAL-M1.

## UP-C5 A — parâmetros iniciais propostos e relógios

| Parâmetro | Valor proposto / início do relógio | Regra em excesso ou falha |
|-----------|----------------------------------|--------------------------|
| Token para iniciar o PUT | 300 s desde criação da tentativa, limitado pela validade da sessão na admissão | Expirado não concede nova entrada; não renovar o mesmo token |
| Tentativa não publicada | Deadline absoluto created_at+900 s | Não publicar após deadline; erro/fila/retry não reiniciam prazo |
| Corpo | Até 600 s desde claim, sempre limitado pelo deadline da tentativa; idle 30 s | Terminar a receção, marcar falha/ambiguidade e reconciliar; um idle timeout não implementa por si o teto total |
| Validação/commit HTTP | Até 180 s desde pedido de confirmação, limitado pelo deadline da tentativa | Erro/timeout não prova ausência de commit; consultar estado/marcador antes de repetir |
| Probe | Até 15 s incluindo espera e I/O; leitura até 2×F+16 MiB | Falha explícita, nunca media ready sem validação real. F é tamanho real/declarado verificado do candidato |
| Vagas de trabalho | 3 globais, partilhadas pelos dois transportes desde claim até hash e limpeza normal; no máximo 3 por sujeito | Nova receção recusa antes do corpo se não houver vaga; não enfileirar corpos em RAM/disco sem limite |
| Tentativas com recursos pendentes | 16 globais, incluindo reservadas/ativas e terminais com cleanup pendente; no máximo 3 por sujeito | Recusa explícita antes de criar mais estado; não é reserva/débito de quota de operações. Falhar não liberta o budget enquanto houver recursos pendentes |
| Hash | 1 cálculo ativo, restantes dentro das vagas reservadas | Espera conta no prazo U14; 3 vagas não provam que 1 leitor cumpre 10/5 s |
| Varredura de limpeza | Intervalo inicial 5 s, operações limitadas e medidas | Falha preserva estado/evidência e volta a tentar sem fingir objeto removido |
| Journal/tombstone | Pelo menos 24 h após resultado reconciliado **e** limpeza verificada | Nunca apagar referência de pendência/evidência só por envelhecer; referência de commit permanece no media/projeto enquanto necessária |
| Registos de journal | 4096 globais incluindo terminais retidos; leituras/varreduras paginadas | Ao atingir o teto, recusar novas tentativas, sem apagar evidência ainda necessária nem materializar tudo em RAM |

Estes valores são propostas de engenharia, não valores já aceites pela validação
de EVAL-M1. Os **10/5 s do hash**, **TTL+60/TTL+10 s da limpeza** e U25 G mantêm
a seleção anterior no seu âmbito. Os 300/900/600/30/180/15 s, vagas, varredura e
retenção aqui descritos não decorrem desses critérios. Os 180 s coincidem com
a proposta do instrumento, mas limite do serviço e timeout do cliente são
parâmetros distintos; registar cada um e a eventual censura de observação.

Vagas/contadores precisam de claim autoritativa atómica e recuperação de reservas
interrompidas, antes de admitir bytes. Crash entre journal e reserva não autoriza
prosseguir; libertação requer fim/fencing do trabalho real, não só lease expirada.
Este controlo também é implementação a testar, não uma propriedade dos nomes
dos estados. Ao testar tetos, confirmar ocupação efetiva no instante da tentativa.

Para a limpeza, a expiração aplicável é explícita: created sem claim expira com
o token (300 s); após claim, vale o deadline absoluto da tentativa ou um término
antecipado demonstrado de falha/cancelamento. É desse instante que se mede U22,
sem o deslocar para o início de uma nova varredura. Um media publicado nunca é
apagado por vencer o TTL do antigo pending; limpar só o staging/temporários
inequivocamente seus. Estado committing incerto exige arbitragem antes de apagar.

A admissão exige JWT de utilizador válido; a identidade RS256 de até 30 s serve
para admitir a chamada, não limita a duração do corpo/trabalho já admitido.
Status/confirmação novos exigem JWT válido e autorização atual; se expirar durante
o envio, a confirmação pode precisar de relogin/reemissão para o mesmo sujeito.
Nenhum resultado é publicado com base apenas no token opaco antigo. Não presumir
revogação instantânea de um corpo já em trânsito; as garantias de visibilidade e
commit abaixo têm de impedir a sua publicação indevida.

## Estados e transições condicionais propostos

O registo Upload contém referências privadas do sujeito/dono/projeto, contextos
de acesso verificados, nome/tamanho esperados, transport, deadlines, geração,
hash do token aleatório, estado e referências de objetos/commit. Nunca guardar
JWT, chave de serviço ou URL assinada nesse journal. Token opaco proposto de
256 bits aleatórios; IDs de tentativa não são credenciais. Não reutilizar IDs
ou chaves entre tentativas ou gerações.

| Estado | Entrada / ação permitida | Visibilidade do objeto |
|--------|--------------------------|------------------------|
| created | Metadados/limites/contexto verificados; ainda sem corpo | Nenhuma |
| receiving | Claim CAS de created, token ainda válido, sujeito/projeto/contexto autorizados e vaga reservada | Só staging; não presumir que o corpo acabou |
| received | Objeto completo observado pelo servidor com tamanho correto e estado reconciliado | Staging privado; 2xx do cliente não basta |
| validating | Lease/geração de validação, candidato novo criado e validado pelo servidor | Candidato privado, nunca oferecido a listagens/signers normais |
| committing | Tentativa quer publicar; barreira autoritativa e CAS no projeto ainda precisam de resolução | Ainda privado até o commit do projeto |
| ready_hash_pending | Commit do projeto provado; candidato associado a um único media, hash ainda pendente | Media legítimo utilizável, com cache sem hash desativada/isolada |
| ready | Hash correto persistido; limpeza normal conferida | Media publicado; eliminar staging não elimina o original |
| rejected / expired / cancelled / failed | Transição terminal que não pode voltar a receber/publicar | Nenhum novo media; limpar apenas objetos inequivocamente próprios/não referenciados |
| reconciling | Resultado de cópia/commit/resposta incerto ou lease perdida | Não presumir sucesso/falha; consultar autoridades e preservar evidência |

Limpeza tem estado próprio (`cleanup_pending`/`cleaned`/`cleanup_failed`), sem
transformar um ready legítimo em upload falhado só por restar um temporário.
Estados observados no journal podem atrasar face ao commit do projeto. O resultado
autoritativo é o marcador/associação no projeto, não um status que o cliente
envia nem um booleano atualizado numa segunda coleção.

## Uso único e comportamento de retry

1. Autenticar/autorizar antes de interpretar, fazer spool ou encaminhar o corpo,
   incluindo no adaptador multipart. O token é vinculado a sujeito/projeto/
   contexto e tentativa; não substitui a política atual da projects.
2. Reclamar `created→receiving` por CAS no servidor; só uma chamada ganha.
   Sem cache do resultado de auth_request nem reexecução transparente de PUT
   no proxy/SDK. A mesma resposta de autorização não é um passe para dois corpos.
3. Se a claim for feita mas o corpo não chegar, ela permanece consumida. Consultar
   estado autenticado; sem prova de corpo completo, nova tentativa/chave. Nunca
   voltar o mesmo token de receiving para created para «facilitar retry».
4. Se a resposta ao PUT se perder, consultar e verificar o objeto real, sem
   reenviar cegamente. A interface oferece repetir confirmação/status, não o
   mesmo corpo. O adaptador antigo não ganha deduplicação universal de todos os
   POST repetidos: preservar nome/versão e não duplicar o mesmo commit interno.
5. Duas confirmações convergem no mesmo marcador/media; conflitos de versão
   mantêm resposta definida. Não aceitar automaticamente a versão mais recente
   para contornar um 409. Se não houve commit, pode repetir confirmação com nova
   versão explicitamente relida pelo cliente e autorização atual, dentro do
   deadline; a leitura de status não cobra nem recria a tentativa.

Proposta de respostas do fluxo novo: autenticação ausente 401, permissão negada
403, tentativa inexistente 404, conflito/consumo ou versão 409, expirada sem commit
410, comprimento obrigatório em falta 411, excesso de tamanho 413, falta de vaga
429 e indisponibilidade 503; ficheiro inválido 400. São respostas a selecionar,
sem traduzir indistintamente falhas internas para negação de acesso. auth_request
tem mapeamento próprio para 2xx/401/403/outros erros, a implementar no controlador
de transporte. O POST antigo preserva 204 e X-Project-Version no sucesso; não
adotar todos os novos códigos no contrato legado sem revisão de compatibilidade.

## UP-C6 — candidato estável, commit e limpeza sem transação S3

**A:** o PUT escreve numa chave staging única. Antes do probe, o servidor cria um
candidato **novo por geração de validação**, que será o original final se o commit
ganhar. O cliente não tem credencial/URL de escrita para esse candidato. Fazer
CopyObject se as garantias forem demonstradas no SeaweedFS; caso contrário rever
explicitamente para cópia em fluxo limitada e medir custo. Validar tamanho e
metadados no candidato, não validar staging e depois publicar bytes diferentes.
Depois de selado, nenhum caminho de retry o reescreve. Falha/geração obsoleta usa
outra chave e nunca substitui o candidato de um media publicado.

A mesma chave candidata pode ocupar o namespace final src, mas permanece inacessível
até haver associação de domínio válida. Prefixo src não concede leitura: signer,
previews, Apply, export e workers só aceitam media publicado/autorizado. Não confiar
no segredo do nome. Não aplicar a rota genérica de copy atual sem autorização e
condições: ela não implementa estas regras.

**Arbitragem no projeto:** criar uma barreira de tentativa/geração no próprio
documento do projeto, separada da lista normal de media. O commit exige essa
barreira ativa, expectedVersion, contexto de permissão aplicável ainda válido e
ausência de marcador anterior; insere media de ID estável, marcador de tentativa/
versão e incremento da versão na mesma atualização condicional. Revogação/cancelamento/
limpeza que fechem essa barreira ganham ou perdem na mesma autoridade. A coleção
Upload não é tratada como lock distribuído que magicamente abranja o projeto.

Reconciliar as janelas entre criação do journal/barreira, criação do objeto,
commit do projeto e atualização do journal. Se o commit ganhou, nunca apagar o
candidato por um status antigo de Upload. Se a limpeza/cancelamento ganhou,
o worker antigo não pode publicar. Antes de apagar um objeto de tentativa incerta,
fechar a barreira contra commits tardios e confirmar que não está referenciado.
Escritores atrasados também têm de estar terminados/fenced; a lease perdida sozinha
não cancela um CopyObject já em trânsito. Inspecionar resíduos posteriores em
nova varredura. Se essa prova faltar, manter cleanup pendente/inconclusivo e
reportar a eventual falha do prazo U22, sem apagar um original legítimo.

Isto não é atomicidade entre duas coleções/S3 nem promessa de exactly-once. É
um desenho a implementar/testar; barreiras e marcadores também precisam de limite
de estado/retenção, preservando informação enquanto houver possibilidade de
escrita/commit/retry. Não usar apenas a versão do projeto como permissão: uma
mudança de partilha precisa de condição efetiva no commit. Perfil/limites da
users são revalidados, sem alegar transação distribuída com projects.

Controlos internos de reserva/barreira não incrementam a versão pública do
projeto só por existir um upload pendente; o commit visível incrementa-a uma vez.
Todos os writers existentes que fazem `$set` de um snapshot do projeto têm de
preservar/excluir os campos de controlo. O updateIfVersion atual não oferece
essa proteção para campos novos: copiá-lo sem adaptação poderia restaurar uma
barreira antiga e invalidar o desenho. Testar mutação normal concorrente e
limpeza/cancelamento, sem aceitar uma versão nova automaticamente no cliente.

**B:** replica set/transações na projects + versão imutável de objeto pode ser
alternativa; não faz o objeto S3 participar na transação. O Compose consultado
usa MongoDB 4.4 sem configuração de replica set demonstrada. Antes de escolher B,
verificar suporte, esforço operacional, migração e custos. Não o assumir disponível.

## UP-C7/C8/C9 — terminar, medir e limpar

- **Hash:** journal durável/recomeço do cálculo para o mesmo candidato/geração,
  com CAS de estado; só a geração que corresponde ao media pode gravar o resultado.
  Reservar vaga antes de ready, incluir fila no prazo U14 e libertar em todos os
  caminhos. Retomar hash não reenvia o corpo, cobra Apply ou reinicia ready_at/
  prazo U14. Falha/deadline não
  inventa hash, não usa chave de cache vazia e não apaga automaticamente o original
  publicado; reportar estado e incumprimento/reconciliação. Hash de bytes entregue
  pelo cliente não substitui leitura/confiança do servidor.
- **Probe:** destino/key e parâmetros gerados pelo servidor; rejeitar redirects/
  hosts arbitrários e demonstrar TLS/identidade do servidor. Limitar bytes, ranges,
  fila, subprocessos e tempo de parede; opções de análise do ffprobe não provam
  sozinhas um limite global de I/O. Definir o mecanismo efetivo nas versões usadas,
  com teste de excesso/timeout; se não houver, o contrato permanece incompleto.
- **Transporte:** no PUT novo, comparar comprimento conhecido com o autorizado
  antes do corpo, impor bytes efetivos e confirmar tamanho real. ContentLength
  assinado não é capacidade demonstrada do SeaweedFS. No multipart antigo,
  distinguir envelope e bytes do ficheiro e impor o limite durante parsing;
  não recusar silenciosamente todos os clientes chunked antes suportados. Buffering,
  retry, timeouts e cancelamento de cada salto são configuração verificável;
  timeout entre leituras não equivale a deadline total.
- **Limpeza:** worker ativo com claim/barreira/geração, idempotente e reexecutável.
  Identificar cada temporário/multipart abortado, staging/candidato não referenciado,
  journal e media publicado; não fazer purge por prefixo sem asserção de posse.
  Índice TTL pode remover metadados terminais depois, não substituir o worker nem
  apagar evidência de objeto pendente. TTL+60/TTL+10 s já selecionados serão medidos
  a partir da expiração aplicável, incluindo filas/falhas; se não cumprir, reportar.

Snapshot/cópia acrescenta I/O/latência e coexistência temporária de objetos:
recalcular o inventário de disco antes de BF; **60 GiB continua piso, não teto**.
O caminho novo e o adaptador são ensaiados separadamente, preservando o mesmo
domínio. O frontend novo só diz pronto depois do commit validado; resposta de
PUT não conta como t_ready. Read/hash/cleanup posteriores entram no budget.

## Cenários a materializar — não executados

| ID | Estímulo e asserção principal | Métricas existentes |
|----|------------------------------|---------------------|
| UL-01 | Dois PUT concorrentes/claim repetida: um vencedor, nenhum overwrite; claim sem corpo não volta a ser utilizável | S22/U26 |
| UL-02 | Ambos os transportes: auth/ACL antes do corpo; válido mantém status/versão/dados, saldo zero sem cobrança | S01/S05/U01/U18/U19/U24/U25/F04 |
| UL-03 | PUT completo com resposta perdida vs incompleto: status distingue os casos; novo corpo nunca reutiliza chave | U21/U23/U26/F10 |
| UL-04 | Token/deadlines/idle/fila/bytes/no-slot; contadores/reservas libertados, sem novo prazo por retry | S22/S23/U03/U18/U20/U22/U26 |
| UL-05 | Revogação/duas vias e mudança de versão/nome durante envio/validação: sem commit indevido nem bypass de 409 | S13/S23/U23/U24/F04 |
| UL-06 | Staging altera-se/tenta leitura; candidato validado não muda após ready e pending nunca é utilizável | S03/S24/U15/U16/U21 |
| UL-07 | Crash em cada fronteira journal/barreira/cópia/commit/ACK: marcador e estado reconciliados, um media, nunca limpar original publicado | U21/U22/U23/F06/F10 |
| UL-08 | Limpeza e worker atrasado, lease/geração velha, CopyObject tardio: barreira impede publicação e resíduos são observados | S23/U21/U22/U23 |
| UL-09 | Hash fila/crash/restart/expiração: prazo inclui espera, estado durável e cache isolada antes/depois | U01/U02/U06/U07/U14/U15/U16/U25 |
| UL-10 | Probe H/T/formatos, bytes/ranges/tempo excedidos/SSRF/TLS inválido e controlo válido | S08/S09/S24/U09/U10/U13/U17/U18 |
| UL-11 | Limpeza TTL sob falha, objeto não removido/403 e autorreferência: não declarar deleted/ready por omissão | S03/U08/U21/U22/F10 |
| UL-12 | Tamanhos/perfis/C=3, clientes legado/novo, trabalho após ready e pedidos leves: recursos e funcionalidades preservados | U01–U04/U09/U10/U14/U17/U20/U25/F01–F05 |

## Fontes e estado da revisão

O código observado oferece [updateIfVersion](../../projects/controllers/project.js),
mas não as barreiras/ledger acima. MongoDB documenta atomicidade por documento e
condições no filtro, não transação automática com S3:
[MongoDB atomicity](https://www.mongodb.com/docs/manual/core/write-operations-atomicity/).
Expiração TTL não é remoção imediata nem rotina de limpeza de objetos:
[MongoDB TTL](https://www.mongodb.com/docs/manual/core/index-ttl/).
CopyObject tem semântica documentada no AWS S3, que não demonstra o comportamento
da implementação SeaweedFS usada aqui:
[AWS CopyObject](https://docs.aws.amazon.com/AmazonS3/latest/API/API_CopyObject.html).
Timeouts de proxy precisam de ser distinguidos de limite total:
[nginx proxy timeouts](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout).

O desenho mantém 60 métricas existentes, U25 G e seleções EVAL anteriores, sem
aprovar os outros limiares. **UP-C4–C9 A foram selecionadas em 21/11** (ver o
início do documento); parâmetros e mecanismos continuam por verificar na
implementação. Não há novos valores de baseline, commit Git, teste,
migração ou acesso a volumes/browsers. IA: desenho apoiado por Codex com a skill
Inception; análise e validação continuam distintas de implementação e avaliação.

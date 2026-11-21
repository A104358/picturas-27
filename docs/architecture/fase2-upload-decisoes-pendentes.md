# Fase 2 — Decisões de upload: seleção parcial e pontos em aberto

**Equipa:** PL2-G4. **Preparado:** 18/11/2026. **Estado:** UP-C1 A/UP-C2 A/UP-C3 A
selecionadas individualmente com confirmação técnica e condições. Fonte: o
utilizador recomenda expressamente as três A, descreve condições e pede fechar
o ciclo; confirmação técnica do assistente, sem inventar acordo dos quatro.
Não resultam por associação de EVAL-M1. Preferência nginx/S3 e
[decisões anteriores](../fase2-ideias-1-e-2.md) mantidas. **Atualização de 21/11:**
UP-C4 A a UP-C9 A selecionadas individualmente pelo utilizador, com a dúvida de
segurança da UP-C7 registada no [ciclo de vida](fase2-upload-ciclo-vida.md#seleção-de-21112026).
Com isto, UP-C1 a UP-C9 estão todas escolhidas. Não há
alteração de aplicação, novo endpoint, esquema ou teste executado nesta tarefa.

## Primeiro grupo — compatibilidade, quota e isolamento

| Ponto | A — seleção individual | B — alternativa e consequência | Confiança |
|-------|------------------|--------------------------------|-----------|
| UP-C1 — API | Novo fluxo de vídeo pedido JSON + PUT via nginx + confirmação no frontend, **mantendo o POST multipart antigo através de adaptador limitado**, com autorização antes de ler o corpo e motor comum de validação/commit | Retirar o POST antigo e atualizar todos os clientes controlados; simplifica o número de percursos, mas quebra o contrato HTTP. Exige decisão explícita e comunicação/adaptação, não alegar API preservada por manter o mesmo URL base | Média-baixa: preservar API é adequado; custo do adaptador e desempenho ainda não estimados/medidos |
| UP-C2 — quota | Preservar a regra atual: upload não cobra nem reserva operações e saldo zero não impede upload de um perfil elegível; Apply mantém a política própria | Impedir/reservar/cobrar no upload introduz política funcional nova e requer definição de libertação/retry/consistência; não decorre da melhoria de recursos | Alta na preservação da regra observada, sem prova experimental nova |
| UP-C3 — pending | Registo de tentativa em coleção própria e objeto em área/chave de staging controlada; só associar media utilizável ao projeto após validação real e commit autorizado | Acrescentar pending à lista normal de media. Menos estrutura inicial, mas cada listagem, signer, preview, Apply, export e worker precisa de filtro correto; um filtro omitido pode expor bytes não validados | Média: separação reduz acoplamento, mas não garante isolamento ou atomicidade por si |

Condições selecionadas: autenticar e autorizar antes de interpretar/armazenar o
corpo, streaming com contrapressão e temporários limitados; mesma validação,
autorização final e motor de commit nos dois transportes, sem duplicar upload ou
cobrança; testes de recursos/falhas/compatibilidade de ambos. Staging não pode
ser lido/usado por URLs normais, previews, Apply ou export; exige permissões,
transições condicionais, confirmação idempotente e reconciliação. Atomicidade
MongoDB não abrange S3. A seleção não declara estas capacidades implementadas.

Se o custo do adaptador comprometer a entrega, reconsiderar UP-C1 explicitamente;
não o retirar silenciosamente nem declarar compatibilidade sem a testar. A quota
permanece só no Apply; isso não escolhe TTL/estado/uso único/retries ou limites
de admissão. Esses detalhes foram selecionados em 21/11 (UP-C4–C9 A) no
[ciclo de vida](fase2-upload-ciclo-vida.md).

### Porquê UP-C1 A e o que exige

O [frontend atual](../../frontend/lib/projects.ts) envia multipart para
`POST /projects/:user/:project/video`, espera sucesso e atualiza a versão a partir
de `X-Project-Version`. O [gateway](../../apiGateway/routes/projects.js) usa multer
em memória **antes** de checkToken; a [projects](../../projects/routes/projects.js)
valida e guarda o vídeo, responde 204 e controla a versão. São observações de
código, não promessas de que todos os erros atuais estão corretos.

O adaptador proposto preserva entrada/status/versão e resultados funcionais
legítimos, sem manter a vulnerabilidade nem reproduzir um erro 501/OOM como
contrato obrigatório. O corpo atravessa o gateway em fluxo; a projects pode
usar um spool limitado para metadados/probe, com limpeza em todos os caminhos,
partilhando as decisões de domínio/commit com o percurso novo. Não chamar
internamente endpoints públicos para duplicar uploads/quotas ou criar dois
motores concorrentes. Definir os detalhes antes de implementar.

Custos: dois percursos de transporte para testar e manter, spool/cancelamento e
trabalho adicional de integração. Medir a API antiga como guarda de compatibilidade,
separada do grupo primário novo; incluir recursos, sem token antes do corpo,
respostas inválidas, nomes duplicados, partilhas e conflito 409. Não comparar o
fim do PUT novo com a resposta validada antiga. UP-C1 A não demonstra o mínimo
temporal do adaptador, nem autoriza removê-lo se esse teste falhar.

### Porquê UP-C2 A e o que não cobre

Em addProjectMedia o perfil determina limites de vídeo; o débito pertence ao
fluxo Apply. Preparar free com quota 0 e 5, premium, dono/editor/leitor e anónimo.
Um anónimo continua sem vídeo; um leitor não adquire edição. Metadados declarados
podem ser triados, mas tamanho/duração/codec/resolução reais são decisivos no
servidor. Outras limitações de abuso/armazenamento/pendentes podem ser necessárias,
mas precisam de limites explícitos; não usar quota de operações como substituto
silencioso. Prova U17/U18/U24/F04/F05.

### Porquê UP-C3 A e o que ainda é desenho pendente

O [schema atual](../../projects/models/project.js) exige og_sha256 em media;
as [stages normais](../../imageStorageService/utils/stages.js) são src/out/preview/
preview_cache. Não existe coleção de upload nem staging configurado. A implica
trabalho real de modelo/storage/limpeza e migração compatível do media ready,
sem relaxar globalmente validação de imagem.

Prefixo ou coleção separados não são controlo de acesso por si: signer/listagens
e permissões de serviço impedem leitura/uso de pending; cliente não escolhe
bucket/key/Host/URL de probe. A estratégia de promoção/referência, hash em falta,
CAS de versão, concorrência, crash entre registo/objeto/associação e reconciliação
precisa de contrato testável. Não presumir transação entre MongoDB e S3 nem
atomicidade entre duas coleções. Confirmação repetida não duplica media nem
ressuscita uma tentativa revogada/expirada. Prova S23/S24/U15/U16/U21–U23.

## Restantes decisões — abertas; alternativas no ciclo de vida

| Tema | O que fechar antes de congelar a avaliação |
|------|-------------------------------------------|
| D11/UP-C4 — token e estado | Identidade/projeto/contexto vinculados; autorização atual na admissão/confirm; reclamação atómica; single PUT concorrente; estado após resposta perdida e mecanismo de retry. Identidade RS256 de serviço não torna o token opaco de uso único |
| UP-C5 — prazos/limites | TTL do token e do pending, duração máxima/idle do corpo, limite de bytes efetivo, reserva concorrente/quantidade de tentativas e comportamento de excesso. EVAL-M1 não escolheu estes números |
| UP-C6 — objeto/confirm | HEAD/versão ou equivalente suportado, objeto imutável após validação, prevenção de overwrite/TOCTOU e comparação de bytes declarados/reais; preservar conflito de versão e nomes |
| UP-C7 — hash/cache | Momento de ready, fila/concorrência e persistência/retoma idempotente do hash; cache sem hash; gate U14 de 10/5 s selecionado não implementa este mecanismo |
| UP-C8 — probe | Destinos internos fixos, SSRF bloqueado, limite de bytes/ranges/tempo e formato H/T; comportamento concreto SeaweedFS por verificar |
| UP-C9 — nginx/S3 | auth_request disponível na imagem congelada; TLS validado por salto, credenciais/permissões; limites/body streaming efetivos; métodos /s3 de leitura preservados; URLs/tokens ausentes de logs e relatório |

O nginx documenta auth_request com 2xx/401/403 e erro para outros resultados;
não equivale a commit S3 nem controlo automático de uma tentativa. O buffering
de pedido tem configuração própria que exige teste. Fontes:
[nginx auth_request](https://nginx.org/en/docs/http/ngx_http_auth_request_module.html),
[nginx proxy_request_buffering](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_request_buffering).
URLs pré-assinados AWS S3 podem ser reutilizados até expiração; o comportamento
real do SeaweedFS tem de ser ensaiado, sem herdar capacidade por analogia.
Fonte: [AWS S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).

## Relação com a avaliação já selecionada

O [plano](../fase2-plano-avaliacao.md) continua a exigir BF antes do refactoring,
calibração, comparabilidade e todos os casos com estado/bytes verificados. Os
60 IDs mantêm-se, com U25 G. A seleção individual UP-C1/C2/C3 A não congela o
manifesto, não aprova os restantes limiares e não substitui a revisão completa
dos requisitos. Os dois conjuntos retidos e a prova real anónima desconhecida
permanecem preservados. IA: preparação apoiada por Codex com a skill Inception.

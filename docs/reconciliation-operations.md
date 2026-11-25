# Reconciliação administrativa de execuções (B11, OPS-C1 A)

`ops/reconcile` trata execuções interrompidas; não repete ferramentas, uploads,
mutações nem billing. Uma execução perdida só pode voltar a correr por um novo
Apply explícito do utilizador, depois de resolvidos os efeitos da anterior.

## Isolamento e inventário

Usar a instalação certa, uma stack de cada vez. Nunca usar `picturas-nfr` para
desenvolvimento, `down -v`, purges globais, prunes ou restauração de snapshots por
cima de trabalho posterior. Os comandos não imprimem credenciais, IDs de domínio,
corpos de mensagens nem URLs assinados.

```bash
export PICTURAS_SECRETS_DIR=$HOME/picturas-secrets
ops/maintenance.sh isolate --project picturas-dev --mode compromise
ops/reconcile inventory --project picturas-dev
ops/reconcile status --project picturas-dev
```

O B10 termina todos os participantes, incluindo workers e ligações persistentes,
sem esperar pelos jobs perante compromisso. Cada ação de reconciliação exige o
gate fechado e todos os participantes parados. Sobe temporariamente **apenas** os
três MongoDB, RabbitMQ e SeaweedFS, sem dependências, ingress ou consumidores; no
fim pára-os. Overrides usados no isolamento são reutilizados. A ferramenta nunca
abre o gate.

O inventário fica em
`$PICTURAS_SECRETS_DIR/maintenance/<projeto>/<operação>/reconciliation/`:
diretórios 0700, ficheiros 0600. É evidência administrativa privada, fora do Git.
Inclui projetos e gerações, executor original, Process/Result, recibos de quota,
intenções de objetos, bytes/hash de fontes e último commit, mensagens e manifestos
de ficheiros locais. O relatório público tem apenas referência opaca e contagens.
Objetos de processamento ou diretórios sem associação conhecida, gerações antigas
sem recibo/Process e tentativas de upload pendentes impedem um inventário limpo.

## Classificação e revisão de integridade

- **Confirmada:** o ponteiro/prova de commit do domínio, o recibo vinculado à
  execução e todos os resultados/bytes conferem com o manifesto SHA-256. Ack de
  AMQP e presença de Result, isoladamente, não demonstram commit.
- **Perdida:** há prova suficiente da admissão/custo, mas não há commit de domínio
  após o isolamento observado; ou há prova de que nunca foi admitida. Os resultados
  parciais não são publicados nem promovidos.
- **Indeterminada:** faltam recibo, executor, dia, integridade, associação de
  mensagens ou prova de commit. Fica isolada e pendente, sem crédito inventado.

Uma alteração de certificados não prova integridade dos dados. Antes de aplicar,
o administrador investiga os dados e prepara um JSON **privado** de revisão, com
`operation`, `snapshot_sha256`, `integrity_verified: true` e `basis` (evidência
concreta usada na análise). Os primeiros dois valores referem o `case.json` e o
SHA-256 dos bytes de `snapshot.json`. Não copiar o inventário para relatórios
públicos. Num incidente real, não declarar dados fiáveis só porque a ferramenta
consegue lê-los; se a origem da prova não for suficiente, manter o caso pendente.

```bash
export PICTURAS_SECRETS_DIR=$HOME/picturas-secrets
ops/reconcile apply --project picturas-dev --integrity-proof /caminho/privado/review.json
ops/reconcile seal --project picturas-dev
```

A revisão tem de estar dentro da instalação privada, sem permissões de grupo ou
outros. A fixture de conformidade usa fontes sintéticas conhecidas e fotografia
nativa anterior à primeira correção como base; não simula investigação forense de
um atacante capaz de modificar todos os dados e o registo administrativo.

## Efeitos e reaplicação

Antes de qualquer compensação ou reabertura, invalida-se a geração com controlo
de versão. Run/Process mantêm a evidência e ficam marcados; não são apagados em
massa. O Apply guarda previamente o executor, custos imagem/vídeo, fontes, jobs e
IDs de mensagens. Os ficheiros vivem em diretórios exclusivos por UUID; respostas
obsoletas são recusadas antes de persistir outputs ou tentar commit.
Os caminhos de entrada/saída publicados são sempre os definidos pelo servidor;
parâmetros de ferramenta não os podem substituir. Edições de perfil e password
também não podem gravar snapshots antigos dos campos de quota.

Os objetos de processamento têm chave por execução e intenção durável anterior à
transferência. A quarentena copia **cada chave identificada**, verifica o SHA-256
dos bytes e só então apaga o original. Uma interrupção entre cópia e eliminação
retoma por leitura dos dois lados. Fontes e último commit são novamente verificados
e não fazem parte da limpeza. Uma ausência que contradiga o inventário não é
tratada como limpeza bem-sucedida.

Cada mensagem afetada é guardada com corpo/propriedades, em ficheiro privado
durável, **antes** do ack administrativo. Não existe purge nem replay. Notificações
WS antigas identificadas pelo projeto são arquivadas individualmente: todos os
sockets/contextos da instalação foram terminados. Mensagens desconhecidas impedem
o selo. A entrega ao socket de um consumidor suspenso pode aparecer como
`unacknowledged`, com `ready=0`; nenhum destes contadores prova commit.

A quota usa o **executor e dia do recibo original**, inclui imagem e vídeo, e
respeita o perfil da admissão. Saldo e identificador de compensação são escritos
na mesma atualização atómica do documento do utilizador, com revisão condicional.
Uma resposta perdida obriga a reler o marcador; não há refund cego nem novo
débito. Repetir o comando, mesmo com outro identificador de caso, não repete uma
compensação já registada. Alterações antigas sem recibo, mudanças não atribuíveis
de saldo ou underflow ficam pendentes. Não se alega uma transação entre MongoDB,
S3, broker e filesystem.

O mover de ficheiros corre separado, sem rede nem credenciais da instalação,
com apenas o volume de media gravável e o plano privado só de leitura. Exige que
os manifestos confiram, recusa symlinks e faz rename atómico para quarentena. Se o
rename ocorreu antes do crash/journal, verifica o destino em vez de mover outra
vez. Uma falha de limpeza impede o selo.

## Selo, reabertura e falhas

O selo liga a operação B10 aos hashes de toda a evidência privada e só é emitido
quando não há ambiguidades, a quota e a quarentena conferem, e os backends estão
parados. O B10 volta a verificar selo, operação, ficheiros, permissões e ausência
de pendências **antes** de arrancar consumidores. A prova técnica D-33 não é usada
por este caminho. Depois do selo, `apply` é recusado: o caso é imutável.

```bash
export PICTURAS_SECRETS_DIR=$HOME/picturas-secrets
ops/maintenance.sh reopen --project picturas-dev
```

Se a CA foi retirada, continuam obrigatórias as provas de browser e ligações
persistentes do B10; a reconciliação não as substitui. Ver
[operações PKI](pki-operations.md).
Num compromisso de identidade/confiança, executar também a retirada da CA pelo
procedimento B10 antes de reabrir. Os ensaios B11 de interrupção de trabalho não
substituem o piloto de retirada/reemissão e de confiança no browser do B10.

Exceções deixam o gate fechado e param os backends. Se o **processo host** morrer
com SIGKILL, verificar o estado dos participantes; parar explicitamente apenas os
backends acima antes de retomar. O lock B10/B11 é do kernel e é libertado mesmo
com SIGKILL; o ficheiro `operation.lock` permanece, não deve ser apagado para
forçar concorrência. Preservar os registos privados de falha e repetir a ação
administrativa após inspeção. A releitura de marcadores/precondições protege os
efeitos; não autoriza reiniciar nem repetir trabalhos de negócio.

Os failpoints `RECONCILE_FAILPOINT`/`RECONCILE_FAIL_MODE` são só de ensaio local do
processo administrativo, nunca parâmetros HTTP. Cobrem geração, cópia/eliminação,
quota, ack e selo; o modo `exit` termina o helper sem finally/journal. O relatório
de aceitação distingue workers reais de estados controlados nos limites de commit.

## Limites

Não há migração (D-15). Execuções anteriores sem o novo recibo/prova não ganham
evidência retroativamente. Uploads pendentes e mensagens desconhecidas exigem
investigação e bloqueiam o selo; esta ferramenta não é recuperação geral do fluxo
de upload, billing ou de toda a mensageria. Ledger, Run, Artifact e quarentena são
retidos para auditoria; a retenção/eliminação futura exige política administrativa
própria. Os defeitos de ack antecipado herdados continuam declarados.

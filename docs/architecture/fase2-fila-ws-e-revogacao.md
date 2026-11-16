# Fase 2 — Fila WS, revogação e ligações persistentes

**Equipa:** PL2-G4. **Preparado:** 16/11/2026. **Revisão de origem:** `3d31003`.
**Estado:** WS-C4 A, PKI-C2 B e PKI-C3 A validadas individualmente pelo utilizador,
registadas em 2026-11-16T20:14:36Z. O restante detalhe concretiza essas condições;
não representa acordo dos quatro elementos, requisitos completos aprovados ou
capacidade demonstrada. A recomendação inicial PKI-C2 A/CRL fica **substituída pela
escolha B**. Não há CRL no mecanismo escolhido para esta entrega.

Mantêm-se WS-C1/C2/C3 A, PKI-C1 A, ACL-C1 A e as restantes validações em
[decisões](../fase2-ideias-1-e-2.md). O par QC-06/QC-05 não está em discussão.
Requisitos completos e baseline formal continuam incompletos.

## Decisões, alternativas e custos

| Ponto | Escolha individual validada | Alternativa não escolhida e custo da decisão |
|-------|----------------------------|---------------------------------------------|
| WS-C4 A | Inicialmente 16 lotes pendentes por processo WS, além das 4 consultas ativas; no máximo 1 lote pendente por projeto; manter plano pendente mais recente sem reiniciar prazo total 1 s | B: 64 lotes. A limita acumulação; pode recusar picos que um buffer maior absorveria, sem capacidade ou prazo demonstrados em qualquer opção. |
| PKI-C2 B | Para retirar confiança a um certificado, substituir a CA e reemitir todos os certificados dessa instalação, retirando a confiança antiga de todos os participantes | A: CRL local assinada. B dispensa gerir CRL/distribuição/validade/versões e verificar suporte desse mecanismo em cada canal, mas um serviço comprometido afeta a disponibilidade de toda a instalação. |
| PKI-C3 A | Manutenção com isolamento e reinício controlado; verificar ligações antigas/retomadas e fluxos completos antes de reabrir; instalação parcial permanece isolada | B: recarregamento em funcionamento/drenagem seletiva. A admite interrupção e coordenação administrativa, sem duração medida; evita implementar rotação em funcionamento nesta entrega. |

**Confiança:** média na adequação/complexidade relativa e no tamanho da fila.
O contexto local independente favorece um procedimento único de retirada de
confiança, mas não existe comparação experimental de custo ou disponibilidade.
Não apresentar a interrupção como gratuita nem como comprovadamente curta.

## WS-C4 A — limites, admissão e justiça

1. Os **16 lotes pendentes** são o total de lotes de autorização admitidos mas ainda
   sem execução HTTP no processo WS, incluindo entradas e revalidações. Há até
   **4 consultas ativas globais**, no máximo **1 ativa e 1 pendente por projeto**.
   Não criar filas adicionais ilimitadas de joins, callbacks, promessas ou ciclos.
   Réplicas futuras exigem redimensionamento; estes números não são limites globais
   de um conjunto arbitrário de réplicas.
2. Cada lote respeita conjuntamente **50 avaliações** e **65 536 bytes UTF-8 por
   corpo JSON**. Dezasseis corpos pendentes no limite representam até **1 MiB de
   JSON serializado**, não 1 MiB de memória total: objetos, referências, respostas,
   sockets e estado de membros têm custos adicionais a medir.
3. Cada avaliação conserva o instante original de admissão e o seu deadline de
   **1 s total**. Agregar, dividir lotes ou repetir uma tentativa não reinicia o
   relógio. O transporte só pode consumir o tempo restante. Não avaliar uma
   resposta após o deadline; cancelar o trabalho de rede quando deixar de ser útil.
4. **Segundo pedido do mesmo projeto:** manter o plano pendente mais recente,
   substituindo o anterior no mesmo slot. Conservar o instante original de entrada
   e nunca deslocar o deadline para a frente: o novo plano usa o menor entre o
   deadline já existente e os prazos originais das avaliações que contém. Remover
   expirados antes de admitir/substituir/ativar e ao vencer o prazo; substituir não
   reanima um pedido expirado. Uma consulta já ativa não é outro slot pendente.
   Cancelar/inutilizar avaliações realmente obsoletas por sujeito/contexto/geração,
   sem invalidar resultados de outros membros só por pertencerem ao mesmo projeto.
   Novos joins exigem decisão fresca. Callbacks de joins retirados/substituídos
   recebem indisponibilidade/substituição explícita (nome concreto ainda proposto),
   nunca silêncio ou sucesso herdado. Revalidações retiradas deixam a pertença
   marcada como devida no estado existente, sem renovar a autorização ou criar
   outra fila. Um novo contexto que não caiba no lote/slot é recusado explicitamente;
   não guardar uma promessa ilimitada para o atender depois. Esta concretização
   preserva membros/contextos distintos e deve ser testada com substituições
   repetidas para detetar fome e perda de pedidos.
5. Revalidações do mesmo contexto são coalescidas, sem criar ciclos acumulados.
   Contextos de um projeto grande são percorridos por cursor, preparando lotes à
   medida que há espaço. Alternar projetos e avançar também o cursor de membros;
   conservar a posição entre ciclos para não começar sempre pelos mesmos.
   Trabalho ainda não admitido conserva o vencimento da autorização existente.
6. Fila cheia, espera excessiva, cancelamento ou falha **não concedem novas entradas
   nem renovam autorizações**. Membros existentes perdem a sala ao terminar o prazo
   previamente válido, mais cedo perante negação efetiva/JWT/permissão expirados.
   A justiça tem de abranger também projetos que não conseguiram entrar na fila;
   um cursor sobre pertenças existentes não deve tornar-se outra fila ilimitada.
7. A fila não limita o total de membros/projetos/contextos guardados. Os limites
   desse estado e a proteção contra abuso de joins continuam a precisar de revisão;
   não declarar a memória WS limitada globalmente apenas por limitar os lotes.

**Ensaios:** ocupar as 4 consultas, admitir 16 lotes, tentar o 17.º e comprovar
recusa/contabilização e ausência de crescimento escondido; medir também 1/4/16
lotes, expirados/cancelados, substituição pelo mais recente sem reiniciar prazo,
callbacks concluídos e libertação de slots. Manter o caso de 500 membros
num projeto com vários pequenos e >20 projetos ativos. Medir espera por projeto e
contexto, justiça na admissão, cadência, memória, recusas e corte ≤5 s/meta ≤2 s.
Quatro consultas simultâneas não provam 4/s nem capacidade para vinte projetos.

## PKI-C2 B — retirada de confiança por substituição da CA

**Escolha individual do utilizador:** não implementar CRL nesta entrega. Para
retirar confiança a um certificado, o script administrativo substitui a CA da
instalação, reemite **todos** os seus certificados com chaves novas e remove a CA
antiga dos trust stores de **todos** os participantes dessa instalação. Só trocar
o certificado do serviço comprometido não cumpre esta decisão. O procedimento
abrange servidores/clientes, nginx, dados/broker/storage e confiança do browser
quando dependam dessa CA, sem exigir mTLS universal. O inventário identifica todos
os consumidores; não inferir que atualizar só WS/projects completa a substituição.

Um serviço comprometido implica este procedimento completo, com indisponibilidade
e coordenação de toda a instalação. As instalações locais são independentes: não
alargar a confiança ou distribuir a chave da CA entre computadores. Manter chaves
privadas fora do Git/build/contentores aplicacionais, proteção de mounts e registo
público de emissor/serial/fingerprint/validade/versão por participante. O script não
está implementado; guardar backups administrativos protegidos e evitar restaurar
uma CA retirada como mecanismo de rollback.

**Renovação normal é distinta:** renovar um certificado que se aproxima da
expiração pode manter a CA; não exige a sua substituição. CA 365 dias é validade
máxima escolhida, não obrigação de conservar a CA durante um ano. Serviços mantêm
30 dias e renovação com 7 dias restantes. Uma CA próxima da expiração requer
substituição antes de emitir para além do seu prazo; compromisso exige retirá-la
antes disso. Não emitir certificados para além da validade da CA.

Uma renovação sob a mesma CA **não invalida por si só** o certificado anterior ainda
válido. O teste obrigatório de recusa de certificado antigo após manutenção é o
caso de **retirada de confiança/substituição da CA**. Se for necessário invalidar
imediatamente o anterior numa renovação, aplicar B também: nova CA e reemissão
completa. Não prometer recusa individual imediata sem esse procedimento. Na
renovação corrente, verificar uso do novo certificado, fecho de ligações antigas
e validade; não apresentar isso como revogação do anterior.

**Alternativa A considerada e não escolhida:** CRL local é tecnicamente viável;
OpenSSL documenta geração/revogação e Node 18 aceita CRL em contexto TLS. Porém,
seria necessário gerir publicação, validade, versões, regressões e prova de carga
em cada participante, além da substituição da CA quando necessária. B evita esses
controlos específicos da CRL, mas conserva o risco de distribuição parcial de
confiança e exige provas em todos os participantes. Não equivale a ausência de
risco operacional. As propostas de CRL 30/7 dias não são decisões vigentes.
Fontes: [OpenSSL ca](https://docs.openssl.org/3.0/man1/openssl-ca/#crl-options),
[Node 18 — TLS secure context](https://nodejs.org/download/release/v18.20.8/docs/api/tls.html#tlscreatesecurecontextoptions).

## PKI-C3 A — manutenção e fecho de ligações

**Renovação planeada:** impedir novos trabalhos, confirmar ausência de uploads e
processamentos em curso antes do corte e suspender admissões. Se não for possível
assegurar esse estado, adiar a manutenção; não matar um worker a meio e declarar
preservação só por a PKI arrancar. Parar os participantes afetados antes de trocar
credenciais/confiança, sem apagar volumes. Na retirada de confiança, substituir
a CA e todas as suas identidades/trust stores. Reiniciar carregando o conjunto
coerente de certificados/CA e verificar fluxos legítimos e, na retirada, rejeição dos
certificados emitidos pela CA antiga antes de reabrir. Se falhar, permanecer
isolado; não recuperar confiança revogada como rollback. O script deve listar participantes e versões efetivamente aplicadas.

**Incidente/compromisso de chave:** isolar imediatamente, sem esperar que os
trabalhos terminem. Registar operações interrompidas e reconciliar estado/quota/objetos; não repetir mutações cegamente nem
prometer exactly-once. A interrupção e recuperação são resultados a medir, não uma
garantia de disponibilidade contínua. A chave CA permanece fora dos processos.

O procedimento tem de fechar sockets HTTP keep-alive, ligações WS afetadas e
clientes/pools que usam o estado TLS antigo. O reinício deve eliminar também caches
de sessões TLS e chaves de tickets antigas; não persistir/restaurar esse estado.
Uma retomada anterior não pode contornar a nova revogação. Testar TLS 1.2/1.3
quando ambos forem permitidos. A configuração inicial proposta para o cliente
Node das APIs é `maxCachedSessions: 0`, sem cache de sessão explícita; configuração
equivalente dos restantes participantes exige prova, sem assumir que um único
flag elimina todos os mecanismos de retomada.
Fonte: [Node 18 — HTTPS Agent](https://nodejs.org/docs/latest-v18.x/api/https.html#new-agentoptions).

Fechar só o servidor HTTP não prova fecho do WebSocket; a API de fecho global HTTP
exclui sockets promovidos a outros protocolos. O runbook deve verificar sockets
reais/novos processos, não apenas ler os novos ficheiros.
Fonte: [Node — closeAllConnections](https://nodejs.org/api/http.html#servercloseallconnections).
Confirmar o comportamento nas versões/imagens fixadas da campanha.

Mesmo sem manutenção, nenhum canal deve continuar autorizado para além da validade
dos certificados aplicáveis. Prever guarda de validade durante funcionamento e
fecho/suspensão ao vencer, além da verificação no arranque; isto **não** é renovação
automática. A implementação por participante ainda precisa de prova, em especial
nas ligações persistentes. Um temporizador de sessão JWT não resolve validade TLS.

Após reinício do WS, o frontend reconecta explicitamente com JWT válido e consulta
nova para cada sala. Não restaurar pertenças por memória de uma ligação anterior
nem criar nova identidade anónima como atalho. Se apenas o canal WS → projects
falhar, continuam as regras já validadas: sem novos joins e autorizações existentes
até ao prazo fixado, nunca além dele. JWT HS256/identidade RS256 e ambos os conjuntos
de volumes preservados mantêm o seu âmbito anterior.

## Procedimento testável e critérios antes da reabertura

Este é o runbook especificado, **não executado**. A escolha A/B/A está validada;
o comando/script concreto, cobertura por versão e prazo operacional ainda não.

1. Identificar instalação, administrador, motivo (renovação ou retirada), versão
   atual e todos os participantes/trust stores. Confirmar os volumes a preservar.
   PKI/dados de ensaio devem ser descartáveis; não testar destrutivamente sobre os
   dois conjuntos retidos de Luís.
2. Planeada: impedir novos trabalhos e comprovar ausência de uploads/processamentos
   em curso antes do corte. Incidente: isolar logo e registar trabalhos interrompidos.
   O estado de manutenção bloqueia reabertura parcial e não depende de um mero
   ficheiro publicado que alguns serviços possam não ter carregado.
3. Preparar novo material fora do Git/build. Retirada: nova CA, chaves/certificados
   de todos os participantes e novos trust stores sem a CA antiga. Renovação normal:
   pode manter a CA, sem alegar invalidação do certificado anterior ainda válido.
4. Fechar processos/clientes/verificadores afetados e conexões persistentes; remover
   caches/tickets/sessões anteriores. Aplicar a configuração coerente e reiniciar
   isoladamente. Registar versões carregadas, identidade e validade em cada ponto.
   A existência de um ficheiro novo não prova uso do novo estado pelo processo.
5. Testar chamadas completas **ws_gateway → projects** e **projects → armazenamento**
   com certificados novos, incluindo autorização legítima e operação real sobre
   media descartável, não apenas um handshake. Verificar os restantes pares/canais
   inventariados, incluindo operações legítimas de dados/broker e TLS de servidor.
6. Na retirada, verificar **recusa de certificado da CA antiga em ligação nova**,
   que nenhum keep-alive/WS/pool antigo se mantém útil e que uma retomada TLS antiga
   falha ou exige handshake novo que recusa essa CA. Controlos negativos devem
   abranger tanto certificado de cliente como servidor nos percursos aplicáveis.
7. Simular um participante não atualizado, certificado expirado, identidade/par
   errado e falha de reinício. **Qualquer aplicação parcial mantém a instalação
   isolada.** Não reabrir só porque os dois percursos de demonstração passaram.
   Verificar a guarda de validade com uma ligação já aberta.
8. Reabrir apenas com manifesto completo e testes satisfeitos; reconectar frontend
   com JWT válido/nova autorização por sala. Confirmar dados, quota, referências de
   objetos e identidade anónima. Em falha, conservar isolamento e reconciliar
   operações interrompidas; não repetir mutações cegamente nem recuperar CA retirada.

Registar separadamente `t_detectado`, `t_isolado`, `t_nova_ca_preparada`,
versões/instantes carregados por participante, fecho de conexões antigas,
resultados dos controlos e `t_reabertura`. Medir deteção→isolamento e duração da
indisponibilidade. **PKI-C4 B fixa isolamento ≤30 s/meta ≤10 s desde comando; substituição por
medir/calibrar no piloto, sem limite prévio imposto**; ≤5 s e
meta ≤2 s continuam exclusivos da autorização de salas WS. Imediato em incidente
é a regra de iniciar isolamento sem esperar pelos trabalhos, não um tempo medido.

Mapeamento: fila em **S10/S12/S21/F07/F09**; retirada e rotação em
**S08/S09/S19/S20/F06/F07**, mais **S16/S17** nos canais de dados/broker afetados.
As 60 métricas continuam as mesmas. Todos os resultados destes mecanismos são NM.

## Critérios posteriores — validação individual B/A/A

O [contrato operacional detalhado](fase2-criterios-operacionais-seguranca.md)
regista **PKI-C4 B/PKI-C5 A/OPS-C1 A**: isolamento ≤30 s/meta ≤10 s desde comando
até corte de novas/persistentes/consumidores/efeitos; substituição medida sem
15/5 min impostos, piloto planeado até 23/11 às 18:00; matriz atual/alvo completa
com browser manual sem ultrapassar avisos e mTLS real no mock; reconciliação
administrativa implementada/ensaiada até à entrega, ou limitação explícita.
Ack antecipado continua defeito conhecido; recuperação automática futura.
Mecanismos e critérios escolhidos não demonstram execução. Instalação/carga,
concretização/testes de isolamento, terminação por canal e ferramenta continuam
por realizar; nenhum novo ensaio/alteração à aplicação foi feito nesta revisão.

## Para a apresentação e o relatório

**Porquê A/B/A:** limita acumulação de consultas e concentra a retirada de confiança
num procedimento administrativo único com manutenção. A CRL era uma recomendação
inicial, substituída pela preferência explícita do utilizador; não a descrever como
inválida nem como testada. O custo aceite é coordenação e interrupção da instalação
inteira quando se retira um certificado, inclusive perante um único serviço
comprometido. Não existe comparação experimental que prove menor esforço ou duração
curta. Reconsiderar CRL/rotação em funcionamento se surgir uma exigência concreta de
continuidade; fila maior só com evidência de benefício dentro do deadline.

**Por fechar:** piloto de substituição até 23/11 às 18:00, instalação/carga,
verificações/configuração por canal e versão e ferramenta/procedimento ensaiado
de reconciliação até à entrega, limites do estado/
abuso WS, corpus final e restantes decisões de sessões/uploads. O runbook e os
critérios acima permitem rever a escolha, sem declarar PKI completa. Não foram
executados ensaios, gerados certificados, implementado script PKI, alterada a
aplicação nem criado commit nesta revisão. Validação individual, sem acordo
atribuído aos restantes elementos.

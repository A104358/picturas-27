#import "../template.typ": *

= Utilização de IA

#orientacao[
  *Origem:* Exercício 6, Bloco 2, secção 7, e Exercício 7, secção 6.

  Obrigatório: documentar as ferramentas, os modelos e as _skills_ utilizadas, enumerar as tarefas apoiadas e comprovar a
  validação realizada pela equipa, tanto na análise e na escrita como no código e nas medições. A equipa é responsável
  por todo o conteúdo entregue, incluindo o gerado por IA.

  Valoriza-se evidência concreta (_commits_, ficheiros de configuração dos agentes) e reflexão crítica: o que a IA
  fez bem, onde errou, como o erro foi detetado e o que foi rejeitado e porquê. Não basta dizer que a IA foi usada; é preciso mostrar
  que o resultado foi verificado.
]

== Ferramentas, modelos e configuração

#tabela(
  colunas: (3.5cm, 1fr),
  [Ferramenta / modelo], [Configuração e utilização (_skills_, instruções de projeto, MCP, …)],
  [Antigravity / Codex, _skill_ local `specsmd-inception-agent`], [Skill de Inception do fluxo AI-DLC local (`.specsmd/aidlc/`), acesso ao código-fonte, configuração, documentos e registo `memory-bank/`. Sem acesso a segredos nem execução de testes de _runtime_ no âmbito de RNF.],
  [Claude Code (CLI) com Claude Opus 5.5 (`claude-opus-5-5`)], [Verificação final (B12), campanhas EXP e MF e apoio à redação dos capítulos 8, 10 e 11. Instruções de projeto em `AGENTS.md` (arquitetura, comandos, armadilhas conhecidas e a regra de não alterar `evaluation/med.py`, `medlib/`, `criteria.yaml` e `cases/`). Estado e regras partilhados em `docs/refactor-plano.md` e `docs/refactor-handoff.md`: ponto atual (§1), decisões (§2.6), diário (§4) e dúvidas (§5), com o pedido de retoma da §6 e numeração própria (decisões ímpares a partir de 41, dúvidas pares a partir de D-30). Regras dadas pelo utilizador em cada sessão: só _commits_ locais, um por passo fechado, com `Co-Authored-By: Claude Opus 5.5`, e nunca _push_. Antes de cada _commit_, varrimento de segredos e `git add` ficheiro a ficheiro, uma só _stack_ ativa, parar sem `-v`, nada de _prunes_ nem de apagar volumes ou imagens sem autorização. Nunca mostrar segredos, JWT ou URLs assinados. Paragem obrigatória em três casos: decisão que muda critério, âmbito ou segurança. Métrica ou guarda falhada sem correção óbvia, necessidade de apagar dados. Acesso à _shell_ local e ao Docker. Os segredos ficam em `$PICTURAS_SECRETS_DIR`, lidos pelos testes mas nunca impressos.],
  [#preencher[Ferramenta(s) usadas nos blocos B0–B11]], [#preencher[Confirmar com cada elemento que ferramenta e modelo usou em cada bloco (os _commits_ de B0 a B11 não têm atribuição de IA) e com que configuração. O pedido de retoma da §6 do _handoff_ foi escrito para «Claude Code ou outro» agente.]],
)

== Tarefas apoiadas e validação

#tab([Tarefas apoiadas por IA e validação],
  tabela(
    colunas: (2.6cm, 2.4cm, 2.4cm, 2.8cm, 2.8cm),
    tamanho: 8.5pt,
    [Ferramenta / modelo / _skill_], [Tarefa apoiada (capítulo)], [O que foi aceite], [O que foi rejeitado e porquê], [Como foi validado pela equipa],
    [Antigravity/Codex, `specsmd-inception-agent`], [Caps. 2–6 (Bloco 1 e 2): leitura de materiais/código, continuação de IDs, cruzamento de decisões/pilotos, formulação de QS/CAND e redação de _trade-offs_], [Rastreabilidade e distinção entre base, decisões individuais e hipóteses, cenários com seis elementos, priorização argumentada], [Confundir mTLS com autorização de operação, afirmar ganhos sem BF. Inventar aprovações do grupo que não ocorreram. Retirar o legado antes de fechar UP-C4–C9], [Utilizador forneceu equipa, par e escolhas com âmbito registado. Confronto estático com código/fontes e histórico. Revisão académica nominal pela equipa ainda pendente.],
    [Antigravity/Codex, verificações estáticas locais], [Caps. 2–4 (Bloco 1): organizar fontes com _hash_, comparar aplicação, conferir IDs/cópias/caminhos/diagramas Mermaid], [Material original intacto, referências explícitas, revisão de cenários/matriz/filas], [Inventar testes, fontes letivas ausentes, medidas finais ou livros não consultados], [Registo de verificação (`evidence/verification-2026-11-20.md`), validação automática não substitui revisão nominal nem teste de arquitetura em _runtime_],
    [Antigravity/Codex, `specsmd-inception-agent`], [Caps. 7–10 (Ex. 7): sintetizar táticas/DA e vistas, elaboração do plano de medição], [Distinção entre base, decisões individuais e hipóteses. Vistas Mermaid com TAT por fronteira, plano de medição concretizado], [Prometer implementação ou resultados. Escolher UP-C4–C9 por preencher a ficha. Somar setas da matriz de efeitos como _ranking_ quantitativo], [Confronto com fontes/código e histórico, utilizador comunicou escolhas anteriores, equipa deve rever esta resolução],
    [Claude Code, Claude Opus 5.5], [Verificação final B12 (caps. 8 e 10): fecho do UL-10, ajuste da U01, regressão F01–F05, conformidade completa e EXP], [Recolha de memória depois de cada parte _multipart_ (decisão 45). Limites do `ffprobe` injetáveis só para apertar (41), marcadores fora de `/tmp` (43). Correção do _watermark_, um defeito anterior à fase encontrado pela regressão (47). Libertação da vaga quando a _media_ é apagada antes do _hash_ (51), com teste próprio, suítes `run-b12.sh`, `b12-regression.py`, `b12-browser-export.py`, `b12-hash-orphan.py` e `b8-outage.py`], [Usar `--force` no _preflight_ e baixar o mínimo de disco da MF (a MF correu com os 60 GiB do plano). Repetir os pilotos B10 na verificação final (não repetidos e declarado: decisão 49), mexer no instrumento congelado], [Cada correção tem um teste que falha antes e passa depois (por exemplo, `b12-hash-orphan.py`: 2 vagas presas antes, 0 depois). Resultado bruto de cada suíte em `tests/conformance/results/2026-11-25/`. _Commits_ locais `db8d10f` a `9565243`. O _push_ e o _merge_ em `main` (`e0a880a`) foram feitos pelo utilizador],
    [Claude Code, Claude Opus 5.5], [Dúvidas D-30 a D-38 (cap. 8): diagnóstico e opções quando uma métrica falhava ou faltavam recursos], [Opções escolhidas pelo utilizador: D-30 A (suspensão do contexto WS, decisão 53), D-32 A e D-34 A (espaço em disco, decisões 55 e 57), D-36 B (segunda MF completa, decisão 59) e D-38 A (decisão 61)], [As restantes opções de cada dúvida, por exemplo D-30 C (declarar o risco do instrumento e aceitar a S04 inconclusiva) e D-36 C (aceitar a U10 da MF1 sem repetir)], [Nenhuma decisão de critério, âmbito, segurança ou apagamento de dados foi tomada pelo agente: cada dúvida ficou registada no _handoff_ (§5) com opções e recomendação, e só depois da resposta do utilizador se agiu. A regra da decisão 59 foi posta em _commit_ (`e1ee41b`) antes de correr a segunda MF],
    [Claude Code, Claude Opus 5.5], [Campanhas MF, `compare` e redação (caps. 8, 10 e 11)], [MF1 e MF2, `compare` com a BF, tabela BF → MF, notas para o relatório no _handoff_. Rascunho dos capítulos 8, 10 e 11 a partir de `compare.md`, `summary.json` e do _handoff_], [Apresentar o resultado da U10 na MF1 como ruído provado: fica registado como inferência, omitir a MF1: é reportada], [Números conferidos com `evaluation/results/MF-20261125T153646Z/compare.md` e `summary.json`, no repositório. Varrimento de segredos dos resultados antes de cada _commit_. #preencher[Revisão da redação pela equipa: quem e quando]],
  ),
)

== Análise crítica

A IA apoiou eficazmente a leitura transversal de múltiplos documentos técnicos (código, configuração, PDF, exercícios), a manutenção da coerência de IDs e a distinção sistemática entre factos (EV-nn), hipóteses (H-nn) e decisões individuais versus aprovações do grupo. O fluxo AI-DLC com a _skill_ `specsmd-inception-agent` estruturou o processo de Inception e manteve o registo do `memory-bank/` atualizado.

As principais limitações observadas foram: (1) tendência para sugerir afirmações de conformidade ou aprovação que não tinham suporte documental: corrigidas pela instrução explícita de não inventar aprovações nem resultados. (2) necessidade de verificação humana dos IDs de evidências e hipóteses, pois a IA pode incorretamente propor reutilização de IDs eliminados. (3) nesta fase de análise a IA não executou testes de _runtime_ nem mediu latência ou memória real.

Na implementação e na medição (Claude Code), a IA executou testes, campanhas EXP e as duas MF, e foi aí que se mostrou mais útil. Ao repetir medições em vez de as dar como fechadas, encontrou defeitos reais: a vaga de _upload_ presa quando a _media_ era apagada antes do _hash_ (todo o _upload_ de vídeo passava a dar 429 a partir de três órfãos), o _watermark_ que falhava sempre desde a base, e a perda do contexto WS dos controlos quando a `projects` reiniciava. Em cada caso o defeito ficou com um teste que o reproduz. As regras de paragem também funcionaram: as cinco dúvidas (D-30 a D-38) foram levadas ao utilizador com opções e recomendação, em vez de resolvidas pelo agente.

Os erros e limites observados nessa fase foram:
- *Ambiente.* Arrancou uma EXP com a _stack_ de desenvolvimento ainda ativa. Foi detetado e corrigido antes de medir, e ficou registado.
- *Testes novos com defeitos.* As primeiras versões tinham erros (um pedido sem `X-Project-Version`, um `\n` literal), só detetados ao correr os testes.
- *Estimativas de disco erradas duas vezes.* Na D-34 e na D-38, apagar imagens libertou menos do que o previsto, por causa das camadas partilhadas. Na D-34 foi preciso também limpar a cache de _build_ e a D-38 foi uma decisão extra.
- *Causas não provadas.* A falha da U10 na MF1 foi atribuída a ruído do _host_ por inferência, e a observação U20 da EXP ficou sem causa determinada.
- *Risco de seleção.* Recomendar a repetição de uma campanha depois de ver o resultado traz esse risco, mitigado com a regra fixada em _commit_ antes da segunda MF.

Em todos os casos, a IA não substitui a decisão nem a revisão humanas.

A equipa é responsável pela validação de todo o conteúdo entregue, incluindo a justificação das decisões técnicas, a coerência dos cenários de qualidade e os resultados das medições após a realização das campanhas.

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
  [Antigravity / Codex; _skill_ local `specsmd-inception-agent`], [Skill de Inception do fluxo AI-DLC local (`.specsmd/aidlc/`); acesso ao código-fonte, configuração, documentos e registo `memory-bank/`; sem acesso a segredos nem execução de testes de _runtime_ no âmbito de RNF.],
)

== Tarefas apoiadas e validação

#tab([Tarefas apoiadas por IA e validação],
  tabela(
    colunas: (2.6cm, 2.4cm, 2.4cm, 2.8cm, 2.8cm),
    tamanho: 8.5pt,
    [Ferramenta / modelo / _skill_], [Tarefa apoiada (capítulo)], [O que foi aceite], [O que foi rejeitado e porquê], [Como foi validado pela equipa],
    [Antigravity/Codex; `specsmd-inception-agent`], [Caps. 2–6 (Bloco 1 e 2): leitura de materiais/código, continuação de IDs, cruzamento de decisões/pilotos, formulação de QS/CAND e redação de _trade-offs_], [Rastreabilidade e distinção entre base, decisões individuais e hipóteses; cenários com seis elementos; priorização argumentada], [Confundir mTLS com autorização de operação; afirmar ganhos sem BF; inventar aprovações do grupo que não ocorreram; retirar o legado antes de fechar UP-C4–C9], [Utilizador forneceu equipa, par e escolhas com âmbito registado; confronto estático com código/fontes e histórico. Revisão académica nominal pela equipa ainda pendente.],
    [Antigravity/Codex; verificações estáticas locais], [Caps. 2–4 (Bloco 1): organizar fontes com _hash_, comparar aplicação, conferir IDs/cópias/caminhos/diagramas Mermaid], [Material original intacto, referências explícitas, revisão de cenários/matriz/filas], [Inventar testes, fontes letivas ausentes, medidas finais ou livros não consultados], [Registo de verificação (`evidence/verification-2026-11-20.md`); validação automática não substitui revisão nominal nem teste de arquitetura em _runtime_],
    [Antigravity/Codex; `specsmd-inception-agent`], [Caps. 7–10 (Ex. 7): sintetizar táticas/DA e vistas; elaboração do plano de medição], [Distinção entre base, decisões individuais e hipóteses; vistas Mermaid com TAT por fronteira; plano de medição concretizado], [Prometer implementação ou resultados; escolher UP-C4–C9 por preencher a ficha; somar setas da matriz de efeitos como _ranking_ quantitativo], [Confronto com fontes/código e histórico; utilizador comunicou escolhas anteriores; equipa deve rever esta resolução],
    [#preencher[Implementação e medição]], [#preencher[Caps. 8 e 10]], [#preencher[…]], [#preencher[…]], [#preencher[a validar após implementação e medição]],
  ),
)

== Análise crítica

A IA apoiou eficazmente a leitura transversal de múltiplos documentos técnicos (código, configuração, PDF, exercícios), a manutenção da coerência de IDs e a distinção sistemática entre factos (EV-nn), hipóteses (H-nn) e decisões individuais versus aprovações do grupo. O fluxo AI-DLC com a _skill_ `specsmd-inception-agent` estruturou o processo de Inception e manteve o registo do `memory-bank/` atualizado.

As principais limitações observadas foram: (1) tendência para sugerir afirmações de conformidade ou aprovação que não tinham suporte documental — corrigidas pela instrução explícita de não inventar aprovações nem resultados; (2) necessidade de verificação humana dos IDs de evidências e hipóteses, pois a IA pode incorretamente propor reutilização de IDs eliminados; (3) a IA não executou testes de _runtime_, não mediu latência ou memória real, e não pode substituir a campanha BF/MF.

A equipa é responsável pela validação de todo o conteúdo entregue, incluindo a justificação das decisões técnicas, a coerência dos cenários de qualidade e os resultados das medições após a realização das campanhas.

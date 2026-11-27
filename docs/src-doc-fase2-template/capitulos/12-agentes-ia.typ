#import "../template.typ": *

= Utilização de IA

== Ferramentas, modelos e instruções

A equipa usou agentes de IA no diagnóstico, no planeamento, na implementação, nos testes e na redação. A atribuição abaixo limita-se aos registos disponíveis: um resultado de teste executado por um agente não é apresentado como revisão humana.

#tab([Ferramentas e configuração registadas], tabela(
  colunas: (3.8cm, 1fr),
  [Ferramenta / modelo], [Configuração e âmbito],
  [Antigravity / Codex, análise inicial], [A documentação dos exercícios regista a utilização da skill local `specsmd-inception-agent`, do fluxo AI-DLC (`.specsmd/aidlc/`) e do `memory-bank/`. O nome exato do modelo não ficou registado nesses artefactos. O âmbito inicial era análise e planeamento; não incluía novos ensaios de runtime.],
  [Codex e agentes de implementação, B0–B11], [Os registos de execução identificam Codex, por exemplo no piloto PKI B10, e o handoff identifica o trabalho dos agentes por bloco. Não existe uma atribuição verificável de ferramenta/modelo para cada bloco B0–B11; essa granularidade não é reconstituída por suposição. As instruções comuns estão em `AGENTS.md`, no plano e no handoff.],
  [Claude Code CLI / Claude Opus 5.5], [Modelo `claude-opus-5-5` registado no relato de B12 e nos trailers de coautoria de commits. Apoio ao fecho de UL-10, memória do adaptador, regressão, conformidade, EXP, duas MF, diagnóstico das falhas e redação dos resultados. Shell/Docker e acesso controlado aos segredos de teste, sem os publicar.],
  [Codex, consolidação do relatório em 27/11], [Inspeção do código final e dos documentos, confronto de manifestos/resumos/brutos BF/MF, correção de referências, diagramas e instruções, compilação Typst e inspeção do PDF. Não voltou a executar campanhas oficiais nem alterou a aplicação ou o instrumento congelado.],
))

As regras comuns exigem leitura do plano/handoff, preservação dos identificadores EV/H/QS/CAND/TAT/DA, decisões e dúvidas registadas, testes de conformidade por bloco e nenhuma alteração ao instrumento congelado fora das exceções autorizadas. Segredos, JWT, tokens de upload, links de partilha e URLs assinados não entram no relatório. Novas decisões de âmbito, critério ou segurança e ações destrutivas dependem do utilizador. Na consolidação documental não foram criados commits nem efetuado push. O histórico do B12 regista uma autorização específica anterior para commits locais assistidos por Claude; o push e a integração em `main` foram feitos pelo utilizador.

== Tarefas apoiadas e validação

#tab([Contributos de IA, evidência e validação], tabela(
  colunas: (2.5cm, 1fr, 1fr), tamanho: 8.5pt,
  [Âmbito], [Contributo aceite], [Validação e limites],
  [Diagnóstico (caps. 2–6)], [Leitura transversal de código/PDF, organização de fontes, classificação dos padrões, alternativas ALT-1/ALT-2, cenários e par QC-06/QC-05.], [Confronto com código e fontes, cópias com hashes e revisão de 20/11 em `docs/exercises/07-architectural-tactics/evidence/verification-2026-11-20.md`. As escolhas do utilizador foram distinguidas de hipóteses e de aprovações coletivas.],
  [Planeamento (caps. 7–9)], [Síntese de táticas/decisões, desenhos, plano B0–B12, corpus, métricas e condições de preservação.], [Decisões e dúvidas documentadas no handoff. Rejeitadas afirmações de ganho sem BF, equivalência entre mTLS e autorização, capacidades novas fora do âmbito e alterações arbitrárias de limiares.],
  [Implementação B0–B11], [PKI/segredos, credenciais por serviço, identidades/ACL, upload, autorização WS, sessões e operação administrativa.], [Spikes, matrizes de rotas/canais, testes por bloco e EXP. Evidência em `tests/conformance/results/` e `docs/refactor-handoff.md`. As decisões humanas precedem os desvios de arquitetura. Não se atribui cada alteração a um modelo sem registo.],
  [Verificação B12], [Ajuste U01, fecho UL-10, correção do hash órfão e do watermark herdado, suíte conjunta e regressão.], [Reprodução antes/depois do defeito do hash: vagas presas antes e libertadas depois. F01: 11 testes Node e 74 de vídeo; regressão: 105/105; exportação: 4/4. Brutos de 25/11.],
  [Dúvidas e medições], [Diagnóstico de S04/U10, opções de suspensão WS e repetição integral da MF.], [D-30/D-32/D-34/D-36/D-38 respondidas pelo utilizador. Regra da MF2 oficial em commit `e1ee41b` antes da execução. As duas MF são conservadas; ruído do host é uma inferência, não uma causa demonstrada.],
  [Relatório final], [Consolidação das 21 métricas, desvios/limitações, reprodução e PDF.], [Resultados cruzados com `compare.md`, `summary.json`, `manifest.json` e brutos. Revisão humana em 26/11/2026 por um elemento do grupo, confirmada pelo utilizador; o nome e uma ata individualizada não foram fornecidos. As alterações documentais de 27/11 são posteriores a essa revisão.],
))

== Reflexão crítica

A IA foi útil para ligar fontes dispersas, manter a rastreabilidade e repetir verificações que encontraram defeitos concretos. O hash órfão podia ocupar as três vagas e bloquear todos os uploads de vídeo; o watermark falhava já na base; a interrupção da projects fazia perder o contexto WS legítimo. Os testes reproduziram estes problemas e verificaram as correções.

Os registos também mostram limites. Houve sugestões iniciais de conformidade sem prova, confundindo desenho com implementação, que foram rejeitadas. Algumas primeiras versões dos testes falharam por erros do próprio harness, incluindo um pedido sem versão do projeto e uma quebra de linha literal. Uma EXP foi preparada com a stack de desenvolvimento ainda ativa e corrigida antes da medição. As estimativas de espaço libertado ignoraram camadas partilhadas, exigindo novas decisões do utilizador. A causa da falha isolada U20 numa EXP continua desconhecida; a atribuição da U10 da MF1 ao ruído do host não foi provada.

Na revisão documental, a versão inicial do instrumento e estados antigos «por implementar» ainda apareciam junto de resultados finais. Foram corrigidos pela consulta dos manifestos e pela separação explícita entre diagnóstico histórico e implementação final. A compilação e os controlos estáticos verificam consistência técnica do documento; não substituem a apreciação académica ou a revisão humana. A equipa mantém a responsabilidade pelo conteúdo entregue e pela interpretação dos resultados.

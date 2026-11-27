#import "../template.typ": *

= Introdução

#orientacao[
  Uma a duas páginas, no máximo. O leitor deve perceber, sem ler o resto, o que é este documento e em que se baseia.
  Respondam a:
  - *Propósito da fase*: que requisitos não funcionais do PictuRAS se pretende melhorar, por _refactoring_ e sem novas
    funcionalidades, e porquê.
  - *_Baseline_*: em que versão do sistema se basearam (_commit_ de partida), a mesma em todos os exercícios. Este
    relatório *estende* os documentos de base; não os reescreve.
  - *Âmbito do que é apresentado*: este relatório reúne os contributos dos Exercícios 6 (Blocos 1 e 2) e 7. Reutiliza
    os respetivos _templates_: copiem o conteúdo já preenchido, *mantendo os IDs* (`EV`, `H`, `ALT`, `QS`, `CAND`,
    `TAT`, `DA`), porque é através deles que os capítulos se encadeiam.
  - *Organização do documento*: Partes II (diagnóstico), III (qualidade), IV (táticas, decisões, medição e resultados)
    e V (síntese).
]

== Propósito e âmbito

Este relatório documenta a Fase 2 do projeto PictuRAS para a equipa PL2-G4, cujo objetivo é a melhoria de dois requisitos não funcionais distintos da aplicação por _refactoring_, preservando integralmente o comportamento funcional existente: o processamento de imagens, o processamento de vídeo, as quotas, a partilha e todos os fluxos já entregues na Fase 1.

Os dois requisitos selecionados são:

+ *CAND-1 (QC-06): Segurança: confidencialidade, integridade e autenticidade.* A proteção conferida pelo API Gateway não cobre todas as identidades, rotas, dados de armazenamento e admissão ao canal WebSocket. Verificaram-se efeitos indevidos nas fronteiras internas. A melhoria consiste em verificar confiança e autorização em cada fronteira relevante (nginx, gateways, `projects`, `wsGateway` e acessos a dados) sem bloquear as operações legítimas de imagem e vídeo.

+ *CAND-2 (QC-05): Eficiência de desempenho: utilização de recursos no carregamento de ficheiros.* Os três serviços Node recebem o corpo integral dos carregamentos em memória. Esta situação provoca picos de RSS, retenção pós-envio e episódios de OOM em vídeos de maior dimensão. A melhoria consiste em separar o transporte do corpo do controlo, reduzindo a memória acumulada nos serviços Node, mantendo os limites por perfil, a quota reservada apenas no _Apply_ e a compatibilidade da API.

Ambas as melhorias incidem sobre a extensão de vídeo enquadrada no padrão global de microserviços, sem alterar os efeitos PIL/FFmpeg, o formato dos resultados, nem acrescentar novas funcionalidades.

== _Baseline_ e repositório
#tab([Artefactos de partida],
  tabela(
    colunas: (5cm, 1fr),
    [Artefacto], [Versão / referência],
    [Documento de requisitos de base (Fase 1 2025/2026)], [doc-ext-requisitos.pdf],
    [Documento de requisitos da extensão de vídeo], [doc-ext-requisitos-2627.pdf: PL1-G4, v2.0, 2026-10-23],
    [Documento de solução arquitetural de base], [doc-sol-arquitetural.pdf: Fase 2 2025/2026],
    [Repositório de partida], [`052310226c51fa57a17101c7bd1ad795674aac95` https://github.com/picturas-um/picturas-27],
    [Repositório entregue], [https://github.com/A104358/picturas-27],
    [Diretrizes da Fase 2], [Versão 1, 2026-11-04],
  ),
)

== Exercícios e versões usadas

#orientacao[
  Indiquem, para cada exercício, a versão do enunciado e do _template_ que usaram, e a versão do vosso documento que
  serviu de entrada ao exercício seguinte (Bloco 1 → Bloco 2 → Exercício 7). Isto garante que quem avalia consegue
  perceber a que regras o trabalho respondeu, caso os enunciados tenham sido atualizados durante a fase.
]

#tab([Exercícios que alimentam este relatório],
  tabela(
    colunas: (3.6cm, 2.2cm, 2cm, 2cm, 1fr),
    [Exercício], [Capítulos], [Enunciado], [Template], [Versão do documento da equipa],
    [Exercício 6, Bloco 1: padrões arquiteturais], [2, 3 e 4], [1.1], [1.1], [v1.3 (2026-11-18, revisão documental 2026-11-20)],
    [Exercício 6, Bloco 2: trade-offs, cenários e candidatos a RNF], [5 e 6], [1.1], [1.1], [v1.1 (2026-11-18, revisão documental 2026-11-20)],
    [Exercício 7: táticas arquiteturais], [7 a 10], [3.0], [3.0], [v1.1 (2026-11-18, revisão documental 2026-11-20)],
  ),
)

== Organização do documento

O relatório está dividido em cinco partes. A *Parte II* (capítulos 2 a 4) contém o diagnóstico arquitetural: o âmbito da solução com o caminho do vídeo em destaque, os padrões atuais (global e do vídeo) e a comparação com alternativas. As afirmações factuais são identificadas por evidências (`EV-nn`) e as previsões não verificadas por hipóteses (`H-nn`). As alternativas usam os IDs `ALT-1` e `ALT-2`. A *Parte III* (capítulos 5 e 6) apresenta os cenários de qualidade (`QS-01` a `QS-07`), a sua priorização, os efeitos colaterais entre atributos e os dois candidatos a RNF (`CAND-1` e `CAND-2`). A *Parte IV* (capítulos 7 a 10) mapeia os cenários às táticas candidatas (`TAT-01` a `TAT-13`), regista as decisões arquiteturais (`DA-1` e `DA-2`), apresenta as vistas antes e depois e descreve o plano de medição e a preservação funcional. A *Parte V* (capítulos 11 e 12) sintetiza as conclusões e regista a utilização de ferramentas de IA. O encadeamento central é: `EV`/`H` → `ALT` → `QS`/`CAND` → `TAT` → `DA` → medição BF/MF.

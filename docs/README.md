# Documentação do PictuRAS — Fase 2

**Equipa PL2-G4 · entrega: 27/11/2026 · implementação B0–B12 concluída.**

O [relatório final em PDF](src-doc-fase2-template/relatorio-fase2-PL2-G4.pdf) e as
[fontes Typst](src-doc-fase2-template/README.md) consolidam o diagnóstico, as decisões,
a implementação e a avaliação. Para instalar e utilizar a aplicação, consultar o
[README principal](../README.md). O diagnóstico dos exercícios descreve a base
`0523102`; a implementação foi integrada em `main` no merge `e0a880a`.

## Resultados oficiais

| Campanha | Código / papel | Evidência |
|---|---|---|
| BF `BF-20261121T013224Z` | Aplicação equivalente a `0523102`, checkout `d6b4497` | [Manifesto](../evaluation/results/BF-20261121T013224Z/manifest.json), [resumo](../evaluation/results/BF-20261121T013224Z/summary.json) |
| MF1 `MF-20261125T135356Z` | Primeira medição final; falha a guarda U10 (razão máxima 1,22) | [Comparação](../evaluation/results/MF-20261125T135356Z/compare.md) |
| MF2 `MF-20261125T153646Z` | **Oficial**, commit `c8a5e3d`; aplicação igual ao congelamento `9b4e87d` | [Comparação](../evaluation/results/MF-20261125T153646Z/compare.md), [manifesto](../evaluation/results/MF-20261125T153646Z/manifest.json), [resumo](../evaluation/results/MF-20261125T153646Z/summary.json) |

As 21 métricas cumprem: **19 no alvo e duas no mínimo** (U01: 45,4 MiB;
U04: SeaweedFS +142,6 MiB). Todas as sete guardas cumprem o alvo. Ambas as MF são
reportadas; a regra de adotar integralmente a segunda foi registada antes da sua
execução (decisão 59). BF/MF correram no mesmo Apple M4 Pro, com 12 CPU e 7,7 GiB
atribuídos ao Docker. EXP são ensaios intermédios, separados da comparação oficial.

O hash final do instrumento é `12c60c7f7695`, comum à MF e ao registo
`instrumento_final` da BF. A evolução autorizada de TLS e protocolo WS consta de
`instrumento_historico` da BF e das [notas de implementação](../evaluation/IMPLEMENTATION_NOTES.md).
Os resultados quantitativos de upload medem o POST legado com adaptador; o PUT
novo tem testes de conformidade próprios. Os limites desta distinção e o risco de
escritores tardios estão declarados no relatório.

## Implementação, critérios e operação

| Documento | Utilização |
|---|---|
| [Plano de refatoração](refactor-plano.md) | Decisões, blocos B0–B12, dependências, aceitação, exceções ao congelamento e limitações obrigatórias. É o plano histórico de execução, não o estado atual de cada bloco. |
| [Handoff](refactor-handoff.md) | Estado final, decisões numeradas, diário, evidências e divergências documentais verificadas na entrega. |
| [Métricas selecionadas](metricas.md) | As 14 principais e sete guardas, mínimos/alvos e sua justificação; valores congelados em `evaluation/criteria.yaml`. |
| [Plano de medição](planoMedicao.md) | Corpus, instrumentos, casos, repetições, agregação e regras de comparabilidade. |
| [Spikes B0](refactor-spikes.md) | SP-01–SP-11, alternativas e limitações que orientaram a implementação. |
| [Matriz de rotas](refactor-matriz-rotas.md) | Cobertura final de 130 declarações rota/verbo e testes de identidade/operação. |
| [Matriz de canais](refactor-matriz-canais.md) | mTLS nas APIs internas; TLS validado e privilégio mínimo nos dados; resultados por canal e principal. |
| [Operação da PKI](pki-operations.md) | Renovação, isolamento, retirada de confiança, perfis de navegador e reabertura. |
| [Piloto PKI B10](refactor-piloto-pki.md) | Três tentativas comparáveis; isolamento máximo 3,686 s e substituição contextual máxima 350,643 s. Não é SLA universal. |
| [Reconciliação administrativa](reconciliation-operations.md) | B11: isolamento, inventário, quarentena, barreiras, compensação comprovada e reabertura; sem replay automático. |
| [Conformidade](../tests/conformance/README.md) | Suites por bloco e regressão; [resultados finais de 25/11](../tests/conformance/results/2026-11-25/) conservam também tentativas corrigidas no índice. |
| [Instrumento de avaliação](../evaluation/README.md) | Uso do med.py, manifestos e resultados brutos. As instruções específicas da versão final estão também no Anexo A do relatório. |
| [Verificação da entrega](src-doc-fase2-template/verificacao-entrega.md) | Conferências documentais, métricas, integridade da evidência e PDF, sem nova campanha. |

## Diagnóstico e documentos de decisão preservados

Os textos abaixo foram escritos antes/durante a implementação. Expressões como
«por executar», «proposta» e «pendente» referem-se à data registada; não anulam o
fecho B12 nem os resultados oficiais acima. Para a versão implementada, prevalecem
as decisões posteriores registadas no handoff, as matrizes aplicadas e o relatório.

| Documento | Conteúdo histórico |
|---|---|
| [Exercício 6, Bloco 1](exercises/06-architectural-patterns/resolution.md) / [índice](exercises/06-architectural-patterns/README.md) | Padrões globais/vídeo, registo EV/H, alternativas ALT-1/ALT-2 e matriz. |
| [Exercício 6, Bloco 2](exercises/06-architectural-patterns/resolution-block-2.md) | Cenários QS-01–QS-07 e candidatos CAND-1/CAND-2. |
| [Exercício 7](exercises/07-architectural-tactics/resolution.md) / [índice](exercises/07-architectural-tactics/README.md) | Táticas TAT-01–TAT-13, DA-1/DA-2 e desenho selecionado; [revisão de 20/11](exercises/07-architectural-tactics/evidence/verification-2026-11-20.md). Os SVG finais estão nas fontes do relatório. |
| [Ideias 1 e 2](fase2-ideias-1-e-2.md) | Escolhas comunicadas, alternativas e fundamentos. |
| [Catálogo de métricas](fase2-metricas-e-baseline.md) | Exploração de 60 dimensões; não equivale às 21 métricas finais. |
| [Plano inicial de avaliação](fase2-plano-avaliacao.md) / [revisão](fase2-revisao-plano-avaliacao.md) | Evolução da escolha do host e EVAL-B1/C1/R1/M1. A escolha Linux de 18/11 foi substituída pelo Mac oficial em 20/11. |
| [Upload: decisões](architecture/fase2-upload-decisoes-pendentes.md) / [ciclo de vida](architecture/fase2-upload-ciclo-vida.md) | UP-C1–C9 e estados/limites. A exceção ao tempo absoluto do PUT e a divergência de limpeza estão declaradas no relatório. |
| [Contrato WS](architecture/fase2-contrato-websocket.md) / [fila e retirada](architecture/fase2-fila-ws-e-revogacao.md) | Limites e autorização WS/PKI. A decisão 53 posterior suspende os contextos cuja autorização expira durante falha, em vez de os remover. |
| [Critérios operacionais](architecture/fase2-criterios-operacionais-seguranca.md) | PKI-C4/C5 e OPS-C1; aceitação executada nos blocos B10/B11. |
| [Sessões, identidade e partilhas](architecture/fase2-sessoes-identidade-partilhas-ws.md) | JWT-C1, SESS-C1, LINK-C1 e respetivos residuais. |
| [Inventário inicial de sessões](architecture/fase2-inventario-sessoes.md) / [recuperação anónima](architecture/fase2-recuperacao-anonima.md) | O reset sem dados reais (D-15) dispensa migração; mantém-se a recuperação assistida para expirações futuras, ensaiada com fixtures. |
| [Memory bank](../memory-bank/intents/001-phase-2-quality-improvements/) / [evidência exploratória](../memory-bank/intents/001-phase-2-quality-improvements/evidence/README.md) | Exploração, acordo do par e pilotos B14/B16; não se agregam às campanhas oficiais. |

Os ficheiros em `docs/templates/` são modelos de preparação e casos privados, não
resultados de execução. Os originais em `exercises/*/sources/` são preservados.

## Referências académicas

| Fonte | Âmbito |
|---|---|
| [Requisitos da base](requirements/doc-ext-requisitos.pdf) | 2025/2026, imagens, presets, IA e partilha. |
| [Requisitos da extensão de vídeo](requirements/doc-ext-requisitos-2627.pdf) | PL1-G4, versão 2.0, 2026/2027. |
| [Solução arquitetural herdada](architecture/doc-sol-arquitetural.pdf) | 2025/2026, arquitetura anterior à extensão. |
| [Diretrizes da fase 2](guidelines/fase-2-guidelines-1.pdf) | Versão 1; a entrega de 20/11 no original foi atualizada para 27/11 por indicação do utilizador. |
| [Aula 11 — Architectural Styles](lectures/RAS-slidesEN-11-ARCH-Styles.pdf) | Estilos, vistas, Pipes and Filters e Batch Sequential. |

# 📝 Exercício 6 (Bloco 2) — Template de Trade-offs, Cenários de Qualidade e Candidatos a RNF
### Fase 2: Melhoria de Requisitos Não Funcionais do PictuRAS · Alimenta as secções de diagnóstico e de decisões arquiteturais do relatório da Fase 2

**Versão do template:** 1.1 · **Data:** 2026-11-04 · **Estado:** Em vigor · **Enunciado compatível:** 1.1

> **Como usar este template**
> - Segue o enunciado `RAS-exercicio_6_bloco2_SWdesign_PT.md` e **continua o template do Bloco 1 já preenchido** (`RAS-exercicio_6_bloco1_SWdesign_template_PT.md`). As secções 4 a 7 deste template correspondem, por ordem, aos pontos 4 a 7 do **Resultado Esperado**.
> - A numeração das secções (4 a 7) e dos IDs continua a do Bloco 1. Reutiliza os `EV-nn`, `H-nn` e `ALT-n` do Bloco 1 e acrescenta os novos ao registo da secção 2.6 desse documento.
> - Regista no relatório as **versões do enunciado e do template** que usaste (campo «Versões usadas» abaixo). O histórico de versões está no fim deste documento.
> - A estrutura final do relatório da Fase 2 será definida numa versão seguinte das diretrizes. Este template agrupa o conteúdo para o poderes copiar para o relatório sem retrabalho.
> - Substitui os textos entre chavetas `{...}`, apaga as linhas de ajuda (`>`) e os exemplos que não se aplicam.
> - **Distingue factos de hipóteses.** Um facto cita uma evidência (`EV-nn`); o que não tem evidência é uma hipótese (`H-nn`).
> - Convenções de IDs novos neste bloco: `QS-nn` (cenário de qualidade), `CAND-n` (candidato a RNF). Nunca reutilizes um ID eliminado.
> - O foco é a **extensão de vídeo**, **enquadrada no padrão global da solução**. Não analises o vídeo isoladamente.
> - Esta fase é de *refactoring*: os candidatos têm de poder ser melhorados sem acrescentar funcionalidades.
> - Se fizeres medições exploratórias, guarda os cenários, *scripts*, dados e ambiente para que sejam reprodutíveis e reutilizáveis como *baseline*.

---

**Equipa:** {PLx-Gy}  
**Elementos:** {nº e nome de cada elemento}  
**Commit de partida:** {hash curto; o mesmo do Bloco 1}  
**Data da análise:** {aaaa-mm-dd}  
**Versão deste documento:** {e.g., v1.0}  
**Versões usadas:** enunciado {e.g., 1.1} · template {e.g., 1.1}  
**Versão do Bloco 1 usada como entrada:** {e.g., v1.0}

---

## 4. Trade-offs, cenários de qualidade e prioridades

### 4.1 Justificação detalhada das avaliações da matriz

> Parte da matriz do Bloco 1 (secção 3.3) e justifica as avaliações atributo a atributo.

| **Atributo** | **Justificação** | **Depende sobretudo de** (padrão global / padrão do vídeo / ambos) | **Evidência** |
|--------------|------------------|---------------------------------------------------------------------|---------------|
| {Eficiência de desempenho} | {…} | {…} | {EV-nn} |
| {Fiabilidade} | {…} | {…} | {…} |
| {…} | {…} | {…} | {…} |

### 4.2 Cenários de qualidade para a extensão de vídeo

> Cada cenário tem os seis elementos. A **medida da resposta** deve ser definida por ti e ser verificável.

| **ID** | **Característica (ISO/IEC 25010)** | **Fonte do estímulo** | **Estímulo** | **Artefacto** | **Ambiente** | **Resposta** | **Medida da resposta** |
|--------|------------------------------------|-----------------------|--------------|---------------|--------------|--------------|------------------------|
| QS-01 | {…} | {…} | {…} | {…} | {…} | {…} | {…} |
| QS-02 | {…} | {…} | {…} | {…} | {…} | {…} | {…} |
| QS-03 | {…} | {…} | {…} | {…} | {…} | {…} | {…} |

**Priorização dos cenários**

| **ID** | **Importância para os stakeholders** | **Dificuldade / risco técnico** | **Prioridade** |
|--------|--------------------------------------|---------------------------------|----------------|
| QS-01 | {Alta / Média / Baixa — porquê} | {Alta / Média / Baixa — porquê} | {1..N} |
| QS-02 | {…} | {…} | {…} |
| QS-03 | {…} | {…} | {…} |

### 4.3 Atributos de qualidade por ordem de prioridade

> Com base nos cenários mais importantes.

1. {Atributo} — {cenários QS-nn; justificação}
2. {Atributo} — {…}
3. {Atributo} — {…}

### 4.4 Pré-requisitos e efeitos colaterais entre atributos

| **Atributo A** | **Atributo B** | **Efeito** (pré-requisito, sinergia ou conflito) | **Razão / evidência** |
|----------------|----------------|--------------------------------------------------|-----------------------|
| {…} | {…} | {…} | {…} |
| {…} | {…} | {…} | {…} |

### 4.5 Recomendações de melhoria à solução atual

| **Recomendação** | **Atributo(s)** | **Padrão a que se refere** (global / vídeo) | **Esforço** | **Risco de regressão** |
|------------------|-----------------|----------------------------------------------|-------------|------------------------|
| {…} | {…} | {…} | {Baixo / Médio / Alto} | {Baixo / Médio / Alto} |
| {…} | {…} | {…} | {…} | {…} |

---

## 5. Candidatos a requisitos não funcionais da Fase 2

> **Dois** requisitos não funcionais **distintos**, classificados segundo a ISO/IEC 25010 (característica e, quando aplicável, subcaracterística). Têm de partir de fragilidades concretas da solução de base, com evidência. Cada um é especificado, implementado e avaliado por si, ainda que possam estar relacionados.

| **#** | **Característica / subcaracterística (ISO/IEC 25010)** | **Fragilidade na base (evidência)** | **Origem** (padrão global / padrão do vídeo / interação) | **Impacto nos stakeholders (pertinência)** | **Exigência técnica (complexidade)** | **Escala e método de medição (esboço)** | **Pré-requisitos / efeitos colaterais** |
|-------|---------------------------------------------------------|--------------------------------------|-----------------------------------------------------------|---------------------------------------------|---------------------------------------|------------------------------------------|----------------------------------------|
| CAND-1 | {…} | {… (EV-nn)} | {…} | {…} | {…} | {…} | {…} |
| CAND-2 | {…} | {… (EV-nn)} | {…} | {…} | {…} | {…} | {…} |

### 5.1 Esboço de quantificação

> Esboça a **escala** e o **método de medição**. Os valores medidos na base, os valores-alvo e os valores mínimos aceitáveis **só são fixados após a medição inicial (*baseline*)**. Não os inventes agora.

| | **CAND-1** | **CAND-2** |
|---|---|---|
| **Escala** (o que se mede e em que unidade) | {…} | {…} |
| **Cenário de medição** | {…} | {…} |
| **Carga** | {…} | {…} |
| **Ambiente** | {…} | {…} |
| **Instrumento** | {…} | {…} |
| **Valor medido na base / valor-alvo / valor mínimo aceitável** | {A definir após a *baseline*} | {A definir após a *baseline*} |

### 5.2 Relação entre os dois candidatos

{Um é condição do outro? A melhoria de um pode degradar o outro? Que outros RNF podem ser afetados? 3 a 6 linhas.}

### 5.3 Evidência exploratória (se existir)

| **Descrição** | **Localização** (scripts, dados, resultados) | **Como repetir** |
|---------------|----------------------------------------------|------------------|
| {…} | {…} | {…} |

---

## 6. Conclusões e recomendações

**Adequação do padrão atual (global e do vídeo):**

{…}

**Sugestões de otimização:**

{…}

**Considerações para evolução futura:**

{…}

**Riscos para a preservação funcional e mitigação**

| **Risco** | **Funcionalidade afetada** (imagem / vídeo) | **Mitigação** | **Teste de regressão** (e.g., `Tools/video/tests`, `projects/tests`) |
|-----------|---------------------------------------------|---------------|-----------------------------------------------------------------------|
| {…} | {…} | {…} | {…} |
| {…} | {…} | {…} | {…} |

---

## 7. Utilização de IA

> Documenta as ferramentas, as *skills*, as tarefas apoiadas e a validação feita pela equipa. A equipa é responsável por todo o conteúdo entregue.

| **Ferramenta / skill** | **Tarefa apoiada** | **Validação feita pela equipa** | **Onde está documentado** |
|------------------------|--------------------|----------------------------------|---------------------------|
| {…} | {…} | {…} | {secção deste documento, relatório ou código} |
| {…} | {…} | {…} | {…} |

---

## ✅ Lista de verificação antes de entregar o Bloco 2

- [ ] O Bloco 1 está concluído e os seus IDs (`EV`, `H`, `ALT`) foram reutilizados, sem alterações (secção 4.1).
- [ ] Todas as avaliações da matriz do Bloco 1 estão justificadas, indicando se dependem do padrão global ou do padrão do vídeo (secção 4.1).
- [ ] Cada cenário de qualidade tem os seis elementos e uma medida da resposta verificável; os cenários estão priorizados (secção 4.2).
- [ ] Os atributos estão ordenados por prioridade, com pré-requisitos e efeitos colaterais identificados (secções 4.3 e 4.4).
- [ ] Há exatamente **dois** candidatos a RNF distintos, classificados pela ISO/IEC 25010, com origem, pertinência e complexidade (secção 5).
- [ ] A escala e o método de medição estão esboçados e **nenhum valor de *baseline*, alvo ou mínimo foi inventado** (secção 5.1).
- [ ] As medições exploratórias, se existirem, são reprodutíveis (secção 5.3).
- [ ] Os riscos para a preservação funcional têm mitigação e testes de regressão associados (secção 6).
- [ ] A utilização de IA está documentada e validada (secção 7).
- [ ] As **versões do enunciado e do template** usadas estão indicadas no cabeçalho.

---

## Histórico de versões do template

> Esta secção documenta o template. **Não a copies para o relatório.** Esquema `major.minor`, igual ao do enunciado: a versão *major* muda quando mudam a estrutura ou os campos obrigatórios; a *minor* muda em clarificações e correções.

| Versão | Data | Alterações | Enunciado compatível |
|--------|------|------------|----------------------|
| 1.1 | 2026-11-04 | Adicionado o controlo de versões (linha de versão, campo «Versões usadas», item na lista de verificação e este histórico). | 1.1 |
| 1.0 | 2026-11-04 | Primeira versão: template do Bloco 2 (secções 4 a 7 e lista de verificação), criado a partir do template combinado do Exercício 6. | 1.0 |

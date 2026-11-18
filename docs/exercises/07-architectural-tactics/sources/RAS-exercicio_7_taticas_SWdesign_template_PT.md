# 📝 Exercício 7 — Template de Táticas Arquiteturais para Melhorar RNF do PictuRAS
### Fase 2: Melhoria de Requisitos Não Funcionais do PictuRAS · Alimenta as secções de diagnóstico, quantificação e decisões arquiteturais do relatório da Fase 2

**Versão do template:** 3.0 · **Data:** 2026-11-17 · **Estado:** Em vigor · **Enunciado compatível:** 3.0

> **Como usar este template**
> - Segue o enunciado `RAS-exercicio_7_taticas_SWdesign_PT.md`. As secções 1 a 5 correspondem às tarefas 1 a 5; a secção 6 à tarefa 6.
> - Continua o registo de evidências e hipóteses do Bloco 1 do Exercício 6 (`EV-nn`, `H-nn`) e **usa os cenários do Bloco 2** (`QS-nn`, `CAND-n`) **sem os reescrever**. Convenções de IDs novos neste exercício: `TAT-nn` (tática candidata) e `DA-n` (decisão arquitetural). Nunca reutilizes um ID eliminado.
> - Regista no relatório as **versões do enunciado e do template** que usaste (campo «Versões usadas»).
> - Substitui os textos entre chavetas `{...}`, apaga as linhas de ajuda (`>`) e os exemplos que não se aplicam.
> - **Distingue factos de hipóteses.** Um facto cita uma evidência (`EV-nn`); o que não tem evidência é uma hipótese (`H-nn`).
> - Esta fase é de *refactoring*: rejeita as táticas que acrescentam funcionalidades (classe C).
> - **Não inventes valores** de *baseline*, alvo ou mínimo aceitável: fixam-se após a medição inicial.
> - Se fizeres medições exploratórias, guarda os cenários, *scripts*, dados e ambiente para os reutilizares como *baseline*.

---

**Equipa:** {PLx-Gy}  
**Elementos:** {nº e nome de cada elemento}  
**Commit de partida:** {hash curto; o mesmo do Bloco 1}  
**Data da análise:** {aaaa-mm-dd}  
**Versão deste documento:** {e.g., v1.0}  
**Versões usadas:** enunciado {e.g., 1.0} · template {e.g., 1.0}  
**Versões do Bloco 1 e do Bloco 2 usadas como entrada:** {e.g., v1.0 · v1.2}

---

## 1. Cenários de entrada (do Bloco 2)

> Copia do Bloco 2 os dois candidatos e os respetivos cenários. **Não os reescrevas:** o Bloco 2 é o único sítio onde os cenários se caracterizam. Se tiveres de corrigir uma medida da resposta, corrige-a lá e regista a alteração abaixo. Nas tabelas seguintes, `QS-01` e `QS-02` designam os cenários de `CAND-1` e `CAND-2`: substitui-os pelos IDs reais do Bloco 2.

### 1.1 Candidatos e cenários

| **Candidato** | **Cenário** (`QS-nn` do Bloco 2) | **Característica / subcaracterística (ISO/IEC 25010)** | **Evidência** | **Origem** (padrão global / padrão do vídeo / interação) | **Estímulo a que a tática reage** | **Resposta e medida (resumo)** | **Escala e método (Bloco 2, secção 5.1)** |
|---------------|----------------------------------|--------------------------------------------------------|---------------|----------------------------------------------------------|-----------------------------------|--------------------------------|--------------------------------------------|
| CAND-1 | {QS-nn} | {…} | {EV-nn} | {…} | {…} | {…} | {…} |
| CAND-2 | {QS-nn} | {…} | {EV-nn} | {…} | {…} | {…} | {…} |

### 1.2 Alterações feitas ao Bloco 2 (se existirem)

| **Cenário** | **O que mudou e porquê** | **Onde foi atualizado no Bloco 2** |
|-------------|--------------------------|-------------------------------------|
| {QS-nn} | {…} | {…} |

---

## 2. Táticas candidatas

> Pelo menos três por cenário. Classe **A** = refactoring puro; **B** = alteração visível que é o objeto da melhoria; **C** = funcionalidade nova (rejeitar).

| **ID** | **Cenário** | **Atributo → categoria** | **Tática** | **Como produz a resposta** (estímulo → tática → resposta) | **Já existe na base?** (evidência) | **Classe (A/B/C)** |
|--------|-------------|--------------------------|------------|-----------------------------------------------------------|------------------------------------|--------------------|
| TAT-01 | QS-01 | {e.g., Desempenho → gerir recursos} | {…} | {…} | {Sim/Parcial/Não — EV-nn} | {A} |
| TAT-02 | QS-01 | {…} | {…} | {…} | {…} | {…} |
| TAT-03 | QS-01 | {…} | {…} | {…} | {…} | {…} |
| TAT-04 | QS-02 | {…} | {…} | {…} | {…} | {…} |
| TAT-05 | QS-02 | {…} | {…} | {…} | {…} | {…} |
| TAT-06 | QS-02 | {…} | {…} | {…} | {…} | {…} |

---

## 3. Decisões arquiteturais

### DA-1 — {título} (cenário QS-01)

| **Campo** | **Conteúdo** |
|-----------|--------------|
| **Contexto** | {fragilidade, cenário, restrições (*refactoring*, preservar comportamento)} |
| **Tática(s) escolhida(s)** | {TAT-nn} |
| **Estrutura / padrão que a realiza** | {e.g., réplicas do *worker*; *Circuit Breaker*; … ou «n/a»} |
| **Alternativas consideradas e razão de rejeição** | {TAT-nn: …} · {TAT-nn: …} |
| **Consequências positivas** | {…} |
| **Consequências negativas / riscos** | {…} |
| **Elementos arquiteturais afetados** | {serviços, filas, ficheiros de configuração, módulos} |
| **Origem e âmbito do *refactoring*** | {padrão global / padrão do vídeo / interação; risco de regressão} |
| **Classe (A/B/C)** | {A ou B; justificação} |

### DA-2 — {título} (cenário QS-02)

{mesma tabela}

---

## 4. Vista arquitetural (antes / depois)

> Diagrama de componentes, implantação ou sequência. Destaca os elementos ou as interações introduzidos ou alterados pelas táticas (estereótipo `«tática: …»` ou cor) e inclui uma legenda.

**Antes**

![Vista antes da decisão]({caminho/para/imagem-ou-ficheiro-do-diagrama})

**Depois**

![Vista depois da decisão]({caminho/para/imagem-ou-ficheiro-do-diagrama})

**Legenda e notas:** {…}

---

## 5. Trade-offs e plano de medição

### 5.1 Matriz de efeitos

> Melhora (↑), degrada (↓) ou neutro (=). Mínimo de quatro atributos, incluindo a característica do outro cenário.

| **Decisão** | **Desempenho** | **Disponibilidade / Fiabilidade** | **Segurança** | **Usabilidade** | **Manutenibilidade / Testabilidade** | **Justificação** |
|-------------|----------------|-----------------------------------|---------------|-----------------|--------------------------------------|------------------|
| DA-1 | {↑ / ↓ / =} | {…} | {…} | {…} | {…} | {…} |
| DA-2 | {…} | {…} | {…} | {…} | {…} | {…} |

### 5.2 Interação entre DA-1 e DA-2

| **Decisão A** | **Decisão B** | **Efeito** (pré-requisito, sinergia ou conflito) | **Razão / evidência** |
|---------------|---------------|--------------------------------------------------|-----------------------|
| DA-1 | DA-2 | {…} | {…} |

### 5.3 Plano de medição (esboço)

> A mesma medição é feita antes e depois do *refactoring*, no mesmo ambiente.

| **Cenário** | **Cenário de teste e carga** | **Ambiente** (máquina, recursos, versões) | **O que se regista** | **Repetições e agregação** | **Onde ficam os *scripts* e os dados** |
|-------------|------------------------------|-------------------------------------------|----------------------|----------------------------|-----------------------------------------|
| QS-01 | {…} | {…} | {…} | {…} | {caminho no repositório} |
| QS-02 | {…} | {…} | {…} | {…} | {…} |

### 5.4 Preservação funcional

| **Zona alterada** | **Testes de regressão existentes** (`Tools/video/tests`, `projects/tests`, …) | **Lacunas de teste** | **Testes a acrescentar** |
|-------------------|--------------------------------------------------------------------------------|----------------------|--------------------------|
| {DA-1: …} | {…} | {…} | {…} |
| {DA-2: …} | {…} | {…} | {…} |

---

## 6. Utilização de IA

| **Ferramenta / modelo** | **Tarefa apoiada** | **O que foi aceite** | **O que foi rejeitado e porquê** | **Como foi validado pela equipa** |
|-------------------------|--------------------|----------------------|----------------------------------|-----------------------------------|
| {…} | {…} | {…} | {…} | {código, medição ou documentação} |

---

## Lista de verificação antes de entregar

- [ ] Os dois cenários vêm do Bloco 2 (`QS-nn`, `CAND-n`) e não foram reescritos; eventuais correções estão registadas e feitas no Bloco 2 (secção 1). **Sem valores de *baseline*, alvo ou mínimo inventados.**
- [ ] Pelo menos três táticas candidatas por cenário, todas classificadas A/B/C (secção 2).
- [ ] Duas decisões com alternativas, consequências e elementos afetados (secção 3).
- [ ] Vista antes/depois com legenda (secção 4).
- [ ] Matriz de efeitos, interação entre as decisões, plano de medição e plano de regressão (secção 5).
- [ ] IA documentada (secção 6).
- [ ] Factos com `EV-nn`; hipóteses marcadas como `H-nn`.

---

## Controlo de versões

| Versão | Data | Alterações | Enunciado compatível |
|--------|------|------------|----------------------|
| 3.0 | 2026-11-17 | Removida a secção de revisão cruzada; a utilização de IA passa a secção 6. Acompanha o enunciado 3.0. | 3.0 |
| 2.0 | 2026-11-05 | Secção 1 passa a «Cenários de entrada», vindos do Bloco 2 (v1.2); removidas a escrita de cenários e a secção de fragilidades (`FR-n`). Acompanha o enunciado 2.0. | 2.0 |
| 1.0 | 2026-11-05 | Primeira versão do template do Exercício 7 (táticas arquiteturais). | 1.0 |

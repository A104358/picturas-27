# 📝 Exercício 6 (Bloco 1) — Template de Identificação e Comparação de Padrões Arquiteturais
### Fase 2: Melhoria de Requisitos Não Funcionais do PictuRAS · Alimenta as secções de diagnóstico e de decisões arquiteturais do relatório da Fase 2

**Versão do template:** 1.1 · **Data:** 2026-11-04 · **Estado:** Em vigor · **Enunciado compatível:** 1.1

> **Como usar este template**
> - Segue o enunciado `RAS-exercicio_6_bloco1_SWdesign_PT.md`. As secções 1 a 3 deste template correspondem, por ordem, aos pontos 1 a 3 do **Resultado Esperado**; a secção 0 corresponde à tarefa de **Preparação**.
> - Este é o **Bloco 1**. O **Bloco 2** (`RAS-exercicio_6_bloco2_SWdesign_template_PT.md`) continua este documento: usa a matriz (secção 3.3), as alternativas (`ALT-n`) e o registo de evidências e hipóteses (secção 2.6). **Mantém os IDs.**
> - Existe uma **versão em inglês** deste template (`RAS-exercicio_6_bloco1_SWdesign_template_EN.md`), com as mesmas secções e os mesmos IDs.
> - Regista no relatório as **versões do enunciado e do template** que usaste (campo «Versões usadas» abaixo). O histórico de versões está no fim deste documento.
> - A estrutura final do relatório da Fase 2 será definida numa versão seguinte das diretrizes. Este template agrupa o conteúdo para o poderes copiar para o relatório sem retrabalho.
> - Substitui os textos entre chavetas `{...}`, apaga as linhas de ajuda (`>`) e os exemplos que não se aplicam.
> - **Distingue factos de hipóteses.** Um facto cita uma evidência (`EV-nn`); o que não tem evidência é uma hipótese (`H-nn`). Regista ambos na secção 2.6.
> - Convenções de IDs: `EV-nn` (evidência), `H-nn` (hipótese), `ALT-n` (alternativa). Nunca reutilizes um ID eliminado.
> - O foco é a **extensão de vídeo**, **enquadrada no padrão global da solução**. Não analises o vídeo isoladamente.
> - Esta fase é de *refactoring*: as alternativas têm de preservar o comportamento funcional.
> - Se fizeres medições exploratórias, guarda os cenários, *scripts*, dados e ambiente para que sejam reprodutíveis e reutilizáveis como *baseline*.

---

**Equipa:** {PLx-Gy}  
**Elementos:** {nº e nome de cada elemento}  
**Commit de partida:** {hash curto; `git rev-parse HEAD` em `picturas-um/picturas-27`}  
**Data da análise:** {aaaa-mm-dd}  
**Versão deste documento:** {e.g., v1.0}  
**Versões usadas:** enunciado {e.g., 1.1} · template {e.g., 1.1}

---

## 0. Preparação e ambiente

> Regista como a solução foi lançada, para que outra pessoa consiga repetir. Se algum passo falhou, indica-o.

| **Item** | **Valor** |
|----------|-----------|
| Commit de partida | {hash} |
| Comando(s) de arranque | {e.g., `docker compose up -d --build`} |
| Ambiente (SO, CPU, RAM, versões de Docker e Compose) | {…} |
| Projeto de teste (nº de imagens e de vídeos, amostras usadas) | {…} |
| Problemas encontrados ao lançar | {…} |

**Como é orquestrado o processamento em lote de imagens e de vídeos** *(5 a 8 linhas)*:

{Descreve, com as tuas palavras, o que acontece desde o *Apply* até ao resultado, para um projeto com imagens e vídeos, e como o sistema distingue os dois tipos de *media*.}

---

## 1. Âmbito e vista da arquitetura

### 1.1 Fontes consultadas

| **Fonte** | **Versão / data** | **Usada para** |
|-----------|-------------------|----------------|
| `README.md` | {commit} | {…} |
| `AGENTS.md` | {commit} | {…} |
| `doc-ext-requisitos-2627.pdf` | {…} | {…} |
| `doc-sol-arquitetural.pdf` | {…} | {…} |
| Diretrizes da Fase 2 | {versão} | {…} |
| Slides da aula 11 (*Arch. Styles*) | {…} | {…} |
| `RAS_support_doc_architectural_patterns_PT.md` | {…} | {…} |
| {outra fonte} | {…} | {…} |

### 1.2 Vista da arquitetura global

> A vista mostra o **padrão global** da solução, com o **caminho do vídeo destacado**. Usa a notação e a ferramenta que preferires (e.g., C4 de contentores, componentes UML, PlantUML, Mermaid, draw.io) e indica uma legenda.

![Vista da arquitetura global com o caminho do vídeo destacado]({caminho/para/imagem-ou-ficheiro-do-diagrama})

**Ferramenta / notação:** {…}

| **Elemento (cor, forma ou estilo)** | **Significado** |
|-------------------------------------|-----------------|
| {…} | {e.g., caminho do vídeo} |
| {…} | {…} |

### 1.3 Diagrama de sequência de um pedido completo

> Carregamento → definição do pipeline → *Apply* → progresso → resultado, para um projeto com vídeos.

![Diagrama de sequência do processamento em lote de um projeto com vídeos]({caminho/para/imagem-ou-ficheiro-do-diagrama})

| **Passo** | **Origem → Destino** | **Mensagem / endpoint / fila** | **Evidência** |
|-----------|----------------------|--------------------------------|---------------|
| Carregamento do vídeo | {…} | {…} | {EV-nn} |
| Definição do pipeline | {…} | {…} | {EV-nn} |
| *Apply* | {…} | {…} | {EV-nn} |
| Progresso | {…} | {…} | {EV-nn} |
| Resultado | {…} | {…} | {EV-nn} |

### 1.4 Onde e porquê o sistema bifurca entre imagem e vídeo

| **Ponto de bifurcação** | **Caminho de imagens** | **Caminho de vídeo** | **Evidência** | **Porquê** (facto ou hipótese) |
|-------------------------|------------------------|----------------------|---------------|--------------------------------|
| {…} | {…} | {…} | {EV-nn} | {…} |
| {…} | {…} | {…} | {EV-nn} | {…} |

---

## 2. Identificação e análise dos padrões atuais

### 2.1 Padrão global da solução

> Identifica o estilo, ou a combinação de estilos, que organiza o PictuRAS como um todo. Este padrão é o **ponto de partida** da análise: define o contexto e as restrições a que qualquer alternativa terá de responder.

| | |
|---|---|
| **Nome(s) do padrão / estilo** | {…} |
| **Descrição** | {2 a 4 linhas} |

**Decisões globais que condicionam o vídeo**

| **Decisão global** | **Evidência** | **Efeito no vídeo** |
|--------------------|---------------|---------------------|
| {…} | {EV-nn} | {…} |
| {…} | {EV-nn} | {…} |

**Benefícios e desafios do padrão global**

| **Tipo** | **Descrição** | **Característica / subcaracterística (ISO/IEC 25010)** | **Facto / hipótese** |
|----------|---------------|--------------------------------------------------------|----------------------|
| Benefício | {…} | {…} | {EV-nn / H-nn} |
| Desafio | {…} | {…} | {EV-nn / H-nn} |

### 2.2 Padrão do processamento de vídeo

| | |
|---|---|
| **Nome do padrão** | {…} |
| **Descrição** | {2 a 4 linhas} |
| **Contraste com o caminho de imagens** | {…} |

**Benefícios e desafios do padrão do vídeo**

| **Tipo** | **Descrição** | **Característica / subcaracterística (ISO/IEC 25010)** | **Facto / hipótese** |
|----------|---------------|--------------------------------------------------------|----------------------|
| Benefício | {…} | {…} | {EV-nn / H-nn} |
| Desafio | {…} | {…} | {EV-nn / H-nn} |

### 2.3 Relação entre o padrão global e o padrão do vídeo

> Em que pontos o vídeo **segue** o padrão global, em que pontos se **afasta** dele e com que consequências.

| **Aspeto** | **O que o padrão global prescreve** | **O que o vídeo faz** | **Segue / afasta-se** | **Consequência** | **Evidência** |
|------------|-------------------------------------|-----------------------|-----------------------|------------------|---------------|
| {…} | {…} | {…} | {Segue / Afasta-se} | {…} | {EV-nn} |
| {…} | {…} | {…} | {…} | {…} | {EV-nn} |

**O que o vídeo herda do padrão global / que restrições este lhe impõe / que fragilidades resultam do desvio** *(3 a 6 linhas)*:

{…}

### 2.4 Legendagem automática e extração de fotogramas

| **Funcionalidade** | **Como se integra no padrão do vídeo** | **Impacto nos atributos de qualidade** | **Evidência** |
|--------------------|----------------------------------------|-----------------------------------------|---------------|
| Legendagem automática | {…} | {…} | {EV-nn} |
| Extração de fotogramas | {…} | {…} | {EV-nn} |

### 2.5 Suporte aos requisitos não funcionais existentes e regras sem requisito explícito

> Usa os documentos de requisitos anteriores e a extensão do PL1-G4. Inclui as regras que não têm requisito explícito (e.g., ordem obrigatória de passos do pipeline).

| **Requisito / regra** (ID, ou «sem requisito explícito») | **Padrão global suporta?** | **Padrão do vídeo suporta?** | **Porquê** | **Evidência** |
|----------------------------------------------------------|----------------------------|------------------------------|------------|---------------|
| {RNF… / regra} | {Sim / Parcial / Não} | {Sim / Parcial / Não} | {…} | {EV-nn} |
| {…} | {…} | {…} | {…} | {…} |

### 2.6 Registo de evidências e hipóteses

> Este registo é **partilhado com o Bloco 2**: novas evidências e hipóteses acrescentam-se aqui, continuando a numeração.

| **ID** | **Tipo** | **Localização** (ficheiro e linhas, commit, comando) | **O que mostra** |
|--------|----------|------------------------------------------------------|------------------|
| EV-01 | {Código / Configuração / Mensagem / Medição / Documento} | {…} | {…} |
| EV-02 | {…} | {…} | {…} |

| **ID** | **Hipótese** | **Como confirmar ou refutar** | **Estado** |
|--------|--------------|-------------------------------|------------|
| H-01 | {…} | {…} | {Por confirmar / Confirmada / Refutada} |
| H-02 | {…} | {…} | {…} |

---

## 3. Alternativas e matriz de comparação

### 3.1 Alternativas consideradas

> 2 a 3 alternativas relevantes **para o processamento de vídeo**. O padrão global é o **contexto da comparação**: indica se cada alternativa o **mantém** ou o **altera**. Consulta os slides da aula 11 e o documento de apoio. Se for relevante, inclui uma alternativa ao próprio padrão global como termo de comparação.

| **ID** | **Nome / padrão** | **Descrição breve** | **Mantém ou altera o padrão global?** | **Fonte** |
|--------|-------------------|---------------------|---------------------------------------|-----------|
| ALT-1 | {…} | {…} | {Mantém / Altera / Afasta-se parcialmente} | {…} |
| ALT-2 | {…} | {…} | {…} | {…} |
| ALT-3 *(opcional)* | {…} | {…} | {…} | {…} |

### 3.2 Análise de cada alternativa

> Copia o bloco para cada alternativa.

**ALT-1 — {nome}**

| | |
|---|---|
| **Coerência com o padrão global** | {…} |
| **Efeito nos atributos de qualidade** | {…} |
| **Vantagens potenciais** | {…} |
| **Desvantagens ou riscos** | {…} |
| **Custo e risco de migração** (a funcionalidade existente tem de ser preservada) | {…} |

**ALT-2 — {nome}**

| | |
|---|---|
| **Coerência com o padrão global** | {…} |
| **Efeito nos atributos de qualidade** | {…} |
| **Vantagens potenciais** | {…} |
| **Desvantagens ou riscos** | {…} |
| **Custo e risco de migração** | {…} |

### 3.3 Matriz de comparação de padrões

> Escala à tua escolha (e.g., Alto / Médio / Baixo). **Justifica cada célula** com evidência da solução (`EV-nn` ou `H-nn`); as avaliações sem fundamento não são valorizadas. A justificação detalhada e a análise de trade-offs fazem-se no Bloco 2 (secção 4.1).

| **Atributo de qualidade (ISO/IEC 25010)** | **Padrão global atual (referência)** | **Padrão atual do vídeo** | **ALT-1** | **ALT-2** |
|-------------------------------------------|--------------------------------------|---------------------------|-----------|-----------|
| Relação com o padrão global | — | {Segue / Afasta-se} | {Mantém / Altera} | {Mantém / Altera} |
| Eficiência de desempenho — comportamento temporal | {nível — justificação (EV-nn)} | {…} | {…} | {…} |
| Eficiência de desempenho — capacidade / elasticidade | {…} | {…} | {…} | {…} |
| Fiabilidade — tolerância a falhas / recuperabilidade | {…} | {…} | {…} | {…} |
| Manutenibilidade — modularidade / modificabilidade | {…} | {…} | {…} | {…} |
| Segurança | {…} | {…} | {…} | {…} |
| Usabilidade — operabilidade | {…} | {…} | {…} | {…} |

### 3.4 Adequação do padrão atual

{Justifica por que o padrão atual (global e do vídeo) é mais ou menos adequado do que as alternativas, considerando os requisitos não funcionais identificados. 5 a 10 linhas.}

---

## ✅ Lista de verificação antes de entregar o Bloco 1

- [ ] O *commit* de partida está identificado e o ambiente de lançamento está descrito (secção 0).
- [ ] A vista da arquitetura mostra o **padrão global** com o caminho do vídeo destacado, e há um diagrama de sequência do processamento em lote (secção 1).
- [ ] O **padrão global** e o **padrão do vídeo** estão identificados, com evidências, benefícios e desafios (secções 2.1 e 2.2).
- [ ] A relação entre os dois padrões está analisada: o que segue, o que se afasta e com que consequências (secção 2.3).
- [ ] Cada afirmação cita uma evidência (`EV-nn`) ou está marcada como hipótese (`H-nn`); factos e hipóteses estão separados (secção 2.6).
- [ ] Há 2 a 3 alternativas e cada uma indica se **mantém ou altera** o padrão global, com custo e risco de migração (secção 3).
- [ ] A matriz inclui o padrão global como referência e **todas as células estão justificadas** (secção 3.3).
- [ ] Os IDs (`EV`, `H`, `ALT`) estão estáveis, porque o Bloco 2 os reutiliza.
- [ ] As **versões do enunciado e do template** usadas estão indicadas no cabeçalho.

---

## Histórico de versões do template

> Esta secção documenta o template. **Não a copies para o relatório.** Esquema `major.minor`, igual ao do enunciado: a versão *major* muda quando mudam a estrutura ou os campos obrigatórios; a *minor* muda em clarificações e correções.

| Versão | Data | Alterações | Enunciado compatível |
|--------|------|------------|----------------------|
| 1.1 | 2026-11-04 | Adicionado o controlo de versões (linha de versão, campo «Versões usadas», item na lista de verificação e este histórico). Versão em inglês disponível: `RAS-exercicio_6_bloco1_SWdesign_template_EN.md`. | 1.1 |
| 1.0 | 2026-11-04 | Primeira versão: template do Bloco 1 (secções 0 a 3 e lista de verificação), criado a partir do template combinado do Exercício 6. | 1.0 |

// =============================================================================
//  PictuRAS · RAS 2026/2027 · Relatório da Fase 2 — Melhoria de Requisitos Não Funcionais
//  Compilar:  typst compile --font-path fonts main.typ
//  Pré-visualizar ao gravar:  typst watch --font-path fonts main.typ
// =============================================================================
#import "cover.typ": cover
#import "template.typ": *

#show: project

// Antes de entregar: `false` esconde todas as caixas de orientação.
#mostrar-orientacoes.update(false)

#cover(
  title: "Fase 2 — Melhoria de Requisitos Não Funcionais",
  subtitle: "Diagnóstico, decisões arquiteturais e avaliação",
  group: "Grupo PL2-G4",
  authors: (
    (name: "Luís Miguel Coelho", number: "PG64000"),
    (name: "Alexandre de Oliveira Monsanto", number: "PG65397"),
    (name: "Diogo Alexandre Gomes Silva", number: "PG63941"),
    (name: "José Miguel da Silva Santos", number: "PG63522"),
  ),
  "Novembro, 2026",
)

// --- Elementos iniciais (numeração romana) -----------------------------------
#set page(numbering: "i", number-align: center)
#counter(page).update(1)

#include "capitulos/00-historico-versoes.typ"
#pagebreak()

#outline(title: [Índice], indent: auto, depth: 3)
#pagebreak()
#block(breakable: true)[
  #set text(size: 9pt)
  #outline(title: [Lista de Figuras], target: figure.where(kind: image))
  #outline(title: [Lista de Tabelas], target: figure.where(kind: table))
]

// --- Corpo do relatório -------------------------------------------------------
#set page(numbering: "1", number-align: center)
#counter(page).update(1)

// Parte I — Enquadramento
#pagebreak(weak: true)
#include "capitulos/01-introducao.typ"

// Parte II — Diagnóstico arquitetural (Exercício 6, Bloco 1)
#pagebreak(weak: true)
#include "capitulos/02-ambito-arquitetura.typ"
#pagebreak(weak: true)
#include "capitulos/03-padroes-atuais.typ"
#pagebreak(weak: true)
#include "capitulos/04-alternativas-matriz.typ"

// Parte III — Qualidade e candidatos a RNF (Exercício 6, Bloco 2)
#pagebreak(weak: true)
#include "capitulos/05-tradeoffs-cenarios.typ"
#pagebreak(weak: true)
#include "capitulos/06-candidatos-rnf.typ"

// Parte IV — Táticas, decisões arquiteturais, medição e resultados (Exercício 7 e implementação)
#pagebreak(weak: true)
#include "capitulos/07-cenarios-taticas.typ"
#pagebreak(weak: true)
#include "capitulos/08-decisoes-arquiteturais.typ"
#pagebreak(weak: true)
#include "capitulos/09-vista-antes-depois.typ"
#pagebreak(weak: true)
#include "capitulos/10-tradeoffs-medicao.typ"

// Parte V — Síntese
#pagebreak(weak: true)
#include "capitulos/11-conclusoes.typ"
#pagebreak(weak: true)
#include "capitulos/12-agentes-ia.typ"

// Anexos
#pagebreak(weak: true)
#include "capitulos/99-anexos.typ"

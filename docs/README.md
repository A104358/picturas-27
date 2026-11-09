# PictuRAS documentation

Academic requirements, architectural references, course material and exercise
deliverables. For application setup and usage, see the [project README](../README.md).

Start with the [Exercise 6 resolution](exercises/06-architectural-patterns/resolution.md)
or its [artifact index](exercises/06-architectural-patterns/README.md).

## Reference documents

| Topic | Document | Period / purpose |
|-------|----------|------------------|
| Requirements | [Base requirements](requirements/doc-ext-requisitos.pdf) | 2025/2026, Phase 1: images, presets, AI assistance and sharing. |
| Requirements | [Video extension requirements](requirements/doc-ext-requisitos-2627.pdf) | 2026/2027, Phase 1, PL1-G4: video MVP and quality requirements. |
| Architecture | [Base architectural solution](architecture/doc-sol-arquitetural.pdf) | 2025/2026, Phase 2: the architecture inherited by the video extension. |
| Guidelines | [Phase 2 guidelines, version 1](guidelines/fase-2-guidelines-1.pdf) | 2026/2027: improve two non-functional requirements through refactoring. |
| Lectures | [Lecture 11 — Architectural Styles](lectures/RAS-slidesEN-11-ARCH-Styles.pdf) | Course slides, October 2021: architectural styles and their constraints. |

## Exercises

| Exercise | Deliverable | Supporting artifacts |
|----------|-------------|----------------------|
| 6 — Architectural patterns, Block 1 | [Resolution — PL2-G4](exercises/06-architectural-patterns/resolution.md) | [Assignment, support material, diagrams and evidence](exercises/06-architectural-patterns/README.md) |

## Folder layout

```text
docs/
├── README.md
├── requirements/                    # Base and video requirements
├── architecture/                    # Architectural reference reports
├── guidelines/                      # Project phase instructions
├── lectures/                        # Course slides
└── exercises/
    └── 06-architectural-patterns/
        ├── README.md                # Exercise artifact index
        ├── resolution.md            # Completed Block 1 report
        ├── sources/                 # Original assignment and support HTML
        ├── diagrams/                # PlantUML sources and SVG renderings
        └── evidence/                # Reproduction script and execution record
```

Keep shared reference material in its topic folder and exercise-specific work
inside the corresponding exercise directory. Retain original reference filenames
and update relative links when moving artifacts.

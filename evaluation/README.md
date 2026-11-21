# `med.py` — medição da Fase 2

Implementação do [plano de medição](../docs/planoMedicao.md) das
[métricas selecionadas](../docs/metricas.md). Recolhe a baseline formal (BF) e a medição
final (MF) com o mesmo método, numa stack Docker isolada (`picturas-nfr`).

## Instalação (uma vez)

```bash
cd evaluation
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.med.example .env.med        # na BF pode ficar como está
```

Requisitos: Docker Desktop com ≥8 CPU e ≥8 GiB, `ffmpeg`/`ffprobe` no PATH e ≥60 GiB livres.

## Campanha completa

```bash
.venv/bin/python med.py preflight --campaign BF   # tudo OK antes de começar
.venv/bin/python med.py corpus                    # ~2,5 GiB em .corpus/ (guardar até à MF)
.venv/bin/python med.py stack up                  # build + up do projeto picturas-nfr (15-30 min na 1.ª vez)
.venv/bin/python med.py run --campaign BF --quick --metrics S01,U01   # ensaio de aceitação (§11)
.venv/bin/python med.py run --campaign BF         # campanha completa (~2-3 h)
.venv/bin/python med.py stack down                # apaga contentores e volumes do projeto isolado
```

Os resultados ficam em `results/<CAMPANHA>-<UTC>/`:

| Ficheiro | Conteúdo |
|----------|----------|
| `manifest.json` | commit, hashes, host, Docker, imagens, corpus, configuração do nginx |
| `raw/<métrica>.jsonl` | uma linha por tentativa (sem segredos) |
| `summary.json` | valor por métrica e estado face a `criteria.yaml` |
| `report.md` | tabelas por RNF |
| `matrix_check.json` | casos congelados em falta ou a mais |

Depois da refatoração, no **mesmo computador**:

```bash
.venv/bin/python med.py run --campaign MF
.venv/bin/python med.py compare results/BF-... results/MF-...
```

Medições de outros elementos da equipa usam `--campaign EXP` e nunca entram no `compare`.

O `compare` só classifica se a MF tiver o mesmo host, limites, corpus, critérios, casos
e **versão do instrumento** que a BF; caso contrário todas as métricas ficam
`COMPARACAO_INVALIDA`. **Não alterar `med.py`, `medlib/`, `criteria.yaml` nem
`cases/` entre a BF e a MF.** Se uma alteração for inevitável e não invalidar os dados da
BF, registá-la com:

```bash
.venv/bin/python med.py freeze results/BF-... --motivo "o que mudou e porquê"
```

## Opções úteis

- `--suite security|upload` corre só um RNF; `--metrics S12,U20` corre métricas soltas.
- `--resume results/<dir>` acrescenta métricas a uma campanha já iniciada.
- `report results/<dir> --resummarise` refaz os resumos dos estratos a partir de `raw/`, sem medir.
- `--quick`: 1 repetição e só 10 MiB, para verificar o instrumento (não é BF nem MF).

## Limpeza

```bash
.venv/bin/python med.py stack purge            # stack, volumes e imagens construídas por picturas-nfr
.venv/bin/python med.py stack purge --corpus   # também o corpus (só depois de existir uma MF)
```

**Nunca** usar `docker system prune` e afins: apagam também outras instalações Docker desta máquina.
O `med.py` só aceita projetos `picturas-nfr[-<sufixo>]` e só apaga volumes de projetos que ele próprio criou.

## Na MF

Preencher `.env.med` com as credenciais de administração (para fixtures e verificação)
e as credenciais legítimas por serviço (`MED_SVC_CRED_*`), usadas só nos casos
"credencial de outro serviço" e nos controlos. Sem elas, esses casos ficam
`INCONCLUSIVO` em vez de passarem por omissão.

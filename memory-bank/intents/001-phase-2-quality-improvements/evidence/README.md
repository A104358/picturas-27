# Exploration Evidence

These artifacts support the six-direction investigation. They are preliminary
observations, not approved requirement baselines or team decisions. Source context
and detailed protocols are in the [investigation plan](../investigation-plan.md).
The November 16 supplied experiments and their methodological review are indexed
in [nfr-2026-11-16/README.md](nfr-2026-11-16/README.md). Current metric definitions,
proposed minimums/targets and explicit missing values are in the
[measurement specification](../../../../docs/fase2-metricas-e-baseline.md).
Read the [live findings and decision brief](../live-findings.md) for the subsequent
application-level experiments and their explicit limits.

## Artifacts

| File | What it records |
|------|-----------------|
| [Source/environment inventory](source-inventory-2026-11-14.json) | Commit, application diff from the prior diagnosis, source hashes and point-in-time host resources. |
| [Acknowledgement-order probe](ack-order.cjs) | Loads the real helper in a VM with a fake AMQP transport and a controlled asynchronous callback. |
| [Acknowledgement-order result](ack-order-2026-11-14.json) | Callback starts, message is acknowledged, then callback completes. No live broker or crash is involved. |
| [Processor probe](video-local-probe.py) | Calls the existing video processor; records timings, progress, output metadata/hashes and unchanged input. |
| [Host processor results](video-local-2026-11-14.json) | Twelve valid local processor calls and one corrupt-input probe using host dependencies. |
| [Isolated-container results](video-container-2026-11-14.json) | Same scenarios with Pillow 11.0.0, fixed image, 2 CPU and 1 GiB. |
| [Verification record](verification-2026-11-14.md) | Host test result, environment checks, numerical summary and limitations. |

## Live Application Evidence

Use the isolated-generator run for the reported metrics. Earlier trial files are
retained for audit and must not be pooled as before/after refactoring results.

| Artifact | Purpose |
|----------|---------|
| [Stack preparation](prepare-live-stack.py) / [sanitized manifest](live-stack-2026-11-14.json) | Derives the 13-service slice from Compose, locks image IDs and records containment/resources. Actual inherited secrets stay in owner-only files under `/tmp`. |
| [Runtime source hashes](live-source-hashes-2026-11-14.json) | All 182 checked source files matched the checkout across seven services. |
| [API/load probe](live-api-probe.cjs) / [authoritative run](live-api-isolated-2026-11-14.json) | Separate client container; 10/50 MiB uploads, eight access cases, three batches, Socket.IO polling and sampled output checks. |
| [Resource sampler](sample-live-resources.py) / [authoritative series](live-resources-isolated-2026-11-14.jsonl.gz) | Compressed raw cgroup CPU/memory and Node RSS samples; corrected `node-MainThread` identification. |
| [Analysis script](analyze-live-results.py) / [derived metrics](live-analysis-2026-11-14.json) | Reproducible resource windows, queueing residuals, progress intervals and batch throughput. |
| [Supplemental access probe](live-access-supplement.cjs) / [result](live-access-supplement-2026-11-14.json) | Forged caller-header read and tokenless retrieval verified against original bytes; internal-network threat model. |
| [Recovery controller](run-recovery-probe.py) / [workload](live-recovery-probe.cjs) / [result](live-recovery-2026-11-14.json) | One early worker kill/restart; queue observation, persisted counts, quota, source integrity and sampled MP4. |
| [Node tests excerpt](live-orchestrator-tests-2026-11-14.txt) | Eight existing orchestrator tests passed in the source-verified container. |
| [Lifecycle record](live-lifecycle-2026-11-14.json) | Experiment containers stopped after measurement; volumes retained. |
| [Initial co-located run](live-api-2026-11-14.json) / [initial resource series](live-resources-2026-11-14.jsonl.gz) | Diagnostic only: client ran in `projects`, RSS predicate missed `node-MainThread`, and the initial storage-read key was invalid. |
| [Intermediate separate-client upload run](live-upload-2026-11-14.json) | Diagnostic acquisition check before the final corrected resource collection. |

## Live Experiment Reproduction

The stack/sampler require Docker access, Python with PyYAML, and a Linux cgroup v2
host. The API probe runs with npm dependencies already present in the projects
image. Keep new output paths separate from the archived evidence. The preparation
command creates a private Compose file and broker environment file under `/tmp`;
never copy these secret-bearing files into the repository.

```bash
python3 memory-bank/intents/001-phase-2-quality-improvements/evidence/prepare-live-stack.py --directory /tmp/picturas-quality-20261114 --manifest /tmp/picturas-quality-new-manifest.json
docker compose -f /tmp/picturas-quality-20261114/compose.json up -d --no-build --pull never
```

Start resource collection in one terminal, then the load generator in another:

```bash
python3 memory-bank/intents/001-phase-2-quality-improvements/evidence/sample-live-resources.py --output /tmp/picturas-quality-new-resources.jsonl.gz --stop-file /tmp/picturas-quality-new-stop --duration 300
```

```bash
docker run --rm -i --network picturas-quality-20261114_elk --cpus 1 --memory 512m --env-file /tmp/picturas-quality-20261114/probe.env --env SOURCE_COMMIT=24484b7 --env LOAD_GENERATOR=separate-container --entrypoint node sha256:5c21e207f6ad56fa1764b5d7b62bee8cd7ba94f8ef7565ab4fe4464e3bf3a950 - < memory-bank/intents/001-phase-2-quality-improvements/evidence/live-api-probe.cjs > /tmp/picturas-quality-new-api.json
```

After the client exits, create the collector's stop file and derive the metrics:

```bash
touch /tmp/picturas-quality-new-stop
python3 memory-bank/intents/001-phase-2-quality-improvements/evidence/analyze-live-results.py --api /tmp/picturas-quality-new-api.json --resources /tmp/picturas-quality-new-resources.jsonl.gz --output /tmp/picturas-quality-new-analysis.json
```

The recovery scenario intentionally kills/restarts only the explicitly identified
experiment worker, after checking its project label. Run it separately from normal
batch measurements, with the same isolated deployment. It is not a test to run
against production or the user's regular Compose project.

```bash
python3 memory-bank/intents/001-phase-2-quality-improvements/evidence/run-recovery-probe.py --output /tmp/picturas-quality-new-recovery.json
docker exec picturas-quality-20261114-projects-1 node --test tests/video-pipeline.test.js tests/frame-extraction.test.js tests/process-batch.test.js
docker compose -f /tmp/picturas-quality-20261114/compose.json stop
```

The builder and controller use a dedicated, fixed experiment name. Before reuse,
inspect existing experiment containers/volumes: a rerun retains previous test data
and warmed allocator/cache state. No command above deletes application volumes.
Update the source revision label for a new checkout and verify runtime hashes.
Port numbers match the base configuration; the internal network prevented host
access in this environment, while requests from the load container exercised nginx
and the internal service boundaries.

## Reproduction

Run from the repository root. Save fresh results under distinct filenames rather
than overwriting the historical records. The Node probe has no npm dependencies.
The Python probe requires Pillow and FFmpeg/ffprobe; the host environment differs
from the production image, so compare only within the same recorded environment.

```bash
node memory-bank/intents/001-phase-2-quality-improvements/evidence/ack-order.cjs
python3 memory-bank/intents/001-phase-2-quality-improvements/evidence/video-local-probe.py --output /tmp/picturas-video-probe.json
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q Tools/video/tests -p no:cacheprovider
```

The isolated experiment used this local image ID:

```text
sha256:4beaa475d81ef9317a63cc14cf0b2dacdb7bb24a6836bc55bf8cdd16b0b64d43
```

The exact command used in this workspace was:

```bash
docker run --rm --network none --read-only --cpus 2 --memory 1g --memory-swap 1g --tmpfs /tmp:rw,nosuid,nodev,size=256m --mount type=bind,src=/home/luis/RAS/Projeto/picturas-27,dst=/workspace,readonly --workdir /workspace --env PYTHONDONTWRITEBYTECODE=1 --entrypoint python sha256:4beaa475d81ef9317a63cc14cf0b2dacdb7bb24a6836bc55bf8cdd16b0b64d43 memory-bank/intents/001-phase-2-quality-improvements/evidence/video-local-probe.py --revision 5678c7cecca1e78ad54ce80e68a3f8f8988bd125 --environment-label isolated-video-image-2cpu-1GiB --output -
```

Adapt the absolute bind source on another machine and identify its actual source
revision. If the image ID is unavailable, build the video image from the identified
revision and record the new image ID and dependency versions. Do not assume that
rebuilding a moving base image produces the same environment. The `--revision`
argument is a supplied label; compare source hashes to verify what was measured.

The probe processes the existing 10 s / 1280×720 sample with brightness 0.6 and
resize to 320×240, then repeats ordinary preview, extraction of three PNGs and
extraction preview. Each valid case runs three times in fixed order. Generated
outputs live in a temporary directory and are removed; JSON retains hashes and
metadata. No accounts, queues, models or application volumes are accessed.

For renewed source inspection, use `git rev-parse HEAD`, the restricted application
diff recorded in the inventory, and SHA-256 of the listed files. A fresh checkout
may have documentation changes while retaining identical application sources.

# Exploration Evidence

These artifacts support the six-direction investigation. They are preliminary
observations, not approved requirement baselines or team decisions. Source context
and detailed protocols are in the [investigation plan](../investigation-plan.md).

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

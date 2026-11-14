# Exploration Verification Record

The source revision was `5678c7cecca1e78ad54ce80e68a3f8f8988bd125`.
The application diff against `484be13` was empty for the inspected application
folders, Compose and RabbitMQ configuration. New files are exploration artifacts;
no application refactoring was performed.

## Environment Checks

- `docker compose ps --format '{{.Service}} {{.State}} {{.Health}}'` completed
  successfully with no services listed for this Compose project.
- Required application images were present locally. The complete stack was not
  started. A separate, temporary video-image container ran without network access
  or application data volumes; the repository bind was read-only.
- The host had 20 logical CPUs, approximately 15 GiB total RAM and approximately
  104 GiB free disk at initial inspection. Free resources vary over time; the
  source inventory records a later point-in-time memory observation.
- Host: Python 3.10.12, Pillow 9.0.1, FFmpeg/ffprobe 4.4.2 and pytest 9.0.2.
- Isolated video image: Python 3.11.18, Pillow 11.0.0, FFmpeg/ffprobe 7.1.5;
  constrained to 2 CPU and 1 GiB with a 256 MiB temporary filesystem.
- Node v20.19.6 was available. Project npm dependencies and host Faster-Whisper
  were absent. No packages or models were downloaded or installed.
- Docker metadata access needed sandbox escalation. The first Node probe could
  not spawn `git` inside the sandbox; the successful rerun supplied the persisted
  acknowledgement result. These access restrictions were not application failures.

## Existing Video Tests

Command:

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q Tools/video/tests -p no:cacheprovider
```

Observed final output:

```text
74 passed in 35.55s
```

The tests used the host dependencies and real FFmpeg. Subtitle recognition is
simulated by the existing tests. This run does not demonstrate real Whisper
accuracy, throughput, crash recovery or the reliability success-rate requirement.
The orchestrator's Node suite was not rerun because its host dependencies were
absent; its earlier results remain historical EV-28 evidence.

## Acknowledgement Order

The actual helper source was evaluated with a fake AMQP channel and a callback
blocked on a controlled promise. Events were:

```text
callback-start
ack
callback-complete
```

This confirms acknowledgement before completion of the asynchronous callback for
the tested helper. It does not execute the real orchestrator callback, broker or
database and cannot quantify message loss. Source SHA-256 and execution time are
in the [raw result](ack-order-2026-11-14.json).

## Isolated Processor Pilot

Input: `samples/video/sample_10s_720p.mp4`, 3,885,435 bytes, 10 s,
1280×720 at 30 fps, H.264 with AAC audio. Ordinary tools were brightness 0.6
then resize to 320×240. Extraction adds three PNG frames. Preview modes use the
existing processor semantics. Wall time covers `process_video`, excluding the
probe's post-call metadata/hash checks and all application services.

| Case | Repetitions | Minimum (s) | Median (s) | Maximum (s) |
|------|-------------|-------------|------------|-------------|
| ordinary | 3 | 4.407 | 4.446 | 4.912 |
| ordinary-preview | 3 | 1.633 | 1.686 | 1.848 |
| frames | 3 | 4.679 | 4.851 | 4.931 |
| frames-preview | 3 | 4.506 | 4.843 | 5.271 |

All twelve valid calls completed. Ordinary outputs had H.264/AAC and the expected
10 s full / 3 s preview durations. Extraction returned three frames; its preview
returned one contact sheet. Both host and isolated-container runs preserved the
input SHA-256. The corrupt-input probe raised `InvalidVideo` and left no target
output in either environment.

The extraction preview includes processing of the complete edited timeline,
consistent with the source. Its observed cost was closer to full extraction than
to ordinary preview. This is an exploratory observation with three repetitions,
not a statistical generalization or a proven violation of a chosen target.

The host and container pilots have different CPU limits, Python/Pillow/FFmpeg
versions and runtime environments. Their differences are not a before/after
refactoring comparison. The probe gained optional revision-label/stdout arguments
between the host and container executions; the workloads were unchanged.

## Limits and Next Measurements

No queue throughput, live WebSocket cadence, upload memory peaks, cross-owner
API attempts, real speech processing or participant usability measurements were
collected. No worker scaling or application crash was performed. Callback timing
is local to the processor, not delivery timing in a browser. Three fixed-order
repetitions on a shared host are insufficient for p95 or acceptance claims.

Use the [investigation protocols](../investigation-plan.md) to obtain the missing
candidate-specific evidence. No final pair, numerical target, minimum acceptable
value or whole-team approval has been inferred from this exploration.

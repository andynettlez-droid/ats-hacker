# Controlled-Screen Adobe Finish Contract

## Production status

This is an optional, fail-closed finishing handoff. It does **not** generate an
After Effects project and it does **not** publish.

The installed `AfterFX` command-line scripting path has hung without creating
the smoke-test `.aep`, so claiming automatic project creation would be unsafe.
The bridge instead prepares a manifest, requires an explicit review of a
manually built project, runs `aerender` only on that hash-bound project, restores
the original AAC packets, and validates the result.

The legacy `fill_template.jsx`, `physical_prop_finish.jsx`, and
`render_aep.ps1` experiments do not meet this controlled-screen contract. In
particular, they can rebuild narration as a separate AE layer, scale footage,
hard-code duration, and add text. Do not use them for this lane.

## Fixed contract

Input:

- one already-rendered `.mp4` with exactly one H.264 video stream;
- exact stored dimensions of 1080x1920, square pixels, no rotation metadata;
- constant frame rate and a countable frame total;
- exactly one AAC narration stream;
- `beat_map.json` with ordered `audioSec` and `visualSec` values no more than
  0.5 seconds apart.

Adobe may add only:

- a restrained marker sweep over existing baked pixels;
- subtle screen/paper texture;
- a soft shadow;
- polish around the already-baked CTA.

Adobe must use one baked source layer at 100% scale, centered at 540x960, with
no transform keyframes, time remapping, camera, 3D layer, audio layer, or new
text layer. The intermediate must be video-only.

The project review is intentionally a human attestation. The wrapper cannot
inspect opaque `.aep` internals, and it does not claim that it can. Machine
validation owns dimensions, frame rate, frame count, timestamps, codecs, file
hashes, and source-AAC packet provenance.

## Workflow

Check readiness without writing anything:

```powershell
py -3 marketing_agent/adobe_finish_bridge.py readiness `
  --source marketing/growth_runs/RUN_ID/controlled_short.mp4 `
  --beat-map marketing/growth_runs/RUN_ID/beat_map.json
```

Preview the handoff manifest without writing it:

```powershell
py -3 marketing_agent/adobe_finish_bridge.py prepare `
  --source marketing/growth_runs/RUN_ID/controlled_short.mp4 `
  --beat-map marketing/growth_runs/RUN_ID/beat_map.json `
  --manifest marketing/growth_runs/RUN_ID/adobe_finish_manifest.json `
  --adobe-video-out marketing/growth_runs/RUN_ID/adobe_finish_video_only.mov `
  --final-out marketing/growth_runs/RUN_ID/controlled_short_adobe_finished.mp4 `
  --dry-run
```

Run the same command without `--dry-run` to write the manifest. Build the AEP
manually from that manifest, using the composition name
`Signal Controlled Screen Finish`, then record the completed visual review:

```powershell
py -3 marketing_agent/adobe_finish_bridge.py review-project `
  --manifest marketing/growth_runs/RUN_ID/adobe_finish_manifest.json `
  --project marketing/growth_runs/RUN_ID/controlled_screen_finish.aep `
  --reviewed-by "REVIEWER" `
  --confirm-contract
```

Preview or run `aerender` against only that reviewed project:

```powershell
py -3 marketing_agent/adobe_finish_bridge.py render `
  --manifest marketing/growth_runs/RUN_ID/adobe_finish_manifest.json `
  --dry-run

py -3 marketing_agent/adobe_finish_bridge.py render `
  --manifest marketing/growth_runs/RUN_ID/adobe_finish_manifest.json
```

Finalization encodes only the finished video and stream-copies narration from
the source short. It does not use `-shortest`, an audio filter, or an audio
encoder. A mismatched frame count, frame rate, timestamp, dimension, AAC packet
payload, AAC packet timing sequence, or narration offset rejects the output.

```powershell
py -3 marketing_agent/adobe_finish_bridge.py finalize `
  --manifest marketing/growth_runs/RUN_ID/adobe_finish_manifest.json
```

Revalidate later with:

```powershell
py -3 marketing_agent/adobe_finish_bridge.py validate `
  --manifest marketing/growth_runs/RUN_ID/adobe_finish_manifest.json
```

Success writes a validation receipt with status
`media_validated_not_published`. There is no publish command.

## Failure behavior

The bridge stops without success when:

- After Effects, matching `aerender`, `ffprobe`, or `ffmpeg` is unavailable;
- the source or beat map changes after manifest creation;
- the reviewed AEP changes after review;
- the Adobe intermediate contains audio;
- any source/final dimension or timing contract differs;
- final AAC packet bytes, relative packet timing, or narration offset differ;
- an output already exists and would be overwritten.

An invalid output created by the bridge is removed. Source media, beat maps,
projects, and existing outputs are never overwritten.

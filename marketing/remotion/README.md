# ATSHacker Remotion Pipeline

Programmatic video (React + [Remotion](https://www.remotion.dev/)) for auto-generating
captioned vertical short-form videos for **TikTok / Reels / Shorts**.

The flagship template is **`ScoreReveal`** — a 16-second, 1080x1920, 30fps video
built around the ATS match-score reveal (the visual climax). Everything is
data-driven via `defaultProps`, so you can spin up many variants by swapping props.

---

## Install

> **Windows gotcha:** the shell may have `NODE_ENV=production` + `npm omit=dev`,
> which prunes dev dependencies. Always install with dev deps explicitly:

```bat
cd marketing\remotion
set NODE_ENV=development && npm install --include=dev
```

(macOS/Linux: `NODE_ENV=development npm install --include=dev`)

Node 18+ is required. Remotion downloads a headless Chromium on the first render.

---

## Preview (Remotion Studio)

```bash
npm run studio
```

Opens the interactive studio at <http://localhost:3000>. You can scrub the timeline,
live-edit props in the right-hand panel, and preview every scene.

---

## Render an MP4

```bash
npm run render
```

This runs `remotion render ScoreReveal out/score-reveal.mp4` and writes the H.264 MP4
to `out/score-reveal.mp4`.

The **first** render downloads a headless Chromium (~110 MB) — that step needs network
access and can take a minute. Subsequent renders reuse it.

---

## Custom props

Three ways to drive the content:

### 1. Inline JSON on the CLI (best for automation)

```bash
npx remotion render ScoreReveal out/my-video.mp4 --props="{\"hook1\":\"512 applications.\",\"hook2\":\"1 callback.\",\"beforeScore\":31,\"afterScore\":92,\"missing\":[\"SQL\",\"dashboards\",\"A/B testing\"],\"cta\":\"Free score in bio 👇\"}"
```

### 2. A props file

```bash
npx remotion render ScoreReveal out/my-video.mp4 --props=./props/data-analyst.json
```

### 3. Edit the defaults

Change `defaultScoreRevealProps` in `src/ScoreReveal.tsx`.

### Available props

| Prop          | Type       | Description                                                        |
| ------------- | ---------- | ------------------------------------------------------------------ |
| `hook1`       | `string`   | First punch line (0–2.5s).                                         |
| `hook2`       | `string`   | Emerald punch-in line.                                             |
| `subline`     | `string`   | Explainer shown over the search-bar scene.                        |
| `missing`     | `string[]` | Missing keywords — render as red chips that flip green.            |
| `beforeScore` | `number`   | Starting ATS score (the count-up starts here).                     |
| `afterScore`  | `number`   | Final ATS score. Color tiers: ≥75 emerald, 50–74 amber, <50 red.   |
| `cta`         | `string`   | Call-to-action shown with the wordmark (12–16s).                   |
| `bgVideo`     | `string?`  | Optional full-bleed background clip (see below).                   |

---

## Background B-roll (Seedance / Kling / etc.)

Pass a generated clip via the `bgVideo` prop. It renders full-bleed behind a dark
scrim so captions stay legible. If omitted, a solid dark background with subtle
emerald accents is used.

- **Local file:** drop the clip in `public/` and pass the filename, e.g.
  `--props="{\"bgVideo\":\"broll.mp4\"}"` (Remotion resolves it via `staticFile`).
- **Remote URL:** pass an `https://...` URL directly and it is used as-is.

```bash
npx remotion render ScoreReveal out/score-reveal.mp4 --props="{\"bgVideo\":\"https://cdn.example.com/kling-clip.mp4\"}"
```

A Seedance/Kling vertical (1080x1920) clip works best; the scene loops and is muted.

---

## End-to-end with the auto-poster

The rendered MP4 feeds the Upload-Post auto-poster in `marketing/autopost/`.

1. Render: `npm run render` (or with custom `--props`).
2. Copy/move the output into the auto-poster's watch folder:

   ```bat
   copy out\score-reveal.mp4 ..\autopost\videos\
   ```

3. Reference the file in `marketing/autopost/posts.json` and run the poster
   (`node marketing/autopost/post.mjs`). See `marketing/autopost/README.md`.

> `marketing/autopost/videos/` and `marketing/remotion/out/` are git-ignored —
> the generated MP4s are build artifacts, not source.

---

## Project layout

```
marketing/remotion/
├── package.json          # type: module; studio/render/bundle/typecheck scripts
├── tsconfig.json
├── remotion.config.ts    # h264, jpeg frames, auto concurrency
├── public/               # optional: local bgVideo clips (staticFile)
└── src/
    ├── index.ts          # registerRoot
    ├── Root.tsx          # <Composition id="ScoreReveal" .../>
    └── ScoreReveal.tsx    # the template + scenes + props schema
```

## Scripts

| Script              | What it does                                          |
| ------------------- | ----------------------------------------------------- |
| `npm run studio`    | Launch Remotion Studio (live preview).                |
| `npm run render`    | Render `ScoreReveal` to `out/score-reveal.mp4`.       |
| `npm run bundle`    | Bundle the project (validates the graph, no Chromium).|
| `npm run typecheck` | `tsc --noEmit`.                                        |

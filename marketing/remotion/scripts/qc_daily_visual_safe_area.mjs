import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { inflateSync } from "node:zlib";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const remotionDir = path.resolve(__dirname, "..");
const rootDir = path.resolve(remotionDir, "..", "..");
const outDir = path.join(remotionDir, "out");
const reportPath = path.join(outDir, "daily-visual-safe-area-qc.json");

const DEFAULT_DRAFTS = path.join(
  rootDir,
  "marketing",
  "daily_content",
  "2026-06-29-ai-looking-resume-bullets-recruiters-ignore",
  "autopost_drafts.json",
);

const DEFAULT_FRAMES = [60, 330, 690, 1080];
const SAFE_MARGIN = 28;
const MAX_ATTENTION_PIXELS_PER_EDGE = 220;

const parseArgs = () => {
  const args = process.argv.slice(2);
  const options = {
    drafts: DEFAULT_DRAFTS,
    frames: DEFAULT_FRAMES,
    render: false,
    json: false,
    report: reportPath,
  };

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === "--drafts") {
      options.drafts = path.resolve(process.cwd(), args[i + 1]);
      i += 1;
    } else if (arg === "--frames") {
      options.frames = String(args[i + 1])
        .split(",")
        .map((value) => Number(value.trim()))
        .filter(Number.isFinite);
      i += 1;
    } else if (arg === "--render") {
      options.render = true;
    } else if (arg === "--json") {
      options.json = true;
    } else if (arg === "--report") {
      options.report = path.resolve(process.cwd(), args[i + 1]);
      i += 1;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!options.frames.length) {
    throw new Error("At least one frame is required.");
  }

  return options;
};

const readJson = (filePath) => JSON.parse(readFileSync(filePath, "utf8"));

const resolveRootRef = (ref) => path.join(rootDir, String(ref).replace(/^marketing[\\/]/, "marketing/"));

const safeSlug = (value) =>
  String(value || "short")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 70) || "short";

const quoteForShell = (value) => `"${String(value).replaceAll('"', '\\"')}"`;

const renderStill = ({ composition, propsPath, outputPath, frame }) => {
  const args = [
    "remotion",
    "still",
    composition,
    path.relative(remotionDir, outputPath),
    `--props=${path.basename(propsPath)}`,
    `--frame=${frame}`,
  ];
  const result =
    process.platform === "win32"
      ? spawnSync(`npx.cmd ${args.map(quoteForShell).join(" ")}`, {
          cwd: remotionDir,
          encoding: "utf8",
          shell: true,
          stdio: "pipe",
        })
      : spawnSync("npx", args, {
          cwd: remotionDir,
          encoding: "utf8",
          stdio: "pipe",
        });

  if (result.status !== 0) {
    throw new Error(
      `Failed to render ${path.basename(outputPath)} at frame ${frame}: ` +
        `${result.error?.message || result.stderr || result.stdout || `exit ${result.status}`}`,
    );
  }
};

const paethPredictor = (left, above, upperLeft) => {
  const estimate = left + above - upperLeft;
  const leftDistance = Math.abs(estimate - left);
  const aboveDistance = Math.abs(estimate - above);
  const upperLeftDistance = Math.abs(estimate - upperLeft);
  if (leftDistance <= aboveDistance && leftDistance <= upperLeftDistance) return left;
  if (aboveDistance <= upperLeftDistance) return above;
  return upperLeft;
};

const parsePng = (filePath) => {
  const buffer = readFileSync(filePath);
  const signature = buffer.subarray(0, 8).toString("hex");
  if (signature !== "89504e470d0a1a0a") {
    throw new Error(`${filePath} is not a PNG file.`);
  }

  let offset = 8;
  let width = 0;
  let height = 0;
  let bitDepth = 0;
  let colorType = 0;
  const idatChunks = [];

  while (offset < buffer.length) {
    const length = buffer.readUInt32BE(offset);
    const type = buffer.subarray(offset + 4, offset + 8).toString("ascii");
    const data = buffer.subarray(offset + 8, offset + 8 + length);
    offset += 12 + length;

    if (type === "IHDR") {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      bitDepth = data[8];
      colorType = data[9];
    } else if (type === "IDAT") {
      idatChunks.push(data);
    } else if (type === "IEND") {
      break;
    }
  }

  if (bitDepth !== 8 || (colorType !== 2 && colorType !== 6)) {
    throw new Error(`${filePath} uses unsupported PNG format bitDepth=${bitDepth} colorType=${colorType}.`);
  }

  const channels = colorType === 6 ? 4 : 3;
  const bytesPerPixel = channels;
  const scanlineLength = width * channels;
  const inflated = inflateSync(Buffer.concat(idatChunks));
  const pixels = new Uint8Array(width * height * 4);
  let sourceOffset = 0;
  let previous = new Uint8Array(scanlineLength);

  for (let y = 0; y < height; y += 1) {
    const filter = inflated[sourceOffset];
    sourceOffset += 1;
    const raw = inflated.subarray(sourceOffset, sourceOffset + scanlineLength);
    sourceOffset += scanlineLength;
    const row = new Uint8Array(scanlineLength);

    for (let x = 0; x < scanlineLength; x += 1) {
      const left = x >= bytesPerPixel ? row[x - bytesPerPixel] : 0;
      const above = previous[x] || 0;
      const upperLeft = x >= bytesPerPixel ? previous[x - bytesPerPixel] || 0 : 0;
      let value = raw[x];
      if (filter === 1) value = (value + left) & 255;
      else if (filter === 2) value = (value + above) & 255;
      else if (filter === 3) value = (value + Math.floor((left + above) / 2)) & 255;
      else if (filter === 4) value = (value + paethPredictor(left, above, upperLeft)) & 255;
      else if (filter !== 0) throw new Error(`${filePath} uses unsupported PNG filter ${filter}.`);
      row[x] = value;
    }

    for (let x = 0; x < width; x += 1) {
      const source = x * channels;
      const dest = (y * width + x) * 4;
      pixels[dest] = row[source];
      pixels[dest + 1] = row[source + 1];
      pixels[dest + 2] = row[source + 2];
      pixels[dest + 3] = channels === 4 ? row[source + 3] : 255;
    }

    previous = row;
  }

  return { width, height, pixels };
};

const lumaAt = (pixels, index) => {
  return (pixels[index] * 0.2126) + (pixels[index + 1] * 0.7152) + (pixels[index + 2] * 0.0722);
};

const isAttentionPixel = (png, x, y) => {
  const { width, height, pixels } = png;
  const index = (y * width + x) * 4;
  const alpha = pixels[index + 3];
  if (alpha < 24) return false;
  const red = pixels[index];
  const green = pixels[index + 1];
  const blue = pixels[index + 2];
  const max = Math.max(red, green, blue);
  const min = Math.min(red, green, blue);
  const brightness = (red + green + blue) / 3;
  const saturation = max - min;
  const luma = lumaAt(pixels, index);
  const samples = [
    [Math.max(0, x - 6), y],
    [Math.min(width - 1, x + 6), y],
    [x, Math.max(0, y - 6)],
    [x, Math.min(height - 1, y + 6)],
  ];
  const contrast = Math.max(
    ...samples.map(([sampleX, sampleY]) => {
      const sampleIndex = (sampleY * width + sampleX) * 4;
      return Math.abs(luma - lumaAt(pixels, sampleIndex));
    }),
  );
  const redAlert = red > 130 && green < 120 && blue < 130;
  const vividAccent = saturation > 82;
  const textLikeContrast = contrast > 42 && (brightness > 205 || brightness < 90);
  const accentLikeContrast = contrast > 28 && (vividAccent || redAlert);
  return textLikeContrast || accentLikeContrast;
};

const scanSafeArea = (png) => {
  const edges = {
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  };

  for (let y = 0; y < png.height; y += 1) {
    for (let x = 0; x < png.width; x += 1) {
      if (!isAttentionPixel(png, x, y)) continue;
      if (x < SAFE_MARGIN) edges.left += 1;
      if (x >= png.width - SAFE_MARGIN) edges.right += 1;
      if (y < SAFE_MARGIN) edges.top += 1;
      if (y >= png.height - SAFE_MARGIN) edges.bottom += 1;
    }
  }

  return edges;
};

const collectShortDrafts = (drafts) =>
  drafts.filter((draft) => draft.composition === "ResumeCrimeScene" || draft.composition === "ResumeDeskReview");

const durationFramesFromProps = (props) => {
  const fps = 30;
  if (Number.isFinite(Number(props.durationSeconds))) {
    return Math.max(1, Math.round(Number(props.durationSeconds) * fps));
  }
  const captions = Array.isArray(props.captions) ? props.captions : [];
  const lastEndMs = Math.max(0, ...captions.map((caption) => Number(caption.endMs || 0)));
  if (lastEndMs > 0) {
    return Math.max(1, Math.round((lastEndMs / 1000 + 3.2) * fps));
  }
  return 45 * fps;
};

const framesForProps = (props, requestedFrames) => {
  const durationFrames = durationFramesFromProps(props);
  const maxFrame = Math.max(0, durationFrames - 1);
  const percentages = [0.08, 0.32, 0.62, 0.9];
  const defaultFrames = percentages.map((pct) => Math.min(maxFrame, Math.max(0, Math.round(maxFrame * pct))));
  const rawFrames = requestedFrames === DEFAULT_FRAMES ? defaultFrames : requestedFrames;
  return [...new Set(rawFrames.map((frame) => Math.min(maxFrame, Math.max(0, Number(frame)))))]
    .filter(Number.isFinite);
};

const main = () => {
  const options = parseArgs();
  mkdirSync(outDir, { recursive: true });

  const drafts = collectShortDrafts(readJson(options.drafts));
  const report = {
    passed: true,
    safeMargin: SAFE_MARGIN,
    maxAttentionPixelsPerEdge: MAX_ATTENTION_PIXELS_PER_EDGE,
    drafts: [],
  };

  for (const draft of drafts) {
    const propsPath = resolveRootRef(draft.renderProps);
    const draftReport = {
      title: draft.title || draft.file,
      renderProps: draft.renderProps,
      passed: true,
      frames: [],
    };

    if (!existsSync(propsPath)) {
      draftReport.passed = false;
      draftReport.error = `Missing props file: ${propsPath}`;
      report.passed = false;
      report.drafts.push(draftReport);
      continue;
    }

    const props = readJson(propsPath);
    for (const frame of framesForProps(props, options.frames)) {
      const outputPath = path.join(outDir, `visual-safe-area-${safeSlug(draft.title || draft.file)}-${frame}.png`);
      if (options.render || !existsSync(outputPath)) {
        renderStill({ composition: draft.composition || "ResumeCrimeScene", propsPath, outputPath, frame });
      }

      const edges = scanSafeArea(parsePng(outputPath));
      const violations = Object.entries(edges)
        .filter(([, count]) => count > MAX_ATTENTION_PIXELS_PER_EDGE)
        .map(([edge, count]) => `${edge}: ${count}`);
      const framePassed = violations.length === 0;
      if (!framePassed) {
        draftReport.passed = false;
        report.passed = false;
      }

      draftReport.frames.push({
        frame,
        still: path.relative(rootDir, outputPath).replaceAll(path.sep, "/"),
        edges,
        passed: framePassed,
        violations,
      });
    }

    report.drafts.push(draftReport);
  }

  writeFileSync(options.report, JSON.stringify(report, null, 2) + "\n");

  if (options.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    for (const draft of report.drafts) {
      console.log(`${draft.passed ? "PASS" : "FAIL"} ${draft.title}`);
      for (const frame of draft.frames || []) {
        console.log(
          `  ${frame.passed ? "PASS" : "FAIL"} frame ${frame.frame}: ` +
            `L${frame.edges.left} R${frame.edges.right} T${frame.edges.top} B${frame.edges.bottom}`,
        );
      }
      if (draft.error) console.log(`  ${draft.error}`);
    }
    console.log(`\nReport: ${path.relative(rootDir, options.report).replaceAll(path.sep, "/")}`);
    console.log(report.passed ? "Visual safe-area QC passed." : "Visual safe-area QC failed.");
  }

  if (!report.passed) {
    process.exit(1);
  }
};

main();

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const videoVariants = [
  {
    fileName: 'resumes-keyword-check.mp4',
    caption: 'Recruiters search by keyword. Not matched = not seen. Free checker, link in bio #resumetips',
    scheduleDate: '2026-06-28T16:00:00Z',
    props: {
      hook1: 'Recruiters search resumes',
      hook2: 'by keyword.',
      subline: 'Not matched = not seen by human recruiters.',
      missing: ['SQL', 'metrics', 'pipeline'],
      beforeScore: 32,
      afterScore: 88,
      cta: 'Free checker link in bio 👇',
      bgVideo: 'bg.mp4'
    }
  },
  {
    fileName: 'resumes-get-buried.mp4',
    caption: 'Why resumes get buried: lack of keywords. Get a free ATS score check. Link in bio #jobsearch',
    scheduleDate: '2026-06-29T16:00:00Z',
    props: {
      hook1: 'Why resumes get buried',
      hook2: 'under 100s of apps.',
      subline: 'Lack of keywords drops your ranking.',
      missing: ['Python', 'analytics', 'dashboards'],
      beforeScore: 45,
      afterScore: 92,
      cta: 'Free ATS score in bio 👇',
      bgVideo: 'bg2.mp4'
    }
  },
  {
    fileName: 'ats-no-autoreject.mp4',
    caption: "ATS doesn't auto-reject you - it ranks by keyword. Match it. Free score, link in bio #jobsearch",
    scheduleDate: '2026-06-30T16:00:00Z',
    props: {
      hook1: 'The ATS does NOT',
      hook2: 'auto-reject you.',
      subline: 'It just ranks you. Match keywords to rank.',
      missing: ['Agile', 'cross-functional', 'deliverables'],
      beforeScore: 55,
      afterScore: 91,
      cta: 'Free score link in bio 👇',
      bgVideo: 'bg.mp4'
    }
  },
  {
    fileName: 'same-resume-different-jobs.mp4',
    caption: 'Same resume, different job = different score. Tailor every time. Free score, link in bio #jobhunt',
    scheduleDate: '2026-07-01T16:00:00Z',
    props: {
      hook1: 'Same resume, different jobs',
      hook2: 'totally different scores.',
      subline: 'Tailor your resume keywords every time.',
      missing: ['AWS', 'CI/CD', 'Kubernetes'],
      beforeScore: 28,
      afterScore: 85,
      cta: 'Tailor in seconds, link in bio 👇',
      bgVideo: 'bg2.mp4'
    }
  },
  {
    fileName: 'stop-paying-subscriptions.mp4',
    caption: 'No more resume subscriptions. Free match score, $9.99 once to fix. Link in bio #careeradvice',
    scheduleDate: '2026-07-02T16:00:00Z',
    props: {
      hook1: 'Stop paying $30/month',
      hook2: 'for resume builders.',
      subline: 'Get a free score, pay $9.99 only to fix.',
      missing: ['Figma', 'wireframes', 'prototypes'],
      beforeScore: 39,
      afterScore: 94,
      cta: 'No subscription! Link in bio 👇',
      bgVideo: 'bg.mp4'
    }
  },
  {
    fileName: 'number-one-keyword.mp4',
    caption: 'Job title is key. Match the JD phrasing to rank higher. Free score check, link in bio #jobhunt',
    scheduleDate: '2026-07-03T16:00:00Z',
    props: {
      hook1: 'The #1 keyword is',
      hook2: 'your target job title.',
      subline: 'Match the job title phrasing exactly.',
      missing: ['product manager', 'roadmap', 'KPIs'],
      beforeScore: 41,
      afterScore: 89,
      cta: 'Check your match free in bio 👇',
      bgVideo: 'bg2.mp4'
    }
  }
];

const cmdPrefix = process.platform === 'win32' ? 'npx.cmd' : 'npx';

console.log('Starting programmatic video rendering pipeline...');

for (const variant of videoVariants) {
  const outPath = path.join(__dirname, 'out', variant.fileName);
  const destPath = path.join(__dirname, '..', 'autopost', 'videos', variant.fileName);
  const tempPropsPath = path.join(__dirname, 'temp_props.json');

  console.log(`\n--- Rendering: ${variant.fileName} ---`);
  
  // Write temp props
  fs.writeFileSync(tempPropsPath, JSON.stringify(variant.props, null, 2));

  try {
const command = process.platform === 'win32'
      ? `node.exe node_modules/@remotion/cli/remotion-cli.js render ScoreReveal out/${variant.fileName} --props=temp_props.json`
      : `npx remotion render ScoreReveal out/${variant.fileName} --props=temp_props.json`;
    console.log(`Executing: ${command}`);
    execSync(command, { cwd: __dirname, stdio: 'inherit' });

    // Copy to autopost videos
    console.log(`Copying output to: ${destPath}`);
    fs.copyFileSync(outPath, destPath);

    console.log(`Successfully completed rendering ${variant.fileName}`);
  } catch (err) {
    console.error(`Failed rendering ${variant.fileName}:`, err);
  } finally {
    if (fs.existsSync(tempPropsPath)) {
      fs.unlinkSync(tempPropsPath);
    }
  }
}

console.log('\nAll videos rendered. Updating posts.json queue...');

const postsJsonPath = path.join(__dirname, '..', 'autopost', 'posts.json');
let posts = [];
if (fs.existsSync(postsJsonPath)) {
  try {
    posts = JSON.parse(fs.readFileSync(postsJsonPath, 'utf-8'));
  } catch (e) {
    console.error('Error parsing posts.json, resetting to empty array', e);
  }
}

for (const variant of videoVariants) {
  const postFileRelative = `videos/${variant.fileName}`;
  // Avoid duplicate entries
  if (!posts.some(p => p.file === postFileRelative)) {
    posts.push({
      caption: variant.caption,
      file: postFileRelative,
      platforms: ['instagram', 'youtube'],
      scheduleDate: variant.scheduleDate
    });
    console.log(`Queued post: ${variant.fileName} scheduled for ${variant.scheduleDate}`);
  }
}

fs.writeFileSync(postsJsonPath, JSON.stringify(posts, null, 2), 'utf-8');
console.log('posts.json queue updated successfully.');

console.log('\nUpdating videos_catalog.md...');
const catalogPath = path.join(__dirname, '..', 'videos_catalog.md');
if (fs.existsSync(catalogPath)) {
  let catalog = fs.readFileSync(catalogPath, 'utf-8');
  
  let appendContent = '\n\n## 4. Programmatic Video Pipeline Rendered Cycle\n';
  for (const variant of videoVariants) {
    appendContent += `\n### [${variant.props.hook1} ${variant.props.hook2}](file:///${path.join(__dirname, 'out', variant.fileName).replace(/\\/g, '/')})\n`;
    appendContent += `*   **Path:** \`marketing/autopost/videos/${variant.fileName}\`\n`;
    appendContent += `*   **Hook:** "${variant.props.hook1} ${variant.props.hook2}"\n`;
    appendContent += `*   **Missing Keywords:** ${JSON.stringify(variant.props.missing)}\n`;
    appendContent += `*   **Score Change:** ${variant.props.beforeScore}% &rarr; ${variant.props.afterScore}%\n`;
    appendContent += `*   **Scheduled Date:** ${variant.scheduleDate}\n`;
    appendContent += `*   **Caption:** "${variant.caption}"\n`;
  }
  
  fs.writeFileSync(catalogPath, catalog + appendContent, 'utf-8');
  console.log('videos_catalog.md updated successfully.');
}

console.log('\nVideo rendering pipeline finished successfully!');

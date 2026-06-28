import { ImageResponse } from 'next/og';

export const runtime = 'edge';

function clampScore(raw: string | null) {
  return Math.max(0, Math.min(100, parseInt(raw || '0', 10) || 0));
}

function safeCount(raw: string | null) {
  return Math.max(0, Math.min(99, parseInt(raw || '0', 10) || 0));
}

function sanitizeKeyword(keyword: string): string {
  const normalized = keyword
    .replace(/[^\w\s+#./-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return normalized.length > 34 ? `${normalized.slice(0, 31)}...` : normalized;
}

function parseSamples(raw: string | null, limit = 3): string[] {
  const seen = new Set<string>();
  return (raw || '')
    .split('|')
    .map(sanitizeKeyword)
    .filter((keyword) => {
      const key = keyword.toLowerCase();
      if (!keyword || seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, limit);
}

function scoreColor(score: number) {
  if (score >= 75) return '#34d399';
  if (score >= 50) return '#fbbf24';
  return '#fb7185';
}

function scoreLabel(score: number) {
  if (score >= 75) return 'Strong Signal';
  if (score >= 50) return 'Needs Sharper Targeting';
  return 'Qualified, But Invisible';
}

function SignalMark() {
  return (
    <div style={{ position: 'relative', width: 124, height: 124, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div
        style={{
          position: 'absolute',
          width: 112,
          height: 46,
          border: '3px solid rgba(125,223,255,0.78)',
          borderRadius: '999px',
          transform: 'rotate(-22deg)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 116,
          height: 48,
          border: '3px solid rgba(96,165,250,0.58)',
          borderRadius: '999px',
          transform: 'rotate(58deg)',
        }}
      />
      <div
        style={{
          position: 'relative',
          width: 74,
          height: 74,
          borderRadius: '999px',
          background: 'radial-gradient(circle at 42% 32%, #ffffff 0 8%, #9ff7ff 15%, #38d5ff 29%, #2563eb 64%, #020617 100%)',
          boxShadow: '0 0 46px rgba(56,213,255,0.72), inset 0 0 18px rgba(255,255,255,0.38)',
        }}
      >
        <div style={{ position: 'absolute', left: 22, top: 27, width: 10, height: 10, borderRadius: '999px', background: '#ffffff' }} />
        <div style={{ position: 'absolute', right: 22, top: 27, width: 10, height: 10, borderRadius: '999px', background: '#ffffff' }} />
        <div
          style={{
            position: 'absolute',
            left: 25,
            top: 46,
            width: 24,
            height: 11,
            borderBottom: '4px solid rgba(255,255,255,0.95)',
            borderRadius: '0 0 999px 999px',
          }}
        />
      </div>
    </div>
  );
}

// Dynamic share card:
// /api/og?score=41&m=9&mk=HubSpot|CAC&hit=Marketing
export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const score = clampScore(searchParams.get('score'));
  const missing = safeCount(searchParams.get('m'));
  const missingSamples = parseSamples(searchParams.get('mk'), 3);
  const matchedSamples = parseSamples(searchParams.get('hit'), 2);
  const color = scoreColor(score);
  const label = scoreLabel(score);

  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          background:
            'radial-gradient(circle at 15% 12%, rgba(56,213,255,0.22), transparent 310px), radial-gradient(circle at 86% 22%, rgba(37,99,235,0.2), transparent 330px), linear-gradient(135deg, #020617 0%, #07111f 62%, #03111a 100%)',
          color: '#f8fafc',
          padding: 64,
          fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
            <SignalMark />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', fontSize: 56, fontWeight: 900, letterSpacing: -3 }}>
                Signal<span style={{ color: '#34d399' }}>.</span>
              </div>
              <div style={{ display: 'flex', fontSize: 22, color: '#94a3b8', fontWeight: 800, letterSpacing: 2, textTransform: 'uppercase' }}>
                by ATSHacker
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <div style={{ display: 'flex', color: '#7ddfff', fontSize: 32, fontWeight: 900, letterSpacing: 2, textTransform: 'uppercase' }}>
              Resume match score
            </div>
            <div style={{ display: 'flex', fontSize: 76, fontWeight: 900, lineHeight: 0.95, maxWidth: 690, letterSpacing: -4 }}>
              {label}
            </div>
            <div style={{ display: 'flex', fontSize: 31, color: '#cbd5e1', maxWidth: 720, lineHeight: 1.25, fontWeight: 700 }}>
              {missing > 0
                ? `${missing} target-job gaps could keep this resume harder to find.`
                : 'Target-job language is showing up clearly.'}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16, color: '#a7f3d0', fontSize: 26, fontWeight: 900 }}>
            <span>Check your free score</span>
            <span style={{ color: '#7ddfff' }}>ats-hacker-swart.vercel.app</span>
          </div>
        </div>

        <div
          style={{
            width: 390,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            border: '1px solid rgba(125,223,255,0.26)',
            borderRadius: 34,
            background: 'rgba(3,7,18,0.62)',
            padding: 34,
            boxShadow: 'inset 0 0 58px rgba(56,213,255,0.08)',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', fontSize: 24, color: '#94a3b8', fontWeight: 900, textTransform: 'uppercase', letterSpacing: 2 }}>
              This resume scored
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end', lineHeight: 1, marginTop: 10 }}>
              <span style={{ fontSize: 172, fontWeight: 900, color, letterSpacing: -10 }}>{score}</span>
              <span style={{ fontSize: 52, color: '#64748b', fontWeight: 900, paddingBottom: 16 }}>/100</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, fontSize: 24, fontWeight: 900 }}>
              <span style={{ color: '#fecdd3' }}>Missing gaps</span>
              <span style={{ color: '#fecdd3' }}>{missing}</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {(missingSamples.length ? missingSamples : ['Role keywords']).map((keyword) => (
                <span
                  key={keyword}
                  style={{
                    display: 'flex',
                    border: '1px solid rgba(251,113,133,0.28)',
                    borderRadius: 14,
                    background: 'rgba(251,113,133,0.12)',
                    color: '#ffe4e6',
                    fontSize: 20,
                    fontWeight: 900,
                    padding: '8px 11px',
                  }}
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', fontSize: 22, color: '#bbf7d0', fontWeight: 900 }}>Already matched</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {(matchedSamples.length ? matchedSamples : ['Real experience']).map((keyword) => (
                <span
                  key={keyword}
                  style={{
                    display: 'flex',
                    border: '1px solid rgba(52,211,153,0.28)',
                    borderRadius: 14,
                    background: 'rgba(52,211,153,0.12)',
                    color: '#dcfce7',
                    fontSize: 20,
                    fontWeight: 900,
                    padding: '8px 11px',
                  }}
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    ),
    { width: 1200, height: 630 },
  );
}

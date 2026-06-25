import { ImageResponse } from 'next/og';

export const runtime = 'edge';

// Dynamic share card: /api/og?score=41&m=9
export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const score = Math.max(0, Math.min(100, parseInt(searchParams.get('score') || '0', 10) || 0));
  const missing = Math.max(0, parseInt(searchParams.get('m') || '0', 10) || 0);
  const scoreColor = score >= 75 ? '#10b981' : score >= 50 ? '#eab308' : '#ef4444';

  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          background: '#0a0a0a',
          color: '#ffffff',
          padding: '80px',
          fontFamily: 'sans-serif',
        }}
      >
        <div style={{ display: 'flex', fontSize: 44, fontWeight: 800 }}>
          <span>ATS</span>
          <span style={{ color: '#10b981' }}>Hacker.</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', fontSize: 36, color: '#a3a3a3' }}>My resume scored</div>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <span style={{ fontSize: 210, fontWeight: 900, color: scoreColor, lineHeight: 1 }}>{score}</span>
            <span style={{ fontSize: 64, color: '#737373', paddingBottom: 24 }}>/100</span>
          </div>
          <div style={{ display: 'flex', fontSize: 32, color: '#a3a3a3' }}>
            {missing > 0 ? `${missing} job-description keywords missing` : 'against a target job description'}
          </div>
        </div>

        <div style={{ display: 'flex', fontSize: 28, color: '#10b981' }}>
          Check your free ATS match score → ats-hacker-swart.vercel.app
        </div>
      </div>
    ),
    { width: 1200, height: 630 },
  );
}

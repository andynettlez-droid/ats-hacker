'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
  DollarSign,
  CreditCard,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Users,
  LayoutDashboard,
  Settings,
  LogOut,
  Lock,
  Loader2,
} from 'lucide-react';

type DailyPoint = { date: string; revenue: number; sales: number };
type Transaction = {
  id: string;
  date: string;
  email: string | null;
  amount: number;
  currency: string;
  status: string;
  paymentMethod: string;
};
type Stats = {
  currency: string;
  windowDays: number;
  totalRevenue: number;
  totalSales: number;
  uniqueCustomers: number;
  growthRate: number;
  dailySeries: DailyPoint[];
  recentTransactions: Transaction[];
  generatedAt: string;
  error?: string;
};

const usd = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);

// ---------------------------------------------------------------------------
// Inline SVG area chart (no chart dependency). Renders the daily revenue series.
// ---------------------------------------------------------------------------
function RevenueChart({ data }: { data: DailyPoint[] }) {
  const width = 900;
  const height = 260;
  const pad = { top: 20, right: 20, bottom: 28, left: 48 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;

  const points = data.length ? data : [{ date: '', revenue: 0, sales: 0 }];
  const maxRevenue = Math.max(1, ...points.map((d) => d.revenue));
  const stepX = points.length > 1 ? innerW / (points.length - 1) : 0;

  const x = (i: number) => pad.left + i * stepX;
  const y = (v: number) => pad.top + innerH - (v / maxRevenue) * innerH;

  const linePath = points
    .map((d, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(d.revenue).toFixed(1)}`)
    .join(' ');
  const areaPath =
    `${linePath} L ${x(points.length - 1).toFixed(1)} ${(pad.top + innerH).toFixed(1)}` +
    ` L ${x(0).toFixed(1)} ${(pad.top + innerH).toFixed(1)} Z`;

  const yTicks = 4;
  const gridLines = Array.from({ length: yTicks + 1 }, (_, i) => {
    const val = (maxRevenue / yTicks) * i;
    return { val, yPos: y(val) };
  });

  // Show ~6 evenly spaced date labels.
  const labelEvery = Math.max(1, Math.ceil(points.length / 6));

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full h-64"
      preserveAspectRatio="none"
      role="img"
      aria-label="Daily revenue chart"
    >
      <defs>
        <linearGradient id="revFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
        </linearGradient>
      </defs>

      {gridLines.map((g, i) => (
        <g key={i}>
          <line
            x1={pad.left}
            x2={width - pad.right}
            y1={g.yPos}
            y2={g.yPos}
            stroke="#262626"
            strokeWidth="1"
          />
          <text x={pad.left - 8} y={g.yPos + 4} textAnchor="end" fontSize="11" fill="#737373">
            {usd(g.val)}
          </text>
        </g>
      ))}

      <path d={areaPath} fill="url(#revFill)" />
      <path d={linePath} fill="none" stroke="#10b981" strokeWidth="2.5" />

      {points.map((d, i) =>
        i % labelEvery === 0 ? (
          <text
            key={d.date + i}
            x={x(i)}
            y={height - 8}
            textAnchor="middle"
            fontSize="10"
            fill="#737373"
          >
            {d.date.slice(5)}
          </text>
        ) : null,
      )}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Login form shown until a valid admin cookie exists.
// ---------------------------------------------------------------------------
function LoginScreen({ onSuccess }: { onSuccess: () => void }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      if (res.ok) {
        onSuccess();
      } else {
        const data = await res.json().catch(() => ({}));
        setError(data.error || 'Login failed.');
      }
    } catch {
      setError('Network error. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans flex items-center justify-center p-6 selection:bg-emerald-500/30">
      <div className="w-full max-w-sm bg-neutral-900 border border-neutral-800 rounded-2xl p-8 shadow-xl">
        <div className="text-2xl font-black tracking-tighter text-white mb-1 text-center">
          ATS<span className="text-emerald-500">Hacker.</span>
        </div>
        <div className="flex items-center justify-center gap-2 text-neutral-400 text-sm mb-6">
          <Lock className="w-4 h-4" />
          <span>Admin access</span>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <input
            type="password"
            autoFocus
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Admin password"
            className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-3 text-white placeholder-neutral-600 focus:outline-none focus:border-emerald-500 transition"
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={loading || !password}
            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-3 rounded-xl font-medium transition flex items-center justify-center gap-2"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            <span>Unlock dashboard</span>
          </button>
        </form>
        <p className="text-xs text-neutral-600 mt-6 text-center">
          Protected by ADMIN_PASSWORD. Revenue data is never shown until you sign in.
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main dashboard.
// ---------------------------------------------------------------------------
export default function AdminDashboard() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    setLoadError(null);
    try {
      const res = await fetch('/api/admin/stats', { cache: 'no-store' });
      if (res.status === 401) {
        setAuthed(false);
        return;
      }
      if (!res.ok) {
        setLoadError('Failed to load analytics.');
        setAuthed(true);
        return;
      }
      const data: Stats = await res.json();
      setStats(data);
      setAuthed(true);
    } catch {
      setLoadError('Network error loading analytics.');
      setAuthed(true);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const logout = async () => {
    await fetch('/api/admin/login', { method: 'DELETE' }).catch(() => {});
    setAuthed(false);
    setStats(null);
  };

  // Initial auth probe in flight.
  if (authed === null) {
    return (
      <div className="min-h-screen bg-neutral-950 text-neutral-100 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
      </div>
    );
  }

  if (authed === false) {
    return <LoginScreen onSuccess={loadStats} />;
  }

  const metrics = {
    revenue: stats ? usd(stats.totalRevenue) : '—',
    sales: stats ? stats.totalSales : '—',
    customers: stats ? stats.uniqueCustomers : '—',
  };
  const growth = stats?.growthRate ?? 0;
  const growthPositive = growth >= 0;
  const series = stats?.dailySeries ?? [];
  const recentTransactions = stats?.recentTransactions ?? [];

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans flex selection:bg-emerald-500/30">
      {/* Sidebar */}
      <aside className="w-64 bg-neutral-900 border-r border-neutral-800 flex flex-col hidden md:flex">
        <div className="p-6">
          <div className="text-2xl font-black tracking-tighter text-white mb-8">
            ATS<span className="text-emerald-500">Hacker.</span>
          </div>
          <nav className="space-y-2">
            <a href="#" className="flex items-center space-x-3 px-4 py-3 bg-emerald-500/10 text-emerald-500 rounded-xl font-medium transition">
              <LayoutDashboard className="w-5 h-5" />
              <span>Dashboard</span>
            </a>
            <a href="#" className="flex items-center space-x-3 px-4 py-3 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-xl font-medium transition">
              <Users className="w-5 h-5" />
              <span>Customers</span>
            </a>
            <a href="#" className="flex items-center space-x-3 px-4 py-3 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-xl font-medium transition">
              <Settings className="w-5 h-5" />
              <span>Settings</span>
            </a>
          </nav>
        </div>
        <div className="mt-auto p-6">
          <button
            onClick={logout}
            className="flex items-center space-x-3 text-neutral-500 hover:text-red-400 transition w-full px-4 py-2 font-medium"
          >
            <LogOut className="w-5 h-5" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 md:p-10 overflow-y-auto">
        <header className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-3xl font-bold text-white">Overview</h1>
            <p className="text-neutral-400 mt-1">
              Live Stripe revenue over the last {stats?.windowDays ?? 30} days.
            </p>
          </div>
          <button
            onClick={loadStats}
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium transition flex items-center space-x-2"
          >
            <span>Refresh</span>
          </button>
        </header>

        {loadError && (
          <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 px-4 py-3 text-sm">
            {loadError}
          </div>
        )}
        {stats?.error === 'stripe_unavailable' && (
          <div className="mb-6 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-300 px-4 py-3 text-sm">
            Stripe data is temporarily unavailable — showing zeros.
          </div>
        )}

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {/* Revenue Card */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
              <DollarSign className="w-24 h-24 text-emerald-500" />
            </div>
            <div className="relative z-10">
              <p className="text-sm font-medium text-neutral-400 mb-1">Total Revenue</p>
              <p className="text-4xl font-black text-white">{metrics.revenue}</p>
              <div
                className={`mt-4 flex items-center text-sm font-medium ${
                  growthPositive ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                {growthPositive ? (
                  <ArrowUpRight className="w-4 h-4 mr-1" />
                ) : (
                  <ArrowDownRight className="w-4 h-4 mr-1" />
                )}
                <span>
                  {growthPositive ? '+' : ''}
                  {growth}% vs prior {stats?.windowDays ?? 30}d
                </span>
              </div>
            </div>
          </div>

          {/* Sales Card */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
              <CreditCard className="w-24 h-24 text-emerald-500" />
            </div>
            <div className="relative z-10">
              <p className="text-sm font-medium text-neutral-400 mb-1">Total Sales</p>
              <p className="text-4xl font-black text-white">{metrics.sales}</p>
              <div className="mt-4 flex items-center text-neutral-500 text-sm font-medium">
                <span>Paid checkouts in window</span>
              </div>
            </div>
          </div>

          {/* Customers Card */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
              <Users className="w-24 h-24 text-emerald-500" />
            </div>
            <div className="relative z-10">
              <p className="text-sm font-medium text-neutral-400 mb-1">Unique Customers</p>
              <p className="text-4xl font-black text-white">{metrics.customers}</p>
              <div className="mt-4 flex items-center text-neutral-500 text-sm font-medium">
                <span>Distinct emails in window</span>
              </div>
            </div>
          </div>
        </div>

        {/* Chart Area */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl mb-10 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-600 to-emerald-400"></div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white">Daily Revenue</h2>
            <span className="text-xs text-neutral-500 flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-emerald-500" /> last {stats?.windowDays ?? 30} days
            </span>
          </div>
          <RevenueChart data={series} />
        </div>

        {/* Recent Transactions Table */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl shadow-xl overflow-hidden">
          <div className="p-6 border-b border-neutral-800 flex justify-between items-center">
            <h2 className="text-xl font-bold text-white">Recent Transactions</h2>
            <span className="text-sm text-neutral-500 font-medium">
              {recentTransactions.length} shown
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-neutral-950/50 text-neutral-400 text-sm uppercase tracking-wider">
                  <th className="p-4 font-semibold">Date</th>
                  <th className="p-4 font-semibold">Customer</th>
                  <th className="p-4 font-semibold">Amount</th>
                  <th className="p-4 font-semibold">Method</th>
                  <th className="p-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800">
                {recentTransactions.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-neutral-500 text-sm">
                      No paid transactions yet.
                    </td>
                  </tr>
                ) : (
                  recentTransactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-neutral-800/50 transition">
                      <td className="p-4 text-sm text-neutral-400">
                        {new Date(tx.date).toLocaleDateString()}
                      </td>
                      <td className="p-4 text-sm text-white">{tx.email ?? '—'}</td>
                      <td className="p-4 text-sm font-bold text-emerald-400">{usd(tx.amount)}</td>
                      <td className="p-4 text-sm text-neutral-300 capitalize">{tx.paymentMethod}</td>
                      <td className="p-4 text-sm">
                        <span className="bg-emerald-500/10 text-emerald-400 px-2.5 py-1 rounded-full text-xs font-semibold border border-emerald-500/20 capitalize">
                          {tx.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

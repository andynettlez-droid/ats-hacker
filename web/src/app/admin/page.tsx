import React from 'react';
import { DollarSign, CreditCard, Activity, ArrowUpRight, Users, LayoutDashboard, Settings, LogOut } from 'lucide-react';

export default function AdminDashboard() {
  // Dummy Data for the UI Implementation Agent
  const metrics = {
    revenue: "$1,250.00",
    sales: 250,
    conversion: "4.2%"
  };

  const recentTransactions = [
    { id: "tx_12345", email: "user1@example.com", amount: "$5.00", date: "2026-06-24", status: "Success" },
    { id: "tx_12346", email: "user2@example.com", amount: "$5.00", date: "2026-06-24", status: "Success" },
    { id: "tx_12347", email: "user3@example.com", amount: "$5.00", date: "2026-06-23", status: "Success" },
    { id: "tx_12348", email: "user4@example.com", amount: "$5.00", date: "2026-06-23", status: "Success" },
  ];

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
          <button className="flex items-center space-x-3 text-neutral-500 hover:text-red-400 transition w-full px-4 py-2 font-medium">
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
            <p className="text-neutral-400 mt-1">Track your traffic and revenue in real-time.</p>
          </div>
          <button className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium transition flex items-center space-x-2">
            <span>Export Data</span>
          </button>
        </header>

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
              <div className="mt-4 flex items-center text-emerald-400 text-sm font-medium">
                <ArrowUpRight className="w-4 h-4 mr-1" />
                <span>+12.5% this week</span>
              </div>
            </div>
          </div>

          {/* Sales Card */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
              <CreditCard className="w-24 h-24 text-emerald-500" />
            </div>
            <div className="relative z-10">
              <p className="text-sm font-medium text-neutral-400 mb-1">Total Checkouts</p>
              <p className="text-4xl font-black text-white">{metrics.sales}</p>
              <div className="mt-4 flex items-center text-emerald-400 text-sm font-medium">
                <ArrowUpRight className="w-4 h-4 mr-1" />
                <span>+8.2% this week</span>
              </div>
            </div>
          </div>

          {/* Conversion Card */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
              <Activity className="w-24 h-24 text-emerald-500" />
            </div>
            <div className="relative z-10">
              <p className="text-sm font-medium text-neutral-400 mb-1">Conversion Rate</p>
              <p className="text-4xl font-black text-white">{metrics.conversion}</p>
              <div className="mt-4 flex items-center text-neutral-500 text-sm font-medium">
                <span>Avg. session duration: 2m 14s</span>
              </div>
            </div>
          </div>
        </div>

        {/* Chart Area Mockup */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl mb-10 h-80 flex flex-col justify-center items-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-600 to-emerald-400"></div>
          <Activity className="w-12 h-12 text-emerald-500/20 mb-4" />
          <p className="text-neutral-500 font-medium">[ Line Chart Implementation Placeholder ]</p>
          <p className="text-xs text-neutral-600 mt-2">Agent: Integrate Recharts or Chart.js here with live Stripe data</p>
        </div>

        {/* Recent Transactions Table */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl shadow-xl overflow-hidden">
          <div className="p-6 border-b border-neutral-800 flex justify-between items-center">
            <h2 className="text-xl font-bold text-white">Recent Transactions</h2>
            <a href="#" className="text-sm text-emerald-500 hover:text-emerald-400 font-medium transition">View all</a>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-neutral-950/50 text-neutral-400 text-sm uppercase tracking-wider">
                  <th className="p-4 font-semibold">Transaction ID</th>
                  <th className="p-4 font-semibold">Customer</th>
                  <th className="p-4 font-semibold">Date</th>
                  <th className="p-4 font-semibold">Amount</th>
                  <th className="p-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800">
                {recentTransactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-neutral-800/50 transition">
                    <td className="p-4 text-sm font-mono text-neutral-300">{tx.id}</td>
                    <td className="p-4 text-sm text-white">{tx.email}</td>
                    <td className="p-4 text-sm text-neutral-400">{tx.date}</td>
                    <td className="p-4 text-sm font-bold text-emerald-400">{tx.amount}</td>
                    <td className="p-4 text-sm">
                      <span className="bg-emerald-500/10 text-emerald-400 px-2.5 py-1 rounded-full text-xs font-semibold border border-emerald-500/20">
                        {tx.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </main>
    </div>
  );
}

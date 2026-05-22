'use client';

import React, { useEffect, useState } from 'react';
import { 
  FileText, 
  Clock, 
  CheckCircle2, 
  FileCheck2, 
  Cpu, 
  ArrowRight,
  TrendingUp
} from 'lucide-react';
import Link from 'next/link';
import { useStore } from '@/store/useStore';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';

const COLORS = ['#94a3b8', '#eab308', '#0a6ed1', '#ef4444', '#a855f7']; // Draft, Pending, Approved, Rejected, Hold

export default function DashboardPage() {
  const { 
    dashboardStats, 
    fetchStats, 
    pos, 
    fetchPos 
  } = useStore();
  
  const [isMounted, setIsMounted] = useState(false);
  const [chartData, setChartData] = useState<{
    status_distribution: any[];
    monthly_invoices: any[];
    vendor_analysis: any[];
  } | null>(null);

  useEffect(() => {
    setIsMounted(true);
    fetchStats();
    fetchPos({ limit: 5 });
    
    // Fetch chart data from backend
    fetch('http://localhost:8000/api/dashboard/charts')
      .then(res => res.json())
      .then(data => setChartData(data))
      .catch(err => console.error('Failed to load charts:', err));
  }, [fetchStats, fetchPos]);

  if (!isMounted) return null;

  const cards = [
    {
      title: 'Total Purchase Orders',
      value: dashboardStats?.total_pos ?? 0,
      icon: FileText,
      color: 'text-blue-600 bg-blue-100 dark:bg-blue-950/30 dark:text-blue-400',
    },
    {
      title: 'Pending Verification',
      value: dashboardStats?.pending_pos ?? 0,
      icon: Clock,
      color: 'text-amber-600 bg-amber-100 dark:bg-amber-950/30 dark:text-amber-400',
    },
    {
      title: 'Approved POs',
      value: dashboardStats?.approved_pos ?? 0,
      icon: CheckCircle2,
      color: 'text-emerald-600 bg-emerald-100 dark:bg-emerald-950/30 dark:text-emerald-400',
    },
    {
      title: 'Linked Invoices',
      value: dashboardStats?.invoice_count ?? 0,
      icon: FileCheck2,
      color: 'text-indigo-600 bg-indigo-100 dark:bg-indigo-950/30 dark:text-indigo-400',
    },
    {
      title: 'Automation Success',
      value: dashboardStats?.automation_runs ? `${dashboardStats.automation_success_rate}%` : '0%',
      subText: `${dashboardStats?.automation_runs ?? 0} total runs`,
      icon: Cpu,
      color: 'text-purple-600 bg-purple-100 dark:bg-purple-950/30 dark:text-purple-400',
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">SAP ERP Dashboard</h1>
          <p className="text-muted-foreground mt-1">Real-time status overview of purchase order flows & robotic tasks.</p>
        </div>
        
        <Link 
          href="/automation"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground font-semibold rounded-lg shadow hover:bg-primary/95 transition-all text-sm"
        >
          <Cpu className="h-4 w-4" />
          <span>Monitor Automation</span>
        </Link>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div 
              key={idx} 
              className="bg-card border border-border rounded-xl p-5 flex flex-col justify-between shadow-sm hover:shadow-md hover:scale-[1.01] transition-all duration-200"
            >
              <div className="flex justify-between items-start">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                  {card.title}
                </span>
                <div className={`p-2 rounded-lg ${card.color}`}>
                  <Icon className="h-4 w-4" />
                </div>
              </div>
              
              <div className="mt-4">
                <h3 className="text-2xl font-bold text-foreground leading-none">
                  {card.value}
                </h3>
                {card.subText && (
                  <span className="text-xs text-muted-foreground mt-1.5 block font-medium">
                    {card.subText}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Status Pie Chart */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
          <h3 className="font-bold text-foreground text-sm tracking-wide uppercase mb-6 flex items-center gap-2">
            <Clock className="h-4 w-4 text-primary" />
            PO Status Distribution
          </h3>
          
          <div className="h-64">
            {chartData?.status_distribution ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData.status_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {chartData.status_distribution.map((entry, index) => {
                      const colorIndex = ['Draft', 'Pending', 'Approved', 'Rejected', 'Hold'].indexOf(entry.name);
                      return <Cell key={`cell-${index}`} fill={COLORS[colorIndex !== -1 ? colorIndex : 0]} />;
                    })}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'var(--card)', 
                      borderColor: 'var(--border)',
                      color: 'var(--foreground)'
                    }} 
                  />
                  <Legend verticalAlign="bottom" height={36} iconSize={10} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
                Loading status chart...
              </div>
            )}
          </div>
        </div>

        {/* Monthly Invoices */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
          <h3 className="font-bold text-foreground text-sm tracking-wide uppercase mb-6 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            Monthly Invoice volume
          </h3>
          
          <div className="h-64">
            {chartData?.monthly_invoices ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData.monthly_invoices}>
                  <XAxis dataKey="month" stroke="var(--muted-foreground)" fontSize={11} tickLine={false} />
                  <YAxis stroke="var(--muted-foreground)" fontSize={11} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'var(--card)', 
                      borderColor: 'var(--border)',
                      color: 'var(--foreground)'
                    }}
                  />
                  <Bar dataKey="amount" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
                Loading volume chart...
              </div>
            )}
          </div>
        </div>

        {/* Vendor Breakdown */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
          <h3 className="font-bold text-foreground text-sm tracking-wide uppercase mb-6 flex items-center gap-2">
            <FileText className="h-4 w-4 text-primary" />
            Vendor Volume Breakdown
          </h3>
          
          <div className="h-64">
            {chartData?.vendor_analysis ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData.vendor_analysis} layout="vertical">
                  <XAxis type="number" stroke="var(--muted-foreground)" fontSize={11} tickLine={false} />
                  <YAxis dataKey="vendor" type="category" stroke="var(--muted-foreground)" fontSize={10} width={75} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'var(--card)', 
                      borderColor: 'var(--border)',
                      color: 'var(--foreground)'
                    }}
                  />
                  <Bar dataKey="amount" fill="#38bdf8" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
                Loading vendor chart...
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Recent Purchase Orders Table */}
      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-border flex items-center justify-between">
          <h3 className="font-bold text-foreground text-sm tracking-wide uppercase">
            Recent Purchase Orders
          </h3>
          <Link 
            href="/pos" 
            className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
          >
            <span>View All Orders</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900/40 text-xs font-semibold text-muted-foreground uppercase border-b border-border">
              <tr>
                <th className="px-6 py-3.5">PO Number</th>
                <th className="px-6 py-3.5">Vendor</th>
                <th className="px-6 py-3.5">Invoice Ref</th>
                <th className="px-6 py-3.5 text-right">Amount</th>
                <th className="px-6 py-3.5 text-center">Status</th>
                <th className="px-6 py-3.5 text-center">Date</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {pos.slice(0, 5).map((po) => {
                const statusColors: any = {
                  Draft: 'bg-slate-100 text-slate-700 dark:bg-slate-900/50 dark:text-slate-400',
                  Pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950/20 dark:text-yellow-400',
                  Approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400',
                  Rejected: 'bg-rose-100 text-rose-800 dark:bg-rose-950/20 dark:text-rose-400',
                  Hold: 'bg-purple-100 text-purple-800 dark:bg-purple-950/20 dark:text-purple-400',
                };
                
                return (
                  <tr key={po.po_number} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/10 transition-colors">
                    <td className="px-6 py-4 font-bold text-foreground">{po.po_number}</td>
                    <td className="px-6 py-4 text-muted-foreground font-medium">{po.vendor_name}</td>
                    <td className="px-6 py-4 font-mono text-xs">{po.invoice_number || '-'}</td>
                    <td className="px-6 py-4 text-right font-semibold text-foreground">
                      {po.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {po.currency}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-flex px-2 py-1 rounded-md text-[11px] font-bold ${statusColors[po.status] || 'bg-slate-100'}`}>
                        {po.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center text-xs text-muted-foreground">{po.created_date}</td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/pos/${po.po_number}`}
                        id={`btn-view-details-${po.po_number}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-secondary text-secondary-foreground font-semibold rounded hover:bg-primary hover:text-primary-foreground transition-all text-xs"
                      >
                        <span>Details</span>
                      </Link>
                    </td>
                  </tr>
                );
              })}
              {pos.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-muted-foreground text-sm">
                    No purchase orders found. Seeding required.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

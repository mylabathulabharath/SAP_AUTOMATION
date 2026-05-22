'use client';

import React, { useEffect } from 'react';
import { FileBarChart2, FileDown, ShieldAlert, CheckCircle, Cpu, Calendar } from 'lucide-react';
import { useStore } from '@/store/useStore';

export default function ReportsPage() {
  const { reports, fetchReports } = useStore();

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  // Calculations
  const totalRuns = reports.length;
  const successRuns = reports.filter(r => r.status === 'Success').length;
  const failureRuns = totalRuns - successRuns;
  const successRate = totalRuns > 0 ? Math.round((successRuns / totalRuns) * 100) : 0;
  
  const avgDuration = totalRuns > 0 
    ? (reports.reduce((acc, curr) => acc + (curr.duration_seconds || 0), 0) / totalRuns).toFixed(1)
    : '0.0';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Audit Reports & History</h1>
          <p className="text-muted-foreground mt-1">Review validation histories, compliance runs, and performance reports.</p>
        </div>

        <a
          href="http://localhost:8001/api/download-output"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground font-semibold rounded-lg shadow hover:bg-primary/95 transition-all text-xs border border-transparent"
        >
          <FileDown className="h-4 w-4" />
          <span>Export All Screenshots (.ZIP)</span>
        </a>
      </div>

      {/* Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Total Audited POs</span>
          <h3 className="text-2xl font-bold text-foreground mt-3">{totalRuns}</h3>
          <p className="text-[10px] text-muted-foreground mt-1.5">Processed by Playwright engine</p>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Compliance Rate</span>
          <h3 className="text-2xl font-bold text-emerald-600 mt-3">{successRate}%</h3>
          <p className="text-[10px] text-muted-foreground mt-1.5">Matches verification parameters</p>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Avg Process Speed</span>
          <h3 className="text-2xl font-bold text-primary mt-3">{avgDuration}s</h3>
          <p className="text-[10px] text-muted-foreground mt-1.5">Per purchase order record</p>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Failed Match Logs</span>
          <h3 className="text-2xl font-bold text-rose-600 mt-3">{failureRuns}</h3>
          <p className="text-[10px] text-muted-foreground mt-1.5">Require manual administrative review</p>
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h3 className="font-bold text-foreground text-sm tracking-wide uppercase flex items-center gap-2">
            <FileBarChart2 className="h-4.5 w-4.5 text-primary" />
            Compliance Run Logs
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900/40 text-xs font-semibold text-muted-foreground uppercase border-b border-border">
              <tr>
                <th className="px-6 py-3.5">PO Number</th>
                <th className="px-6 py-3.5">Supplier Name</th>
                <th className="px-6 py-3.5">Linked Invoice</th>
                <th className="px-6 py-3.5 text-center">Status</th>
                <th className="px-6 py-3.5 text-center">Duration</th>
                <th className="px-6 py-3.5 text-center">Timestamp</th>
                <th className="px-6 py-3.5">Audit Detail</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {reports.map((report, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/10 transition-colors">
                  <td className="px-6 py-4 font-bold text-foreground">{report.po_number}</td>
                  <td className="px-6 py-4 text-muted-foreground font-medium">{report.vendor_name}</td>
                  <td className="px-6 py-4 font-mono text-xs">{report.invoice_number}</td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-flex px-2 py-0.5 rounded-md text-[10px] font-bold items-center gap-1 ${
                      report.status === 'Success' 
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400' 
                        : 'bg-rose-100 text-rose-800 dark:bg-rose-950/20 dark:text-rose-400'
                    }`}>
                      {report.status === 'Success' ? <CheckCircle className="h-2.5 w-2.5" /> : <ShieldAlert className="h-2.5 w-2.5" />}
                      <span>{report.status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center font-semibold">{report.duration_seconds}s</td>
                  <td className="px-6 py-4 text-center text-xs text-muted-foreground">
                    <span className="flex items-center justify-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>{report.timestamp}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 text-xs text-muted-foreground max-w-xs truncate">
                    {report.error ? (
                      <span className="text-rose-500 font-semibold">{report.error}</span>
                    ) : (
                      <span>Match verified. Invoice Approved in SAP system.</span>
                    )}
                  </td>
                </tr>
              ))}
              {reports.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-muted-foreground text-sm">
                    No run compliance reports available. Launch a robot session in the Automation workspace.
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

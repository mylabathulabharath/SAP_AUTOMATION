'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Square, 
  UploadCloud, 
  Download, 
  Terminal, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  TrendingUp,
  Image as ImageIcon,
  Loader2
} from 'lucide-react';
import { useStore } from '@/store/useStore';

export default function AutomationMonitorPage() {
  const { 
    automationStatus, 
    logs, 
    reports,
    uploadExcel, 
    startAutomation, 
    fetchAutomationStatus, 
    fetchLogs,
    fetchReports
  } = useStore();

  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<{ status: string; message: string }>({ status: 'idle', message: '' });
  
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<any>(null);

  // Poll status & logs during execution
  useEffect(() => {
    fetchAutomationStatus();
    fetchLogs();
    fetchReports();

    timerRef.current = setInterval(() => {
      fetchAutomationStatus();
      fetchLogs();
      fetchReports();
    }, 1200);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetchAutomationStatus, fetchLogs, fetchReports]);

  // Scroll to bottom of terminal when logs change
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      await handleUpload(droppedFile);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      await handleUpload(selectedFile);
    }
  };

  const handleUpload = async (fileToUpload: File) => {
    setUploadState({ status: 'loading', message: 'Parsing Excel spreadsheet...' });
    try {
      const data = await uploadExcel(fileToUpload);
      setUploadState({ 
        status: 'success', 
        message: `Successfully uploaded "${data.filename}" containing ${data.rows_count} PO records.` 
      });
      fetchAutomationStatus();
    } catch (err: any) {
      setUploadState({ status: 'error', message: err.message || 'File upload failed.' });
    }
  };

  const handleStart = async () => {
    const ok = await startAutomation();
    if (ok) {
      setUploadState({ status: 'idle', message: '' });
    }
  };

  // Status and calculations
  const isRunning = automationStatus?.status === 'running';
  const total = automationStatus?.total_count ?? 0;
  const processed = automationStatus?.processed_count ?? 0;
  const successCount = automationStatus?.success_count ?? 0;
  const failureCount = automationStatus?.failure_count ?? 0;
  const currentPo = automationStatus?.current_po ?? '';
  
  const progressPercent = total > 0 ? Math.round((processed / total) * 100) : 0;
  const successRate = processed > 0 ? Math.round((successCount / processed) * 100) : 0;

  // Screenshots preview urls
  const screenshotTargets = [
    { name: 'Dashboard Screen', file: 'dashboard.png' },
    { name: 'PO Search Table', file: 'search-results.png' },
    { name: 'PO Details Card', file: 'po-details.png' },
    { name: 'Invoice Tab', file: 'invoice-tab.png' },
    { name: 'Approval Section', file: 'approval-section.png' }
  ];

  return (
    <div className="space-y-6 animate-fade-in pb-16">
      
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">RPA Automation Studio</h1>
          <p className="text-muted-foreground mt-1">
            Run, monitor, and audit background Playwright robot sessions processing purchase orders.
          </p>
        </div>
        
        {/* Sample Downloader */}
        <a 
          href="/sample-data/sample_po_list.xlsx"
          download="sample_po_list.xlsx"
          className="inline-flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground font-semibold rounded-lg hover:bg-secondary/90 transition-all text-xs border border-border shadow-sm"
        >
          <Download className="h-3.5 w-3.5" />
          <span>Download Sample PO List</span>
        </a>
      </div>

      {/* Main Grid: Controls Left, Terminal Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* 1. Control & Upload Card */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-6 lg:col-span-1">
          
          <div className="border-b border-border pb-4">
            <h3 className="font-bold text-foreground text-sm uppercase tracking-wide">
              Robot Orchestrator
            </h3>
          </div>

          {/* Upload Box */}
          <div className="space-y-3">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
              1. Load Target Records (Excel)
            </span>
            
            <div 
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-200 ${
                dragActive 
                  ? 'border-primary bg-primary/5' 
                  : 'border-border hover:border-primary/50 bg-secondary/10'
              }`}
            >
              <UploadCloud className="h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-xs font-bold text-foreground">Drag & drop excel spreadsheet here</p>
              <p className="text-[10px] text-muted-foreground mt-1">Supports .xlsx or .xls</p>
              
              <label className="mt-3 px-3 py-1.5 bg-primary/10 text-primary hover:bg-primary/20 font-semibold text-xs rounded transition-colors cursor-pointer">
                <span>Browse File</span>
                <input 
                  type="file" 
                  className="hidden" 
                  accept=".xlsx, .xls"
                  onChange={handleFileChange}
                />
              </label>
            </div>

            {/* File info / upload message */}
            {uploadState.message && (
              <div className={`p-3 rounded-lg border flex gap-2 text-xs font-medium leading-relaxed ${
                uploadState.status === 'success'
                  ? 'bg-emerald-50 dark:bg-emerald-950/15 border-emerald-200 dark:border-emerald-900/30 text-emerald-800 dark:text-emerald-400'
                  : uploadState.status === 'error'
                  ? 'bg-destructive/10 border-destructive/20 text-destructive'
                  : 'bg-secondary/40 border-border text-muted-foreground'
              }`}>
                {uploadState.status === 'loading' && <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0 text-primary" />}
                {uploadState.status === 'success' && <CheckCircle className="h-3.5 w-3.5 shrink-0 text-emerald-600" />}
                {uploadState.status === 'error' && <AlertCircle className="h-3.5 w-3.5 shrink-0" />}
                <span>{uploadState.message}</span>
              </div>
            )}
          </div>

          {/* Trigger controls */}
          <div className="space-y-3 pt-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
              2. Launch Executable Action
            </span>

            {isRunning ? (
              <button
                type="button"
                disabled
                className="w-full py-3 bg-secondary text-muted-foreground font-bold rounded-lg border border-border flex items-center justify-center gap-2 text-sm opacity-70"
              >
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span>Running Playwright Sessions...</span>
              </button>
            ) : (
              <button
                type="button"
                id="btn-start-automation"
                onClick={handleStart}
                className="w-full py-3 bg-primary text-primary-foreground font-bold rounded-lg shadow-md hover:bg-primary/95 transition-all flex items-center justify-center gap-2 text-sm cursor-pointer"
              >
                <Play className="h-4 w-4 fill-primary-foreground" />
                <span>Start Playwright Automation</span>
              </button>
            )}
          </div>

          {/* Progress / Status metrics */}
          <div className="space-y-4 pt-4 border-t border-border/60">
            <div>
              <div className="flex justify-between items-center text-xs font-semibold mb-1">
                <span className="text-muted-foreground">Session Status:</span>
                <span className={`uppercase font-bold ${
                  isRunning 
                    ? 'text-yellow-500 animate-pulse' 
                    : automationStatus?.status === 'completed'
                    ? 'text-emerald-500'
                    : 'text-muted-foreground'
                }`}>
                  {automationStatus?.status || 'Idle'}
                </span>
              </div>

              {isRunning && (
                <div className="flex justify-between items-center text-xs font-semibold mt-1">
                  <span className="text-muted-foreground">Processing Record:</span>
                  <span className="text-primary font-mono font-bold animate-pulse">{currentPo}</span>
                </div>
              )}
            </div>

            {/* Progress Bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-muted-foreground">Queue Progress ({processed}/{total})</span>
                <span className="text-foreground">{progressPercent}%</span>
              </div>
              <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary rounded-full transition-all duration-500" 
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>

            {/* Counters */}
            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="bg-slate-50 dark:bg-slate-900/40 p-3 rounded-lg border border-border text-center">
                <span className="text-[10px] text-muted-foreground font-semibold uppercase block">Success</span>
                <p className="text-lg font-bold text-emerald-600 mt-0.5">{successCount}</p>
              </div>
              <div className="bg-slate-50 dark:bg-slate-900/40 p-3 rounded-lg border border-border text-center">
                <span className="text-[10px] text-muted-foreground font-semibold uppercase block">Failed</span>
                <p className="text-lg font-bold text-rose-600 mt-0.5">{failureCount}</p>
              </div>
            </div>
          </div>

        </div>

        {/* 2. Terminal Console Logs */}
        <div className="bg-slate-950 text-slate-100 rounded-xl border border-slate-800 shadow-xl overflow-hidden lg:col-span-2 flex flex-col h-[480px] lg:h-auto">
          <div className="bg-slate-900 px-5 py-3.5 border-b border-slate-800 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <Terminal className="h-4.5 w-4.5 text-emerald-400" />
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-300">
                Robot Stdout Terminal Stream
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className={`h-2.5 w-2.5 rounded-full ${isRunning ? 'bg-yellow-500 animate-ping' : 'bg-slate-700'}`} />
              <span className="text-[10px] font-mono text-slate-400 font-bold uppercase">
                {isRunning ? 'Streaming' : 'Offline'}
              </span>
            </div>
          </div>
          
          <div className="flex-1 p-5 overflow-y-auto font-mono text-xs space-y-1.5 terminal-glow bg-slate-950/90 text-emerald-400 selection:bg-emerald-800 selection:text-white">
            {logs.split('\n').map((line, idx) => {
              let textColors = 'text-emerald-400';
              if (line.includes('[ERROR]')) textColors = 'text-rose-400 font-bold';
              else if (line.includes('[SUCCESS]')) textColors = 'text-emerald-300 font-bold';
              else if (line.includes('[WARNING]')) textColors = 'text-yellow-400';
              
              return (
                <div key={idx} className={textColors}>
                  {line}
                </div>
              );
            })}
            <div ref={terminalEndRef} />
          </div>
        </div>

      </div>

      {/* 3. Live Screenshots Grid */}
      {isRunning && currentPo && currentPo !== 'Initializing...' && (
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4 animate-fade-in">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <ImageIcon className="h-4.5 w-4.5 text-primary" />
            <h3 className="font-bold text-foreground text-sm uppercase tracking-wide">
              Live Browser View: PO {currentPo}
            </h3>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
            {screenshotTargets.map((target) => {
              // Construct static image URL served from port 8001
              // Append a timestamp hash to bypass browser image cache reload!
              const imgUrl = `http://localhost:8001/outputs/${currentPo}/${target.file}?t=${Date.now()}`;
              return (
                <div key={target.name} className="border border-border rounded-lg overflow-hidden bg-secondary/10 flex flex-col group hover:shadow transition-all">
                  <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
                    <img 
                      src={imgUrl} 
                      alt={target.name}
                      onError={(e) => {
                        // If file is not yet generated, display a loading card
                        (e.target as HTMLElement).style.display = 'none';
                        const parent = (e.target as HTMLElement).parentElement;
                        if (parent) {
                          const placeholder = parent.querySelector('.img-placeholder');
                          if (placeholder) placeholder.classList.remove('hidden');
                        }
                      }}
                      onLoad={(e) => {
                        (e.target as HTMLElement).style.display = 'block';
                        const parent = (e.target as HTMLElement).parentElement;
                        if (parent) {
                          const placeholder = parent.querySelector('.img-placeholder');
                          if (placeholder) placeholder.classList.add('hidden');
                        }
                      }}
                      className="object-contain w-full h-full"
                    />
                    
                    {/* Placeholder */}
                    <div className="img-placeholder w-full h-full flex flex-col items-center justify-center p-3 text-center text-[10px] text-muted-foreground animate-pulse">
                      <Clock className="h-5 w-5 mb-1" />
                      <span>Awaiting generation...</span>
                    </div>
                  </div>
                  <div className="p-2 border-t border-border bg-slate-50 dark:bg-slate-900/20 text-center shrink-0">
                    <span className="text-[10px] font-bold text-foreground">{target.name}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Complete Audit Reports List */}
      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h3 className="font-bold text-foreground text-sm tracking-wide uppercase">
            Automation Audit Reports
          </h3>
          
          <a 
            href="http://localhost:8001/api/download-output"
            className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
          >
            <span>Download All Screenshots (.ZIP)</span>
          </a>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900/40 text-xs font-semibold text-muted-foreground uppercase border-b border-border">
              <tr>
                <th className="px-6 py-3.5">PO Number</th>
                <th className="px-6 py-3.5">Vendor</th>
                <th className="px-6 py-3.5">Invoice</th>
                <th className="px-6 py-3.5 text-center">Status</th>
                <th className="px-6 py-3.5 text-center">Execution Time</th>
                <th className="px-6 py-3.5 text-center">Finished At</th>
                <th className="px-6 py-3.5">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {reports.map((report, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/10 transition-colors">
                  <td className="px-6 py-4 font-bold text-foreground">{report.po_number}</td>
                  <td className="px-6 py-4 text-muted-foreground font-medium">{report.vendor_name}</td>
                  <td className="px-6 py-4 font-mono text-xs">{report.invoice_number}</td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-flex px-2 py-0.5 rounded-md text-[10px] font-bold ${
                      report.status === 'Success' 
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400' 
                        : 'bg-rose-100 text-rose-800 dark:bg-rose-950/20 dark:text-rose-400'
                    }`}>
                      {report.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center font-semibold">{report.duration_seconds}s</td>
                  <td className="px-6 py-4 text-center text-xs text-muted-foreground">{report.timestamp}</td>
                  <td className="px-6 py-4 text-xs text-muted-foreground max-w-xs truncate">
                    {report.error ? (
                      <span className="text-rose-500 font-semibold">{report.error}</span>
                    ) : (
                      <span>Completed without exceptions.</span>
                    )}
                  </td>
                </tr>
              ))}
              {reports.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-muted-foreground text-sm">
                    No automation reports found yet. Run an automation cycle.
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

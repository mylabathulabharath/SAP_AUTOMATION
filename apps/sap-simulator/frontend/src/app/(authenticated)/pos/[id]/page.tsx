'use client';

import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Building, 
  FileCheck2, 
  FileText, 
  History, 
  DollarSign, 
  Check, 
  X, 
  Pause,
  AlertTriangle
} from 'lucide-react';
import { useStore } from '@/store/useStore';

export default function PODetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const po_number = resolvedParams.id;
  const router = useRouter();
  
  const { currentPo, fetchPoDetail, executePoAction } = useStore();
  
  const [activeTab, setActiveTab] = useState<'details' | 'invoice' | 'attachments' | 'logs' | 'payment'>('details');
  const [remarks, setRemarks] = useState('');
  
  // Interactive Verification Section states (targets for Playwright)
  const [verificationStatus, setVerificationStatus] = useState<'verified' | 'unverified' | ''>('');
  const [itemsChecked, setItemsChecked] = useState(false);
  const [pricesChecked, setPricesChecked] = useState(false);
  
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState('');

  useEffect(() => {
    fetchPoDetail(po_number);
  }, [po_number, fetchPoDetail]);

  if (!currentPo) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground text-sm">
        Loading Purchase Order {po_number} details...
      </div>
    );
  }

  const { header, vendor, items, invoice, attachments, audit_logs, payment_details } = currentPo;

  const handleAction = async (action: 'Approve' | 'Reject' | 'Hold') => {
    setActionLoading(true);
    setActionMessage('');
    
    // Auto-fill remarks if empty based on checkboxes
    let finalRemarks = remarks;
    if (!finalRemarks) {
      finalRemarks = `Automated action ${action}. Verification status: ${verificationStatus}. Items verified: ${itemsChecked}. Prices verified: ${pricesChecked}.`;
    }

    const success = await executePoAction(po_number, action, finalRemarks);
    setActionLoading(false);
    
    if (success) {
      setActionMessage(`PO status updated successfully to: ${action === 'Approve' ? 'Approved' : action === 'Reject' ? 'Rejected' : 'Hold'}`);
      // Show success toast or message and scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      setActionMessage('Failed to update PO status. Please try again.');
    }
  };

  const getStatusClass = (status: string) => {
    const classes: any = {
      Draft: 'bg-slate-100 text-slate-700 dark:bg-slate-900/50 dark:text-slate-400 border-slate-200 dark:border-slate-800',
      Pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950/20 dark:text-yellow-400 border-yellow-200 dark:border-yellow-900/30',
      Approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400 border-emerald-200 dark:border-emerald-900/30',
      Rejected: 'bg-rose-100 text-rose-800 dark:bg-rose-950/20 dark:text-rose-400 border-rose-200 dark:border-rose-900/30',
      Hold: 'bg-purple-100 text-purple-800 dark:bg-purple-950/20 dark:text-purple-400 border-purple-200 dark:border-purple-900/30',
    };
    return classes[status] || 'bg-slate-100 border-slate-200';
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-6xl mx-auto pb-16">
      
      {/* Back Link & Header */}
      <div className="flex items-center gap-3">
        <button 
          onClick={() => router.push('/pos')}
          className="p-2 rounded-lg bg-card border border-border text-muted-foreground hover:text-foreground transition-colors shadow-sm"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div>
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
            Verification Workspace
          </span>
          <h2 className="text-2xl font-bold text-foreground">Purchase Order: {header.po_number}</h2>
        </div>
        
        {/* Status Badge */}
        <span className={`inline-flex px-3 py-1.5 rounded-full text-xs font-bold border ml-3 ${getStatusClass(header.status)}`}>
          {header.status}
        </span>
      </div>

      {/* Action Toast Alert */}
      {actionMessage && (
        <div className={`p-4 rounded-xl border flex items-center gap-3 text-sm animate-fade-in ${
          actionMessage.includes('successfully') 
            ? 'bg-emerald-50 dark:bg-emerald-950/15 border-emerald-200 dark:border-emerald-900/30 text-emerald-800 dark:text-emerald-400'
            : 'bg-destructive/10 border-destructive/20 text-destructive'
        }`}>
          <FileCheck2 className="h-5 w-5 shrink-0" />
          <span className="font-semibold">{actionMessage}</span>
        </div>
      )}

      {/* Main Grid: Details left, Vendor card right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left pane: Details Card & Tabs */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Header Summary Card */}
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <span className="text-xs text-muted-foreground font-semibold uppercase block">Invoice Amount</span>
              <p className="text-xl font-bold text-foreground mt-1">
                {header.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })} {header.currency}
              </p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground font-semibold uppercase block">Creation Date</span>
              <p className="text-sm font-semibold text-foreground mt-1.5">{header.created_date}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground font-semibold uppercase block">Approval status</span>
              <p className="text-sm font-semibold text-foreground mt-1.5">{header.approval_status}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground font-semibold uppercase block">Vendor ID</span>
              <p className="text-sm font-semibold text-primary mt-1.5">{header.vendor_id}</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-border bg-card rounded-t-xl px-2">
            {[
              { id: 'details', label: 'Items & Verification', icon: FileText },
              { id: 'invoice', label: 'Invoice Details', icon: FileCheck2 },
              { id: 'attachments', label: 'Attachments', icon: DollarSign }, // Keep it simple
              { id: 'logs', label: 'Audit Trail', icon: History },
              { id: 'payment', label: 'Payment Terms', icon: Building }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  id={`tab-${tab.id}`}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-5 py-3.5 border-b-2 font-semibold text-sm transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab Contents */}
          <div className="bg-card border border-t-0 border-border rounded-b-xl p-6 shadow-sm min-h-[300px]">
            
            {/* 1. Items & Verification Tab */}
            {activeTab === 'details' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-bold text-foreground uppercase tracking-wider mb-3">
                    Line Item Breakdown
                  </h3>
                  <div className="overflow-x-auto border border-border rounded-lg">
                    <table className="w-full border-collapse text-left text-sm">
                      <thead className="bg-slate-50 dark:bg-slate-900/40 text-xs font-semibold text-muted-foreground uppercase border-b border-border">
                        <tr>
                          <th className="px-4 py-2.5">Item Code</th>
                          <th className="px-4 py-2.5">Description</th>
                          <th className="px-4 py-2.5 text-center">Qty</th>
                          <th className="px-4 py-2.5 text-right">Unit Price</th>
                          <th className="px-4 py-2.5 text-right">Tax %</th>
                          <th className="px-4 py-2.5 text-right">Total</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {items.map((item, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/5 transition-colors">
                            <td className="px-4 py-3 font-mono font-semibold text-foreground text-xs">{item.item_code}</td>
                            <td className="px-4 py-3 text-muted-foreground">{item.description}</td>
                            <td className="px-4 py-3 text-center">{item.quantity}</td>
                            <td className="px-4 py-3 text-right">{item.price.toFixed(2)}</td>
                            <td className="px-4 py-3 text-right">{item.tax}%</td>
                            <td className="px-4 py-3 text-right font-bold text-foreground">{item.total.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Verification Card (Targets for Playwright) */}
                <div className="border border-border rounded-xl p-5 bg-slate-50/30 dark:bg-slate-900/5 space-y-4">
                  <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    Interactive Verification Form
                  </h4>

                  {/* Radios */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-foreground block">Three-Way Matching Status:</span>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer select-none">
                        <input
                          type="radio"
                          id="radio-verify-ok"
                          name="matching"
                          checked={verificationStatus === 'verified'}
                          onChange={() => setVerificationStatus('verified')}
                          className="rounded-full border-border text-primary focus:ring-primary h-4 w-4"
                        />
                        <span className="text-foreground font-semibold">Verified Match (PO/GR/IR)</span>
                      </label>
                      <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer select-none">
                        <input
                          type="radio"
                          id="radio-verify-fail"
                          name="matching"
                          checked={verificationStatus === 'unverified'}
                          onChange={() => setVerificationStatus('unverified')}
                          className="rounded-full border-border text-primary focus:ring-primary h-4 w-4"
                        />
                        <span>Mismatch Found</span>
                      </label>
                    </div>
                  </div>

                  {/* Checkboxes */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-foreground block">Verification Checklist:</span>
                    <div className="flex gap-6">
                      <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer select-none">
                        <input
                          type="checkbox"
                          id="check-verify-items"
                          checked={itemsChecked}
                          onChange={(e) => setItemsChecked(e.target.checked)}
                          className="rounded border-border text-primary focus:ring-primary h-4 w-4"
                        />
                        <span>Verify quantities & item codes</span>
                      </label>
                      <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer select-none">
                        <input
                          type="checkbox"
                          id="check-verify-prices"
                          checked={pricesChecked}
                          onChange={(e) => setPricesChecked(e.target.checked)}
                          className="rounded border-border text-primary focus:ring-primary h-4 w-4"
                        />
                        <span>Verify unit prices & tax charges</span>
                      </label>
                    </div>
                  </div>

                  {/* Remarks */}
                  <div className="space-y-1.5">
                    <label htmlFor="textarea-remarks" className="text-xs font-semibold text-foreground block">
                      Verification Remarks
                    </label>
                    <textarea
                      id="textarea-remarks"
                      rows={3}
                      placeholder="Add system remarks, audit comments, or mismatch details..."
                      value={remarks}
                      onChange={(e) => setRemarks(e.target.value)}
                      className="w-full px-3 py-2 bg-secondary/50 border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* 2. Invoice Details Tab */}
            {activeTab === 'invoice' && (
              <div className="space-y-6">
                {invoice ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <h4 className="text-sm font-bold text-foreground uppercase tracking-wider">
                        Metadata from Extracted Invoice
                      </h4>
                      <div className="space-y-2.5 text-sm">
                        <div className="flex justify-between border-b border-border pb-1.5">
                          <span className="text-muted-foreground">Invoice Reference:</span>
                          <span className="font-bold text-foreground font-mono">{invoice.invoice_number}</span>
                        </div>
                        <div className="flex justify-between border-b border-border pb-1.5">
                          <span className="text-muted-foreground">Invoice Amount:</span>
                          <span className="font-semibold text-foreground">{invoice.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })} {invoice.currency}</span>
                        </div>
                        <div className="flex justify-between border-b border-border pb-1.5">
                          <span className="text-muted-foreground">Invoice Date:</span>
                          <span className="font-semibold text-foreground">{invoice.created_date}</span>
                        </div>
                        <div className="flex justify-between border-b border-border pb-1.5">
                          <span className="text-muted-foreground">Processing Status:</span>
                          <span className="font-bold text-primary">{invoice.status}</span>
                        </div>
                      </div>
                    </div>

                    {/* Invoice visual placeholder */}
                    <div className="border border-border rounded-xl p-5 bg-slate-50/50 dark:bg-slate-900/20 flex flex-col items-center justify-center text-center">
                      <FileCheck2 className="h-10 w-10 text-primary mb-3 animate-pulse" />
                      <p className="font-bold text-foreground text-sm">Linked Invoice Scan (PDF)</p>
                      <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">OCR text extraction completed using Ollama VLM.</p>
                      <button className="mt-4 px-3.5 py-1.5 bg-secondary text-secondary-foreground font-semibold text-xs rounded hover:bg-secondary/85 transition-colors">
                        View Original Document
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center p-8 text-center text-sm border border-dashed border-border rounded-xl">
                    <AlertTriangle className="h-8 w-8 text-yellow-500 mb-2" />
                    <p className="font-bold text-foreground">No Invoice Linked</p>
                    <p className="text-xs text-muted-foreground mt-1">This PO does not have an active invoice linked to it. Run automation to map invoice scans.</p>
                  </div>
                )}
              </div>
            )}

            {/* 3. Attachments Tab */}
            {activeTab === 'attachments' && (
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-foreground uppercase tracking-wider mb-2">
                  System Attachments
                </h3>
                <div className="space-y-2">
                  {attachments.map((file, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 border border-border rounded-lg bg-secondary/20 hover:bg-secondary/40 transition-colors">
                      <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-primary" />
                        <div>
                          <p className="text-sm font-semibold text-foreground">{file.filename}</p>
                          <p className="text-[10px] text-muted-foreground">{file.size} • {file.type}</p>
                        </div>
                      </div>
                      <button className="px-2.5 py-1 bg-secondary text-secondary-foreground hover:bg-primary hover:text-primary-foreground font-semibold text-xs rounded transition-all">
                        Download
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. Audit Trail Tab */}
            {activeTab === 'logs' && (
              <div className="space-y-6">
                <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">
                  Audit Logs & History
                </h3>
                <div className="relative border-l-2 border-border pl-6 ml-2 space-y-6">
                  {audit_logs.map((log, idx) => (
                    <div key={idx} className="relative">
                      {/* Timeline dot */}
                      <span className="absolute -left-[31px] top-1.5 h-3 w-3 rounded-full bg-primary border-2 border-card" />
                      <div className="text-xs text-muted-foreground font-semibold">{log.timestamp}</div>
                      <div className="text-sm font-bold text-foreground mt-0.5">{log.action}</div>
                      <div className="text-xs text-muted-foreground mt-0.5">Performed by: <span className="font-semibold text-foreground">{log.performed_by}</span></div>
                      <p className="text-xs text-muted-foreground mt-1 bg-secondary/35 p-2 rounded border border-border/40 max-w-xl">{log.details}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 5. Payment Terms Tab */}
            {activeTab === 'payment' && (
              <div className="space-y-4 max-w-lg">
                <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">
                  Payment Account & Terms
                </h3>
                <div className="space-y-2.5 text-sm">
                  <div className="flex justify-between border-b border-border pb-1.5">
                    <span className="text-muted-foreground">Target Bank:</span>
                    <span className="font-semibold text-foreground">{payment_details.bank_name}</span>
                  </div>
                  <div className="flex justify-between border-b border-border pb-1.5">
                    <span className="text-muted-foreground">Virtual Account:</span>
                    <span className="font-bold text-foreground font-mono">{payment_details.account_number}</span>
                  </div>
                  <div className="flex justify-between border-b border-border pb-1.5">
                    <span className="text-muted-foreground">Payment Terms:</span>
                    <span className="font-semibold text-foreground">{payment_details.payment_terms}</span>
                  </div>
                  <div className="flex justify-between border-b border-border pb-1.5">
                    <span className="text-muted-foreground">Currency:</span>
                    <span className="font-semibold text-foreground">{payment_details.currency}</span>
                  </div>
                  <div className="flex justify-between border-b border-border pb-1.5">
                    <span className="text-muted-foreground">Calculated Due Date:</span>
                    <span className="font-bold text-primary">{payment_details.due_date}</span>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>

        {/* Right pane: Vendor Info Card & Approval Block */}
        <div className="space-y-6">
          
          {/* Vendor Details Card */}
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center gap-2 border-b border-border pb-3">
              <Building className="h-5 w-5 text-primary" />
              <h3 className="font-bold text-foreground text-sm uppercase tracking-wide">
                Vendor Information
              </h3>
            </div>
            
            <div className="space-y-3.5 text-sm">
              <div>
                <span className="text-[10px] text-muted-foreground font-semibold uppercase block">Company Name</span>
                <p className="font-bold text-foreground mt-0.5">{vendor.name}</p>
              </div>
              <div>
                <span className="text-[10px] text-muted-foreground font-semibold uppercase block">Tax ID / GST Number</span>
                <p className="font-semibold text-foreground mt-0.5">{vendor.gst_number}</p>
              </div>
              <div>
                <span className="text-[10px] text-muted-foreground font-semibold uppercase block">Address</span>
                <p className="text-muted-foreground text-xs leading-relaxed mt-0.5">{vendor.address}</p>
              </div>
              <div>
                <span className="text-[10px] text-muted-foreground font-semibold uppercase block">Contact Email</span>
                <p className="text-primary font-semibold text-xs mt-0.5">{vendor.email}</p>
              </div>
              <div>
                <span className="text-[10px] text-muted-foreground font-semibold uppercase block">Phone</span>
                <p className="text-foreground font-medium text-xs mt-0.5">{vendor.phone}</p>
              </div>
              <div>
                <span className="text-[10px] text-muted-foreground font-semibold uppercase block">Contract Terms</span>
                <p className="text-foreground font-semibold text-xs mt-0.5 bg-secondary px-2 py-1 rounded inline-block">
                  {vendor.payment_terms}
                </p>
              </div>
            </div>
          </div>

          {/* Action Approval Card (Targets for Playwright) */}
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-foreground text-sm uppercase tracking-wide border-b border-border pb-3">
              Workflow Status Actions
            </h3>
            
            <div className="space-y-3">
              <p className="text-xs text-muted-foreground leading-relaxed">
                Approve, reject, or put this purchase order on hold. Taking action will notify the vendor and release payments.
              </p>

              {/* Approve Button */}
              <button
                type="button"
                id="btn-approved"
                disabled={actionLoading}
                onClick={() => handleAction('Approve')}
                className="w-full py-2.5 bg-emerald-600 text-white font-bold rounded-lg shadow hover:bg-emerald-700 disabled:opacity-50 transition-all flex items-center justify-center gap-2 text-sm cursor-pointer"
              >
                <Check className="h-4 w-4" />
                <span>Approve Order</span>
              </button>

              {/* Reject Button */}
              <button
                type="button"
                id="btn-rejected"
                disabled={actionLoading}
                onClick={() => handleAction('Reject')}
                className="w-full py-2.5 bg-rose-600 text-white font-bold rounded-lg shadow hover:bg-rose-700 disabled:opacity-50 transition-all flex items-center justify-center gap-2 text-sm cursor-pointer"
              >
                <X className="h-4 w-4" />
                <span>Reject Order</span>
              </button>

              {/* Hold Button */}
              <button
                type="button"
                id="btn-hold"
                disabled={actionLoading}
                onClick={() => handleAction('Hold')}
                className="w-full py-2.5 bg-purple-600 text-white font-bold rounded-lg shadow hover:bg-purple-700 disabled:opacity-50 transition-all flex items-center justify-center gap-2 text-sm cursor-pointer"
              >
                <Pause className="h-4 w-4" />
                <span>Place On Hold</span>
              </button>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}

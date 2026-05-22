'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Search, RotateCcw, Eye, FileText, Filter } from 'lucide-react';
import { useStore } from '@/store/useStore';
import Link from 'next/link';

export default function POSearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialStatus = searchParams.get('status') || 'All';

  const { pos, totalPosCount, fetchPos } = useStore();
  const [poNumberFilter, setPoNumberFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState(initialStatus);
  const [vendorFilter, setVendorFilter] = useState('');
  const [vendorsList, setVendorsList] = useState<any[]>([]);
  const [sortBy, setSortBy] = useState('po_number');
  
  // Extra elements for Playwright targets
  const [activeOnly, setActiveOnly] = useState(false);
  const [highValueOnly, setHighValueOnly] = useState(false);

  // Sync status filter if query params change
  useEffect(() => {
    setStatusFilter(initialStatus);
  }, [initialStatus]);

  useEffect(() => {
    // Load vendors list for dropdown
    fetch('http://localhost:8000/api/vendors')
      .then(res => res.json())
      .then(data => setVendorsList(data))
      .catch(err => console.error(err));
  }, []);

  // Fetch POs on filter change
  useEffect(() => {
    fetchPos({
      po_number: poNumberFilter,
      vendor_id: vendorFilter,
      status: statusFilter,
    });
  }, [statusFilter, fetchPos]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPos({
      po_number: poNumberFilter,
      vendor_id: vendorFilter,
      status: statusFilter,
    });
  };

  const handleReset = () => {
    setPoNumberFilter('');
    setStatusFilter('All');
    setVendorFilter('');
    setActiveOnly(false);
    setHighValueOnly(false);
    
    // Clear URL query params
    router.push('/pos');
    
    fetchPos({
      po_number: '',
      vendor_id: '',
      status: 'All',
    });
  };

  const getStatusBadge = (status: string) => {
    const badges: any = {
      Draft: 'bg-slate-100 text-slate-700 dark:bg-slate-900/50 dark:text-slate-400',
      Pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950/20 dark:text-yellow-400',
      Approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400',
      Rejected: 'bg-rose-100 text-rose-800 dark:bg-rose-950/20 dark:text-rose-400',
      Hold: 'bg-purple-100 text-purple-800 dark:bg-purple-950/20 dark:text-purple-400',
    };
    return (
      <span className={`inline-flex px-2 py-1 rounded-md text-[11px] font-bold ${badges[status] || 'bg-slate-100'}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Purchase Order Workspace</h1>
        <p className="text-muted-foreground mt-1">Search, verify, and action enterprise purchase orders and invoices.</p>
      </div>

      {/* Filter Card */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
        <form onSubmit={handleSearch} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* PO Number Search */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                PO Number
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  id="search-po-input"
                  placeholder="e.g. 45000012"
                  value={poNumberFilter}
                  onChange={(e) => setPoNumberFilter(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-secondary/50 border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                />
              </div>
            </div>

            {/* Vendor Filter */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                Vendor
              </label>
              <select
                id="filter-vendor"
                value={vendorFilter}
                onChange={(e) => setVendorFilter(e.target.value)}
                className="w-full px-3 py-2 bg-secondary/50 border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm h-[38px] cursor-pointer"
              >
                <option value="">All Vendors</option>
                {vendorsList.map((vendor) => (
                  <option key={vendor.vendor_id} value={vendor.vendor_id}>
                    {vendor.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                Status
              </label>
              <select
                id="filter-status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 bg-secondary/50 border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm h-[38px] cursor-pointer"
              >
                <option value="All">All Statuses</option>
                <option value="Draft">Draft</option>
                <option value="Pending">Pending</option>
                <option value="Approved">Approved</option>
                <option value="Rejected">Rejected</option>
                <option value="Hold">Hold</option>
              </select>
            </div>

            {/* Sort Filter */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-3 py-2 bg-secondary/50 border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm h-[38px] cursor-pointer"
              >
                <option value="po_number">PO Number (Desc)</option>
                <option value="amount">Amount (High to Low)</option>
                <option value="date">Created Date</option>
              </select>
            </div>
          </div>

          {/* Radio Buttons & Checkboxes (Playwright verification targets) */}
          <div className="flex flex-wrap items-center gap-6 pt-2 border-t border-border/50 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mr-2">Scope:</span>
              <label className="flex items-center gap-2 text-muted-foreground cursor-pointer select-none">
                <input
                  type="radio"
                  name="scope"
                  checked={!activeOnly}
                  onChange={() => setActiveOnly(false)}
                  className="rounded-full border-border text-primary focus:ring-primary h-4 w-4"
                />
                <span>All Orders</span>
              </label>
              <label className="flex items-center gap-2 text-muted-foreground cursor-pointer select-none ml-2">
                <input
                  type="radio"
                  name="scope"
                  checked={activeOnly}
                  onChange={() => setActiveOnly(true)}
                  className="rounded-full border-border text-primary focus:ring-primary h-4 w-4"
                />
                <span>Active Only</span>
              </label>
            </div>

            <div className="h-4 w-px bg-border" />

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-muted-foreground cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={highValueOnly}
                  onChange={(e) => setHighValueOnly(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary h-4 w-4"
                />
                <span>High Value (&gt;$50K)</span>
              </label>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              id="btn-reset-filters"
              onClick={handleReset}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-secondary text-secondary-foreground font-semibold rounded-lg hover:bg-secondary/85 transition-all text-xs"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Reset</span>
            </button>
            <button
              type="submit"
              id="btn-search-po"
              className="inline-flex items-center gap-1.5 px-5 py-2 bg-primary text-primary-foreground font-semibold rounded-lg shadow-sm hover:bg-primary/95 transition-all text-xs"
            >
              <Search className="h-3.5 w-3.5" />
              <span>Search</span>
            </button>
          </div>
        </form>
      </div>

      {/* Results Table Card */}
      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h3 className="font-bold text-foreground text-sm tracking-wide uppercase">
            Search Results ({totalPosCount} found)
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900/40 text-xs font-semibold text-muted-foreground uppercase border-b border-border">
              <tr>
                <th className="px-6 py-3.5">PO Number</th>
                <th className="px-6 py-3.5">Vendor</th>
                <th className="px-6 py-3.5">Invoice Number</th>
                <th className="px-6 py-3.5 text-right">Amount</th>
                <th className="px-6 py-3.5 text-center">Status</th>
                <th className="px-6 py-3.5 text-center">Created Date</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {pos
                .filter(po => {
                  if (activeOnly && (po.status === 'Approved' || po.status === 'Rejected')) return false;
                  if (highValueOnly && po.amount <= 50000) return false;
                  return true;
                })
                .sort((a, b) => {
                  if (sortBy === 'amount') return b.amount - a.amount;
                  if (sortBy === 'date') return new Date(b.created_date).getTime() - new Date(a.created_date).getTime();
                  return b.po_number.localeCompare(a.po_number);
                })
                .map((po) => (
                  <tr key={po.po_number} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/10 transition-colors">
                    <td className="px-6 py-4 font-bold text-foreground">{po.po_number}</td>
                    <td className="px-6 py-4 text-muted-foreground font-medium">{po.vendor_name}</td>
                    <td className="px-6 py-4 font-mono text-xs">{po.invoice_number || '-'}</td>
                    <td className="px-6 py-4 text-right font-semibold text-foreground">
                      {po.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {po.currency}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {getStatusBadge(po.status)}
                    </td>
                    <td className="px-6 py-4 text-center text-xs text-muted-foreground">{po.created_date}</td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-2">
                        <Link
                          href={`/pos/${po.po_number}`}
                          id={`btn-view-details-${po.po_number}`}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary text-primary-foreground font-semibold rounded hover:bg-primary/90 transition-all text-xs"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          <span>View Details</span>
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              {pos.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-muted-foreground text-sm">
                    No results match the query filters.
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

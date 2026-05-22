'use client';

import React, { useEffect, useState } from 'react';
import { Search, Building2, Mail, Phone, MapPin, Receipt } from 'lucide-react';

export default function VendorsPage() {
  const [vendors, setVendors] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedVendor, setSelectedVendor] = useState<any | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/vendors')
      .then(res => res.json())
      .then(data => {
        setVendors(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const filteredVendors = vendors.filter(v => 
    v.name.toLowerCase().includes(search.toLowerCase()) ||
    v.vendor_id.toLowerCase().includes(search.toLowerCase()) ||
    v.gst_number.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Vendor Directory</h1>
        <p className="text-muted-foreground mt-1">Review active suppliers, contract metadata, and bank details.</p>
      </div>

      {/* Main Grid: Directory Left, Detail Card Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* List Pane */}
        <div className="lg:col-span-2 space-y-4">
          {/* Search bar */}
          <div className="bg-card border border-border rounded-xl p-4 shadow-sm flex items-center gap-3">
            <Search className="h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by company name, vendor ID, or Tax ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-transparent border-0 outline-none text-sm text-foreground placeholder:text-muted-foreground w-full"
            />
          </div>

          {/* Vendors Card List */}
          <div className="bg-card border border-border rounded-xl shadow-sm divide-y divide-border overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                Fetching vendors database...
              </div>
            ) : filteredVendors.length > 0 ? (
              filteredVendors.map(vendor => (
                <div 
                  key={vendor.vendor_id}
                  onClick={() => setSelectedVendor(vendor)}
                  className={`p-4 flex items-center justify-between cursor-pointer transition-colors ${
                    selectedVendor?.vendor_id === vendor.vendor_id 
                      ? 'bg-primary/5 dark:bg-primary/10' 
                      : 'hover:bg-slate-50/50 dark:hover:bg-slate-900/10'
                  }`}
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className="h-9 w-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
                      <Building2 className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <h4 className="font-bold text-foreground text-sm truncate">{vendor.name}</h4>
                      <p className="text-xs text-muted-foreground font-semibold mt-0.5">{vendor.vendor_id}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4 shrink-0 text-right">
                    <div className="hidden md:block">
                      <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block">Terms</span>
                      <span className="text-xs font-semibold text-foreground bg-secondary px-2 py-0.5 rounded mt-0.5 inline-block">
                        {vendor.payment_terms}
                      </span>
                    </div>
                    <div className="hidden lg:block text-left w-36">
                      <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block">Tax Ref</span>
                      <span className="text-xs font-mono text-foreground truncate block">{vendor.gst_number}</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-muted-foreground text-sm">
                No vendors found matching your query.
              </div>
            )}
          </div>
        </div>

        {/* Detailed Pane */}
        <div className="lg:col-span-1">
          {selectedVendor ? (
            <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-5 animate-fade-in sticky top-8">
              <div className="flex items-center gap-3 border-b border-border pb-4">
                <div className="h-10 w-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                  <Building2 className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-foreground text-sm">{selectedVendor.name}</h3>
                  <p className="text-xs text-muted-foreground font-semibold">{selectedVendor.vendor_id}</p>
                </div>
              </div>

              <div className="space-y-4 text-sm">
                <div className="flex gap-3">
                  <Receipt className="h-4.5 w-4.5 text-muted-foreground shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block">Tax Reference (GST/VAT)</span>
                    <span className="font-mono text-foreground mt-0.5 block">{selectedVendor.gst_number}</span>
                  </div>
                </div>

                <div className="flex gap-3">
                  <MapPin className="h-4.5 w-4.5 text-muted-foreground shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block">Billing Address</span>
                    <span className="text-xs text-muted-foreground leading-relaxed mt-0.5 block">{selectedVendor.address}</span>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Mail className="h-4.5 w-4.5 text-muted-foreground shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block">Contract Email</span>
                    <span className="text-primary font-semibold text-xs mt-0.5 block">{selectedVendor.email}</span>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Phone className="h-4.5 w-4.5 text-muted-foreground shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block">Phone Contact</span>
                    <span className="text-foreground text-xs mt-0.5 block">{selectedVendor.phone}</span>
                  </div>
                </div>

                <div className="pt-2 border-t border-border/60">
                  <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block mb-1">Contract Terms</span>
                  <span className="inline-block bg-primary/10 text-primary px-2.5 py-1 rounded font-bold text-xs">
                    {selectedVendor.payment_terms}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-card border border-border border-dashed rounded-xl p-8 text-center text-sm text-muted-foreground flex flex-col items-center justify-center h-48 sticky top-8">
              <Building2 className="h-8 w-8 text-muted-foreground mb-2 animate-bounce" />
              <p className="font-semibold text-foreground">Select a Vendor</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">Click any supplier card to load full contact directory details.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

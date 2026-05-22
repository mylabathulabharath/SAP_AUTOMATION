'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { 
  LayoutDashboard, 
  FileSearch, 
  FileCheck, 
  Users, 
  FileBarChart, 
  Terminal, 
  Settings, 
  LogOut, 
  Sun, 
  Moon,
  Building2
} from 'lucide-react';
import { useStore } from '../store/useStore';

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, darkMode, toggleDarkMode } = useStore();

  const menuItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: '/dashboard', id: 'nav-dashboard' },
    { name: 'Purchase Orders', icon: FileSearch, path: '/pos', id: 'nav-pos' },
    { name: 'Invoice Verification', icon: FileCheck, path: '/pos?status=Pending', id: 'nav-invoice-verify' },
    { name: 'Vendor Management', icon: Users, path: '/vendors', id: 'nav-vendors' },
    { name: 'Automation Dashboard', icon: Terminal, path: '/automation', id: 'nav-automation' },
    { name: 'Reports & Audits', icon: FileBarChart, path: '/reports', id: 'nav-reports' },
  ];

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const isItemActive = (itemPath: string) => {
    if (itemPath.includes('?')) {
      // For query parameters like ?status=Pending
      const [base, query] = itemPath.split('?');
      if (typeof window !== 'undefined') {
        return pathname === base && window.location.search.includes(query);
      }
      return false;
    }
    // Standard path matching
    if (itemPath === '/dashboard') return pathname === '/dashboard';
    return pathname.startsWith(itemPath);
  };

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col h-screen shrink-0 transition-all duration-300 z-10">
      {/* Brand Logo Header */}
      <div className="h-16 flex items-center px-6 border-b border-border bg-gradient-to-r from-primary/10 to-transparent">
        <div className="flex items-center gap-2">
          <Building2 className="h-6 w-6 text-primary animate-pulse" />
          <span className="font-bold text-lg tracking-wider bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
            SAP Fiori
          </span>
          <span className="text-[10px] uppercase font-semibold text-muted-foreground bg-secondary px-1.5 py-0.5 rounded ml-1">
            Sim
          </span>
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const active = isItemActive(item.path);
          return (
            <Link
              key={item.name}
              href={item.path}
              id={item.id}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${
                active
                  ? 'bg-primary text-primary-foreground shadow-md shadow-primary/20 scale-[1.02]'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
              }`}
            >
              <Icon className={`h-4.5 w-4.5 transition-transform duration-200 group-hover:scale-110 ${active ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-primary'}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer Actions */}
      <div className="p-4 border-t border-border bg-slate-50/50 dark:bg-slate-900/10 space-y-2">
        {/* Dark Mode Toggle */}
        <button
          onClick={toggleDarkMode}
          className="flex w-full items-center justify-between px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
        >
          <div className="flex items-center gap-3">
            {darkMode ? <Sun className="h-4.5 w-4.5 text-yellow-500" /> : <Moon className="h-4.5 w-4.5 text-primary" />}
            <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
          </div>
          <span className="text-[10px] text-muted-foreground uppercase font-bold bg-secondary px-1.5 py-0.5 rounded">
            Theme
          </span>
        </button>

        {/* User Card */}
        {user && (
          <div className="flex items-center gap-3 p-2 rounded-lg bg-card border border-border">
            <div className="h-9 w-9 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-sm border border-primary/20">
              {user.username.slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-foreground truncate">{user.username}</p>
              <p className="text-[10px] text-muted-foreground truncate">System Administrator</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}

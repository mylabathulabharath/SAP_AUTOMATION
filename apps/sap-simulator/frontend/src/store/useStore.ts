import { create } from 'zustand';

interface User {
  username: string;
  token: string;
}

interface POHeader {
  po_number: string;
  vendor_id: string;
  vendor_name: string;
  invoice_number: string | null;
  amount: number;
  currency: string;
  status: string;
  approval_status: string;
  created_date: string;
}

interface PODetail {
  header: POHeader;
  vendor: {
    name: string;
    address: string;
    email: string;
    gst_number: string;
    phone: string;
    payment_terms: string;
  };
  items: Array<{
    item_code: string;
    description: string;
    quantity: number;
    price: number;
    tax: number;
    total: number;
  }>;
  invoice: {
    invoice_number: string;
    amount: number;
    currency: string;
    status: string;
    created_date: string;
  } | null;
  attachments: Array<{
    filename: string;
    size: string;
    type: string;
  }>;
  audit_logs: Array<{
    action: string;
    performed_by: string;
    timestamp: string;
    details: string;
  }>;
  payment_details: {
    bank_name: string;
    account_number: string;
    payment_terms: string;
    currency: string;
    due_date: string;
  };
}

interface AutomationStatus {
  status: 'idle' | 'running' | 'completed' | 'failed';
  current_po: string;
  processed_count: number;
  total_count: number;
  success_count: number;
  failure_count: number;
  start_time: string;
}

interface DashboardStats {
  total_pos: number;
  pending_pos: number;
  approved_pos: number;
  invoice_count: number;
  automation_runs: number;
  automation_success_rate: number;
}

interface StoreState {
  user: User | null;
  darkMode: boolean;
  pos: POHeader[];
  totalPosCount: number;
  currentPo: PODetail | null;
  dashboardStats: DashboardStats | null;
  automationStatus: AutomationStatus | null;
  logs: string;
  reports: any[];
  
  // Actions
  login: (username: string, token: string) => void;
  logout: () => void;
  toggleDarkMode: () => void;
  setDarkMode: (val: boolean) => void;
  fetchStats: () => Promise<void>;
  fetchPos: (filters?: { po_number?: string; vendor_id?: string; status?: string; limit?: number; offset?: number }) => Promise<void>;
  fetchPoDetail: (po_number: string) => Promise<void>;
  executePoAction: (po_number: string, action: string, remarks?: string) => Promise<boolean>;
  
  // Automation actions
  uploadExcel: (file: File) => Promise<{ filename: string; rows_count: number }>;
  startAutomation: () => Promise<boolean>;
  fetchAutomationStatus: () => Promise<void>;
  fetchLogs: () => Promise<void>;
  fetchReports: () => Promise<void>;
}

const SAP_API_URL = 'http://localhost:8000/api';
const AUTO_API_URL = 'http://localhost:8001/api';

export const useStore = create<StoreState>((set, get) => ({
  user: null,
  darkMode: false,
  pos: [],
  totalPosCount: 0,
  currentPo: null,
  dashboardStats: null,
  automationStatus: null,
  logs: '',
  reports: [],

  login: (username, token) => {
    const user = { username, token };
    localStorage.setItem('sap_user', JSON.stringify(user));
    set({ user });
  },

  logout: () => {
    localStorage.removeItem('sap_user');
    set({ user: null });
  },

  toggleDarkMode: () => {
    const nextMode = !get().darkMode;
    if (nextMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    set({ darkMode: nextMode });
  },

  setDarkMode: (val) => {
    if (val) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    set({ darkMode: val });
  },

  fetchStats: async () => {
    try {
      const res = await fetch(`${SAP_API_URL}/dashboard/stats`);
      if (res.ok) {
        const data = await res.json();
        set({ dashboardStats: data });
      }
    } catch (e) {
      console.error('Failed to fetch stats:', e);
    }
  },

  fetchPos: async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      if (filters.po_number) params.append('po_number', filters.po_number);
      if (filters.vendor_id) params.append('vendor_id', filters.vendor_id);
      if (filters.status && filters.status !== 'All') params.append('status', filters.status);
      params.append('limit', String(filters.limit || 50));
      params.append('offset', String(filters.offset || 0));

      const res = await fetch(`${SAP_API_URL}/pos?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        set({ pos: data.data, totalPosCount: data.total });
      }
    } catch (e) {
      console.error('Failed to fetch PO list:', e);
    }
  },

  fetchPoDetail: async (po_number) => {
    try {
      const res = await fetch(`${SAP_API_URL}/pos/${po_number}`);
      if (res.ok) {
        const data = await res.json();
        set({ currentPo: data });
      } else {
        set({ currentPo: null });
      }
    } catch (e) {
      console.error('Failed to fetch PO details:', e);
      set({ currentPo: null });
    }
  },

  executePoAction: async (po_number, action, remarks = '') => {
    try {
      const res = await fetch(`${SAP_API_URL}/pos/${po_number}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, remarks }),
      });
      if (res.ok) {
        // Refresh details and recent list
        await get().fetchPoDetail(po_number);
        await get().fetchStats();
        return true;
      }
      return false;
    } catch (e) {
      console.error('Failed to execute action:', e);
      return false;
    }
  },

  uploadExcel: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${AUTO_API_URL}/upload-excel`, {
      method: 'POST',
      body: formData,
    });
    if (res.ok) {
      const data = await res.json();
      await get().fetchAutomationStatus();
      return data;
    }
    throw new Error(await res.text() || 'Failed to upload Excel');
  },

  startAutomation: async () => {
    try {
      const res = await fetch(`${AUTO_API_URL}/start-automation`, {
        method: 'POST',
      });
      if (res.ok) {
        set({ logs: '[INFO] Launching browser...\n' });
        await get().fetchAutomationStatus();
        return true;
      }
      return false;
    } catch (e) {
      console.error('Failed to start automation:', e);
      return false;
    }
  },

  fetchAutomationStatus: async () => {
    try {
      const res = await fetch(`${AUTO_API_URL}/automation-status`);
      if (res.ok) {
        const data = await res.json();
        set({ automationStatus: data });
      }
    } catch (e) {
      console.error('Failed to fetch automation status:', e);
    }
  },

  fetchLogs: async () => {
    try {
      const res = await fetch(`${AUTO_API_URL}/logs`);
      if (res.ok) {
        const data = await res.json();
        set({ logs: data.logs });
      }
    } catch (e) {
      console.error('Failed to fetch logs:', e);
    }
  },

  fetchReports: async () => {
    try {
      const res = await fetch(`${AUTO_API_URL}/reports`);
      if (res.ok) {
        const data = await res.json();
        set({ reports: data.reports });
      }
    } catch (e) {
      console.error('Failed to fetch reports:', e);
    }
  },
}));

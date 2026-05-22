'use client';

import { useEffect } from 'react';
import { useStore } from '../store/useStore';

export default function ClientInit() {
  const { login, setDarkMode } = useStore();

  useEffect(() => {
    // 1. Restore Auth User
    const savedUser = localStorage.getItem('sap_user');
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser);
        login(parsed.username, parsed.token);
      } catch (e) {
        localStorage.removeItem('sap_user');
      }
    }

    // 2. Restore Dark Mode
    const isDark = document.documentElement.classList.contains('dark') || 
                   localStorage.getItem('theme') === 'dark';
    if (isDark) {
      setDarkMode(true);
    }
  }, [login, setDarkMode]);

  return null;
}

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useStore } from '../store/useStore';
import { Loader2 } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const { user } = useStore();

  useEffect(() => {
    // Check localstorage directly since store might still be initializing
    const savedUser = localStorage.getItem('sap_user');
    if (savedUser || user) {
      router.replace('/dashboard');
    } else {
      router.replace('/login');
    }
  }, [user, router]);

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground font-medium">Loading SAP Fiori Environment...</p>
      </div>
    </div>
  );
}

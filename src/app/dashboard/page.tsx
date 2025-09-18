'use client'

import type { Metadata } from "next";
import { Suspense, useEffect } from 'react';
import { useRouter } from "next/navigation";
import ClientOnly from "@/components/client-only";
import { useAuth } from "@/contexts/AuthContext";
import { ChatProvider } from "@/contexts/ChatContext";

import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/sidebar";
import Chat from "@/components/chat";

import { DashboardSidebarClient } from "@/components/dashboard-sidebar-client";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <ChatProvider userId={user.id}>
      <SidebarProvider>
        <Suspense fallback={<div className="w-64 bg-sidebar"></div>}>
          <DashboardSidebarClient />
        </Suspense>
        <SidebarInset className="bg-sidebar group/sidebar-inset">
          <header className="dark flex h-12 shrink-0 items-center gap-2 px-4 md:px-6 lg:px-8 bg-sidebar text-sidebar-foreground relative before:absolute before:inset-y-3 before:-left-px before:w-px before:bg-gradient-to-b before:from-white/5 before:via-white/15 before:to-white/5 before:z-50">
            <SidebarTrigger className="-ms-2 h-8 w-8 [&>svg]:size-4" />
          </header>
          <Suspense fallback={<div>Loading chat...</div>}>
            <div className="flex h-[calc(100svh-3rem)] bg-[hsl(240_5%_92.16%)] md:rounded-s-3xl md:group-peer-data-[state=collapsed]/sidebar-inset:rounded-s-none transition-all ease-in-out duration-300">
              <Chat />
            </div>
          </Suspense>
        </SidebarInset>
      </SidebarProvider>
    </ChatProvider>
  );
}

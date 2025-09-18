import * as React from "react";
import { useState, useEffect } from "react";

import UserDropdown from "@/components/user-dropdown";
import { GmailConnectDialog } from "@/components/gmail-connect-dialog";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/sidebar";
import {
  RiMailLine,
  RiPlanetLine,
  RiSeedlingLine,
  RiSettings3Line,
  RiAddLine,
  RiHistoryLine,
} from "@remixicon/react";
import { useAuth } from "@/contexts/AuthContext";
import { useChat } from "@/contexts/ChatContext";

const data = {
  navMain: [
    {
      title: "Integrations",
      url: "#",
      items: [
        {
          title: "Gmail",
          url: "#",
          icon: RiMailLine,
        },
      ],
    },
    {
      title: "More",
      url: "#",
      items: [
        {
          title: "Community",
          url: "#",
          icon: RiPlanetLine,
        },
        {
          title: "Help Centre",
          url: "#",
          icon: RiSeedlingLine,
        },
        {
          title: "Settings",
          url: "#",
          icon: RiSettings3Line,
        },
      ],
    },
  ],
};

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const [gmailDialogOpen, setGmailDialogOpen] = useState(false);
  const [gmailConnected, setGmailConnected] = useState(false);
  const { user } = useAuth();
  const { 
    conversations, 
    currentConversationId, 
    isLoadingConversations, 
    createNewConversation, 
    selectConversation 
  } = useChat();

  useEffect(() => {
    if (user) {
      checkGmailConnection();
    }
  }, [user]);

  const checkGmailConnection = async () => {
    try {
      const response = await fetch('/api/auth/gmail/status', {
        headers: {
          'Authorization': `Bearer ${user?.id}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setGmailConnected(data.connected);
      }
    } catch (error) {
      console.error('Error checking Gmail connection:', error);
    }
  };

  const handleGmailClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setGmailDialogOpen(true);
  };

  const handleNewChat = async (e: React.MouseEvent) => {
    e.preventDefault();
    await createNewConversation();
  };

  const handleSelectConversation = (conversationId: string, e: React.MouseEvent) => {
    e.preventDefault();
    selectConversation(conversationId);
  };

  return (
    <Sidebar {...props} className="dark !border-none">
      <SidebarHeader>
        <div className="p-4">
          <UserDropdown />
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent className="px-2">
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  className="group/menu-button font-medium gap-3 h-9 rounded-md hover:bg-sidebar-accent [&>svg]:size-auto"
                >
                  <button onClick={handleNewChat} className="flex items-center w-full">
                    <RiAddLine size={22} className="text-sidebar-foreground/50" />
                    <span>New Chat</span>
                  </button>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel className="uppercase text-sidebar-foreground/50">
            History
          </SidebarGroupLabel>
          <SidebarGroupContent className="px-2 max-h-96 overflow-y-auto">
            <SidebarMenu>
              {isLoadingConversations ? (
                <SidebarMenuItem>
                  <div className="flex items-center gap-3 h-9 px-2">
                    <div className="animate-pulse bg-muted rounded w-5 h-5" />
                    <div className="animate-pulse bg-muted rounded w-32 h-4" />
                  </div>
                </SidebarMenuItem>
              ) : conversations.length === 0 ? (
                <SidebarMenuItem>
                  <span className="text-xs text-muted-foreground px-2">No conversations yet</span>
                </SidebarMenuItem>
              ) : (
                conversations.slice(0, 10).map((conversation) => (
                  <SidebarMenuItem key={conversation.id}>
                    <SidebarMenuButton
                      asChild
                      className="group/menu-button font-medium gap-3 h-9 rounded-md data-[active=true]:hover:bg-transparent data-[active=true]:bg-gradient-to-b data-[active=true]:from-sidebar-primary data-[active=true]:to-sidebar-primary/70 data-[active=true]:shadow-[0_1px_2px_0_rgb(0_0_0/.05),inset_0_1px_0_0_rgb(255_255_255/.12)] [&>svg]:size-auto"
                      isActive={conversation.id === currentConversationId}
                    >
                      <button 
                        onClick={(e) => handleSelectConversation(conversation.id, e)}
                        className="flex items-center justify-between w-full"
                      >
                        <div className="flex items-center gap-3">
                          <RiHistoryLine size={16} className="text-sidebar-foreground/50" />
                          <span className="truncate max-w-32 text-left">{conversation.title}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(conversation.updated_at).toLocaleDateString()}
                        </span>
                      </button>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarGroup>
          <SidebarGroupLabel className="uppercase text-sidebar-foreground/50">
            {data.navMain[0]?.title}
          </SidebarGroupLabel>
          <SidebarGroupContent className="px-2">
            <SidebarMenu>
              {data.navMain[0]?.items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    className="group/menu-button font-medium gap-3 h-9 rounded-md data-[active=true]:hover:bg-transparent data-[active=true]:bg-gradient-to-b data-[active=true]:from-sidebar-primary data-[active=true]:to-sidebar-primary/70 data-[active=true]:shadow-[0_1px_2px_0_rgb(0_0_0/.05),inset_0_1px_0_0_rgb(255_255_255/.12)] [&>svg]:size-auto"
                    isActive={false}
                  >
                    <a 
                      href={item.url}
                      onClick={item.title === 'Gmail' ? handleGmailClick : undefined}
                      className="flex items-center justify-between w-full"
                    >
                      <div className="flex items-center gap-3">
                        {item.icon && (
                          <item.icon
                            className="text-sidebar-foreground/50 group-data-[active=true]/menu-button:text-sidebar-foreground"
                            size={22}
                            aria-hidden="true"
                          />
                        )}
                        <span>{item.title}</span>
                      </div>
                      {item.title === 'Gmail' && gmailConnected && (
                        <span className="text-xs text-green-400 font-medium">
                          connected
                        </span>
                      )}
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel className="uppercase text-sidebar-foreground/50">
            {data.navMain[1]?.title}
          </SidebarGroupLabel>
          <SidebarGroupContent className="px-2">
            <SidebarMenu>
              {data.navMain[1]?.items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    className="group/menu-button font-medium gap-3 h-9 rounded-md [&>svg]:size-auto"
                    isActive={false}
                  >
                    <a href={item.url}>
                      {item.icon && (
                        <item.icon
                          className="text-sidebar-foreground/50 group-data-[active=true]/menu-button:text-primary"
                          size={22}
                          aria-hidden="true"
                        />
                      )}
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarFooter>

      <GmailConnectDialog 
        open={gmailDialogOpen} 
        onOpenChange={setGmailDialogOpen}
      />
    </Sidebar>
  );
}
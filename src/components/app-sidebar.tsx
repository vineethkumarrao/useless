import * as React from "react";
import { useState, useEffect } from "react";

import { TeamSwitcher } from "@/components/team-switcher";
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
  RiChat1Line,
  RiMailLine,
  RiMickeyLine,
  RiMicLine,
  RiCheckDoubleLine,
  RiBracesLine,
  RiPlanetLine,
  RiSeedlingLine,
  RiSettings3Line,
} from "@remixicon/react";
import { useAuth } from "@/contexts/AuthContext";

// This is sample data.
const data = {
  teams: [
    {
      name: "ArkDigital",
      logo: "https://raw.githubusercontent.com/origin-space/origin-images/refs/heads/main/exp2/logo-01_upxvqe.png",
    },
    {
      name: "Acme Corp.",
      logo: "https://raw.githubusercontent.com/origin-space/origin-images/refs/heads/main/exp2/logo-01_upxvqe.png",
    },
    {
      name: "Evil Corp.",
      logo: "https://raw.githubusercontent.com/origin-space/origin-images/refs/heads/main/exp2/logo-01_upxvqe.png",
    },
  ],
  navMain: [
    {
      title: "Playground",
      url: "#",
      items: [
        {
          title: "Chat",
          url: "#",
          icon: RiChat1Line,
          isActive: true,
        },
        {
          title: "Gmail",
          url: "#",
          icon: RiMailLine,
        },
        {
          title: "Assistants",
          url: "#",
          icon: RiMickeyLine,
        },
        {
          title: "Audio",
          url: "#",
          icon: RiMicLine,
        },
        {
          title: "Metrics",
          url: "#",
          icon: RiCheckDoubleLine,
        },
        {
          title: "Documentation",
          url: "#",
          icon: RiBracesLine,
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
  const [gmailDialogOpen, setGmailDialogOpen] = useState(false)
  const [gmailConnected, setGmailConnected] = useState(false)
  const { user } = useAuth()

  // Check Gmail connection status on mount
  useEffect(() => {
    if (user) {
      checkGmailConnection()
    }
  }, [user])

  const checkGmailConnection = async () => {
    try {
      const response = await fetch('/api/auth/gmail/status', {
        headers: {
          'Authorization': `Bearer ${user?.id}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setGmailConnected(data.connected)
      }
    } catch (error) {
      console.error('Error checking Gmail connection:', error)
    }
  }

  const handleGmailClick = (e: React.MouseEvent) => {
    e.preventDefault()
    setGmailDialogOpen(true)
  }

  return (
    <Sidebar {...props} className="dark !border-none">
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        {/* We only show the first parent group */}
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
                    isActive={item.isActive}
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
      </SidebarContent>
      <SidebarFooter>
        {/* Secondary Navigation */}
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
                    isActive={item.isActive}
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

      {/* Gmail Connect Dialog */}
      <GmailConnectDialog 
        open={gmailDialogOpen} 
        onOpenChange={setGmailDialogOpen}
      />
    </Sidebar>
  );
}

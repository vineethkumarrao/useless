import { Avatar, AvatarFallback, AvatarImage } from "@/components/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/dropdown-menu";

import {
  RiLogoutCircleLine,
  RiTimer2Line,
  RiUserLine,
  RiFindReplaceLine,
  RiPulseLine,
} from "@remixicon/react";

import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";

export default function UserDropdown() {
  const { user, signOut } = useAuth();
  const router = useRouter();

  // Generate user initials for avatar fallback
  const getUserInitials = (fullName?: string) => {
    if (!fullName) return 'U';
    const names = fullName.split(' ');
    const initials = names.map(name => name.charAt(0)).join('');
    return initials.substring(0, 2).toUpperCase();
  };

  const handleLogout = async () => {
    try {
      await signOut();
      router.push('/');
    } catch (error) {
      console.error('Error during logout:', error);
      // Even if there's an error, still redirect to home
      router.push('/');
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-auto p-0 hover:bg-transparent" suppressHydrationWarning>
          <Avatar className="size-8">
            <AvatarImage
              src="https://raw.githubusercontent.com/origin-space/origin-images/refs/heads/main/exp2/user-02_mlqqqt.png"
              width={32}
              height={32}
              alt="Profile image"
            />
            <AvatarFallback>{getUserInitials(user?.full_name)}</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="max-w-64 p-2" align="end">
        <DropdownMenuLabel className="flex min-w-0 flex-col py-0 px-1 mb-2">
          <span className="truncate text-sm font-medium text-foreground mb-0.5">
            {user?.full_name || 'User'}
          </span>
          <span className="truncate text-xs font-normal text-muted-foreground">
            {user?.email || 'user@example.com'}
          </span>
        </DropdownMenuLabel>
        <DropdownMenuItem className="gap-3 px-1">
          <RiTimer2Line
            size={20}
            className="text-muted-foreground/70"
            aria-hidden="true"
          />
          <span>Dashboard</span>
        </DropdownMenuItem>
        <DropdownMenuItem className="gap-3 px-1">
          <RiUserLine
            size={20}
            className="text-muted-foreground/70"
            aria-hidden="true"
          />
          <span>Profile</span>
        </DropdownMenuItem>
        <DropdownMenuItem className="gap-3 px-1">
          <RiPulseLine
            size={20}
            className="text-muted-foreground/70"
            aria-hidden="true"
          />
          <span>Changelog</span>
        </DropdownMenuItem>
        <DropdownMenuItem className="gap-3 px-1">
          <RiFindReplaceLine
            size={20}
            className="text-muted-foreground/70"
            aria-hidden="true"
          />
          <span>History</span>
        </DropdownMenuItem>
        <DropdownMenuItem className="gap-3 px-1" onClick={handleLogout}>
          <RiLogoutCircleLine
            size={20}
            className="text-muted-foreground/70"
            aria-hidden="true"
          />
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

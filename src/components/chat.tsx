"use client";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/dropdown-menu";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/scroll-area";
import {
  RiShining2Line,
  RiAttachment2,
  RiMicLine,
  RiLeafLine,
  RiSendPlane2Fill,
  RiAddFill,
  RiWifiLine,
  RiWifiOffLine,
  RiErrorWarningLine
} from "@remixicon/react";
import { ChatMessage } from "@/components/chat-message";
import { useRef, useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useChat } from "@/contexts/ChatContext";
import { supabase } from "@/lib/supabase";
import type { Message as DBMessage } from "@/lib/supabase";

interface Message {
  role: "user" | "assistant";
  content: string;
  type?: string;  // 'simple' | 'complex' | 'error'
}

// Badge-like styled span
const StyledBadge = ({ variant = "default", className = "", children }: { variant?: "default" | "secondary" | "destructive"; className?: string; children: React.ReactNode; }) => {
  const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
  const variantClasses = {
    default: "bg-primary text-primary-foreground",
    secondary: "bg-secondary text-secondary-foreground",
    destructive: "bg-destructive text-destructive-foreground"
  };
  return <span className={`${baseClasses} ${variantClasses[variant] || "bg-muted text-muted-foreground"} ${className}`}>{children}</span>;
};

export default function Chat() {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [agentMode, setAgentMode] = useState(false);
  const [selectedApps, setSelectedApps] = useState<string[]>([]);
  const [showAppDropdown, setShowAppDropdown] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();
  const {
    currentConversationId,
    currentMessages,
    loadConversations,
    selectConversation,
    reloadCurrentConversation,
    addOptimisticMessage,
    userId,
    isLoadingMessages,
  } = useChat();

  const messages: Message[] = currentMessages.map((msg: DBMessage) => ({
    role: msg.role as "user" | "assistant",
    content: msg.content,
    type: msg.metadata?.type || undefined,
  }));

  // Check connections on mount and agent mode change
  useEffect(() => {
    if (agentMode && userId) {
      checkConnections();
    }
  }, [agentMode, userId]);

  const checkConnections = async () => {
    try {
      const response = await fetch("/api/integrations/status", {
        headers: { 
          "Authorization": `Bearer ${userId}`,
          "Content-Type": "application/json"
        },
      });
      
      if (response.ok) {
        const status = await response.json();
        setConnectionStatus(status);
      }
    } catch (error) {
      console.error("Connection check failed:", error);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading || !currentConversationId) return;

    const userMessageContent = input.trim();
    setInput("");
    setIsLoading(true);

    // Add user message optimistically
    const tempUserMessage: DBMessage = {
      id: `temp-${Date.now()}`,
      conversation_id: currentConversationId,
      user_id: userId!,
      content: userMessageContent,
      role: 'user',
      created_at: new Date().toISOString(),
      metadata: {},
    };
    
    addOptimisticMessage(tempUserMessage);

    try {
      console.log("=== CHAT DEBUG INFO ===");
      console.log("UserId:", userId);
      console.log("Message:", userMessageContent);
      console.log("Conversation ID:", currentConversationId);
      console.log("Agent Mode:", agentMode);
      console.log("========================");

      const useGmailAgent = agentMode && selectedApps.includes("Gmail");
      
      const requestBody = {
        message: userMessageContent,
        conversation_id: currentConversationId,
        agent_mode: agentMode,
        selected_apps: selectedApps,
        use_gmail_agent: useGmailAgent
      };

      console.log("Request body:", JSON.stringify(requestBody, null, 2));
      
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${userId}`
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.text();
        console.error("API Error Details:", {
          status: response.status,
          statusText: response.statusText,
          errorData: errorData
        });
        throw new Error(`API error: ${response.statusText} - ${errorData}`);
      }

      const data = await response.json();
      console.log("API Response:", data);

      // Handle different response types
      const assistantMessage: DBMessage = {
        id: `server-${Date.now()}`,
        conversation_id: currentConversationId,
        user_id: userId!,
        content: data.response,
        role: 'assistant',
        created_at: new Date().toISOString(),
        metadata: { type: data.type },
      };
      
      addOptimisticMessage(assistantMessage);

      // Don't reload - we already have the messages in memory
      console.log("Chat message processed successfully");

    } catch (error) {
      console.error("Chat error:", error);
      
      // Show error message
      const errorMessage: DBMessage = {
        id: `error-${Date.now()}`,
        conversation_id: currentConversationId,
        user_id: userId!,
        content: "Sorry, I encountered an error processing your request. Please try again.",
        role: 'assistant',
        created_at: new Date().toISOString(),
        metadata: { type: 'error' },
      };
      
      addOptimisticMessage(errorMessage);
      
      // Don't reload on error - keep the conversation in memory
      console.log("Error handled, conversation preserved");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleAgentMode = () => {
    setAgentMode(prev => {
      const newMode = !prev;
      if (newMode) {
        setSelectedApps([]); // Reset selections
      }
      return newMode;
    });
  };

  const handleAppSelect = (app: string) => {
    setSelectedApps(prev =>
      prev.includes(app) ? prev.filter(a => a !== app) : [...prev, app]
    );
  };

  const confirmApps = () => {
    console.log("Selected apps:", selectedApps);
    if (selectedApps.includes("Gmail")) {
      console.log("Gmail agent activated");
    }
    setShowAppDropdown(false);
  };

  const cancelApps = () => {
    setSelectedApps([]);
    setShowAppDropdown(false);
  };

  if (isLoadingMessages) {
    return (
      <div className="flex items-center justify-center h-full">
        <div>Loading messages...</div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 [&>div>div]:h-full w-full shadow-md md:rounded-s-[inherit] min-[1024px]:rounded-e-3xl bg-background">
      <div className="h-full flex flex-col px-4 md:px-6 lg:px-8">
        {/* Top status bar */}
        <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 pt-4 pb-2 border-b">
          <div className="max-w-3xl mx-auto flex items-center justify-between">
            {/* Agent Mode Status */}
            <div className="flex items-center space-x-2">
              <StyledBadge variant={agentMode ? "default" : "outline"} className="text-xs">
                {agentMode ? "🤖 Agent Mode Active" : "💭 Simple Chat"}
              </StyledBadge>
              {agentMode && selectedApps.length > 0 && (
                <StyledBadge variant="secondary" className="text-xs">
                  {selectedApps.length} App{selectedApps.length > 1 ? 's' : ''}
                </StyledBadge>
              )}
            </div>
            
            {/* Connection Status */}
            {agentMode && Object.keys(connectionStatus).some(status => connectionStatus[status]) && (
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <RiWifiLine className="w-4 h-4" />
                <span>Connections Active</span>
              </div>
            )}
            
            {/* Conversation ID display */}
            {currentConversationId && (
              <div className="text-xs text-muted-foreground">
                ID: {currentConversationId.substring(0, 8)}...
              </div>
            )}
          </div>
        </div>

        {/* Messages area */}
        <div className="relative grow">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.length === 0 && !isLoading && (
              <div className="text-center my-8">
                <div className="inline-flex items-center bg-white rounded-full border border-black/[0.08] shadow-xs text-xs font-medium py-1 px-3 text-foreground/80">
                  <RiShining2Line
                    className="me-1.5 text-muted-foreground/70 -ms-1"
                    size={14}
                    aria-hidden="true"
                  />
                  Today
                </div>
                <p className="text-muted-foreground mt-4">
                  {agentMode 
                    ? "Agent mode is ready. Select apps above to activate specific tools." 
                    : "Start chatting! Toggle Agent Mode for advanced features."
                  }
                </p>
              </div>
            )}
            {messages.map((message, index) => (
              <ChatMessage 
                key={index} 
                isUser={message.role === "user"}
                type={message.type}
              >
                {message.content}
              </ChatMessage>
            ))}
            {isLoading && (
              <div className="flex items-start space-x-3 p-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted animate-pulse" />
                <div className="flex-1 space-y-2">
                  <div className="flex items-center space-x-2">
                    <div className="h-3 bg-muted rounded-full animate-pulse w-24" />
                    <span className="text-xs text-muted-foreground">Thinking...</span>
                  </div>
                  <div className="h-4 bg-muted rounded animate-pulse w-3/4" />
                  <div className="h-4 bg-muted rounded animate-pulse w-1/2" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} aria-hidden="true" />
          </div>
        </div>

        {/* Input form */}
        <form onSubmit={handleSubmit} className="sticky bottom-0 pt-3 md:pt-6 z-50">
          <div className="max-w-3xl mx-auto bg-background rounded-[20px] pb-3 md:pb-6">
            <div className="relative rounded-[20px] border border-transparent bg-muted transition-colors focus-within:bg-muted/50 focus-within:border-input has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-50 [&:has(input:is(:disabled))_*]:pointer-events-none">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="flex sm:min-h-[60px] w-full bg-transparent px-3 py-2 text-sm leading-normal text-foreground placeholder:text-muted-foreground/70 focus-visible:outline-none resize-none"
                placeholder={
                  agentMode && selectedApps.length > 0
                    ? `Agent active with ${selectedApps.join(', ')} - Type your request...`
                    : agentMode
                      ? "Agent mode active - Select apps above to activate tools..."
                      : "Ask me anything..."
                }
                aria-label="Enter your message"
                disabled={isLoading}
                rows={1}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
              />
              
              {/* Input actions */}
              <div className="flex items-center justify-between gap-2 p-2">
                {/* Left actions */}
                <div className="flex items-center gap-1">
                  {/* Agent toggle */}
                  <div className="relative">
                    <Button
                      type="button"
                      variant={agentMode ? "default" : "outline"}
                      size="sm"
                      className={`h-7 px-3 text-xs transition-all ${agentMode ? 'shadow-md' : ''}`}
                      onClick={toggleAgentMode}
                      disabled={isLoading}
                    >
                      {agentMode ? (
                        <>
                          <RiShining2Line className="w-3 h-3 mr-1" />
                          Agent ON
                        </>
                      ) : (
                        'Agent OFF'
                      )}
                    </Button>
                    
                    {/* Agent mode tooltip */}
                    {agentMode && (
                      <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-background border rounded-md shadow-lg px-2 py-1 text-xs z-50">
                        {selectedApps.length > 0 
                          ? `${selectedApps.length} app${selectedApps.length > 1 ? 's' : ''} active`
                          : 'No apps selected'
                        }
                      </div>
                    )}
                  </div>
                  
                  {/* App selector - only show in agent mode */}
                  {agentMode && (
                    <DropdownMenu open={showAppDropdown} onOpenChange={setShowAppDropdown}>
                      <DropdownMenuTrigger asChild>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2 text-xs"
                          disabled={isLoading}
                        >
                          {selectedApps.length > 0 
                            ? `${selectedApps.length} App${selectedApps.length > 1 ? 's' : ''}`
                            : 'Select Apps'
                          }
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent className="w-56 p-2" align="start">
                        <DropdownMenuLabel>Apps for Agent</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        
                        {['Gmail', 'Calendar', 'Docs', 'Notion', 'GitHub'].map(app => (
                          <DropdownMenuItem 
                            key={app}
                            onSelect={(e) => e.preventDefault()}
                            className="flex items-center justify-between p-2 cursor-pointer -m-2 rounded-md"
                          >
                            <div className="flex items-center space-x-2">
                              <Checkbox
                                id={app.toLowerCase()}
                                checked={selectedApps.includes(app)}
                                onCheckedChange={() => handleAppSelect(app)}
                              />
                              <label 
                                htmlFor={app.toLowerCase()} 
                                className="text-sm font-medium cursor-pointer"
                              >
                                {app}
                              </label>
                            </div>
                            <StyledBadge variant={connectionStatus[app.toLowerCase()] ? "default" : "destructive"} className="text-xs">
                              {connectionStatus[app.toLowerCase()] ? (
                                <>
                                  <RiWifiLine className="w-3 h-3 mr-1" />
                                  Connected
                                </>
                              ) : (
                                <>
                                  <RiWifiOffLine className="w-3 h-3 mr-1" />
                                  Connect
                                </>
                              )}
                            </StyledBadge>
                          </DropdownMenuItem>
                        ))}
                        
                        <DropdownMenuSeparator />
                        <div className="flex justify-end space-x-2 pt-2 border-t">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={cancelApps}
                            className="h-6 px-2 text-xs"
                          >
                            Clear All
                          </Button>
                          <Button
                            size="sm"
                            onClick={confirmApps}
                            className="h-6 px-2 text-xs"
                            disabled={selectedApps.length === 0}
                          >
                            Apply ({selectedApps.length})
                          </Button>
                        </div>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                  
                  {/* Standard input buttons */}
                  <Button 
                    type="button" 
                    variant="ghost" 
                    size="icon" 
                    className="rounded-full size-8 hover:bg-muted/50" 
                    disabled={isLoading}
                    title="Attach file"
                  >
                    <RiAttachment2 className="text-muted-foreground size-4" />
                  </Button>
                  <Button 
                    type="button" 
                    variant="ghost" 
                    size="icon" 
                    className="rounded-full size-8 hover:bg-muted/50" 
                    disabled={isLoading}
                    title="Voice input"
                  >
                    <RiMicLine className="text-muted-foreground size-4" />
                  </Button>
                </div>
                
                {/* Send button */}
                <Button 
                  type="submit" 
                  className="rounded-full h-8 px-4 transition-all" 
                  disabled={isLoading || !input.trim()}
                  variant={input.trim() ? "default" : "outline"}
                >
                  {isLoading ? (
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span className="text-xs">Thinking...</span>
                    </div>
                  ) : (
                    <>
                      <RiSendPlane2Fill className={`size-4 mr-1 transition-transform ${input.trim() ? 'rotate-[-20deg]' : ''}`} />
                      {input.trim() ? 'Send' : 'Ask'}
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </ScrollArea>
  );
}

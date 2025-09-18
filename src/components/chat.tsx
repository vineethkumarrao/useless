"use client";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/scroll-area";
import {
  RiShining2Line,
  RiAttachment2,
  RiMicLine,
  RiLeafLine,
  RiSendPlane2Fill,
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
}

export default function Chat() {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();
  const {
    currentConversationId,
    currentMessages,
    loadConversations,
    selectConversation,
    reloadCurrentConversation,
    userId,
    isLoadingMessages,
  } = useChat();

  const messages: Message[] = currentMessages.map((msg: DBMessage) => ({
    role: msg.role as "user" | "assistant",
    content: msg.content,
  }));

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading || !currentConversationId) return;

    const userMessageContent = input;
    setInput("");
    setIsLoading(true);

    // Insert user message to Supabase
    const userMessage: DBMessage = {
      id: '', // Will be generated
      conversation_id: currentConversationId,
      user_id: userId!,
      content: userMessageContent,
      role: 'user',
      created_at: new Date().toISOString(),
      metadata: {},
    };
    // Note: Embedding not inserted here as it's frontend, backend will handle if needed

    try {
      // For now, just add to local state; backend will save during API call
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${userId}`
        },
        body: JSON.stringify({ 
          messages: [...messages, { role: "user", content: userMessageContent }],
          conversation_id: currentConversationId,
          user_id: userId || 'anonymous'
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("Full API Response:", data);

      // The backend should have saved both messages and updated conversation
      // Refresh conversations to update updated_at
      await loadConversations();

      // Reload the current conversation's messages to show the new messages from database
      if (currentConversationId) {
        await reloadCurrentConversation();
      }

      // Messages are updated via context from backend or local
      // Assuming backend returns the assistant message, but since context loads from DB, it should be fine
    } catch (error) {
      console.error("Chat error:", error);
      // Add error message locally
      const errorMessage: Message = {
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
      };
      // Would need to add to currentMessages, but for simplicity, show in UI
    } finally {
      setIsLoading(false);
    }
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
        {/* Messages start immediately, no header */}
        <div className="relative grow">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.length === 0 && (
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
                  Start a conversation by typing a message below or select from history.
                </p>
              </div>
            )}
            {messages.map((message, index) => (
              <ChatMessage key={index} isUser={message.role === "user"}>
                {message.content}
              </ChatMessage>
            ))}
            {isLoading && (
              <ChatMessage>
                <div className="flex items-center justify-start space-x-2">
                  <div className="animate-pulse bg-muted rounded-full h-2 w-2"></div>
                  <div
                    className="animate-pulse bg-muted rounded-full h-2 w-2"
                    style={{ animationDelay: "0.1s" }}
                  ></div>
                  <div
                    className="animate-pulse bg-muted rounded-full h-2 w-2"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                  <span className="text-muted-foreground">Typing...</span>
                </div>
              </ChatMessage>
            )}
            <div ref={messagesEndRef} aria-hidden="true" />
          </div>
        </div>
        {/* Footer remains unchanged */}
        <form
          onSubmit={handleSubmit}
          className="sticky bottom-0 pt-3 md:pt-6 z-50"
        >
          <div className="max-w-3xl mx-auto bg-background rounded-[20px] pb-3 md:pb-6">
            <div className="relative rounded-[20px] border border-transparent bg-muted transition-colors focus-within:bg-muted/50 focus-within:border-input has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-50 [&:has(input:is(:disabled))_*]:pointer-events-none">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="flex sm:min-h-[60px] w-full bg-transparent px-3 py-2 text-sm leading-normal text-foreground placeholder:text-muted-foreground/70 focus-visible:outline-none [resize:none]"
                placeholder="Ask me anything..."
                aria-label="Enter your prompt"
                disabled={isLoading}
              />
              <div className="flex items-center justify-between gap-2 p-2">
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    className="rounded-full size-8 border-none hover:bg-background hover:shadow-md transition-[box-shadow]"
                    disabled={isLoading}
                  >
                    <RiAttachment2
                      className="text-muted-foreground/70 size-5"
                      size={20}
                      aria-hidden="true"
                    />
                    <span className="sr-only">Attach</span>
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    className="rounded-full size-8 border-none hover:bg-background hover:shadow-md transition-[box-shadow]"
                    disabled={isLoading}
                  >
                    <RiMicLine
                      className="text-muted-foreground/70 size-5"
                      size={20}
                      aria-hidden="true"
                    />
                    <span className="sr-only">Audio</span>
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    className="rounded-full size-8 border-none hover:bg-background hover:shadow-md transition-[box-shadow]"
                    disabled={isLoading}
                  >
                    <RiLeafLine
                      className="text-muted-foreground/70 size-5"
                      size={20}
                      aria-hidden="true"
                    />
                    <span className="sr-only">Action</span>
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    className="rounded-full size-8 border-none hover:bg-background hover:shadow-md transition-[box-shadow]"
                    disabled={isLoading}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      fill="none"
                    >
                      <g clipPath="url(#icon-a)">
                        <path
                          fill="url(#icon-b)"
                          d="m8 .333 2.667 5 5 2.667-5 2.667-2.667 5-2.667-5L.333 8l5-2.667L8 .333Z"
                        />
                        <path
                          stroke="#451A03"
                          strokeOpacity=".04"
                          d="m8 1.396 2.225 4.173.072.134.134.071L14.604 8l-4.173 2.226-.134.071-.072.134L8 14.604l-2.226-4.173-.071-.134-.134-.072L1.396 8l4.173-2.226.134-.071.071-.134L8 1.396Z"
                        />
                      </g>
                      <defs>
                        <linearGradient
                          id="icon-b"
                          x1="8"
                          x2="8"
                          y1=".333"
                          y2="15.667"
                          gradientUnits="userSpaceOnUse"
                        >
                          <stop stopColor="#FDE68A" />
                          <stop offset="1" stopColor="#F59E0B" />
                        </linearGradient>
                        <clipPath id="icon-a">
                          <path fill="#fff" d="M0 0h16v16H0z" />
                        </clipPath>
                      </defs>
                    </svg>
                    <span className="sr-only">Generate</span>
                  </Button>
                  <Button
                    type="submit"
                    className="rounded-full h-8"
                    disabled={isLoading || !input.trim()}
                  >
                    {isLoading ? (
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Thinking...</span>
                      </div>
                    ) : (
                      <>
                        <RiSendPlane2Fill className="size-4 mr-1" />
                        Ask Bart
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </form>
      </div>
    </ScrollArea>
  );
}

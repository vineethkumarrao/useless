import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { supabase } from '@/lib/supabase';
import type { Conversation, Message } from '@/lib/supabase';

interface ChatContextType {
  conversations: Conversation[];
  currentConversationId: string | null;
  currentMessages: Message[];
  isLoadingConversations: boolean;
  isLoadingMessages: boolean;
  createNewConversation: () => Promise<void>;
  selectConversation: (conversationId: string) => Promise<void>;
  reloadCurrentConversation: () => Promise<void>;
  loadConversations: () => Promise<void>;
  addOptimisticMessage: (message: Message) => void;
  userId: string | null;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children, userId }: { children: ReactNode; userId: string | null }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [currentMessages, setCurrentMessages] = useState<Message[]>([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);

  const loadConversations = async () => {
    if (!userId) return;
    setIsLoadingConversations(true);
    try {
      const { data, error } = await supabase
        .from('conversations')
        .select('*')
        .eq('user_id', userId)
        .order('updated_at', { ascending: false });
      if (error) throw error;
      setConversations(data || []);
      // Set first conversation as current if none selected and list not empty
      if (!currentConversationId && data && data.length > 0) {
        setCurrentConversationId(data[0].id);
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  const createNewConversation = async () => {
    if (!userId) return;
    try {
      const { data, error } = await supabase
        .from('conversations')
        .insert({ user_id: userId, title: 'New Conversation' })
        .select()
        .single();
      if (error) throw error;
      setConversations([data, ...conversations]);
      setCurrentConversationId(data.id);
      setCurrentMessages([]);
    } catch (error) {
      console.error('Error creating conversation:', error);
    }
  };

  const reloadCurrentConversation = async () => {
    if (!userId || !currentConversationId) return;
    setIsLoadingMessages(true);
    try {
      const { data, error } = await supabase
        .from('messages')
        .select('*')
        .eq('conversation_id', currentConversationId)
        .order('created_at', { ascending: true });
      if (error) throw error;
      setCurrentMessages(data || []);
    } catch (error) {
      console.error('Error reloading messages:', error);
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const selectConversation = async (conversationId: string) => {
    if (!userId) return;
    setCurrentConversationId(conversationId);
    setIsLoadingMessages(true);
    try {
      const { data, error } = await supabase
        .from('messages')
        .select('*')
        .eq('conversation_id', conversationId)
        .order('created_at', { ascending: true });
      if (error) throw error;
      setCurrentMessages(data || []);
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const addOptimisticMessage = (message: Message) => {
    setCurrentMessages(prev => [...prev, message]);
  };

  useEffect(() => {
    if (userId) {
      loadConversations();
    }
  }, [userId]);

  useEffect(() => {
    if (currentConversationId && userId) {
      selectConversation(currentConversationId);
    }
  }, [currentConversationId, userId]);

  const value: ChatContextType = {
    conversations,
    currentConversationId,
    currentMessages,
    isLoadingConversations,
    isLoadingMessages,
    createNewConversation,
    selectConversation,
    loadConversations,
    reloadCurrentConversation,
    addOptimisticMessage,
    userId,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

'use client'

import React, { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RiNotionLine, RiCheckLine, RiLoaderLine } from '@remixicon/react'
import { useAuth } from '@/contexts/AuthContext'

interface NotionConnectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function NotionConnectDialog({ open, onOpenChange }: NotionConnectDialogProps) {
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle')
  const { user } = useAuth()

  // Check if user already has Notion connected
  useEffect(() => {
    if (open && user) {
      checkNotionConnection()
    }
  }, [open, user])

  const checkNotionConnection = async () => {
    try {
      const response = await fetch('/api/auth/notion/status', {
        headers: {
          'Authorization': `Bearer ${user?.id}` // Using user ID as simple auth for now
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setIsConnected(data.connected)
        setConnectionStatus(data.connected ? 'connected' : 'idle')
      }
    } catch (error) {
      console.error('Error checking Notion connection:', error)
    }
  }

  const handleConnectNotion = async () => {
    if (!user) {
      alert('Please login first to connect Notion')
      return
    }

    setIsConnecting(true)
    setConnectionStatus('connecting')

    try {
      // Use backend OAuth flow
      const backendAuthUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/notion/authorize?user_id=${user.id}`
      
      // Open Notion OAuth in popup
      const authWindow = window.open(
        backendAuthUrl,
        'notion-oauth',
        'width=500,height=600,scrollbars=yes,resizable=yes'
      )

      // Listen for OAuth completion
      const checkClosed = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(checkClosed)
          setIsConnecting(false)
          
          // Check connection status after OAuth window closes
          setTimeout(() => {
            checkNotionConnection()
          }, 1000)
        }
      }, 1000)

      // Listen for successful OAuth message from popup
      const handleMessage = (event: MessageEvent) => {
        // Accept messages from backend
        if (event.origin !== (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')) return
        
        if (event.data.type === 'NOTION_AUTH_SUCCESS') {
          setIsConnected(true)
          setConnectionStatus('connected')
          setIsConnecting(false)
          clearInterval(checkClosed)
          window.removeEventListener('message', handleMessage)
          onOpenChange(false)  // Close dialog
        } else if (event.data.type === 'NOTION_AUTH_ERROR') {
          console.error('Notion auth error:', event.data.error)
          setConnectionStatus('error')
          setIsConnecting(false)
          clearInterval(checkClosed)
          window.removeEventListener('message', handleMessage)
          onOpenChange(false)  // Close dialog
        }
      }

      window.addEventListener('message', handleMessage)

    } catch (error) {
      console.error('Error connecting Notion:', error)
      setIsConnecting(false)
      setConnectionStatus('error')
    }
  }

  const handleDisconnect = async () => {
    try {
      const response = await fetch('/api/auth/notion/disconnect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user?.id}`
        }
      })

      if (response.ok) {
        setIsConnected(false)
        setConnectionStatus('idle')
      }
    } catch (error) {
      console.error('Error disconnecting Notion:', error)
    }
  }

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connecting':
        return <RiLoaderLine className="animate-spin text-blue-500" size={20} />
      case 'connected':
        return <RiCheckLine className="text-green-500" size={20} />
      case 'error':
        return <RiNotionLine className="text-red-500" size={20} />
      default:
        return <RiNotionLine className="text-gray-500" size={20} />
    }
  }

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connecting':
        return 'Connecting to Notion...'
      case 'connected':
        return 'Notion Connected Successfully!'
      case 'error':
        return 'Connection Failed. Please try again.'
      default:
        return 'Connect your Notion workspace to enable integration'
    }
  }

  const getDescription = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Your Notion workspace is connected. You can now create, edit, and manage pages, databases, and content through our AI assistant.'
      case 'error':
        return 'There was an error connecting to Notion. Please ensure you have granted the necessary permissions and try again.'
      default:
        return 'Connect your Notion workspace to enable powerful knowledge management features. Our AI can help you create pages, manage databases, organize content, and collaborate on your Notion workspace efficiently.'
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              {getStatusIcon()}
              <span>Notion Integration</span>
            </DialogTitle>
            <DialogDescription className="pt-2">
              {getDescription()}
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex flex-col gap-4 py-4">
            <div className="text-sm text-muted-foreground">
              {getStatusText()}
            </div>
            
            {connectionStatus === 'connected' ? (
              <div className="space-y-3">
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2 text-green-800">
                    <RiCheckLine size={16} />
                    <span className="font-medium">Successfully Connected</span>
                  </div>
                  <p className="text-sm text-green-700 mt-1">
                    Your Notion workspace is now integrated with our AI assistant.
                  </p>
                </div>
                <Button 
                  variant="outline" 
                  onClick={handleDisconnect}
                  className="w-full"
                >
                  Disconnect Notion
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">Workspace Permissions</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Read pages and databases</li>
                    <li>• Create and update content</li>
                    <li>• Manage page properties and structure</li>
                    <li>• Access and organize workspace content</li>
                  </ul>
                </div>
                <Button 
                  onClick={handleConnectNotion} 
                  disabled={isConnecting}
                  className="w-full"
                >
                  {isConnecting ? (
                    <>
                      <RiLoaderLine className="mr-2 animate-spin" size={16} />
                      Connecting...
                    </>
                  ) : (
                    <>
                      <RiNotionLine className="mr-2" size={16} />
                      Connect Notion
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
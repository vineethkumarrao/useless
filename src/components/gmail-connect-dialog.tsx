'use client'

import React, { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RiMailLine, RiCheckLine, RiLoaderLine } from '@remixicon/react'
import { useAuth } from '@/contexts/AuthContext'

interface GmailConnectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function GmailConnectDialog({ open, onOpenChange }: GmailConnectDialogProps) {
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle')
  const { user } = useAuth()

  // Check if user already has Gmail connected
  useEffect(() => {
    if (open && user) {
      checkGmailConnection()
    }
  }, [open, user])

  const checkGmailConnection = async () => {
    try {
      const response = await fetch('/api/auth/gmail/status', {
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
      console.error('Error checking Gmail connection:', error)
    }
  }

  const handleConnectGmail = async () => {
    if (!user) {
      alert('Please login first to connect Gmail')
      return
    }

    setIsConnecting(true)
    setConnectionStatus('connecting')

    try {
      // Use backend OAuth flow (should work with existing Google Console config)
      const backendAuthUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/gmail/authorize?user_id=${user.id}`
      
      // Open Google OAuth in popup - backend will redirect to Google
      const authWindow = window.open(
        backendAuthUrl,
        'gmail-oauth',
        'width=500,height=600,scrollbars=yes,resizable=yes'
      )

      // Listen for OAuth completion
      const checkClosed = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(checkClosed)
          setIsConnecting(false)
          
          // Check connection status after OAuth window closes
          setTimeout(() => {
            checkGmailConnection()
          }, 1000)
        }
      }, 1000)

      // Listen for successful OAuth message from popup
      const handleMessage = (event: MessageEvent) => {
        // Accept messages from backend
        if (event.origin !== (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')) return
        
        if (event.data.type === 'GMAIL_AUTH_SUCCESS') {
          setIsConnected(true)
          setConnectionStatus('connected')
          setIsConnecting(false)
          authWindow?.close()
          clearInterval(checkClosed)
          window.removeEventListener('message', handleMessage)
        } else if (event.data.type === 'GMAIL_AUTH_ERROR') {
          console.error('Gmail auth error:', event.data.error)
          setConnectionStatus('error')
          setIsConnecting(false)
          authWindow?.close()
          clearInterval(checkClosed)
          window.removeEventListener('message', handleMessage)
        }
      }

      window.addEventListener('message', handleMessage)

    } catch (error) {
      console.error('Error connecting Gmail:', error)
      setIsConnecting(false)
      setConnectionStatus('error')
    }
  }

  const handleDisconnect = async () => {
    try {
      const response = await fetch('/api/auth/gmail/disconnect', {
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
      console.error('Error disconnecting Gmail:', error)
    }
  }

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connecting':
        return <RiLoaderLine className="animate-spin text-blue-500" size={20} />
      case 'connected':
        return <RiCheckLine className="text-green-500" size={20} />
      case 'error':
        return <RiMailLine className="text-red-500" size={20} />
      default:
        return <RiMailLine className="text-gray-500" size={20} />
    }
  }

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connecting':
        return 'Connecting to Gmail...'
      case 'connected':
        return 'Gmail Connected Successfully!'
      case 'error':
        return 'Connection Failed. Please try again.'
      default:
        return 'Connect your Gmail account to enable email integration'
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getStatusIcon()}
            Gmail Integration
          </DialogTitle>
          <DialogDescription>
            {getStatusText()}
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex flex-col items-center space-y-4 py-4">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
            <RiMailLine size={32} className="text-red-600" />
          </div>
          
          {connectionStatus === 'connected' ? (
            <div className="text-center space-y-4">
              <p className="text-sm text-green-600 font-medium">
                ✅ Your Gmail account is connected and ready to use
              </p>
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleDisconnect}>
                  Disconnect
                </Button>
                <Button onClick={() => onOpenChange(false)}>
                  Done
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-center space-y-4">
              <p className="text-sm text-gray-600">
                Allow access to your Gmail account to enable:
              </p>
              <ul className="text-sm text-gray-500 space-y-1">
                <li>• Read and summarize emails</li>
                <li>• Send emails on your behalf</li>
                <li>• Manage email labels and filters</li>
                <li>• Search and organize messages</li>
              </ul>
              
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleConnectGmail} 
                  disabled={isConnecting}
                  className="bg-red-600 hover:bg-red-700"
                >
                  {isConnecting ? (
                    <>
                      <RiLoaderLine className="animate-spin mr-2" size={16} />
                      Connecting...
                    </>
                  ) : (
                    <>
                      <RiMailLine className="mr-2" size={16} />
                      Connect Gmail
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
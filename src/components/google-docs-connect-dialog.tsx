'use client'

import React, { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RiFileTextLine, RiCheckLine, RiLoaderLine } from '@remixicon/react'
import { useAuth } from '@/contexts/AuthContext'

interface GoogleDocsConnectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function GoogleDocsConnectDialog({ open, onOpenChange }: GoogleDocsConnectDialogProps) {
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle')
  const { user } = useAuth()

  // Check if user already has Google Docs connected
  useEffect(() => {
    if (open && user) {
      checkDocsConnection()
    }
  }, [open, user])

  const checkDocsConnection = async () => {
    try {
      const response = await fetch('/api/auth/google-docs/status', {
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
      console.error('Error checking Google Docs connection:', error)
    }
  }

  const handleConnectDocs = async () => {
    if (!user) {
      alert('Please login first to connect Google Docs')
      return
    }

    setIsConnecting(true)
    setConnectionStatus('connecting')

    try {
      // Use backend OAuth flow
      const backendAuthUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/google-docs/authorize?user_id=${user.id}`
      
      // Open Google OAuth in popup
      const authWindow = window.open(
        backendAuthUrl,
        'google-docs-oauth',
        'width=500,height=600,scrollbars=yes,resizable=yes'
      )

      if (!authWindow) {
        throw new Error('Popup blocked by browser. Please allow popups for this site.')
      }

      // Set a timeout for the OAuth process (5 minutes max)
      const maxWaitTime = 300000; // 5 minutes
      const timeoutId = setTimeout(() => {
        setIsConnecting(false)
        setConnectionStatus('error')
        // Don't call close() here to avoid COOP issues
        // Clean up listeners
        window.removeEventListener('message', handleMessage)
        console.warn('OAuth timeout reached')
      }, maxWaitTime)

      // Listen for OAuth completion
      const handleMessage = (event: MessageEvent) => {
        // Allow messages from backend origin
        const backendOrigin = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        if (event.origin !== backendOrigin && event.origin !== window.location.origin) return
        
        console.log('Received message:', event.data)
        
        if (event.data.type === 'GOOGLE_DOCS_AUTH_SUCCESS') {
          console.log('Google Docs auth success:', event.data)
          setIsConnected(true)
          setConnectionStatus('connected')
          setIsConnecting(false)
          clearTimeout(timeoutId)
          window.removeEventListener('message', handleMessage)
          // Don't close the window here - let the backend HTML handle it
        } else if (event.data.type === 'GOOGLE_DOCS_AUTH_ERROR') {
          console.error('Google Docs auth error:', event.data.error)
          setConnectionStatus('error')
          setIsConnecting(false)
          clearTimeout(timeoutId)
          window.removeEventListener('message', handleMessage)
          // Don't close the window here
        }
      }

      window.addEventListener('message', handleMessage)

      // No periodic checks - rely on message and timeout only

    } catch (error) {
      console.error('Error connecting Google Docs:', error)
      setIsConnecting(false)
      setConnectionStatus('error')
    }
  }

  const handleDisconnect = async () => {
    try {
      const response = await fetch('/api/auth/google-docs/disconnect', {
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
      console.error('Error disconnecting Google Docs:', error)
    }
  }

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connecting':
        return <RiLoaderLine className="animate-spin text-blue-500" size={20} />
      case 'connected':
        return <RiCheckLine className="text-green-500" size={20} />
      case 'error':
        return <RiFileTextLine className="text-red-500" size={20} />
      default:
        return <RiFileTextLine className="text-gray-500" size={20} />
    }
  }

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connecting':
        return 'Connecting to Google Docs...'
      case 'connected':
        return 'Google Docs Connected Successfully!'
      case 'error':
        return 'Connection Failed. Please try again.'
      default:
        return 'Connect your Google Docs to enable document integration'
    }
  }

  const getDescription = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Your Google Docs is connected. You can now create, edit, and manage documents through our AI assistant.'
      case 'error':
        return 'There was an error connecting to Google Docs. Please ensure you have granted the necessary permissions and try again.'
      default:
        return 'Connect your Google Docs to enable powerful document management features. Our AI can help you create documents, edit content, format text, and collaborate on documents efficiently.'
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              {getStatusIcon()}
              <span>Google Docs Integration</span>
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
                    Your Google Docs is now integrated with our AI assistant.
                  </p>
                </div>
                <Button 
                  variant="outline" 
                  onClick={handleDisconnect}
                  className="w-full"
                >
                  Disconnect Google Docs
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">Document Permissions</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Read your documents</li>
                    <li>• Create and edit documents</li>
                    <li>• Manage document formatting</li>
                    <li>• Share and collaborate on documents</li>
                  </ul>
                </div>
                <Button 
                  onClick={handleConnectDocs} 
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
                      <RiFileTextLine className="mr-2" size={16} />
                      Connect Google Docs
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
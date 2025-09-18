'use client'

import React, { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RiCalendarLine, RiCheckLine, RiLoaderLine } from '@remixicon/react'
import { useAuth } from '@/contexts/AuthContext'

interface GoogleCalendarConnectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function GoogleCalendarConnectDialog({ open, onOpenChange }: GoogleCalendarConnectDialogProps) {
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle')
  const { user } = useAuth()

  // Check if user already has Google Calendar connected
  useEffect(() => {
    if (open && user) {
      checkCalendarConnection()
    }
  }, [open, user])

  const checkCalendarConnection = async () => {
    try {
      const response = await fetch('/api/auth/google-calendar/status', {
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
      console.error('Error checking Google Calendar connection:', error)
    }
  }

  const handleConnectCalendar = async () => {
    if (!user) {
      alert('Please login first to connect Google Calendar')
      return
    }

    setIsConnecting(true)
    setConnectionStatus('connecting')

    try {
      // Use backend OAuth flow
      const backendAuthUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/google-calendar/authorize?user_id=${user.id}`
      
      // Open Google OAuth in popup
      const authWindow = window.open(
        backendAuthUrl,
        'google-calendar-oauth',
        'width=500,height=600,scrollbars=yes,resizable=yes'
      )

      // Listen for OAuth completion
      const checkClosed = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(checkClosed)
          setIsConnecting(false)
          
          // Check connection status after OAuth window closes
          setTimeout(() => {
            checkCalendarConnection()
          }, 1000)
        }
      }, 1000)

      // Listen for successful OAuth message from popup
      const handleMessage = (event: MessageEvent) => {
        // Accept messages from backend
        if (event.origin !== (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')) return
        
        if (event.data.type === 'GOOGLE_CALENDAR_AUTH_SUCCESS') {
          setIsConnected(true)
          setConnectionStatus('connected')
          setIsConnecting(false)
          authWindow?.close()
          clearInterval(checkClosed)
          window.removeEventListener('message', handleMessage)
        } else if (event.data.type === 'GOOGLE_CALENDAR_AUTH_ERROR') {
          console.error('Google Calendar auth error:', event.data.error)
          setConnectionStatus('error')
          setIsConnecting(false)
          authWindow?.close()
          clearInterval(checkClosed)
          window.removeEventListener('message', handleMessage)
        }
      }

      window.addEventListener('message', handleMessage)

    } catch (error) {
      console.error('Error connecting Google Calendar:', error)
      setIsConnecting(false)
      setConnectionStatus('error')
    }
  }

  const handleDisconnect = async () => {
    try {
      const response = await fetch('/api/auth/google-calendar/disconnect', {
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
      console.error('Error disconnecting Google Calendar:', error)
    }
  }

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connecting':
        return <RiLoaderLine className="animate-spin text-blue-500" size={20} />
      case 'connected':
        return <RiCheckLine className="text-green-500" size={20} />
      case 'error':
        return <RiCalendarLine className="text-red-500" size={20} />
      default:
        return <RiCalendarLine className="text-gray-500" size={20} />
    }
  }

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connecting':
        return 'Connecting to Google Calendar...'
      case 'connected':
        return 'Google Calendar Connected Successfully!'
      case 'error':
        return 'Connection Failed. Please try again.'
      default:
        return 'Connect your Google Calendar to enable calendar integration'
    }
  }

  const getDescription = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Your Google Calendar is connected. You can now access your calendar events, create new events, and manage your schedule through our AI assistant.'
      case 'error':
        return 'There was an error connecting to Google Calendar. Please ensure you have granted the necessary permissions and try again.'
      default:
        return 'Connect your Google Calendar to enable powerful calendar management features. Our AI can help you schedule meetings, check availability, create events, and manage your calendar efficiently.'
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              {getStatusIcon()}
              <span>Google Calendar Integration</span>
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
                    Your Google Calendar is now integrated with our AI assistant.
                  </p>
                </div>
                <Button 
                  variant="outline" 
                  onClick={handleDisconnect}
                  className="w-full"
                >
                  Disconnect Google Calendar
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">Calendar Permissions</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Read your calendar events</li>
                    <li>• Create and update events</li>
                    <li>• Manage your calendar settings</li>
                    <li>• Check availability and schedule meetings</li>
                  </ul>
                </div>
                <Button 
                  onClick={handleConnectCalendar} 
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
                      <RiCalendarLine className="mr-2" size={16} />
                      Connect Google Calendar
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
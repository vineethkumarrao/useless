'use client'

import React, { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RiGithubLine, RiCheckLine, RiLoaderLine } from '@remixicon/react'
import { useAuth } from '@/contexts/AuthContext'

interface GitHubConnectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function GitHubConnectDialog({ open, onOpenChange }: GitHubConnectDialogProps) {
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle')
  const { user } = useAuth()

  // Check if user already has GitHub connected
  useEffect(() => {
    if (open && user) {
      checkGitHubConnection()
    }
  }, [open, user])

  const checkGitHubConnection = async () => {
    try {
      const response = await fetch('/api/auth/github/status', {
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
      console.error('Error checking GitHub connection:', error)
    }
  }

  const handleConnectGitHub = async () => {
    if (!user) {
      alert('Please login first to connect GitHub')
      return
    }

    setIsConnecting(true)
    setConnectionStatus('connecting')

    try {
      // Use backend OAuth flow
      const backendAuthUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/github/authorize?user_id=${user.id}`
      
      // Open GitHub OAuth in popup
      const authWindow = window.open(
        backendAuthUrl,
        'github-oauth',
        'width=500,height=600,scrollbars=yes,resizable=yes'
      )

      // Listen for OAuth completion
      const checkClosed = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(checkClosed)
          setIsConnecting(false)
          
          // Check connection status after OAuth window closes
          setTimeout(() => {
            checkGitHubConnection()
          }, 1000)
        }
      }, 1000)

      // Listen for successful OAuth message from popup
      const handleMessage = (event: MessageEvent) => {
        // Accept messages from backend
        if (event.origin !== (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')) return
        
        if (event.data.type === 'GITHUB_AUTH_SUCCESS') {
          setIsConnected(true)
          setConnectionStatus('connected')
          setIsConnecting(false)
          clearInterval(checkClosed)
          window.removeEventListener('message', handleMessage)
          onOpenChange(false)  // Close dialog
        } else if (event.data.type === 'GITHUB_AUTH_ERROR') {
          console.error('GitHub auth error:', event.data.error)
          setConnectionStatus('error')
          setIsConnecting(false)
          clearInterval(checkClosed)
          window.removeEventListener('message', handleMessage)
          onOpenChange(false)  // Close dialog
        }
      }

      window.addEventListener('message', handleMessage)

    } catch (error) {
      console.error('Error connecting GitHub:', error)
      setIsConnecting(false)
      setConnectionStatus('error')
    }
  }

  const handleDisconnect = async () => {
    try {
      const response = await fetch('/api/auth/github/disconnect', {
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
      console.error('Error disconnecting GitHub:', error)
    }
  }

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connecting':
        return <RiLoaderLine className="animate-spin text-blue-500" size={20} />
      case 'connected':
        return <RiCheckLine className="text-green-500" size={20} />
      case 'error':
        return <RiGithubLine className="text-red-500" size={20} />
      default:
        return <RiGithubLine className="text-gray-500" size={20} />
    }
  }

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connecting':
        return 'Connecting to GitHub...'
      case 'connected':
        return 'GitHub Connected Successfully!'
      case 'error':
        return 'Connection Failed. Please try again.'
      default:
        return 'Connect your GitHub account to enable repository integration'
    }
  }

  const getDescription = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Your GitHub account is connected. You can now manage repositories, create issues, review code, and collaborate on projects through our AI assistant.'
      case 'error':
        return 'There was an error connecting to GitHub. Please ensure you have granted the necessary permissions and try again.'
      default:
        return 'Connect your GitHub account to enable powerful development workflow features. Our AI can help you manage repositories, create issues, review pull requests, analyze code, and streamline your development process.'
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              {getStatusIcon()}
              <span>GitHub Integration</span>
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
                    Your GitHub account is now integrated with our AI assistant.
                  </p>
                </div>
                <Button 
                  variant="outline" 
                  onClick={handleDisconnect}
                  className="w-full"
                >
                  Disconnect GitHub
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">Repository Permissions</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Access public and private repositories</li>
                    <li>• Create and manage issues</li>
                    <li>• Review and create pull requests</li>
                    <li>• Read and write repository content</li>
                  </ul>
                </div>
                <Button 
                  onClick={handleConnectGitHub} 
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
                      <RiGithubLine className="mr-2" size={16} />
                      Connect GitHub
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
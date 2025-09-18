'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import axios from 'axios'

interface AuthUser {
  id: string
  email: string
  full_name: string
}

interface AuthContextType {
  user: AuthUser | null
  session: any | null
  loading: boolean
  signUp: (email: string, password: string, fullName: string) => Promise<any>
  signIn: (email: string, password: string) => Promise<any>
  signOut: () => Promise<void>
  requestOTP: (email: string, password: string, fullName: string) => Promise<any>
  verifyOTP: (email: string, otpCode: string) => Promise<any>
  completeSignup: (email: string, password: string, fullName: string, otpId: string) => Promise<any>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [session, setSession] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    // Check if user is logged in by checking local storage
    const storedUser = localStorage.getItem('auth_user')
    const storedSession = localStorage.getItem('auth_session')
    
    if (storedUser && storedSession) {
      try {
        setUser(JSON.parse(storedUser))
        setSession(JSON.parse(storedSession))
      } catch (error) {
        console.error('Error parsing stored auth data:', error)
        localStorage.removeItem('auth_user')
        localStorage.removeItem('auth_session')
      }
    }
    
    setLoading(false)
  }, [])

  const requestOTP = async (email: string, password: string, fullName: string) => {
    try {
      const response = await axios.post(`${API_URL}/auth/signup/request-otp`, {
        email,
        password,
        full_name: fullName
      })
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to request OTP')
    }
  }

  const verifyOTP = async (email: string, otpCode: string) => {
    try {
      const response = await axios.post(`${API_URL}/auth/signup/verify-otp`, {
        email,
        otp_code: otpCode
      })
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to verify OTP')
    }
  }

  const completeSignup = async (email: string, password: string, fullName: string, otpId: string) => {
    try {
      const response = await axios.post(`${API_URL}/auth/signup/complete`, {
        email,
        password,
        full_name: fullName,
        otp_id: otpId
      })

      if (response.data.success) {
        const userData = response.data.user
        const sessionData = response.data.session

        setUser(userData)
        setSession(sessionData)
        
        // Store in localStorage
        localStorage.setItem('auth_user', JSON.stringify(userData))
        localStorage.setItem('auth_session', JSON.stringify(sessionData))

        return response.data
      } else {
        throw new Error(response.data.message || 'Signup failed')
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to complete signup')
    }
  }

  const signUp = async (email: string, password: string, fullName: string) => {
    // This is a wrapper that handles the full signup flow
    // For now, just call requestOTP - the UI will handle the flow
    return requestOTP(email, password, fullName)
  }

  const signIn = async (email: string, password: string) => {
    try {
      const response = await axios.post(`${API_URL}/auth/signin`, {
        email,
        password
      })

      if (response.data.success) {
        const userData = response.data.user
        const sessionData = response.data.session

        setUser(userData)
        setSession(sessionData)
        
        // Store in localStorage
        localStorage.setItem('auth_user', JSON.stringify(userData))
        localStorage.setItem('auth_session', JSON.stringify(sessionData))

        return response.data
      } else {
        throw new Error(response.data.message || 'Login failed')
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to sign in')
    }
  }

  const signOut = async () => {
    try {
      // Try to call the backend signout endpoint if we have a session
      if (session?.access_token) {
        await axios.post(`${API_URL}/auth/signout`, {
          access_token: session.access_token
        })
      }
    } catch (error) {
      console.error('Error signing out from backend:', error)
    } finally {
      // Always clear local state
      setUser(null)
      setSession(null)
      localStorage.removeItem('auth_user')
      localStorage.removeItem('auth_session')
    }
  }

  const value = {
    user,
    session,
    loading,
    signUp,
    signIn,
    signOut,
    requestOTP,
    verifyOTP,
    completeSignup
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
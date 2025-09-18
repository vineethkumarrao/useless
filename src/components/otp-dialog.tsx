'use client'

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/contexts/AuthContext"

const otpSchema = z.object({
  otpCode: z.string().min(6, "OTP must be 6 digits").max(6, "OTP must be 6 digits")
})

type OTPFormData = z.infer<typeof otpSchema>

interface OTPDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  email: string
  password: string
  fullName: string
  onSuccess: () => void
}

export function OTPDialog({ open, onOpenChange, email, password, fullName, onSuccess }: OTPDialogProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [otpId, setOtpId] = useState("")
  
  const { verifyOTP, completeSignup } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm<OTPFormData>({
    resolver: zodResolver(otpSchema)
  })

  const onSubmit = async (data: OTPFormData) => {
    setLoading(true)
    setError("")

    try {
      // First verify the OTP
      const verifyResult = await verifyOTP(email, data.otpCode)
      
      if (verifyResult.success) {
        // Then complete the signup
        const signupResult = await completeSignup(email, password, fullName, verifyResult.otp_id)
        
        if (signupResult.success) {
          reset()
          onSuccess()
          onOpenChange(false)
        } else {
          setError("Failed to create account. Please try again.")
        }
      } else {
        setError("Invalid OTP. Please check your email and try again.")
      }
    } catch (err: any) {
      setError(err.message || "Verification failed. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleResendOTP = async () => {
    // This would trigger a new OTP request
    // You might want to implement this functionality
    setError("Resend functionality not implemented yet")
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <div className="flex flex-col items-center gap-2">
          <div
            className="flex size-11 shrink-0 items-center justify-center rounded-full border"
            aria-hidden="true"
          >
            <svg
              className="stroke-zinc-800 dark:stroke-zinc-100"
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 32 32"
              aria-hidden="true"
            >
              <circle cx="16" cy="16" r="12" fill="none" strokeWidth="8" />
            </svg>
          </div>
          <DialogHeader>
            <DialogTitle className="sm:text-center">Verify your email</DialogTitle>
            <DialogDescription className="sm:text-center">
              We've sent a 6-digit code to {email}. Please enter it below.
            </DialogDescription>
          </DialogHeader>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {error && (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded">
              {error}
            </div>
          )}
          
          <div className="space-y-4">
            <div className="*:not-first:mt-2">
              <Label htmlFor="otpCode">Verification Code</Label>
              <Input
                id="otpCode"
                placeholder="Enter 6-digit code"
                type="text"
                maxLength={6}
                {...register("otpCode")}
                disabled={loading}
                className="text-center text-lg tracking-widest"
              />
              {errors.otpCode && (
                <p className="text-sm text-red-600">{errors.otpCode.message}</p>
              )}
            </div>
          </div>
          
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Verifying..." : "Verify and Create Account"}
          </Button>
          
          <div className="text-center">
            <button
              type="button"
              onClick={handleResendOTP}
              className="text-sm text-blue-600 hover:underline"
              disabled={loading}
            >
              Didn't receive the code? Resend
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
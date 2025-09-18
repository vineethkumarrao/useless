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
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/contexts/AuthContext"
import { OTPDialog } from "@/components/otp-dialog"

const signupSchema = z.object({
  fullName: z.string().min(2, "Full name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters")
})

type SignupFormData = z.infer<typeof signupSchema>

export function SignupDialog() {
  const [open, setOpen] = useState(false)
  const [otpDialogOpen, setOtpDialogOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [signupData, setSignupData] = useState<SignupFormData | null>(null)
  
  const { signUp } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema)
  })

  const onSubmit = async (data: SignupFormData) => {
    setLoading(true)
    setError("")

    try {
      const result = await signUp(data.email, data.password, data.fullName)
      
      if (result.success && result.step === 'otp_sent') {
        setSignupData(data)
        setOpen(false)
        setOtpDialogOpen(true)
      }
    } catch (err: any) {
      setError(err.message || "Signup failed. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleOTPSuccess = () => {
    reset()
    setSignupData(null)
    setOtpDialogOpen(false)
    // User is now signed in via the auth context
  }

  const handleGoogleSignup = () => {
    // Implement Google OAuth signup
    setError("Google signup not implemented yet")
  }

  return (
    <>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button size="sm">Sign up</Button>
        </DialogTrigger>
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
              <DialogTitle className="sm:text-center">Create your account</DialogTitle>
              <DialogDescription className="sm:text-center">
                We just need a few details to get you started.
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
                <Label htmlFor="fullName">Full name</Label>
                <Input
                  id="fullName"
                  placeholder="Matt Welsh"
                  type="text"
                  {...register("fullName")}
                  disabled={loading}
                />
                {errors.fullName && (
                  <p className="text-sm text-red-600">{errors.fullName.message}</p>
                )}
              </div>
              <div className="*:not-first:mt-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  placeholder="hi@yourcompany.com"
                  type="email"
                  {...register("email")}
                  disabled={loading}
                />
                {errors.email && (
                  <p className="text-sm text-red-600">{errors.email.message}</p>
                )}
              </div>
              <div className="*:not-first:mt-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  placeholder="Enter your password"
                  type="password"
                  {...register("password")}
                  disabled={loading}
                />
                {errors.password && (
                  <p className="text-sm text-red-600">{errors.password.message}</p>
                )}
              </div>
            </div>
            
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Creating account..." : "Sign up"}
            </Button>
          </form>

          <div className="before:bg-border after:bg-border flex items-center gap-3 before:h-px before:flex-1 after:h-px after:flex-1">
            <span className="text-muted-foreground text-xs">Or</span>
          </div>

          <Button variant="outline" onClick={handleGoogleSignup} disabled={loading}>
            Continue with Google
          </Button>

          <p className="text-muted-foreground text-center text-xs">
            By signing up you agree to our{" "}
            <a className="underline hover:no-underline" href="#">
              Terms
            </a>
            .
          </p>
        </DialogContent>
      </Dialog>

      {signupData && (
        <OTPDialog
          open={otpDialogOpen}
          onOpenChange={setOtpDialogOpen}
          email={signupData.email}
          password={signupData.password}
          fullName={signupData.fullName}
          onSuccess={handleOTPSuccess}
        />
      )}
    </>
  )
}

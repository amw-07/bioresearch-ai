'use client';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
 import Link from'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
 import * as z from'zod';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { authService } from '@/lib/api/auth-service';
import { useToast } from '@/components/ui/use-toast';
import { Loader2, Microscope } from 'lucide-react';
import { useState } from 'react';

const emailSchema = z.object({ email: z.string().email('Invalid email') })
const resetSchema = z.object({
  password: z.string().min(8, 'At least 8 characters'),
  confirm: z.string(),
}).refine(d => d.password === d.confirm, { message: "Passwords don't match", path: ['confirm'] })

type EmailForm = z.infer<typeof emailSchema>
type ResetForm = z.infer<typeof resetSchema>

function ResetPasswordContent() {
  const params = useSearchParams()
  const token = params.get('token')
  const { toast } = useToast()
  const [sent, setSent] = useState(false)

  const emailForm = useForm<EmailForm>({ resolver: zodResolver(emailSchema) })
  const resetForm = useForm<ResetForm>({ resolver: zodResolver(resetSchema) })

  const inputCls = 'bg-[rgba(255,255,255,0.04)] border-[rgba(255,255,255,0.08)] text-zinc-100 placeholder:text-zinc-700 focus:border-[rgba(0,214,143,0.4)] transition-colors'

  if (token) {
    return (
      <div className="w-full max-w-sm animate-fade-up">
        <div className="rounded-2xl border p-8" style={{ background: 'rgba(11,18,36,0.88)', backdropFilter: 'blur(24px)', borderColor: 'rgba(0,214,143,0.12)' }}>
          <h1 className="font-syne text-2xl font-700 text-white mb-6">Set new password</h1>
          <form onSubmit={resetForm.handleSubmit(async (d) => {
            try {
              await authService.resetPassword(token, d.password)
              toast({ title: 'Password reset', description: 'You can now sign in.' })
            } catch {
              toast({ title: 'Error', description: 'Invalid or expired token.', variant: 'destructive' })
            }
          })} className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-xs uppercase tracking-widest text-zinc-500">New password</Label>
              <Input type="password" placeholder="••••••••" {...resetForm.register('password')} className={inputCls} />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs uppercase tracking-widest text-zinc-500">Confirm password</Label>
              <Input type="password" placeholder="••••••••" {...resetForm.register('confirm')} className={inputCls} />
              {resetForm.formState.errors.confirm && <p className="text-xs text-red-400">{resetForm.formState.errors.confirm.message}</p>}
            </div>
            <button type="submit" className="w-full rounded-xl py-3 text-sm font-syne font-600" style={{ background: '#00d68f', color: 'hsl(222,47%,4%)' }}>
              Reset password
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-sm animate-fade-up">
      <div className="flex items-center justify-center gap-3 mb-8">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[rgba(0,214,143,0.3)] bg-[rgba(0,214,143,0.1)]">
          <Microscope className="h-5 w-5 text-[#00d68f]" />
        </div>
        <p className="font-syne font-700 text-white text-base">BioResearch AI</p>
      </div>
      <div className="rounded-2xl border p-8" style={{ background: 'rgba(11,18,36,0.88)', backdropFilter: 'blur(24px)', borderColor: 'rgba(0,214,143,0.12)' }}>
        {sent ? (
          <div className="text-center space-y-3">
            <p className="font-syne text-xl text-white">Check your email</p>
            <p className="text-sm text-zinc-500">We sent a reset link to your inbox.</p>
            <Link href="/login" className="text-sm text-[#00d68f] hover:underline">Back to sign in</Link>
          </div>
        ) : (
          <>
            <h1 className="font-syne text-2xl font-700 text-white mb-2">Reset password</h1>
            <p className="text-sm text-zinc-500 mb-6">Enter your email and we&apos;ll send a reset link.</p>
            <form onSubmit={emailForm.handleSubmit(async (d) => {
              try {
                await authService.requestPasswordReset(d.email)
                setSent(true)
              } catch {
                toast({ title: 'Error', description: 'Could not send reset email.', variant: 'destructive' })
              }
            })} className="space-y-4">
              <div className="space-y-1.5">
                <Label className="text-xs uppercase tracking-widest text-zinc-500">Email</Label>
                <Input type="email" placeholder="you@example.com" {...emailForm.register('email')} className={inputCls} />
                {emailForm.formState.errors.email && <p className="text-xs text-red-400">{emailForm.formState.errors.email.message}</p>}
              </div>
              <button type="submit" disabled={emailForm.formState.isSubmitting} className="w-full flex items-center justify-center gap-2 rounded-xl py-3 text-sm font-syne font-600 disabled:opacity-60" style={{ background: '#00d68f', color: 'hsl(222,47%,4%)' }}>
                {emailForm.formState.isSubmitting ? <><Loader2 className="h-4 w-4 animate-spin" /> Sending…</> : 'Send reset link'}
              </button>
            </form>
            <p className="text-center text-xs text-zinc-600 mt-6">
              <Link href="/login" className="text-[#00d68f] hover:underline">Back to sign in</Link>
            </p>
          </>
        )}
      </div>
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div />}>
      <ResetPasswordContent />
    </Suspense>
  )
}

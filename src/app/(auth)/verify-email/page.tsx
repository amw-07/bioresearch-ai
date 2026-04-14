'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
 import Link from'next/link';
import { authService } from '@/lib/api/auth-service';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

function VerifyEmailContent() {
  const params = useSearchParams()
  const token = params?.get('token')
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')

  useEffect(() => {
    if (!token) { setStatus('error'); return }
    authService?.verifyEmail(token)?.then(() => setStatus('success'))?.catch(() => setStatus('error'))
  }, [token])

  return (
    <div className="w-full max-w-sm animate-fade-up">
      <div className="rounded-2xl border p-8 text-center" style={{ background: 'rgba(11,18,36,0.88)', backdropFilter: 'blur(24px)', borderColor: 'rgba(0,214,143,0.12)' }}>
        {status === 'loading' && <><Loader2 className="h-8 w-8 animate-spin text-[#00d68f] mx-auto mb-4" /><p className="text-zinc-400">Verifying your email…</p></>}
        {status === 'success' && <><CheckCircle className="h-8 w-8 text-[#00d68f] mx-auto mb-4" /><p className="font-syne text-xl text-white mb-2">Email verified!</p><p className="text-sm text-zinc-500 mb-4">Your account is now active.</p><Link href="/login" className="text-[#00d68f] hover:underline text-sm">Sign in →</Link></>}
        {status === 'error' && <><XCircle className="h-8 w-8 text-red-400 mx-auto mb-4" /><p className="font-syne text-xl text-white mb-2">Verification failed</p><p className="text-sm text-zinc-500 mb-4">The link may be invalid or expired.</p><Link href="/login" className="text-[#00d68f] hover:underline text-sm">Back to sign in</Link></>}
      </div>
    </div>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div />}>
      <VerifyEmailContent />
    </Suspense>
  )
}

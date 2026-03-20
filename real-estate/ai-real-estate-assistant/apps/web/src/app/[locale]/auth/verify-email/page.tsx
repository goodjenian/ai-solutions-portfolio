'use client';

import { Suspense, useEffect, useReducer } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2, CheckCircle2, XCircle, ArrowLeft } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { verifyEmail } from '@/lib/auth';

type State = {
  status: 'loading' | 'success' | 'error';
  error: string | null;
};

type Action = { type: 'SUCCESS' } | { type: 'ERROR'; error: string };

function reducer(_state: State, action: Action): State {
  switch (action.type) {
    case 'SUCCESS':
      return { status: 'success', error: null };
    case 'ERROR':
      return { status: 'error', error: action.error };
    default:
      return _state;
  }
}

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Get token and derive initial validation state
  const token = searchParams.get('token');
  const hasValidToken = Boolean(token);

  // Use reducer to avoid setState in effect
  const [state, dispatch] = useReducer(reducer, {
    status: hasValidToken ? 'loading' : 'error',
    error: hasValidToken ? null : 'Invalid or missing verification token',
  });

  // Only make API call if we have a valid token
  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    verifyEmail(token)
      .then(() => {
        if (!cancelled) {
          dispatch({ type: 'SUCCESS' });
        }
      })
      .catch((err) => {
        if (!cancelled) {
          dispatch({
            type: 'ERROR',
            error: err instanceof Error ? err.message : 'Failed to verify email',
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  if (state.status === 'loading') {
    return (
      <Card className="w-full max-w-sm">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="mt-4 text-sm text-muted-foreground">Verifying your email...</p>
        </CardContent>
      </Card>
    );
  }

  if (state.status === 'success') {
    return (
      <Card className="w-full max-w-sm">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-2">
            <div className="rounded-full bg-green-100 dark:bg-green-900/20 p-3">
              <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <CardTitle className="text-2xl">Email verified</CardTitle>
          <CardDescription>Your email has been verified successfully</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-center text-muted-foreground">
            You can now log in to your account.
          </p>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button className="w-full" onClick={() => router.push('/auth/login')}>
            Go to login
          </Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader className="space-y-1 text-center">
        <div className="flex justify-center mb-2">
          <div className="rounded-full bg-destructive/15 p-3">
            <XCircle className="h-6 w-6 text-destructive" />
          </div>
        </div>
        <CardTitle className="text-2xl">Verification failed</CardTitle>
        <CardDescription>{state.error || 'Failed to verify your email'}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-center text-muted-foreground">
          The verification link may be expired or invalid.
        </p>
      </CardContent>
      <CardFooter className="flex flex-col gap-4">
        <Button className="w-full" variant="outline" onClick={() => router.push('/auth/register')}>
          Request new verification email
        </Button>
        <div className="text-sm text-center text-muted-foreground">
          <Link
            href="/auth/login"
            className="inline-flex items-center gap-1 text-primary hover:underline"
          >
            <ArrowLeft className="h-3 w-3" />
            Back to login
          </Link>
        </div>
      </CardFooter>
    </Card>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <Card className="w-full max-w-sm">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="mt-4 text-sm text-muted-foreground">Loading...</p>
          </CardContent>
        </Card>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}

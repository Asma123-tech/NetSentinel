'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Shield, Eye, EyeOff, Sparkles, AlertCircle } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/context/AuthContext';

// ── Validation schema ──────────────────────────────────────────

const loginSchema = z.object({
  username: z
    .string()
    .min(1, 'Username or email is required'),
  password: z
    .string()
    .min(1, 'Password is required'),
  remember: z.boolean().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

// ── Error message component ────────────────────────────────────

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p className="mt-1.5 flex items-center gap-1.5 text-xs text-rose-600 font-medium">
      <AlertCircle size={13} className="shrink-0" />
      {message}
    </p>
  );
}

// ── Page ───────────────────────────────────────────────────────

export default function LoginPage() {
  const { login } = useAuth();
  const router    = useRouter();

  const [showPass,    setShowPass]    = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '', remember: false },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      setServerError(null);
      await login(data.username.trim(), data.password);
      router.replace('/search');
    } catch (err: any) {
      // Map common backend error messages to user-friendly text
      const msg: string = err.message || '';
      if (
        msg.toLowerCase().includes('incorrect') ||
        msg.toLowerCase().includes('unauthorized') ||
        msg.toLowerCase().includes('invalid')
      ) {
        setServerError('Incorrect username or password. Please try again.');
      } else if (msg.toLowerCase().includes('not found')) {
        setServerError('No account found with that username or email.');
      } else {
        setServerError(msg || 'Login failed. Please try again.');
      }
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center px-4 py-10">

      {/* Background image */}
      <div
        className="fixed inset-0 -z-[5] bg-cover bg-center blur-md scale-105 pointer-events-none"
        style={{ backgroundImage: "url('/images/logo 2.jpeg')" }}
      />
      <div className="fixed inset-0 -z-[4] bg-white/50 pointer-events-none" />

      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex h-16 w-16 rounded-3xl bg-gradient-to-br from-blue-600 to-violet-600 items-center justify-center shadow-lg mb-4">
            <Shield className="text-white" size={32} />
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900">NetSentinel</h1>
          <p className="text-slate-500 mt-1 text-sm">Sign in to your account</p>
        </div>

        {/* Card */}
        <div className="bg-white/85 backdrop-blur-xl rounded-3xl shadow-xl border border-white/60 p-8">

          {/* Server error banner */}
          {serverError && (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3">
              <AlertCircle size={16} className="mt-0.5 text-rose-500 shrink-0" />
              <p className="text-sm text-rose-700 font-medium">{serverError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">

            {/* Username / Email */}
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-semibold text-slate-700 mb-1.5"
              >
                Username or Email
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                placeholder="Enter your username or email"
                {...register('username')}
                className={`w-full rounded-xl border bg-white/70 px-4 py-3 text-slate-900 text-sm outline-none transition
                  focus:ring-2
                  ${errors.username
                    ? 'border-rose-400 focus:border-rose-400 focus:ring-rose-100'
                    : 'border-slate-200 focus:border-blue-400 focus:ring-blue-100'
                  }`}
              />
              <FieldError message={errors.username?.message} />
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-semibold text-slate-700 mb-1.5"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPass ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  {...register('password')}
                  className={`w-full rounded-xl border bg-white/70 px-4 py-3 pr-11 text-slate-900 text-sm outline-none transition
                    focus:ring-2
                    ${errors.password
                      ? 'border-rose-400 focus:border-rose-400 focus:ring-rose-100'
                      : 'border-slate-200 focus:border-blue-400 focus:ring-blue-100'
                    }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition"
                  aria-label={showPass ? 'Hide password' : 'Show password'}
                >
                  {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <FieldError message={errors.password?.message} />
            </div>

            {/* Remember me */}
            <div className="flex items-center gap-2.5">
              <input
                id="remember"
                type="checkbox"
                {...register('remember')}
                className="h-4 w-4 rounded border-slate-300 accent-blue-600 cursor-pointer"
              />
              <label
                htmlFor="remember"
                className="text-sm text-slate-600 cursor-pointer select-none"
              >
                Remember me
              </label>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-blue-600 to-violet-600 px-5 py-3 text-white font-semibold shadow-md hover:shadow-lg hover:scale-[1.02] transition-all duration-200 disabled:opacity-60 disabled:scale-100 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <span className="h-5 w-5 rounded-full border-2 border-white border-t-transparent animate-spin" />
              ) : (
                <>
                  <Sparkles size={16} />
                  Sign In
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 h-px bg-slate-200" />
            <span className="text-xs text-slate-400 font-medium">OR</span>
            <div className="flex-1 h-px bg-slate-200" />
          </div>

          {/* Signup link */}
          <p className="text-center text-sm text-slate-600">
            Don&apos;t have an account?{' '}
            <Link
              href="/signup"
              className="font-semibold text-blue-600 hover:text-blue-700 underline-offset-2 hover:underline transition"
            >
              Sign Up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
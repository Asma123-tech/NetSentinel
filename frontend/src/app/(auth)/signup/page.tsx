'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Shield, Eye, EyeOff, Sparkles, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/context/AuthContext';

// ── Validation schema ──────────────────────────────────────────

const signupSchema = z
  .object({
    full_name: z
      .string()
      .min(2, 'Full name must be at least 2 characters')
      .max(100, 'Full name must be at most 100 characters')
      .regex(/^[a-zA-Z\s'-]+$/, 'Full name can only contain letters, spaces, hyphens and apostrophes'),

    email: z
      .string()
      .min(1, 'Email address is required')
      .email('Please enter a valid email address')
      .max(255, 'Email address is too long'),

    username: z
      .string()
      .min(3, 'Username must be at least 3 characters')
      .max(30, 'Username must be at most 30 characters')
      .regex(
        /^[a-zA-Z0-9_]+$/,
        'Username can only contain letters, numbers, and underscores',
      ),

    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .max(128, 'Password is too long')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Password must contain at least one number')
      .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character'),

    confirm_password: z.string().min(1, 'Please confirm your password'),

    terms: z
      .boolean()
      .refine((v) => v === true, {
        message: 'You must accept the Terms & Privacy Policy to continue',
      }),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });

type SignupFormData = z.infer<typeof signupSchema>;

// ── Helpers ────────────────────────────────────────────────────

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p className="mt-1.5 flex items-center gap-1.5 text-xs text-rose-600 font-medium">
      <AlertCircle size={13} className="shrink-0" />
      {message}
    </p>
  );
}

function passwordStrength(pw: string): { score: number; label: string; color: string } {
  let score = 0;
  if (pw.length >= 8)           score++;
  if (/[A-Z]/.test(pw))        score++;
  if (/[0-9]/.test(pw))        score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;

  const labels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
  const colors = [
    '',
    'bg-rose-500',
    'bg-amber-400',
    'bg-blue-500',
    'bg-emerald-500',
  ];

  return { score, label: labels[score], color: colors[score] };
}

// ── Page ───────────────────────────────────────────────────────

export default function SignupPage() {
  const { signup } = useAuth();
  const router     = useRouter();

  const [showPass,    setShowPass]    = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      full_name: '',
      email: '',
      username: '',
      password: '',
      confirm_password: '',
      terms: false,
    },
  });

  const passwordValue = watch('password');
  const strength      = passwordStrength(passwordValue || '');

  const onSubmit = async (data: SignupFormData) => {
    try {
      setServerError(null);
      await signup(data.username, data.email, data.password, data.full_name);
      router.replace('/search');
    } catch (err: any) {
      const msg: string = err.message || '';

      // Map backend errors to specific user-friendly messages
      if (msg.toLowerCase().includes('email') && msg.toLowerCase().includes('exist')) {
        setServerError(
          'An account with this email address already exists. Please sign in instead.',
        );
      } else if (
        msg.toLowerCase().includes('username') &&
        msg.toLowerCase().includes('exist')
      ) {
        setServerError(
          'This username is already taken. Please choose a different username.',
        );
      } else if (msg.toLowerCase().includes('already registered')) {
        setServerError(
          'An account with this email or username already exists.',
        );
      } else if (msg.toLowerCase().includes('password')) {
        setServerError('Password does not meet security requirements.');
      } else {
        setServerError(msg || 'Signup failed. Please check your details and try again.');
      }
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center px-4 py-10">

      {/* Background */}
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
          <p className="text-slate-500 mt-1 text-sm">Create your account</p>
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

            {/* Full Name */}
            <div>
              <label
                htmlFor="full_name"
                className="block text-sm font-semibold text-slate-700 mb-1.5"
              >
                Full Name
              </label>
              <input
                id="full_name"
                type="text"
                autoComplete="name"
                placeholder="e.g. John Smith"
                {...register('full_name')}
                className={`w-full rounded-xl border bg-white/70 px-4 py-3 text-slate-900 text-sm outline-none transition focus:ring-2
                  ${errors.full_name
                    ? 'border-rose-400 focus:border-rose-400 focus:ring-rose-100'
                    : 'border-slate-200 focus:border-blue-400 focus:ring-blue-100'
                  }`}
              />
              <FieldError message={errors.full_name?.message} />
            </div>

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-semibold text-slate-700 mb-1.5"
              >
                Email Address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                {...register('email')}
                className={`w-full rounded-xl border bg-white/70 px-4 py-3 text-slate-900 text-sm outline-none transition focus:ring-2
                  ${errors.email
                    ? 'border-rose-400 focus:border-rose-400 focus:ring-rose-100'
                    : 'border-slate-200 focus:border-blue-400 focus:ring-blue-100'
                  }`}
              />
              <FieldError message={errors.email?.message} />
            </div>

            {/* Username */}
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-semibold text-slate-700 mb-1.5"
              >
                Username
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                placeholder="e.g. john_smith"
                {...register('username')}
                className={`w-full rounded-xl border bg-white/70 px-4 py-3 text-slate-900 text-sm outline-none transition focus:ring-2
                  ${errors.username
                    ? 'border-rose-400 focus:border-rose-400 focus:ring-rose-100'
                    : 'border-slate-200 focus:border-blue-400 focus:ring-blue-100'
                  }`}
              />
              <FieldError message={errors.username?.message} />
              {!errors.username && (
                <p className="mt-1 text-xs text-slate-400">
                  Letters, numbers and underscores only. 3–30 characters.
                </p>
              )}
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
                  autoComplete="new-password"
                  placeholder="Create a strong password"
                  {...register('password')}
                  className={`w-full rounded-xl border bg-white/70 px-4 py-3 pr-11 text-slate-900 text-sm outline-none transition focus:ring-2
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

              {/* Strength meter */}
              {passwordValue && (
                <div className="mt-2">
                  <div className="flex gap-1 mb-1">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className={`h-1.5 flex-1 rounded-full transition-colors ${
                          i <= strength.score ? strength.color : 'bg-slate-200'
                        }`}
                      />
                    ))}
                  </div>
                  <p
                    className={`text-xs font-medium ${
                      strength.score <= 1
                        ? 'text-rose-500'
                        : strength.score === 2
                        ? 'text-amber-500'
                        : strength.score === 3
                        ? 'text-blue-500'
                        : 'text-emerald-600'
                    }`}
                  >
                    {strength.label} password
                  </p>
                </div>
              )}

              <FieldError message={errors.password?.message} />
            </div>

            {/* Confirm Password */}
            <div>
              <label
                htmlFor="confirm_password"
                className="block text-sm font-semibold text-slate-700 mb-1.5"
              >
                Confirm Password
              </label>
              <input
                id="confirm_password"
                type={showPass ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="Repeat your password"
                {...register('confirm_password')}
                className={`w-full rounded-xl border bg-white/70 px-4 py-3 text-slate-900 text-sm outline-none transition focus:ring-2
                  ${errors.confirm_password
                    ? 'border-rose-400 focus:border-rose-400 focus:ring-rose-100'
                    : 'border-slate-200 focus:border-blue-400 focus:ring-blue-100'
                  }`}
              />
              <FieldError message={errors.confirm_password?.message} />
            </div>

            {/* Terms checkbox */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
              <div className="flex items-start gap-3">
                <input
                  id="terms"
                  type="checkbox"
                  {...register('terms')}
                  className="mt-0.5 h-4 w-4 rounded border-slate-300 accent-blue-600 cursor-pointer shrink-0"
                />
                <label
                  htmlFor="terms"
                  className="text-sm text-slate-700 cursor-pointer leading-relaxed select-none"
                >
                  I agree to the{' '}
                  <span className="font-semibold text-blue-600">Terms of Service</span>{' '}
                  and{' '}
                  <span className="font-semibold text-blue-600">Privacy Policy</span>.
                  I understand that NetSentinel collects search data to improve safety
                  filtering.
                </label>
              </div>
              <FieldError message={errors.terms?.message} />
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
                  Create Account
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

          {/* Login link */}
          <p className="text-center text-sm text-slate-600">
            Already have an account?{' '}
            <Link
              href="/login"
              className="font-semibold text-blue-600 hover:text-blue-700 underline-offset-2 hover:underline transition"
            >
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

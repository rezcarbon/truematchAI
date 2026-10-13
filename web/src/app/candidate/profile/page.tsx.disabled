import { useEffect, useState } from 'react';
'use client';
function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

import { AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function Card({ className, ...props }: any) {
  return (
    <div className={cn("rounded-lg border border-gray-200 bg-white shadow-sm", className)} {...props} />
  );
}
function CardHeader({ className, ...props }: any) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}
function CardTitle({ className, ...props }: any) {
  return <h2 className={cn("text-2xl font-semibold leading-none tracking-tight", className)} {...props} />;
}
function CardDescription({ className, ...props }: any) {
  return <p className={cn("text-sm text-gray-500", className)} {...props} />;
}
function CardContent({ className, ...props }: any) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}

function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
    </div>
  );
}

function Button({ className, variant = "default", size = "default", ...props }: any) {
  const variants: any = { default: "bg-blue-600 text-white hover:bg-blue-700", outline: "border border-gray-300 bg-white hover:bg-gray-50", ghost: "hover:bg-gray-100" };
  const sizes: any = { default: "px-4 py-2", sm: "px-3 py-1 text-sm", lg: "px-6 py-3 text-lg" };
  return <button className={cn("inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none", variants[variant], sizes[size], className)} {...props} />;
}

interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  location: string | null;
  headline: string | null;
  role: string;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    display_name: '',
    location: '',
    headline: '',
  });

  // Fetch current profile
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/proxy/profile/user/me');

        if (!response.ok) {
          throw new Error('Failed to fetch profile');
        }

        const data: UserProfile = await response.json();
        setProfile(data);
        setFormData({
          display_name: data.display_name || '',
          location: data.location || '',
          headline: data.headline || '',
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    setError(null);
    setSuccess(false);
    setSaving(true);

    try {
      const response = await fetch('/api/proxy/profile/user/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update profile');
      }

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Calculate profile completion percentage
  const completionPercentage = Math.round(
    ((formData.display_name ? 1 : 0) +
      (formData.location ? 1 : 0) +
      (formData.headline ? 1 : 0)) /
      3 *
      100
  );

  const isProfileIncomplete = completionPercentage < 100;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Your profile"
        subtitle="Manage your details and assessment preferences."
        icon="User"
      />

      <div className="mx-auto max-w-2xl px-4">
        {/* Profile Completion Progress */}
        <div className="mb-6 p-4 bg-blue-50/60 border border-blue-200/60 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-blue-900">Profile completion</p>
            <p className="text-sm font-bold text-blue-600">{completionPercentage}%</p>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2 overflow-hidden">
            <div
              className="bg-blue-600 h-full transition-all duration-300"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
          {isProfileIncomplete && (
            <p className="text-xs text-blue-700 mt-2">
              {3 - (formData.display_name ? 1 : 0) - (formData.location ? 1 : 0) - (formData.headline ? 1 : 0)} more field{3 - (formData.display_name ? 1 : 0) - (formData.location ? 1 : 0) - (formData.headline ? 1 : 0) !== 1 ? 's' : ''} to go
            </p>
          )}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Personal details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">Email</label>
                <input
                  id="email"
                  type="email"
                  value={profile?.email || ''}
                  disabled
                  className="w-full rounded-md border bg-muted px-3 py-2 text-sm disabled:opacity-50"
                />
                <p className="text-xs text-muted-foreground">Email cannot be changed</p>
              </div>

              <div className="space-y-2">
                <label htmlFor="display_name" className="text-sm font-medium">Full name</label>
                <input
                  id="display_name"
                  name="display_name"
                  type="text"
                  value={formData.display_name}
                  onChange={handleChange}
                  placeholder="e.g., Priya Nair"
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="location" className="text-sm font-medium">Location</label>
                <input
                  id="location"
                  name="location"
                  type="text"
                  value={formData.location}
                  onChange={handleChange}
                  placeholder="e.g., Singapore"
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="headline" className="text-sm font-medium">Professional headline</label>
                <input
                  id="headline"
                  name="headline"
                  type="text"
                  value={formData.headline}
                  onChange={handleChange}
                  placeholder="e.g., Senior Backend Engineer"
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>
            </div>

            {error && (
              <div className="flex items-start gap-3 rounded-lg bg-red-50/60 border border-red-200/60 p-4">
                <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            {success && (
              <div className="flex items-start gap-3 rounded-lg bg-green-50/60 border border-green-200/60 p-4">
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-green-600">Profile updated successfully</p>
              </div>
            )}

            <Button onClick={handleSave} disabled={saving} className="w-full sm:w-auto">
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Saving...
                </>
              ) : (
                'Save changes'
              )}
            </Button>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">Account information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Account type</span>
              <span className="text-sm font-medium capitalize">{profile?.role}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Account ID</span>
              <span className="text-sm font-mono text-muted-foreground">{profile?.id.slice(0, 8)}...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}



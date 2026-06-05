'use client';

import { useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, Loader2, Eye, EyeOff } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/providers/ToastProvider';
import { ThemeToggle } from '@/components/shared/ThemeToggle';

export default function SettingsPage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleChangePassword = async () => {
    setError(null);

    // Validation
    if (!formData.current_password) {
      setError('Current password is required');
      addToast('Current password is required', 'warning');
      return;
    }
    if (!formData.new_password || formData.new_password.length < 8) {
      setError('New password must be at least 8 characters');
      addToast('New password must be at least 8 characters', 'warning');
      return;
    }
    if (formData.new_password !== formData.confirm_password) {
      setError('Passwords do not match');
      addToast('Passwords do not match', 'error');
      return;
    }
    if (formData.current_password === formData.new_password) {
      setError('New password must be different from current password');
      addToast('New password must be different from current password', 'warning');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/proxy/auth/password', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: formData.current_password,
          new_password: formData.new_password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || 'Failed to change password'
        );
      }

      addToast('Password changed successfully! 🎉', 'success');
      setFormData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      addToast(message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Administrator Settings"
        subtitle="Manage your account security and system preferences."
        icon="Settings"
      />

      <div className="mx-auto max-w-2xl px-4">
        <Card>
          <CardHeader>
            <CardTitle>Change password</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Current Password */}
            <div className="space-y-2">
              <label htmlFor="current_password" className="text-sm font-medium">
                Current password
              </label>
              <div className="relative">
                <input
                  id="current_password"
                  name="current_password"
                  type={showCurrentPassword ? 'text' : 'password'}
                  value={formData.current_password}
                  onChange={handleChange}
                  className="w-full rounded-md border bg-background px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                  placeholder="Enter your current password"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showCurrentPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* New Password */}
            <div className="space-y-2">
              <label htmlFor="new_password" className="text-sm font-medium">
                New password
              </label>
              <div className="relative">
                <input
                  id="new_password"
                  name="new_password"
                  type={showNewPassword ? 'text' : 'password'}
                  value={formData.new_password}
                  onChange={handleChange}
                  className="w-full rounded-md border bg-background px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                  placeholder="Enter a new password (minimum 8 characters)"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showNewPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              <p className="text-xs text-muted-foreground">
                Use at least 8 characters with a mix of uppercase, lowercase, numbers, and symbols.
              </p>
            </div>

            {/* Confirm Password */}
            <div className="space-y-2">
              <label htmlFor="confirm_password" className="text-sm font-medium">
                Confirm new password
              </label>
              <div className="relative">
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={formData.confirm_password}
                  onChange={handleChange}
                  className="w-full rounded-md border bg-background px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                  placeholder="Confirm your new password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="flex items-start gap-3 rounded-lg bg-red-50/60 border border-red-200/60 p-4">
                <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <Button
              onClick={handleChangePassword}
              disabled={loading}
              className="w-full sm:w-auto"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Changing password...
                </>
              ) : (
                'Change password'
              )}
            </Button>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
          </CardHeader>
          <CardContent>
            <ThemeToggle />
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">Administrator Security</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium">Two-factor authentication</p>
                  <p className="text-xs text-muted-foreground mt-1">Add extra security with 2FA</p>
                </div>
                <Badge variant="secondary">Coming soon</Badge>
              </div>
              <div className="flex items-start justify-between pt-3 border-t">
                <div>
                  <p className="text-sm font-medium">Login alerts</p>
                  <p className="text-xs text-muted-foreground mt-1">Get notified of new login attempts</p>
                </div>
                <Badge variant="secondary">Coming soon</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">Security recommendations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <ul className="text-sm text-muted-foreground space-y-2 list-disc list-inside">
              <li>Use a unique, strong password that you don't use on other websites</li>
              <li>Change your password every 3 months as an administrator</li>
              <li>Use a combination of uppercase, lowercase, numbers, and special symbols</li>
              <li>Never share your credentials with anyone else</li>
              <li>Enable two-factor authentication when available for enhanced security</li>
              <li>Immediately change password if you suspect account compromise</li>
              <li>Review login activity regularly in audit logs</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

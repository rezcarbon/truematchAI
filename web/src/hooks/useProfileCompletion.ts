import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';

interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  location: string | null;
  headline: string | null;
  role: string;
}

export function useProfileCompletion(role: string) {
  const router = useRouter();
  const pathname = usePathname();
  const { data: session } = useSession();

  useEffect(() => {
    if (!session?.user) return;

    // Don't redirect if already on profile page or settings
    const isOnProfilePage = pathname.includes('/profile') || pathname.includes('/settings');
    if (isOnProfilePage) return;

    const checkProfileCompletion = async () => {
      try {
        const response = await fetch('/api/proxy/profile/user/me');
        if (!response.ok) return;

        const profile: UserProfile = await response.json();

        // Check if profile is incomplete
        const isIncomplete = !profile.display_name || profile.display_name.trim() === '';

        if (isIncomplete) {
          // Redirect to profile completion page
          router.push(`/${role}/profile?incomplete=true`);
        }
      } catch (error) {
        console.error('Failed to check profile completion:', error);
      }
    };

    // Check after a short delay to allow session to be established
    const timer = setTimeout(checkProfileCompletion, 1000);
    return () => clearTimeout(timer);
  }, [session, role, router, pathname]);
}

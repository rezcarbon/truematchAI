import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
"use client";
function cn(...classes: (string | undefined | null | boolean)[]): string {
  return classes.filter(Boolean).join(" ");
}

// Inline Card components
function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-lg border border-gray-200 bg-white shadow-sm",
        className
      )}
      {...props}
    />
  );
}

function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col space-y-1.5 p-6 border-b", className)}
      {...props}
    />
  );
}

function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn(
        "text-2xl font-semibold leading-none tracking-tight",
        className
      )}
      {...props}
    />
  );
}

function CardContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6", className)} {...props} />;
}

export default function CandidateDashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth/login");
    }
  }, [status, router]);

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">TrueMatch</h1>
            <p className="text-sm text-gray-600">Candidate Dashboard</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-700">
              Welcome, {session?.user?.name || "User"}
            </span>
            <button
              onClick={() => router.push("/api/auth/signout")}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to TrueMatch
          </h2>
          <p className="text-lg text-gray-600">
            Discover opportunities that match your skills and aspirations
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          {[
            { label: "Profile Completeness", value: "85%", color: "bg-blue-100" },
            { label: "Matches This Week", value: "12", color: "bg-green-100" },
            { label: "Applications", value: "5", color: "bg-purple-100" },
          ].map((stat) => (
            <Card key={stat.label} className={stat.color}>
              <CardContent className="text-center">
                <div className="text-3xl font-bold text-gray-900 mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Recent Matches */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Matches</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    title: "Senior Software Engineer",
                    company: "TechCorp",
                    match: "92%",
                  },
                  {
                    title: "Full Stack Developer",
                    company: "StartupXYZ",
                    match: "87%",
                  },
                  {
                    title: "Tech Lead",
                    company: "InnovateCo",
                    match: "84%",
                  },
                ].map((job, i) => (
                  <div key={i} className="flex items-start justify-between pb-4 border-b last:border-b-0">
                    <div>
                      <h4 className="font-semibold text-gray-900">{job.title}</h4>
                      <p className="text-sm text-gray-600">{job.company}</p>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-green-600">{job.match}</div>
                      <p className="text-xs text-gray-500">match</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Next Steps */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Next Steps</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-sm font-semibold text-blue-600">
                    1
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Complete Your Profile</h4>
                    <p className="text-sm text-gray-600">Add more details to improve matches</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-sm font-semibold text-blue-600">
                    2
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Review Matches</h4>
                    <p className="text-sm text-gray-600">Browse personalized opportunities</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-sm font-semibold text-blue-600">
                    3
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Apply & Interview</h4>
                    <p className="text-sm text-gray-600">Take the next step in your career</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}


// Inline utility

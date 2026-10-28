"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Briefcase, TrendingUp, FileText, CheckCircle2, ArrowRight, LogOut } from "lucide-react";

// Inline utility
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
      <header className="bg-gradient-to-r from-purple-600 to-purple-800 text-white">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">TrueMatch</h1>
            <p className="text-purple-100 text-sm mt-1">Candidate Dashboard</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-white">
                {session?.user?.name || "Welcome"}
              </p>
              <p className="text-xs text-purple-100">{session?.user?.email}</p>
            </div>
            <button
              onClick={() => router.push("/api/auth/signout")}
              className="px-4 py-2 text-sm font-medium text-purple-700 bg-white rounded-lg hover:bg-purple-50 transition flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
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
            { label: "Profile Completeness", value: "85%", color: "from-blue-50 to-blue-100", icon: FileText, iconColor: "text-blue-600" },
            { label: "Matches This Week", value: "12", color: "from-green-50 to-green-100", icon: TrendingUp, iconColor: "text-green-600" },
            { label: "Applications", value: "5", color: "from-purple-50 to-purple-100", icon: Briefcase, iconColor: "text-purple-600" },
          ].map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.label} className={`bg-gradient-to-br ${stat.color} border-0`}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-3xl font-bold text-gray-900 mb-1">
                        {stat.value}
                      </div>
                      <div className="text-sm text-gray-700">{stat.label}</div>
                    </div>
                    <Icon className={`w-12 h-12 ${stat.iconColor} opacity-30`} />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Main Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Recent Matches */}
          <Card className="hover:shadow-lg transition">
            <CardHeader className="border-b border-gray-100 bg-gradient-to-r from-blue-50 to-transparent">
              <CardTitle className="text-lg flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-blue-600" />
                Recent Matches
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
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
                  <div key={i} className="flex items-start justify-between pb-4 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 -mx-6 px-6 py-2 rounded transition">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 text-sm">{job.title}</h4>
                      <p className="text-xs text-gray-600 mt-1">{job.company}</p>
                    </div>
                    <div className="text-right ml-4">
                      <div className="inline-flex items-center gap-2 px-3 py-1 bg-green-100 rounded-full">
                        <CheckCircle2 className="w-4 h-4 text-green-600" />
                        <span className="font-bold text-green-700 text-sm">{job.match}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <a href="#" className="flex items-center gap-2 text-blue-600 font-medium text-sm mt-6 hover:text-blue-700">
                View All Matches
                <ArrowRight className="w-4 h-4" />
              </a>
            </CardContent>
          </Card>

          {/* Next Steps */}
          <Card className="hover:shadow-lg transition">
            <CardHeader className="border-b border-gray-100 bg-gradient-to-r from-purple-50 to-transparent">
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-purple-600" />
                Your Roadmap
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                {[
                  { num: "1", title: "Complete Your Profile", desc: "Add more details to improve matches" },
                  { num: "2", title: "Review Matches", desc: "Browse personalized opportunities" },
                  { num: "3", title: "Apply & Interview", desc: "Take the next step in your career" },
                ].map((step, i) => (
                  <div key={i} className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
                      {step.num}
                    </div>
                    <div className="flex-1 pt-0.5">
                      <h4 className="font-semibold text-gray-900 text-sm">{step.title}</h4>
                      <p className="text-xs text-gray-600 mt-0.5">{step.desc}</p>
                    </div>
                    {i < 2 && <div className="absolute left-[45px] top-[120px] w-0.5 h-12 bg-gradient-to-b from-purple-300 to-purple-100 -ml-0" />}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Users, Briefcase, Clock, CheckCircle, LogOut, Plus } from "lucide-react";

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

// Inline Button
function Button({
  className,
  disabled,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md px-4 py-2 font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50",
        className
      )}
      disabled={disabled}
      {...props}
    />
  );
}

// Inline Badge
function Badge({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium bg-blue-100 text-blue-800",
        className
      )}
      {...props}
    />
  );
}

export default function RecruiterDashboard() {
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
      <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">TrueMatch</h1>
            <p className="text-blue-100 text-sm mt-1">Recruiter Dashboard</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-white">
                {session?.user?.name || "Welcome"}
              </p>
              <p className="text-xs text-blue-100">{session?.user?.email}</p>
            </div>
            <button
              onClick={() => router.push("/api/auth/signout")}
              className="px-4 py-2 text-sm font-medium text-blue-700 bg-white rounded-lg hover:bg-blue-50 transition flex items-center gap-2"
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
            Welcome to TrueMatch Recruiting
          </h2>
          <p className="text-lg text-gray-600">
            Find the best talent using AI-powered matching
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          {[
            { label: "Open Positions", value: "8", color: "bg-blue-100" },
            { label: "Active Candidates", value: "247", color: "bg-green-100" },
            { label: "Pending Interviews", value: "12", color: "bg-purple-100" },
            { label: "Offers Pending", value: "3", color: "bg-orange-100" },
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

        {/* Main Content Grid */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* Open Positions */}
          <Card className="md:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Open Positions</CardTitle>
                <Button className="text-sm px-3 py-1 h-auto">Post New</Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    title: "Senior Engineer",
                    candidates: "24",
                    status: "Active",
                  },
                  {
                    title: "Product Manager",
                    candidates: "18",
                    status: "Active",
                  },
                  {
                    title: "UX Designer",
                    candidates: "12",
                    status: "Active",
                  },
                  {
                    title: "Data Analyst",
                    candidates: "9",
                    status: "Review",
                  },
                ].map((job, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between pb-4 border-b last:border-b-0"
                  >
                    <div>
                      <h4 className="font-semibold text-gray-900">
                        {job.title}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {job.candidates} candidates
                      </p>
                    </div>
                    <Badge
                      className={
                        job.status === "Active"
                          ? "bg-green-100 text-green-800"
                          : "bg-yellow-100 text-yellow-800"
                      }
                    >
                      {job.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    action: "Interview Scheduled",
                    person: "Alice Johnson",
                    time: "2 hours ago",
                  },
                  {
                    action: "Application Received",
                    person: "Bob Smith",
                    time: "4 hours ago",
                  },
                  {
                    action: "Offer Extended",
                    person: "Carol White",
                    time: "1 day ago",
                  },
                ].map((activity, i) => (
                  <div key={i} className="pb-4 border-b last:border-b-0">
                    <p className="font-semibold text-gray-900 text-sm">
                      {activity.action}
                    </p>
                    <p className="text-sm text-gray-600">{activity.person}</p>
                    <p className="text-xs text-gray-500">{activity.time}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Top Candidates */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-lg">Top Matched Candidates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-gray-900">
                      Name
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-900">
                      Position
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-900">
                      Match Score
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-900">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    {
                      name: "Alice Johnson",
                      position: "Senior Engineer",
                      score: "94%",
                      status: "Interviewing",
                    },
                    {
                      name: "Bob Smith",
                      position: "Product Manager",
                      score: "89%",
                      status: "New",
                    },
                    {
                      name: "Carol White",
                      position: "UX Designer",
                      score: "85%",
                      status: "New",
                    },
                  ].map((candidate, i) => (
                    <tr
                      key={i}
                      className="border-b hover:bg-gray-50 last:border-b-0"
                    >
                      <td className="px-4 py-3 font-medium text-gray-900">
                        {candidate.name}
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {candidate.position}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-green-600">
                          {candidate.score}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className="bg-blue-100 text-blue-800">
                          {candidate.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

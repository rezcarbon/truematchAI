export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-900 via-purple-900 to-slate-900 text-white">
      <nav className="flex items-center justify-between px-6 py-4 border-b border-purple-800">
        <h1 className="text-2xl font-bold">TrueMatch</h1>
        <div className="flex gap-4">
          <a href="/auth/login" className="px-4 py-2 rounded hover:bg-purple-800">
            Login
          </a>
          <a href="/auth/signup" className="px-4 py-2 bg-purple-600 rounded hover:bg-purple-700">
            Sign Up
          </a>
        </div>
      </nav>

      <section className="px-6 py-20 text-center">
        <h2 className="text-5xl font-bold mb-6">
          AI-Powered Candidate & Job Matching
        </h2>
        <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
          TrueMatch uses advanced AI to match candidates with opportunities,
          ensuring the best fit for both parties.
        </p>
        <div className="flex gap-4 justify-center">
          <a
            href="/auth/signup"
            className="px-6 py-3 bg-purple-600 rounded-lg hover:bg-purple-700 font-semibold"
          >
            Get Started
          </a>
          <a
            href="/auth/login"
            className="px-6 py-3 border border-purple-400 rounded-lg hover:bg-purple-800"
          >
            Login
          </a>
        </div>
      </section>

      <section className="px-6 py-16 grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {[
          {
            title: "For Candidates",
            description: "Discover opportunities that match your skills and aspirations"
          },
          {
            title: "For Recruiters",
            description: "Find the best talent using advanced matching algorithms"
          },
          {
            title: "For Enterprises",
            description: "Enterprise-grade AI-powered recruiting platform"
          }
        ].map((feature) => (
          <div
            key={feature.title}
            className="p-6 rounded-lg border border-purple-700 bg-purple-900/20"
          >
            <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
            <p className="text-gray-300">{feature.description}</p>
          </div>
        ))}
      </section>
    </main>
  );
}

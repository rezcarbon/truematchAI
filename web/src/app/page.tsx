'use client';

import { Zap, Users, Briefcase, ArrowRight, CheckCircle2, Brain, Target } from 'lucide-react';

export default function Home() {
  return (
    <main className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-gray-200 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-purple-900 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">T</span>
            </div>
            <h1 className="text-xl font-bold text-gray-900">TrueMatch</h1>
          </div>
          <div className="flex gap-3">
            <a
              href="/auth/login"
              className="px-4 py-2 text-gray-700 font-medium hover:bg-gray-100 rounded-lg transition"
            >
              Login
            </a>
            <a
              href="/auth/signup"
              className="px-4 py-2 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 transition shadow-sm"
            >
              Sign Up
            </a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 bg-gradient-to-br from-purple-50 via-white to-blue-50">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 rounded-full mb-6">
            <Zap className="w-4 h-4 text-purple-600" />
            <span className="text-sm font-medium text-purple-700">AI-Powered Matching Engine</span>
          </div>

          <h2 className="text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Find Your Perfect Match with AI
          </h2>

          <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed">
            TrueMatch uses advanced AI to match candidates with opportunities, ensuring the best fit for both parties. Powered by Singpass authentication for Singapore.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <a
              href="/auth/signup"
              className="px-8 py-4 bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold rounded-lg hover:shadow-lg transition flex items-center justify-center gap-2"
            >
              Get Started Free
              <ArrowRight className="w-4 h-4" />
            </a>
            <a
              href="/auth/login"
              className="px-8 py-4 border-2 border-gray-300 text-gray-900 font-semibold rounded-lg hover:border-purple-600 hover:text-purple-600 transition"
            >
              Sign In
            </a>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-8 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <span>No credit card required</span>
            </div>
            <div className="hidden sm:block w-px h-5 bg-gray-300" />
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <span>Start matching in minutes</span>
            </div>
            <div className="hidden sm:block w-px h-5 bg-gray-300" />
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <span>Singpass integrated</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h3 className="text-4xl font-bold text-gray-900 mb-4">Built for Everyone</h3>
            <p className="text-lg text-gray-600">Whether you're a candidate, recruiter, or enterprise, TrueMatch has the tools you need.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Users,
                title: "For Candidates",
                description: "Discover job opportunities that match your skills, experience, and career aspirations with AI precision.",
                features: ["Smart job matching", "Resume optimization", "Application tracking"]
              },
              {
                icon: Briefcase,
                title: "For Recruiters",
                description: "Find the best talent quickly using advanced AI matching and candidate assessment tools.",
                features: ["AI talent matching", "Candidate pipeline", "Interview scheduling"]
              },
              {
                icon: Brain,
                title: "For Enterprises",
                description: "Enterprise-grade AI-powered recruiting platform with advanced analytics and compliance.",
                features: ["Team collaboration", "Advanced analytics", "Compliance ready"]
              }
            ].map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="p-8 rounded-2xl border border-gray-200 bg-white hover:shadow-lg transition group"
                >
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-100 to-purple-50 rounded-xl flex items-center justify-center mb-6 group-hover:shadow-md transition">
                    <Icon className="w-6 h-6 text-purple-600" />
                  </div>
                  <h4 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h4>
                  <p className="text-gray-600 mb-6">{feature.description}</p>
                  <ul className="space-y-3">
                    {feature.features.map((item) => (
                      <li key={item} className="flex items-center gap-2 text-sm text-gray-700">
                        <div className="w-1.5 h-1.5 bg-purple-600 rounded-full" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-r from-purple-600 to-purple-800">
        <div className="max-w-4xl mx-auto text-center text-white">
          <h3 className="text-4xl font-bold mb-6">Ready to Transform Your Recruiting?</h3>
          <p className="text-lg text-purple-100 mb-10">Join hundreds of organizations using TrueMatch to find better matches, faster.</p>
          <a
            href="/auth/signup"
            className="inline-block px-8 py-4 bg-white text-purple-700 font-semibold rounded-lg hover:shadow-lg transition"
          >
            Start Free Trial
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 bg-gray-50 border-t border-gray-200">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-6 h-6 bg-gradient-to-br from-purple-600 to-purple-900 rounded-lg" />
                <span className="font-bold text-gray-900">TrueMatch</span>
              </div>
              <p className="text-sm text-gray-600">AI-Powered Candidate & Job Matching for Singapore</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><a href="/auth/signup" className="hover:text-purple-600">For Candidates</a></li>
                <li><a href="/auth/signup" className="hover:text-purple-600">For Recruiters</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><a href="#" className="hover:text-purple-600">About</a></li>
                <li><a href="#" className="hover:text-purple-600">Blog</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><a href="#" className="hover:text-purple-600">Privacy</a></li>
                <li><a href="#" className="hover:text-purple-600">Terms</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-gray-200 text-center text-sm text-gray-600">
            <p>&copy; 2026 TrueMatch. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </main>
  );
}

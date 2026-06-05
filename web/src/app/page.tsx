import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowRight, Gauge, ShieldCheck, GitCompareArrows } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="flex h-16 items-center justify-between border-b px-6">
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 rounded-md bg-primary" />
          <span className="font-bold">TrueMatch</span>
        </div>
        <nav className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" size="sm">Log in</Button>
          </Link>
          <Link href="/signup">
            <Button size="sm">Get started</Button>
          </Link>
        </nav>
      </header>

      <section className="mx-auto max-w-4xl px-6 py-24 text-center">
        <span className="inline-block rounded-full bg-accent px-3 py-1 text-xs font-semibold text-accent-foreground">
          AI-embodied hiring assessment
        </span>
        <h1 className="mt-6 text-5xl font-extrabold tracking-tight">
          See the candidate the keyword filter missed.
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
          Traditional ATS systems score the words on a resume. TrueMatch scores demonstrated
          capability — then shows you the delta between the two. That gap is where great hires hide.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link href="/signup">
            <Button size="lg">Start assessing <ArrowRight className="h-4 w-4" /></Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="outline">Sign in</Button>
          </Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-6 px-6 pb-24 md:grid-cols-3">
        {[
          { icon: GitCompareArrows, title: "Dual scoring", body: "Traditional ATS score vs capability score, side by side, with the delta highlighted." },
          { icon: Gauge, title: "Capability narrative", body: "Evidence-based reasoning across systems, delivery, collaboration, and learning velocity." },
          { icon: ShieldCheck, title: "Governed by design", body: "Coherence, consistency, and fidelity signals plus fairness monitoring on every assessment." },
        ].map((f) => (
          <Card key={f.title}>
            <CardContent className="space-y-3 p-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10">
                <f.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold">{f.title}</h3>
              <p className="text-sm text-muted-foreground">{f.body}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <footer className="border-t px-6 py-8 text-center text-sm text-muted-foreground">
        © {new Date().getFullYear()} TrueMatch. Capability-first hiring.
      </footer>
    </div>
  );
}

import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default async function JobDetailPage({ params }: { params: { id: string } }) {
  const positions = await api.getPositions();
  const p = positions.find((x) => x.id === params.id) ?? positions[0];
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={p.title} subtitle={`${p.department} · ${p.location}`} />
      <Card>
        <CardHeader>
          <CardTitle>About this role</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="leading-relaxed text-muted-foreground">
            We&apos;re looking for someone who can own ambiguous problems end to end, collaborate
            across functions, and ramp quickly into new domains. TrueMatch assesses your application
            for demonstrated capability — so a non-obvious background is welcome.
          </p>
          <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
            <li>Own delivery of significant features and systems</li>
            <li>Partner closely with product and design</li>
            <li>Mentor and raise the engineering bar</li>
          </ul>
          <Button>Apply with my profile</Button>
        </CardContent>
      </Card>
    </div>
  );
}

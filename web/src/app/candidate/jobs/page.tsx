import Link from "next/link";
import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { api } from "@/lib/api";
import { MapPin, Building2 } from "lucide-react";

export default async function JobsPage() {
  const positions = await api.getPositions();
  return (
    <div>
      <PageHeader title="Open roles" subtitle="Browse roles and see how your capability profile maps." />
      <div className="grid gap-4 md:grid-cols-2">
        {positions.map((p) => (
          <Link key={p.id} href={`/candidate/jobs/${p.id}`}>
            <Card className="transition-shadow hover:shadow-md">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <h3 className="font-semibold">{p.title}</h3>
                  <StatusBadge status={p.status} />
                </div>
                <div className="mt-2 flex gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1"><Building2 className="h-4 w-4" />{p.department}</span>
                  <span className="flex items-center gap-1"><MapPin className="h-4 w-4" />{p.location}</span>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { FileCheck } from "lucide-react";

export interface ComplianceItem {
  area: string;
  status: "pass" | "review" | "fail";
  detail: string;
}

export function ComplianceReport({ items }: { items: ComplianceItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileCheck className="h-5 w-5 text-primary" />
          Compliance Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.map((it, i) => (
          <div key={i} className="flex items-start justify-between gap-3 rounded-md border p-4">
            <div>
              <p className="font-medium">{it.area}</p>
              <p className="text-sm text-muted-foreground">{it.detail}</p>
            </div>
            <StatusBadge status={it.status} />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

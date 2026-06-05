"use client";
import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";
import type { AuditEntry } from "@/lib/types";

export function AuditTrailViewer({ entries }: { entries: AuditEntry[] }) {
  const [query, setQuery] = React.useState("");
  const filtered = entries.filter(
    (e) =>
      e.actor.toLowerCase().includes(query.toLowerCase()) ||
      e.action.toLowerCase().includes(query.toLowerCase()) ||
      e.target.toLowerCase().includes(query.toLowerCase())
  );
  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit Trail</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter by actor, action, or target…"
          className="w-full rounded-md border bg-background px-3 py-2 text-sm"
        />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="p-2 font-medium">Timestamp</th>
                <th className="p-2 font-medium">Actor</th>
                <th className="p-2 font-medium">Action</th>
                <th className="p-2 font-medium">Target</th>
                <th className="p-2 font-medium">IP</th>
              </tr>
            </thead>
            <tbody className="font-mono text-xs">
              {filtered.map((e) => (
                <tr key={e.id} className="border-b last:border-0">
                  <td className="p-2 text-muted-foreground">{formatDate(e.timestamp)}</td>
                  <td className="p-2">{e.actor}</td>
                  <td className="p-2 font-semibold">{e.action}</td>
                  <td className="p-2 text-muted-foreground">{e.target}</td>
                  <td className="p-2 text-muted-foreground">{e.ip}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

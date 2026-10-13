"use client";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export interface BiasMetric {
  group: string;
  selectionRate: number; // backend-supplied %
}

// Renders backend-supplied fairness metrics (e.g. selection rates by group).
// The web client never computes fairness — it visualizes reported values.
export function BiasReport({ metrics }: { metrics: BiasMetric[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Fairness Monitoring</CardTitle>
        <CardDescription>Selection rates by group, as reported by the assessment service</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={metrics} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(214 32% 91%)" vertical={false} />
              <XAxis dataKey="group" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis fontSize={12} tickLine={false} axisLine={false} unit="%" />
              <Tooltip contentStyle={{ borderRadius: 8 }} cursor={{ fill: "hsl(210 40% 96%)" }} />
              <Bar dataKey="selectionRate" name="Selection rate" fill="hsl(221 83% 53%)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

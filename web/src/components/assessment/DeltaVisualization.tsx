"use client";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  CartesianGrid,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

// Visualizes the two scores and their gap as a small bar chart. Values are
// backend-supplied; the chart performs no computation beyond the difference.
export function DeltaVisualization({
  traditionalScore,
  capabilityScore,
}: {
  traditionalScore: number;
  capabilityScore: number;
}) {
  const data = [
    { name: "Traditional", value: traditionalScore, fill: "hsl(215 16% 47%)" },
    { name: "Capability", value: capabilityScore, fill: "hsl(221 83% 53%)" },
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle>Score Comparison</CardTitle>
        <CardDescription>Side-by-side view of the two scoring models</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(214 32% 91%)" vertical={false} />
              <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ borderRadius: 8 }} cursor={{ fill: "hsl(210 40% 96%)" }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={64}>
                {data.map((d, i) => (
                  <Cell key={i} fill={d.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

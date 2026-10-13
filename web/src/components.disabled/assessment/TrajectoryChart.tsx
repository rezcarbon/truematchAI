"use client";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import type { TrajectoryPoint } from "@/lib/types";

// Recharts career-arc visualization. Plots backend-supplied capability and
// scope estimates over time.
export function TrajectoryChart({ data }: { data: TrajectoryPoint[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Career Trajectory</CardTitle>
        <CardDescription>Capability and scope of responsibility over time</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="capFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(221 83% 53%)" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="hsl(221 83% 53%)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="scopeFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(142 71% 45%)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(142 71% 45%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(214 32% 91%)" />
              <XAxis dataKey="period" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: "1px solid hsl(214 32% 91%)" }}
                labelFormatter={(label, payload) => {
                  const role = payload?.[0]?.payload?.role;
                  return role ? `${label} — ${role}` : label;
                }}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="capability"
                name="Capability"
                stroke="hsl(221 83% 53%)"
                fill="url(#capFill)"
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="scope"
                name="Scope"
                stroke="hsl(142 71% 45%)"
                fill="url(#scopeFill)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

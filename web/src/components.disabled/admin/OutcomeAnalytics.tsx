"use client";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export interface OutcomePoint {
  month: string;
  traditionalHires: number;
  capabilityHires: number;
}

// Tracks hiring outcomes attributed to each scoring lens over time. All
// figures are backend-supplied.
export function OutcomeAnalytics({ data }: { data: OutcomePoint[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Outcome Analytics</CardTitle>
        <CardDescription>Hires influenced by capability vs traditional signals</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(214 32% 91%)" />
              <XAxis dataKey="month" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ borderRadius: 8 }} />
              <Legend />
              <Line type="monotone" dataKey="capabilityHires" name="Capability-led" stroke="hsl(221 83% 53%)" strokeWidth={2} />
              <Line type="monotone" dataKey="traditionalHires" name="Traditional-led" stroke="hsl(215 16% 47%)" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

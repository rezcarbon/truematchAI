import { Gauge } from "@/components/ui/gauge";

// Display wrapper around the gauge primitive. The score is backend-supplied.
export function ScoreGauge({
  score,
  label,
  size = 120,
}: {
  score: number;
  label?: string;
  size?: number;
}) {
  return <Gauge value={score} label={label} size={size} />;
}

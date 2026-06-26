"use client";

// Renders a structured "dashboard" block emitted by the chat agent inside a
// ```truematch-dashboard fenced JSON code block. Keeps interactive metrics out
// of brittle prose-parsing: the agent emits data, the client renders widgets.
//
// Contract (all fields optional except cards[].label):
// {
//   "title": "System Status",
//   "cards": [
//     { "label": "Active Assessments", "value": "42", "delta": "+12%",
//       "intent": "up", "hint": "vs last week",
//       "prompt": "Show the assessment queue",   // click -> sends this message
//       "href": "/admin/analytics/pipeline" }    // or navigates here
//   ]
// }

import Link from "next/link";
import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export type DashboardIntent = "up" | "down" | "good" | "warn" | "bad" | "neutral";

export interface DashboardCard {
  label: string;
  value?: string | number;
  delta?: string;
  intent?: DashboardIntent;
  hint?: string;
  prompt?: string;
  href?: string;
}

export interface DashboardData {
  title?: string;
  cards: DashboardCard[];
}

const INTENT_BADGE: Record<DashboardIntent, "default" | "secondary" | "warning" | "destructive"> = {
  up: "default",
  good: "default",
  down: "destructive",
  bad: "destructive",
  warn: "warning",
  neutral: "secondary",
};

function DeltaIcon({ intent }: { intent?: DashboardIntent }) {
  if (intent === "up" || intent === "good") return <ArrowUpRight className="h-3 w-3" />;
  if (intent === "down" || intent === "bad") return <ArrowDownRight className="h-3 w-3" />;
  return <Minus className="h-3 w-3" />;
}

function CardBody({ card }: { card: DashboardCard }) {
  return (
    <div className="flex flex-col gap-1 p-4">
      <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {card.label}
      </span>
      <div className="flex items-baseline gap-2">
        {card.value !== undefined && (
          <span className="text-2xl font-semibold tabular-nums">{card.value}</span>
        )}
        {card.delta && (
          <Badge variant={INTENT_BADGE[card.intent ?? "neutral"]} className="gap-0.5">
            <DeltaIcon intent={card.intent} />
            {card.delta}
          </Badge>
        )}
      </div>
      {card.hint && <span className="text-xs text-muted-foreground">{card.hint}</span>}
    </div>
  );
}

export function DashboardWidget({
  data,
  onPrompt,
}: {
  data: DashboardData;
  onPrompt?: (text: string) => void;
}) {
  const cards = Array.isArray(data.cards) ? data.cards : [];
  if (cards.length === 0) return null;

  return (
    <div className="my-3 not-prose">
      {data.title && (
        <h4 className="mb-2 text-sm font-semibold text-foreground">{data.title}</h4>
      )}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {cards.map((card, i) => {
          const interactive = Boolean(card.href || (card.prompt && onPrompt));
          const base =
            "overflow-hidden transition-colors " +
            (interactive ? "cursor-pointer hover:border-primary hover:bg-secondary/40" : "");

          if (card.href) {
            return (
              <Link key={i} href={card.href} className="block">
                <Card className={base}>
                  <CardBody card={card} />
                </Card>
              </Link>
            );
          }
          if (card.prompt && onPrompt) {
            return (
              <button key={i} type="button" onClick={() => onPrompt(card.prompt!)} className="text-left">
                <Card className={base}>
                  <CardBody card={card} />
                </Card>
              </button>
            );
          }
          return (
            <Card key={i} className={base}>
              <CardBody card={card} />
            </Card>
          );
        })}
      </div>
    </div>
  );
}

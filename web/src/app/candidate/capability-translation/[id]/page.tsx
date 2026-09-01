"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CapabilityGap } from "@/components/shared/CapabilityGap";
import { LanguageBadge, languageName } from "@/components/shared/LanguageBadge";
import { api, type CapabilityTranslationResult } from "@/lib/api";
import { Loader2, Copy, Check, Sparkles, ShieldCheck, ChevronDown, ChevronUp } from "lucide-react";

const STRENGTH_VARIANT: Record<string, "success" | "secondary" | "warning"> = {
  HIGH: "success",
  MEDIUM: "secondary",
  WEAK: "warning",
};

export default function TranslationResultPage({ params }: { params: { id: string } }) {
  const [data, setData] = useState<CapabilityTranslationResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [showOriginal, setShowOriginal] = useState(false);

  useEffect(() => {
    let active = true;
    let tries = 0;
    const poll = async () => {
      try {
        const r = await api.getCapabilityTranslation(params.id);
        if (!active) return;
        setData(r);
        if (r.status === "completed" || r.status === "failed") return;
      } catch {
        /* keep polling */
      }
      if (active && tries++ < 60) setTimeout(poll, 4000);
    };
    poll();
    return () => {
      active = false;
    };
  }, [params.id]);

  const copyRewrite = async () => {
    if (!data) return;
    const lines = [
      data.summary ?? "",
      "",
      data.skills.length ? `Skills: ${data.skills.join(", ")}` : "",
      "",
      ...data.bullets.map((b) => `• ${b.text}`),
    ];
    await navigator.clipboard.writeText(lines.filter(Boolean).join("\n"));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!data || (data.status !== "completed" && data.status !== "failed")) {
    return (
      <div className="mx-auto flex max-w-2xl flex-col items-center gap-3 py-20 text-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">
          Translating your capability into ATS-legible language… this takes a minute.
        </p>
      </div>
    );
  }

  if (data.status === "failed") {
    return (
      <div className="mx-auto max-w-2xl py-16">
        <Card className="border-destructive/40">
          <CardHeader>
            <CardTitle>Translation failed</CardTitle>
            <CardDescription>{data.error || "Something went wrong. Please try again."}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 py-2">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
          <Sparkles className="h-6 w-6 text-primary" /> Your capability, made legible
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {data.targetRole ? `Targeted at: ${data.targetRole}. ` : ""}Every line below is grounded in
          your real experience — nothing was invented.
        </p>
        {languageName(data.sourceLanguage) && (
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <LanguageBadge language={data.sourceLanguage} label="Original CV in" />
            <span className="text-xs text-muted-foreground">
              We translated it to English and re-expressed it for ATS systems — your original is below.
            </span>
          </div>
        )}
      </div>

      {/* Measured before → after lift — the signature gap visual */}
      <CapabilityGap
        beforeKeyword={data.beforeKeywordScore ?? 0}
        afterKeyword={data.afterKeywordScore ?? 0}
        beforeSemantic={data.beforeSemanticScore ?? 0}
        afterSemantic={data.afterSemanticScore ?? 0}
        capability={data.capabilityScore}
        targetRole={data.targetRole}
      />

      {/* The rewrite */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>ATS-optimized rewrite</CardTitle>
            <CardDescription>Grounded re-expression of your evidenced capability.</CardDescription>
          </div>
          <Button variant="outline" size="sm" className="gap-1.5 shrink-0" onClick={copyRewrite}>
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? "Copied" : "Copy"}
          </Button>
        </CardHeader>
        <CardContent className="space-y-5">
          {data.summary && (
            <div>
              <div className="mb-1 text-xs font-medium uppercase text-muted-foreground">Summary</div>
              <p className="text-sm">{data.summary}</p>
            </div>
          )}

          {data.skills.length > 0 && (
            <div>
              <div className="mb-1.5 text-xs font-medium uppercase text-muted-foreground">Skills</div>
              <div className="flex flex-wrap gap-1.5">
                {data.skills.map((s) => (
                  <Badge key={s} variant="outline">
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {data.bullets.length > 0 && (
            <div>
              <div className="mb-2 text-xs font-medium uppercase text-muted-foreground">
                Experience (each line traced to your resume)
              </div>
              <ul className="space-y-3">
                {data.bullets.map((b, i) => (
                  <li key={i} className="rounded-md border bg-muted/30 p-3">
                    <p className="text-sm">{b.text}</p>
                    <div className="mt-1.5 flex items-center gap-2 text-xs text-muted-foreground">
                      <Badge variant={STRENGTH_VARIANT[b.evidenceStrength] ?? "secondary"}>
                        {b.evidenceStrength}
                      </Badge>
                      <span className="flex items-center gap-1">
                        <ShieldCheck className="h-3 w-3" /> grounded in: {b.grounding}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Original (non-English) CV — retained verbatim, never altered */}
      {languageName(data.sourceLanguage) && data.originalText && (
        <Card>
          <CardHeader className="py-3">
            <button
              type="button"
              onClick={() => setShowOriginal((v) => !v)}
              className="flex w-full items-center justify-between text-left"
            >
              <div className="flex items-center gap-2">
                <CardTitle className="text-base">
                  Original CV ({languageName(data.sourceLanguage)})
                </CardTitle>
                <LanguageBadge language={data.sourceLanguage} label="" size="xs" />
              </div>
              {showOriginal ? (
                <ChevronUp className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              )}
            </button>
            {!showOriginal && (
              <CardDescription>
                Your original text, kept verbatim for reference. Click to view.
              </CardDescription>
            )}
          </CardHeader>
          {showOriginal && (
            <CardContent>
              <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-sm font-sans">
                {data.originalText}
              </pre>
            </CardContent>
          )}
        </Card>
      )}

      {/* Honesty line */}
      {(data.translationNotes || data.droppedUngrounded > 0 || data.stillMissingKeywords.length > 0) && (
        <Card className="border-amber-200 bg-amber-50/50">
          <CardHeader>
            <CardTitle className="text-base">What we did NOT add</CardTitle>
            <CardDescription>
              We never fabricate. These are genuine gaps to consider building — not keywords to stuff.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {data.translationNotes && <p>{data.translationNotes}</p>}
            {data.droppedUngrounded > 0 && (
              <p className="text-muted-foreground">
                {data.droppedUngrounded} suggested line(s) were dropped because your resume didn&apos;t
                support them.
              </p>
            )}
            {data.stillMissingKeywords.length > 0 && (
              <div>
                <span className="text-muted-foreground">Still not matched: </span>
                {data.stillMissingKeywords.join(", ")}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

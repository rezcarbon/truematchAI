import { Languages } from "lucide-react";
import { cn } from "@/lib/utils";

// ISO 639-1 (and a few common 639-2/3) → display name. Unknown codes fall back
// to an upper-cased code so the badge still renders meaningfully.
const LANGUAGE_NAMES: Record<string, string> = {
  ms: "Malay",
  zh: "Mandarin",
  "zh-cn": "Mandarin",
  "zh-tw": "Mandarin",
  cmn: "Mandarin",
  ja: "Japanese",
  ko: "Korean",
  hi: "Hindi",
  ta: "Tamil",
  te: "Telugu",
  bn: "Bengali",
  ml: "Malayalam",
  pa: "Punjabi",
  ur: "Urdu",
  th: "Thai",
  vi: "Vietnamese",
  id: "Indonesian",
  tl: "Tagalog",
  ar: "Arabic",
  he: "Hebrew",
  ru: "Russian",
  de: "German",
  fr: "French",
  es: "Spanish",
  pt: "Portuguese",
  it: "Italian",
  nl: "Dutch",
  tr: "Turkish",
  fa: "Persian",
};

export function languageName(code?: string | null): string | null {
  if (!code) return null;
  const c = code.trim().toLowerCase();
  if (!c || c === "en" || c === "eng" || c === "und" || c === "unknown") return null;
  return LANGUAGE_NAMES[c] ?? c.toUpperCase();
}

/**
 * Shows "Translated from <Language>" when the source CV/JD was non-English and an
 * English pivot was scored. Renders nothing for English (or unknown) input, so it
 * is safe to drop in unconditionally.
 */
export function LanguageBadge({
  language,
  label = "Translated from",
  size = "sm",
}: {
  language?: string | null;
  label?: string;
  size?: "sm" | "xs";
}) {
  const name = languageName(language);
  if (!name) return null;
  return (
    <span
      title={`Original ${name} text was machine-translated to an English pivot for scoring. Keyword scoring is language-invariant; the semantic and capability signals are language-responsive — they reflect how legibly the evidence reads in translation. The original is retained.`}
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-medium",
        "bg-violet-50 border border-violet-200 text-violet-700",
        size === "xs" ? "px-1.5 py-0.5 text-[9px]" : "px-2 py-0.5 text-xs"
      )}
    >
      <Languages className={size === "xs" ? "h-2.5 w-2.5" : "h-3 w-3"} />
      {label ? `${label} ${name}` : name}
    </span>
  );
}

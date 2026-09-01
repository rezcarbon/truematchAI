'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, type ReferralInfo } from "@/lib/api";
import { Gift, Copy, Check, Loader2 } from "lucide-react";

export default function ReferPage(): React.ReactElement {
  const [info, setInfo] = useState<ReferralInfo | null>(null);
  const [copied, setCopied] = useState(false);
  const [code, setCode] = useState("");
  const [redeemMsg, setRedeemMsg] = useState<string | null>(null);
  const [redeemErr, setRedeemErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.getReferral().then(setInfo).catch(() => {}); }, []);

  const link = info?.code ? `${info.share_base.replace(/\/share$/, "")}/pricing?ref=${info.code}` : "";

  const copy = async (): Promise<void> => {
    if (!link) return;
    await navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const redeem = async (): Promise<void> => {
    setRedeemErr(null); setRedeemMsg(null); setBusy(true);
    try {
      const r = await api.redeemReferral(code.trim());
      setRedeemMsg(`+${r.granted_credits} credit — balance ${r.balance}.`);
      setCode("");
      api.getReferral().then(setInfo).catch(() => {});
    } catch (e) {
      setRedeemErr(e instanceof Error ? e.message : "Could not redeem code");
    } finally { setBusy(false); }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
          <Gift className="h-6 w-6 text-blue-600" /> Refer & earn
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Share your link. They get their first assessment free — you get a free credit for every friend who joins.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Your referral link</CardTitle>
          <CardDescription>Anyone who signs up and redeems your code earns you both a credit.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input readOnly value={link} placeholder={info ? "" : "Loading…"} className="font-mono text-sm" />
            <Button onClick={copy} disabled={!link} variant="outline" className="shrink-0">
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          {info && (
            <p className="mt-3 text-sm text-muted-foreground">
              Code <span className="font-mono font-semibold text-foreground">{info.code}</span> ·{" "}
              {info.referrals} referral{info.referrals === 1 ? "" : "s"} ·{" "}
              {info.credits_earned} credit{info.credits_earned === 1 ? "" : "s"} earned
            </p>
          )}
        </CardContent>
      </Card>

      <Card className="mt-5">
        <CardHeader>
          <CardTitle className="text-base">Have a referral code?</CardTitle>
          <CardDescription>Redeem a friend&apos;s code for a free assessment credit (once per account).</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="e.g. AB12CD34"
              className="font-mono"
            />
            <Button onClick={redeem} disabled={busy || code.trim().length === 0} className="shrink-0">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Redeem"}
            </Button>
          </div>
          {redeemMsg && <p className="mt-3 text-sm text-green-700">{redeemMsg}</p>}
          {redeemErr && <p className="mt-3 text-sm text-red-700">{redeemErr}</p>}
        </CardContent>
      </Card>
    </div>
  );
}

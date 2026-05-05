import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { PredictResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

interface PredictFormData {
  proto: string;
  service: string;
  state: string;
  dur: number;
  spkts: number;
  dpkts: number;
  sbytes: number;
  dbytes: number;
  rate: number;
  sttl: number;
  dttl: number;
}

const initial: PredictFormData = {
  proto: "tcp",
  service: "-",
  state: "INT",
  dur: 0.5,
  spkts: 5,
  dpkts: 3,
  sbytes: 500,
  dbytes: 1500,
  rate: 100,
  sttl: 64,
  dttl: 64,
};

export function ManualPredictForm() {
  const [form, setForm] = useState<PredictFormData>(initial);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [serverDebug, setServerDebug] = useState<any | null>(null);

  const mutation = useMutation({
    mutationFn: (p: PredictFormData) => api.predict({ features: p }),
    onSuccess: (r) => {
      setResult(r);
      toast.success(`Prediction: ${r.decision}`);
    },
    onError: (e: Error) => toast.error(`Predict failed: ${e.message}`),
  });

  function update<K extends keyof PredictFormData>(k: K, v: PredictFormData[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  function num(k: keyof PredictFormData) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      update(k, Number(e.target.value) as PredictFormData[typeof k]);
  }

  function str(k: keyof PredictFormData) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      update(k, e.target.value as PredictFormData[typeof k]);
  }

  const decision = result?.decision?.toString().toUpperCase();
  const isAttack =
    decision === "BLOCK" || decision === "ATTACK" || decision === "ALERT" || decision === "MALICIOUS";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Manual Prediction</CardTitle>
        <CardDescription>Submit network flow features to the model for classification.</CardDescription>
      </CardHeader>
      <CardContent>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate(form);
          }}
          className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3"
        >
          <Field label="Protocol" id="proto">
            <Input id="proto" value={form.proto} onChange={str("proto")} placeholder="tcp" />
          </Field>
          <Field label="Service" id="service">
            <Input id="service" value={form.service} onChange={str("service")} placeholder="-" />
          </Field>
          <Field label="State" id="state">
            <Input id="state" value={form.state} onChange={str("state")} placeholder="INT" />
          </Field>
          <Field label="Duration (s)" id="dur">
            <Input id="dur" type="number" step="0.01" value={form.dur} onChange={num("dur")} />
          </Field>
          <Field label="Source Packets" id="spkts">
            <Input id="spkts" type="number" value={form.spkts} onChange={num("spkts")} />
          </Field>
          <Field label="Dest Packets" id="dpkts">
            <Input id="dpkts" type="number" value={form.dpkts} onChange={num("dpkts")} />
          </Field>
          <Field label="Source Bytes" id="sbytes">
            <Input id="sbytes" type="number" value={form.sbytes} onChange={num("sbytes")} />
          </Field>
          <Field label="Dest Bytes" id="dbytes">
            <Input id="dbytes" type="number" value={form.dbytes} onChange={num("dbytes")} />
          </Field>
          <Field label="Rate" id="rate">
            <Input id="rate" type="number" value={form.rate} onChange={num("rate")} />
          </Field>
          <Field label="Source TTL" id="sttl">
            <Input id="sttl" type="number" value={form.sttl} onChange={num("sttl")} />
          </Field>
          <Field label="Dest TTL" id="dttl">
            <Input id="dttl" type="number" value={form.dttl} onChange={num("dttl")} />
          </Field>

          <div className="sm:col-span-2 lg:col-span-3">
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Predicting…" : "Run Prediction"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="ml-2"
              onClick={async () => {
                try {
                  const d = await api.debugLastPredict();
                  setServerDebug(d);
                  toast.success("Fetched server debug");
                } catch (e: any) {
                  toast.error(`Debug fetch failed: ${e?.message ?? e}`);
                }
              }}
            >
              Fetch Server Last Predict
            </Button>
          </div>
        </form>

        {result && (
          <div className="mt-4 rounded-md border border-border bg-muted/40 p-3">
            <div className="flex items-center gap-2">
              <Badge
                className={
                  isAttack
                    ? "bg-destructive text-destructive-foreground"
                    : "bg-success text-success-foreground"
                }
              >
                {decision}
              </Badge>
              {typeof result.confidence === "number" && (
                <span className="font-mono text-sm">
                  Confidence: {(result.confidence * 100).toFixed(2)}%
                </span>
              )}
              {(result.reason || (result as any).rule) && (
                <span className="text-sm text-muted-foreground">— {result.reason ?? (result as any).rule}</span>
              )}
            </div>
            <pre className="mt-2 max-h-48 overflow-auto rounded bg-background p-2 font-mono text-xs">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}

        {serverDebug && (
          <div className="mt-4 rounded-md border border-border bg-muted/40 p-3">
            <div className="flex items-center gap-2">
              <strong>Server last predict</strong>
            </div>
            <pre className="mt-2 max-h-48 overflow-auto rounded bg-background p-2 font-mono text-xs">
              {JSON.stringify(serverDebug, null, 2)}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Field({
  label,
  id,
  children,
}: {
  label: string;
  id: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className="text-xs">{label}</Label>
      {children}
    </div>
  );
}

/**
 * The planner phase machine. Owns all app state and is the only caller of the
 * API client. Phases: input -> thinking -> result. The backend does the real
 * planning; this hook orchestrates presentation (streamed steps, refine chat).
 */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  getConfig,
  refine as apiRefine,
  streamPlan,
  type AppConfig,
  type Plan,
  type TimelineStep,
} from "../api/client";
import { DEFAULT_CHIPS, FALLBACK_PLAN, type Chip } from "../data/seed";

export type Phase = "input" | "thinking" | "result";

export interface RefineMessage {
  role: "user" | "agent";
  text: string;
}

export function usePlanner() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [phase, setPhase] = useState<Phase>("input");
  const [request, setRequest] = useState("");
  const [requestEcho, setRequestEcho] = useState("");
  const [chips, setChips] = useState<Chip[]>(DEFAULT_CHIPS);
  const [streamedSteps, setStreamedSteps] = useState<TimelineStep[]>([]);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [messages, setMessages] = useState<RefineMessage[]>([]);
  const [replanning, setReplanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    getConfig().then(setConfig).catch(() => setConfig({ seedMode: true, hasKey: false }));
  }, []);

  const activePreferences = useCallback(
    () => chips.filter((c) => c.on).map((c) => c.label),
    [chips],
  );

  const toggleChip = useCallback((id: string) => {
    setChips((cs) => cs.map((c) => (c.id === id ? { ...c, on: !c.on } : c)));
  }, []);

  const submit = useCallback(
    async (textOverride?: string) => {
      const text = (textOverride ?? request).trim();
      setRequestEcho(text || "Plan my weekend 4–5 July 2026.");
      setError(null);
      setStreamedSteps([]);
      setPlan(null);
      setMessages([]);
      setPhase("thinking");

      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;

      try {
        await streamPlan(
          { request: text, preferences: activePreferences() },
          {
            onStep: (step) =>
              setStreamedSteps((prev) =>
                prev.some((s) => s.key === step.key) ? prev : [...prev, step],
              ),
            onResult: (p) => {
              setPlan(p);
              // brief hold so the last step reads as done before the payoff
              window.setTimeout(() => setPhase("result"), 600);
            },
            onError: (msg) => setError(msg),
          },
          ctrl.signal,
        );
      } catch (e) {
        if ((e as Error).name === "AbortError") return;
        // graceful offline fallback so the UI is never dead
        setError((e as Error).message);
        setPlan(FALLBACK_PLAN);
        window.setTimeout(() => setPhase("result"), 400);
      }
    },
    [request, activePreferences],
  );

  const sendRefine = useCallback(
    async (message: string) => {
      if (!plan || !message.trim()) return;
      setMessages((m) => [...m, { role: "user", text: message }]);
      setReplanning(true);
      try {
        const res = await apiRefine({
          request: requestEcho,
          preferences: activePreferences(),
          message,
          plan,
        });
        setPlan(res.plan);
        setMessages((m) => [...m, { role: "agent", text: res.reply }]);
      } catch (e) {
        setMessages((m) => [
          ...m,
          { role: "agent", text: `Sorry — refine failed (${(e as Error).message}).` },
        ]);
      } finally {
        setReplanning(false);
      }
    },
    [plan, requestEcho, activePreferences],
  );

  const startOver = useCallback(() => {
    abortRef.current?.abort();
    setPhase("input");
    setPlan(null);
    setStreamedSteps([]);
    setMessages([]);
    setError(null);
  }, []);

  return {
    config,
    phase,
    request,
    setRequest,
    requestEcho,
    chips,
    toggleChip,
    streamedSteps,
    plan,
    messages,
    replanning,
    error,
    submit,
    sendRefine,
    startOver,
  };
}

import { AgentTimeline } from "./components/AgentTimeline";
import { Header } from "./components/Header";
import { Itinerary } from "./components/Itinerary";
import { RequestInput } from "./components/RequestInput";
import { usePlanner } from "./hooks/usePlanner";

export default function App() {
  const p = usePlanner();

  return (
    <div className="app">
      <Header
        config={p.config}
        showStartOver={p.phase !== "input"}
        onStartOver={p.startOver}
      />

      <main className="app-main">
        {p.phase === "input" && (
          <RequestInput
            request={p.request}
            setRequest={p.setRequest}
            chips={p.chips}
            onToggle={p.toggleChip}
            onSubmit={p.submit}
          />
        )}

        {p.phase === "thinking" && (
          <AgentTimeline requestEcho={p.requestEcho} steps={p.streamedSteps} />
        )}

        {p.phase === "result" && p.plan && (
          <Itinerary
            plan={p.plan}
            messages={p.messages}
            replanning={p.replanning}
            onRefine={p.sendRefine}
          />
        )}
      </main>

      {p.error && p.phase !== "result" && (
        <div className="error-toast mono" role="alert">
          {p.error}
        </div>
      )}
    </div>
  );
}

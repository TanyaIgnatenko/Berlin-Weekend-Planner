interface Props {
  config: { seedMode: boolean } | null;
  showStartOver: boolean;
  onStartOver: () => void;
}

export function Header({ config, showStartOver, onStartOver }: Props) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark mono" aria-hidden="true">
          B
        </span>
        <span className="brand-word">Berlin Weekend Planner</span>
      </div>
      <div className="header-right">
        {config?.seedMode && (
          <span className="mode-badge mono" title="Running the offline sample scenario — no API key in use.">
            SEED MODE
          </span>
        )}
        {showStartOver && (
          <button className="ghost-btn mono" onClick={onStartOver}>
            ↺ Start over
          </button>
        )}
      </div>
    </header>
  );
}

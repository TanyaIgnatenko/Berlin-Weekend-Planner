interface Props {
  message: string;
  onClose: () => void;
}

/** Shown when the backend returns 429 (demo request cap reached). Explains what
 *  happened and why, briefly, instead of silently failing or faking a plan. */
export function RateLimitModal({ message, onClose }: Props) {
  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="rl-title"
      onClick={onClose}
    >
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <span className="modal-kicker mono">DEMO LIMIT</span>
        <h2 id="rl-title" className="modal-title">
          You've hit the demo request limit
        </h2>
        <p className="modal-body">{message}</p>
        <p className="modal-note">
          This is a live demo running a real AI agent, so requests are capped to
          keep it free for everyone. The limit resets — please try again later.
        </p>
        <button className="cta-btn modal-btn" onClick={onClose} autoFocus>
          Got it
        </button>
      </div>
    </div>
  );
}

/** The "agent is intelligent" moment. Two flavours:
 *  - weather swap (ochre, ↺): outdoor → indoor because it's wet.
 *  - refine edit (green, ✎): a card changed by a refine. */
interface Props {
  kind: "swap" | "edit";
  text: string;
}

export function SwapCallout({ kind, text }: Props) {
  const glyph = kind === "swap" ? "↺" : "✎";
  // bold the leading "Word." (e.g. "Weather swap." / "Updated.")
  const m = text.match(/^(\S[^.]*\.)\s*(.*)$/);
  return (
    <div className={`callout ${kind}`} role="note">
      <span className="callout-glyph mono" aria-hidden="true">
        {glyph}
      </span>
      <span className="callout-text">
        {m ? (
          <>
            <strong>{m[1]}</strong> {m[2]}
          </>
        ) : (
          text
        )}
      </span>
    </div>
  );
}

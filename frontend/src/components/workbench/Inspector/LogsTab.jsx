import React from "react";

export function LogsTab({ events }) {
  return (
    <div className="flex flex-col gap-2">
      {events.map((event) =>
        event.type === "trace.separator" ? (
          <div
            className="rounded-md border border-accent/25 bg-accent/10 px-3 py-2 text-center text-[11px] font-semibold uppercase tracking-wide text-accent"
            key={event.id}
            role="separator"
          >
            {event.detail}
          </div>
        ) : (
          <div
            className="grid grid-cols-[72px_minmax(0,1fr)] gap-3 rounded-md bg-white/[0.025] p-2 text-sm"
            key={event.id}
          >
            <span className="font-mono text-xs text-dim">{event.time}</span>
            <div>
              <strong className="block truncate text-xs">{event.type}</strong>
              <p className="mt-1 text-xs leading-snug text-muted">
                {typeof event.detail === "string" ? event.detail : JSON.stringify(event.detail)}
              </p>
              <small className="text-dim">{event.actor}</small>
            </div>
          </div>
        )
      )}
    </div>
  );
}

import React from "react";

export function EmptyState({ detail, icon: Icon, title }) {
  return (
    <div className="grid min-h-44 place-items-center rounded-lg border border-dashed border-white/15 bg-black/15 p-4 text-center">
      <div className="grid place-items-center gap-2">
        <Icon className="text-muted" size={28} />
        <strong>{title}</strong>
        <p className="max-w-[260px] text-sm leading-snug text-muted">{detail}</p>
      </div>
    </div>
  );
}

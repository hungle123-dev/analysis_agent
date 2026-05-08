import React from "react";

export function Panel({ title, meta, children }) {
  return (
    <section className="mb-3 border border-line bg-white/[0.025] p-3">
      <div className="mb-2 flex items-center justify-between text-[11px] font-extrabold uppercase text-muted">
        <span>{title}</span>
        <code>{meta}</code>
      </div>
      {children}
    </section>
  );
}

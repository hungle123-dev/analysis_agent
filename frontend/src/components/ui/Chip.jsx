import React from "react";

export function Chip({ children }) {
  return <span className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-muted">{children}</span>;
}

import React from "react";
import { statusLabel, statusTone } from "../../lib/constants";

export function StatusBadge({ status }) {
  return (
    <div className={`status-badge border bg-white/[0.05] px-2.5 py-1 text-xs font-medium ${statusTone[status]}`}>
      {statusLabel[status]}
    </div>
  );
}

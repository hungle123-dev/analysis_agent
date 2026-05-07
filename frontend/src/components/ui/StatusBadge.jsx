import React from "react";
import { statusLabel, statusTone } from "../../lib/constants";

export function StatusBadge({ status }) {
  return (
    <div className={`status-badge rounded-lg border bg-white/[0.05] px-3 py-1.5 text-sm font-medium ${statusTone[status]}`}>
      {statusLabel[status]}
    </div>
  );
}

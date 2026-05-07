import React from "react";
import { Chip } from "../ui/Chip";

export function ProposalHeader({ proposal }) {
  return (
    <div className="px-4 py-3 shrink-0">
      <div className="mb-2 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold">Review generated analysis code</h1>
          <p className="text-[11px] font-extrabold uppercase text-muted mt-1">
            AI proposal: {proposal?.summary ?? "Monthly revenue trend"}
          </p>
        </div>
        <span className="rounded-full border border-amber-soft/35 bg-amber-soft/10 px-2.5 py-1 text-xs font-bold text-[#ffe6ac]">
          {proposal?.risk_flags?.[0] ?? "creates_chart_file"}
        </span>
      </div>
      <p className="text-sm text-muted truncate max-w-full" title="Creates a dataframe copy, groups revenue by month, prints a summary table, and saves a chart artifact.">
        {proposal?.explanation ?? "Creates a dataframe copy, groups revenue by month, prints a summary table, and saves a chart artifact."}
      </p>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        {(proposal?.expected_outputs ?? ["table", "chart"]).map((item) => (
          <Chip key={item}>{item}</Chip>
        ))}
      </div>
    </div>
  );
}

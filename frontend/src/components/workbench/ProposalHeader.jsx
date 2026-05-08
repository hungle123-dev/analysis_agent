import React from "react";
import { Chip } from "../ui/Chip";

export function ProposalHeader({ proposal }) {
  const outputs = proposal?.expected_outputs ?? [];

  return (
    <div className="shrink-0 border-b border-line bg-panel px-4 py-3">
      <div className="mb-2 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold">Review generated analysis code</h1>
          <p className="text-[11px] font-extrabold uppercase text-muted mt-1">
            AI proposal: {proposal?.summary ?? "No proposal generated yet"}
          </p>
        </div>
        {proposal?.risk_flags?.[0] && (
          <span className="border border-amber-soft/35 bg-amber-soft/10 px-2.5 py-1 text-xs font-bold text-amber-soft">
            {proposal.risk_flags[0]}
          </span>
        )}
      </div>
      <p className="max-w-full truncate text-sm text-muted" title={proposal?.explanation ?? "Generate a proposal to inspect the explanation here."}>
        {proposal?.explanation ?? "Generate a proposal to inspect the explanation here."}
      </p>
      {outputs.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          {outputs.map((item) => (
            <Chip key={item}>{item}</Chip>
          ))}
        </div>
      )}
    </div>
  );
}

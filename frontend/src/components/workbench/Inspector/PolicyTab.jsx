import React from "react";
import { AlertTriangle, Check } from "lucide-react";

const defaultRules = [
  [
    "Danh sách import được phép",
    "Cho phép pandas, numpy, matplotlib, seaborn, scipy (stats/optimize), các module sklearn, statsmodels, math, statistics, datetime và collections."
  ],
  ["Giới hạn dataset", "Code chỉ được dùng df đã nạp sẵn, không được đọc thêm file hay dataset khác."],
  ["Không truy cập shell", "os.system, subprocess, socket, requests, urllib đều bị chặn."],
  ["Output bị giới hạn phạm vi", "File sinh ra phải nằm trong outputs/{run_id}, không được ghi ra ngoài."],
  ["Bắt buộc phê duyệt", "Thực thi sẽ bị từ chối nếu code_hash không khớp với bản đã phê duyệt."]
];

export function PolicyTab({ issues = [] }) {
  if (issues.length > 0) {
    return (
      <div className="grid gap-2">
        {issues.map((issue, idx) => (
          <div className="rounded-md border border-rose-soft/30 bg-rose-soft/10 p-3" key={`${issue.code}-${idx}`}>
            <div className="flex items-center gap-2 text-sm font-bold text-[#ffd4da]">
              <AlertTriangle size={14} />
              <span>{issue.code}</span>
              <code className="ml-auto text-[11px] uppercase text-rose-soft">{issue.severity}</code>
            </div>
            <p className="mt-1 text-xs leading-snug text-[#ffd4da]">{issue.message}</p>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-2">
      {defaultRules.map(([title, detail]) => (
        <div className="rounded-md border border-white/10 bg-white/[0.025] p-3" key={title}>
          <div className="flex items-center gap-2 text-sm font-bold text-[#cbffef]">
            <Check size={14} />
            {title}
          </div>
          <p className="mt-1 text-xs leading-snug text-muted">{detail}</p>
        </div>
      ))}
    </div>
  );
}

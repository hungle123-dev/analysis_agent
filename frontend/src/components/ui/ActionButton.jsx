import React from "react";
import { buttonBase } from "../../lib/constants";

export function ActionButton({ children, className = "", disabled, icon: Icon, iconClassName = "", onClick, tone }) {
  const toneClass = {
    ghost: "border-line bg-panel-2 text-text-main hover:bg-panel-3",
    danger: "border-rose-soft/40 bg-rose-soft/10 text-[#ffd4da] hover:bg-rose-soft/20",
    approve: "approve-action border-mint bg-mint text-ink hover:bg-mint-deep",
    run: "border-accent bg-accent text-white hover:bg-[#0069ad] disabled:border-white/10 disabled:bg-white/[0.04] disabled:text-dim"
  }[tone];

  return (
    <button className={`${buttonBase} ${toneClass} ${className}`} disabled={disabled} onClick={onClick}>
      {Icon && <Icon size={15} className={iconClassName} />}
      {children}
    </button>
  );
}

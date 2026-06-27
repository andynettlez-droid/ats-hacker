import React from 'react';

type SignalMascotProps = {
  className?: string;
};

type SignalPeekProps = {
  className?: string;
  size?: string;
};

export function SignalMascot({ className = '' }: SignalMascotProps) {
  return (
    <span className={`relative inline-flex items-center justify-center ${className}`} aria-hidden="true">
      <span className="signal-ring signal-ring-a absolute inset-x-[6%] inset-y-[31%] rounded-full border border-cyan-200/75 -rotate-[22deg] shadow-[0_0_18px_rgba(56,213,255,0.38)]" />
      <span className="signal-ring signal-ring-b absolute inset-x-[5%] inset-y-[30%] rounded-full border border-cyan-300/65 rotate-[58deg] shadow-[0_0_18px_rgba(56,213,255,0.3)]" />
      <span className="signal-ring signal-ring-c absolute inset-x-[30%] inset-y-[6%] rounded-full border border-cyan-100/40 rotate-90" />
      <span className="signal-core relative h-[58%] w-[58%] rounded-full bg-[radial-gradient(circle_at_45%_34%,#ffffff_0_9%,#9ff7ff_15%,#38d5ff_28%,#2563eb_62%,#020617_100%)] shadow-[0_0_34px_rgba(56,213,255,0.88),inset_0_0_18px_rgba(255,255,255,0.38)]">
        <span className="signal-eye absolute left-[30%] top-[37%] h-[16%] w-[16%] rounded-full bg-white shadow-[0_0_9px_rgba(255,255,255,0.9)]" />
        <span className="signal-eye absolute right-[30%] top-[37%] h-[16%] w-[16%] rounded-full bg-white shadow-[0_0_9px_rgba(255,255,255,0.9)]" />
        <span className="absolute left-1/2 top-[61%] h-[14%] w-[36%] -translate-x-1/2 rounded-b-full border-b-2 border-white/95" />
      </span>
      <span className="signal-spark signal-spark-a absolute left-[10%] top-[18%] h-[7%] w-[7%] rounded-full bg-white shadow-[0_0_10px_rgba(56,213,255,0.9)]" />
      <span className="signal-spark signal-spark-b absolute right-[6%] top-[34%] h-[6%] w-[6%] rounded-full bg-white/85 shadow-[0_0_10px_rgba(56,213,255,0.9)]" />
      <span className="signal-spark signal-spark-c absolute bottom-[12%] left-[24%] h-[5%] w-[5%] rounded-full bg-cyan-100/90 shadow-[0_0_10px_rgba(56,213,255,0.9)]" />
    </span>
  );
}

export function SignalPeek({ className = '', size = 'h-14 w-14' }: SignalPeekProps) {
  return (
    <span
      className={`pointer-events-none absolute z-10 hidden place-items-center rounded-3xl border border-cyan-200/20 bg-[#07111f]/70 p-2 shadow-[0_0_48px_rgba(56,213,255,0.16),inset_0_0_24px_rgba(56,213,255,0.06)] ring-1 ring-cyan-300/10 backdrop-blur-sm lg:grid ${className}`}
      aria-hidden="true"
    >
      <SignalMascot className={`signal-mascot ${size}`} />
    </span>
  );
}

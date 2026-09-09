export function DocStackHero() {
  return (
    <div className="relative w-full h-[340px] flex items-center justify-center select-none" aria-hidden="true">
      <svg viewBox="0 0 420 340" className="w-full h-full max-w-[440px]">
        <g style={{ transformOrigin: "180px 210px" }} className="animate-float" data-r="-6deg">
          <rect x="120" y="150" width="180" height="130" rx="10" fill="#EAE4FB" transform="rotate(-6 210 215)" />
        </g>
        <g style={{ transformOrigin: "220px 210px", animationDelay: "0.6s" }} className="animate-float">
          <rect x="140" y="130" width="180" height="130" rx="10" fill="#FBEAC8" transform="rotate(4 230 195)" />
        </g>
        <rect x="130" y="100" width="180" height="150" rx="12" fill="#FFFFFF" stroke="#E7E4DD" />
        {[0, 1, 2, 3, 4].map((i) => (
          <rect key={i} x="150" y={128 + i * 18} width={i === 4 ? 80 : 140 - i * 6} height="7" rx="3.5" fill="#EDEBE4" />
        ))}

        <circle cx="300" cy="230" r="30" fill="#DFF3EA" className="animate-pulseRing" style={{ transformOrigin: "300px 230px" }} />
        <circle cx="300" cy="230" r="24" fill="#1F9C77" />
        <path
          d="M289 230l7 7 15-16"
          fill="none"
          stroke="white"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          pathLength={1}
          strokeDasharray={1}
          strokeDashoffset={1}
          className="animate-dash"
        />
      </svg>
    </div>
  );
}

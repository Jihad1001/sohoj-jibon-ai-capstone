import { useEffect, useState } from "react";

const STEPS = ["Understanding", "Discovery", "Verification", "Planning"];

export default function ProgressModal() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((p) => Math.min(p + 1, STEPS.length - 1)), 700);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 w-80 text-center">
        <div className="w-12 h-12 mx-auto border-4 border-green-600 border-t-transparent rounded-full animate-spin mb-4" />
        <ol className="text-left space-y-1">
          {STEPS.map((s, k) => (
            <li key={s} className={k < i ? "text-green-700" : k === i ? "font-bold" : "text-gray-400"}>
              {k < i ? "✓" : k === i ? "…" : "○"} {s}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

import { useState } from "react";

function Gauge({ value }) {
  const pct = Math.round(value * 100);
  const r = 40, c = 2 * Math.PI * r;
  const color = pct >= 75 ? "#16a34a" : pct >= 50 ? "#d97706" : "#dc2626";
  return (
    <svg viewBox="0 0 100 100" className="w-28 h-28">
      <circle cx="50" cy="50" r={r} fill="none" stroke="#e5e7eb" strokeWidth="10" />
      <circle cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
        strokeDasharray={`${(pct / 100) * c} ${c}`} transform="rotate(-90 50 50)" />
      <text x="50" y="56" textAnchor="middle" fontSize="20" fontWeight="bold">{pct}%</text>
    </svg>
  );
}

const BADGE = { High: "bg-green-100 text-green-800", Medium: "bg-amber-100 text-amber-800", Low: "bg-red-100 text-red-800" };

export default function ResultView({ result, onBack }) {
  const [done, setDone] = useState({});
  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4">
      <button onClick={onBack} className="text-sm text-green-700">← নতুন প্রশ্ন</button>

      <div className="bg-white rounded-2xl shadow p-4 flex items-center gap-4">
        <Gauge value={result.confidence_score} />
        <div>
          <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${result.verified_claim ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
            {result.verified_claim ? "✔ যাচাইকৃত" : "✖ যাচাই হয়নি"}
          </div>
          <p className="text-xs text-gray-500 mt-2">প্রশ্ন: {result.query_used}</p>
          {result.latency_ms != null && <p className="text-xs text-gray-400">সময়: {result.latency_ms} ms</p>}
        </div>
      </div>

      {result.input_note && <p className="text-amber-700 text-sm">{result.input_note}</p>}

      {(result.results || []).filter((r) => r.matched).map((r) => (
        <div key={r.feature} className="bg-white rounded-2xl shadow p-4">
          <h3 className="font-semibold text-green-700">{r.feature_name}</h3>
          <p>{r.summary}</p>
        </div>
      ))}

      <div className="bg-white rounded-2xl shadow p-4">
        <h3 className="font-semibold mb-2">করণীয় তালিকা</h3>
        {result.action_plan.map((s, i) => (
          <label key={i} className="flex gap-2 items-start py-1 cursor-pointer">
            <input type="checkbox" checked={!!done[i]} onChange={() => setDone({ ...done, [i]: !done[i] })} className="mt-1" />
            <span className={done[i] ? "line-through text-gray-400" : ""}>{s}</span>
          </label>
        ))}
      </div>

      {result.evidence_sources.length > 0 && (
        <div className="bg-white rounded-2xl shadow p-4">
          <h3 className="font-semibold mb-2">প্রমাণ / উৎস</h3>
          {result.evidence_sources.map((e, i) => (
            <div key={i} className="border-t py-2 text-sm">
              <span className={`text-xs px-2 py-0.5 rounded-full mr-2 ${BADGE[e.trust_label]}`}>{e.trust_label} ({e.trust_score})</span>
              <a href={e.url} target="_blank" rel="noreferrer" className="text-blue-600 underline">{e.title || e.url}</a>
              <p className="text-gray-500">{e.snippet}</p>
              <span className="text-xs text-gray-400">{e.source_type === "local_dataset" ? "স্থানীয় ডেটা স্ন্যাপশট" : "ওয়েব সার্চ"}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

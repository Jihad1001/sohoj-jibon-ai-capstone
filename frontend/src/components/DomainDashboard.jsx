export default function DomainDashboard({ domains, profile, onPick, onLogout }) {
  return (
    <div className="max-w-3xl mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-xl font-bold text-green-700">সহজ জীবন AI</h1>
          <p className="text-sm text-gray-500">জেলা: {profile.district} • {profile.role}</p>
        </div>
        <button onClick={onLogout} className="text-sm text-gray-500 underline">লগআউট</button>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        {domains.map((d) => (
          <button key={d.id} onClick={() => onPick(d)}
            className="bg-white rounded-2xl shadow p-6 text-center hover:shadow-lg hover:bg-green-50 transition">
            <div className="text-5xl mb-2">{d.icon}</div>
            <div className="font-semibold text-lg">{d.name_bn}</div>
            <div className="text-xs text-gray-500">{d.name_en}</div>
            <div className="text-xs text-gray-400 mt-2">{d.description}</div>
            <div className="mt-3 text-green-700 text-sm">🎤 ভয়েসে জিজ্ঞেস করুন</div>
          </button>
        ))}
      </div>
    </div>
  );
}

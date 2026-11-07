import { useState } from "react";

const ROLES = [["Farmer", "কৃষক"], ["Consumer", "ভোক্তা"], ["General", "সাধারণ"]];

// Local-only profile (saved in the browser). Replace with real backend auth later if needed.
export default function AuthProfile({ districts, onDone }) {
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [district, setDistrict] = useState("Dhaka");
  const [role, setRole] = useState("General");
  const [err, setErr] = useState("");

  const submit = (e) => {
    e.preventDefault();
    if (!/^01[3-9]\d{8}$/.test(mobile)) return setErr("সঠিক মোবাইল নম্বর দিন (যেমন 01712345678)");
    if (password.length < 4) return setErr("পাসওয়ার্ড কমপক্ষে ৪ অক্ষর হতে হবে");
    onDone({ mobile, district, role });
  };

  return (
    <form onSubmit={submit} className="max-w-md mx-auto mt-10 bg-white p-6 rounded-2xl shadow space-y-4">
      <h1 className="text-2xl font-bold text-green-700 text-center">সহজ জীবন AI</h1>
      <p className="text-center text-gray-500 text-sm">Sohoj Jibon AI — যাচাইকৃত তথ্য, সহজ সিদ্ধান্ত</p>
      <input className="w-full border rounded-lg p-3" placeholder="মোবাইল নম্বর" value={mobile} onChange={(e) => setMobile(e.target.value)} />
      <input className="w-full border rounded-lg p-3" type="password" placeholder="পাসওয়ার্ড" value={password} onChange={(e) => setPassword(e.target.value)} />
      <select className="w-full border rounded-lg p-3" value={district} onChange={(e) => setDistrict(e.target.value)}>
        {districts.map((d) => <option key={d.en} value={d.en}>{d.bn} ({d.en})</option>)}
      </select>
      <div className="flex gap-2 justify-center">
        {ROLES.map(([en, bn]) => (
          <button type="button" key={en} onClick={() => setRole(en)}
            className={`px-4 py-1 rounded-full border ${role === en ? "bg-green-600 text-white" : "bg-white"}`}>{bn}</button>
        ))}
      </div>
      {err && <p className="text-red-600 text-sm">{err}</p>}
      <button className="w-full bg-green-600 text-white rounded-lg p-3 font-semibold">শুরু করুন</button>
    </form>
  );
}

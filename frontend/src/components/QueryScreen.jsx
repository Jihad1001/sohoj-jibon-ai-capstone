import { useRef, useState } from "react";
import { transcribe } from "../api";

export default function QueryScreen({ domain, districts, profile, onSubmit, onBack }) {
  const [text, setText] = useState("");
  const [district, setDistrict] = useState(profile.district);
  const [image, setImage] = useState(null);
  const [recording, setRecording] = useState(false);
  const [msg, setMsg] = useState("");
  const recRef = useRef(null);
  const chunks = useRef([]);

  const startStop = async () => {
    if (recording) { recRef.current.stop(); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      chunks.current = [];
      rec.ondataavailable = (e) => chunks.current.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        setMsg("ভয়েস লেখায় রূপান্তর হচ্ছে...");
        try {
          const r = await transcribe(new Blob(chunks.current, { type: "audio/webm" }));
          setText((p) => (p + " " + r.text).trim());   // user can EDIT before submit
          setMsg("লেখা ঠিক আছে কিনা দেখে নিন, তারপর জমা দিন।");
        } catch (e) { setMsg(e.message); }
      };
      rec.start();
      recRef.current = rec;
      setRecording(true);
      setMsg("রেকর্ড হচ্ছে... থামাতে আবার চাপ দিন");
    } catch { setMsg("মাইক্রোফোন অনুমতি দিন"); }
  };

  const submit = () => {
    if (!text.trim() && !image) return setMsg("প্রশ্ন লিখুন বা ছবি দিন");
    onSubmit({ domain: domain.id, query_text: text, district, media_file: image });
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      <button onClick={onBack} className="text-sm text-green-700 mb-3">← ফিরে যান</button>
      <h2 className="text-2xl font-bold mb-3">{domain.icon} {domain.name_bn}</h2>
      <textarea rows={4} className="w-full border rounded-xl p-3" placeholder="আপনার প্রশ্ন লিখুন..." value={text} onChange={(e) => setText(e.target.value)} />
      <div className="flex flex-wrap gap-2 my-2">
        {domain.hints.map((h) => (
          <button key={h} onClick={() => setText(h)} className="text-xs bg-green-100 text-green-800 rounded-full px-3 py-1">{h}</button>
        ))}
      </div>
      <div className="flex gap-3 items-center my-3">
        <button onClick={startStop} className={`rounded-full px-4 py-2 text-white ${recording ? "bg-red-600 animate-pulse" : "bg-green-600"}`}>
          🎤 {recording ? "থামান" : "ভয়েস"}
        </button>
        <label className="cursor-pointer bg-white border rounded-full px-4 py-2 text-sm">
          📎 {image ? image.name : "ছবি দিন"}
          <input type="file" accept="image/*" hidden onChange={(e) => setImage(e.target.files[0] || null)} />
        </label>
        <select className="border rounded-lg p-2 text-sm ml-auto" value={district} onChange={(e) => setDistrict(e.target.value)}>
          {districts.map((d) => <option key={d.en} value={d.en}>{d.bn}</option>)}
        </select>
      </div>
      {msg && <p className="text-sm text-amber-700 mb-2">{msg}</p>}
      <button onClick={submit} className="w-full bg-green-600 text-white rounded-xl p-3 font-semibold">যাচাই করে উত্তর দিন</button>
    </div>
  );
}

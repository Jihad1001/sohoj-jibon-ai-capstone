import { useEffect, useState } from "react";
import { getDistricts, getDomains, processQuery } from "./api";
import AuthProfile from "./components/AuthProfile.jsx";
import DomainDashboard from "./components/DomainDashboard.jsx";
import QueryScreen from "./components/QueryScreen.jsx";
import ProgressModal from "./components/ProgressModal.jsx";
import ResultView from "./components/ResultView.jsx";

export default function App() {
  const [districts, setDistricts] = useState([]);
  const [domains, setDomains] = useState([]);
  const [profile, setProfile] = useState(() => JSON.parse(localStorage.getItem("sj_profile") || "null"));
  const [domain, setDomain] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getDistricts(), getDomains()])
      .then(([d, dm]) => { setDistricts(d); setDomains(dm); })
      .catch(() => setError("Backend চালু নেই। আগে backend চালু করুন (uvicorn main:app --reload)।"));
  }, []);

  const saveProfile = (p) => { localStorage.setItem("sj_profile", JSON.stringify(p)); setProfile(p); };
  const logout = () => { localStorage.removeItem("sj_profile"); setProfile(null); setDomain(null); setResult(null); };

  const submit = async (payload) => {
    setLoading(true); setError("");
    try { setResult(await processQuery(payload)); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  if (error && !districts.length) return <p className="p-6 text-red-600">{error}</p>;
  if (!districts.length) return <p className="p-6">লোড হচ্ছে...</p>;
  if (!profile) return <AuthProfile districts={districts} onDone={saveProfile} />;

  return (
    <>
      {loading && <ProgressModal />}
      {error && <p className="bg-red-100 text-red-700 p-2 text-center">{error}</p>}
      {result ? <ResultView result={result} onBack={() => setResult(null)} />
        : domain ? <QueryScreen domain={domain} districts={districts} profile={profile} onSubmit={submit} onBack={() => setDomain(null)} />
        : <DomainDashboard domains={domains} profile={profile} onPick={setDomain} onLogout={logout} />}
    </>
  );
}

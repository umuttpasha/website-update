import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import {
  LogOut, Save, Plus, Trash2, Pencil, ShieldCheck, BookText, Megaphone, X, ArrowLeft,
} from "lucide-react";
import { toast, Toaster } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const TOKEN_KEY = "tc_token";

const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ""}` });

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/auth/login`, { username, password });
      localStorage.setItem(TOKEN_KEY, data.access_token);
      onLogin(data.user);
      toast.success(`Hoş geldin, ${data.user.username}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Giriş başarısız");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tc-root min-h-screen flex items-center justify-center px-5">
      <div className="tc-grid-bg" />
      <motion.form
        onSubmit={submit}
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="tc-panel relative z-10 w-full max-w-sm p-8" data-testid="admin-login-form"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="tc-bot-avatar"><ShieldCheck className="w-5 h-5 text-black" /></div>
          <div>
            <div className="font-black tc-title text-lg">Yetkili Girişi</div>
            <div className="text-xs text-zinc-500">TrapClub Yönetim Paneli</div>
          </div>
        </div>
        <label className="tc-stat-label">Kullanıcı Adı</label>
        <input className="tc-input w-full mt-1 mb-4" value={username} onChange={(e) => setUsername(e.target.value)}
          placeholder="admin" data-testid="admin-username-input" />
        <label className="tc-stat-label">Şifre</label>
        <input type="password" className="tc-input w-full mt-1 mb-6" value={password}
          onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" data-testid="admin-password-input" />
        <button type="submit" disabled={loading} className="tc-discord w-full justify-center" data-testid="admin-login-button">
          {loading ? "Giriş yapılıyor..." : "Giriş Yap"}
        </button>
        <a href="/" className="mt-4 flex items-center justify-center gap-1 text-xs text-zinc-500 hover:text-lime-400">
          <ArrowLeft className="w-3 h-3" /> Siteye dön
        </a>
      </motion.form>
      <Toaster theme="dark" position="top-center" />
    </div>
  );
};

const KnowledgeEditor = () => {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    axios.get(`${API}/admin/knowledge`, { headers: authHeader() })
      .then((r) => setContent(r.data.content))
      .catch(() => toast.error("Bilgi bankası yüklenemedi"))
      .finally(() => setLoading(false));
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/knowledge`, { content }, { headers: authHeader() });
      toast.success("Bilgi bankası yayınlandı ✅ AI artık yeni bilgiyle cevap verir");
    } catch {
      toast.error("Kaydedilemedi");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="tc-panel p-6" data-testid="knowledge-editor">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <BookText className="w-5 h-5 text-lime-400" />
          <h2 className="text-lg font-bold tracking-wide uppercase">Bilgi Bankası</h2>
        </div>
        <button onClick={save} disabled={saving || loading} className="tc-discord" data-testid="knowledge-save-button">
          <Save className="w-4 h-4" /> {saving ? "Kaydediliyor..." : "Kaydet & Yayınla"}
        </button>
      </div>
      <p className="text-xs text-zinc-500 mb-3">
        Bu metni AI asistan cevap üretirken kullanır. Değiştirip kaydedince anında yayına girer.
      </p>
      {loading ? (
        <div className="text-sm text-zinc-500">Yükleniyor...</div>
      ) : (
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="tc-textarea"
          data-testid="knowledge-textarea"
          spellCheck={false}
        />
      )}
    </div>
  );
};

const emptyForm = { id: null, title: "", tag: "", body: "", image: "" };

const AnnouncementsManager = () => {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [busy, setBusy] = useState(false);

  const load = () => axios.get(`${API}/announcements`).then((r) => setItems(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    const payload = { title: form.title, tag: form.tag, body: form.body, image: form.image || null };
    try {
      if (form.id) {
        await axios.put(`${API}/admin/announcements/${form.id}`, payload, { headers: authHeader() });
        toast.success("Duyuru güncellendi");
      } else {
        await axios.post(`${API}/admin/announcements`, payload, { headers: authHeader() });
        toast.success("Duyuru eklendi ve yayınlandı");
      }
      setForm(emptyForm);
      load();
    } catch {
      toast.error("İşlem başarısız");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Bu duyuru silinsin mi?")) return;
    try {
      await axios.delete(`${API}/admin/announcements/${id}`, { headers: authHeader() });
      toast.success("Duyuru silindi");
      load();
    } catch {
      toast.error("Silinemedi");
    }
  };

  return (
    <div className="grid md:grid-cols-2 gap-6" data-testid="announcements-manager">
      <div className="tc-panel p-6">
        <div className="flex items-center gap-3 mb-4">
          <Megaphone className="w-5 h-5 text-lime-400" />
          <h2 className="text-lg font-bold tracking-wide uppercase">Duyurular</h2>
        </div>
        <div className="space-y-3">
          {items.length === 0 && <div className="text-sm text-zinc-500">Duyuru yok.</div>}
          {items.map((a) => (
            <div key={a.id} className="tc-ann" data-testid={`admin-ann-${a.id}`}>
              <div className="flex items-center justify-between">
                <span className="tc-tag">{a.tag}</span>
                <div className="flex gap-1">
                  <button onClick={() => setForm({ id: a.id, title: a.title, tag: a.tag, body: a.body, image: a.image || "" })}
                    className="tc-icon-btn" data-testid={`edit-ann-${a.id}`}><Pencil className="w-3.5 h-3.5" /></button>
                  <button onClick={() => remove(a.id)} className="tc-icon-btn tc-icon-danger" data-testid={`delete-ann-${a.id}`}>
                    <Trash2 className="w-3.5 h-3.5" /></button>
                </div>
              </div>
              <div className="font-semibold text-sm mt-1">{a.title}</div>
              <div className="text-xs text-zinc-400 mt-1 line-clamp-2">{a.body}</div>
            </div>
          ))}
        </div>
      </div>

      <form onSubmit={submit} className="tc-panel p-6 h-fit" data-testid="announcement-form">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold uppercase tracking-wide">{form.id ? "Duyuruyu Düzenle" : "Yeni Duyuru"}</h3>
          {form.id && (
            <button type="button" onClick={() => setForm(emptyForm)} className="tc-icon-btn"><X className="w-3.5 h-3.5" /></button>
          )}
        </div>
        <label className="tc-stat-label">Başlık</label>
        <input className="tc-input w-full mt-1 mb-3" value={form.title} required
          onChange={(e) => setForm({ ...form, title: e.target.value })} data-testid="ann-title-input" />
        <label className="tc-stat-label">Etiket (örn: Turnuva, Güncelleme)</label>
        <input className="tc-input w-full mt-1 mb-3" value={form.tag} required
          onChange={(e) => setForm({ ...form, tag: e.target.value })} data-testid="ann-tag-input" />
        <label className="tc-stat-label">İçerik</label>
        <textarea className="tc-textarea h-32 mt-1 mb-3" value={form.body} required
          onChange={(e) => setForm({ ...form, body: e.target.value })} data-testid="ann-body-input" />
        <label className="tc-stat-label">Görsel URL (opsiyonel)</label>
        <input className="tc-input w-full mt-1 mb-5" value={form.image}
          onChange={(e) => setForm({ ...form, image: e.target.value })} data-testid="ann-image-input" />
        <button type="submit" disabled={busy} className="tc-discord w-full justify-center" data-testid="ann-submit-button">
          {form.id ? <><Save className="w-4 h-4" /> Güncelle</> : <><Plus className="w-4 h-4" /> Ekle & Yayınla</>}
        </button>
      </form>
    </div>
  );
};

export default function Yonetim() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [tab, setTab] = useState("knowledge");

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) { setChecking(false); return; }
    axios.get(`${API}/auth/me`, { headers: authHeader() })
      .then((r) => setUser(r.data))
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setChecking(false));
  }, []);

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  };

  if (checking) return <div className="tc-root min-h-screen flex items-center justify-center text-zinc-500">Yükleniyor...</div>;
  if (!user) return <Login onLogin={setUser} />;

  return (
    <div className="tc-root min-h-screen text-zinc-100">
      <div className="tc-grid-bg" />
      <header className="relative z-10 max-w-6xl mx-auto px-5 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="tc-bot-avatar"><ShieldCheck className="w-5 h-5 text-black" /></div>
          <div>
            <div className="text-lg font-black tc-title">TRAP<span className="text-lime-400">CLUB</span> Yönetim</div>
            <div className="text-[10px] uppercase tracking-[0.3em] text-zinc-500">{user.username} · {user.role}</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <a href="/" className="tc-ip" data-testid="back-to-site">Siteye Dön</a>
          <button onClick={logout} className="tc-discord" data-testid="admin-logout-button">
            <LogOut className="w-4 h-4" /> Çıkış
          </button>
        </div>
      </header>

      <main className="relative z-10 max-w-6xl mx-auto px-5 pb-20">
        <div className="flex gap-2 mb-6">
          <button onClick={() => setTab("knowledge")} className={`tc-tabbtn ${tab === "knowledge" ? "tc-tabbtn-on" : ""}`}
            data-testid="tab-knowledge"><BookText className="w-4 h-4" /> Bilgi Bankası</button>
          <button onClick={() => setTab("announcements")} className={`tc-tabbtn ${tab === "announcements" ? "tc-tabbtn-on" : ""}`}
            data-testid="tab-announcements"><Megaphone className="w-4 h-4" /> Duyurular</button>
        </div>
        {tab === "knowledge" ? <KnowledgeEditor /> : <AnnouncementsManager />}
      </main>
      <Toaster theme="dark" position="top-center" />
    </div>
  );
}

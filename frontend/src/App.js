import { useEffect, useRef, useState } from "react";
import "@/App.css";
import axios from "axios";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Yonetim from "@/Yonetim";
import { motion } from "framer-motion";
import {
  Server, Users, Gauge, Copy, Check, Send, MessageSquare,
  Circle, Bot, ExternalLink, ShieldAlert, Sparkles, Megaphone,
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const SERVER_IP = "play.trapclub.net";
const DISCORD_URL = "https://discord.gg/trapclub";

const QUICK_QUESTIONS = [
  "Server IP nedir?",
  "Sunucuya giriş nasıl yaparım?",
  "VIP fiyatları ne?",
  "Kurallar neler?",
  "Turnuva ne zaman?",
  "Ban yedim ne yapmalıyım?",
];

const StatusCard = ({ status, loading }) => {
  const online = status?.online;
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
      className="tc-panel p-6 sm:p-8" data-testid="server-status-card"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Server className="w-5 h-5 text-lime-400" />
          <h2 className="text-lg font-bold tracking-wide uppercase">Sunucu Durumu</h2>
        </div>
        <span className={`tc-badge ${online ? "tc-badge-on" : "tc-badge-off"}`} data-testid="server-status-indicator">
          <Circle className={`w-2.5 h-2.5 ${online ? "fill-lime-400 text-lime-400" : "fill-red-500 text-red-500"}`} />
          {loading ? "Sorgulanıyor..." : online ? "ÇEVRİMİÇİ" : "ÇEVRİMDIŞI"}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="tc-stat" data-testid="stat-players">
          <Users className="w-4 h-4 text-zinc-500" />
          <div>
            <div className="tc-stat-value">{status ? `${status.players}/${status.max_players}` : "—"}</div>
            <div className="tc-stat-label">Oyuncu</div>
          </div>
        </div>
        <div className="tc-stat" data-testid="stat-version">
          <Gauge className="w-4 h-4 text-zinc-500" />
          <div>
            <div className="tc-stat-value text-base">{status?.version || "—"}</div>
            <div className="tc-stat-label">Sürüm</div>
          </div>
        </div>
      </div>
      <div className="mt-6">
        <div className="tc-stat-label mb-1">Sunucu IP</div>
        <div className="text-sm font-mono text-lime-400">{status?.ip || SERVER_IP}</div>
      </div>
    </motion.div>
  );
};

const IpBar = () => {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(SERVER_IP);
    setCopied(true); setTimeout(() => setCopied(false), 1600);
  };
  return (
    <button className="tc-ip" onClick={copy} data-testid="copy-ip-button">
      <span className="text-zinc-500 text-xs uppercase tracking-widest mr-2">IP</span>
      <span className="font-mono text-lime-400">{SERVER_IP}</span>
      {copied ? <Check className="w-4 h-4 text-lime-400" /> : <Copy className="w-4 h-4 text-zinc-400" />}
    </button>
  );
};

const Announcements = ({ items }) => (
  <motion.div
    initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
    className="tc-panel p-6" data-testid="announcements-panel"
  >
    <div className="flex items-center gap-3 mb-4">
      <Megaphone className="w-5 h-5 text-lime-400" />
      <h2 className="text-lg font-bold tracking-wide uppercase">Duyurular</h2>
    </div>
    <div className="space-y-3">
      {items.length === 0 && <div className="text-sm text-zinc-500">Duyuru yok.</div>}
      {items.map((a) => (
        <div key={a.id} className="tc-ann" data-testid={`announcement-${a.id}`}>
          <div className="flex items-center gap-2 mb-1">
            <span className="tc-tag">{a.tag}</span>
            <span className="text-xs text-zinc-500">{a.author}</span>
          </div>
          <div className="font-semibold text-sm">{a.title}</div>
          <div className="text-xs text-zinc-400 mt-1 line-clamp-2">{a.body}</div>
        </div>
      ))}
    </div>
  </motion.div>
);

const ChatPanel = () => {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Selam, arenaya hoş geldin! Ben TrapClub AI asistanıyım. Sunucuya giriş, VIP paketler, kurallar, turnuvalar... ne merak ediyorsan sor." },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const sessionId = useRef(`web-${Math.random().toString(36).slice(2)}`);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, sending]);

  const send = async (text) => {
    const msg = (text ?? input).trim();
    if (!msg || sending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: msg }, { role: "assistant", text: "" }]);
    setSending(true);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, session_id: sessionId.current }),
      });
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "", acc = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop();
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data:")) continue;
          const data = line.slice(5).trim();
          if (data === "[DONE]") continue;
          try {
            const obj = JSON.parse(data);
            if (obj.token) {
              acc += obj.token;
              setMessages((m) => {
                const copy = [...m];
                copy[copy.length - 1] = { role: "assistant", text: acc };
                return copy;
              });
            }
          } catch (e) { /* ignore */ }
        }
      }
    } catch (e) {
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = { role: "assistant", text: "Bağlantı hatası. Discord: " + DISCORD_URL };
        return copy;
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
      className="tc-panel flex flex-col h-[560px]" data-testid="ai-chat-panel"
    >
      <div className="flex items-center gap-3 px-6 py-4 border-b border-zinc-800">
        <div className="tc-bot-avatar"><Bot className="w-5 h-5 text-black" /></div>
        <div>
          <div className="font-bold tracking-wide">TrapClub Asistan</div>
          <div className="text-xs text-lime-400 flex items-center gap-1">
            <Circle className="w-2 h-2 fill-lime-400 text-lime-400" /> çevrimiçi
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 tc-scroll" data-testid="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`tc-bubble ${m.role === "user" ? "tc-bubble-user" : "tc-bubble-bot"}`}>
              {m.text || (sending && i === messages.length - 1 ? <span className="tc-typing"><span className="tc-dot" /><span className="tc-dot" /><span className="tc-dot" /></span> : "")}
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div className="px-4 pb-2 flex flex-wrap gap-2">
        {QUICK_QUESTIONS.map((q) => (
          <button key={q} onClick={() => send(q)} disabled={sending} className="tc-chip"
            data-testid={`quick-question-${q.slice(0, 6)}`}>
            {q}
          </button>
        ))}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); send(); }}
        className="flex items-center gap-2 p-4 border-t border-zinc-800">
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Sorunu yaz..."
          className="tc-input" data-testid="chat-input" />
        <button type="submit" disabled={sending} className="tc-send" data-testid="chat-send-button">
          <Send className="w-4 h-4" />
        </button>
      </form>
    </motion.div>
  );
};

function HomePage() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [announcements, setAnnouncements] = useState([]);

  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API}/server/status`);
      setStatus(res.data);
    } catch (e) { setStatus(null); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchStatus();
    axios.get(`${API}/announcements`).then((r) => setAnnouncements(r.data)).catch(() => {});
    const t = setInterval(fetchStatus, 30000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="tc-root min-h-screen text-zinc-100">
      <div className="tc-grid-bg" />
      <header className="relative z-10 max-w-6xl mx-auto px-5 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src="https://minotar.net/helm/TrapMaster_TR/40.png" alt="TrapClub" className="tc-logo-skin" />
          <div>
            <div className="text-xl font-black tracking-tight tc-title">TRAP<span className="text-lime-400">CLUB</span></div>
            <div className="text-[10px] uppercase tracking-[0.3em] text-zinc-500">Trap PvP Network</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <IpBar />
          <a href={DISCORD_URL} target="_blank" rel="noreferrer" className="tc-discord" data-testid="discord-button">
            <MessageSquare className="w-4 h-4" /> Discord
          </a>
        </div>
      </header>

      <main className="relative z-10 max-w-6xl mx-auto px-5 pb-20">
        <section className="pt-10 pb-12 text-center">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <span className="tc-eyebrow"><Sparkles className="w-3 h-3" /> Canlı Sunucu & AI Destek</span>
            <h1 className="mt-5 text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight tc-title">
              TrapClub'a <span className="text-lime-400">Hoş Geldin</span>
            </h1>
            <p className="mt-4 text-zinc-400 max-w-xl mx-auto text-sm sm:text-base">
              Sunucu durumunu anlık takip et, aklına takılan her şeyi asistana sor.
              IP, VIP, kurallar, turnuvalar ve daha fazlası tek yerde.
            </p>
          </motion.div>
        </section>

        <div className="grid lg:grid-cols-2 gap-6 items-start">
          <div className="space-y-6">
            <StatusCard status={status} loading={loading} />
            <Announcements items={announcements} />
            <motion.a href={DISCORD_URL} target="_blank" rel="noreferrer"
              initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.15 }}
              className="tc-panel p-6 flex items-center justify-between group" data-testid="support-card">
              <div className="flex items-center gap-3">
                <ShieldAlert className="w-5 h-5 text-lime-400" />
                <div>
                  <div className="font-bold">Ceza itirazı & destek</div>
                  <div className="text-xs text-zinc-500">Ban/mute itirazlarını Discord'dan yap</div>
                </div>
              </div>
              <ExternalLink className="w-4 h-4 text-zinc-500 group-hover:text-lime-400 transition-colors" />
            </motion.a>
          </div>
          <ChatPanel />
        </div>
      </main>

      <footer className="relative z-10 border-t border-zinc-900 py-6 text-center text-xs text-zinc-600">
        TrapClub © {new Date().getFullYear()} · {SERVER_IP}
      </footer>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/yonetim" element={<Yonetim />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

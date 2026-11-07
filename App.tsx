import React, { useCallback, useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { CareerExplorer } from './components/CareerExplorer';
import { RoadmapView } from './components/RoadmapView';
import { ChatDrawer } from './components/ChatDrawer';
import { Icon } from './components/Icons';
import { getCareers, getHealth, getRoadmap, sendChat } from './services/api';
import type { CareerCard, CourseStatus, Health, Message, Profile, Roadmap } from './types';

const GREETING: Message = {
  id: 'greet', sender: 'bot',
  text: "Hi! I'm NextStop. Tell me what you like doing, in or out of school, and I'll suggest careers and the MDC path to get there.",
};

function useLocal<T>(key: string, initial: T) {
  const [v, setV] = useState<T>(() => {
    try { const s = localStorage.getItem(key); return s ? (JSON.parse(s) as T) : initial; } catch { return initial; }
  });
  useEffect(() => { try { localStorage.setItem(key, JSON.stringify(v)); } catch { /* storage full or blocked */ } }, [key, v]);
  return [v, setV] as const;
}

const providerLabel = (h: Health | null) => {
  if (!h) return { text: 'Connecting...', tone: 'bg-slate-100 text-slate-600' };
  const parts = [];
  if (h.llmProviders.includes('prune')) parts.push('Gemini via Prune');
  else if (h.llmProviders.includes('gemini')) parts.push('Gemini');
  else if (h.llmProviders.length) parts.push(h.llmProviders[0]);
  if (h.swarms) parts.push('Swarms agents');
  return parts.length ? { text: parts.join(' + '), tone: 'bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200' }
                      : { text: 'Offline mode', tone: 'bg-amber-50 text-amber-800 ring-1 ring-amber-200' };
};

const App: React.FC = () => {
  const [health, setHealth] = useState<Health | null>(null);
  const [careers, setCareers] = useState<CareerCard[]>([]);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loadingRoadmap, setLoadingRoadmap] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useLocal<Profile>('nextstop.profile', { grade: '', interests: '' });
  const [progress, setProgress] = useLocal<Record<string, Record<string, CourseStatus>>>('nextstop.progress', {});
  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth({ status: 'down', llmProviders: [], swarms: false, pdfContext: false, careers: 0 }));
    getCareers().then(r => setCareers(r.careers)).catch(() => setError('Cannot reach the NextStop API. Start the backend with "python app.py" in /backend.'));
  }, []);

  const open = useCallback(async (opts: { careerId?: string; query?: string }) => {
    setLoadingRoadmap(true);
    setError(null);
    try {
      // show the curated roadmap instantly, then swap in the AI-personalized one
      if (opts.careerId) {
        setRoadmap(await getRoadmap({ ...opts, profile, personalize: false }));
      }
      setRoadmap(await getRoadmap({ ...opts, profile }));
    } catch (e: any) {
      setError(e?.status === 404
        ? `No roadmap for "${opts.query}" yet. Try a card, or ask the advisor.`
        : 'Could not build that roadmap. Is the backend running?');
    } finally {
      setLoadingRoadmap(false);
    }
  }, [profile]);

  const send = async (text: string) => {
    const user: Message = { id: crypto.randomUUID(), sender: 'user', text };
    const next = [...messages, user];
    setMessages(next);
    setChatLoading(true);
    try {
      const r = await sendChat(next.filter(m => m.id !== 'greet'));
      setMessages(m => [...m, { id: crypto.randomUUID(), sender: 'bot', text: r.chatResponse, careerId: r.careerId, engine: r.engine }]);
      if (r.careerId && r.careerId !== roadmap?.careerId) open({ careerId: r.careerId });
    } catch {
      setMessages(m => [...m, { id: crypto.randomUUID(), sender: 'bot', text: "I couldn't reach the server. Please try again in a moment." }]);
    } finally {
      setChatLoading(false);
    }
  };

  const status = providerLabel(health);
  const statuses = roadmap ? progress[roadmap.careerId] ?? {} : {};

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:px-6">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-navy-900">
            <svg viewBox="0 0 32 32" className="h-5 w-5" aria-hidden><path d="M8 23l8-14 8 14" stroke="#f59e0b" strokeWidth="3.2" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </span>
          <div className="mr-auto leading-tight">
            <h1 className="font-bold text-navy-900">NextStop</h1>
            <p className="text-xs text-slate-500">Miami Dade College career pathway navigator</p>
          </div>
          <span className={`hidden rounded-full px-2.5 py-1 text-xs font-medium sm:inline-flex ${status.tone}`} title="AI engine status">{status.text}</span>
          <button onClick={() => setChatOpen(true)} className="flex items-center gap-2 rounded-xl bg-amber-500 px-3.5 py-2 text-sm font-semibold text-navy-950 hover:bg-amber-400">
            <Icon name="chat" className="h-4 w-4" /> Ask the advisor
          </button>
        </div>
      </header>

      <main className="mx-auto grid min-h-0 w-full max-w-7xl flex-1 grid-cols-1 gap-5 px-4 py-5 sm:px-6 lg:grid-cols-[minmax(320px,5fr)_7fr]">
        <div className="min-h-0 lg:h-full">
          <CareerExplorer
            careers={careers}
            selectedId={roadmap?.careerId ?? null}
            profile={profile}
            onProfile={setProfile}
            onSelect={id => open({ careerId: id })}
            onCustom={q => open({ query: q })}
            busy={loadingRoadmap}
          />
        </div>

        <div className="relative min-h-[60vh] lg:h-full lg:min-h-0">
          {error && <p role="alert" className="mb-3 rounded-xl bg-rose-50 p-3 text-sm text-rose-800 ring-1 ring-rose-200">{error}</p>}
          <AnimatePresence mode="wait">
            {roadmap ? (
              <motion.div key={roadmap.careerId} className="h-full" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <RoadmapView
                  roadmap={roadmap}
                  statuses={statuses}
                  onCourse={(name, s) => setProgress(p => ({ ...p, [roadmap.careerId]: { ...(p[roadmap.careerId] ?? {}), [name]: s } }))}
                  onReset={() => setProgress(p => ({ ...p, [roadmap.careerId]: {} }))}
                />
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                          className="grid h-full place-items-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-8 text-center">
                <div className="max-w-sm">
                  <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-navy-900 text-amber-400"><Icon name="compass" className="h-7 w-7" /></span>
                  <h2 className="mt-4 text-xl font-semibold text-slate-900">Your roadmap starts here</h2>
                  <p className="mt-2 text-sm text-slate-600">Choose a career to see every step: high school prep, MDC classes, certifications, transfer to FIU or UM, and your first job.</p>
                  <button onClick={() => setChatOpen(true)} className="mt-4 text-sm font-medium text-navy-800 underline decoration-amber-500 underline-offset-4">
                    Not sure? Chat with the advisor
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          {loadingRoadmap && (
            <div className="pointer-events-none absolute right-4 top-4 flex items-center gap-2 rounded-full bg-navy-900/90 px-3 py-1.5 text-xs text-white">
              <motion.span className="h-2 w-2 rounded-full bg-amber-400" animate={{ scale: [1, 1.6, 1] }} transition={{ repeat: Infinity, duration: 0.9 }} />
              {health?.swarms ? 'Swarm agents personalizing...' : 'Building roadmap...'}
            </div>
          )}
        </div>
      </main>

      <ChatDrawer
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        messages={messages}
        loading={chatLoading}
        onSend={send}
        onOpenCareer={id => open({ careerId: id })}
        careerTitle={id => careers.find(c => c.id === id)?.title ?? 'this'}
      />
    </div>
  );
};

export default App;

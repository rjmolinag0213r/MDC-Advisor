import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import type { Message } from '../types';
import { Icon } from './Icons';

interface Props {
  open: boolean;
  onClose: () => void;
  messages: Message[];
  loading: boolean;
  onSend: (text: string) => void;
  onOpenCareer: (careerId: string) => void;
  careerTitle: (id: string) => string;
}

const STARTERS = ['I like video games and math', 'I want to help people but I like tech', '¿Qué programas tienen?', "I'm not sure what I want yet"];

export const ChatDrawer: React.FC<Props> = ({ open, onClose, messages, loading, onSend, onOpenCareer, careerTitle }) => {
  const [text, setText] = useState('');
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }), [messages, loading]);

  const submit = (t: string) => {
    if (!t.trim() || loading) return;
    onSend(t.trim());
    setText('');
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          aria-label="Chat with NextStop"
          initial={{ x: '100%', opacity: 0.5 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: '100%', opacity: 0.5 }}
          transition={{ type: 'spring', damping: 28, stiffness: 260 }}
          className="fixed inset-y-0 right-0 z-30 flex w-full max-w-md flex-col bg-white shadow-2xl ring-1 ring-slate-200"
        >
          <header className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-navy-900 text-amber-400"><Icon name="chat" className="h-4 w-4" /></span>
            <div className="flex-1">
              <p className="font-semibold text-slate-900">NextStop advisor</p>
              <p className="text-xs text-slate-500">Not sure yet? Tell me what you enjoy. English o español.</p>
            </div>
            <button onClick={onClose} aria-label="Close chat" className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100"><Icon name="close" /></button>
          </header>

          <div className="scroll-thin flex-1 space-y-3 overflow-y-auto px-5 py-4" aria-live="polite">
            {messages.map(m => (
              <motion.div key={m.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                          className={`flex ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm ${
                  m.sender === 'user' ? 'rounded-br-md bg-navy-900 text-white' : 'rounded-bl-md bg-slate-100 text-slate-800'}`}>
                  {m.text}
                  {m.careerId && (
                    <button onClick={() => onOpenCareer(m.careerId!)}
                            className="mt-2 flex items-center gap-1.5 rounded-lg bg-amber-500 px-2.5 py-1.5 text-xs font-semibold text-navy-950 hover:bg-amber-400">
                      <Icon name="rocket" className="h-3.5 w-3.5" /> Open {careerTitle(m.careerId)} roadmap
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
            {loading && (
              <div className="flex gap-1 px-2" aria-label="NextStop is typing">
                {[0, 1, 2].map(i => (
                  <motion.span key={i} className="h-2 w-2 rounded-full bg-slate-400"
                               animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1, delay: i * 0.15 }} />
                ))}
              </div>
            )}
            {messages.length <= 1 && !loading && (
              <div className="flex flex-wrap gap-1.5 pt-2">
                {STARTERS.map(s => (
                  <button key={s} onClick={() => submit(s)} className="rounded-full bg-white px-3 py-1 text-xs text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50">{s}</button>
                ))}
              </div>
            )}
            <div ref={end} />
          </div>

          <form onSubmit={e => { e.preventDefault(); submit(text); }} className="flex gap-2 border-t border-slate-200 p-3">
            <label className="flex-1">
              <span className="sr-only">Message</span>
              <input value={text} onChange={e => setText(e.target.value)} maxLength={1000}
                     placeholder="Ask about careers, classes, transfer..."
                     className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-amber-500 focus:outline-none" />
            </label>
            <button type="submit" disabled={!text.trim() || loading} aria-label="Send"
                    className="grid w-11 place-items-center rounded-xl bg-navy-900 text-amber-400 hover:bg-navy-800 disabled:opacity-40">
              <Icon name="send" className="h-4 w-4" />
            </button>
          </form>
          <p className="px-4 pb-3 text-[11px] text-slate-500">Don't share phone numbers, addresses or IDs. Official answers: MDC advisement (305) 237-8888.</p>
        </motion.aside>
      )}
    </AnimatePresence>
  );
};

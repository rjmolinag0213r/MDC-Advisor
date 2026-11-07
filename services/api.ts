import type { CareerCard, ChatReply, Health, Message, Profile, Roadmap } from '../types';

// Empty base = same origin (Vite dev proxy). Set VITE_BACKEND_URL when the API is hosted elsewhere.
const BASE = (import.meta as any).env?.VITE_BACKEND_URL ?? '';

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(body.message || body.error || `HTTP ${res.status}`), { status: res.status, body });
  return body as T;
}

export const getHealth = () => req<Health>('/health');
export const getCareers = () => req<{ careers: CareerCard[]; disclaimer: string }>('/api/careers');

export const getRoadmap = (opts: { careerId?: string; query?: string; profile: Profile; personalize?: boolean }) =>
  req<Roadmap>('/api/roadmap', {
    method: 'POST',
    body: JSON.stringify({
      careerId: opts.careerId,
      query: opts.query,
      personalize: opts.personalize ?? true,
      profile: {
        grade: opts.profile.grade || undefined,
        interests: opts.profile.interests ? opts.profile.interests.split(',').map(s => s.trim()).filter(Boolean) : [],
      },
    }),
  });

export const sendChat = (history: Message[]) =>
  req<ChatReply>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ chatHistory: history.map(m => ({ sender: m.sender, text: m.text })) }),
  });

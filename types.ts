export type CourseStatus = 'pending' | 'planned' | 'in-progress' | 'completed';
export type ProgramCode = 'AI' | 'DATA' | 'CYBER' | 'SWE' | 'NET' | 'ECE' | 'OTHER';

export interface Salary { median: number | null; occupation: string }

export interface CareerCard {
  id: string;
  title: string;
  icon: string;
  cluster: string;
  tagline: string;
  program: ProgramCode | null;
  salary: Salary;
}

export interface Course { name: string; status: CourseStatus }
export interface TransferOption { name: string; program: string; note: string }

export type Stage =
  | { id: 'hs' | 'certs'; title: string; items: string[] }
  | { id: 'mdc'; title: string; credential: string; notes: string; courses: Course[] }
  | { id: 'transfer'; title: string; options: TransferOption[] }
  | { id: 'career'; title: string; items: string[]; license: string | null };

export interface Engine { name: 'swarms' | 'llm' | 'catalog' | 'offline' | 'guard'; detail: string; seconds?: number }

export interface Roadmap {
  careerId: string;
  title: string;
  tagline: string;
  cluster: string;
  program: { key: ProgramCode; name: string; code: string } | null;
  salary: Salary;
  salarySource: { label: string; url: string };
  stages: Stage[];
  personalTips: string[];
  summary?: string;
  reviewed: boolean;
  disclaimer: string;
  engine: Engine;
}

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  careerId?: string | null;
  engine?: Engine;
}

export interface ChatReply {
  chatResponse: string;
  recommendedProgram: ProgramCode | null;
  careerId: string | null;
  language: 'en' | 'es';
  engine: Engine;
}

export interface Health { status: string; llmProviders: string[]; swarms: boolean; pdfContext: boolean; careers: number }

export interface Profile { grade: string; interests: string }

export type CourseStatus = 'pending' | 'planned' | 'in-progress' | 'completed';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
}

export interface RequiredClass {
  name: string;
  status: CourseStatus;
}

export interface TransferUniversity {
  name:string;
  gpa: string;
  prereqs: string;
  notes: string;
}

export interface CareerData {
  programName: string | null;
  progress: number;
  requiredClasses: RequiredClass[];
  transferUniversities: TransferUniversity[];
}

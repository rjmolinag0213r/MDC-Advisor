import { Type } from '@google/genai';

export const GEMINI_RESPONSE_SCHEMA = {
  type: Type.OBJECT,
  properties: {
    chatResponse: {
      type: Type.STRING,
      description: "A friendly, conversational response to the user's message."
    },
    careerPlan: {
      type: Type.OBJECT,
      description: "An object containing the student's updated career plan.",
      properties: {
        programName: {
          type: Type.STRING,
          description: "The name of the academic program the user is interested in. Should be null if not yet determined."
        },
        progress: {
          type: Type.NUMBER,
          description: "A percentage (0-100) representing the student's progress towards completing required courses."
        },
        requiredClasses: {
          type: Type.ARRAY,
          description: "A list of required MDC classes for the specified program.",
          items: {
            type: Type.OBJECT,
            properties: {
              name: { type: Type.STRING },
              status: { 
                type: Type.STRING,
                description: "The student's status for the course. Can be 'pending', 'planned', 'in-progress', or 'completed'."
              }
            },
            required: ['name', 'status']
          }
        },
        transferUniversities: {
          type: Type.ARRAY,
          description: "A list of top transfer universities for the program.",
          items: {
            type: Type.OBJECT,
            properties: {
              name: { type: Type.STRING },
              gpa: { type: Type.STRING },
              prereqs: { type: Type.STRING },
              notes: { type: Type.STRING }
            },
            required: ['name', 'gpa', 'prereqs', 'notes']
          }
        }
      }
    }
  }
};

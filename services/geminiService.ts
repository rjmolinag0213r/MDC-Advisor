import { Message, CareerData } from '../types';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

export const getCareerGuidance = async (chatHistory: Message[]): Promise<{ chatResponse: string; careerPlan: CareerData }> => {
  try {
    // Format chat history for the backend
    const formattedHistory = chatHistory.map(msg => ({
      sender: msg.sender,
      text: msg.text,
      role: msg.sender === 'bot' ? 'model' : 'user',
      parts: [{ text: msg.text }]
    }));

    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chatHistory: formattedHistory
      })
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Validate the structure
    if (data.chatResponse && data.careerPlan) {
      return {
        chatResponse: data.chatResponse,
        careerPlan: data.careerPlan,
      };
    } else {
      throw new Error("Invalid JSON structure from backend");
    }
  } catch (e) {
    console.error("Failed to get career guidance from backend:", e);
    return {
      chatResponse: "I'm sorry, I'm having trouble connecting to the advisor service. Please make sure the backend server is running and try again.",
      careerPlan: {
        programName: null,
        progress: 0,
        requiredClasses: [],
        transferUniversities: [],
      }
    };
  }
};

import { Message, CareerData } from '../types';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

export const getCareerGuidance = async (chatHistory: Message[]): Promise<{ chatResponse: string; careerPlan: CareerData }> => {
  try {
    console.log('[geminiService] Starting request with', chatHistory.length, 'messages');
    
    // Format chat history for the backend
    const formattedHistory = chatHistory.map(msg => ({
      sender: msg.sender,
      text: msg.text,
      role: msg.sender === 'bot' ? 'model' : 'user',
      parts: [{ text: msg.text }]
    }));

    console.log('[geminiService] Formatted history:', formattedHistory.length, 'messages');

    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chatHistory: formattedHistory
      })
    });

    console.log('[geminiService] Response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[geminiService] Backend error:', errorText);
      throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('[geminiService] Received data:', {
      hasChatResponse: !!data.chatResponse,
      hasCareerPlan: !!data.careerPlan,
      classesCount: data.careerPlan?.requiredClasses?.length || 0
    });
    
    // Validate and sanitize the structure
    if (data.chatResponse && data.careerPlan) {
      // Ensure requiredClasses is an array
      if (!Array.isArray(data.careerPlan.requiredClasses)) {
        console.warn('[geminiService] requiredClasses is not an array, fixing...');
        data.careerPlan.requiredClasses = [];
      }
      
      // Ensure transferUniversities is an array
      if (!Array.isArray(data.careerPlan.transferUniversities)) {
        console.warn('[geminiService] transferUniversities is not an array, fixing...');
        data.careerPlan.transferUniversities = [];
      }
      
      // Validate each course has required fields
      data.careerPlan.requiredClasses = data.careerPlan.requiredClasses.filter((cls: any) => {
        if (!cls.name || typeof cls.name !== 'string') {
          console.warn('[geminiService] Invalid course object, removing:', cls);
          return false;
        }
        return true;
      });
      
      console.log('[geminiService] Returning validated data');
      return {
        chatResponse: data.chatResponse,
        careerPlan: data.careerPlan,
      };
    } else {
      console.error('[geminiService] Invalid JSON structure:', data);
      throw new Error("Invalid JSON structure from backend");
    }
  } catch (e) {
    console.error("[geminiService] Error:", e);
    if (e instanceof Error) {
      console.error("[geminiService] Error message:", e.message);
      console.error("[geminiService] Error stack:", e.stack);
    }
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

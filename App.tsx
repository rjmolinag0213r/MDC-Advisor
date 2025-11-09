import React, { useState, useEffect, useCallback } from 'react';
import { CareerJourneyPanel } from './components/CareerJourneyPanel';
import { ChatPanel } from './components/ChatPanel';
import { getCareerGuidance } from './services/geminiService';
import { Message, CareerData, CourseStatus } from './types';

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [careerData, setCareerData] = useState<CareerData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedUniversities, setSelectedUniversities] = useState<string[]>([]);

  const initializeChat = useCallback(() => {
    setIsLoading(true);
    setMessages([{ 
        id: '1', 
        text: "Hi! I'm MyMDC.NextStop Chat. What program are you interested in? For example: Nursing, Computer Science, or Business.", 
        sender: 'bot' 
    }]);
    setCareerData(null);
    setSelectedUniversities([]);
    setIsLoading(false);
  }, []);
  
  useEffect(() => {
    initializeChat();
  }, [initializeChat]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = { id: Date.now().toString(), text, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const chatHistory = [...messages, userMessage];
      const { chatResponse, careerPlan } = await getCareerGuidance(chatHistory);
      
      const botMessage: Message = { id: (Date.now() + 1).toString(), text: chatResponse, sender: 'bot' };
      setMessages(prev => [...prev, botMessage]);
      setCareerData(careerPlan);
    } catch (error) {
      console.error("Error communicating with Gemini API:", error);
      const errorMessage: Message = { 
        id: (Date.now() + 1).toString(), 
        text: "Sorry, I'm having trouble connecting right now. Please try again in a moment.", 
        sender: 'bot' 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCourseStatusChange = (courseName: string, status: CourseStatus) => {
    setCareerData(prevData => {
      if (!prevData) return null;
      
      const updatedClasses = prevData.requiredClasses.map(c => 
        c.name === courseName ? { ...c, status } : c
      );
      
      const completedCount = updatedClasses.filter(c => c.status === 'completed').length;
      const totalCount = updatedClasses.length;
      const newProgress = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

      return {
        ...prevData,
        requiredClasses: updatedClasses,
        progress: newProgress,
      };
    });
  };

  const handleToggleUniversity = (universityName: string) => {
    setSelectedUniversities(prevSelected => 
      prevSelected.includes(universityName)
        ? prevSelected.filter(name => name !== universityName)
        : [...prevSelected, universityName]
    );
  };

  return (
    <div className="bg-gray-100 flex items-center justify-center min-h-screen font-sans">
      <div className="flex w-full h-screen lg:h-[90vh] lg:max-w-6xl lg:rounded-2xl shadow-2xl overflow-hidden bg-white">
        <CareerJourneyPanel 
          careerData={careerData}
          onCourseStatusChange={handleCourseStatusChange}
          selectedUniversities={selectedUniversities}
          onToggleUniversity={handleToggleUniversity}
        />
        <ChatPanel
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};

export default App;

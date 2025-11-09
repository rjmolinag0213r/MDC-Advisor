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
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      console.log('Sending chat history with', newMessages.length, 'messages');
      const { chatResponse, careerPlan } = await getCareerGuidance(newMessages);
      
      console.log('Received response:', { 
        responseLength: chatResponse.length, 
        hasPlan: !!careerPlan.programName,
        requiredClassesCount: careerPlan.requiredClasses?.length || 0
      });
      
      // Validate careerPlan structure
      if (careerPlan && careerPlan.requiredClasses) {
        console.log('First course:', careerPlan.requiredClasses[0]);
        // Check for non-ASCII in course names
        careerPlan.requiredClasses.forEach((course, idx) => {
          if (!/^[\x00-\x7F]*$/.test(course.name)) {
            console.error(`Course ${idx} has non-ASCII characters:`, course.name);
          }
        });
      }
      
      const botMessage: Message = { id: (Date.now() + 1).toString(), text: chatResponse, sender: 'bot' };
      setMessages(prev => [...prev, botMessage]);
      
      if (careerPlan) {
        console.log('Setting career data...');
        setCareerData(careerPlan);
        console.log('Career data set successfully');
      }
    } catch (error) {
      console.error("Error communicating with backend:", error);
      console.error("Error details:", error instanceof Error ? error.message : String(error));
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

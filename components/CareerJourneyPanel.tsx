import React, { useState, useMemo } from 'react';
import { CareerData, CourseStatus, TransferUniversity } from '../types';
import { ProgressCircle } from './ProgressCircle';
import { CheckIcon } from './icons/CheckIcon';
import { SortAscIcon, SortDescIcon } from './icons/SortIcons';

interface CareerJourneyPanelProps {
  careerData: CareerData | null;
  onCourseStatusChange: (courseName: string, status: CourseStatus) => void;
  selectedUniversities: string[];
  onToggleUniversity: (universityName: string) => void;
}

const statusStyles: { [key in CourseStatus]: string } = {
  pending: 'border-l-4 border-transparent',
  planned: 'bg-blue-50 border-l-4 border-blue-500',
  'in-progress': 'bg-yellow-50 border-l-4 border-yellow-500',
  completed: 'bg-green-50 border-l-4 border-green-500 text-slate-500 line-through',
};

export const CareerJourneyPanel: React.FC<CareerJourneyPanelProps> = ({
  careerData, onCourseStatusChange, selectedUniversities, onToggleUniversity
}) => {
  const [universityFilter, setUniversityFilter] = useState('');
  const [sortConfig, setSortConfig] = useState<{ key: keyof TransferUniversity, direction: 'asc' | 'desc' }>({ key: 'gpa', direction: 'desc' });

  const programName = careerData?.programName ?? '...';
  const progress = careerData?.progress ?? 0;
  const completedClasses = careerData?.requiredClasses?.filter(c => c.status === 'completed').length ?? 0;
  const totalClasses = careerData?.requiredClasses?.length ?? 0;

  const filteredUniversities = useMemo(() => {
    if (!careerData?.transferUniversities || !Array.isArray(careerData.transferUniversities)) {
      return [];
    }
    return careerData.transferUniversities.filter(uni => 
      uni && uni.name && typeof uni.name === 'string' && 
      uni.name.toLowerCase().includes(universityFilter.toLowerCase())
    );
  }, [careerData?.transferUniversities, universityFilter]);

  const sortedSelectedUniversities = useMemo(() => {
    if (selectedUniversities.length === 0 || !careerData?.transferUniversities) return [];

    const selectedData = careerData.transferUniversities.filter(uni => 
      uni && uni.name && selectedUniversities.includes(uni.name)
    );
    
    return [...selectedData].sort((a, b) => {
      const aVal = parseFloat(a[sortConfig.key] as string);
      const bVal = parseFloat(b[sortConfig.key] as string);
      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [selectedUniversities, careerData?.transferUniversities, sortConfig]);

  const handleSort = (key: keyof TransferUniversity) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  return (
    <div className="hidden lg:flex flex-col flex-1 p-6 bg-slate-50 border-r border-slate-200 overflow-y-auto">
      <h2 className="text-2xl font-bold text-slate-800 text-center mb-6">Your Career Journey</h2>
      
      <div className="flex flex-col items-center mb-8">
        <ProgressCircle progress={progress} />
        <div className="w-full mt-6 space-y-2 text-sm text-slate-600">
          <div className="flex justify-between items-center"><span className="font-semibold">1. Interest</span> <span className="text-blue-500 font-bold">{programName}</span></div>
          <div className="w-full h-px bg-slate-200 my-1"></div>
          <div className="flex justify-between items-center"><span className="font-semibold">2. Courses</span> <span>{completedClasses}/{totalClasses} reqs met</span></div>
        </div>
      </div>

      {careerData && careerData.programName ? (
        <>
          <h3 className="text-lg font-semibold text-slate-700 mt-2 mb-3">Required MDC Classes</h3>
          <ul className="bg-white border border-slate-200 rounded-lg divide-y divide-slate-200">
            {careerData.requiredClasses.length > 0 ? careerData.requiredClasses.map((cls, index) => (
              <li key={`${cls.name}-${index}`} className={`px-3 py-2 flex justify-between items-center text-slate-700 text-sm transition-colors ${statusStyles[cls.status]}`}>
                <span className="flex-1">{cls.name}</span>
                 {cls.status === 'completed' && <div className="mr-2"><CheckIcon /></div>}
                <select 
                  value={cls.status} 
                  onChange={(e) => onCourseStatusChange(cls.name, e.target.value as CourseStatus)}
                  className="text-xs rounded border-slate-300 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="pending">Pending</option>
                  <option value="planned">Planned</option>
                  <option value="in-progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
              </li>
            )) : <li className="px-4 py-3 text-slate-500 text-sm">No classes listed yet.</li>}
          </ul>

          <h3 className="text-lg font-semibold text-slate-700 mt-6 mb-3">Top Transfer Universities</h3>
          <input 
            type="text"
            placeholder="Filter universities..."
            value={universityFilter}
            onChange={(e) => setUniversityFilter(e.target.value)}
            className="w-full p-2 mb-3 border border-slate-300 rounded-md text-sm"
          />
          <div className="max-h-60 overflow-y-auto border border-slate-200 rounded-lg p-2 space-y-2 bg-white">
            {filteredUniversities.length > 0 ? filteredUniversities.map((uni, index) => (
              <label key={`${uni.name}-${index}`} className="flex items-center p-2 rounded-md hover:bg-slate-100 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={selectedUniversities.includes(uni.name)}
                  onChange={() => onToggleUniversity(uni.name)}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-3 text-sm font-medium text-slate-800">{uni.name}</span>
              </label>
            )) : <div className="text-center py-4 text-slate-500 text-sm">No universities match your filter.</div>}
          </div>

          {selectedUniversities.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-slate-700 mb-3">Comparison View</h3>
              <div className="overflow-x-auto bg-white border border-slate-200 rounded-lg">
                <table className="min-w-full text-sm divide-y divide-slate-200">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="px-4 py-2 text-left font-semibold text-slate-600">University</th>
                      <th 
                        className="px-4 py-2 text-left font-semibold text-slate-600 cursor-pointer hover:bg-slate-200"
                        onClick={() => handleSort('gpa')}
                      >
                        <div className="flex items-center">
                          GPA
                          {sortConfig.key === 'gpa' && (
                            sortConfig.direction === 'asc' ? <SortAscIcon className="ml-1" /> : <SortDescIcon className="ml-1" />
                          )}
                        </div>
                      </th>
                      <th className="px-4 py-2 text-left font-semibold text-slate-600">Prerequisites</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {sortedSelectedUniversities.map((uni, index) => (
                      <tr key={`${uni.name}-${index}`}>
                        <td className="px-4 py-3 font-medium text-blue-700">{uni.name}</td>
                        <td className="px-4 py-3 text-slate-700">{uni.gpa}</td>
                        <td className="px-4 py-3 text-slate-600">{uni.prereqs}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center text-slate-500 mt-10">
            <p>Your academic plan will appear here once you select a program in the chat.</p>
        </div>
      )}
    </div>
  );
};

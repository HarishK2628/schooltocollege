import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Input } from './ui/input';
import { Search, GraduationCap } from 'lucide-react';

const SchoolsSection = ({ schools, isSearched }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('all');

  const filteredSchools = schools.filter(school => 
    school.school_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!isSearched) {
    return (
      <div className="px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <Card className="bg-gray-50 border-gray-200">
            <CardHeader>
              <CardTitle className="text-xl font-bold text-gray-900">Schools</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <Tabs value="all" className="w-full">
                <TabsList className="grid w-full grid-cols-2 mb-6">
                  <TabsTrigger value="all" className="text-blue-600 border-b-2 border-blue-600">All Schools</TabsTrigger>
                  <TabsTrigger value="my" className="text-gray-600">My Schools</TabsTrigger>
                </TabsList>
                
                <div className="mb-6">
                  <div className="relative">
                    <Input
                      type="text"
                      placeholder="Search school by name..."
                      className="pl-10 bg-gray-100 border-gray-200"
                      disabled
                    />
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  </div>
                </div>

                <div className="text-center py-12">
                  <GraduationCap className="mx-auto w-12 h-12 text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-600 mb-2">No schools listed</h3>
                  <p className="text-gray-500">School data will appear here after you search for an address.</p>
                </div>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="px-6 py-6">
      <div className="max-w-7xl mx-auto">
        <Card className="bg-white border-gray-200">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-gray-900">Schools</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6">
                <TabsTrigger value="all" className="data-[state=active]:text-blue-600 data-[state=active]:border-b-2 data-[state=active]:border-blue-600">All Schools</TabsTrigger>
                <TabsTrigger value="my" className="text-gray-600">My Schools</TabsTrigger>
              </TabsList>
              
              <div className="mb-6">
                <div className="relative">
                  <Input
                    type="text"
                    placeholder="Search schools"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                </div>
              </div>

              <TabsContent value="all">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-medium text-gray-600">School</th>
                        <th className="text-center py-3 px-4 font-medium text-gray-600">College Readiness Score</th>
                        <th className="text-center py-3 px-4 font-medium text-gray-600">College Preparation</th>
                        <th className="text-center py-3 px-4 font-medium text-gray-600">College Enrollment</th>
                        <th className="text-center py-3 px-4 font-medium text-gray-600">College Performance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredSchools.map((school) => (
                        <tr key={school.id} className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer">
                          <td className="py-4 px-4">
                            <div className="font-medium text-gray-900">{school.school_name}</div>
                            <div className="text-sm text-gray-500">{school.address_city}, {school.address_state}</div>
                          </td>
                          <td className="text-center py-4 px-4">
                            <span className="text-blue-600 font-medium">{school.college_readiness_score}</span>
                          </td>
                          <td className="text-center py-4 px-4">
                            <span className="text-blue-600 font-medium">{school.college_preparation}</span>
                          </td>
                          <td className="text-center py-4 px-4">
                            <span className="text-blue-600 font-medium">{school.college_enrollment}</span>
                          </td>
                          <td className="text-center py-4 px-4">
                            <span className="text-blue-600 font-medium">{school.college_performance}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </TabsContent>
              
              <TabsContent value="my">
                <div className="text-center py-12">
                  <GraduationCap className="mx-auto w-12 h-12 text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-600 mb-2">No saved schools</h3>
                  <p className="text-gray-500">Schools you bookmark will appear here.</p>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SchoolsSection;
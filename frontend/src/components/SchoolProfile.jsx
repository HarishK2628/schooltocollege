import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { ScrollArea } from './ui/scroll-area';
import { 
  MapPin, 
  Phone, 
  Globe, 
  Users, 
  GraduationCap, 
  School, 
  DollarSign,
  Award,
  BookOpen,
  Target,
  TrendingUp,
  X
} from 'lucide-react';
import { schoolAPI } from '../services/api';

const SchoolProfile = ({ schoolId, isOpen, onClose }) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && schoolId) {
      fetchSchoolProfile();
    }
  }, [isOpen, schoolId]);

  const fetchSchoolProfile = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await schoolAPI.getSchoolDetails(schoolId);
      if (response.success) {
        setProfile(response.data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatPercentage = (value) => {
    if (!value) return 'N/A';
    return `${Math.round(value)}%`;
  };

  const formatNumber = (value) => {
    if (!value) return 'N/A';
    return value.toLocaleString();
  };

  const getSchoolTypes = (profile) => {
    const types = [];
    if (profile?.is_public) types.push('Public');
    if (profile?.is_charter) types.push('Charter');
    if (profile?.is_boarding) types.push('Boarding');
    if (!profile?.is_public && !profile?.is_charter) types.push('Private');
    return types;
  };

  const getGradeLevels = (profile) => {
    const levels = [];
    if (profile?.is_pk) levels.push('Pre-K');
    if (profile?.is_elementary) levels.push('Elementary');
    if (profile?.is_middle) levels.push('Middle');
    if (profile?.is_high) levels.push('High');
    return levels;
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader className="flex flex-row items-center justify-between">
          <DialogTitle className="text-2xl font-bold">
            {profile?.school_name || 'School Profile'}
          </DialogTitle>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <X className="w-4 h-4" />
          </button>
        </DialogHeader>
        
        <ScrollArea className="h-[calc(90vh-100px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3">Loading school profile...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="text-red-600 mb-2">Error loading profile</div>
              <p className="text-gray-600">{error}</p>
              <button 
                onClick={fetchSchoolProfile}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Try Again
              </button>
            </div>
          ) : profile ? (
            <div className="space-y-6">
              {/* Basic Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <School className="w-5 h-5 mr-2" />
                    Basic Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-600">School Name</label>
                      <p className="text-lg font-semibold">{profile.school_name}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">School ID</label>
                      <p className="text-sm text-gray-800">{profile.niche_school_uuid}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">NCES ID</label>
                      <p className="text-sm text-gray-800">{profile.nces_id || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">District</label>
                      <p className="text-sm text-gray-800">{profile.sd_name || 'N/A'}</p>
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-2">
                    {getSchoolTypes(profile).map(type => (
                      <Badge key={type} variant="secondary">{type}</Badge>
                    ))}
                    {getGradeLevels(profile).map(level => (
                      <Badge key={level} variant="outline">{level}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Location & Contact */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <MapPin className="w-5 h-5 mr-2" />
                    Location & Contact
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-start space-x-2">
                    <MapPin className="w-4 h-4 mt-1 text-gray-500" />
                    <div>
                      <p>{profile.address_address}</p>
                      <p>{profile.address_city}, {profile.address_state} {profile.address_zipcode}</p>
                      <p className="text-sm text-gray-600">
                        {profile.county_name} • {profile.metro_area_name}
                      </p>
                    </div>
                  </div>
                  
                  {profile.phone_number && (
                    <div className="flex items-center space-x-2">
                      <Phone className="w-4 h-4 text-gray-500" />
                      <span>{profile.phone_number}</span>
                    </div>
                  )}
                  
                  {profile.website && (
                    <div className="flex items-center space-x-2">
                      <Globe className="w-4 h-4 text-gray-500" />
                      <a 
                        href={profile.website.startsWith('http') ? profile.website : `https://${profile.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        {profile.website}
                      </a>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Tabs defaultValue="academics" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="academics">Academics</TabsTrigger>
                  <TabsTrigger value="colleges">Top Colleges</TabsTrigger>
                  <TabsTrigger value="majors">Top Majors</TabsTrigger>
                </TabsList>

                <TabsContent value="academics" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <GraduationCap className="w-5 h-5 mr-2" />
                        Academic Performance
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600">
                            {formatPercentage(profile.graduation_rate)}
                          </div>
                          <div className="text-sm text-gray-600">Graduation Rate</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">
                            {formatPercentage(profile.four_year_matriculation_rate)}
                          </div>
                          <div className="text-sm text-gray-600">College Enrollment</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-purple-600">
                            {profile.student_teacher_ratio || 'N/A'}
                          </div>
                          <div className="text-sm text-gray-600">Student:Teacher Ratio</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-orange-600">
                            {profile.grade_overall || 'N/A'}
                          </div>
                          <div className="text-sm text-gray-600">Overall Grade</div>
                        </div>
                      </div>
                      
                      {/* Student Demographics */}
                      <Separator className="my-6" />
                      <div>
                        <h4 className="text-lg font-semibold mb-4 flex items-center">
                          <Users className="w-5 h-5 mr-2" />
                          Student Body Overview
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="text-center">
                            <div className="text-2xl font-bold text-blue-600">
                              {formatNumber(profile.total_students)}
                            </div>
                            <div className="text-sm text-gray-600">Total Students</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-pink-600">
                              {formatPercentage(profile.gender_breakdown_female)}
                            </div>
                            <div className="text-sm text-gray-600">Female</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-blue-600">
                              {formatPercentage(profile.gender_breakdown_male)}
                            </div>
                            <div className="text-sm text-gray-600">Male</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-gray-600">
                              {profile.religion_general || 'Secular'}
                            </div>
                            <div className="text-sm text-gray-600">Religious Affiliation</div>
                          </div>
                        </div>
                      </div>
                      
                      {profile.grades_offered && (
                        <>
                          <Separator className="my-4" />
                          <div>
                            <label className="text-sm font-medium text-gray-600">Grades Offered</label>
                            <p className="text-gray-800">{profile.grades_offered}</p>
                          </div>
                        </>
                      )}
                      
                      {(profile.tuition || profile.pk_tuit) && (
                        <>
                          <Separator className="my-4" />
                          <div>
                            <label className="text-sm font-medium text-gray-600 flex items-center mb-2">
                              <DollarSign className="w-4 h-4 mr-1" />
                              Tuition Information
                            </label>
                            <div className="grid grid-cols-2 gap-4">
                              {profile.tuition && (
                                <div>
                                  <p className="text-lg font-semibold">${formatNumber(profile.tuition)}</p>
                                  <p className="text-sm text-gray-600">Annual Tuition</p>
                                </div>
                              )}
                              {profile.pk_tuit && (
                                <div>
                                  <p className="text-lg font-semibold">${formatNumber(profile.pk_tuit)}</p>
                                  <p className="text-sm text-gray-600">Pre-K Tuition</p>
                                </div>
                              )}
                            </div>
                          </div>
                        </>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>



                <TabsContent value="colleges" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <Award className="w-5 h-5 mr-2" />
                        Top Colleges Attended by Graduates
                      </CardTitle>
                      <p className="text-sm text-gray-600 mt-2">
                        This list shows the most popular colleges and universities where graduates from this school continue their higher education. 
                        The rankings reflect the percentage of students who enrolled at each institution based on historical data.
                      </p>
                    </CardHeader>
                    <CardContent>
                      {profile.top_colleges && profile.top_colleges.length > 0 ? (
                        <div className="grid gap-3">
                          {profile.top_colleges.slice(0, 10).map((college, index) => (
                            <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border hover:bg-gray-100 transition-colors">
                              <div className="flex-1">
                                <div className="font-semibold text-gray-900 text-lg">{college.name}</div>
                                {college.ipeds && (
                                  <div className="text-sm text-gray-500 mt-1">Institution ID: {college.ipeds}</div>
                                )}
                              </div>
                              <div className="flex items-center space-x-3">
                                <div className="text-right">
                                  <div className="text-sm text-gray-500">Rank</div>
                                  <Badge variant="secondary" className="text-lg font-bold">#{index + 1}</Badge>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-12">
                          <Award className="mx-auto w-12 h-12 text-gray-400 mb-4" />
                          <h3 className="text-lg font-medium text-gray-600 mb-2">No College Data Available</h3>
                          <p className="text-gray-500">College enrollment information for graduates is not currently available for this school.</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="majors" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <BookOpen className="w-5 h-5 mr-2" />
                        Top Majors Chosen by Graduates
                      </CardTitle>
                      <p className="text-sm text-gray-600 mt-2">
                        This section displays the most popular academic majors and fields of study selected by graduates when they enter college. 
                        The data represents career paths and academic interests of students from this school, helping you understand the school's academic strengths and student outcomes.
                      </p>
                    </CardHeader>
                    <CardContent>
                      {profile.top_majors && profile.top_majors.length > 0 ? (
                        <div className="grid gap-3">
                          {profile.top_majors.slice(0, 10).map((major, index) => (
                            <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border hover:bg-gray-100 transition-colors">
                              <div className="flex-1">
                                <div className="font-semibold text-gray-900 text-lg">{major.name}</div>
                                {major.cip_code && (
                                  <div className="text-sm text-gray-500 mt-1">CIP Code: {major.cip_code}</div>
                                )}
                              </div>
                              <div className="flex items-center space-x-3">
                                <div className="text-right">
                                  <div className="text-sm text-gray-500">Rank</div>
                                  <Badge variant="secondary" className="text-lg font-bold">#{index + 1}</Badge>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-12">
                          <BookOpen className="mx-auto w-12 h-12 text-gray-400 mb-4" />
                          <h3 className="text-lg font-medium text-gray-600 mb-2">No Major Data Available</h3>
                          <p className="text-gray-500">Academic major information for graduates is not currently available for this school.</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          ) : null}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};

export default SchoolProfile;
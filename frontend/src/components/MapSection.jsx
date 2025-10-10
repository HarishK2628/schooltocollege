import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { MapPin } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default markers in React Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const MapSection = ({ schools, searchCenter, isSearched }) => {
  const formatScore = (value) => {
    if (value === null || value === undefined) return 'N/A';
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return 'N/A';
    return Math.round(numeric);
  };

  if (!isSearched) {
    return (
      <div className="px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <Card className="bg-gray-50 border-gray-200">
            <CardHeader>
              <CardTitle className="text-xl font-bold text-gray-900">Map</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="h-80 bg-gray-100 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <MapPin className="mx-auto w-12 h-12 text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-600 mb-2">Map data not loaded</h3>
                  <p className="text-gray-500">Geographic data will be shown here after selection.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const center = searchCenter || [40.7589, -73.9851];

  return (
    <div className="px-6 py-6">
      <div className="max-w-7xl mx-auto">
        <Card className="bg-white border-gray-200">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-gray-900">Map</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="h-80 rounded-lg overflow-hidden">
              <MapContainer
                center={center}
                zoom={13}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                
                {schools.map((school) => (
                  <Marker
                    key={school.id}
                    position={[school.latitude, school.longitude]}
                  >
                    <Popup>
                      <div className="p-2">
                        <h3 className="font-semibold text-gray-900">{school.school_name}</h3>
                        <p className="text-sm text-gray-600">{school.address_address}</p>
                        <p className="text-sm text-gray-600">{school.address_city}, {school.address_state}</p>
                        <div className="mt-2 text-sm">
                          <span className="font-medium">College Readiness: </span>
                          <span className="text-blue-600">{formatScore(school.college_readiness_score)}</span>
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MapSection;

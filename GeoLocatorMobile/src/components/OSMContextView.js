import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

const OSMContextView = ({ osmContext, zoneType }) => {
  if (!osmContext) return null;

  const { buildings, amenities, building_count, amenity_count } = osmContext;

  const getZoneIcon = (type) => {
    switch (type) {
      case 'education_zone': return '🏫';
      case 'healthcare_zone': return '🏥';
      case 'commercial_zone': return '🏪';
      case 'residential_zone': return '🏠';
      default: return '📍';
    }
  };

  const getZoneName = (type) => {
    switch (type) {
      case 'education_zone': return 'Образовательная зона';
      case 'healthcare_zone': return 'Медицинская зона';
      case 'commercial_zone': return 'Торговая зона';
      case 'residential_zone': return 'Жилая зона';
      default: return 'Общая зона';
    }
  };

  const getAmenityIcon = (amenity) => {
    const amenityType = amenity.amenity || amenity.category;
    switch (amenityType) {
      case 'school': return '🏫';
      case 'kindergarten': return '🧸';
      case 'university': return '🎓';
      case 'hospital': return '🏥';
      case 'clinic': return '⚕️';
      case 'pharmacy': return '💊';
      case 'restaurant': return '🍽️';
      case 'shop': return '🛍️';
      case 'bank': return '🏦';
      case 'fuel': return '⛽';
      case 'parking': return '🅿️';
      case 'bus_station': return '🚌';
      default: return '📍';
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.zoneIcon}>{getZoneIcon(zoneType)}</Text>
        <Text style={styles.zoneTitle}>{getZoneName(zoneType)}</Text>
      </View>
      
      <View style={styles.stats}>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{building_count || 0}</Text>
          <Text style={styles.statLabel}>Зданий</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{amenity_count || 0}</Text>
          <Text style={styles.statLabel}>Объектов</Text>
        </View>
      </View>

      {amenities && amenities.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Ближайшие объекты:</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {amenities.slice(0, 5).map((amenity, index) => (
              <View key={index} style={styles.amenityCard}>
                <Text style={styles.amenityIcon}>
                  {getAmenityIcon(amenity)}
                </Text>
                <Text style={styles.amenityName} numberOfLines={2}>
                  {amenity.name || amenity.amenity || 'Без названия'}
                </Text>
                <Text style={styles.amenityType}>
                  {amenity.category || amenity.amenity}
                </Text>
              </View>
            ))}
          </ScrollView>
        </View>
      )}

      {buildings && buildings.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Ближайшие здания:</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {buildings.slice(0, 3).map((building, index) => (
              <View key={index} style={styles.buildingCard}>
                <Text style={styles.buildingIcon}>🏢</Text>
                <Text style={styles.buildingName} numberOfLines={2}>
                  {building.name || building.building_type || 'Здание'}
                </Text>
                {building.levels && (
                  <Text style={styles.buildingDetails}>
                    {building.levels} этажей
                  </Text>
                )}
                {building.address && building.address.street && (
                  <Text style={styles.buildingAddress} numberOfLines={1}>
                    {building.address.street} {building.address.housenumber || ''}
                  </Text>
                )}
              </View>
            ))}
          </ScrollView>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#f8f9fa',
    padding: 12,
    borderRadius: 8,
    marginVertical: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  zoneIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  zoneTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
    paddingVertical: 8,
    backgroundColor: 'white',
    borderRadius: 6,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
  },
  section: {
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  amenityCard: {
    backgroundColor: 'white',
    padding: 10,
    borderRadius: 8,
    marginRight: 8,
    minWidth: 100,
    maxWidth: 120,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  amenityIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  amenityName: {
    fontSize: 12,
    fontWeight: '500',
    color: '#333',
    textAlign: 'center',
    marginBottom: 2,
  },
  amenityType: {
    fontSize: 10,
    color: '#666',
    textAlign: 'center',
  },
  buildingCard: {
    backgroundColor: 'white',
    padding: 10,
    borderRadius: 8,
    marginRight: 8,
    minWidth: 110,
    maxWidth: 130,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  buildingIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  buildingName: {
    fontSize: 12,
    fontWeight: '500',
    color: '#333',
    textAlign: 'center',
    marginBottom: 2,
  },
  buildingDetails: {
    fontSize: 10,
    color: '#007AFF',
    textAlign: 'center',
    marginBottom: 2,
  },
  buildingAddress: {
    fontSize: 9,
    color: '#666',
    textAlign: 'center',
  },
});

export default OSMContextView;

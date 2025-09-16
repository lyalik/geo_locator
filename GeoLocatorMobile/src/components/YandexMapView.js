import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { WebView } from 'react-native-webview';

const { width, height } = Dimensions.get('window');

export default function YandexMapView({ 
  region, 
  violations = [], 
  onMarkerPress, 
  style 
}) {
  const [mapHtml, setMapHtml] = useState('');

  useEffect(() => {
    generateMapHtml();
  }, [region, violations]);

  const generateMapHtml = () => {
    const markers = violations.map((violation, index) => {
      if (!violation.coordinates || !violation.coordinates.latitude || !violation.coordinates.longitude) {
        return '';
      }

      const { latitude, longitude } = violation.coordinates;
      const category = violation.category || 'Неизвестно';
      const confidence = violation.confidence ? Math.round(violation.confidence * 100) : 0;
      
      return `
        var marker${index} = new ymaps.Placemark([${latitude}, ${longitude}], {
          balloonContent: '<div style="padding: 10px;"><strong>${category}</strong><br/>Точность: ${confidence}%<br/>ID: ${violation.id}</div>',
          hintContent: '${category} (${confidence}%)'
        }, {
          preset: 'islands#redDotIcon',
          iconColor: '#ff0000'
        });
        myMap.geoObjects.add(marker${index});
        
        marker${index}.events.add('click', function() {
          window.ReactNativeWebView.postMessage(JSON.stringify({
            type: 'markerPress',
            violation: ${JSON.stringify(violation)}
          }));
        });
      `;
    }).join('\n');

    const html = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Yandex Map</title>
    <script src="https://api-maps.yandex.ru/2.1/?apikey=YOUR_API_KEY&lang=ru_RU" type="text/javascript"></script>
    <style>
        html, body, #map {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <script type="text/javascript">
        ymaps.ready(init);
        
        function init() {
            var myMap = new ymaps.Map("map", {
                center: [${region.latitude}, ${region.longitude}],
                zoom: 12,
                controls: ['zoomControl', 'searchControl', 'typeSelector', 'fullscreenControl']
            });

            // Добавляем маркеры нарушений
            ${markers}

            // Обработка изменения центра карты
            myMap.events.add('boundschange', function(e) {
                var center = myMap.getCenter();
                var zoom = myMap.getZoom();
                window.ReactNativeWebView.postMessage(JSON.stringify({
                    type: 'regionChange',
                    latitude: center[0],
                    longitude: center[1],
                    zoom: zoom
                }));
            });
        }
    </script>
</body>
</html>
    `;

    setMapHtml(html);
  };

  const handleMessage = (event) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      
      if (data.type === 'markerPress' && onMarkerPress) {
        onMarkerPress(data.violation);
      }
    } catch (error) {
      console.error('Error parsing WebView message:', error);
    }
  };

  return (
    <View style={[styles.container, style]}>
      <WebView
        source={{ html: mapHtml }}
        style={styles.webview}
        onMessage={handleMessage}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        startInLoadingState={true}
        scalesPageToFit={true}
        scrollEnabled={false}
        bounces={false}
        showsHorizontalScrollIndicator={false}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  webview: {
    flex: 1,
  },
});

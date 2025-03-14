import React, { useEffect, useRef, useState } from "react";
import { Button, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { CameraView, CameraType, useCameraPermissions, Camera } from 'expo-camera';




export default function App() {
  const [facing, setFacing] = useState<CameraType>('back');
  const [permission, requestPermission] = useCameraPermissions();
  //const [uri, setUri] = useState<string | null>(null);
  const cameraRef = useRef<CameraView>(null);
  const socketRef = useRef<WebSocket | null> (null);


  useEffect(() => {
    const socket = new WebSocket('ws://10.0.0.15:8765');

    socket.onopen = () => {
      console.log('WebSocket connected');
    };

    socket.onmessage = (event) => {
      console.log('Server response:', event.data);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code);
    };

    socketRef.current = socket; 

  }, []);

  if (!permission) {
    // Camera permissions are still loading.
    return <View />;
  }

  if (!permission.granted) {
    // Camera permissions are not granted yet.
    return (
      <View style={styles.container}>
        <Text style={styles.message}>We need your permission to show the camera</Text>
        <Button onPress={requestPermission} title="grant permission" />
      </View>
    );
  }

  function toggleCameraFacing() {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  }

  const takePicture = async () => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error("WebSocket nicht verbunden");
      return;
    }
    if (!cameraRef.current) return;
    
    try {
      console.log("📸 Nehme Bild auf...");
      const photo = await cameraRef.current.takePictureAsync({ base64: true });

      if (!photo?.base64) {
        console.error("❌ Fehler: Bild konnte nicht in Base64 konvertiert werden.");
        return;
      }

      //setUri(photo?.uri);  

      // JSON-Header + End of Header divider + Base64-Encoded Image
      const base64Image = photo?.base64.replace(/^data:image\/\w+;base64,/, '');
      const frameData = `{"nightmode":false}\n--END-OF-HEADER--\n${base64Image}`;
      console.log("📤 Sende Bild an WebSocket...");

      socketRef.current?.send(frameData);  //send to server
    } catch (error) {
      console.error("could not take picture:", error);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.cameraContainer}>
        <CameraView style={styles.camera} facing={facing} ref={cameraRef}/>
      </View>

      <View style={styles.buttonContainer}>
        <TouchableOpacity style={styles.button} onPress={takePicture}>
          <Text style={styles.text}>Flip Camera</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
  },
  message: {
    textAlign: 'center',
    paddingBottom: 10,
  },
  cameraContainer: {
    flex: 1, 
    width: '100%',
    alignSelf: 'center',
  },
  camera: {
    flex: 1,  
    width: '100%',
  },
  buttonContainer: {
    flex: 0.5,
    flexDirection: 'row',
    backgroundColor: 'transparent',
    margin: 64,
  },
  button: {
    flex: 1,
    alignSelf: 'flex-end',
    alignItems: 'center',
  },
  text: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
  },
});

import React, { useEffect, useRef, useState } from "react";
import { Button, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { CameraView, CameraType, useCameraPermissions, Camera } from 'expo-camera';
import * as FileSystem from 'expo-file-system';
import SignDisplay from "@/components/SignDisplay";

export default function App() {
  const [facing, setFacing] = useState<CameraType>('back');
  const [permission, requestPermission] = useCameraPermissions();
  const [detectedClasses, setDetectedClasses] = useState<string[]>(['']);
  const cameraRef = useRef<CameraView>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const socket = new WebSocket('ws://10.0.0.15:8765');

    socket.onopen = () => {
      console.log('WebSocket connected');
    };

    socket.onmessage = (event) => {
      const responseArray: string[] = event.data.split(',').map((item: string) => 
        item.trim().replace(/\s*\([^)]*\)\s*$/, '')
      );
      
      console.log('Server response:', responseArray);
      setDetectedClasses(responseArray);
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
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>We need your permission to show the camera</Text>
        <Button onPress={requestPermission} title="Grant permission" />
      </View>
    );
  }

  function toggleCameraFacing() {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  }

  const takePicture = async () => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error("WebSocket not connected");
      return;
    }
    if (!cameraRef.current) return;

    try {
      const photo = await cameraRef.current.takePictureAsync({ base64: false, quality: 0.2, shutterSound: false });
      const imagePath = photo.uri;

      // Use expo-file-system to read the file as binary data
      const imageData = await FileSystem.readAsStringAsync(imagePath, {
        encoding: FileSystem.EncodingType.Base64, // Use Base64 encoding for simplicity
      });

      const header = JSON.stringify({ nightmode: false });
      const headerBuffer = new TextEncoder().encode(header);

      const headerLength = new Uint16Array([headerBuffer.byteLength]);
      const fullBuffer = new Uint8Array(
        headerLength.byteLength + headerBuffer.byteLength + imageData.length
      );

      fullBuffer.set(new Uint8Array(headerLength.buffer), 0);
      fullBuffer.set(headerBuffer, headerLength.byteLength);
      fullBuffer.set(new Uint8Array(atob(imageData).split('').map(c => c.charCodeAt(0))), headerLength.byteLength + headerBuffer.byteLength);

      console.log("Sending image + metadata to WebSocket...");
      socketRef.current?.send(fullBuffer.buffer);

    } catch (error) {
      console.error("Error sending image:", error);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.cameraContainer}>
        <CameraView style={styles.camera} facing={facing} ref={cameraRef}/>
      </View>

      <View style={styles.signDisplayContainer}>
        <SignDisplay inputArray={detectedClasses}></SignDisplay>
      </View>

      <View style={styles.buttonContainer}>
        <TouchableOpacity style={styles.button} onPress={takePicture}>
          <Text style={styles.text}>Take Picture</Text>
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
    flex: 0,
    flexDirection: 'row',
    backgroundColor: '#f8f9fb',
    padding: 40,
  },
  button: {
    flex: 1,
    borderColor: "black",
    borderWidth: 2,
    borderRadius: 20,
    alignSelf: 'flex-end',
    alignItems: 'center',
  },
  text: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'black',
  },
  signDisplayContainer: {
    flex: 0.5,
    width: '100%',
    height: '50%',
  }
});

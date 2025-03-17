import React, { useEffect, useRef, useState } from "react";
import { Button, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { CameraView, CameraType, useCameraPermissions, Camera } from 'expo-camera';
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
      const photo = await cameraRef.current.takePictureAsync({ base64: false });
      //@ts-ignore
      const response = await fetch(photo.uri);
      const imageBlob = await response.blob();
  
      const imageArrayBuffer = await new Promise<ArrayBuffer>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          if (reader.result instanceof ArrayBuffer) {
            resolve(reader.result);
          } else {
            reject(new Error("Failed to read image as ArrayBuffer"));
          }
        };
        reader.onerror = (error) => reject(error);
        reader.readAsArrayBuffer(imageBlob);
      });
  
      const header = JSON.stringify({ nightmode: false });
      const headerBuffer = new TextEncoder().encode(header);
  
      const headerLength = new Uint16Array([headerBuffer.byteLength]);
      const fullBuffer = new Uint8Array(
        headerLength.byteLength + headerBuffer.byteLength + imageArrayBuffer.byteLength
      );
  
      fullBuffer.set(new Uint8Array(headerLength.buffer), 0);
      fullBuffer.set(headerBuffer, headerLength.byteLength);
      fullBuffer.set(new Uint8Array(imageArrayBuffer), headerLength.byteLength + headerBuffer.byteLength);
  
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
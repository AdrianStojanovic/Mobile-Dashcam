import asyncio
import websockets
import base64
import io
import sys
import os
import torch
from ultralytics import YOLO
from PIL import Image
from torchvision import models, transforms 

sys.path.append(os.path.abspath("service"))  
from constants import class_names
from execute_object_classification import process_image 

def load_mobilenet_model(model_path, num_classes, device):
    model_mobileNet = models.mobilenet_v2(pretrained=False)
    num_ftrs = model_mobileNet.classifier[1].in_features
    model_mobileNet.classifier[1] = torch.nn.Linear(num_ftrs, num_classes)
    model_mobileNet.load_state_dict(torch.load(model_path))
    model_mobileNet = model_mobileNet.to(device)
    return model_mobileNet

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model_yolo = YOLO("models/YOLO/trained_model.pt")
model_mobileNet = load_mobilenet_model("models/mobileNetV2/mobilenetv2_trained_model.pth", len(class_names), device)

# WebSocket handler expects base64 encoded image
async def handler(websocket):  
    try:
        base64_string = await websocket.recv()

        if not base64_string:
            print("server has not received data")
            await websocket.send("No image data received")
            return
        
        try:
            image_data = base64.b64decode(base64_string)
            print(f"Decoded image data, length: {len(image_data)}")
        except Exception as e:
            print(f"Error while decoding image: {e}")
            await websocket.send("Error decoding image data")
            return

        try:
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            print(f"Error while opening image: {e}")
            await websocket.send("Error opening image")
            return

        detected_classes = process_image(image, device, model_yolo, model_mobileNet, class_names)
        print(f"Detected classes: {', '.join(detected_classes)}")
        await websocket.send(f"Image received. Detected classes: {', '.join(detected_classes)}")

    except Exception as e:
        print(f"Error while receiving image: {e}")
        await websocket.send("Server could not handle image")

# main function to start server
async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Server running on ws://localhost:8765")
        await asyncio.Future()  # Running forever

asyncio.run(main())

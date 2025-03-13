import asyncio
import websockets
import base64
import io
import sys
import os
import json
import torch
from ultralytics import YOLO
from PIL import Image
from torchvision import models, transforms 

sys.path.append(os.path.abspath("service"))  
from constants import class_names
from execute_object_classification import process_image, enhance_and_classify

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
        full_message = await websocket.recv()

        if not full_message:
            await websocket.send("no image received")
            return

        if '--END-OF-HEADER--' in full_message:
            header, base64_image = full_message.split('--END-OF-HEADER--', 1)
        else:
            await websocket.send("Error while receiving image")
            return

        header = header.strip()
        try:
            header_data = json.loads(header.strip())
            nightmode = header_data.get("nightmode", False)
            print(f"Nightmode: {nightmode}")
        except json.JSONDecodeError:
            print("Fehler beim Parsen des Headers")
            await websocket.send("Fehler beim Parsen des Headers")
            return

        try:
            image_data = base64.b64decode(base64_image.strip())
            print(f"Decoded image data, length: {len(image_data)}")
        except Exception as e:
            print(f"image could not be decoded: {e}")
            await websocket.send("image could not be decoded")
            return

        try:
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            print(f"image could not be opened: {e}")
            await websocket.send("image could not be opened")
            return

        if nightmode:
            print("Nnightmode is active use image enhancement")
            detected_classes = enhance_and_classify(image, device, model_yolo, model_mobileNet, class_names)
        else:
            print("no nightmode")
            detected_classes = process_image(image, device, model_yolo, model_mobileNet, class_names)

        print(f"Detected classes: {', '.join(detected_classes)}")
        await websocket.send(f"detected classes: {', '.join(detected_classes)}")

    except Exception as e:
        print(f"Error while handeling image: {e}")
        await websocket.send("Error while handeling image")

# main function to start server
async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Server running on ws://localhost:8765")
        await asyncio.Future() 

asyncio.run(main())

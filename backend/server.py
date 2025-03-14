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
        async for full_message in websocket: 
            if not full_message:
                await websocket.send("no message received")
                continue

            # Handle image data
            if '--END-OF-HEADER--' in full_message:
                header, base64_image = full_message.split('--END-OF-HEADER--', 1)
            else:
                await websocket.send("Error while receiving image")
                continue

            header = header.strip()
            #JSON parsing
            try:
                header_data = json.loads(header.strip())
                nightmode = header_data.get("nightmode", False)
                print(f"Nightmode: {nightmode}")
            except json.JSONDecodeError:
                print("Fehler beim Parsen des Headers")
                await websocket.send("Fehler beim Parsen des Headers")
                continue

            try:
                image_data = base64.b64decode(base64_image.strip())
                print(f"Decoded image data, length: {len(image_data)}")
            except Exception as e:
                print(f"Image could not be decoded: {e}")
                await websocket.send("Image could not be decoded")
                continue

            try:
                image = Image.open(io.BytesIO(image_data))
            except Exception as e:
                print(f"Image could not be opened: {e}")
                await websocket.send("Image could not be opened")
                continue

            if nightmode:
                print("Nightmode is active, using image enhancement")
                detected_classes = enhance_and_classify(image, device, model_yolo, model_mobileNet, class_names)
            else:
                print("No nightmode")
                detected_classes = process_image(image, device, model_yolo, model_mobileNet, class_names)

            print(f"Detected classes: {', '.join(detected_classes)}")
            await websocket.send(f"Detected classes: {', '.join(detected_classes)}")

    except Exception as e:
        print(f"Error while handling image or message: {e}")
        await websocket.send("Error while handling message")

# Main function to start the server
async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8765)  # Start the server
    print("Server running on ws://localhost:8765")
    await server.wait_closed()  # Wait until the server is closed. Otherwise the server disconnects after every message.

asyncio.run(main())

import asyncio
import websockets
import io
import sys
import os
import json
import struct 
import torch
from ultralytics import YOLO
from PIL import Image
from torchvision import models

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

async def handler(websocket):
    try:
        async for full_message in websocket:
            if not full_message:
                await websocket.send("No message received")
                continue

            if not isinstance(full_message, bytes):
                await websocket.send("Invalid message format")
                continue

            # Read header length from the first 2 bytes
            header_length = struct.unpack("H", full_message[:2])[0]
            header_json = full_message[2:2+header_length].decode("utf-8")  # Extract header
            image_data = full_message[2+header_length:]  

            print(f"Header received (Length: {header_length} bytes)")

            # Parse JSON header
            try:
                header_data = json.loads(header_json)
                nightmode = header_data.get("nightmode", False)
                print(f"Night mode: {nightmode}")
            except json.JSONDecodeError:
                print("Error parsing header")
                await websocket.send("Error parsing header")
                continue

            # Open image
            try:
                image = Image.open(io.BytesIO(image_data))
                print("Image successfully loaded")
            except Exception as e:
                print(f"Error opening image: {e}")
                await websocket.send("Error opening image")
                continue

            # Process image based on mode
            if nightmode:
                print("Night mode active ")
                detected_classes = enhance_and_classify(image, device, model_yolo, model_mobileNet, class_names)
            else:
                print("Standard classification")
                detected_classes = process_image(image, device, model_yolo, model_mobileNet, class_names)

            print(f"{', '.join(detected_classes)}")
            await websocket.send(f"{', '.join(detected_classes)}")  # Send response

    except Exception as e:
        print(f"Error processing message: {e}")
        await websocket.send("Error processing message")

# Start server
async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8765, max_size=10_000_000)
    print("Server running on ws://localhost:8765")
    await server.wait_closed()

asyncio.run(main())

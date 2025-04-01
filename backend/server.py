import asyncio
import websockets
import io
import sys
import os
import json
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

def clean_detected_classes(detected_classes):
    cleaned_classes = []
    for item in detected_classes:
        cleaned_class_name = item["class"].split(" (")[0].strip()
        bbox = item["bbox"]
        confidence = item["confidence"]
        cleaned_classes.append({"class": cleaned_class_name, "bbox": bbox, "confidence": confidence})
    return cleaned_classes

async def handler(websocket):
    try:
        async for message in websocket:
            if isinstance(message, bytes) and len(message) > 10:
                header_bytes = message[:10]
                header = header_bytes.decode("utf-8").strip() 
                
                image_data = message[10:]
                image = Image.open(io.BytesIO(image_data))

                mode = "nightmode" if header == "NIGHT_MODE" else "normal"

                if mode == "nightmode":
                    print("PROCESSING IN NIGHTMODE")
                    detected_classes = enhance_and_classify(image, device, model_yolo, model_mobileNet, class_names)
                else:
                    print("PROCESSING IN NORMAL")
                    detected_classes = process_image(image, device, model_yolo, model_mobileNet, class_names)

                cleaned_classes = clean_detected_classes(json.loads(detected_classes))
                await websocket.send(json.dumps(cleaned_classes))
            else:
                await websocket.send(json.dumps({"error": "Invalid message format"}))
    except Exception as e:
        await websocket.send(json.dumps({"error": str(e)}))

async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("WebSocket server running on ws://localhost:8765")
    await server.wait_closed()

asyncio.run(main())

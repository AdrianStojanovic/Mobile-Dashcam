import sys
import os
import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
from ultralytics import YOLO
from constants import class_names

# Funktion zum Laden des MobileNetV2 Modells
def load_mobilenet_model(model_path, num_classes, device):
    model_mobileNet = models.mobilenet_v2(pretrained=False)
    num_ftrs = model_mobileNet.classifier[1].in_features
    model_mobileNet.classifier[1] = torch.nn.Linear(num_ftrs, num_classes)
    model_mobileNet.load_state_dict(torch.load(model_path))
    model_mobileNet = model_mobileNet.to(device)
    return model_mobileNet

# Transformationen für MobileNetV2
def transform_image(image_pil):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    return transform(image_pil).unsqueeze(0)  # Batch-Dimension hinzufügen

def classify_image(image_tensor, device, class_names, model_mobileNet):
    image_tensor = image_tensor.to(device)
    model_mobileNet.eval()  # Setze das Modell in den Evaluierungsmodus
    with torch.no_grad():  # Keine Gradientenberechnung erforderlich
        outputs = model_mobileNet(image_tensor)
    
    # Berechne die Vorhersage
    _, predicted_class = torch.max(outputs, 1)

    # Klassenname zuordnen (mit eigenen Klassennamen)
    predicted_class_name = class_names[predicted_class.item()]
    
    return predicted_class_name
# Funktion, die die Bildverarbeitung und Inferenz durchführt
def process_image(image_pil, device, model_yolo, model_mobileNet, class_names):
    # Konvertiere PIL-Bild in ein NumPy-Array
    image_np = np.array(image_pil)
    
    # Konvertiere von RGB (PIL) nach BGR (OpenCV)
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    # Führe YOLO-Objekterkennung durch
    results = model_yolo(image_bgr)

    detected_classes = set()  # Set, um doppelte Klassennamen zu vermeiden

    for result in results:
        for i, box in enumerate(result.boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cropped_img = image_bgr[y1:y2, x1:x2]

            if cropped_img.shape[0] > 0 and cropped_img.shape[1] > 0:
                cropped_pil = Image.fromarray(cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB))

                # Verarbeite das Bild mit MobileNetV2
                input_tensor = transform_image(cropped_pil)
                
                predicted_class = classify_image(input_tensor, device, class_names, model_mobileNet)

                detected_classes.add(predicted_class)

    return detected_classes

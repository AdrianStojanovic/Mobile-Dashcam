import sys
import os
import cv2
import numpy as np
import torch
import json
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
from ultralytics import YOLO
from constants import class_names

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from models.zero_DCE_plus import model

def load_mobilenet_model(model_path, num_classes, device):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"model could not be found: {model_path}")

    model_mobileNet = models.mobilenet_v2(pretrained=False)
    num_ftrs = model_mobileNet.classifier[1].in_features
    model_mobileNet.classifier[1] = torch.nn.Linear(num_ftrs, num_classes)

    try:
        checkpoint = torch.load(model_path, map_location=device) 
        model_mobileNet.load_state_dict(checkpoint)
        print(" weights are loaded")
    except Exception as e:
        raise RuntimeError(f" error while loading weights {model_path}: {e}")

    model_mobileNet = model_mobileNet.to(device)
    model_mobileNet.eval()  
    return model_mobileNet



def transform_image(image_pil):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    return transform(image_pil).unsqueeze(0)  

def classify_image(image_tensor, device, class_names, model_mobileNet):
    image_tensor = image_tensor.to(device)
    model_mobileNet.eval()  
    with torch.no_grad():  
        outputs = model_mobileNet(image_tensor)
    
    _, predicted_class = torch.max(outputs, 1)

    predicted_class_name = class_names[predicted_class.item()]
    
    return predicted_class_name

def enhance_image(image_pil, device):
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    scale_factor = 4
    data_lowlight = torch.from_numpy(np.asarray(image_pil) / 255.0).float()
    data_lowlight = data_lowlight.permute(2, 0, 1).unsqueeze(0).to(device)
    
    DCE_net = model.enhance_net_nopool(scale_factor).to(device)
    DCE_net.load_state_dict(torch.load('service/snapshots/Epoch99plus.pth'))
    
    with torch.no_grad():
        enhanced_image, _ = DCE_net(data_lowlight)
    
    enhanced_pil = transforms.ToPILImage()(enhanced_image.squeeze().cpu())


    return enhanced_pil

def process_image(image_pil, device, model_yolo, model_mobileNet, class_names):
    image_np = np.array(image_pil)
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    results = model_yolo(image_bgr)
    detected_objects = []  

    for result in results:
        for i, box in enumerate(result.boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0].item())

            cropped_img = image_bgr[y1:y2, x1:x2]

            if cropped_img.shape[0] > 0 and cropped_img.shape[1] > 0:

                class_id = int(box.cls[0].item())
                predicted_class = model_yolo.model.names[class_id] 
                
                detected_objects.append({
                    "class": predicted_class,
                    "bbox": (x1, y1, x2, y2),
                    "confidence": confidence
                })
    
    for detected_object in detected_objects:
        detected_object["bbox"] = list(detected_object["bbox"])

    detected_objects_json = json.dumps(detected_objects)

    return detected_objects_json

def enhance_and_classify(image_pil, device, model_yolo, model_mobileNet, class_names):
    enhanced_pil = enhance_image(image_pil, device) 
    
    image_np = np.array(enhanced_pil)
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    results = model_yolo(image_bgr)
    detected_objects = [] 
    
    for result in results:
        for i, box in enumerate(result.boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0].item())
            cropped_img = image_bgr[y1:y2, x1:x2]
            
            if cropped_img.shape[0] > 0 and cropped_img.shape[1] > 0:
                class_id = int(box.cls[0].item())
                predicted_class = model_yolo.model.names[class_id] 
                
                detected_objects.append({
                    "class": predicted_class,
                    "bbox": (x1, y1, x2, y2),
                    "confidence": confidence
                })
    for detected_object in detected_objects:
        detected_object["bbox"] = list(detected_object["bbox"])

    detected_objects_json = json.dumps(detected_objects)
    
    return detected_objects_json

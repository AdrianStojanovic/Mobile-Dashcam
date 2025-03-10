import torch
from torchvision import transforms, models
from PIL import Image
import os

# This script is for testing purposes only. If you execute the model will classify images from a test folder.
# This script is not being used in the application. 
# Please keep also in mind that this model is only used for classification. The object detection is done by the YOLO model before.

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"used device: {device}")

# transformations (mobileNet expects 224x224)
transform = transforms.Compose([
    transforms.Resize((224, 224)), 
    transforms.ToTensor(), 
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

model = models.mobilenet_v2(pretrained=False) 
num_ftrs = model.classifier[1].in_features
model.classifier[1] = torch.nn.Linear(num_ftrs, len(os.listdir("[path to your training image folder]")))  #insert your own path here


model.load_state_dict(torch.load("mobilenetv2_trained_model.pth"))
model = model.to(device)

def classify_image(image_path):
    image = Image.open(image_path)

    input_tensor = transform(image)
    input_batch = input_tensor.unsqueeze(0)  

    input_batch = input_batch.to(device)

    model.eval() 
    with torch.no_grad():
        outputs = model(input_batch)
    
    _, predicted_class = torch.max(outputs, 1)

    class_names = os.listdir("[path to your training image folder]") #insert your own path here
    predicted_class_name = class_names[predicted_class.item()]
    
    return predicted_class_name

test_dir = "[path to your TEST image folder]"  #insert your own path here

image_files = [f for f in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, f)) and f.endswith(('.jpg', '.png', '.jpeg'))]
image_files = image_files[:1000] 

for filename in image_files:
    file_path = os.path.join(test_dir, filename)
    predicted_class = classify_image(file_path)
    print(f"image: {filename} -> predicted class: {predicted_class}")

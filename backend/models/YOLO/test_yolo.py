from ultralytics import YOLO

# This script is for testing purposes only. If you execute it a runs folder will be created where the results of YOLO object detection can be seen.
# This script is not being used in the application. 
# Please keep also in mind that yolo object classification is inaccurate, thats why it is only being used for object detection.

model = YOLO("trained_model.pt")
results = model("[test image folder path]", save=True) #insert your test image folder path here

for r in results:
    for box in r.boxes:
        print(f"Klasse: {box.cls}, Konfidenz: {box.conf}, BBox: {box.xyxy}")
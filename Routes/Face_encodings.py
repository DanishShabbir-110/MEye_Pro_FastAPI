import json
import os
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File
import face_recognition
import numpy as np
import cv2

def process_image_get_encoding_from_path(image_path: str):
    try:
        image = face_recognition.load_image_file(image_path)

        # Hard enforce correct format
        image = np.asarray(image, dtype=np.uint8)
        image = np.ascontiguousarray(image)

        # STEP 1: explicitly detect face locations (hog is safest)
        face_locations = face_recognition.face_locations(
            image,
            model="hog"   #  DO NOT use cnn
        )

        if not face_locations:
            print("No face detected")
            return None

        # STEP 2: generate encodings using detected locations
        encodings = face_recognition.face_encodings(
            image,
            known_face_locations=face_locations,
            num_jitters=1
        )

        if not encodings:
            return None

        return encodings[0].tolist()

    except Exception as e:
        print(f"Image Encoding Error ({image_path}): {e}")
        return None


async def save_face_encodings_from_paths(
    stu_regno: str,Role:str,
    image_paths: List[str]
):
    
    encodings_output = {}

    for img_path in image_paths:
        img_name = os.path.basename(img_path)

        if not os.path.exists(img_path):
            encodings_output[img_name] = None
            continue

        try:
            encoding = process_image_get_encoding_from_path(img_path)
            encodings_output[img_name] = encoding
        except Exception as e:
            print(f"Encoding error ({img_path}): {e}")
            encodings_output[img_name] = None

    # JSON file path
    if Role=="Student":
        json_file_path="EncodingsFile/student_encodings.json"
    else:
        json_file_path="EncodingsFile/teacher_encodings.json"   
   
    # Load existing JSON
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
    else:
        data = {}

    # Update  entry
    data[stu_regno] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "encodings": encodings_output
    }

    # Save JSON
    with open(json_file_path, "w") as f:
        json.dump(data, f, indent=4)
        
    return {
        "status": "success",
        "reg_no": stu_regno,
        "total_images": len(image_paths),
        "encodings_found": sum(1 for v in encodings_output.values() if v is not None),
        "message": "Student face encodings saved successfully from image paths"
    }
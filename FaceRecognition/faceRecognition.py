# from fastapi import FastAPI, HTTPException, UploadFile, File,APIRouter,Depends
# import cv2
# import numpy as np
# import tempfile
# import json
# import face_recognition
# import pyodbc
# from DB_Setup.connection import get_connection_for_face_Recognition
# from datetime import datetime


# router=APIRouter(prefix="/facerecognition",tags=["Testing"])

# @router.post("/markAttendance")
# async def markedAttendance(video:UploadFile=File(...)):
#     #Bytes read kara ga video sa
#     video_bytes=await video.read()
    
#     with tempfile.NamedTemporaryFile(delete=True,suffix=".mp4") as temp_video:
#         temp_video.write(video_bytes)
#         temp_video.flush()

#         final_list=process_video_and_save_frames(temp_video.name)
    
#     return{
#         "Attendance is marked":final_list,
#         "Total Students":len(final_list)
#     }


# ###Extract Frames from vedio
# def extract_frames(video_path):
#     cap=cv2.VideoCapture(video_path)

#     ##Ik minute mai 3 frames atract ho ga
#     fps=int(cap.get(cv2.CAP_PROP_FPS))
#     frames_interval=fps*20

#     frame_count=0
#     saved_frames=[]

#     while True:
#         ret,frame=cap.read()
#         if not ret:
#             break
#         if frame_count%frames_interval==0:
#             saved_frames.append(frame)

#         frame_count+=1    

#     cap.release()
#     return saved_frames




# def process_video_and_save_frames(video_path):
#     frames=extract_frames(video_path)

#     detectedList=[]

#     for frame in frames:
#         encodings=get_face_encodings(frame)

#         for encoding in encodings:
#             regno=match_with_json_file(encoding)
#             detectedList.append(regno if regno else "unknown")    

#     marked_attendance(detectedList)
#     return detectedList


# def get_face_encodings(frame):
#     rgb_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

#     face_locations=face_recognition.face_locations(rgb_frame)

#     encodings=face_recognition.face_encodings(
#         rgb_frame,face_locations
#     )

#     return encodings


# def match_with_json_file(unknownEncodings):
#     json_path="EncodingsFile/student_encodings.json"
#     THRESHOLD = 0.50
#     try:
#         with open(json_path,"r") as f:
#             stored_data=json.load(f)
#     except FileNotFoundError:
#         return None
    
#     knownEncodings=[]
#     knownRegnos=[]

#     # best_match=None
#     # min_distance=float("inf")

#     for regno,data in stored_data.items():
#         for pic_name, encoding in data["encodings"].items():
#             knownEncodings.append(encoding)
#             knownRegnos.append(regno)
#     if not knownEncodings:
#             return None
    
#     knownEncodings_np=np.array(knownEncodings,dtype=np.float64)
    
#     distances=face_recognition.face_distance(knownEncodings_np,unknownEncodings)
#     min_distance_index=np.argmin(distances)
#     min_distance=distances[min_distance_index]

#     if min_distance<=THRESHOLD:
#         return knownRegnos[min_distance_index]
    

# def marked_attendance(
#         detectedList   
# ):
#     conn=get_connection_for_face_Recognition()
#     now = datetime.now()
#     current_date = now.date()
#     current_time = now.time()
#     if conn is None:
#         return {"Error": "connection not built"}
#     try:
#         cursor=conn.cursor()
#         for stu in detectedList:
#             insert_query="Insert into [Student Attendance] (regno,[Date],[Time],[Status]) values (?,?,?,?)"
#             cursor.execute(insert_query,(stu,current_date,current_time,"Present"))
#         conn.commit()
#         cursor.close()    
#     except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))





from fastapi import FastAPI, HTTPException, UploadFile, File, APIRouter
import cv2
import numpy as np
import tempfile
import json
import face_recognition
import os
from DB_Setup.connection import get_connection_for_face_Recognition
from datetime import datetime

router = APIRouter(prefix="/facerecognition", tags=["Testing"])

# --- Global Settings ---
ENCODINGS_PATH = "EncodingsFile/student_encodings.json"
CAPTURED_FRAMES_DIR = "CapturedFrames"

# Folder create karein agar nahi hai
if not os.path.exists(CAPTURED_FRAMES_DIR):
    os.makedirs(CAPTURED_FRAMES_DIR)

cached_encodings = None
cached_regnos = None

def load_encodings():
    global cached_encodings, cached_regnos
    try:
        with open(ENCODINGS_PATH, "r") as f:
            stored_data = json.load(f)
        
        knownEncodings = []
        knownRegnos = []

        for regno, data in stored_data.items():
            for pic_name, encoding in data["encodings"].items():
                if isinstance(encoding, list) and len(encoding) == 128:
                    knownEncodings.append(encoding)
                    knownRegnos.append(regno)
        
        cached_encodings = np.array(knownEncodings, dtype=np.float64)
        cached_regnos = knownRegnos
        print("Encodings Loaded Successfully!")
    except FileNotFoundError:
        print("Encoding file not found.")
        cached_encodings = []
        cached_regnos = []

load_encodings()

@router.post("/markAttendance")
async def markedAttendance(video: UploadFile = File(...)):
    video_bytes = await video.read()
    
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp4") as temp_video:
        temp_video.write(video_bytes)
        temp_video.flush()
        
        processed_data = process_video_and_save_frames(temp_video.name)
    
    return {
        "Message": "Processing Complete",
        "Total Frames Saved": processed_data["total_frames"],
        "Total DB Entries": len(processed_data["entries"]),
        "Details": processed_data["entries"]
    }

def extract_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps == 0: fps = 30
    
    # Har 20 seconds baad 1 frame (Total 3 frames per minute)
    frames_interval = int(fps * 20) 

    frame_count = 0
    saved_frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frames_interval == 0:
            saved_frames.append(frame)

        frame_count += 1    

    cap.release()
    return saved_frames

def process_video_and_save_frames(video_path):
    frames = extract_frames(video_path)
    
    all_entries = []
    video_unknown_encodings = [] # Unknowns ko track karne k liye
    
    # Current Timestamp for unique filenames
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, frame in enumerate(frames):
        # 1. SAB SE PEHLE FRAME SAVE KAREIN (Requirement: 6 frames lazmi honay chahiyen)
        image_filename = f"Frame_{i}_{batch_timestamp}.jpg"
        save_path = os.path.join(CAPTURED_FRAMES_DIR, image_filename)
        cv2.imwrite(save_path, frame)
        
        # 2. Recognition Shuru (Resize hata diya taake Known detect ho sake)
        # Note: Resize hatane se accuracy barhegi, magar speed thori kam hogi
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Agar koi face detect hua to DB entry banayein
        for encoding in encodings:
            regno = None
            
            # Step A: Check Database (Known)
            matched_regno = match_with_json_file(encoding)
            
            if matched_regno:
                regno = matched_regno
            else:
                # Step B: Handle Unknowns (Consistent IDs)
                match_found = False
                if len(video_unknown_encodings) > 0:
                    unknowns_np = np.array(video_unknown_encodings)
                    distances = face_recognition.face_distance(unknowns_np, encoding)
                    
                    min_dist_idx = np.argmin(distances)
                    if distances[min_dist_idx] < 0.50:
                        match_found = True
                        regno = f"Unknown_{min_dist_idx + 1}"
                
                if not match_found:
                    video_unknown_encodings.append(encoding)
                    regno = f"Unknown_{len(video_unknown_encodings)}"

            # DB Entry List mai daalein
            if regno:
                entry_data = {
                    "regno": regno,
                    "status": "Unknown" if regno.startswith("Unknown") else "Present",
                    "image_path": save_path # Wohi frame jo upar save kia tha
                }
                all_entries.append(entry_data)

    # Database Insert
    if all_entries:
        mark_attendance_in_db(all_entries)
    
    return {
        "total_frames": len(frames), # Ye ab exactly 6 hoga (agar 2 min ki video hai)
        "entries": all_entries
    }

def match_with_json_file(unknown_encoding):
    global cached_encodings, cached_regnos
    THRESHOLD = 0.50 

    if cached_encodings is None or len(cached_encodings) == 0:
        return None

    distances = face_recognition.face_distance(cached_encodings, unknown_encoding)
    min_distance_index = np.argmin(distances)
    min_distance = distances[min_distance_index]

    if min_distance <= THRESHOLD:
        return cached_regnos[min_distance_index]
    
    return None

def mark_attendance_in_db(all_entries):
    conn = get_connection_for_face_Recognition()
    now = datetime.now()
    current_date = now.date()
    current_time = now.time()
    
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        
        for entry in all_entries:
            regno = entry["regno"]
            status = entry["status"]
            
            insert_query = "INSERT INTO [Student Attendance] (regno, [Date], [Time], [Status]) VALUES (?, ?, ?, ?)"
            cursor.execute(insert_query, (regno, current_date, current_time, status))
            print(f"Marked: {regno} in DB")

        conn.commit()
        cursor.close()    
    except Exception as e:
        print(f"DB Error: {str(e)}")
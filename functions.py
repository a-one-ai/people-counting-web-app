import cv2
cv2.setNumThreads(4)  # Set the number of threads for OpenCV

from ultralytics import YOLO
import math
import numpy as np
from pytube import YouTube
import streamlink
import pandas as pd
from ultralytics import YOLO
from tracker import Tracker
import cvzone
from datetime import datetime 
import time
import pyrebase
import base64
from flask import jsonify
import threading
import torch
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
torch.cuda.set_device(0) 
#num_cpu_cores = torch.multiprocessing.cpu_count()
torch.set_num_threads(4)  # Set the number of threads for PyTorch


tracker = Tracker()


# Add firebase configuration to connect firebase and upload data in it
firebaseConfig = {
  "apiKey": "AIzaSyDWvrfySM8YXYa6AWvmglGfQwgeccaf7WQ",
  "authDomain": "camera-c-97e7e.firebaseapp.com",
  "databaseURL": "https://camera-c-97e7e-default-rtdb.firebaseio.com",
  "projectId": "camera-c-97e7e",
  "storageBucket": "camera-c-97e7e.appspot.com",
  "messagingSenderId": "150541285688",
  "appId": "1:150541285688:web:56a9be67cf0d1fa80169cd",
  "measurementId": "G-KTFCLTGHT1"
}
# Intilaize firebase with the provided configuration (firebaseConfig)

firebase = pyrebase.initialize_app(firebaseConfig)
# Access firebase storage service

storage = firebase.storage()
# Access firebase realtime database service

db = firebase.database()


#Loading crowd model
crwod_model = YOLO("best_crowded.pt")
#Loading count model
count_model = YOLO('yolov8s.pt')
# Read Coco.txt to get class names objects for that we can detect it using yolo model
my_file = open("coco.txt", "r")
data = my_file.read()
class_list = data.split("\n")


def number_generator():
    number_generator.total = getattr(number_generator, 'total', 0) + 1
    return number_generator.total


# Function that return people counted in frame and the frame 
def count_humans(frame) :
    count = 0
    try :
      #Assign image to model
        results = crwod_model(frame,stream=True)

            # Getting bbox,confidence and class names informations to work with
            # Assign image to model to detect people and get boxes
        for info in results:
                boxes = info.boxes
                for box in boxes:
                    confidence = box.conf[0]
                    confidence = math.ceil(confidence * 100)
                    # Class = int(box.cls[0])
                    # Add box if confidence of detection more than or eqaul to 30% and count objects
                    if confidence >= 40:
                        x1,y1,x2,y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1),int(y1),int(x2),int(y2)
                        cv2.rectangle(frame,(x1,y1),(x2,y2),(0, 255, 0),2)
                        count +=1
                cv2.putText(frame, f"Count : {count}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (100,100,250), 5)
                # cv2.imwrite(f"counted_image.jpg" , frame)
        return count, frame

    except :
        print('\t>> Error Estimating Count')
        return count , frame
    

# Function that return url for youtube videos 
def youtube(url):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(file_extension="mp4",res="480p").first()
        video_url = stream.url
        return  video_url
    except:
        return "url error"
    
# Function that return url for live streaming (Facebook - Twitter - Youtube) 
def stream(url):
    try:
        streams = streamlink.streams(url)
        best_stream = streams["best"]
        return best_stream.url
    except:
        return "url error"

# Function to draw a line on the video frame
def draw_line(frame,points,up,down,counted_id,in_line):
    
    offset =  6
    results = count_model.predict(frame) 
    a = results[0].boxes.data
    try:
        a_gpu = torch.tensor(a).to("cuda:0") # Move to GPU

    #px = pd.DataFrame(a).astype("float")
        px = pd.DataFrame(a_gpu.cpu().numpy()).astype("float") # Convert to NumPy on CPU
    except:
        px = pd.DataFrame(a).astype("float")

    list = []
    for index, row in px.iterrows():
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])
        d = int(row[5])
     
        c = class_list[d]
        if 'person' in c:
            list.append([x1, y1, x2, y2]) 
    bbox_id = tracker.update(list)
    for bbox in bbox_id:
    #box axis and id
        x3, y3, x4, y4, id = bbox
        cx = (x3 + x4) // 2
        cy = (y3 + y4) // 2
        # drow circle in the center of the box
        cv2.circle(frame, (cx, cy), 4, (255, 0, 255), -1)
        # if the center point in the line
        if len(points) == 2: 
            if points[0][1] <(y3 + offset ) and points[0][1] >(y3-offset):
                cv2.rectangle(frame,(x3,y3),(x4,y4),(0,0,255))
                cvzone.putTextRect(frame,f'{id}',(x3,y3),1,2)
                # check if it calulated or not
                if id not in in_line:
                    in_line.append(id)
            # if the point in the line        
            else:
                # if the point go across the line and not counted 
                if id not in counted_id and id in in_line:
                    # if the point above line 
                    if  y3>(points[0][1] + offset+6):
                        up= up+1
                        in_line.remove(id)
                        counted_id.append(id)
                    # if the point under line
                    elif y3 <(points[0][1]-offset-6):
                        down = down+1
                        in_line.remove(id)
                        counted_id.append(id)
            cv2.line(frame, points[0],points[1], 100,4)        
            print('line done------------------------') 
   # Draw  2 text boxes for people passes line if there is in , out
    # Draw text box for total in&out people        
    cvzone.putTextRect(frame,f'Out{up}',(50,60),2,2)
    cvzone.putTextRect(frame,f'In{down}',(50,130),2,2)
    total = up-down
    cvzone.putTextRect(frame,f'Total{total}',(50,200),2,2)
    return frame,up,down,counted_id,in_line

# funciton that check 
def check_points(point):
    if len(point) > 2:  # Limit the number of points stored
        point = point[-2:] 
    return point

# funciton to Load data to firebase
def load_data_firebase(gate_name, frame, count):
    _, encoded_frame = cv2.imencode('.jpg', frame)
    frame_bytes = encoded_frame.tobytes()
    timestamp = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    file_name = f"{gate_name}{timestamp}.jpg"
    storage_ref = storage.child(file_name)
    firebase_path = storage_ref.put(frame)
    
    # Write frame number and timestamp to the Realtime Database
    db.child("timestamps").child(f"counter{timestamp}").push({"image_name": file_name, "Timestamp": timestamp, "count": count, "from": gate_name})
    return "done"

def get_coordinates(points, list=None):
    if list is None:
        list = []

    for x in points:
        list.append((int(x['x']), int(x['y'])))
    
    return list

#generate_frames for crowd people
def crowd_url(url):
    count = 0
    video_capture = cv2.VideoCapture(url) 
    while True:
        success, frame = video_capture.read()
        if not success:
            break
        else:
            frame = cv2.resize(frame, (700, 500))
            # if button == 1:
            #     print("here is button")
            #     count, img = count_humans(frame)

            #     _, encoded_image_data = cv2.imencode('.jpg', img)
            #     encoded_image_data = base64.b64encode(encoded_image_data).decode('utf-8')
            #     load_data_firebase("crowd", img, count)
            #     # Send back the processed image data
            #     return jsonify({'image_data': encoded_image_data})
    
            _, encoded_frame = cv2.imencode('.jpg', frame)
            frame_bytes = encoded_frame.tobytes()      
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    video_capture.release()



class VideoFeed:
    def __init__(self, camera_type, gate_name, points):
        self.camera_type = camera_type
        self.gate_name = gate_name
        self.points = points
        self.points_lock = threading.Lock()
        self.video_capture = cv2.VideoCapture(self.camera_type)
        self.in_line = []
        self.up = 0
        self.down = 0
        self.wait = 0
        self.total = self.down - self.up
        self.counted_id = []
        self.start_time = time.time()

    def update_points(self, new_points):
       # with self.points_lock:
        self.points = new_points
 
    def generate_frames(self):
        up =0
        down = 0
        counted_id=[]
        in_line = []
        while True:
            try:
                success, frame = self.video_capture.read()
                #with self.points_lock:
                points = self.points  # Get the points
                if not success:
                    print("not success")
                    break
                print('thepointis',points)
                frame = cv2.resize(frame, (700, 500))
            # Your frame processing logic using updated points...
                try:
                    frame, up, down, counted_id, in_line = draw_line(frame, points, up, down, counted_id, in_line)
                except:
                    print("line errorss")
                _, encoded_frame = cv2.imencode('.jpg', frame)
                frame_bytes = encoded_frame.tobytes()
                current_time = time.time()

                elapsed_time = current_time - self.start_time
                if elapsed_time >= 300:
                    self.start_time = time.time()
               
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                print("caught an exception: ", e)
    def release_capture(self):
        self.video_capture.release()

# class CauntCamera:
#     def __init__(self, camera_type, gate_name, points,frame):
#         self.camera_type = camera_type
#         self.gate_name = gate_name
#         self.points = points
#         self.points_lock = threading.Lock()
#         self.in_line = []
#         self.up = 0
#         self.down = 0
#         self.wait = 0
#         self.total = self.down - self.up
#         self.counted_id = []
#         self.start_time = time.time()
#         self.frame = frame
#     def update_points(self, new_points):
#         with self.points_lock:
#             self.points = new_points
#     def frames(self, new_frame):
#         with self.points_lock:
#             self.frame = new_frame
    
#     def process_frame(self, frame,up,down,counted_id, in_line):
#         # Convert base64 string to numpy array
#         encoded_data = frame.split(',')[1]  # Remove header from base64 data
#         nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
#         frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

#         frame = cv2.resize(frame, (640, 480))

#         # Create a copy of the frame for processing
#         # processed_frame = frame.copy()

#         # Example: Drawing a line on the frame
#         processed_frame,up,down,counted_id,in_line = draw_line(frame,points,up,down,counted_id,in_line)
#         print("good")
#         # Convert processed frame back to base64 string
#         _, encoded_frame = cv2.imencode('.jpg', processed_frame)
#         processed_frame_data = base64.b64encode(encoded_frame).decode('utf-8')
#         return processed_frame_data

def generate_and_increment():
    # Initialize a counter if it doesn't exist
    if 'counter' not in generate_and_increment.__dict__:
        generate_and_increment.counter = 0
    # Generate the current number
    current_number = generate_and_increment.counter
    # Increment the counter for the next call
    generate_and_increment.counter += 1
    return current_number

class User:
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.points = []  # Initialize points for each user

    def process_frame(self, frame_data):
        # Process frame received from the frontend for this user
        # Adjust this logic based on your requirements
        encoded_data = frame_data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        width = 640
        height = 480
        frame = cv2.resize(frame, (width, height))
        up = 0
        down = 0
        counted_id = []
        in_line = []
        try:

            processed_frame, up, down, counted_id, in_line = draw_line(frame, self.points, up, down, counted_id, in_line)
        except:
            print("line errors")
        print("Good")
        
        _, encoded_frame = cv2.imencode('.jpg', processed_frame)
        processed_frame_data = base64.b64encode(encoded_frame).decode('utf-8')
        return processed_frame_data



class CameraCrowdUser:
    def __init__(self, ip):
        self.ip = ip
        self.captured_image_data = None  # Initialize captured image data as None for each user
        
    def set_captured_image_data(self, image_data):
        self.captured_image_data = image_data
        
    def get_captured_image_data(self):
        return self.captured_image_data
    





class url_crowd_VideoFeed:
    def __init__(self, camera_type):
        self.camera_type = camera_type
        self.cap_frame = None
        self.frame_lock = threading.Lock()
        self.video_capture = cv2.VideoCapture(self.camera_type)
        self.in_line = []
        self.up = 0
        self.down = 0
        self.wait = 0
        self.total = self.down - self.up
        self.counted_id = []
        self.start_time = time.time()

    def update_frame(self, new_frame):
        with self.frame_lock:
            self.frame = new_frame
    
    def process_cap_frame(self,cap_frame):
        count,frame = count_humans(cap_frame)
        return count,frame
    def generate_frames(self):
        up =0
        down = 0
        counted_id=[]
        in_line = []
        while True:
            success, frame = self.video_capture.read()
            if not success:
                break
            frame = cv2.resize(frame, (700, 500))
            # Your frame processing logic using updated points...
            self.cap_frame = frame
            _, encoded_frame = cv2.imencode('.jpg', frame)
            frame_bytes = encoded_frame.tobytes()
            current_time = time.time()

            elapsed_time = current_time - self.start_time
            if elapsed_time >= 300:
                self.start_time = time.time()
                # Your other logic...

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def release_capture(self):
        self.video_capture.release()


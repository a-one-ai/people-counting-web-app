from flask_cors import CORS
from flask import redirect, url_for
from flask import Flask, render_template, Response, request, jsonify
import numpy as np
from functions import *

import cv2
# cv2.setNumThreads(4)  # Set the number of threads for OpenCV
# import torch
# device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
# torch.cuda.set_device(0)
#num_cpu_cores = torch.multiprocessing.cpu_count()
# torch.set_num_threads(4)

app = Flask(__name__)
CORS(app) 


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        selection = request.form['selection']  # Get the selection (url,camera)
        gate_name = request.form['gate_name']  # Get the gate name
        button = request.form['button']        # Get the button that pressed
        url = request.form.get('url')          # Get the URL input value if present

        if url != '':
            try:
                try_url = youtube(url)
                if try_url =='url error':
                    url = stream(url)
                else:
                    url = try_url
            except:
                return "url error"
            
        ip = gate_name+"_"+str(number_generator())
        if gate_name.strip() == "":
            return render_template('form.html', error="Please write the gate name")
        elif selection == 'url' and url.strip() == "":
            return render_template('form.html', error="Please enter the URL")

        if selection == 'url' and button == 'count':
            rout = 'url_count'
            return redirect(url_for(rout, my_gate_name=gate_name, url=url, ip=ip))
        elif selection == 'url' and button == 'crowd':
            rout = 'url_crowd'
            return redirect(url_for(rout, my_gate_name=gate_name, url=url,ip=ip))
        elif selection == 'url' and button == 'border':
            rout = 'url_border'
            return redirect(url_for(rout, my_gate_name=gate_name,url=url,ip=ip))


        elif selection == 'camera' and button == 'count':
            rout = 'camera_count'
            return redirect(url_for(rout, my_gate_name=gate_name,ip=ip))
        elif selection == 'camera' and button == 'crowd':
            rout = 'camera_crowd'
            return redirect(url_for(rout, my_gate_name=gate_name,ip=ip))
        elif selection == 'camera' and button == 'border':
            rout = 'camera_border'
            return redirect(url_for(rout, my_gate_name=gate_name,ip=ip))
    return render_template('form.html')


#############url_count
url_count_users = {}  # Store video feeds for different clients
@app.route('/url_count')
def url_count():
    gate_name = request.args.get('my_gate_name')
    url = request.args.get('url')
    ip = request.args.get('ip')
    return render_template('url_count.html', gate_name=gate_name, url=url,ip=ip)


@app.route('/update_coordinates', methods=['POST'])
def update_coordinates():
    data = request.json
    received_coordinates = data.get('coordinates')
    ip = data.get('ip') 
    if received_coordinates:
        points = get_coordinates(received_coordinates)
        points = check_points(points)
        client_id = ip  # Get client IP as a unique identifier
        if client_id not in url_count_users:
            return jsonify({"error": "Video feed not found for this client"})
        video_feed = url_count_users[client_id]
        video_feed.points = points  # Ensure 'update_points' method updates the points correctly

        return jsonify({"success": True, "points": points})
    return jsonify({"error": "Invalid request"})

@app.route('/video_feed', methods=['GET', 'POST'])
def video_feed(): 
    points = request.args.get('points')
    url = request.args.get('url')
    gate_name = request.args.get('gate_name')
    ip = request.args.get('ip')  # Get the 'ip' parameter from the query string
    client_id = ip  # Unique client identifier
    if client_id not in url_count_users:
        url_count_users[client_id] = countUrl_VideoFeed(url, gate_name, points)
    return Response(url_count_users[client_id].generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')      

@app.route('/release_capture', methods=['POST'])
def release_capture():
    ip = request.args.get('ip')
    client_id = ip
    if client_id in url_count_users:
        url_count_users[client_id].release_capture()
        del url_count_users[client_id]  # Remove the video feed for the client
        return jsonify({"success": True})
    return jsonify({"error": "Video feed not found for this client"})

#######camera_count
camera_count_users = {}  # Dictionary to store user instances

# camear_count route for render camera_count template
@app.route('/camera_count')
def camera_count():
    gate_name = request.args.get('my_gate_name')
    ip = request.args.get('ip')
    return render_template('camera_count.html', gateNameInput=gate_name, ip=ip)

# receive frames form frontend and process it and return it to user 
@app.route('/process_frame', methods=['POST'])
def process_received_frame():
    if request.method == 'POST':
        frame_data = request.json['frame']
        ip = request.json['ip']
        client_id = ip

        if client_id not in camera_count_users:
            camera_count_users[client_id] = camera_count_User(client_id)

        user = camera_count_users[client_id]
        processed_data = user.process_frame(frame_data)
        
        return jsonify({'processed_frame': processed_data})

@app.route('/mouse_event', methods=['POST'])
def handle_mouse_event():
    if request.method == 'POST':
        data = request.json
        x = int(data.get('x'))
        y = int(data.get('y'))
        ip = data.get('ip')
        print('the ip is is is ***************',ip)
        # client_id = request.remote_addr  # Get client IP as a unique identifier
        client_id = ip  # Get client IP as a unique identifier

        if client_id not in camera_count_users:
            camera_count_users[client_id] = camera_count_User(client_id)
        
        user = camera_count_users[client_id]
        user.points.append((x, y))
        user.points = check_points(user.points)
        print('Points received:', user.points)

        return jsonify({'message': 'Coordinates received successfully'})

###################################################


# Dictionary to store CameraCrowdUser instances based on user IP
camera_crowd_users = {}

@app.route('/camera_crowd')   
def camera_crowd():
    gate_name = request.args.get('my_gate_name')
    ip = request.args.get('ip')
    
    # Check if the user already exists based on their IP
    if ip in camera_crowd_users:
        # User exists, retrieve their instance
        user_instance = camera_crowd_users[ip]
    else:
        # Create a new instance for the user
        user_instance = CameraCrowdUser(ip)
        camera_crowd_users[ip] = user_instance
    
    return render_template('camera_crowd.html', gateNameInput=gate_name, ip=ip)


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    try:
        data = request.json
        ip = data.get('ip')  # Retrieve the 'ip' value from the JSON payload
        print('the ip is', ip) 
        # Retrieve or create the user instance based on IP
        if ip in camera_crowd_users:
            user_instance = camera_crowd_users[ip]
        else:
            user_instance = CameraCrowdUser(ip)
            camera_crowd_users[ip] = user_instance
        
        # Receive the image data from the client

        image_data = data.get('image_data')
        
        # Set the captured image data for the user instance
        user_instance.set_captured_image_data(image_data)
        
        # Get the captured image data for processing or other operations
        captured_image_data = user_instance.get_captured_image_data()
 # Decode the base64-encoded image data
        image_bytes = base64.b64decode(captured_image_data.split(',')[1])

        # Convert the image data to a NumPy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # Decode the NumPy array to a CV2 image
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Perform processing on the captured image data if needed
        count, img = count_humans(frame)
        _, encoded_image_data = cv2.imencode('.jpg', img)
        encoded_image_data = base64.b64encode(encoded_image_data).decode('utf-8')

            
        # Assuming img is a base64-encoded image string
        img_bytes = base64.b64decode(img)
    
        # Send back the processed image data
        return jsonify({'image_data': encoded_image_data})

    except Exception as e:
        error_message = f"Error processing image: {e}"
        print(error_message)

#***************************************************


url_crowd_users = {}


class UrlCrowdVideoFeed:
    def __init__(self, camera_type):
        self.camera_type = camera_type
        self.cap_frame = None
        self.video_capture = cv2.VideoCapture(self.camera_type)

    def get_frames(self):
        while True:
            success, frame = self.video_capture.read()
            if not success:
                break
            frame = cv2.resize(frame, (700, 500))
            self.cap_frame = frame
            _, encoded_frame = cv2.imencode('.jpg', frame)
            frame_bytes = encoded_frame.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def release_capture(self):
        self.video_capture.release()


@app.route('/url_crowd')
def url_crowd():
    gate_name = request.args.get('my_gate_name')
    url = request.args.get('url')
    ip = request.args.get('ip')
    print("ggggg",gate_name)
    print("uuuuuuu",url)
    print("ip",ip)
    if ip not in url_crowd_users:
        url_crowd_users[ip] = UrlCrowdVideoFeed(url)
    print("dictio ",url_crowd_users)
    return render_template('url_crowd.html', gate_name=gate_name, url=url, ip=ip)


@app.route('/capture_signal', methods=['POST'])
def capture_signal():
    data = request.json
    value = data.get('value')
    ip = data.get('ip')
    print("the is fjaiojiae",ip)
    if value and ip in url_crowd_users:
        user_instance = url_crowd_users[ip]
        processed_image_data = process_captured_frame(user_instance.cap_frame)
        return jsonify({'image': processed_image_data})

    return jsonify({'message': 'Invalid request'})


def process_captured_frame(cap_frame):
    if cap_frame is not None:
        count,frame = count_humans(cap_frame)
        _, encoded_image = cv2.imencode('.jpg', frame)
        encoded_image_data = base64.b64encode(encoded_image).decode('utf-8')
        return encoded_image_data

    return None


@app.route('/crowd_video_feed', methods=['GET', 'POST'])
def crowd_video_feed():
    url = request.args.get('url')
    ip = request.args.get('ip')
    print("mmmmmm",url)
    print("IIIIIIIII",ip)
    if ip in url_crowd_users:
        return Response(url_crowd_users[ip].get_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    return jsonify({"error": "Video feed not found"})

###################################################


@app.route('/url_border')
def url_border():
    gate_name = request.args.get('my_gate_name')
    url = request.args.get('url')
    ip = request.args.get('ip')
    print('**************************************')
    print(gate_name)
    print(url)
    print(ip)
    return render_template('url_border.html', gate_name=gate_name, url=url,ip=ip)

border_video_feeds = {}  # Store video feeds for different clients

@app.route('/border_video_feed', methods=['GET', 'POST'])
def border_video_feed(): 

    url = request.args.get('url')
    gate_name = request.args.get('gate_name')
    ip = request.args.get('ip')  # Get the 'ip' parameter from the query string
    print("my IP is the ......",ip )
    # client_id = request.remote_addr  # Unique client identifier
    client_id = ip  # Unique client identifier

    if client_id not in border_video_feeds:
        border_video_feeds[client_id] = border_VideoFeed(url, gate_name)

    print('iam the caunt man',border_video_feeds[client_id].count)
    return Response(border_video_feeds[client_id].generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
      
@app.route('/get_count')
def get_count():
    ip = request.args.get('ip')
    client_id = ip

    if client_id in border_video_feeds:
        count = border_video_feeds[client_id].count
        return jsonify({'count': count})

    return jsonify({'count': 0})  # Return default count if client_id not found

#####################################################################camera_border

user_dict_border = {}  # Dictionary to store user instances
@app.route('/camera_border')
def camera_border():
    gate_name = request.args.get('my_gate_name')
    ip = request.args.get('ip')
    return render_template('camera_border.html', gateNameInput=gate_name, ip=ip)

@app.route('/process_frame_border', methods=['POST'])
def process_frame_border():
    if request.method == 'POST':
        frame_data = request.json['frame']
        ip = request.json['ip']  # Get 'ip' from the request body
        # client_id = request.remote_addr  # Get client IP as a unique identifier
        client_id = ip  # Get client IP as a unique identifier

        print("the ip is .......................",ip)
        if client_id not in user_dict_border:
            user_dict_border[client_id] = border_User(client_id)
        user = user_dict_border[client_id]
        processed_data,count = user.process_frame(frame_data)
        print("All good")
        return jsonify({'processed_frame': processed_data,'count':count})

# @app.route('/mouse_event', methods=['POST'])
# def handle_mouse_event():
#     if request.method == 'POST':
#         data = request.json
#         x = int(data.get('x'))
#         y = int(data.get('y'))
#         ip = data.get('ip')
#         print('the ip is is is ***************',ip)
#         # client_id = request.remote_addr  # Get client IP as a unique identifier
#         client_id = ip  # Get client IP as a unique identifier

#         if client_id not in user_dict:
#             user_dict[client_id] = User(client_id)
        
#         user = user_dict[client_id]
#         user.points.append((x, y))
#         user.points = check_points(user.points)
#         print('Points received:', user.points)

#         return jsonify({'message': 'Coordinates received successfully'})




if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7050)


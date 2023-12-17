from flask_cors import CORS
from flask import redirect, url_for
from flask import Flask, render_template, Response, request, jsonify

import cv2

cv2.setNumThreads(1)  # Set the number of threads for OpenCV

import torch
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
torch.cuda.set_device(0) 
torch.set_num_threads(1)  # Set the number of threads for PyTorch



from datetime import datetime 
# from  crowdDensity import counter
import numpy as np
# from crowd_frames import count_humans
from functions import *
import cv2
import urllib.request
import threading
app = Flask(__name__)
CORS(app) 

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selection = request.form['selection']
        gate_name = request.form['gate_name']
        button = request.form['button']
        print(selection)
        print(button)
        url = request.form.get('url')  # Get the URL input value if present
        print(url)
        if url != '':
            try:
                try_url = youtube(url)
                print("the url", url)
                if try_url =='url error':
                    url = stream(url)
                else:
                    url = try_url
            except:
                return "url error"
        if gate_name.strip() == "":
            return render_template('form.html', error="Please write the gate name")
        elif selection == 'url' and url.strip() == "":
            return render_template('form.html', error="Please enter the URL")

        if selection == 'url' and button == 'count':
            rout = 'url_count'
            return redirect(url_for(rout, my_gate_name=gate_name, url=url))
        elif selection == 'url' and button == 'crowd':
            rout = 'url_crowd'
            return redirect(url_for(rout, my_gate_name=gate_name, url=url))
        elif selection == 'camera' and button == 'count':
            rout = 'camera_count'
            url = ''
            print("url is ",url)
            return redirect(url_for(rout, my_gate_name=gate_name))
        elif selection == 'camera' and button == 'crowd':
            rout = 'camera_crowd'
            return redirect(url_for(rout, my_gate_name=gate_name))

    return render_template('form.html')


@app.route('/url_count')
def url_count():
    gate_name = request.args.get('my_gate_name')
    url = request.args.get('url')
    return render_template('url_count.html', gate_name=gate_name, url=url)

video_feeds = {}  # Store video feeds for different clients

@app.route('/update_coordinates', methods=['POST'])
def update_coordinates():
    data = request.json
    received_coordinates = data.get('coordinates')
    gate_name = request.args.get('gate_name')  # Ensure 'gate_name' is properly extracted
    if received_coordinates:
        points = get_coordinates(received_coordinates)
        points = check_points(points)
        client_id = request.remote_addr  # Get client IP as a unique identifier
        print("****************************************************************************")
        print("****************************************************************************")
        print("*******************************Maggy*********************************************")
        print("****************************************************************************")
        print("****************************************************************************")
        print("****************************************************************************")
        print("*****************************Mostafa***********************************************")
        print("****************************************************************************")
        print("****************************************************************************")
        print("****************************************************************************")
        print("******************************Aslam**********************************************")
        print("****************************************************************************")
        print("****************************************************************************")
        print("****************************************************************************")
        print("****************************************************************************")
   
        print(request.remote_addr)
        if client_id not in video_feeds:
            return jsonify({"error": "Video feed not found for this client"})
        video_feed = video_feeds[client_id]
        video_feed.update_points(points)  # Ensure 'update_points' method updates the points correctly
        print('update points',points)
        print(video_feed.update_points(points))
        return jsonify({"success": True, "points": points})
    return jsonify({"error": "Invalid request"})

@app.route('/video_feed', methods=['GET', 'POST'])
def video_feed(): 
    points = request.args.get('points')
    url = request.args.get('url')
    gate_name = request.args.get('gate_name')

    client_id = request.remote_addr  # Unique client identifier
    if client_id not in video_feeds:
        video_feeds[client_id] = VideoFeed(url, gate_name, points)
    return Response(video_feeds[client_id].generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/release_capture', methods=['POST'])
def release_capture():
    client_id = request.headers.get('X-Forwarded-For') or request.headers.get('X-Real-IP')  # Unique client identifier
    if client_id in video_feeds:
        video_feeds[client_id].release_capture()
        del video_feeds[client_id]  # Remove the video feed for the client
        return jsonify({"success": True})
    return jsonify({"error": "Video feed not found for this client"})


user_dict = {}  # Dictionary to store user instances

@app.route('/camera_count')
def camera_count():
    gate_name = request.args.get('my_gate_name')
    return render_template('camera_count.html', gateNameInput=gate_name)

@app.route('/process_frame', methods=['POST'])
def process_received_frame():
    if request.method == 'POST':
        frame_data = request.json['frame']
        client_id = request.remote_addr  # Get client IP as a unique identifier
        
        if client_id not in user_dict:
            user_dict[client_id] = User(client_id)
        
        user = user_dict[client_id]
        processed_data = user.process_frame(frame_data)
        print("All good")

        return jsonify({'processed_frame': processed_data})

@app.route('/mouse_event', methods=['POST'])
def handle_mouse_event():
    if request.method == 'POST':
        data = request.json
        x = int(data.get('x'))
        y = int(data.get('y'))

        client_id = request.remote_addr  # Get client IP as a unique identifier
        
        if client_id not in user_dict:
            user_dict[client_id] = User(client_id)
        
        user = user_dict[client_id]
        user.points.append((x, y))
        user.points = check_points(user.points)
        print('Points received:', user.points)

        return jsonify({'message': 'Coordinates received successfully'})



if __name__ == '__main__':
    app.run(debug=True ,host="0.0.0.0", port=6001)


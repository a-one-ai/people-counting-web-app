from flask_cors import CORS
from flask import redirect, url_for
from flask import Flask, render_template, Response, request, jsonify
import cv2
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
        elif selection == 'url' and button == 'crowd':
            rout = 'url_crowd'
        elif selection == 'camera' and button == 'count':
            rout = 'camera_count'
        elif selection == 'camera' and button == 'crowd':
            rout = 'camera_crowd'
        
        return redirect(url_for(rout, my_gate_name=gate_name, url=url))

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
        client_id = request.remote_addr  # Unique client identifier
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
    client_id = request.remote_addr  # Unique client identifier
    if client_id in video_feeds:
        video_feeds[client_id].release_capture()
        del video_feeds[client_id]  # Remove the video feed for the client
        return jsonify({"success": True})
    return jsonify({"error": "Video feed not found for this client"})












# @app.route('/url_crowd')
# def url_crowd():
#     url = request.args.get('url')
#     gate_name = request.args.get('gate_name')
#     print(gate_name)
#     return render_template('url_crowd.html', gate_name=gate_name, url=url)


# value = 0
# @app.route('/crowd_video_feed', methods=['GET', 'POST'])
# def crowd_video_feed():
#     global value

#     if request.method == 'POST':
#         data = request.json
#         value = data.get('value')
#         print(value)
#         return "Coordinates received successfully"

#     url = request.args.get('url')
#     gate_name = request.args.get('gate_name')

#     def crowd_url(url):
#         count = 0
#         video_capture = cv2.VideoCapture(url)
#         while True:
#             success, frame = video_capture.read()
#             if not success:
#                 break
#             else:
#                 frame = cv2.resize(frame, (700, 500))
#                 print(value)
#                 if value == 1:
#                     print("Button pressed")
#                     count, img = count_humans(frame)

#                     _, encoded_image_data = cv2.imencode('.jpg', img)
#                     encoded_image_data = base64.b64encode(encoded_image_data).decode('utf-8')
#                     yield jsonify({'image_data': encoded_image_data})  # Yield processed data
                
#                 _, encoded_frame = cv2.imencode('.jpg', frame)
#                 frame_bytes = encoded_frame.tobytes()
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
#         video_capture.release()

#     return Response(crowd_url(url), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route('/crowd_video_feed')
# # Function that returns a response object for video streaming using generate_frames function
# def crowd_video_feed():
#     with app.app_context():
#         url = request.args.get('url')
#         gate_name = request.args.get('gate_name')
#         print(gate_name)
#         return Response(crowd_url(url), mimetype='multipart/x-mixed-replace; boundary=frame')


# @app.route('/temp3')
# def temp3():
#     gate_name = request.args.get('my_gate_name')
#     return render_template('temp3.html', gate_name=gate_name)

# @app.route('/temp4')
# def temp4():
#     gate_name = request.args.get('my_gate_name')
#     return render_template('temp4.html', gate_name=gate_name)


# # Function that returns a response object for video streaming using generate_frames function
# @app.route('/video_feed')
# def video_feed():
#     gate_name = 'get_gate_name()'
#     return Response(generate_frames(gate_name), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)








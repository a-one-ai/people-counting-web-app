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



@app.route('/video_feed', methods=['GET', 'POST'])
def video_feed():
    points = []  # Initialize an empty list for coordinates

    if request.method == 'POST':
        data = request.json
        received_coordinates = data.get('coordinates')
        if received_coordinates:
            points = get_coordinates(received_coordinates)
            points = check_points(points)
            print(points)
            return "Coordinates received successfully"
    print("it's a fkn point",points)
    url = request.args.get('url')
    gate_name = request.args.get('gate_name')
    # generate_frames for counting people 
    def generate_frames(camera_type, gate_name):
        print("it's a fkn point",points)
        print(type(points))
        in_line = []
        up = 0 
        down = 0
        wait = 0
        total = down-up
        counted_id = []
        # Set the start time
        start_time = time.time()
        # Open video
        try:
            video_capture = cv2.VideoCapture(camera_type)
        except Exception as e:
            print(f"Error opening video capture: {e}")
            return
        while True:
            # Return frame of video 
            
            success, frame = video_capture.read()
            print("its a point", points)
            if not success:
                print("End of video stream")
                break
            else:
                # Resize frame
                frame = cv2.resize(frame, (700, 500))

                # Calling funcation that apply the model and draw the line and points on the frame
                frame,up,down,counted_id,in_line = draw_line(frame,points,up,down,counted_id,in_line)
                print(points)
                print(len(points))
                print(type(points))

                _, encoded_frame = cv2.imencode('.jpg', frame)
                frame_bytes = encoded_frame.tobytes()
                current_time = time.time()

                # Calculate the elapsed time
                elapsed_time = current_time - start_time
                if elapsed_time >= 300:
                    # Reset the start time
                    start_time = time.time()
                    load_data_firebase(gate_name, frame, total)
                    print("frames loaded to firebase")

                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')        
        video_capture.release()
    return Response(generate_frames(url, gate_name), mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/url_crowd')
def url_crowd():
    url = request.args.get('url')
    gate_name = request.args.get('gate_name')
    print(gate_name)
    return render_template('url_crowd.html', gate_name=gate_name, url=url)


value = 0
@app.route('/crowd_video_feed', methods=['GET', 'POST'])
def crowd_video_feed():
    global value

    if request.method == 'POST':
        data = request.json
        value = data.get('value')
        print(value)
        return "Coordinates received successfully"

    url = request.args.get('url')
    gate_name = request.args.get('gate_name')

    def crowd_url(url):
        count = 0
        video_capture = cv2.VideoCapture(url)
        while True:
            success, frame = video_capture.read()
            if not success:
                break
            else:
                frame = cv2.resize(frame, (700, 500))
                print(value)
                if value == 1:
                    print("Button pressed")
                    count, img = count_humans(frame)

                    _, encoded_image_data = cv2.imencode('.jpg', img)
                    encoded_image_data = base64.b64encode(encoded_image_data).decode('utf-8')
                    yield jsonify({'image_data': encoded_image_data})  # Yield processed data
                
                _, encoded_frame = cv2.imencode('.jpg', frame)
                frame_bytes = encoded_frame.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        video_capture.release()

    return Response(crowd_url(url), mimetype='multipart/x-mixed-replace; boundary=frame')

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
    app.run(debug=True, port=5001)







    
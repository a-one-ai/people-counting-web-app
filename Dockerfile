FROM nvidia/cuda:11.1.1-cudnn8-runtime-ubuntu20.04


RUN apt-get update && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

RUN apt-get update && \
    apt-get install -y python3 python3-pip

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
# Assuming you have a requirements.txt file. If not, you can install packages directlyRUN pip install --no-cache-dir -r requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run app.py using torchrun when the container launches
CMD ["torchrun", "app.py"]

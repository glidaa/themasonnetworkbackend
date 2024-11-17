# Use a base image with Python and CUDA support if GPU support is needed
FROM nvidia/cuda:11.7.1-cudnn8-devel-ubuntu20.04

# Set up dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip git && \
    pip3 install torch transformers flask

# Clone the LLaMA repository (adjust the URL if you have a custom version)
WORKDIR /app
RUN git clone https://github.com/facebookresearch/llama.git
WORKDIR /app/llama

# Install LLaMA and dependencies
RUN pip3 install -r requirements.txt

# Copy the Flask app to the container
COPY app.py /app/app.py

# Expose the port the app runs on
EXPOSE 8000

# Set the entry point to launch the Flask app
ENTRYPOINT ["python3", "/app/app.py"]

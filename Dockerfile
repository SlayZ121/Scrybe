FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

# Copy source code and requirements
COPY main.py src/extract.py run.py requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download models into models/ folder
RUN python run.py

# Create runtime folders
RUN mkdir -p /app/input /app/output


CMD ["python", "main.py"]

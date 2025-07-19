FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

COPY process_pdfs.py extract.py requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/input /app/output

CMD ["python", "process_pdfs.py"]
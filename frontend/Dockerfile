FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

ENV API_URL=http://backend:8000/summarize

EXPOSE 8501

COPY frontend.py .

CMD ["streamlit", "run", "frontend.py", "--server.address=0.0.0.0", "--server.port=8501"]

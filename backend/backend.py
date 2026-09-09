# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from transformers import pipeline
import requests
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

app = FastAPI()

class SummarizeRequest(BaseModel):

    url: str
    model: str
    max_length: int = 150
    min_length: int = 40

# 모델 캐시
MODEL_CACHE = {}


def get_model(model_name):
    if model_name not in MODEL_CACHE:
        MODEL_CACHE[model_name] = pipeline(
            task="summarization",
            model=model_name,
            tokenizer=model_name,
            framework="pt"
        )
    return MODEL_CACHE[model_name]

def extract_url(url):
    headers = {
        "User-Agent":"Mozilla/5.0"
    }
    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )
    response.raise_for_status()
    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )
    paragraphs = [
        p.get_text(" ", strip=True)
        for p in soup.find_all("p")
    ]
    return "\n".join(paragraphs)

@app.post("/summarize")

def summarize(req: SummarizeRequest):
    try:
        text = extract_url(req.url)
        if len(text) == 0:
            raise HTTPException(
                status_code=400,
                detail="본문을 추출할 수 없습니다."
            )
        summarizer = get_model(req.model)
        result = summarizer(
            text,
            max_length=req.max_length,
            min_length=req.min_length,
            truncation=True
        )
        return {
            "model": req.model,
            "summary": result[0]["summary_text"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================
# Database
# =========================

DATABASE_URL = "sqlite:///./summaries.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    model = Column(String, nullable=False)
    max_length = Column(Integer)
    min_length = Column(Integer)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


# =========================
# Request Model
# =========================

class SummaryRequest(BaseModel):
    url: str
    model: str
    max_length: int
    min_length: int


# =========================
# Summarize API
# =========================

@app.post("/summarize")
def summarize(request: SummaryRequest):

    # 기사 가져오기
    response = requests.get(request.url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(" ", strip=True)

    # 모델 로딩
    summarizer = pipeline(
        "summarization",
        model=request.model
    )

    # 요약
    result = summarizer(
        text,
        max_length=request.max_length,
        min_length=request.min_length,
        do_sample=False
    )

    summary_text = result[0]["summary_text"]

    # =========================
    # DB 저장
    # =========================

    db = SessionLocal()

    try:
        history = Summary(
            url=request.url,
            model=request.model,
            max_length=request.max_length,
            min_length=request.min_length,
            summary=summary_text
        )

        db.add(history)
        db.commit()
        db.refresh(history)

        return {
            "id": history.id,
            "url": history.url,
            "model": history.model,
            "summary": history.summary,
            "created_at": history.created_at
        }

    finally:
        db.close()


# =========================
# History API
# =========================

@app.get("/history")
def get_history():

    db = SessionLocal()

    try:
        histories = (
            db.query(Summary)
            .order_by(Summary.created_at.desc())
            .all()
        )

        return [
            {
                "id": item.id,
                "url": item.url,
                "model": item.model,
                "max_length": item.max_length,
                "min_length": item.min_length,
                "summary": item.summary,
                "created_at": item.created_at
            }
            for item in histories
        ]

    finally:
        db.close()

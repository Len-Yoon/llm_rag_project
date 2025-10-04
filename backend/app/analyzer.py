# backend/app/analyzer.py
from transformers import pipeline

# 1. 감성 분석 (한국어/영어 지원되는 멀티 모델)
_sentiment = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

# 2. 요약 모델 (작은 T5 사용)
_summarizer = pipeline("summarization", model="t5-small")

def analyze_text(text: str):
    # 감성 분석
    try:
        sentiment_res = _sentiment(text[:512])[0]  # 긴 본문은 자르기
        sentiment = sentiment_res["label"]
    except Exception:
        sentiment = "unknown"

    # 요약
    try:
        summary_res = _summarizer(text[:1000], max_length=50, min_length=10, do_sample=False)
        summary = summary_res[0]["summary_text"]
    except Exception:
        summary = text[:150] + "..."

    return sentiment, summary

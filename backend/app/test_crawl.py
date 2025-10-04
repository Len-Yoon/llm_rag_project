# backend/app/test_crawl.py
import sys
from crawler_google import NaverNewsCrawler

q = sys.argv[1] if len(sys.argv) > 1 else "미국 경제"
days = int(sys.argv[2]) if len(sys.argv) > 2 else 3
pages = int(sys.argv[3]) if len(sys.argv) > 3 else 1
headless = (sys.argv[4].lower() != "false") if len(sys.argv) > 4 else True

cr = NaverNewsCrawler(headless=headless, max_pages=pages)
try:
    links = cr.search_links(q, days=days, max_pages=pages)
    print(f"수집 링크 개수: {len(links)}")
    for i, (u, t) in enumerate(links[:10], 1):
        print(f"{i:02d}. {t or '-'} | {u}")
    if links:
        print("\n=== 샘플 본문 ===")
        print(cr.extract_article_text(links[0][0])[:500])
finally:
    cr.close()

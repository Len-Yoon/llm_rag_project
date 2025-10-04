# backend/app/crawler_google.py
from __future__ import annotations

import html
import random
import re
import time
import xml.etree.ElementTree as ET
from typing import List, Tuple
from urllib.parse import urlparse

import requests
from requests import Session
from requests.adapters import HTTPAdapter, Retry

import trafilatura

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import ui as selenium_ui
from webdriver_manager.chrome import ChromeDriverManager

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)

def _sleep(a: float = 0.25, b: float = 0.6) -> None:
    time.sleep(random.uniform(a, b))

def _headers() -> dict:
    return {
        "User-Agent": UA,
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://news.google.com/",
    }

def _session() -> Session:
    s = requests.Session()
    retries = Retry(
        total=2, connect=2, read=2, backoff_factor=0.3,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    s.headers.update(_headers())
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

def _new_driver(headless: bool):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    # 가벼운 렌더링 & 안정화
    opts.add_argument("--disable-gpu")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.add_argument("--disable-remote-fonts")
    opts.add_argument("--mute-audio")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1360,2400")
    opts.add_argument("--lang=ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-background-networking")
    opts.add_argument("--metrics-recording-only")
    opts.add_argument("--disable-sync")
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(f"user-agent={UA}")
    # 리다이렉트 있는 경우에 대비해 eager (none은 너무 일찍 끊길 수 있음)
    opts.page_load_strategy = "eager"

    try:
        drv = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    except Exception:
        drv = webdriver.Chrome(options=opts)

    try:
        drv.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
    except Exception:
        pass

    drv.set_page_load_timeout(30)
    drv.implicitly_wait(1)
    return drv

# -------------------- Google News: RSS --------------------
def _google_news_rss_links(q: str, pages: int, dbg: bool=False) -> List[Tuple[str, str]]:
    max_items = max(1, pages) * 10
    url = "https://news.google.com/rss/search"
    params = {"q": q, "hl": "ko", "gl": "KR", "ceid": "KR:ko"}
    sess = _session()
    links: List[Tuple[str, str]] = []
    try:
        r = sess.get(url, params=params, timeout=10)
        if dbg: print(f"[crawler][gn-rss][{r.status_code}] {r.url}")
        r.raise_for_status()
        root = ET.fromstring(r.content)
        for item in root.findall(".//item"):
            title = html.unescape((item.findtext("title") or "").strip())
            link = html.unescape((item.findtext("link") or "").strip())
            if link and title:
                links.append((link, title))
            if len(links) >= max_items:
                break
        if dbg: print(f"[crawler][gn-rss] found={len(links)}")
    except Exception as e:
        if dbg: print(f"[crawler][gn-rss][error] msg={e}")
    # dedup
    seen = set()
    uniq: List[Tuple[str, str]] = []
    for u, t in links:
        if u not in seen:
            uniq.append((u, t))
            seen.add(u)
    return uniq

# -------------------- Google News: HTML --------------------
_GOOGLE_LINK_PAT = re.compile(
    r'<a\s+href="(?P<href>https?://[^"]+)"[^>]*>(?:<h3[^>]*>(?P<title_h3>.*?)</h3>|<div[^>]*>(?P<title_div>.*?)</div>)',
    re.I | re.S,
)
_TAG_STRIP = re.compile(r"<[^>]+>")

def _clean_html(t: str) -> str:
    return _TAG_STRIP.sub("", t or "").strip()

def _google_news_links(q: str, days: int, pages: int, dbg: bool=False) -> List[Tuple[str, str]]:
    links: List[Tuple[str, str]] = []
    base = "https://www.google.com/search"
    sess = _session()
    if days <= 1:  tbs = "qdr:d1"
    elif days <= 7: tbs = "qdr:w1"
    else:          tbs = "qdr:m1"

    for page in range(pages):
        params = {"tbm": "nws", "q": q, "start": page * 10, "hl": "ko", "tbs": tbs}
        try:
            r = sess.get(base, params=params, timeout=10)
            if dbg: print(f"[crawler][google][{r.status_code}] {r.url}")
            r.raise_for_status()
            found = []
            for m in _GOOGLE_LINK_PAT.finditer(r.text):
                href = m.group("href")
                title = _clean_html(m.group("title_h3") or m.group("title_div") or "")
                if href and title:
                    found.append((href, title))
            if dbg: print(f"[crawler][google] page={page+1} found={len(found)}")
            links.extend(found)
        except requests.RequestException as e:
            if dbg:
                body = getattr(e.response, "text", "")[:200] if getattr(e, "response", None) else ""
                print(f"[crawler][google][error] params={params} msg={e} sample={body!r}")
        _sleep()
    # dedup
    seen = set()
    uniq: List[Tuple[str, str]] = []
    for u, t in links:
        if u not in seen:
            uniq.append((u, t))
            seen.add(u)
    return uniq

# -------------------- 본문 추출 --------------------
def _extract_via_trafilatura(url: str, timeout: float = 12.0) -> tuple[str, str]:
    """
    trafilatura로 추출.
    - news.google.com/rss/articles/... 같은 중간 링크면 -> 최종 리다이렉트 URL을 따라가 재시도
    return: (텍스트, 최종_URL)
    """
    s = _session()
    r = s.get(url, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    final_url = r.url  # 리다이렉트 반영된 URL
    txt = trafilatura.extract(
        r.content,
        include_comments=False,
        favor_recall=True,
        target_language="ko",
        no_fallback=False,
        url=final_url,
    ) or ""
    txt = txt.strip()

    # 리다이렉트 후에도 빈 경우: 최종 URL로 재요청해 다시 시도
    if len(txt) < 120 and final_url != url:
        r2 = s.get(final_url, timeout=timeout, allow_redirects=True)
        r2.raise_for_status()
        txt2 = trafilatura.extract(
            r2.content,
            include_comments=False,
            favor_recall=True,
            target_language="ko",
            no_fallback=False,
            url=final_url,
        ) or ""
        txt2 = txt2.strip()
        if len(txt2) > len(txt):
            txt = txt2

    return txt, final_url

class NaverNewsCrawler:
    """검색: Google News RSS → (실패시) Google News HTML
       본문: trafilatura(HTTP) 우선 → 실패 시 Selenium 폴백(+리다이렉트 완료 대기)
    """
    def __init__(self, headless: bool = True, max_pages: int = 3, debug: bool = False):
        self.max_pages = max_pages
        self.debug = debug
        self.headless = headless
        self.driver = None

    def search_links(self, q: str, days: int = 3, max_pages: int | None = None) -> List[Tuple[str, str]]:
        pages = max_pages or self.max_pages
        rss = _google_news_rss_links(q, pages, dbg=self.debug)
        if self.debug: print(f"[crawler][gn-rss] total={len(rss)}")
        if rss: return rss
        google_links = _google_news_links(q, days, pages, dbg=self.debug)
        if self.debug: print(f"[crawler][google-news] total={len(google_links)}")
        return google_links

    def extract_article_text(self, url: str) -> str:
        # 1) trafilatura 먼저
        try:
            text, final_url = _extract_via_trafilatura(url)
            if self.debug:
                print(f"[extract][trafilatura] {len(text)} chars | {final_url}")
            if len(text) >= 160:
                return text
            # trafilatura가 짧으면 Selenium 폴백으로 이어감
            url = final_url
        except Exception as e:
            if self.debug:
                print(f"[extract][trafilatura][error] {e}")

        # 2) Selenium 폴백
        if self.driver is None:
            self.driver = _new_driver(headless=self.headless)

        self.driver.get(url)

        # news.google.com 중간 URL이면 리다이렉트 완료까지 잠깐 대기
        try:
            host = urlparse(url).netloc
            if "news.google.com" in host:
                selenium_ui.WebDriverWait(self.driver, timeout=3.0).until(
                    lambda d: "news.google.com" not in urlparse(d.current_url).netloc
                )
        except Exception:
            pass

        # 너무 무겁게 로드되기 전에 중단
        _sleep(0.6, 1.2)
        try:
            self.driver.execute_script("window.stop();")
        except Exception:
            pass

        try:
            selenium_ui.WebDriverWait(self.driver, timeout=2.0).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception:
            pass

        selector_candidates = [
            "#dic_area", "article", "div#newsct",
            "div.article_body", "div.news_body",
            "div#articeBody", "div#articleBody",
            "div#news_body_area", "div#contentArea",
        ]
        for sel in selector_candidates:
            try:
                text = self.driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                if len(text) > 160:
                    if self.debug:
                        print(f"[extract][selenium] {len(text)} chars | sel={sel}")
                    return text
            except Exception:
                continue
        try:
            text = self.driver.find_element(By.TAG_NAME, "body").text.strip()
            if self.debug:
                print(f"[extract][selenium][body] {len(text)} chars")
            return text
        except Exception:
            return ""

    def close(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

    def __enter__(self):  # type: ignore[override]
        return self

    def __exit__(self, exc_type, exc, tb):  # type: ignore[override]
        self.close()

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from discord_webhook import DiscordWebhook
import openai
import os
import time
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 키 로드
openai.api_key = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_nate_top_articles(limit=5):
    url = "https://news.nate.com/rank/?mid=n1000"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")

    article_blocks = soup.select("div.postRankSubjectList ul li")[:limit]
    articles = []

    for i, block in enumerate(article_blocks, 1):
        a_tag = block.select_one("a")
        if not a_tag:
            continue

        title = a_tag.get_text(strip=True)
        link = "https:" + a_tag["href"]
        content = fetch_article_body(link)

        print(f"\n[📰 기사 {i}] {title}")
        print(f"URL: {link}")
        print(f"본문 길이: {len(content)}자")

        if not content:
            print("⛔ 본문 없음, 스킵")
            continue

        summary = summarize_with_gpt(title, content)
        articles.append({
            "title": title,
            "link": link,
            "summary": summary
        })

        time.sleep(1.5)  # GPT API 요청 간격 제한 회피용

    return articles

def fetch_article_body(link):
    try:
        res = requests.get(link, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        content_div = soup.select_one("div.articleCont, div.article")
        if not content_div:
            return ""
        paragraphs = content_div.stripped_strings
        text = " ".join(paragraphs)
        return text.strip()
    except Exception as e:
        print(f"❌ 본문 크롤링 실패: {e}")
        return ""

def summarize_with_gpt(title, text):
    prompt = f"""다음은 뉴스 기사입니다.

[제목]
{title}

[내용]
{text}

위 기사를 사람이 빠르게 말했을 때 약 20초 분량으로 자연스럽게 요약해줘. 
가능하면 서민이나 독자들에게 끼칠 영향이나 조심해야 할 점, 제안도 포함해줘. 
친절하고 뉴스 앵커 말투처럼 써줘."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "너는 요약 전문 기자야."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )
        result = response['choices'][0]['message']['content'].strip()
        print("✅ GPT 응답 수신 완료")
        print(result)
        return result
    except Exception as e:
        print(f"❌ GPT 오류 발생: {e}")
        return f"⚠️ GPT 요약 실패: {e}"

def send_to_discord(articles):
    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M 기준 📢")
    message = f"📰 **실시간 네이트 뉴스 TOP 5 요약** ({now})\n\n"

    if not articles:
        message += "❗ 기사 요약에 실패했습니다."

    for i, art in enumerate(articles, 1):
        message += f"**[{i}위] {art['title']}**\n"
        message += f"{art['link']}\n"
        message += f"📝 {art['summary']}\n\n"

    webhook = DiscordWebhook(url=WEBHOOK_URL, content=message[:1900])
    webhook.execute()

if __name__ == "__main__":
    print("📡 Nate 뉴스 수집 시작...")
    top_articles = get_nate_top_articles()
    print(f"✅ 총 {len(top_articles)}개 기사 요약 완료")
    print("🚀 디스코드 전송 시작...")
    send_to_discord(top_articles)
    print("✅ 완료")

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from discord_webhook import DiscordWebhook
import os

def get_top_naver_news():
    url = "https://news.naver.com/main/ranking/popularDay.naver"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    articles = soup.select(".rankingnews_box a")[:3]
    summaries = []

    for i, article in enumerate(articles, 1):
        title = article.get_text(strip=True)
        link = article['href']
        summaries.append(f"**[{i}위] {title}**\n{link}")

    return summaries

def send_to_discord(messages):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M 기준 📢")
    content = f"📰 **오늘의 인기 뉴스 TOP 3** ({now})\n\n" + "\n\n".join(messages)
    webhook = DiscordWebhook(url=webhook_url, content=content)
    webhook.execute()

if __name__ == "__main__":
    news = get_top_naver_news()
    send_to_discord(news)

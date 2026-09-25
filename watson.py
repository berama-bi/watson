import requests
import json
import time

SEARCH_TERMS = [
    "wingo",
    "swisscom",
    "coop mobile",
    "migros mobile",
    "spusu",
    "yallo",
    "sunrise",
    "salt",
    "quickline",
    "chmobile",
    "gomo"
]

SEARCH_URL = "https://www.watson.ch/api/2.0/articles/search"
DISCUSSION_URL = "https://www.watson.ch/api/2.0/discussions"

session = requests.Session()
session.trust_env = False

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_all_search_results(term):
    page = 1
    articles = []

    while True:

        params = {
            "resource": "search",
            "q": term,
            "page": page,
            "period": "total",
            "limit": 40
        }

        try:

            response = session.get(
                SEARCH_URL,
                params=params,
                headers=HEADERS,
                timeout=30
            )

            print(
                f"[SEARCH] {term} | "
                f"Page {page} | "
                f"HTTP {response.status_code}"
            )

            if response.status_code != 200:
                break

            data = response.json()

        except Exception as e:
            print(f"[ERROR] Search {term}: {e}")
            break

        page_articles = data.get("data", [])

        if not page_articles:
            break

        articles.extend(page_articles)

        print(
            f"Articles this page: {len(page_articles)} | "
            f"Total: {len(articles)}"
        )

        if len(page_articles) < 40:
            break

        page += 1

        time.sleep(0.5)

    return articles


def get_comments(story_id):

    url = f"{DISCUSSION_URL}/{story_id}"

    try:

        response = session.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        print(
            f"[COMMENTS] {story_id} | "
            f"HTTP {response.status_code}"
        )

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as e:

        print(
            f"[COMMENTS ERROR] {story_id}: {e}"
        )

        return None


output = {
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "searches": []
}

for term in SEARCH_TERMS:

    print("\n" + "=" * 80)
    print("SEARCH:", term)
    print("=" * 80)

    articles = get_all_search_results(term)

    search_data = {
        "search_term": term,
        "article_count": len(articles),
        "articles": []
    }

    for idx, article in enumerate(articles, start=1):

        story_id = article.get("story_id")

        print(
            f"[ARTICLE] "
            f"{idx}/{len(articles)} "
            f"ID={story_id}"
        )

        discussion = None
        comment_count = 0

        if story_id:

            discussion = get_comments(story_id)

            if discussion:

                comment_count = (
                    discussion
                    .get("data", {})
                    .get("comments_count", 0)
                )

        entry = {
            "story_id": story_id,
            "title": article.get("title"),
            "url": article.get("full_url"),
            "published_at": article.get("published_at"),
            "comment_count": comment_count,
            "article": article,
            "discussion": discussion
        }

        search_data["articles"].append(entry)

        time.sleep(0.2)

    output["searches"].append(search_data)

with open(
    "watson_export.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=2
    )

print("\n" + "=" * 80)
print("DONE")
print("Saved: watson_export.json")
print("=" * 80)

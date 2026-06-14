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

            r = session.get(
                SEARCH_URL,
                params=params,
                headers=HEADERS,
                timeout=30
            )

            print(
                f"[SEARCH] {term} "
                f"Seite {page} "
                f"HTTP {r.status_code}"
            )

            if r.status_code != 200:
                break

            data = r.json()

        except Exception as e:

            print(
                f"Fehler Suche {term}: {e}"
            )

            break

        page_articles = data.get(
            "data",
            []
        )

        if not page_articles:
            break

        articles.extend(
            page_articles
        )

        print(
            f"  Artikel auf Seite: "
            f"{len(page_articles)} "
            f"| Total bisher: "
            f"{len(articles)}"
        )

        if len(page_articles) < 40:
            break

        page += 1

        time.sleep(0.5)

    return articles


def get_comments(story_id):

    url = (
        f"{DISCUSSION_URL}/{story_id}"
    )

    try:

        r = session.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        print(
            f"[COMMENTS] "
            f"{story_id} "
            f"HTTP {r.status_code}"
        )

        if r.status_code != 200:
            return None

        return r.json()

    except Exception as e:

        print(
            f"[COMMENTS] Fehler "
            f"{story_id}: {e}"
        )

        return None


output = {
    "generated_at": time.strftime(
        "%Y-%m-%d %H:%M:%S"
    ),
    "searches": []
}

for term in SEARCH_TERMS:

    print()
    print("=" * 60)
    print("SUCHE:", term)
    print("=" * 60)

    articles = get_all_search_results(
        term
    )

    search_data = {
        "search_term": term,
        "article_count": len(articles),
        "articles": []
    }

    for idx, article in enumerate(
        articles,
        start=1
    ):

        story_id = article.get(
            "story_id"
        )

        article_url = article.get(
            "full_url"
        )

        print()
        print(
            f"[ARTICLE] "
            f"{idx}/{len(articles)} "
            f"ID={story_id}"
        )

        discussion = None
        comment_count = 0

        if story_id:

            discussion = get_comments(
                story_id
            )

            if discussion:

                comment_count = (
                    discussion
                    .get("data", {})
                    .get("comments_count", 0)
                )

        search_data["articles"].append(
            {
                "story_id": story_id,
                "url": article_url,
                "title": article.get("title"),
                "published_at": article.get(
                    "published_at"
                ),
                "article": article,
                "comment_count": comment_count,
                "discussion": discussion
            }
        )

        time.sleep(0.2)

    output["searches"].append(
        search_data
    )

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

print()
print("=" * 60)
print("FERTIG")
print("Datei gespeichert:")
print("  watson_export.json")
print("=" * 60)
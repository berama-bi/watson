import json
import time
import requests

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

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

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.trust_env = False

adapter = requests.adapters.HTTPAdapter(
    pool_connections=50,
    pool_maxsize=50
)

session.mount("https://", adapter)
session.mount("http://", adapter)


def get_all_search_results(term):

    page = 1
    articles = []

    while True:

        params = {
            "resource": "search",
            "q": term,
            "page": page,
            "period": "total",
            "limit": 5
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

            print(
                f"[SEARCH ERROR] "
                f"{term}: {e}"
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
            f"Found {len(page_articles)} "
            f"articles | "
            f"Total {len(articles)}"
        )

        if len(page_articles) < 40:
            break

        page += 1

    return articles


def get_comments(story_id):

    try:

        url = (
            f"{DISCUSSION_URL}/{story_id}"
        )

        response = session.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as e:

        print(
            f"[COMMENT ERROR] "
            f"{story_id}: {e}"
        )

        return None


def process_article(article):

    story_id = article.get(
        "story_id"
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
                .get(
                    "comments_count",
                    0
                )
            )

    return {
        "story_id": story_id,
        "url": article.get(
            "full_url"
        ),
        "title": article.get(
            "title"
        ),
        "published_at": article.get(
            "published_at"
        ),
        "comment_count": comment_count,
        "article": article,
        "discussion": discussion
    }


output = {
    "generated_at": time.strftime(
        "%Y-%m-%d %H:%M:%S"
    ),
    "searches": []
}


for term in SEARCH_TERMS:

    print()
    print("=" * 80)
    print("SEARCH:", term)
    print("=" * 80)

    articles = get_all_search_results(
        term
    )

    search_data = {
        "search_term": term,
        "article_count": len(
            articles
        ),
        "articles": []
    }

    total = len(articles)

    with ThreadPoolExecutor(
        max_workers=25
    ) as executor:

        futures = {
            executor.submit(
                process_article,
                article
            ): article
            for article in articles
        }

        done = 0

        for future in as_completed(
            futures
        ):

            try:

                result = future.result()

                search_data[
                    "articles"
                ].append(
                    result
                )

            except Exception as e:

                print(
                    f"[PROCESS ERROR] {e}"
                )

            done += 1

            if done % 25 == 0:

                print(
                    f"{term}: "
                    f"{done}/{total}"
                )

    output[
        "searches"
    ].append(
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
print("=" * 80)
print("DONE")
print(
    "Saved: watson_export.json"
)
print("=" * 80)

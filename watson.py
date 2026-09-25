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

MAX_PAGES = 20
LIMIT = 50

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

# ---------------------------------------------------------
# SEARCH ARTICLES
# ---------------------------------------------------------

def get_all_search_results(term):

    page = 1
    articles = []

    while page <= MAX_PAGES:

        params = {
            "resource": "search",
            "q": term,
            "page": page,
            "period": "total",
            "limit": LIMIT
        }

        try:

            response = session.get(
                SEARCH_URL,
                params=params,
                headers=HEADERS,
                timeout=15
            )

            print(
                f"[SEARCH] {term} | "
                f"Page {page}/{MAX_PAGES} | "
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
            f"Found {len(page_articles)} articles | "
            f"Total {len(articles)}"
        )

        if len(page_articles) < LIMIT:
            break

        page += 1

    return articles


# ---------------------------------------------------------
# GET COMMENTS
# ---------------------------------------------------------

def get_comments(story_id):

    try:

        url = f"{DISCUSSION_URL}/{story_id}"

        response = session.get(
            url,
            headers=HEADERS,
            timeout=15
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


# ---------------------------------------------------------
# PROCESS ARTICLE
# ---------------------------------------------------------

def process_article(article, search_term):

    story_id = article.get("story_id")

    rows = []

    news_row = {
        "record_type": "news",
        "search_term": search_term,
        "story_id": story_id,
        "title": article.get("title"),
        "lead": article.get("lead"),
        "url": article.get("full_url"),
        "published_at": article.get("published_at"),
        "comment_count": 0
    }

    rows.append(news_row)

    if not story_id:
        return rows

    discussion = get_comments(story_id)

    if not discussion:
        return rows

    data = discussion.get(
        "data",
        {}
    )

    news_row["comment_count"] = data.get(
        "comments_count",
        0
    )

    for comment in data.get(
        "comments",
        []
    ):

        rows.append({
            "record_type": "comment",
            "search_term": search_term,
            "story_id": story_id,
            "comment_id": comment.get("id"),
            "created_at": comment.get("created_at"),
            "author": (
                comment.get("user", {})
                .get("username")
            ),
            "text": (
                comment.get("text")
                or comment.get("content")
            )
        })

    return rows


# ---------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------

output = []

# ---------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------

for term in SEARCH_TERMS:

    print()
    print("=" * 80)
    print("SEARCH:", term)
    print("=" * 80)

    articles = get_all_search_results(
        term
    )

    total = len(articles)

    print(
        f"Total articles found: {total}"
    )

    with ThreadPoolExecutor(
        max_workers=25
    ) as executor:

        futures = [
            executor.submit(
                process_article,
                article,
                term
            )
            for article in articles
        ]

        done = 0

        for future in as_completed(
            futures
        ):

            try:

                rows = future.result()

                output.extend(rows)

            except Exception as e:

                print(
                    f"[PROCESS ERROR] {e}"
                )

            done += 1

            if done % 25 == 0 or done == total:

                print(
                    f"{term}: "
                    f"{done}/{total}"
                )

# ---------------------------------------------------------
# SAVE JSON
# ---------------------------------------------------------

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

news_count = sum(
    1 for x in output
    if x.get("record_type") == "news"
)

comment_count = sum(
    1 for x in output
    if x.get("record_type") == "comment"
)

print()
print("=" * 80)
print(f"News rows    : {news_count}")
print(f"Comment rows : {comment_count}")
print("Saved        : watson_export.json")
print("=" * 80)

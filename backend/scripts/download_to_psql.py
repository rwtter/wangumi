import time
import json
import argparse
import psycopg2 as psycopg
from psycopg2.extras import Json
import requests

# ============ 配置部分 ============
API_URL = "https://graphql.anilist.co"
PER_PAGE = 50
SLEEP_SEC = 0.5

# PostgreSQL 连接配置
PG_CONFIG = {
    "host": "dpg-d3spgmq4d50c73eicoqg-a.singapore-postgres.render.com",
    "port": "5432",
    "dbname": "wangumi_db",
    "user": "gumi",
    "password": "oflWEdPlFvd6jWE8nZZ3yg1862FTE5kZ",
    "sslmode": "require"
}

# GraphQL 查询
QUERY = """
query (
  $page: Int,
  $perPage: Int,
  $type: MediaType,
  $beforeDate: FuzzyDateInt,
  $sort: [MediaSort]
) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { currentPage hasNextPage }
    media(
      type: $type,
      sort: $sort,
      startDate_lesser: $beforeDate
    ) {
      id
      idMal
      title { romaji english native }
      startDate { year month day }
      format
      episodes
      status
      season
      seasonYear
      averageScore
      popularity
      genres
      coverImage {
        extraLarge
        large
        medium
        color
      }
      studios(isMain: true) { nodes { id name } }
      siteUrl
      updatedAt
    }
  }
}
"""

def get_conn():
    return psycopg.connect(**PG_CONFIG)

def fetch_page(page, per_page, before_date, sort):
    variables = {
        "page": page,
        "perPage": per_page,
        "type": "ANIME",
        "beforeDate": before_date,
        "sort": sort,
    }
    resp = requests.post(API_URL, json={"query": QUERY, "variables": variables})
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
    data = resp.json()["data"]["Page"]
    return data["media"], data["pageInfo"]["hasNextPage"]

def upsert_items(conn, items):
    from datetime import date, datetime

    with conn.cursor() as cur:
        for m in items:
            nodes = m.get("studios", {}).get("nodes", [])
            if nodes:
                s_id = nodes[0].get("id")
                s_name = nodes[0].get("name")
            else:
                s_id = None
                s_name = None

# 将 Unix 时间戳转换成 datetime
            updated_at_ts = m.get("updatedAt")
            updated_at = datetime.fromtimestamp(updated_at_ts) if updated_at_ts else None


            start_date = m.get("startDate") or {}
            release_date = None
            try:
                year = start_date.get("year")
                if year:
                    month = start_date.get("month") or 1
                    day = start_date.get("day") or 1
                    release_date = date(int(year), int(month), int(day))
            except Exception:
                release_date = None

            cur.execute(
                """
                INSERT INTO wangumi_app_anime (
                    id, title, title_cn, description, release_date, airtime,
                    cover_image, cover_url, uid, rating, popularity, wishes, collections,
                    doing, on_hold, dropped, status, total_episodes, platform, is_series, nsfw, is_banned,
                    created_at, updated_at, genres
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    title_cn = EXCLUDED.title_cn,
                    description = EXCLUDED.description,
                    release_date = EXCLUDED.release_date,
                    airtime = EXCLUDED.airtime,
                    cover_image = EXCLUDED.cover_image,
                    cover_url = EXCLUDED.cover_url,
                    uid = EXCLUDED.uid,
                    rating = EXCLUDED.rating,
                    popularity = EXCLUDED.popularity,
                    wishes = EXCLUDED.wishes,
                    collections = EXCLUDED.collections,
                    doing = EXCLUDED.doing,
                    on_hold = EXCLUDED.on_hold,
                    dropped = EXCLUDED.dropped,
                    status = EXCLUDED.status,
                    total_episodes = EXCLUDED.total_episodes,
                    platform = EXCLUDED.platform,
                    is_series = EXCLUDED.is_series,
                    nsfw = EXCLUDED.nsfw,
                    is_banned = EXCLUDED.is_banned,
                    updated_at = EXCLUDED.updated_at,
                    genres = EXCLUDED.genres
                    """,
                (
                    m["id"],
                    (m.get("title") or {}).get("romaji") or "未知标题",
                    (m.get("title") or {}).get("native")
                    or (m.get("title") or {}).get("english")
                    or "",
                    m.get("description") or "",
                    release_date,
                    "",   # airtime
                    "",  # cover_image stored only for local uploads
                    (m.get("coverImage") or {}).get("large")
                    or (m.get("coverImage") or {}).get("extraLarge")
                    or (m.get("coverImage") or {}).get("medium")
                    or "",
                    str(m.get("idMal", "")),  # uid
                    (m.get("averageScore") or 0) / 10.0,  # rating (转换评分)
                    m.get("popularity") or 0,
                    0,  # wishes
                    0,  # collections
                    0,  # doing
                    0,  # on_hold
                    0,  # dropped
                    m.get("status") or "",
                    m.get("episodes") or 0,
                    "",  # platform
                    True if m.get("format") == "TV" else False,  # is_series
                    False,  # nsfw
                    False,  # is_banned
                    updated_at,  # created_at
                    updated_at,  # updated_at
                    Json(m.get("genres") or []),
                )
            )
    conn.commit()


def _before_date_from_year(year: int) -> int:
    return year * 10000 + 101


def main():
    parser = argparse.ArgumentParser(description="抓取指定年份之前的热门番剧并写入")
    parser.add_argument("--before-year", type=int, default=2025, help="抓取该年份之前的数据，默认 2025")
    parser.add_argument("--limit", type=int, default=1, help="抓取总条数上限，默认 30")
    parser.add_argument(
        "--sort",
        type=str,
        default="POPULARITY_DESC",
        choices=["POPULARITY_DESC", "TRENDING_DESC", "SCORE_DESC"],
        help="默认 POPULARITY_DESC"
    )
    args = parser.parse_args()

    target_total = max(0, args.limit)
    if target_total == 0:
        print("limit 为 0，无需抓取。")
        return

    before_date = _before_date_from_year(args.before_year)
    sort_arg = [args.sort]

    conn = get_conn()
    page = 1
    fetched = 0
    try:
        while True:
            remaining = target_total - fetched
            if remaining <= 0:
                break
            per_page = min(PER_PAGE, remaining)
            media, has_next = fetch_page(page, per_page, before_date, sort_arg)
            if not media:
                break
            upsert_items(conn, media)
            fetched += len(media)
            print(f"Page {page}: +{len(media)} items (total {fetched}/{target_total})")
            if not has_next:
                break
            page += 1
            time.sleep(SLEEP_SEC)
    finally:
        conn.close()

    print("Finished!")

if __name__ == "__main__":
    main()

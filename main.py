import os
import requests
from datetime import datetime, timezone

API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN", "")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "GitRank"
}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


# ---------------- API ----------------

def get(url, params=None):
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=10
        )

        if r.status_code == 200:
            return r.json()

        if r.status_code == 403:
            print("❌ GitHub API rate limit/permission error.")
        elif r.status_code == 404:
            print("❌ User not found.")
        else:
            print(f"❌ API error: {r.status_code}")

    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")

    return None


def date(text):
    if not text:
        return None

    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        )
    except ValueError:
        return None


def age(text):
    d = date(text)

    if not d:
        return None

    return (datetime.now(timezone.utc) - d).days


# ---------------- GitHub ----------------

def profile(username):
    return get(f"{API}/users/{username}")


def repos(username):
    result = []
    page = 1

    while True:
        data = get(
            f"{API}/users/{username}/repos",
            {
                "per_page": 100,
                "page": page,
                "sort": "updated"
            }
        )

        if data is None:
            return None

        if not data:
            break

        result.extend(data)

        if len(data) < 100:
            break

        page += 1

    return result


# ---------------- Analysis ----------------

def analyze(rs):
    stats = {
        "stars": 0,
        "forks": 0,
        "issues": 0,
        "active30": 0,
        "active180": 0,
        "original": 0,
        "archived": 0,
        "stale": 0,
        "languages": {}
    }

    for r in rs:
        stats["stars"] += r.get("stargazers_count", 0)
        stats["forks"] += r.get("forks_count", 0)
        stats["issues"] += r.get("open_issues_count", 0)

        if not r.get("fork"):
            stats["original"] += 1

        if r.get("archived"):
            stats["archived"] += 1

        days = age(r.get("pushed_at"))

        if days is not None:
            if days <= 30:
                stats["active30"] += 1

            if days <= 180:
                stats["active180"] += 1

            if days > 180 and not r.get("archived"):
                stats["stale"] += 1

        lang = r.get("language")

        if lang:
            stats["languages"][lang] = (
                stats["languages"].get(lang, 0) + 1
            )

    return stats


def repo_score(r):
    score = 0

    score += min(r.get("stargazers_count", 0) * 2, 30)
    score += min(r.get("forks_count", 0) * 3, 20)

    if r.get("description"):
        score += 10

    if r.get("topics"):
        score += min(len(r["topics"]) * 2, 10)

    if r.get("license"):
        score += 5

    if r.get("homepage"):
        score += 5

    if not r.get("fork"):
        score += 10

    days = age(r.get("pushed_at"))

    if days is not None:
        if days <= 7:
            score += 10
        elif days <= 30:
            score += 8
        elif days <= 180:
            score += 4

    if r.get("archived"):
        score -= 5

    return max(0, min(score, 100))


def completeness(p):
    fields = [
        p.get("name"),
        p.get("bio"),
        p.get("location"),
        p.get("blog"),
        p.get("company")
    ]

    return round(
        sum(bool(x) for x in fields)
        / len(fields) * 100
    )


def portfolio_score(p, s):
    total = len(repos_cache)

    if not total:
        return 0

    activity = min(
        s["active30"] / total * 100,
        100
    )

    original = (
        s["original"] / total * 100
    )

    long_activity = min(
        s["active180"] * 5,
        100
    )

    return round(
        completeness(p) * .20 +
        activity * .20 +
        original * .20 +
        long_activity * .20 +
        min(s["stars"], 100) * .10 +
        min(p.get("followers", 0), 100) * .10,
        1
    )


# ---------------- Display ----------------

def show(p, rs, s):
    print("\n" + "=" * 50)
    print("             GITRANK v1.1")
    print("=" * 50)

    print(f"\n👤 {p.get('name') or p['login']}")
    print(f"Bio: {p.get('bio') or 'None'}")
    print(f"Followers: {p.get('followers', 0)}")
    print(f"Repositories: {len(rs)}")
    print(f"Profile: {completeness(p)}%")

    print("\n📊 STATISTICS")
    print(f"⭐ Stars: {s['stars']}")
    print(f"🍴 Forks: {s['forks']}")
    print(f"🐛 Issues: {s['issues']}")
    print(f"🔥 Active 30d: {s['active30']}")
    print(f"📅 Active 180d: {s['active180']}")
    print(f"💡 Original: {s['original']}")
    print(f"💤 Stale: {s['stale']}")

    print("\n💻 LANGUAGES")

    for lang, count in sorted(
        s["languages"].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"  {lang}: {count}")

    print("\n🏆 TOP PROJECTS")

    for i, r in enumerate(
        sorted(
            rs,
            key=repo_score,
            reverse=True
        )[:5],
        1
    ):
        print(
            f"{i}. {r['name']} "
            f"({repo_score(r)}/100) "
            f"⭐{r.get('stargazers_count', 0)}"
        )

    best = max(rs, key=repo_score) if rs else None

    if best:
        print("\n🥇 BEST PROJECT")
        print(best["name"])
        print(best.get("html_url", ""))

    score = portfolio_score(p, s)

    print("\n🎯 GITRANK SCORE")
    print(f"{score}/100")

    xp = (
        len(rs) * 25 +
        s["original"] * 15 +
        s["stars"] * 10 +
        s["forks"] * 15 +
        s["active30"] * 30
    )

    level = xp // 250 + 1

    print("\n🎮 DEVELOPER LEVEL")
    print(f"Level {level} • {xp} XP")


# ---------------- Search ----------------

def search(rs):
    q = input(
        "\nSearch repository: "
    ).lower().strip()

    found = [
        r for r in rs
        if q in r["name"].lower()
    ]

    if not found:
        print("No results.")
        return

    for r in sorted(
        found,
        key=repo_score,
        reverse=True
    ):
        print(
            f"{r['name']} "
            f"| {repo_score(r)}/100 "
            f"| ⭐{r.get('stargazers_count', 0)}"
        )


# ---------------- Main ----------------

repos_cache = []


def main():
    global repos_cache

    username = input(
        "GitHub username: "
    ).strip()

    if not username:
        print("❌ Username required.")
        return

    print("\n🔎 Analyzing GitHub...")

    p = profile(username)

    if not p:
        return

    repos_cache = repos(username)

    if repos_cache is None:
        return

    s = analyze(repos_cache)

    show(
        p,
        repos_cache,
        s
    )

    while True:
        choice = input(
            "\nSearch repositories? (y/n): "
        ).lower().strip()

        if choice == "y":
            search(repos_cache)
        else:
            break

    print("\n✅ GitRank analysis complete.")


if __name__ == "__main__":
    main()
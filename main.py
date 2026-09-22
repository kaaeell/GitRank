import os
import requests
from datetime import datetime, timezone

API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN", "")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "GitRank",
    "X-GitHub-Api-Version": "2022-11-28"
}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


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

        if r.status_code == 404:
            print("❌ GitHub user not found.")

        elif r.status_code == 403:
            print("❌ GitHub API rate limit or permission error.")
            print(f"   {r.json().get('message', 'Unknown error')}")

        else:
            print(f"❌ API error: {r.status_code}")

    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")

    return None


def days_ago(date_text):
    if not date_text:
        return None

    try:
        date = datetime.fromisoformat(
            date_text.replace("Z", "+00:00")
        )
        return (datetime.now(timezone.utc) - date).days
    except (ValueError, TypeError):
        return None


def get_profile(username):
    return get(f"{API}/users/{username}")


def get_repos(username):
    repos = []
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

        repos.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repos


def analyze(repos):
    stats = {
        "stars": 0,
        "forks": 0,
        "issues": 0,
        "active30": 0,
        "active180": 0,
        "original": 0,
        "stale": 0,
        "archived": 0,
        "languages": {}
    }

    for repo in repos:
        stats["stars"] += repo.get("stargazers_count", 0)
        stats["forks"] += repo.get("forks_count", 0)

        # GitHub counts open PRs in open_issues_count too.
        stats["issues"] += repo.get("open_issues_count", 0)

        if not repo.get("fork"):
            stats["original"] += 1

        if repo.get("archived"):
            stats["archived"] += 1

        days = days_ago(repo.get("pushed_at"))

        if days is not None:
            if days <= 30:
                stats["active30"] += 1

            if days <= 180:
                stats["active180"] += 1

            if days > 180 and not repo.get("archived"):
                stats["stale"] += 1

        language = repo.get("language")

        if language:
            stats["languages"][language] = (
                stats["languages"].get(language, 0) + 1
            )

    return stats


def repo_score(repo):
    score = 0

    score += min(repo.get("stargazers_count", 0) * 2, 30)
    score += min(repo.get("forks_count", 0) * 3, 20)

    if repo.get("description"):
        score += 10

    topics = repo.get("topics", [])

    if topics:
        score += min(len(topics) * 2, 10)

    if repo.get("license"):
        score += 5

    if repo.get("homepage"):
        score += 5

    if not repo.get("fork"):
        score += 10

    days = days_ago(repo.get("pushed_at"))

    if days is not None:
        if days <= 7:
            score += 10
        elif days <= 30:
            score += 8
        elif days <= 180:
            score += 4

    if repo.get("archived"):
        score -= 5

    return max(0, min(score, 100))


def completeness(profile):
    fields = [
        profile.get("name"),
        profile.get("bio"),
        profile.get("location"),
        profile.get("blog"),
        profile.get("company")
    ]

    return round(
        sum(bool(field) for field in fields)
        / len(fields)
        * 100
    )


def portfolio_score(profile, stats, total_repos):
    if total_repos == 0:
        return 0

    activity = min(
        stats["active30"] / total_repos * 100,
        100
    )

    original = (
        stats["original"] / total_repos * 100
    )

    long_activity = min(
        stats["active180"] * 5,
        100
    )

    stars = min(stats["stars"], 100)
    followers = min(profile.get("followers", 0), 100)

    score = (
        completeness(profile) * 0.20 +
        activity * 0.20 +
        original * 0.20 +
        long_activity * 0.20
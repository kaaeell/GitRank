import os
import sys
from datetime import datetime, timezone
import requests

API_URL = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN", "")
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "GitRank",
    **( {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {} )
}


# ---------------- API Helper ----------------

def fetch_json(endpoint: str, params: dict = None):
    try:
        r = requests.get(f"{API_URL}/{endpoint}", headers=HEADERS, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        
        errors = {
            403: "❌ GitHub API rate limit hit or permission error.",
            404: "❌ Requested resource not found."
        }
        print(errors.get(r.status_code, f"❌ API error: {r.status_code}"))
    except requests.RequestException as err:
        print(f"❌ Connection error: {err}")
    return None


def fetch_all_repos(username: str):
    repos, page = [], 1
    while True:
        data = fetch_json(f"users/{username}/repos", {"per_page": 100, "page": page, "sort": "updated"})
        if data is None:
            return None
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


# ---------------- Scoring & Metrics ----------------

def calculate_days_ago(iso_str: str) -> int | None:
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except ValueError:
        return None


def compute_repo_score(repo: dict, days_since_push: int | None) -> int:
    score = (
        min(repo.get("stargazers_count", 0) * 2, 30)
        + min(repo.get("forks_count", 0) * 3, 20)
        + (10 if repo.get("description") else 0)
        + min(len(repo.get("topics", [])) * 2, 10)
        + (5 if repo.get("license") else 0)
        + (5 if repo.get("homepage") else 0)
        + (10 if not repo.get("fork") else 0)
    )

    if days_since_push is not None:
        if days_since_push <= 7:
            score += 10
        elif days_since_push <= 30:
            score += 8
        elif days_since_push <= 180:
            score += 4

    if repo.get("archived"):
        score -= 5

    return max(0, min(score, 100))


def compute_profile_completeness(profile: dict) -> int:
    fields = ("name", "bio", "location", "blog", "company")
    completed = sum(1 for field in fields if profile.get(field))
    return round((completed / len(fields)) * 100)


def analyze_account(profile: dict, repos: list):
    stats = {
        "stars": 0,
        "forks": 0,
        "issues": 0,
        "active30": 0,
        "active180": 0,
        "original": 0,
        "archived": 0,
        "stale": 0,
        "languages": {},
    }

    # Attach score to repo objects directly to avoid re-computation
    for r in repos:
        stars = r.get("stargazers_count", 0)
        forks = r.get("forks_count", 0)
        pushed_days = calculate_days_ago(r.get("pushed_at"))
        
        r["_score"] = compute_repo_score(r, pushed_days)

        stats["stars"] += stars
        stats["forks"] += forks
        stats["issues"] += r.get("open_issues_count", 0)

        if not r.get("fork"):
            stats["original"] += 1
        if r.get("archived"):
            stats["archived"] += 1

        if pushed_days is not None:
            if pushed_days <= 30:
                stats["active30"] += 1
            if pushed_days <= 180:
                stats["active180"] += 1
            if pushed_days > 180 and not r.get("archived"):
                stats["stale"] += 1

        if lang := r.get("language"):
            stats["languages"][lang] = stats["languages"].get(lang, 0) + 1

    total_repos = len(repos) or 1
    completeness = compute_profile_completeness(profile)
    
    activity_score = min(stats["active30"] / total_repos * 100, 100)
    original_ratio = stats["original"] / total_repos * 100
    long_activity = min(stats["active180"] * 5, 100)

    overall_score = round(
        completeness * 0.20
        + activity_score * 0.20
        + original_ratio * 0.20
        + long_activity * 0.20
        + min(stats["stars"], 100) * 0.10
        + min(profile.get("followers", 0), 100) * 0.10,
        1,
    )

    xp = (
        len(repos) * 25
        + stats["original"] * 15
        + stats["stars"] * 10
        + stats["forks"] * 15
        + stats["active30"] * 30
    )
    level = xp // 250 + 1

    return {
        "stats": stats,
        "completeness": completeness,
        "score": overall_score,
        "xp": xp,
        "level": level,
    }


# ---------------- CLI Display ----------------

def print_dashboard(profile: dict, repos: list, metrics: dict):
    s = metrics["stats"]
    print("\n" + "=" * 50)
    print("             GITRANK v1.1")
    print("=" * 50)

    print(f"\n👤 {profile.get('name') or profile['login']}")
    print(f"Bio: {profile.get('bio') or 'None'}")
    print(f"Followers: {profile.get('followers', 0)}")
    print(f"Repositories: {len(repos)}")
    print(f"Profile Completeness: {metrics['completeness']}%")

    print("\n📊 STATISTICS")
    print(f"⭐ Stars: {s['stars']} | 🍴 Forks: {s['forks']} | 🐛 Issues: {s['issues']}")
    print(f"🔥 Active (30d): {s['active30']} | 📅 Active (180d): {s['active180']}")
    print(f"💡 Original: {s['original']} | 💤 Stale: {s['stale']}")

    print("\n💻 LANGUAGES")
    sorted_langs = sorted(s["languages"].items(), key=lambda x: x[1], reverse=True)
    for lang, count in sorted_langs:
        print(f"  • {lang}: {count}")

    sorted_repos = sorted(repos, key=lambda x: x["_score"], reverse=True)

    print("\n🏆 TOP PROJECTS")
    for i, r in enumerate(sorted_repos[:5], 1):
        print(f"{i}. {r['name']} ({r['_score']}/100) ⭐ {r.get('stargazers_count', 0)}")

    if sorted_repos:
        best = sorted_repos[0]
        print(f"\n🥇 BEST PROJECT\n{best['name']}\n{best.get('html_url', '')}")

    print(f"\n🎯 GITRANK SCORE\n{metrics['score']}/100")
    print(f"\n🎮 DEVELOPER LEVEL\nLevel {metrics['level']} • {metrics['xp']} XP")


def handle_search_mode(repos: list):
    while True:
        choice = input("\nSearch repositories? (y/n): ").strip().lower()
        if choice != "y":
            break

        query = input("Search query: ").strip().lower()
        if not query:
            continue

        matches = [r for r in repos if query in r["name"].lower()]
        if not matches:
            print("No matching repositories found.")
            continue

        matches.sort(key=lambda x: x["_score"], reverse=True)
        print("\nSearch Results:")
        for r in matches:
            print(f"  • {r['name']} | Score: {r['_score']}/100 | ⭐ {r.get('stargazers_count', 0)}")


# ---------------- Entry Point ----------------

def main():
    username = input("GitHub username: ").strip()
    if not username:
        print("❌ Username required.")
        return

    print("\n🔎 Fetching data from GitHub...")
    profile = fetch_json(f"users/{username}")
    if not profile:
        return

    repos = fetch_all_repos(username)
    if repos is None:
        return

    metrics = analyze_account(profile, repos)
    print_dashboard(profile, repos, metrics)
    handle_search_mode(repos)

    print("\n✅ GitRank analysis complete.")


if __name__ == "__main__":
    main()

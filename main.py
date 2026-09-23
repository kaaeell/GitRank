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
            print("❌ User or resource not found.")
        elif r.status_code == 403:
            print("❌ GitHub API rate limit or permission error.")
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
def account_age(date_text):
    days = days_ago(date_text)
    if days is None:
        return "Unknown"
    years = days // 365
    months = (days % 365) // 30
    if years:
        return f"{years}y {months}m"
    return f"{months} months"
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
        sum(bool(x) for x in fields) / len(fields) * 100
    )
def portfolio_score(profile, stats, total_repos):
    if not total_repos:
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
    return round(
        completeness(profile) * 0.20 +
        activity * 0.20 +
        original * 0.20 +
        long_activity * 0.20 +
        min(stats["stars"], 100) * 0.10 +
        min(profile.get("followers", 0), 100) * 0.10,
        1
    )
def most_used_language(stats):
    if not stats["languages"]:
        return "None"
    return max(
        stats["languages"],
        key=stats["languages"].get
    )
def calculate_xp(repos, stats):
    return (
        len(repos) * 25 +
        stats["original"] * 15 +
        stats["stars"] * 10 +
        stats["forks"] * 15 +
        stats["active30"] * 30
    )
def show(profile, repos, stats):
    print("\n" + "=" * 52)
    print("                 GITRANK v1.2")
    print("=" * 52)
    username = profile.get("login", "Unknown")
    name = profile.get("name") or username
    print(f"\n👤 {name} (@{username})")
    print(f"Bio: {profile.get('bio') or 'None'}")
    print(f"Followers: {profile.get('followers', 0)}")
    print(f"Following: {profile.get('following', 0)}")
    print(f"Public gists: {profile.get('public_gists', 0)}")
    print(f"Account age: {account_age(profile.get('created_at'))}")
    print(f"Profile: {completeness(profile)}%")
    print(f"GitHub: https://github.com/{username}")
    print("\n📊 STATISTICS")
    print(f"⭐ Stars: {stats['stars']}")
    print(f"🍴 Forks: {stats['forks']}")
    print(f"🐛 Open Issues/PRs: {stats['issues']}")
    print(f"🔥 Active 30d: {stats['active30']}")
    print(f"📅 Active 180d: {stats['active180']}")
    print(f"💡 Original: {stats['original']}")
    print(f"💤 Stale: {stats['stale']}")
    print(f"📦 Archived: {stats['archived']}")
    print(f"💻 Main language: {most_used_language(stats)}")
    print("\n💻 LANGUAGES")
    if stats["languages"]:
        for language, count in sorted(
            stats["languages"].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"  {language}: {count}")
    else:
        print("  None detected.")
    print("\n🏆 TOP PROJECTS")
    top = sorted(
        repos,
        key=repo_score,
        reverse=True
    )[:5]
    if top:
        for i, repo in enumerate(top, 1):
            print(
                f"{i}. {repo['name']} "
                f"({repo_score(repo)}/100) "
                f"⭐{repo.get('stargazers_count', 0)}"
            )
    else:
        print("No repositories.")
    if repos:
        best = max(repos, key=repo_score)
        print("\n🥇 TOP PROJECT")
        print(f"Name: {best['name']}")
        print(f"Score: {repo_score(best)}/100")
        print(f"URL: {best.get('html_url', '')}")
        if best.get("description"):
            print(f"About: {best['description']}")
    recent = sorted(
        repos,
        key=lambda r: r.get("pushed_at") or "",
        reverse=True
    )
    if recent:
        print("\n🟢 RECENTLY UPDATED")
        print(recent[0]["name"])
        print(recent[0].get("html_url", ""))
    score = portfolio_score(
        profile,
        stats,
        len(repos)
    )
    print("\n🎯 GITRANK SCORE")
    print(f"{score}/100")
    xp = calculate_xp(repos, stats)
    level = xp // 250 + 1
    print("\n🎮 DEVELOPER LEVEL")
    print(f"Level {level} • {xp} XP")
def search_repos(repos):
    query = input(
        "\nSearch repository: "
    ).strip().lower()
    if not query:
        return
    found = []
    for repo in repos:
        name = repo.get("name", "").lower()
        description = (
            repo.get("description") or ""
        ).lower()
        language = (
            repo.get("language") or ""
        ).lower()
        if (
            query in name
            or query in description
            or query in language
        ):
            found.append(repo)
    if not found:
        print("❌ No results.")
        return
    print("\n🔎 RESULTS")
    for repo in sorted(
        found,
        key=repo_score,
        reverse=True
    ):
        print(
            f"{repo['name']} | "
            f"{repo_score(repo)}/100 | "
            f"⭐{repo.get('stargazers_count', 0)}"
        )
def export_report(profile, repos, stats):
    username = profile.get("login", "github_user")
    score = portfolio_score(
        profile,
        stats,
        len(repos)
    )
    xp = calculate_xp(repos, stats)
    filename = f"{username}_gitrank.txt"
    with open(filename, "w", encoding="utf-8") as file:
        file.write("GITRANK v1.2\n")
        file.write("=" * 40 + "\n\n")
        file.write(f"User: {username}\n")
        file.write(
            f"Name: {profile.get('name') or username}\n"
        )
        file.write(
            f"Followers: {profile.get('followers', 0)}\n"
        )
        file.write(
            f"Following: {profile.get('following', 0)}\n"
        )
        file.write(
            f"Repositories: {len(repos)}\n"
        )
        file.write(
            f"Account age: "
            f"{account_age(profile.get('created_at'))}\n"
        )
        file.write("\nSTATISTICS\n")
        file.write("-" * 40 + "\n")
        file.write(f"Stars: {stats['stars']}\n")
        file.write(f"Forks: {stats['forks']}\n")
        file.write(f"Active 30d: {stats['active30']}\n")
        file.write(f"Active 180d: {stats['active180']}\n")
        file.write(f"Original: {stats['original']}\n")
        file.write(f"Stale: {stats['stale']}\n")
        file.write("\nGITRANK\n")
        file.write("-" * 40 + "\n")
        file.write(f"Score: {score}/100\n")
        file.write(f"Level: {xp // 250 + 1}\n")
        file.write(f"XP: {xp}\n")
        file.write("\nTOP PROJECTS\n")
        file.write("-" * 40 + "\n")
        for repo in sorted(
            repos,
            key=repo_score,
            reverse=True
        )[:5]:
            file.write(
                f"{repo['name']} - "
                f"{repo_score(repo)}/100\n"
            )
    print(f"\n💾 Report saved as: {filename}")
def main():
    username = input(
        "GitHub username: "
    ).strip()
    if not username:
        print("❌ Username required.")
        return
    print("\n🔎 Analyzing GitHub...")
    profile = get_profile(username)
    if not profile:
        return
    repos = get_repos(username)
    if repos is None:
        return
    stats = analyze(repos)
    show(profile, repos, stats)
    while True:
        print("\nOPTIONS")
        print("1. Search repositories")
        print("2. Export report")
        print("3. Exit")
        choice = input("\nChoose: ").strip()
        if choice == "1":
            search_repos(repos)
        elif choice == "2":
            export_report(profile, repos, stats)
        elif choice == "3":
            break
        else:
            print("❌ Invalid option.")
    print("\n✅ GitRank analysis complete.")
if __name__ == "__main__":
    main()
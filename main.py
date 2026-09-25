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


def format_date(date_text):
    if not date_text:
        return "Unknown"

    try:
        date = datetime.fromisoformat(
            date_text.replace("Z", "+00:00")
        )
        return date.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return "Unknown"


def activity_status(repo):
    days = days_ago(repo.get("pushed_at"))

    if days is None:
        return "Unknown"

    if days <= 30:
        return "🟢 Active"
    if days <= 180:
        return "🟡 Recent"

    return "🔴 Stale"


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

    if repo.get("topics"):
        score += min(len(repo["topics"]) * 2, 10)

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


def normalize(value, maximum):
    if maximum <= 0:
        return 0

    return min(value / maximum * 100, 100)


def portfolio_score(profile, stats, total_repos):
    if total_repos == 0:
        return 0

    profile_score = completeness(profile)

    recent_activity = normalize(
        stats["active30"],
        total_repos
    )

    original_repos = normalize(
        stats["original"],
        total_repos
    )

    six_month_activity = normalize(
        stats["active180"],
        total_repos
    )

    stars = normalize(stats["stars"], 100)
    followers = normalize(
        profile.get("followers", 0),
        100
    )

    score = (
        profile_score * 0.20 +
        recent_activity * 0.20 +
        original_repos * 0.20 +
        six_month_activity * 0.15 +
        stars * 0.15 +
        followers * 0.10
    )

    return round(min(score, 100), 1)


def score_breakdown(profile, stats, total_repos):
    if total_repos == 0:
        return {}

    return {
        "Profile": completeness(profile) * 0.20,
        "Recent activity": normalize(
            stats["active30"],
            total_repos
        ) * 0.20,
        "Original repositories": normalize(
            stats["original"],
            total_repos
        ) * 0.20,
        "6-month activity": normalize(
            stats["active180"],
            total_repos
        ) * 0.15,
        "Stars": normalize(
            stats["stars"],
            100
        ) * 0.15,
        "Followers": normalize(
            profile.get("followers", 0),
            100
        ) * 0.10
    }


def achievements(profile, repos, stats):
    badges = []

    if stats["original"] > 0:
        badges.append("🏗️ Original Builder")

    if stats["active30"] > 0:
        badges.append("🔥 Active Developer")

    if stats["stars"] >= 10:
        badges.append("⭐ Star Collector")

    if stats["forks"] > 0:
        badges.append("🍴 Open Source")

    if profile.get("followers", 0) >= 10:
        badges.append("👥 Community")

    if len(repos) >= 10:
        badges.append("📚 Project Builder")

    if stats["languages"]:
        badges.append("💻 Multi-Language")

    return badges


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


def show_repo(repo, number=None):
    prefix = f"{number}. " if number else ""

    print(
        f"{prefix}{repo['name']} "
        f"({repo_score(repo)}/100)"
    )

    print(f"   {activity_status(repo)}")
    print(f"   ⭐ {repo.get('stargazers_count', 0)}")
    print(f"   Updated: {format_date(repo.get('pushed_at'))}")

    if repo.get("language"):
        print(f"   Language: {repo['language']}")

    if repo.get("description"):
        print(f"   {repo['description']}")

    topics = repo.get("topics", [])

    if topics:
        print(f"   Topics: {', '.join(topics[:5])}")

    print(f"   {repo.get('html_url', '')}")


def show(profile, repos, stats):
    print("\n" + "=" * 55)
    print("                  GITRANK v1.3")
    print("=" * 55)

    username = profile.get("login", "Unknown")
    name = profile.get("name") or username

    print(f"\n👤 {name} (@{username})")
    print(f"Bio: {profile.get('bio') or 'None'}")
    print(f"Followers: {profile.get('followers', 0)}")
    print(f"Following: {profile.get('following', 0)}")
    print(f"Public gists: {profile.get('public_gists', 0)}")
    print(f"Account age: {account_age(profile.get('created_at'))}")
    print(f"Profile completeness: {completeness(profile)}%")
    print(f"GitHub: https://github.com/{username}")

    print("\n📊 REPOSITORY METRICS")
    print(f"⭐ Total Stars: {stats['stars']}")
    print(f"🍴 Total Forks: {stats['forks']}")
    print(f"🐛 Open Issues & PRs: {stats['issues']}")
    print(f"🔥 Updated in 30 Days: {stats['active30']}")
    print(f"📅 Updated in 180 Days: {stats['active180']}")
    print(f"💡 Original Repositories: {stats['original']}")
    print(f"💤 Inactive 180+ Days: {stats['stale']}")
    print(f"📦 Archived Repositories: {stats['archived']}")
    print(f"💻 Main Language: {most_used_language(stats)}")

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
            show_repo(repo, i)
    else:
        print("No repositories.")

    if repos:
        recent = max(
            repos,
            key=lambda r: r.get("pushed_at") or ""
        )

        print("\n🟢 MOST RECENTLY UPDATED")
        show_repo(recent)

    print("\n🎯 GITRANK SCORE")

    score = portfolio_score(
        profile,
        stats,
        len(repos)
    )

    print(f"{score}/100")

    print("\n📈 SCORE BREAKDOWN")

    breakdown = score_breakdown(
        profile,
        stats,
        len(repos)
    )

    for name, value in breakdown.items():
        print(f"  {name}: {value:.1f}")

    print("\n🏅 ACHIEVEMENTS")

    badges = achievements(
        profile,
        repos,
        stats
    )

    if badges:
        for badge in badges:
            print(f"  {badge}")
    else:
        print("  Keep building to unlock badges.")

    xp = calculate_xp(repos, stats)
    level = xp // 250 + 1

    print("\n🎮 DEVELOPER LEVEL")
    print(f"Level {level} • {xp} XP")


def search_repos(repos):
    query = input(
        "\nSearch name, description, language or topic: "
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

        topics = [
            topic.lower()
            for topic in repo.get("topics", [])
        ]

        if (
            query in name
            or query in description
            or query in language
            or query in topics
        ):
            found.append(repo)

    if not found:
        print("❌ No results.")
        return

    print(f"\n🔎 {len(found)} RESULT(S)")

    for repo in sorted(
        found,
        key=repo_score,
        reverse=True
    ):
        show_repo(repo)


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
        file.write("GITRANK v1.3\n")
        file.write("=" * 45 + "\n\n")

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
        file.write(
            f"Profile completeness: "
            f"{completeness(profile)}%\n"
        )

        file.write("\nREPOSITORY METRICS\n")
        file.write("-" * 45 + "\n")
        file.write(f"Total Stars: {stats['stars']}\n")
        file.write(f"Total Forks: {stats['forks']}\n")
        file.write(
            f"Open Issues & PRs: {stats['issues']}\n"
        )
        file.write(
            f"Updated in 30 Days: {stats['active30']}\n"
        )
        file.write(
            f"Updated in 180 Days: {stats['active180']}\n"
        )
        file.write(
            f"Original Repositories: {stats['original']}\n"
        )
        file.write(
            f"Inactive 180+ Days: {stats['stale']}\n"
        )
        file.write(
            f"Archived Repositories: {stats['archived']}\n"
        )
        file.write(
            f"Main Language: "
            f"{most_used_language(stats)}\n"
        )

        file.write("\nGITRANK SCORE\n")
        file.write("-" * 45 + "\n")
        file.write(f"Score: {score}/100\n")

        file.write("\nSCORE BREAKDOWN\n")
        file.write("-" * 45 + "\n")

        for name, value in score_breakdown(
            profile,
            stats,
            len(repos)
        ).items():
            file.write(f"{name}: {value:.1f}\n")

        file.write("\nACHIEVEMENTS\n")
        file.write("-" * 45 + "\n")

        for badge in achievements(
            profile,
            repos,
            stats
        ):
            file.write(f"{badge}\n")

        file.write("\nDEVELOPER LEVEL\n")
        file.write("-" * 45 + "\n")
        file.write(f"Level: {xp // 250 + 1}\n")
        file.write(f"XP: {xp}\n")

        file.write("\nTOP PROJECTS\n")
        file.write("-" * 45 + "\n")

        for repo in sorted(
            repos,
            key=repo_score,
            reverse=True
        )[:5]:
            file.write(
                f"{repo['name']} - "
                f"{repo_score(repo)}/100\n"
            )
            file.write(
                f"{repo.get('html_url', '')}\n"
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
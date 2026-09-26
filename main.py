def activity_status(repo):
    if repo.get("archived"):
        return "📦 Archived"

    days = days_ago(repo.get("pushed_at"))

    if days is None:
        return "Unknown"
    if days <= 30:
        return "🟢 Active"
    if days <= 180:
        return "🟡 Recent"

    return "🔴 Stale"


def score_breakdown(profile, stats, total_repos):
    if total_repos == 0:
        return {}

    metrics = [
        ("Profile", completeness(profile), 0.20),
        ("Recent activity",
         normalize(stats["active30"], total_repos), 0.20),
        ("Original repositories",
         normalize(stats["original"], total_repos), 0.20),
        ("6-month activity",
         normalize(stats["active180"], total_repos), 0.15),
        ("Stars", normalize(stats["stars"], 100), 0.15),
        ("Followers",
         normalize(profile.get("followers", 0), 100), 0.10)
    ]

    return {
        name: {
            "value": value,
            "weight": weight,
            "points": value * weight
        }
        for name, value, weight in metrics
    }


def search_repos(repos):
    query = input(
        "\nSearch name, description, language or topic: "
    ).strip().lower()

    if not query:
        return

    found = []

    for repo in repos:
        name = (repo.get("name") or "").lower()
        description = (repo.get("description") or "").lower()
        language = (repo.get("language") or "").lower()
        topics = [
            topic.lower()
            for topic in repo.get("topics", [])
        ]

        if (
            query in name
            or query in description
            or query in language
            or any(query in topic for topic in topics)
        ):
            found.append(repo)

    if not found:
        print("❌ No results.")
        return

    print(f"\n🔎 {len(found)} RESULT(S)")

    for repo in sorted(found, key=repo_score, reverse=True):
        show_repo(repo)


def show_repo(repo, number=None):
    name = repo.get("name") or "Unknown"
    prefix = f"{number}. " if number else ""

    print(f"{prefix}{name} ({repo_score(repo)}/100)")
    print(f"   {activity_status(repo)}")
    print(f"   ⭐ {repo.get('stargazers_count', 0)}")
    print(f"   Updated: {format_date(repo.get('pushed_at'))}")

    if repo.get("language"):
        print(f"   Language: {repo['language']}")

    if repo.get("description"):
        print(f"   {repo['description']}")

    topics = repo.get("topics") or []
    if topics:
        print(f"   Topics: {', '.join(topics[:5])}")

    print(f"   {repo.get('html_url') or 'No URL available'}")
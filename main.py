import os
import requests
from datetime import datetime, timezone


# ============================================================
# GITRANK v1.1
# GitHub Developer Portfolio Analyzer
# ============================================================

VERSION = "1.1.0"
BASE_URL = "https://api.github.com"
REQUEST_TIMEOUT = 10

# Optional GitHub token.
# Recommended:
#   Linux/macOS: export GITHUB_TOKEN="your_token"
#   Windows:     set GITHUB_TOKEN=your_token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


# ============================================================
# API
# ============================================================

def get_headers():
    """Return HTTP headers used for GitHub API requests."""

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitRank-GitHub-Analyzer",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    return headers


def get_json(url, params=None):
    """Make a GET request and safely return JSON data."""

    try:
        response = requests.get(
            url,
            headers=get_headers(),
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 200:
            return response.json()

        if response.status_code == 404:
            print("❌ GitHub user/resource not found.")
            return None

        if response.status_code == 401:
            print("❌ GitHub authentication failed.")
            return None

        if response.status_code == 403:
            remaining = response.headers.get(
                "X-RateLimit-Remaining"
            )

            if remaining == "0":
                reset = response.headers.get(
                    "X-RateLimit-Reset"
                )

                if reset:
                    try:
                        reset_time = datetime.fromtimestamp(
                            int(reset),
                            tz=timezone.utc,
                        )

                        print(
                            "❌ GitHub API rate limit reached."
                        )
                        print(
                            f"   Reset time: {reset_time}"
                        )

                    except (ValueError, TypeError):
                        print(
                            "❌ GitHub API rate limit reached."
                        )
                else:
                    print(
                        "❌ GitHub API rate limit reached."
                    )
            else:
                print(
                    "❌ GitHub API returned 403 Forbidden."
                )

            return None

        print(
            f"❌ GitHub API error: "
            f"{response.status_code}"
        )

        return None

    except requests.exceptions.Timeout:
        print("❌ Request timed out.")
        return None

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to GitHub.")
        return None

    except requests.exceptions.RequestException as error:
        print(f"❌ Request error: {error}")
        return None

    except ValueError:
        print("❌ GitHub returned invalid JSON.")
        return None


# ============================================================
# DATE UTILITIES
# ============================================================

def parse_date(date_text):
    """Convert a GitHub ISO date into a timezone-aware datetime."""

    if not date_text:
        return None

    try:
        date = datetime.fromisoformat(
            date_text.replace("Z", "+00:00")
        )

        if date.tzinfo is None:
            date = date.replace(
                tzinfo=timezone.utc
            )

        return date

    except (ValueError, TypeError):
        return None


def days_since(date_text):
    """Return the number of days since a GitHub timestamp."""

    date = parse_date(date_text)

    if not date:
        return None

    now = datetime.now(timezone.utc)

    return max(
        0,
        (now - date).days,
    )


def format_date(date_text):
    """Format a GitHub timestamp as YYYY-MM-DD."""

    date = parse_date(date_text)

    if not date:
        return "Unknown"

    return date.strftime("%Y-%m-%d")


# ============================================================
# PROFILE
# ============================================================

def get_profile(username):
    """Fetch a GitHub user's public profile."""

    url = f"{BASE_URL}/users/{username}"

    return get_json(url)


# ============================================================
# REPOSITORIES
# ============================================================

def get_repositories(username):
    """Fetch all public repositories with pagination."""

    repositories = []
    page = 1

    while True:

        url = f"{BASE_URL}/users/{username}/repos"

        batch = get_json(
            url,
            params={
                "per_page": 100,
                "page": page,
                "sort": "updated",
                "direction": "desc",
            },
        )

        # None means an API failure.
        if batch is None:
            return None

        # Empty list means there are no more pages.
        if not batch:
            break

        repositories.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return repositories


# ============================================================
# REPOSITORY SCORING
# ============================================================

def repository_score(repo):
    """
    Calculate a simple project quality score from 0-100.

    Signals:
    - Stars
    - Forks
    - Description
    - Topics
    - License
    - Homepage
    - Original work
    - Recent activity
    """

    score = 0

    stars = repo.get(
        "stargazers_count",
        0,
    ) or 0

    forks = repo.get(
        "forks_count",
        0,
    ) or 0

    # Community recognition
    score += min(stars * 2, 30)
    score += min(forks * 3, 20)

    # Documentation / project metadata
    if repo.get("description"):
        score += 10

    topics = repo.get("topics") or []

    score += min(
        len(topics) * 2,
        10,
    )

    if repo.get("license"):
        score += 5

    if repo.get("homepage"):
        score += 5

    # Original work
    if not repo.get("fork", False):
        score += 10

    # Activity
    age = days_since(
        repo.get("pushed_at")
    )

    if age is not None:

        if age <= 7:
            score += 10

        elif age <= 30:
            score += 8

        elif age <= 180:
            score += 4

    # Archived repositories shouldn't receive an activity bonus.
    if repo.get("archived"):
        score -= 5

    return max(
        0,
        min(score, 100),
    )


# ============================================================
# PORTFOLIO ANALYSIS
# ============================================================

def analyze_repositories(repositories):

    total_stars = 0
    total_forks = 0
    total_open_issues = 0
    total_size = 0

    active_7 = 0
    active_30 = 0
    active_180 = 0

    stale_repositories = 0
    archived_repositories = 0
    original_repositories = 0

    languages = {}
    licenses = {}

    for repo in repositories:

        stars = repo.get(
            "stargazers_count",
            0,
        ) or 0

        forks = repo.get(
            "forks_count",
            0,
        ) or 0

        issues = repo.get(
            "open_issues_count",
            0,
        ) or 0

        size = repo.get(
            "size",
            0,
        ) or 0

        total_stars += stars
        total_forks += forks
        total_open_issues += issues
        total_size += size

        age = days_since(
            repo.get("pushed_at")
        )

        if age is not None:

            if age <= 7:
                active_7 += 1

            if age <= 30:
                active_30 += 1

            if age <= 180:
                active_180 += 1

            if (
                age > 180
                and not repo.get("archived", False)
            ):
                stale_repositories += 1

        if repo.get("archived"):
            archived_repositories += 1

        if not repo.get("fork", False):
            original_repositories += 1

        language = repo.get("language")

        if language:
            languages[language] = (
                languages.get(language, 0) + 1
            )

        license_data = repo.get("license")

        if license_data:

            license_name = license_data.get(
                "spdx_id"
            )

            if license_name:
                licenses[license_name] = (
                    licenses.get(
                        license_name,
                        0,
                    ) + 1
                )

    return {
        "total_repos": len(repositories),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "total_open_issues": total_open_issues,
        "total_size_kb": total_size,
        "active_7": active_7,
        "active_30": active_30,
        "active_180": active_180,
        "stale_repositories": stale_repositories,
        "archived_repositories": archived_repositories,
        "original_repositories": original_repositories,
        "languages": languages,
        "licenses": licenses,
    }


# ============================================================
# PROFILE COMPLETENESS
# ============================================================

def profile_completeness(profile):

    fields = [
        profile.get("name"),
        profile.get("bio"),
        profile.get("company"),
        profile.get("location"),
        profile.get("blog"),
        profile.get("twitter_username"),
    ]

    completed = sum(
        1
        for field in fields
        if field
    )

    return round(
        completed / len(fields) * 100
    )


# ============================================================
# PORTFOLIO SCORE
# ============================================================

def portfolio_score(profile, stats):

    completeness = profile_completeness(
        profile
    )

    profile_points = completeness * 0.20

    if stats["total_repos"] > 0:
        activity_ratio = (
            stats["active_30"]
            / stats["total_repos"]
        ) * 100
    else:
        activity_ratio = 0

    activity_ratio = min(
        activity_ratio,
        100,
    )

    activity_points = (
        activity_ratio * 0.20
    )

    if stats["total_repos"] > 0:
        original_ratio = (
            stats["original_repositories"]
            / stats["total_repos"]
        ) * 100
    else:
        original_ratio = 0

    original_points = (
        original_ratio * 0.20
    )

    long_term_activity = min(
        stats["active_180"] * 5,
        100,
    )

    activity_history_points = (
        long_term_activity * 0.20
    )

    star_points = (
        min(stats["total_stars"], 100)
        * 0.10
    )

    follower_points = (
        min(
            profile.get("followers", 0),
            100,
        )
        * 0.10
    )

    total = (
        profile_points
        + activity_points
        + original_points
        + activity_history_points
        + star_points
        + follower_points
    )

    return round(
        min(total, 100),
        1,
    )


# ============================================================
# XP SYSTEM
# ============================================================

def calculate_xp(profile, stats):

    xp = 0

    xp += stats["total_repos"] * 25
    xp += stats["original_repositories"] * 15
    xp += stats["total_stars"] * 10
    xp += stats["total_forks"] * 15
    xp += stats["active_30"] * 30
    xp += len(stats["languages"]) * 50
    xp += profile.get("followers", 0) * 5

    return xp


def developer_level(xp):

    level = (
        xp // 250
    ) + 1

    current_xp = xp % 250

    return level, current_xp


# ============================================================
# ACHIEVEMENTS
# ============================================================

def get_achievements(
    profile,
    stats,
    repositories,
):

    achievements = []

    followers = profile.get(
        "followers",
        0,
    )

    if followers >= 10:
        achievements.append(
            "👥 Community Builder"
        )

    if followers >= 50:
        achievements.append(
            "🌟 Popular Developer"
        )

    if stats["total_stars"] >= 10:
        achievements.append(
            "⭐ Star Collector"
        )

    if stats["total_stars"] >= 50:
        achievements.append(
            "🌠 Rising Star"
        )

    if stats["total_forks"] >= 10:
        achievements.append(
            "🍴 Open Source Contributor"
        )

    if stats["total_repos"] >= 10:
        achievements.append(
            "📦 Project Builder"
        )

    if stats["total_repos"] >= 25:
        achievements.append(
            "🏗️ Portfolio Builder"
        )

    if stats["active_30"] >= 3:
        achievements.append(
            "🔥 Active Developer"
        )

    if stats["original_repositories"] >= 10:
        achievements.append(
            "💡 Original Creator"
        )

    language_count = len(
        stats["languages"]
    )

    if language_count >= 3:
        achievements.append(
            "🌐 Polyglot Programmer"
        )

    if language_count >= 5:
        achievements.append(
            "🧠 Multi-Language Developer"
        )

    if any(
        repo.get("homepage")
        for repo in repositories
    ):
        achievements.append(
            "🚀 Project Deployer"
        )

    return achievements


# ============================================================
# BEST PROJECT
# ============================================================

def best_project(repositories):

    if not repositories:
        return None

    return max(
        repositories,
        key=repository_score,
    )


# ============================================================
# TOP REPOSITORIES
# ============================================================

def top_repositories(
    repositories,
    amount=10,
):

    return sorted(
        repositories,
        key=repository_score,
        reverse=True,
    )[:amount]


# ============================================================
# TECH STACK
# ============================================================

def show_tech_stack(stats):

    print("\n" + "=" * 60)
    print("💻 TECH STACK")
    print("=" * 60)

    languages = stats["languages"]

    if not languages:
        print("No language information available.")
        return

    total = sum(
        languages.values()
    )

    for language, count in sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True,
    ):

        percentage = (
            count / total * 100
        )

        bar_length = int(
            percentage / 5
        )

        bar = "█" * bar_length

        print(
            f"{language:<15}"
            f"{bar:<20}"
            f"{percentage:>5.1f}%"
        )


# ============================================================
# TIMELINE
# ============================================================

def portfolio_timeline(repositories):

    dates = []

    for repo in repositories:

        created = parse_date(
            repo.get("created_at")
        )

        if created:
            dates.append(created)

    if not dates:
        return None

    dates.sort()

    first = dates[0]
    latest = dates[-1]

    span_years = round(
        (latest - first).days / 365,
        1,
    )

    return {
        "first_project": first.strftime(
            "%Y-%m-%d"
        ),
        "latest_project": latest.strftime(
            "%Y-%m-%d"
        ),
        "years": span_years,
    }


# ============================================================
# ACTIVITY
# ============================================================

def activity_name(event_type):

    names = {
        "PushEvent": "Pushed code",
        "CreateEvent": "Created repository/branch",
        "DeleteEvent": "Deleted branch/tag",
        "IssuesEvent": "Updated an issue",
        "IssueCommentEvent": "Commented on an issue",
        "PullRequestEvent": "Updated a pull request",
        "PullRequestReviewEvent": "Reviewed a pull request",
        "PullRequestReviewCommentEvent":
            "Commented on a pull request",
        "ForkEvent": "Forked a repository",
        "WatchEvent": "Starred a repository",
        "ReleaseEvent": "Published a release",
        "PublicEvent": "Made repository public",
        "CommitCommentEvent": "Commented on a commit",
        "GollumEvent": "Updated a wiki",
    }

    return names.get(
        event_type,
        event_type,
    )


def get_recent_activity(username):

    url = (
        f"{BASE_URL}/users/"
        f"{username}/events/public"
    )

    events = get_json(
        url,
        params={
            "per_page": 30
        },
    )

    if events is None:
        return []

    return events


# ============================================================
# SEARCH
# ============================================================

def search_repositories(repositories):

    query = input(
        "\nEnter repository name to search: "
    ).strip().lower()

    if not query:
        print(
            "❌ Search cannot be empty."
        )
        return

    results = [
        repo
        for repo in repositories
        if query in repo.get(
            "name",
            "",
        ).lower()
    ]

    print("\n" + "=" * 60)
    print("🔎 SEARCH RESULTS")
    print("=" * 60)

    if not results:
        print(
            "No repositories found."
        )
        return

    results.sort(
        key=repository_score,
        reverse=True,
    )

    for repo in results:

        print(
            f"\n📦 {repo['name']}"
        )

        print(
            f"   Score: "
            f"{repository_score(repo)}/100"
        )

        print(
            f"   Language: "
            f"{repo.get('language') or 'N/A'}"
        )

        print(
            f"   ⭐ Stars: "
            f"{repo.get('stargazers_count', 0)}"
        )

        print(
            f"   🍴 Forks: "
            f"{repo.get('forks_count', 0)}"
        )

        print(
            f"   Updated: "
            f"{format_date(repo.get('pushed_at'))}"
        )


# ============================================================
# RECRUITER SNAPSHOT
# ============================================================

def recruiter_snapshot(
    profile,
    stats,
    score,
):

    print("\n" + "=" * 60)
    print("🎯 RECRUITER SNAPSHOT")
    print("=" * 60)

    print(
        f"Developer: "
        f"{profile.get('name') or profile.get('login')}"
    )

    print(
        f"Portfolio Score: "
        f"{score}/100"
    )

    print(
        f"Public Repositories: "
        f"{stats['total_repos']}"
    )

    print(
        f"Stars: "
        f"{stats['total_stars']}"
    )

    print(
        f"Forks: "
        f"{stats['total_forks']}"
    )

    print(
        f"Followers: "
        f"{profile.get('followers', 0)}"
    )

    print(
        f"Languages: "
        f"{len(stats['languages'])}"
    )

    print(
        f"Active Last 30 Days: "
        f"{stats['active_30']}"
    )


# ============================================================
# IMPROVEMENT TIPS
# ============================================================

def improvement_tips(
    profile,
    stats,
    repositories,
):

    tips = []

    if not profile.get("bio"):
        tips.append(
            "Add a clear developer bio."
        )

    if not profile.get("blog"):
        tips.append(
            "Add a portfolio website or personal site."
        )

    if not profile.get("location"):
        tips.append(
            "Consider adding your location."
        )

    if stats["total_repos"] < 5:
        tips.append(
            "Build more meaningful projects."
        )

    if stats["active_30"] == 0:
        tips.append(
            "Push a project update to show recent activity."
        )

    if stats["total_stars"] == 0:
        tips.append(
            "Improve your project READMEs and publish useful projects."
        )

    missing_descriptions = sum(
        1
        for repo in repositories
        if not repo.get("description")
    )

    if missing_descriptions:
        tips.append(
            f"{missing_descriptions} "
            "repository/repositories have no description."
        )

    missing_topics = sum(
        1
        for repo in repositories
        if not repo.get("topics")
    )

    if missing_topics:
        tips.append(
            "Add topics to important repositories."
        )

    missing_licenses = sum(
        1
        for repo in repositories
        if (
            not repo.get("license")
            and not repo.get("fork")
        )
    )

    if missing_licenses:
        tips.append(
            "Consider adding licenses to open-source projects."
        )

    if stats["stale_repositories"] > 5:
        tips.append(
            "Archive or update old projects that are no longer maintained."
        )

    return tips


# ============================================================
# REPORT
# ============================================================

def build_report(
    profile,
    stats,
    repositories,
    score,
    xp,
    level,
    achievements,
    best,
):

    lines = []

    lines.append("=" * 60)
    lines.append(
        f"GITRANK v{VERSION} - "
        "GITHUB DEVELOPER REPORT"
    )
    lines.append("=" * 60)

    lines.append("")
    lines.append("PROFILE")
    lines.append("-" * 60)

    lines.append(
        f"Username: "
        f"{profile.get('login', 'Unknown')}"
    )

    lines.append(
        f"Name: "
        f"{profile.get('name') or 'Not provided'}"
    )

    lines.append(
        f"Bio: "
        f"{profile.get('bio') or 'Not provided'}"
    )

    lines.append(
        f"Location: "
        f"{profile.get('location') or 'Not provided'}"
    )

    lines.append(
        f"Followers: "
        f"{profile.get('followers', 0)}"
    )

    lines.append(
        f"Following: "
        f"{profile.get('following', 0)}"
    )

    lines.append(
        f"Profile Completeness: "
        f"{profile_completeness(profile)}%"
    )

    lines.append("")
    lines.append("PORTFOLIO")
    lines.append("-" * 60)

    lines.append(
        f"Portfolio Score: {score}/100"
    )

    lines.append(
        f"XP: {xp}"
    )

    lines.append(
        f"Developer Level: {level}"
    )

    lines.append(
        f"Repositories: "
        f"{stats['total_repos']}"
    )

    lines.append(
        f"Original Repositories: "
        f"{stats['original_repositories']}"
    )

    lines.append(
        f"Stars: "
        f"{stats['total_stars']}"
    )

    lines.append(
        f"Forks: "
        f"{stats['total_forks']}"
    )

    lines.append(
        f"Open Issues: "
        f"{stats['total_open_issues']}"
    )

    lines.append(
        f"Active Last 7 Days: "
        f"{stats['active_7']}"
    )

    lines.append(
        f"Active Last 30 Days: "
        f"{stats['active_30']}"
    )

    lines.append(
        f"Active Last 180 Days: "
        f"{stats['active_180']}"
    )

    lines.append(
        f"Stale Projects: "
        f"{stats['stale_repositories']}"
    )

    lines.append(
        f"Archived Projects: "
        f"{stats['archived_repositories']}"
    )

    lines.append("")
    lines.append("TECH STACK")
    lines.append("-" * 60)

    for language, count in sorted(
        stats["languages"].items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        lines.append(
            f"{language}: "
            f"{count} repositories"
        )

    lines.append("")
    lines.append("ACHIEVEMENTS")
    lines.append("-" * 60)

    if achievements:

        lines.extend(
            achievements
        )

    else:
        lines.append(
            "No achievements yet."
        )

    lines.append("")
    lines.append("TOP REPOSITORIES")
    lines.append("-" * 60)

    for index, repo in enumerate(
        top_repositories(repositories),
        1,
    ):

        lines.append(
            f"{index}. {repo['name']} | "
            f"Score: {repository_score(repo)}/100 | "
            f"Stars: {repo.get('stargazers_count', 0)} | "
            f"Language: {repo.get('language') or 'N/A'}"
        )

    lines.append("")
    lines.append("BEST PROJECT")
    lines.append("-" * 60)

    if best:

        lines.append(
            f"Name: {best['name']}"
        )

        lines.append(
            f"Score: "
            f"{repository_score(best)}/100"
        )

        lines.append(
            f"Language: "
            f"{best.get('language') or 'N/A'}"
        )

        lines.append(
            f"Stars: "
            f"{best.get('stargazers_count', 0)}"
        )

        lines.append(
            f"Forks: "
            f"{best.get('forks_count', 0)}"
        )

        lines.append(
            f"URL: "
            f"{best.get('html_url', '')}"
        )

    return "\n".join(lines)


# ============================================================
# EXPORT
# ============================================================

def export_report(report):

    filename = "gitrank_report.txt"

    try:

        with open(
            filename,
            "w",
            encoding="utf-8",
        ) as file:

            file.write(report)

        print(
            f"\n✅ Report exported to "
            f"{filename}"
        )

    except OSError as error:

        print(
            f"\n❌ Could not export report: "
            f"{error}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        f"                 GITRANK v{VERSION}"
    )
    print(
        "          GitHub Developer Analyzer"
    )
    print("=" * 60)

    username = input(
        "\nEnter GitHub username: "
    ).strip()

    if not username:
        print(
            "❌ Username cannot be empty."
        )
        return

    print(
        "\n🔎 Fetching GitHub profile..."
    )

    profile = get_profile(
        username
    )

    if profile is None:
        print(
            "❌ Could not retrieve GitHub profile."
        )
        return

    print(
        "📦 Fetching repositories..."
    )

    repositories = get_repositories(
        username
    )

    if repositories is None:
        print(
            "❌ Could not retrieve repositories."
        )
        return

    print(
        f"✅ Found "
        f"{len(repositories)} repositories."
    )

    stats = analyze_repositories(
        repositories
    )

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("👤 PROFILE INFORMATION")
    print("=" * 60)

    print(
        f"Username: "
        f"{profile.get('login', 'Unknown')}"
    )

    print(
        f"Name: "
        f"{profile.get('name') or 'Not provided'}"
    )

    print(
        f"Bio: "
        f"{profile.get('bio') or 'Not provided'}"
    )

    print(
        f"Location: "
        f"{profile.get('location') or 'Not provided'}"
    )

    print(
        f"Company: "
        f"{profile.get('company') or 'Not provided'}"
    )

    print(
        f"Followers: "
        f"{profile.get('followers', 0)}"
    )

    print(
        f"Following: "
        f"{profile.get('following', 0)}"
    )

    print(
        f"Public Repositories: "
        f"{profile.get('public_repos', 0)}"
    )

    print(
        f"Profile Created: "
        f"{format_date(profile.get('created_at'))}"
    )

    print(
        f"Profile Completeness: "
        f"{profile_completeness(profile)}%"
    )

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("📊 PORTFOLIO STATISTICS")
    print("=" * 60)

    print(
        f"Total Repositories: "
        f"{stats['total_repos']}"
    )

    print(
        f"Original Repositories: "
        f"{stats['original_repositories']}"
    )

    print(
        f"⭐ Total Stars: "
        f"{stats['total_stars']}"
    )

    print(
        f"🍴 Total Forks: "
        f"{stats['total_forks']}"
    )

    print(
        f"🐛 Open Issues: "
        f"{stats['total_open_issues']}"
    )

    print(
        f"💾 Repository Size: "
        f"{stats['total_size_kb']:,} KB"
    )

    print(
        f"🔥 Active Last 7 Days: "
        f"{stats['active_7']}"
    )

    print(
        f"🔥 Active Last 30 Days: "
        f"{stats['active_30']}"
    )

    print(
        f"📅 Active Last 180 Days: "
        f"{stats['active_180']}"
    )

    print(
        f"💤 Stale Repositories: "
        f"{stats['stale_repositories']}"
    )

    print(
        f"📦 Archived Repositories: "
        f"{stats['archived_repositories']}"
    )

    # --------------------------------------------------------
    # TECH STACK
    # --------------------------------------------------------

    show_tech_stack(
        stats
    )

    # --------------------------------------------------------
    # LICENSES
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("📜 LICENSES")
    print("=" * 60)

    if stats["licenses"]:

        for license_name, count in sorted(
            stats["licenses"].items(),
            key=lambda item: item[1],
            reverse=True,
        ):

            print(
                f"{license_name}: "
                f"{count} repositories"
            )

    else:
        print(
            "No licenses detected."
        )

    # --------------------------------------------------------
    # TOP REPOSITORIES
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("🏆 TOP REPOSITORIES")
    print("=" * 60)

    for index, repo in enumerate(
        top_repositories(
            repositories,
            10,
        ),
        1,
    ):

        print(
            f"\n{index}. 📦 "
            f"{repo.get('name', 'Unknown')}"
        )

        print(
            f"   Score: "
            f"{repository_score(repo)}/100"
        )

        print(
            f"   ⭐ Stars: "
            f"{repo.get('stargazers_count', 0)}"
        )

        print(
            f"   🍴 Forks: "
            f"{repo.get('forks_count', 0)}"
        )

        print(
            f"   💻 Language: "
            f"{repo.get('language') or 'N/A'}"
        )

        print(
            f"   Updated: "
            f"{format_date(repo.get('pushed_at'))}"
        )

    # --------------------------------------------------------
    # BEST PROJECT
    # --------------------------------------------------------

    best = best_project(
        repositories
    )

    print("\n" + "=" * 60)
    print("🥇 BEST PROJECT")
    print("=" * 60)

    if best:

        print(
            f"Name: {best['name']}"
        )

        print(
            f"Score: "
            f"{repository_score(best)}/100"
        )

        print(
            f"Language: "
            f"{best.get('language') or 'N/A'}"
        )

        print(
            f"Stars: "
            f"{best.get('stargazers_count', 0)}"
        )

        print(
            f"Forks: "
            f"{best.get('forks_count', 0)}"
        )

        print(
            f"URL: "
            f"{best.get('html_url', '')}"
        )

    # --------------------------------------------------------
    # PORTFOLIO SCORE
    # --------------------------------------------------------

    score = portfolio_score(
        profile,
        stats,
    )

    print("\n" + "=" * 60)
    print("🏆 PORTFOLIO SCORE")
    print("=" * 60)

    print(
        f"GitRank Score: "
        f"{score}/100"
    )

    # --------------------------------------------------------
    # XP
    # --------------------------------------------------------

    xp = calculate_xp(
        profile,
        stats,
    )

    level, current_xp = developer_level(
        xp
    )

    print("\n" + "=" * 60)
    print("🎮 DEVELOPER XP")
    print("=" * 60)

    print(
        f"XP: {xp}"
    )

    print(
        f"Level: {level}"
    )

    print(
        f"Progress: "
        f"{current_xp}/250 XP"
    )

    progress = int(
        current_xp / 250 * 20
    )

    print(
        "Progress: "
        + "█" * progress
        + "░" * (20 - progress)
    )

    # --------------------------------------------------------
    # ACHIEVEMENTS
    # --------------------------------------------------------

    achievements = get_achievements(
        profile,
        stats,
        repositories,
    )

    print("\n" + "=" * 60)
    print("🏅 ACHIEVEMENTS")
    print("=" * 60)

    if achievements:

        for achievement in achievements:
            print(
                f"✓ {achievement}"
            )

    else:
        print(
            "No achievements yet."
        )

    # --------------------------------------------------------
    # TIMELINE
    # --------------------------------------------------------

    timeline = portfolio_timeline(
        repositories
    )

    print("\n" + "=" * 60)
    print("📅 PORTFOLIO TIMELINE")
    print("=" * 60)

    if timeline:

        print(
            f"First Project: "
            f"{timeline['first_project']}"
        )

        print(
            f"Latest Project: "
            f"{timeline['latest_project']}"
        )

        print(
            f"Portfolio Span: "
            f"{timeline['years']} years"
        )

    else:
        print(
            "Timeline unavailable."
        )

    # --------------------------------------------------------
    # ACTIVITY
    # --------------------------------------------------------

    events = get_recent_activity(
        username
    )

    print("\n" + "=" * 60)
    print("⚡ RECENT PUBLIC ACTIVITY")
    print("=" * 60)

    if events:

        for event in events[:10]:

            event_type = event.get(
                "type",
                "UnknownEvent",
            )

            repo_name = (
                event.get("repo", {})
                .get(
                    "name",
                    "Unknown repository",
                )
            )

            created_at = format_date(
                event.get("created_at")
            )

            print(
                f"{created_at} | "
                f"{activity_name(event_type)} | "
                f"{repo_name}"
            )

    else:
        print(
            "No recent public activity found."
        )

    # --------------------------------------------------------
    # RECRUITER SNAPSHOT
    # --------------------------------------------------------

    recruiter_snapshot(
        profile,
        stats,
        score,
    )

    # --------------------------------------------------------
    # TIPS
    # --------------------------------------------------------

    tips = improvement_tips(
        profile,
        stats,
        repositories,
    )

    print("\n" + "=" * 60)
    print("💡 IMPROVEMENT TIPS")
    print("=" * 60)

    if tips:

        for tip in tips:
            print(
                f"• {tip}"
            )

    else:
        print(
            "No major improvements detected."
        )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    while True:

        choice = input(
            "\nSearch repositories? (y/n): "
        ).strip().lower()

        if choice == "y":

            search_repositories(
                repositories
            )

        elif choice == "n":
            break

        else:
            print(
                "Please enter y or n."
            )

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    report = build_report(
        profile,
        stats,
        repositories,
        score,
        xp,
        level,
        achievements,
        best,
    )

    export_choice = input(
        "\nExport full report to TXT? (y/n): "
    ).strip().lower()

    if export_choice == "y":
        export_report(
            report
        )

    print("\n" + "=" * 60)
    print(
        "✅ GITRANK ANALYSIS COMPLETE"
    )
    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
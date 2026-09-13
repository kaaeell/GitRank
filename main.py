import requests
from datetime import datetime, timezone

GITHUB_TOKEN = ""  # Optional: add a GitHub Personal Access Token

BASE_URL = "https://api.github.com"


def get_headers():
    if GITHUB_TOKEN:
        return {"Authorization": f"token {GITHUB_TOKEN}"}
    return {}


def get_json(url, params=None):
    try:
        response = requests.get(
            url,
            headers=get_headers(),
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()

        if response.status_code == 404:
            print("GitHub user or resource not found.")
        elif response.status_code == 403:
            print("GitHub API rate limit exceeded. Consider adding a token.")
        elif response.status_code >= 500:
            print("GitHub server error.")
        else:
            print(f"Request failed. Status code: {response.status_code}")

    except requests.exceptions.Timeout:
        print("Request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")

    return None


def parse_date(date_text):
    if not date_text:
        return None

    try:
        return datetime.strptime(
            date_text,
            "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def print_header(title):
    print("\n" + "=" * 60)
    print(title.center(60))
    print("=" * 60)


def get_repositories(username):
    repos = []
    page = 1

    # GitHub returns up to 100 repositories per page.
    while True:
        batch = get_json(
            f"{BASE_URL}/users/{username}/repos",
            params={
                "per_page": 100,
                "sort": "updated",
                "page": page
            }
        )

        if batch is None or not batch:
            break

        repos.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return repos


def analyze_repositories(repos):
    stats = {
        "total_stars": 0,
        "total_forks": 0,
        "total_watchers": 0,
        "total_issues": 0,
        "total_size": 0,
        "original": 0,
        "forked": 0,
        "archived": 0,
        "disabled": 0,
        "healthy": 0,
        "active_30": 0,
        "active_180": 0,
        "stale": 0,
        "languages": {},
        "licenses": {},
        "pushed_dates": []
    }

    now = datetime.now(timezone.utc)

    for repo in repos:
        stats["total_stars"] += repo.get("stargazers_count", 0)
        stats["total_forks"] += repo.get("forks_count", 0)
        stats["total_watchers"] += repo.get("watchers_count", 0)
        stats["total_issues"] += repo.get("open_issues_count", 0)
        stats["total_size"] += repo.get("size", 0)

        if repo.get("fork"):
            stats["forked"] += 1
        else:
            stats["original"] += 1

        if repo.get("archived"):
            stats["archived"] += 1

        if repo.get("disabled"):
            stats["disabled"] += 1

        language = repo.get("language")
        if language:
            stats["languages"][language] = (
                stats["languages"].get(language, 0) + 1
            )

        license_name = (
            repo.get("license", {}).get("spdx_id")
            if repo.get("license")
            else None
        )

        if license_name:
            stats["licenses"][license_name] = (
                stats["licenses"].get(license_name, 0) + 1
            )

        health_points = sum([
            bool(repo.get("description")),
            len(repo.get("topics", [])) > 0,
            bool(repo.get("homepage")),
            bool(repo.get("license"))
        ])

        if health_points >= 2:
            stats["healthy"] += 1

        pushed_at = parse_date(repo.get("pushed_at"))

        if pushed_at:
            stats["pushed_dates"].append(pushed_at)
            days = (now - pushed_at).days

            if days <= 30:
                stats["active_30"] += 1

            if days <= 180:
                stats["active_180"] += 1
            else:
                stats["stale"] += 1

    return stats


def repository_score(repo):
    """Simple popularity/activity score used only for ranking repositories."""
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    watchers = repo.get("watchers_count", 0)

    score = stars * 3 + forks * 2 + watchers

    if repo.get("description"):
        score += 2

    if repo.get("topics"):
        score += 2

    if repo.get("license"):
        score += 2

    if not repo.get("archived"):
        score += 1

    return score


def profile_completeness(data):
    fields = [
        data.get("name"),
        data.get("bio"),
        data.get("company"),
        data.get("location"),
        data.get("blog"),
        data.get("twitter_username")
    ]

    completed = sum(1 for field in fields if field)
    percentage = (completed / len(fields)) * 100

    return completed, len(fields), percentage


def get_recent_activity(username):
    events = get_json(
        f"{BASE_URL}/users/{username}/events/public",
        params={"per_page": 30}
    )

    if not events:
        return []

    return events


def activity_name(event_type):
    names = {
        "PushEvent": "Pushed code",
        "PullRequestEvent": "Pull request",
        "IssuesEvent": "Issue activity",
        "IssueCommentEvent": "Issue comment",
        "CreateEvent": "Created repository/branch",
        "DeleteEvent": "Deleted branch/tag",
        "ForkEvent": "Forked repository",
        "WatchEvent": "Starred repository",
        "ReleaseEvent": "Released a version",
        "PublicEvent": "Made repository public"
    }

    return names.get(event_type, event_type)


def build_report(username, data, repos, stats, portfolio_score):
    completed, total_fields, completeness = profile_completeness(data)

    lines = []

    lines.append("=" * 60)
    lines.append("GITRANK - GITHUB PROFILE REPORT".center(60))
    lines.append("=" * 60)

    lines.append("")
    lines.append("PROFILE")
    lines.append("-" * 60)
    lines.append(f"Username:              {data.get('login')}")
    lines.append(f"Name:                  {data.get('name') or 'None'}")
    lines.append(f"Bio:                   {data.get('bio') or 'None'}")
    lines.append(f"Followers:             {data.get('followers', 0)}")
    lines.append(f"Following:             {data.get('following', 0)}")
    lines.append(f"Public repositories:   {data.get('public_repos', 0)}")
    lines.append(f"Profile URL:           {data.get('html_url')}")

    created = parse_date(data.get("created_at"))
    if created:
        age_days = (datetime.now(timezone.utc) - created).days
        lines.append(f"Account created:       {created.strftime('%B %d, %Y')}")
        lines.append(f"Account age:           {age_days / 365.25:.1f} years")

    lines.append("")
    lines.append("REPOSITORIES")
    lines.append("-" * 60)
    lines.append(f"Repositories analyzed: {len(repos)}")
    lines.append(f"Original repositories:  {stats['original']}")
    lines.append(f"Forked repositories:    {stats['forked']}")
    lines.append(f"Archived repositories:  {stats['archived']}")
    lines.append(f"Disabled repositories:  {stats['disabled']}")
    lines.append(f"Total stars:            {stats['total_stars']}")
    lines.append(f"Total forks:            {stats['total_forks']}")
    lines.append(f"Total watchers:         {stats['total_watchers']}")
    lines.append(f"Open issues:            {stats['total_issues']}")
    lines.append(f"Repository size:        {stats['total_size'] / 1024:.2f} MB")

    if repos:
        lines.append(
            f"Average stars/repo:     "
            f"{stats['total_stars'] / len(repos):.2f}"
        )

    lines.append("")
    lines.append("PROFILE COMPLETENESS")
    lines.append("-" * 60)
    lines.append(f"Completed fields:       {completed}/{total_fields}")
    lines.append(f"Completeness:           {completeness:.0f}%")

    lines.append("")
    lines.append("LANGUAGES")
    lines.append("-" * 60)

    for language, count in sorted(
        stats["languages"].items(),
        key=lambda item: item[1],
        reverse=True
    ):
        percentage = (count / len(repos)) * 100
        lines.append(
            f"{language}: {count} repos ({percentage:.1f}%)"
        )

    lines.append("")
    lines.append("REPOSITORY HEALTH")
    lines.append("-" * 60)

    if repos:
        health_percentage = (stats["healthy"] / len(repos)) * 100
    else:
        health_percentage = 0

    lines.append(
        f"Healthy repositories:   {stats['healthy']}/{len(repos)}"
    )
    lines.append(f"Repository health:      {health_percentage:.0f}%")

    lines.append("")
    lines.append("ACTIVITY")
    lines.append("-" * 60)

    if stats["pushed_dates"]:
        latest = max(stats["pushed_dates"])
        days = (datetime.now(timezone.utc) - latest).days

        lines.append(
            f"Last code push:         "
            f"{latest.strftime('%B %d, %Y')} ({days} days ago)"
        )

    lines.append(f"Repos active last 30d:  {stats['active_30']}")
    lines.append(f"Repos active last 180d: {stats['active_180']}")
    lines.append(f"Stale repositories:     {stats['stale']}")

    lines.append("")
    lines.append("TOP 10 REPOSITORIES")
    lines.append("-" * 60)

    ranked = sorted(repos, key=repository_score, reverse=True)

    for index, repo in enumerate(ranked[:10], start=1):
        lines.append(
            f"{index}. {repo.get('name')} | "
            f"Score: {repository_score(repo)} | "
            f"Stars: {repo.get('stargazers_count', 0)} | "
            f"Forks: {repo.get('forks_count', 0)}"
        )

    lines.append("")
    lines.append("PORTFOLIO SCORE")
    lines.append("-" * 60)
    lines.append(f"Portfolio score:       {portfolio_score:.1f}/100")

    return "\n".join(lines)


def main():
    username = input("Enter GitHub username: ").strip()

    if not username:
        print("Username cannot be empty.")
        return

    print("\nLoading GitHub profile...")

    data = get_json(f"{BASE_URL}/users/{username}")

    if not data:
        return

    repos = get_repositories(username)

    if repos is None:
        print("Could not load repositories.")
        return

    stats = analyze_repositories(repos)

    completed, total_fields, completeness = profile_completeness(data)

    if repos:
        health_percentage = (stats["healthy"] / len(repos)) * 100
        original_points = (
            stats["original"] / len(repos) * 100 * 0.20
        )
        activity_points = (
            stats["active_180"] / len(repos) * 100 * 0.20
        )
    else:
        health_percentage = 0
        original_points = 0
        activity_points = 0

    profile_points = completeness * 0.20
    health_points = health_percentage * 0.20
    recognition_points = min(stats["total_stars"], 100) * 0.10

    portfolio_score = (
        profile_points
        + health_points
        + original_points
        + activity_points
        + recognition_points
    )

    print_header("GITHUB PROFILE INFORMATION")

    print(f"Username:              {data.get('login')}")
    print(f"Name:                  {data.get('name') or 'None'}")
    print(f"Bio:                   {data.get('bio') or 'None'}")
    print(f"Account type:          {data.get('type')}")
    print(f"Company:               {data.get('company') or 'None'}")
    print(f"Location:              {data.get('location') or 'None'}")
    print(f"Followers:             {data.get('followers', 0)}")
    print(f"Following:             {data.get('following', 0)}")
    print(f"Public repositories:   {data.get('public_repos', 0)}")
    print(f"Public gists:          {data.get('public_gists', 0)}")
    print(f"Profile URL:           {data.get('html_url')}")

    created = parse_date(data.get("created_at"))

    if created:
        account_age_days = (
            datetime.now(timezone.utc) - created
        ).days

        print(f"Account created:       {created.strftime('%B %d, %Y')}")
        print(f"Account age:           {account_age_days / 365.25:.1f} years")

    print_header("REPOSITORY STATISTICS")

    print(f"Repositories analyzed: {len(repos)}")
    print(f"Original repositories:  {stats['original']}")
    print(f"Forked repositories:    {stats['forked']}")
    print(f"Archived repositories:  {stats['archived']}")
    print(f"Disabled repositories:  {stats['disabled']}")
    print(f"Total stars:            {stats['total_stars']}")
    print(f"Total forks:            {stats['total_forks']}")
    print(f"Total watchers:         {stats['total_watchers']}")
    print(f"Open issues:            {stats['total_issues']}")
    print(f"Total size:             {stats['total_size'] / 1024:.2f} MB")

    if repos:
        print(
            f"Average stars/repo:     "
            f"{stats['total_stars'] / len(repos):.2f}"
        )

    if stats["total_forks"] > 0:
        print(
            f"Star/Fork ratio:        "
            f"{stats['total_stars'] / stats['total_forks']:.2f}"
        )

    print_header("DEVELOPER ACTIVITY")

    if stats["pushed_dates"]:
        latest_push = max(stats["pushed_dates"])
        days_since_push = (
            datetime.now(timezone.utc) - latest_push
        ).days

        print(
            f"Last code push:         "
            f"{latest_push.strftime('%B %d, %Y')} "
            f"({days_since_push} days ago)"
        )

        if days_since_push <= 7:
            print("Activity status:        Highly Active")
        elif days_since_push <= 30:
            print("Activity status:        Active")
        elif days_since_push <= 180:
            print("Activity status:        Moderate")
        else:
            print("Activity status:        Inactive")

    print(f"Repos active last 30d:  {stats['active_30']}")
    print(f"Repos active last 180d: {stats['active_180']}")
    print(f"Stale repositories:     {stats['stale']}")

    print_header("LANGUAGE ANALYSIS")

    if stats["languages"]:
        for language, count in sorted(
            stats["languages"].items(),
            key=lambda item: item[1],
            reverse=True
        ):
            percentage = (count / len(repos)) * 100
            print(
                f"{language}:".ljust(25)
                + f"{count} repos ({percentage:.1f}%)"
            )

        main_language = max(
            stats["languages"],
            key=stats["languages"].get
        )
        print(f"\nMain language:          {main_language}")
    else:
        main_language = "Unknown"
        print("No programming languages detected.")

    print_header("LICENSE ANALYSIS")

    licensed = sum(stats["licenses"].values())
    unlicensed = len(repos) - licensed

    print(f"Licensed repositories:  {licensed}")
    print(f"Without a license:      {unlicensed}")

    for license_name, count in sorted(
        stats["licenses"].items(),
        key=lambda item: item[1],
        reverse=True
    ):
        print(f"{license_name}:".ljust(25) + f"{count} repos")

    print_header("REPOSITORY HEALTH")

    print(f"Healthy repositories:   {stats['healthy']}/{len(repos)}")
    print(f"Repository health:      {health_percentage:.0f}%")

    if health_percentage >= 80:
        print("Health status:          Excellent")
    elif health_percentage >= 60:
        print("Health status:          Good")
    elif health_percentage >= 40:
        print("Health status:          Could Improve")
    else:
        print("Health status:          Needs Work")

    print_header("TOP 10 REPOSITORIES")

    ranked_repos = sorted(
        repos,
        key=repository_score,
        reverse=True
    )

    for index, repo in enumerate(ranked_repos[:10], start=1):
        print(f"\n{index}. {repo.get('name')}")
        print(f"   Rank score:  {repository_score(repo)}")
        print(f"   Stars:       {repo.get('stargazers_count', 0)}")
        print(f"   Forks:       {repo.get('forks_count', 0)}")
        print(f"   Watchers:    {repo.get('watchers_count', 0)}")
        print(f"   Language:    {repo.get('language') or 'Unknown'}")
        print(f"   Size:        {repo.get('size', 0) / 1024:.2f} MB")
        print(f"   Archived:    {'Yes' if repo.get('archived') else 'No'}")
        print(f"   URL:         {repo.get('html_url')}")

    print_header("PORTFOLIO SCORE")

    print(f"Portfolio score:       {portfolio_score:.1f}/100")

    if portfolio_score >= 80:
        print("Portfolio level:       Excellent")
    elif portfolio_score >= 60:
        print("Portfolio level:       Strong")
    elif portfolio_score >= 40:
        print("Portfolio level:       Growing")
    else:
        print("Portfolio level:       Early Stage")

    print_header("SOCIAL METRICS")

    followers = data.get("followers", 0)
    following = data.get("following", 0)

    if following > 0:
        print(
            f"Follower/Following:    "
            f"{followers / following:.2f}"
        )
    else:
        print("Follower/Following:    N/A")

    print_header("RECENT PUBLIC ACTIVITY")

    events = get_recent_activity(username)

    if events:
        event_counts = {}

        for event in events:
            event_type = event.get("type", "Unknown")
            event_counts[event_type] = (
                event_counts.get(event_type, 0) + 1
            )

        for event_type, count in sorted(
            event_counts.items(),
            key=lambda item: item[1],
            reverse=True
        ):
            print(f"{activity_name(event_type)}: {count}")

        print(f"\nEvents analyzed:       {len(events)}")
    else:
        print("No recent public activity found.")

    print_header("QUICK IMPROVEMENT TIPS")

    tips = []

    if completeness < 100:
        tips.append("Complete more profile fields.")

    if health_percentage < 70:
        tips.append(
            "Improve repository descriptions, topics, homepages, and licenses."
        )

    if stats["stale"] > 0:
        tips.append(
            "Update or archive repositories that are no longer maintained."
        )

    if unlicensed > 0:
        tips.append(
            "Consider adding licenses to repositories you want others to use."
        )

    if stats["original"] < len(repos):
        tips.append("Build more original projects instead of relying on forks.")

    if stats["total_stars"] < 10:
        tips.append(
            "Improve project READMEs and share useful projects to gain visibility."
        )

    if not tips:
        tips.append("Profile looks solid. Keep building and shipping.")

    for tip in tips:
        print(f"- {tip}")

    print_header("REPOSITORY SEARCH")

    while True:
        search = input(
            "Search your repositories by name (or press Enter to skip): "
        ).strip().lower()

        if not search:
            break

        matches = [
            repo for repo in repos
            if search in repo.get("name", "").lower()
        ]

        if matches:
            for repo in matches:
                print(
                    f"- {repo.get('name')} | "
                    f"Stars: {repo.get('stargazers_count', 0)} | "
                    f"Forks: {repo.get('forks_count', 0)} | "
                    f"{repo.get('html_url')}"
                )
        else:
            print("No matching repositories found.")

        again = input("Search again? (y/n): ").strip().lower()
        if again != "y":
            break

    print_header("EXPORT REPORT")

    save_report = input(
        "Save the complete analysis to a text file? (y/n): "
    ).strip().lower()

    if save_report == "y":
        report_name = f"{username}_gitrank_report.txt"

        report = build_report(
            username,
            data,
            repos,
            stats,
            portfolio_score
        )

        try:
            with open(report_name, "w", encoding="utf-8") as file:
                file.write(report)

            print(f"Report saved successfully: {report_name}")

        except OSError as e:
            print(f"Could not save report: {e}")

    print_header("DONE")


if __name__ == "__main__":
    main()
import requests
from datetime import datetime, timezone

GITHUB_TOKEN = ""  # Optional: add a GitHub Personal Access Token

BASE_URL = "https://api.github.com"


def get_headers():
    if GITHUB_TOKEN:
        return {"Authorization": f"token {GITHUB_TOKEN}"}
    return {}


def get_json(url, params=None):
    try:
        response = requests.get(
            url,
            headers=get_headers(),
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()

        if response.status_code == 404:
            print("GitHub user or resource not found.")
        elif response.status_code == 403:
            print("GitHub API rate limit exceeded. Consider adding a token.")
        elif response.status_code >= 500:
            print("GitHub server error.")
        else:
            print(f"Request failed. Status code: {response.status_code}")

    except requests.exceptions.Timeout:
        print("Request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")

    return None


def parse_date(date_text):
    if not date_text:
        return None

    try:
        return datetime.strptime(
            date_text,
            "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def print_header(title):
    print("\n" + "=" * 60)
    print(title.center(60))
    print("=" * 60)


def get_repositories(username):
    repos = []
    page = 1

    # GitHub returns up to 100 repositories per page.
    while True:
        batch = get_json(
            f"{BASE_URL}/users/{username}/repos",
            params={
                "per_page": 100,
                "sort": "updated",
                "page": page
            }
        )

        if batch is None or not batch:
            break

        repos.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return repos


def analyze_repositories(repos):
    stats = {
        "total_stars": 0,
        "total_forks": 0,
        "total_watchers": 0,
        "total_issues": 0,
        "total_size": 0,
        "original": 0,
        "forked": 0,
        "archived": 0,
        "disabled": 0,
        "healthy": 0,
        "active_30": 0,
        "active_180": 0,
        "stale": 0,
        "languages": {},
        "licenses": {},
        "pushed_dates": []
    }

    now = datetime.now(timezone.utc)

    for repo in repos:
        stats["total_stars"] += repo.get("stargazers_count", 0)
        stats["total_forks"] += repo.get("forks_count", 0)
        stats["total_watchers"] += repo.get("watchers_count", 0)
        stats["total_issues"] += repo.get("open_issues_count", 0)
        stats["total_size"] += repo.get("size", 0)

        if repo.get("fork"):
            stats["forked"] += 1
        else:
            stats["original"] += 1

        if repo.get("archived"):
            stats["archived"] += 1

        if repo.get("disabled"):
            stats["disabled"] += 1

        language = repo.get("language")
        if language:
            stats["languages"][language] = (
                stats["languages"].get(language, 0) + 1
            )

        license_name = (
            repo.get("license", {}).get("spdx_id")
            if repo.get("license")
            else None
        )

        if license_name:
            stats["licenses"][license_name] = (
                stats["licenses"].get(license_name, 0) + 1
            )

        health_points = sum([
            bool(repo.get("description")),
            len(repo.get("topics", [])) > 0,
            bool(repo.get("homepage")),
            bool(repo.get("license"))
        ])

        if health_points >= 2:
            stats["healthy"] += 1

        pushed_at = parse_date(repo.get("pushed_at"))

        if pushed_at:
            stats["pushed_dates"].append(pushed_at)
            days = (now - pushed_at).days

            if days <= 30:
                stats["active_30"] += 1

            if days <= 180:
                stats["active_180"] += 1
            else:
                stats["stale"] += 1

    return stats


def repository_score(repo):
    """Simple popularity/activity score used only for ranking repositories."""
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    watchers = repo.get("watchers_count", 0)

    score = stars * 3 + forks * 2 + watchers

    if repo.get("description"):
        score += 2

    if repo.get("topics"):
        score += 2

    if repo.get("license"):
        score += 2

    if not repo.get("archived"):
        score += 1

    return score


def profile_completeness(data):
    fields = [
        data.get("name"),
        data.get("bio"),
        data.get("company"),
        data.get("location"),
        data.get("blog"),
        data.get("twitter_username")
    ]

    completed = sum(1 for field in fields if field)
    percentage = (completed / len(fields)) * 100

    return completed, len(fields), percentage


def get_recent_activity(username):
    events = get_json(
        f"{BASE_URL}/users/{username}/events/public",
        params={"per_page": 30}
    )

    if not events:
        return []

    return events


def activity_name(event_type):
    names = {
        "PushEvent": "Pushed code",
        "PullRequestEvent": "Pull request",
        "IssuesEvent": "Issue activity",
        "IssueCommentEvent": "Issue comment",
        "CreateEvent": "Created repository/branch",
        "DeleteEvent": "Deleted branch/tag",
        "ForkEvent": "Forked repository",
        "WatchEvent": "Starred repository",
        "ReleaseEvent": "Released a version",
        "PublicEvent": "Made repository public"
    }

    return names.get(event_type, event_type)


def build_report(username, data, repos, stats, portfolio_score):
    completed, total_fields, completeness = profile_completeness(data)

    lines = []

    lines.append("=" * 60)
    lines.append("GITRANK - GITHUB PROFILE REPORT".center(60))
    lines.append("=" * 60)

    lines.append("")
    lines.append("PROFILE")
    lines.append("-" * 60)
    lines.append(f"Username:              {data.get('login')}")
    lines.append(f"Name:                  {data.get('name') or 'None'}")
    lines.append(f"Bio:                   {data.get('bio') or 'None'}")
    lines.append(f"Followers:             {data.get('followers', 0)}")
    lines.append(f"Following:             {data.get('following', 0)}")
    lines.append(f"Public repositories:   {data.get('public_repos', 0)}")
    lines.append(f"Profile URL:           {data.get('html_url')}")

    created = parse_date(data.get("created_at"))
    if created:
        age_days = (datetime.now(timezone.utc) - created).days
        lines.append(f"Account created:       {created.strftime('%B %d, %Y')}")
        lines.append(f"Account age:           {age_days / 365.25:.1f} years")

    lines.append("")
    lines.append("REPOSITORIES")
    lines.append("-" * 60)
    lines.append(f"Repositories analyzed: {len(repos)}")
    lines.append(f"Original repositories:  {stats['original']}")
    lines.append(f"Forked repositories:    {stats['forked']}")
    lines.append(f"Archived repositories:  {stats['archived']}")
    lines.append(f"Disabled repositories:  {stats['disabled']}")
    lines.append(f"Total stars:            {stats['total_stars']}")
    lines.append(f"Total forks:            {stats['total_forks']}")
    lines.append(f"Total watchers:         {stats['total_watchers']}")
    lines.append(f"Open issues:            {stats['total_issues']}")
    lines.append(f"Repository size:        {stats['total_size'] / 1024:.2f} MB")

    if repos:
        lines.append(
            f"Average stars/repo:     "
            f"{stats['total_stars'] / len(repos):.2f}"
        )

    lines.append("")
    lines.append("PROFILE COMPLETENESS")
    lines.append("-" * 60)
    lines.append(f"Completed fields:       {completed}/{total_fields}")
    lines.append(f"Completeness:           {completeness:.0f}%")

    lines.append("")
    lines.append("LANGUAGES")
    lines.append("-" * 60)

    for language, count in sorted(
        stats["languages"].items(),
        key=lambda item: item[1],
        reverse=True
    ):
        percentage = (count / len(repos)) * 100
        lines.append(
            f"{language}: {count} repos ({percentage:.1f}%)"
        )

    lines.append("")
    lines.append("REPOSITORY HEALTH")
    lines.append("-" * 60)

    if repos:
        health_percentage = (stats["healthy"] / len(repos)) * 100
    else:
        health_percentage = 0

    lines.append(
        f"Healthy repositories:   {stats['healthy']}/{len(repos)}"
    )
    lines.append(f"Repository health:      {health_percentage:.0f}%")

    lines.append("")
    lines.append("ACTIVITY")
    lines.append("-" * 60)

    if stats["pushed_dates"]:
        latest = max(stats["pushed_dates"])
        days = (datetime.now(timezone.utc) - latest).days

        lines.append(
            f"Last code push:         "
            f"{latest.strftime('%B %d, %Y')} ({days} days ago)"
        )

    lines.append(f"Repos active last 30d:  {stats['active_30']}")
    lines.append(f"Repos active last 180d: {stats['active_180']}")
    lines.append(f"Stale repositories:     {stats['stale']}")

    lines.append("")
    lines.append("TOP 10 REPOSITORIES")
    lines.append("-" * 60)

    ranked = sorted(repos, key=repository_score, reverse=True)

    for index, repo in enumerate(ranked[:10], start=1):
        lines.append(
            f"{index}. {repo.get('name')} | "
            f"Score: {repository_score(repo)} | "
            f"Stars: {repo.get('stargazers_count', 0)} | "
            f"Forks: {repo.get('forks_count', 0)}"
        )

    lines.append("")
    lines.append("PORTFOLIO SCORE")
    lines.append("-" * 60)
    lines.append(f"Portfolio score:       {portfolio_score:.1f}/100")

    return "\n".join(lines)


def main():
    username = input("Enter GitHub username: ").strip()

    if not username:
        print("Username cannot be empty.")
        return

    print("\nLoading GitHub profile...")

    data = get_json(f"{BASE_URL}/users/{username}")

    if not data:
        return

    repos = get_repositories(username)

    if repos is None:
        print("Could not load repositories.")
        return

    stats = analyze_repositories(repos)

    completed, total_fields, completeness = profile_completeness(data)

    if repos:
        health_percentage = (stats["healthy"] / len(repos)) * 100
        original_points = (
            stats["original"] / len(repos) * 100 * 0.20
        )
        activity_points = (
            stats["active_180"] / len(repos) * 100 * 0.20
        )
    else:
        health_percentage = 0
        original_points = 0
        activity_points = 0

    profile_points = completeness * 0.20
    health_points = health_percentage * 0.20
    recognition_points = min(stats["total_stars"], 100) * 0.10

    portfolio_score = (
        profile_points
        + health_points
        + original_points
        + activity_points
        + recognition_points
    )

    print_header("GITHUB PROFILE INFORMATION")

    print(f"Username:              {data.get('login')}")
    print(f"Name:                  {data.get('name') or 'None'}")
    print(f"Bio:                   {data.get('bio') or 'None'}")
    print(f"Account type:          {data.get('type')}")
    print(f"Company:               {data.get('company') or 'None'}")
    print(f"Location:              {data.get('location') or 'None'}")
    print(f"Followers:             {data.get('followers', 0)}")
    print(f"Following:             {data.get('following', 0)}")
    print(f"Public repositories:   {data.get('public_repos', 0)}")
    print(f"Public gists:          {data.get('public_gists', 0)}")
    print(f"Profile URL:           {data.get('html_url')}")

    created = parse_date(data.get("created_at"))

    if created:
        account_age_days = (
            datetime.now(timezone.utc) - created
        ).days

        print(f"Account created:       {created.strftime('%B %d, %Y')}")
        print(f"Account age:           {account_age_days / 365.25:.1f} years")

    print_header("REPOSITORY STATISTICS")

    print(f"Repositories analyzed: {len(repos)}")
    print(f"Original repositories:  {stats['original']}")
    print(f"Forked repositories:    {stats['forked']}")
    print(f"Archived repositories:  {stats['archived']}")
    print(f"Disabled repositories:  {stats['disabled']}")
    print(f"Total stars:            {stats['total_stars']}")
    print(f"Total forks:            {stats['total_forks']}")
    print(f"Total watchers:         {stats['total_watchers']}")
    print(f"Open issues:            {stats['total_issues']}")
    print(f"Total size:             {stats['total_size'] / 1024:.2f} MB")

    if repos:
        print(
            f"Average stars/repo:     "
            f"{stats['total_stars'] / len(repos):.2f}"
        )

    if stats["total_forks"] > 0:
        print(
            f"Star/Fork ratio:        "
            f"{stats['total_stars'] / stats['total_forks']:.2f}"
        )

    print_header("DEVELOPER ACTIVITY")

    if stats["pushed_dates"]:
        latest_push = max(stats["pushed_dates"])
        days_since_push = (
            datetime.now(timezone.utc) - latest_push
        ).days

        print(
            f"Last code push:         "
            f"{latest_push.strftime('%B %d, %Y')} "
            f"({days_since_push} days ago)"
        )

        if days_since_push <= 7:
            print("Activity status:        Highly Active")
        elif days_since_push <= 30:
            print("Activity status:        Active")
        elif days_since_push <= 180:
            print("Activity status:        Moderate")
        else:
            print("Activity status:        Inactive")

    print(f"Repos active last 30d:  {stats['active_30']}")
    print(f"Repos active last 180d: {stats['active_180']}")
    print(f"Stale repositories:     {stats['stale']}")

    print_header("LANGUAGE ANALYSIS")

    if stats["languages"]:
        for language, count in sorted(
            stats["languages"].items(),
            key=lambda item: item[1],
            reverse=True
        ):
            percentage = (count / len(repos)) * 100
            print(
                f"{language}:".ljust(25)
                + f"{count} repos ({percentage:.1f}%)"
            )

        main_language = max(
            stats["languages"],
            key=stats["languages"].get
        )
        print(f"\nMain language:          {main_language}")
    else:
        main_language = "Unknown"
        print("No programming languages detected.")

    print_header("LICENSE ANALYSIS")

    licensed = sum(stats["licenses"].values())
    unlicensed = len(repos) - licensed

    print(f"Licensed repositories:  {licensed}")
    print(f"Without a license:      {unlicensed}")

    for license_name, count in sorted(
        stats["licenses"].items(),
        key=lambda item: item[1],
        reverse=True
    ):
        print(f"{license_name}:".ljust(25) + f"{count} repos")

    print_header("REPOSITORY HEALTH")

    print(f"Healthy repositories:   {stats['healthy']}/{len(repos)}")
    print(f"Repository health:      {health_percentage:.0f}%")

    if health_percentage >= 80:
        print("Health status:          Excellent")
    elif health_percentage >= 60:
        print("Health status:          Good")
    elif health_percentage >= 40:
        print("Health status:          Could Improve")
    else:
        print("Health status:          Needs Work")

    print_header("TOP 10 REPOSITORIES")

    ranked_repos = sorted(
        repos,
        key=repository_score,
        reverse=True
    )

    for index, repo in enumerate(ranked_repos[:10], start=1):
        print(f"\n{index}. {repo.get('name')}")
        print(f"   Rank score:  {repository_score(repo)}")
        print(f"   Stars:       {repo.get('stargazers_count', 0)}")
        print(f"   Forks:       {repo.get('forks_count', 0)}")
        print(f"   Watchers:    {repo.get('watchers_count', 0)}")
        print(f"   Language:    {repo.get('language') or 'Unknown'}")
        print(f"   Size:        {repo.get('size', 0) / 1024:.2f} MB")
        print(f"   Archived:    {'Yes' if repo.get('archived') else 'No'}")
        print(f"   URL:         {repo.get('html_url')}")

    print_header("PORTFOLIO SCORE")

    print(f"Portfolio score:       {portfolio_score:.1f}/100")

    if portfolio_score >= 80:
        print("Portfolio level:       Excellent")
    elif portfolio_score >= 60:
        print("Portfolio level:       Strong")
    elif portfolio_score >= 40:
        print("Portfolio level:       Growing")
    else:
        print("Portfolio level:       Early Stage")

    print_header("SOCIAL METRICS")

    followers = data.get("followers", 0)
    following = data.get("following", 0)

    if following > 0:
        print(
            f"Follower/Following:    "
            f"{followers / following:.2f}"
        )
    else:
        print("Follower/Following:    N/A")

    print_header("RECENT PUBLIC ACTIVITY")

    events = get_recent_activity(username)

    if events:
        event_counts = {}

        for event in events:
            event_type = event.get("type", "Unknown")
            event_counts[event_type] = (
                event_counts.get(event_type, 0) + 1
            )

        for event_type, count in sorted(
            event_counts.items(),
            key=lambda item: item[1],
            reverse=True
        ):
            print(f"{activity_name(event_type)}: {count}")

        print(f"\nEvents analyzed:       {len(events)}")
    else:
        print("No recent public activity found.")

    print_header("QUICK IMPROVEMENT TIPS")

    tips = []

    if completeness < 100:
        tips.append("Complete more profile fields.")

    if health_percentage < 70:
        tips.append(
            "Improve repository descriptions, topics, homepages, and licenses."
        )

    if stats["stale"] > 0:
        tips.append(
            "Update or archive repositories that are no longer maintained."
        )

    if unlicensed > 0:
        tips.append(
            "Consider adding licenses to repositories you want others to use."
        )

    if stats["original"] < len(repos):
        tips.append("Build more original projects instead of relying on forks.")

    if stats["total_stars"] < 10:
        tips.append(
            "Improve project READMEs and share useful projects to gain visibility."
        )

    if not tips:
        tips.append("Profile looks solid. Keep building and shipping.")

    for tip in tips:
        print(f"- {tip}")

    print_header("REPOSITORY SEARCH")

    while True:
        search = input(
            "Search your repositories by name (or press Enter to skip): "
        ).strip().lower()

        if not search:
            break

        matches = [
            repo for repo in repos
            if search in repo.get("name", "").lower()
        ]

        if matches:
            for repo in matches:
                print(
                    f"- {repo.get('name')} | "
                    f"Stars: {repo.get('stargazers_count', 0)} | "
                    f"Forks: {repo.get('forks_count', 0)} | "
                    f"{repo.get('html_url')}"
                )
        else:
            print("No matching repositories found.")

        again = input("Search again? (y/n): ").strip().lower()
        if again != "y":
            break

    print_header("EXPORT REPORT")

    save_report = input(
        "Save the complete analysis to a text file? (y/n): "
    ).strip().lower()

    if save_report == "y":
        report_name = f"{username}_gitrank_report.txt"

        report = build_report(
            username,
            data,
            repos,
            stats,
            portfolio_score
        )

        try:
            with open(report_name, "w", encoding="utf-8") as file:
                file.write(report)

            print(f"Report saved successfully: {report_name}")

        except OSError as e:
            print(f"Could not save report: {e}")

    print_header("DONE")


if __name__ == "__main__":
    main()

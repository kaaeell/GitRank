import requests
from datetime import datetime, timezone, timedelta

# Optional Personal Access Token to avoid strict API rate limiting
GITHUB_TOKEN = ""  # Add token here if needed

username = input("Enter GitHub username: ").strip()

if not username:
    print("Username cannot be empty.")
else:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    url = f"https://api.github.com/users/{username}"

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            print("\n" + "=" * 60)
            print("                 GITHUB PROFILE INFORMATION")
            print("=" * 60)

            # -------------------------------------------------
            # BASIC PROFILE INFORMATION
            # -------------------------------------------------

            print(f"Username:              {data.get('login')}")
            print(f"Name:                  {data.get('name') or 'None'}")
            print(f"Bio:                   {data.get('bio') or 'None'}")
            print(f"Account type:          {data.get('type')}")
            print(f"Company:               {data.get('company') or 'None'}")
            print(f"Location:              {data.get('location') or 'None'}")
            print(f"Blog:                  {data.get('blog') or 'None'}")
            print(f"Twitter:               {data.get('twitter_username') or 'None'}")
            print(f"Followers:             {data.get('followers', 0)}")
            print(f"Following:             {data.get('following', 0)}")
            print(f"Public repositories:   {data.get('public_repos', 0)}")
            print(f"Public gists:          {data.get('public_gists', 0)}")
            print(f"Profile URL:           {data.get('html_url')}")

            # -------------------------------------------------
            # ACCOUNT AGE
            # -------------------------------------------------

            created_at = data.get("created_at")
            account_age_years = 0

            if created_at:
                created_date = datetime.strptime(
                    created_at,
                    "%Y-%m-%dT%H:%M:%SZ"
                ).replace(tzinfo=timezone.utc)

                account_age_days = (datetime.now(timezone.utc) - created_date).days
                account_age_years = account_age_days / 365.25

                print(f"\nAccount created:       {created_date.strftime('%B %d, %Y')}")
                print(f"Account age:           {account_age_years:.1f} years")

            # -------------------------------------------------
            # PROFILE COMPLETENESS
            # -------------------------------------------------

            profile_fields = [
                data.get("name"),
                data.get("bio"),
                data.get("company"),
                data.get("location"),
                data.get("blog"),
                data.get("twitter_username")
            ]

            completed_fields = sum(1 for field in profile_fields if field)
            completeness = (completed_fields / len(profile_fields)) * 100

            print("\n" + "-" * 60)
            print("                    PROFILE COMPLETENESS")
            print("-" * 60)

            print(f"Completed fields:      {completed_fields}/{len(profile_fields)}")
            print(f"Profile completeness:  {completeness:.0f}%")

            if completeness == 100:
                print("Profile status:        Complete")
            elif completeness >= 70:
                print("Profile status:        Well Completed")
            elif completeness >= 40:
                print("Profile status:        Could Improve")
            else:
                print("Profile status:        Basic Profile")

            # -------------------------------------------------
            # REPOSITORIES
            # -------------------------------------------------

            repos = []
            page = 1
            max_pages = 3

            while page <= max_pages:
                repos_url = f"https://api.github.com/users/{username}/repos"

                repos_response = requests.get(
                    repos_url,
                    headers=headers,
                    params={
                        "per_page": 100,
                        "sort": "updated",
                        "page": page
                    },
                    timeout=10
                )

                if repos_response.status_code == 200:
                    batch = repos_response.json()

                    if not batch:
                        break

                    repos.extend(batch)
                    page += 1
                else:
                    break

            if repos:
                total_stars = 0
                total_forks = 0
                total_watchers = 0
                total_issues = 0
                total_size = 0

                original_repos = 0
                forked_repos = 0
                archived_repos = 0
                disabled_repos = 0

                languages = {}
                healthy_repos = 0
                pushed_dates = []

                active_30_days = 0
                active_180_days = 0
                stale_repos = 0

                licenses = {}

                now = datetime.now(timezone.utc)

                for repo in repos:
                    stars = repo.get("stargazers_count", 0)
                    forks = repo.get("forks_count", 0)
                    watchers = repo.get("watchers_count", 0)
                    issues = repo.get("open_issues_count", 0)
                    size = repo.get("size", 0)

                    total_stars += stars
                    total_forks += forks
                    total_watchers += watchers
                    total_issues += issues
                    total_size += size

                    if repo.get("fork"):
                        forked_repos += 1
                    else:
                        original_repos += 1

                    if repo.get("archived"):
                        archived_repos += 1

                    if repo.get("disabled"):
                        disabled_repos += 1

                    language = repo.get("language")

                    if language:
                        languages[language] = languages.get(language, 0) + 1

                    license_name = repo.get("license", {}).get("spdx_id") if repo.get("license") else None

                    if license_name:
                        licenses[license_name] = licenses.get(license_name, 0) + 1

                    has_description = bool(repo.get("description"))
                    has_topics = len(repo.get("topics", [])) > 0
                    has_homepage = bool(repo.get("homepage"))
                    has_license = bool(repo.get("license"))

                    health_points = sum([
                        has_description,
                        has_topics,
                        has_homepage,
                        has_license
                    ])

                    if health_points >= 2:
                        healthy_repos += 1

                    pushed_at = repo.get("pushed_at")

                    if pushed_at:
                        push_date = datetime.strptime(
                            pushed_at,
                            "%Y-%m-%dT%H:%M:%SZ"
                        ).replace(tzinfo=timezone.utc)

                        pushed_dates.append(push_date)

                        days_since_push = (now - push_date).days

                        if days_since_push <= 30:
                            active_30_days += 1

                        if days_since_push <= 180:
                            active_180_days += 1
                        else:
                            stale_repos += 1

                print("\n" + "=" * 60)
                print("                    REPOSITORY STATISTICS")
                print("=" * 60)

                print(f"Repositories analyzed: {len(repos)}")
                print(f"Original repositories:  {original_repos}")
                print(f"Forked repositories:    {forked_repos}")
                print(f"Archived repositories:  {archived_repos}")
                print(f"Disabled repositories:  {disabled_repos}")
                print(f"Total stars:            {total_stars}")
                print(f"Total forks:            {total_forks}")
                print(f"Total watchers:         {total_watchers}")
                print(f"Open issues:            {total_issues}")
                print(f"Total size:             {total_size} KB")

                average_stars = total_stars / len(repos)
                print(f"Average stars/repo:     {average_stars:.2f}")

                if original_repos > 0:
                    original_star_average = total_stars / original_repos
                    print(f"Stars/original repo:    {original_star_average:.2f}")

                if total_forks > 0:
                    ratio = total_stars / total_forks
                    print(f"Star/Fork ratio:        {ratio:.2f}")
                else:
                    print("Star/Fork ratio:        N/A")

                # -------------------------------------------------
                # ACTIVITY ANALYSIS
                # -------------------------------------------------

                print("\n" + "-" * 60)
                print("                     DEVELOPER ACTIVITY")
                print("-" * 60)

                if pushed_dates:
                    latest_push = max(pushed_dates)
                    days_since_push = (now - latest_push).days

                    print(
                        f"Last code push:         "
                        f"{latest_push.strftime('%B %d, %Y')} "
                        f"({days_since_push} days ago)"
                    )

                    print(f"Repos active last 30d:  {active_30_days}")
                    print(f"Repos active last 180d: {active_180_days}")
                    print(f"Stale repositories:     {stale_repos}")

                    if days_since_push <= 7:
                        print("Activity status:        Highly Active")
                    elif days_since_push <= 30:
                        print("Activity status:        Active")
                    elif days_since_push <= 180:
                        print("Activity status:        Moderate")
                    else:
                        print("Activity status:        Inactive")

                # -------------------------------------------------
                # LANGUAGE ANALYSIS
                # -------------------------------------------------

                print("\n" + "-" * 60)
                print("                     LANGUAGE ANALYSIS")
                print("-" * 60)

                sorted_languages = []

                if languages:
                    sorted_languages = sorted(
                        languages.items(),
                        key=lambda item: item[1],
                        reverse=True
                    )

                    for language, count in sorted_languages:
                        percentage = (count / len(repos)) * 100
                        print(
                            f"{language}:".ljust(25)
                            + f"{count} repos ({percentage:.1f}%)"
                        )

                    most_used_language = sorted_languages[0][0]
                    print(f"\nMain language:          {most_used_language}")
                else:
                    most_used_language = "Unknown"
                    print("No programming languages detected.")

                # -------------------------------------------------
                # LICENSE ANALYSIS
                # -------------------------------------------------

                print("\n" + "-" * 60)
                print("                     LICENSE ANALYSIS")
                print("-" * 60)

                licensed_repos = sum(licenses.values())
                unlicensed_repos = len(repos) - licensed_repos

                print(f"Licensed repositories:  {licensed_repos}")
                print(f"Without a license:      {unlicensed_repos}")

                if licenses:
                    for license_name, count in sorted(
                        licenses.items(),
                        key=lambda item: item[1],
                        reverse=True
                    ):
                        print(f"{license_name}:".ljust(25) + f"{count} repos")
                else:
                    print("No repository licenses detected.")

                # -------------------------------------------------
                # REPOSITORY HEALTH
                # -------------------------------------------------

                print("\n" + "-" * 60)
                print("                     REPOSITORY HEALTH")
                print("-" * 60)

                health_percentage = (healthy_repos / len(repos)) * 100

                print(f"Healthy repositories:   {healthy_repos}/{len(repos)}")
                print(f"Repository health:      {health_percentage:.0f}%")

                if health_percentage >= 80:
                    print("Health status:          Excellent")
                elif health_percentage >= 60:
                    print("Health status:          Good")
                elif health_percentage >= 40:
                    print("Health status:          Could Improve")
                else:
                    print("Health status:          Needs Work")

                # -------------------------------------------------
                # TOP 5 REPOSITORIES
                # -------------------------------------------------

                sorted_repos = sorted(
                    repos,
                    key=lambda repo: (
                        repo.get("stargazers_count", 0)
                        + repo.get("forks_count", 0)
                    ),
                    reverse=True
                )

                print("\n" + "-" * 60)
                print("                    TOP 5 REPOSITORIES")
                print("-" * 60)

                for index, repo in enumerate(sorted_repos[:5], start=1):
                    print(f"\n{index}. {repo.get('name')}")
                    print(f"   Stars:       {repo.get('stargazers_count', 0)}")
                    print(f"   Forks:       {repo.get('forks_count', 0)}")
                    print(f"   Watchers:    {repo.get('watchers_count', 0)}")
                    print(f"   Language:    {repo.get('language') or 'Unknown'}")
                    print(f"   Archived:    {'Yes' if repo.get('archived') else 'No'}")
                    print(
                        f"   Description: "
                        f"{repo.get('description') or 'None'}"
                    )
                    print(f"   URL:         {repo.get('html_url')}")

                # -------------------------------------------------
                # RECENTLY UPDATED REPOSITORIES
                # -------------------------------------------------

                print("\n" + "-" * 60)
                print("                RECENTLY UPDATED REPOSITORIES")
                print("-" * 60)

                recent_repos = sorted(
                    repos,
                    key=lambda repo: repo.get("updated_at", ""),
                    reverse=True
                )

                for repo in recent_repos[:5]:
                    updated = repo.get("updated_at")

                    if updated:
                        updated_date = datetime.strptime(
                            updated,
                            "%Y-%m-%dT%H:%M:%SZ"
                        ).strftime("%Y-%m-%d")
                    else:
                        updated_date = "Unknown"

                    print(
                        f"{repo.get('name')}:".ljust(30)
                        + updated_date
                    )

                # -------------------------------------------------
                # BEST REPOSITORY
                # -------------------------------------------------

                best_repo = max(
                    repos,
                    key=lambda repo: (
                        repo.get("stargazers_count", 0)
                        + repo.get("forks_count", 0)
                    )
                )

                print("\n" + "-" * 60)
                print("                     BEST REPOSITORY")
                print("-" * 60)

                print(f"Name:                  {best_repo.get('name')}")
                print(f"Stars:                 {best_repo.get('stargazers_count', 0)}")
                print(f"Forks:                 {best_repo.get('forks_count', 0)}")
                print(f"Watchers:              {best_repo.get('watchers_count', 0)}")
                print(f"Language:              {best_repo.get('language') or 'Unknown'}")
                print(f"Repository URL:        {best_repo.get('html_url')}")

                # -------------------------------------------------
                # FOLLOWER / FOLLOWING RATIO
                # -------------------------------------------------

                followers = data.get("followers", 0)
                following = data.get("following", 0)

                print("\n" + "-" * 60)
                print("                   SOCIAL METRICS")
                print("-" * 60)

                if following > 0:
                    follower_ratio = followers / following
                    print(f"Follower/Following:    {follower_ratio:.2f}")
                else:
                    print("Follower/Following:    N/A")

                # -------------------------------------------------
                # GITHUB SCORE
                # -------------------------------------------------

                score = (
                    followers
                    + following
                    + data.get("public_repos", 0) * 2
                    + total_stars * 3
                    + total_forks * 2
                    + total_watchers
                )

                print("\n" + "=" * 60)
                print("                      GITHUB SCORE")
                print("=" * 60)

                print(f"GitHub score:          {score}")

                if score >= 1000:
                    level = "Very Active"
                elif score >= 500:
                    level = "Active Developer"
                elif score >= 100:
                    level = "Growing Developer"
                else:
                    level = "Beginner / New Account"

                print(f"Developer level:       {level}")

                # -------------------------------------------------
                # PORTFOLIO SCORE
                # -------------------------------------------------
                # This is a separate 100-point score based on
                # profile completeness, repository health, activity,
                # original work, and community recognition.

                profile_points = completeness * 0.20
                health_points = health_percentage * 0.20

                if len(repos) > 0:
                    original_points = (original_repos / len(repos)) * 100 * 0.20
                    activity_points = (active_180_days / len(repos)) * 100 * 0.20
                else:
                    original_points = 0
                    activity_points = 0

                recognition_base = min(total_stars, 100) * 0.10

                portfolio_score = (
                    profile_points
                    + health_points
                    + original_points
                    + activity_points
                    + recognition_base
                )

                print("\n" + "=" * 60)
                print("                    PORTFOLIO SCORE")
                print("=" * 60)

                print(f"Portfolio score:       {portfolio_score:.1f}/100")

                if portfolio_score >= 80:
                    print("Portfolio level:       Excellent")
                elif portfolio_score >= 60:
                    print("Portfolio level:       Strong")
                elif portfolio_score >= 40:
                    print("Portfolio level:       Growing")
                else:
                    print("Portfolio level:       Early Stage")

                # -------------------------------------------------
                # QUICK IMPROVEMENT TIPS
                # -------------------------------------------------

                print("\n" + "-" * 60)
                print("                  QUICK IMPROVEMENT TIPS")
                print("-" * 60)

                tips = []

                if completeness < 100:
                    tips.append("Complete more profile fields.")

                if health_percentage < 70:
                    tips.append("Improve repository descriptions, topics, homepages, and licenses.")

                if stale_repos > 0:
                    tips.append("Update or archive old repositories that are no longer maintained.")

                if unlicensed_repos > 0:
                    tips.append("Consider adding licenses to repositories you want others to use.")

                if original_repos < len(repos):
                    tips.append("Build more original projects instead of relying on forks.")

                if total_stars < 10:
                    tips.append("Improve project READMEs and share useful projects to gain visibility.")

                if not tips:
                    tips.append("Profile looks solid. Keep building and shipping.")

                for tip in tips:
                    print(f"- {tip}")

                # -------------------------------------------------
                # DEVELOPER SUMMARY
                # -------------------------------------------------

                print("\n" + "-" * 60)
                print("                    DEVELOPER SUMMARY")
                print("-" * 60)

                if followers >= 100:
                    audience = "has a strong GitHub audience"
                elif followers >= 20:
                    audience = "has a growing GitHub audience"
                else:
                    audience = "is still building a GitHub audience"

                if total_stars >= 100:
                    popularity = "has highly popular repositories"
                elif total_stars >= 10:
                    popularity = "has some repository recognition"
                else:
                    popularity = "is still building repository recognition"

                print(
                    f"{username} {audience} and {popularity}."
                )

                if languages:
                    print(
                        f"Main technical focus appears to be "
                        f"{most_used_language}."
                    )

                print(
                    f"The account contains {len(repos)} analyzed repositories."
                )

                # -------------------------------------------------
                # EXPORT REPORT
                # -------------------------------------------------

                save_report = input(
                    "\nSave this analysis to a text file? (y/n): "
                ).strip().lower()

                if save_report == "y":
                    report_name = f"{username}_gitrank_report.txt"

                    print(
                        f"Report filename: {report_name}"
                    )

                    print(
                        "\nNote: automatic report exporting will be added "
                        "in the next version."
                    )

            else:
                print("\nCould not load repositories.")

            print("\n" + "=" * 60)
            print("                         DONE")
            print("=" * 60)

        elif response.status_code == 404:
            print("GitHub user not found.")
        elif response.status_code == 403:
            print(
                "GitHub API rate limit exceeded. "
                "Consider adding an API token."
            )
        elif response.status_code >= 500:
            print("GitHub server error.")
        else:
            print(
                f"Request failed. Status code: "
                f"{response.status_code}"
            )

    except requests.exceptions.Timeout:
        print("Request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
    except ValueError:
        print("Could not process GitHub data.")

import requests
from datetime import datetime

username = input("Enter GitHub username: ").strip()

if not username:
    print("Username cannot be empty.")

else:
    url = f"https://api.github.com/users/{username}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            print("\n" + "=" * 55)
            print("          GITHUB PROFILE INFORMATION")
            print("=" * 55)

            # Basic profile information
            print(f"Username:              {data.get('login')}")
            print(f"Name:                  {data.get('name')}")
            print(f"Bio:                   {data.get('bio')}")
            print(f"Account type:          {data.get('type')}")
            print(f"Company:               {data.get('company')}")
            print(f"Location:              {data.get('location')}")
            print(f"Blog:                  {data.get('blog')}")
            print(f"Twitter:               {data.get('twitter_username')}")
            print(f"Followers:             {data.get('followers')}")
            print(f"Following:             {data.get('following')}")
            print(f"Public repositories:   {data.get('public_repos')}")
            print(f"Public gists:          {data.get('public_gists')}")
            print(f"Profile URL:           {data.get('html_url')}")

            # Account creation date
            created_at = data.get("created_at")

            if created_at:
                created_date = datetime.strptime(
                    created_at,
                    "%Y-%m-%dT%H:%M:%SZ"
                )

                formatted_date = created_date.strftime(
                    "%B %d, %Y"
                )

                account_age_days = (
                    datetime.utcnow() - created_date
                ).days

                account_age_years = account_age_days / 365.25

                print(f"Account created:       {formatted_date}")
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

            completed_fields = sum(
                1 for field in profile_fields if field
            )

            completeness = (
                completed_fields / len(profile_fields)
            ) * 100

            print("\n" + "-" * 55)
            print("                 PROFILE COMPLETENESS")
            print("-" * 55)

            print(f"Completed fields:      {completed_fields}/{len(profile_fields)}")
            print(f"Profile completeness:  {completeness:.0f}%")

            if completeness == 100:
                print("Profile status:        🏆 Complete")
            elif completeness >= 70:
                print("Profile status:        ⭐ Well Completed")
            elif completeness >= 40:
                print("Profile status:        📈 Could Improve")
            else:
                print("Profile status:        🌱 Basic Profile")

            # -------------------------------------------------
            # REPOSITORIES
            # -------------------------------------------------

            repos_url = f"https://api.github.com/users/{username}/repos"

            repos_response = requests.get(
                repos_url,
                params={
                    "per_page": 100,
                    "sort": "updated"
                },
                timeout=10
            )

            if repos_response.status_code == 200:

                repos = repos_response.json()

                total_stars = 0
                total_forks = 0
                total_watchers = 0
                total_issues = 0
                total_size = 0

                original_repos = 0
                forked_repos = 0

                languages = {}

                healthy_repos = 0

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

                    # Original vs fork
                    if repo.get("fork"):
                        forked_repos += 1
                    else:
                        original_repos += 1

                    # Languages
                    language = repo.get("language")

                    if language:
                        languages[language] = (
                            languages.get(language, 0) + 1
                        )

                    # Repository health
                    has_description = bool(repo.get("description"))
                    has_topics = len(repo.get("topics", [])) > 0
                    has_homepage = bool(repo.get("homepage"))

                    health_points = sum([
                        has_description,
                        has_topics,
                        has_homepage
                    ])

                    if health_points >= 2:
                        healthy_repos += 1

                print("\n" + "=" * 55)
                print("                 REPOSITORY STATISTICS")
                print("=" * 55)

                print(f"Repositories analyzed: {len(repos)}")
                print(f"Original repositories: {original_repos}")
                print(f"Forked repositories:   {forked_repos}")
                print(f"Total stars:           {total_stars}")
                print(f"Total forks:           {total_forks}")
                print(f"Total watchers:        {total_watchers}")
                print(f"Open issues:           {total_issues}")
                print(f"Total size:            {total_size} KB")

                if repos:
                    average_stars = total_stars / len(repos)

                    print(
                        f"Average stars/repo:    "
                        f"{average_stars:.2f}"
                    )

                # Star / fork ratio
                if total_forks > 0:
                    ratio = total_stars / total_forks
                    print(f"Star/Fork ratio:       {ratio:.2f}")
                else:
                    print("Star/Fork ratio:       N/A")

                # -------------------------------------------------
                # MOST USED LANGUAGE
                # -------------------------------------------------

                print("\n" + "-" * 55)
                print("                 LANGUAGE ANALYSIS")
                print("-" * 55)

                if languages:

                    sorted_languages = sorted(
                        languages.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )

                    for language, count in sorted_languages:
                        print(f"{language}:".ljust(25) + f"{count} repos")

                    most_used_language = sorted_languages[0][0]

                    print(
                        f"\nMain language:         "
                        f"{most_used_language}"
                    )

                else:
                    print("No programming languages detected.")

                # -------------------------------------------------
                # REPOSITORY HEALTH
                # -------------------------------------------------

                print("\n" + "-" * 55)
                print("                 REPOSITORY HEALTH")
                print("-" * 55)

                if repos:
                    health_percentage = (
                        healthy_repos / len(repos)
                    ) * 100

                    print(
                        f"Healthy repositories:  "
                        f"{healthy_repos}/{len(repos)}"
                    )

                    print(
                        f"Repository health:     "
                        f"{health_percentage:.0f}%"
                    )

                # -------------------------------------------------
                # TOP 3 REPOSITORIES
                # -------------------------------------------------

                sorted_repos = sorted(
                    repos,
                    key=lambda repo: (
                        repo.get("stargazers_count", 0)
                        + repo.get("forks_count", 0)
                    ),
                    reverse=True
                )

                print("\n" + "-" * 55)
                print("                  TOP 3 REPOSITORIES")
                print("-" * 55)

                for index, repo in enumerate(
                    sorted_repos[:3],
                    start=1
                ):

                    print(f"\n{index}. {repo.get('name')}")
                    print(
                        f"   ⭐ Stars:       "
                        f"{repo.get('stargazers_count', 0)}"
                    )
                    print(
                        f"   🍴 Forks:       "
                        f"{repo.get('forks_count', 0)}"
                    )
                    print(
                        f"   👀 Watchers:    "
                        f"{repo.get('watchers_count', 0)}"
                    )
                    print(
                        f"   💻 Language:    "
                        f"{repo.get('language') or 'Unknown'}"
                    )
                    print(
                        f"   📝 Description: "
                        f"{repo.get('description') or 'None'}"
                    )
                    print(
                        f"   🔗 URL:         "
                        f"{repo.get('html_url')}"
                    )

                # -------------------------------------------------
                # RECENTLY UPDATED REPOSITORIES
                # -------------------------------------------------

                print("\n" + "-" * 55)
                print("             RECENTLY UPDATED REPOSITORIES")
                print("-" * 55)

                recent_repos = sorted(
                    repos,
                    key=lambda repo: repo.get(
                        "updated_at", ""
                    ),
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
                        f"{repo.get('name')}: "
                        f"{updated_date}"
                    )

                # -------------------------------------------------
                # BEST REPOSITORY
                # -------------------------------------------------

                if repos:

                    best_repo = max(
                        repos,
                        key=lambda repo: (
                            repo.get("stargazers_count", 0)
                        )
                    )

                    print("\n" + "-" * 55)
                    print("                  BEST REPOSITORY")
                    print("-" * 55)

                    print(
                        f"Name:                  "
                        f"{best_repo.get('name')}"
                    )

                    print(
                        f"Stars:                 "
                        f"{best_repo.get('stargazers_count', 0)}"
                    )

                    print(
                        f"Forks:                 "
                        f"{best_repo.get('forks_count', 0)}"
                    )

                    print(
                        f"Language:              "
                        f"{best_repo.get('language') or 'Unknown'}"
                    )

                    print(
                        f"Repository URL:        "
                        f"{best_repo.get('html_url')}"
                    )

                # -------------------------------------------------
                # GITHUB SCORE
                # -------------------------------------------------

                score = (
                    data.get("followers", 0)
                    + data.get("following", 0)
                    + data.get("public_repos", 0) * 2
                    + total_stars * 3
                    + total_forks * 2
                    + total_watchers
                )

                print("\n" + "=" * 55)
                print("                    GITHUB SCORE")
                print("=" * 55)

                print(f"GitHub score:          {score}")

                if score >= 1000:
                    level = "🔥 Very Active"
                elif score >= 500:
                    level = "🚀 Active Developer"
                elif score >= 100:
                    level = "💻 Growing Developer"
                else:
                    level = "🌱 Beginner / New Account"

                print(f"Developer level:       {level}")

                # -------------------------------------------------
                # DEVELOPER SUMMARY
                # -------------------------------------------------

                print("\n" + "-" * 55)
                print("                 DEVELOPER SUMMARY")
                print("-" * 55)

                if data.get("followers", 0) >= 100:
                    audience = "has a strong GitHub audience"
                elif data.get("followers", 0) >= 20:
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
                    f"The account contains "
                    f"{len(repos)} analyzed repositories."
                )

            else:
                print("\nCould not load repositories.")

            print("\n" + "=" * 55)
            print("                    DONE")
            print("=" * 55)

        elif response.status_code == 404:
            print("GitHub user not found.")

        elif response.status_code == 403:
            print("GitHub API rate limit exceeded.")

        elif response.status_code >= 500:
            print("GitHub server error.")

        else:
            print(
                f"Request failed. "
                f"Status code: {response.status_code}"
            )

    except requests.exceptions.Timeout:
        print("Request timed out. Please try again.")

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")

    except ValueError:
        print("Could not process GitHub data.")
import requests
from datetime import datetime

username = input("Enter GitHub username: ").strip()

if not username:
    print("Username cannot be empty.")

else:
    url = f"https://api.github.com/users/{username}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            print("\n" + "=" * 55)
            print("             GITHUB PROFILE INFORMATION")
            print("=" * 55)

            # Basic profile information
            print(f"Username:              {data.get('login')}")
            print(f"Name:                  {data.get('name')}")
            print(f"Bio:                   {data.get('bio')}")
            print(f"Account type:          {data.get('type')}")
            print(f"Followers:             {data.get('followers')}")
            print(f"Following:             {data.get('following')}")
            print(f"Public repositories:   {data.get('public_repos')}")
            print(f"Public gists:          {data.get('public_gists')}")
            print(f"Profile URL:           {data.get('html_url')}")

            # Account creation date
            created_at = data.get("created_at")

            if created_at:
                date = datetime.strptime(
                    created_at, "%Y-%m-%dT%H:%M:%SZ"
                ).strftime("%B %d, %Y")

                print(f"Account created:       {date}")

                # Calculate account age
                created_date = datetime.strptime(
                    created_at, "%Y-%m-%dT%H:%M:%SZ"
                )

                age_days = (datetime.now() - created_date).days
                age_years = age_days / 365.25

                print(f"Account age:           {age_years:.1f} years")

            # Get repositories
            repos_url = f"https://api.github.com/users/{username}/repos"

            repos_response = requests.get(
                repos_url,
                params={
                    "per_page": 100,
                    "sort": "stars"
                }
            )

            if repos_response.status_code == 200:

                repos = repos_response.json()

                total_stars = 0
                total_forks = 0

                best_repo = None
                oldest_repo = None
                newest_repo = None

                languages = {}

                for repo in repos:

                    stars = repo.get("stargazers_count", 0)
                    forks = repo.get("forks_count", 0)

                    total_stars += stars
                    total_forks += forks

                    # Best repository
                    if best_repo is None or stars > best_repo.get(
                        "stargazers_count", 0
                    ):
                        best_repo = repo

                    # Oldest repository
                    if oldest_repo is None or repo.get(
                        "created_at", ""
                    ) < oldest_repo.get("created_at", ""):
                        oldest_repo = repo

                    # Newest repository
                    if newest_repo is None or repo.get(
                        "created_at", ""
                    ) > newest_repo.get("created_at", ""):
                        newest_repo = repo

                    # Programming languages
                    language = repo.get("language")

                    if language:
                        languages[language] = languages.get(language, 0) + 1

                print("\n" + "=" * 55)
                print("                GITHUB STATISTICS")
                print("=" * 55)

                print(f"Repositories analyzed: {len(repos)}")
                print(f"Total stars:           {total_stars}")
                print(f"Total forks:           {total_forks}")

                # Average stars
                if repos:
                    average_stars = total_stars / len(repos)
                    print(f"Average stars/repo:    {average_stars:.2f}")

                # Star/Fork ratio
                if total_forks > 0:
                    ratio = total_stars / total_forks
                    print(f"Star/Fork ratio:       {ratio:.2f}")
                else:
                    print("Star/Fork ratio:       N/A")

                # Most-used language
                if languages:
                    most_used_language = max(
                        languages,
                        key=languages.get
                    )

                    print(
                        f"Most-used language:    "
                        f"{most_used_language} "
                        f"({languages[most_used_language]} repos)"
                    )
                else:
                    print("Most-used language:    Unknown")

                # Top 3 repositories
                sorted_repos = sorted(
                    repos,
                    key=lambda repo: repo.get("stargazers_count", 0),
                    reverse=True
                )

                print("\n" + "-" * 55)
                print("                 TOP 3 REPOSITORIES")
                print("-" * 55)

                for index, repo in enumerate(sorted_repos[:3], start=1):

                    print(f"\n{index}. {repo.get('name')}")
                    print(
                        f"   ⭐ Stars: {repo.get('stargazers_count', 0)}"
                    )
                    print(
                        f"   🍴 Forks: {repo.get('forks_count', 0)}"
                    )
                    print(
                        f"   💻 Language: "
                        f"{repo.get('language') or 'Unknown'}"
                    )
                    print(
                        f"   📝 Description: "
                        f"{repo.get('description') or 'No description'}"
                    )
                    print(
                        f"   🔗 URL: {repo.get('html_url')}"
                    )

                # Best repository
                if best_repo:

                    print("\n" + "-" * 55)
                    print("                  BEST REPOSITORY")
                    print("-" * 55)

                    print(f"Name:                  {best_repo.get('name')}")
                    print(
                        f"Stars:                 "
                        f"{best_repo.get('stargazers_count')}"
                    )
                    print(
                        f"Forks:                 "
                        f"{best_repo.get('forks_count')}"
                    )
                    print(
                        f"Language:              "
                        f"{best_repo.get('language') or 'Unknown'}"
                    )
                    print(
                        f"Description:           "
                        f"{best_repo.get('description') or 'No description'}"
                    )
                    print(
                        f"Repository URL:        "
                        f"{best_repo.get('html_url')}"
                    )

                # Oldest repository
                if oldest_repo:

                    oldest_date = datetime.strptime(
                        oldest_repo.get("created_at"),
                        "%Y-%m-%dT%H:%M:%SZ"
                    ).strftime("%B %d, %Y")

                    print("\n" + "-" * 55)
                    print("                  OLDEST REPOSITORY")
                    print("-" * 55)

                    print(f"Name:                  {oldest_repo.get('name')}")
                    print(f"Created:               {oldest_date}")
                    print(f"URL:                   {oldest_repo.get('html_url')}")

                # Newest repository
                if newest_repo:

                    newest_date = datetime.strptime(
                        newest_repo.get("created_at"),
                        "%Y-%m-%dT%H:%M:%SZ"
                    ).strftime("%B %d, %Y")

                    print("\n" + "-" * 55)
                    print("                  NEWEST REPOSITORY")
                    print("-" * 55)

                    print(f"Name:                  {newest_repo.get('name')}")
                    print(f"Created:               {newest_date}")
                    print(f"URL:                   {newest_repo.get('html_url')}")

                # GitHub score
                score = (
                    data.get("followers", 0)
                    + data.get("following", 0)
                    + data.get("public_repos", 0) * 2
                    + total_stars * 3
                    + total_forks * 2
                )

                print("\n" + "=" * 55)
                print("                  GITHUB SCORE")
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

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
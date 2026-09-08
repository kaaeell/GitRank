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

            print("\n" + "=" * 45)
            print("        GITHUB PROFILE INFORMATION")
            print("=" * 45)

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

                for repo in repos:
                    stars = repo.get("stargazers_count", 0)
                    forks = repo.get("forks_count", 0)

                    total_stars += stars
                    total_forks += forks

                    # Find best repository
                    if best_repo is None or stars > best_repo.get(
                        "stargazers_count", 0
                    ):
                        best_repo = repo

                print("\n" + "=" * 45)
                print("           GITHUB STATISTICS")
                print("=" * 45)

                print(f"Total stars:           {total_stars}")
                print(f"Total forks:           {total_forks}")

                # Best repository
                if best_repo:
                    print(f"\nBest repository:       {best_repo.get('name')}")
                    print(f"Best repo stars:       {best_repo.get('stargazers_count')}")
                    print(f"Best repo forks:       {best_repo.get('forks_count')}")
                    print(f"Repository URL:        {best_repo.get('html_url')}")

                # Simple GitHub score
                score = (
                    data.get("followers", 0)
                    + data.get("following", 0)
                    + data.get("public_repos", 0) * 2
                    + total_stars * 3
                    + total_forks * 2
                )

                print(f"\nGitHub score:          {score}")

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

            print("\n" + "=" * 45)

        elif response.status_code == 404:
            print("GitHub user not found.")

        elif response.status_code == 403:
            print("GitHub API rate limit exceeded.")

        elif response.status_code >= 500:
            print("GitHub server error.")

        else:
            print(f"Request failed. Status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
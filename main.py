Yeah bro 😭 I’ll keep the project basically the same and just add a few small upgrades—no turning it into a whole different project.

Added:

* 🔗 Repository URLs
* 📅 Repository creation dates
* 🍴 Total forks across all displayed repos
* 🧑‍💻 Account type (User/Organization)
* 📝 Public/private-looking profile info
* ⭐ Best repo among the 3
* 📈 Simple GitHub “score”
* ⏱️ Request timeout so it doesn’t hang forever
* Better handling for network errors

import requests
from datetime import datetime
import time
import random
print("Hello! Let me fetch a GitHub profile for you.")
username = input("Enter GitHub username: ").strip()
if not username:
    print("Oh, you didn't enter a username. That's okay, try again next time.")
else:
    url = f"https://api.github.com/users/{username}"
    print(f"\nLooking up {username} on GitHub...")
    time.sleep(0.5)
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("\n" + "=" * 44)
            print("            GITHUB PROFILE")
            print("=" * 44)
            print(f"Username:        {data['login']}")
            print(f"Name:            {data['name'] or 'Not provided'}")
            print(f"Location:        {data['location'] or 'Not provided'}")
            print(f"Email:           {data['email'] or 'Not provided'}")
            print(f"Followers:       {data['followers']}")
            print(f"Following:       {data['following']}")
            print(f"Public repos:    {data['public_repos']}")
            print(f"Public gists:    {data['public_gists']}")
            print(f"Account type:    {data['type']}")
            print(f"Profile:         {data['html_url']}")
            print(f"Avatar:          {data['avatar_url']}")
            # Account information
            created_at = datetime.strptime(
                data['created_at'],
                "%Y-%m-%dT%H:%M:%SZ"
            )
            print(f"Joined GitHub:   {created_at.strftime('%B %d, %Y')}")
            print(f"Joined in:       {created_at.year}")
            days_old = (datetime.utcnow() - created_at).days
            years = days_old // 365
            months = (days_old % 365) // 30
            days_remaining = (days_old % 365) % 30
            print(
                f"Member for:      {years} years, "
                f"{months} months, and {days_remaining} days"
            )
            months_old = days_old // 30
            print(f"Account age:     {months_old} months")
            # Optional profile information
            if data['bio']:
                print(f"Bio:             {data['bio']}")
            if data['company']:
                print(f"Company:         {data['company']}")
            if data['blog']:
                print(f"Website:         {data['blog']}")
            if data.get('twitter_username'):
                print(f"Twitter:         @{data['twitter_username']}")
            hireable = "Yes" if data['hireable'] else "No"
            print(f"Open to hiring:  {hireable}")
            # Profile completeness
            profile_fields = [
                data['name'],
                data['bio'],
                data['location'],
                data['company']
            ]
            filled_fields = sum(1 for field in profile_fields if field)
            completeness = int((filled_fields / 4) * 100)
            print(f"Profile complete: {completeness}%")
            # Activity description
            if data['public_repos'] == 0:
                print("Activity:        No public repositories")
            elif data['public_repos'] < 5:
                print("Activity:        Getting started")
            elif data['public_repos'] < 20:
                print("Activity:        Building a portfolio")
            else:
                print("Activity:        Very active portfolio")
            # Account status
            if days_old < 30:
                print("Status:          New to GitHub! Welcome!")
            elif days_old < 365:
                print("Status:          Active community member")
            else:
                print("Status:          Seasoned GitHub veteran")
            # Day they joined
            joined_day = created_at.strftime('%A')
            print(f"Joined on:       {joined_day}")
            print("=" * 44)
            # GitHub score
            github_score = (
                data['followers'] * 2
                + data['public_repos'] * 3
                + data['public_gists']
                + data['following']
            )
            print(f"GitHub score:    {github_score}")
            if github_score >= 5000:
                print("   Level:        🚀 GitHub Legend")
            elif github_score >= 1000:
                print("   Level:        ⭐ Advanced")
            elif github_score >= 300:
                print("   Level:        🔥 Rising Developer")
            else:
                print("   Level:        🌱 Beginner")
            # Latest repositories
            print("\nChecking their latest repositories...")
            time.sleep(0.3)
            repos_url = data['repos_url']
            repos_response = requests.get(
                repos_url + "?sort=updated&per_page=3",
                timeout=10
            )
            if repos_response.status_code == 200:
                repos = repos_response.json()
                if repos:
                    total_stars = sum(
                        repo['stargazers_count']
                        for repo in repos
                    )
                    total_forks = sum(
                        repo['forks_count']
                        for repo in repos
                    )
                    languages_used = set(
                        repo['language']
                        for repo in repos
                        if repo['language']
                    )
                    print(
                        "\nHere are their 3 most recently "
                        "updated projects:"
                    )
                    print(
                        f"   Total stars across these: "
                        f"{total_stars}"
                    )
                    print(
                        f"   Total forks across these: "
                        f"{total_forks}"
                    )
                    average_stars = total_stars / len(repos)
                    print(
                        f"   Average stars: "
                        f"{average_stars:.1f}"
                    )
                    if languages_used:
                        print(
                            f"   Languages used: "
                            f"{', '.join(sorted(languages_used))}"
                        )
                    # Find best repository
                    best_repo = max(
                        repos,
                        key=lambda repo: repo['stargazers_count']
                    )
                    print(
                        f"   ⭐ Most starred: "
                        f"{best_repo['name']}"
                    )
                    print()
                    for i, repo in enumerate(repos, 1):
                        stars = repo['stargazers_count']
                        forks = repo['forks_count']
                        language = repo['language'] or "Not specified"
                        watchers = repo['watchers_count']
                        print(f"Project {i}: {repo['name']}")
                        print(
                            f"   Stars: {stars}   "
                            f"Forks: {forks}   "
                            f"Watchers: {watchers}"
                        )
                        print(f"   Language: {language}")
                        # Repository size
                        size_mb = repo['size'] / 1024
                        print(
                            f"   Size: {size_mb:.2f} MB"
                        )
                        # Repository creation date
                        repo_created = datetime.strptime(
                            repo['created_at'],
                            "%Y-%m-%dT%H:%M:%SZ"
                        )
                        print(
                            f"   Created: "
                            f"{repo_created.strftime('%B %d, %Y')}"
                        )
                        # Repository URL
                        print(
                            f"   URL: {repo['html_url']}"
                        )
                        # Description
                        if repo['description']:
                            desc = repo['description']
                            if len(desc) > 60:
                                desc = desc[:60] + "..."
                            print(
                                f"   Description: {desc}"
                            )
                        # Archived status
                        if repo['archived']:
                            print("   Status: ARCHIVED")
                        else:
                            print("   Status: Active")
                        # Visibility
                        if repo['private']:
                            print("   Visibility: Private")
                        else:
                            print("   Visibility: Public")
                        # Open issues
                        if repo['open_issues_count'] > 0:
                            print(
                                f"   Open issues: "
                                f"{repo['open_issues_count']}"
                            )
                        # Last update
                        updated = datetime.strptime(
                            repo['updated_at'],
                            "%Y-%m-%dT%H:%M:%SZ"
                        )
                        days_since = (
                            datetime.utcnow() - updated
                        ).days
                        if days_since == 0:
                            print("   Updated: today!")
                        elif days_since == 1:
                            print("   Updated: yesterday")
                        else:
                            print(
                                f"   Updated: "
                                f"{days_since} days ago"
                            )
                        print("-" * 44)
                else:
                    print(
                        "This user doesn't have any public "
                        "repositories yet."
                    )
                    print(
                        "Maybe they're new to GitHub or prefer "
                        "to keep things private."
                    )
            else:
                print(
                    "Hmm, couldn't fetch their repository data "
                    "at the moment."
                )
                print(
                    "The GitHub API might be a bit slow right now."
                )
            # Follower-to-following ratio
            if data['followers'] > 0 and data['following'] > 0:
                ratio = data['followers'] / data['following']
                print("\nSocial ratio:")
                print(
                    f"   Followers/Following: "
                    f"{ratio:.2f}"
                )
                if ratio > 10:
                    print(
                        "   Note: This user has many more "
                        "followers than people they follow."
                    )
                elif ratio < 0.1:
                    print(
                        "   Note: This user follows many more "
                        "people than follow them."
                    )
            # Follower category
            if data['followers'] >= 1000:
                print("🔥 Popular GitHub profile!")
            elif data['followers'] >= 100:
                print("⭐ Growing GitHub profile!")
            else:
                print(
                    "🌱 Still building their GitHub audience."
                )
            # Average repositories per year
            if years > 0:
                repos_per_year = (
                    data['public_repos'] / years
                )
                if repos_per_year > 20:
                    print(
                        f"📊 Very productive: "
                        f"{repos_per_year:.1f} repos per year"
                    )
                elif repos_per_year > 5:
                    print(
                        f"📊 Moderately productive: "
                        f"{repos_per_year:.1f} repos per year"
                    )
                else:
                    print(
                        f"📊 Taking it slow: "
                        f"{repos_per_year:.1f} repos per year"
                    )
            # Random GitHub fact
            facts = [
                "GitHub was launched in 2008.",
                "The name 'GitHub' combines 'Git' and 'hub'.",
                "GitHub was acquired by Microsoft in 2018.",
                "GitHub uses the Octocat as its mascot.",
                "GitHub Actions was introduced in 2019.",
                "The Octocat has many different versions.",
                "GitHub hosts millions of open-source projects."
            ]
            print("\n" + "=" * 44)
            print(
                f"Did you know? {random.choice(facts)}"
            )
            print("=" * 44)
        elif response.status_code == 404:
            print(
                f"Sorry, I couldn't find a GitHub user "
                f"named '{username}'."
            )
            print(
                "Check for typos or try a different username."
            )
            print("\nPopular GitHub users to try:")
            popular_users = [
                "octocat",
                "torvalds",
                "google",
                "microsoft",
                "facebook"
            ]
            for user in popular_users:
                print(f"  - {user}")
        elif response.status_code == 403:
            print("⚠️ GitHub API rate limit exceeded.")
            print("Wait a little while and try again.")
        elif response.status_code == 500:
            print("⚠️ GitHub's servers might be having issues.")
            print("Try again later.")
        else:
            print(
                f"Oops, something went wrong. "
                f"Status code: {response.status_code}"
            )
    except requests.exceptions.Timeout:
        print("⚠️ The request took too long.")
        print("Check your internet connection and try again.")
    except requests.exceptions.ConnectionError:
        print("⚠️ Couldn't connect to GitHub.")
        print("Check your internet connection.")
    except requests.exceptions.RequestException as error:
        print(f"⚠️ Something went wrong: {error}")
print("\nThanks for using the GitHub profile viewer!")
print("Have a great day!")
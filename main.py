import requests
from datetime import datetime
import time
import random

print("Hello! Let me fetch a GitHub profile for you.")
username = input("Enter GitHub username: ")

if not username:
    print("Oh, you didn't enter a username. That's okay, try again next time.")
else:
    url = f"https://api.github.com/users/{username}"
    print(f"\nLooking up {username} on GitHub...")
    time.sleep(0.5)
    
    response = requests.get(url)

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
        
        created_at = datetime.strptime(data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        print(f"Joined GitHub:   {created_at.strftime('%B %d, %Y')}")
        
        days_old = (datetime.now() - created_at).days
        years = days_old // 365
        months = (days_old % 365) // 30
        days_remaining = (days_old % 365) % 30
        print(f"Member for:      {years} years, {months} months, and {days_remaining} days")
        
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
        
        profile_fields = [data['name'], data['bio'], data['location'], data['company']]
        filled_fields = sum(1 for field in profile_fields if field)
        completeness = int((filled_fields / 4) * 100)
        print(f"Profile complete: {completeness}%")
        
        # Check if account is recent
        if days_old < 30:
            print("Status:          New to GitHub! Welcome!")
        elif days_old < 365:
            print("Status:          Active community member")
        else:
            print("Status:          Seasoned GitHub veteran")
        
        print("=" * 44)
        
        # Let's also check out their recent work
        print("\nChecking their latest repositories...")
        time.sleep(0.3)
        
        repos_url = data['repos_url']
        repos_response = requests.get(repos_url + "?sort=updated&per_page=3")
        
        if repos_response.status_code == 200:
            repos = repos_response.json()
            
            if repos:
                total_stars = sum(repo['stargazers_count'] for repo in repos)
                total_forks = sum(repo['forks_count'] for repo in repos)
                languages_used = set(repo['language'] for repo in repos if repo['language'])
                
                print(f"\nHere are their 3 most recently updated projects:")
                print(f"   Total stars across these: {total_stars}")
                print(f"   Total forks across these: {total_forks}")
                if languages_used:
                    print(f"   Languages used: {', '.join(languages_used)}")
                print()
                
                for i, repo in enumerate(repos, 1):
                    stars = repo['stargazers_count']
                    forks = repo['forks_count']
                    language = repo['language'] or "Not specified"
                    watchers = repo['watchers_count']
                    
                    print(f"Project {i}: {repo['name']}")
                    print(f"   Stars: {stars}   Forks: {forks}   Watchers: {watchers}")
                    print(f"   Language: {language}")
                    
                    if repo['description']:
                        desc = repo['description']
                        if len(desc) > 60:
                            desc = desc[:60] + "..."
                        print(f"   Description: {desc}")
                    
                    # Check if repo has issues
                    if repo['open_issues_count'] > 0:
                        print(f"   Open issues: {repo['open_issues_count']}")
                    
                    updated = datetime.strptime(repo['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
                    days_since = (datetime.now() - updated).days
                    if days_since == 0:
                        print(f"   Updated: today!")
                    elif days_since == 1:
                        print(f"   Updated: yesterday")
                    else:
                        print(f"   Updated: {days_since} days ago")
                    print()
            else:
                print("This user doesn't have any public repositories yet.")
                print("Maybe they're new to GitHub or prefer to keep things private.")
        else:
            print("Hmm, couldn't fetch their repository data at the moment.")
            print("The GitHub API might be a bit slow right now.")
            
        # Check follower-to-following ratio
        if data['followers'] > 0 and data['following'] > 0:
            ratio = data['followers'] / data['following']
            if ratio > 10:
                print("Note: This user has many more followers than they follow.")
                print("      They might be quite popular or influential!")
            elif ratio < 0.1:
                print("Note: This user follows many more people than follow them.")
                print("      They might be new or very active in following others.")
        
        # Random GitHub fact
        facts = [
            "GitHub was launched in 2008.",
            "The name 'GitHub' combines 'Git' and 'hub'.",
            "GitHub has over 100 million developers worldwide.",
            "The first GitHub repository was octocat/Spoon-Knife.",
            "GitHub was acquired by Microsoft in 2018.",
            "The most starred repository on GitHub is freeCodeCamp.",
            "GitHub uses the Octocat as its mascot.",
            "GitHub hosts over 200 million repositories.",
            "The most forked repository on GitHub is FirstContributions.",
            "GitHub Actions was introduced in 2019."
        ]
        print("\n" + "=" * 44)
        print(f"Did you know? {random.choice(facts)}")
        print("=" * 44)

    elif response.status_code == 404:
        print(f"Sorry, I couldn't find a GitHub user named '{username}'. Are you sure that's correct?")
        print("Check for typos or try a different username.")
        
        print("\nPopular GitHub users to try:")
        popular_users = ["octocat", "torvalds", "google", "microsoft", "facebook", "twitter", "angular", "reactjs", "vuejs"]
        for user in popular_users[:5]:
            print(f"  - {user}")
        
        print("\nTip: You can also try searching for organizations or teams!")

    else:
        print(f"Oops, something went wrong. The server returned status code: {response.status_code}.")
        print("This might be a temporary issue. Please try again in a moment.")
        
        # Show what status codes mean
        if response.status_code == 403:
            print("Note: Rate limit exceeded. Wait a moment and try again.")
        elif response.status_code == 500:
            print("Note: GitHub's servers might be experiencing issues.")

print("\nThanks for using the GitHub profile viewer!")
print("Have a great day!")

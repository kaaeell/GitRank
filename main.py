import requests
from datetime import datetime

print("Hello! Let me fetch a GitHub profile for you.")
username = input("Enter GitHub username: ")

if not username:
    print("Oh, you didn't enter a username. That's okay, try again next time.")
else:
    url = f"https://api.github.com/users/{username}"
    print(f"\nLooking up {username} on GitHub...")
    
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
        print(f"Member for:      {years} years and {months} months")
        
        if data['bio']:
            print(f"Bio:             {data['bio']}")
        
        if data['company']:
            print(f"Company:         {data['company']}")
        
        if data['blog']:
            print(f"Website:         {data['blog']}")
        
        if data.get('twitter_username'):
            print(f"Twitter:         @{data['twitter_username']}")
        
        hireable = "Yes" : "No" if data['hireable'] else "No"
        print(f"Open to hiring:  {hireable}")
        
        print("=" * 44)
        
        # Let's also check out their recent work
        print("\nChecking their latest repositories...")
        repos_url = data['repos_url']
        repos_response = requests.get(repos_url + "?sort=updated&per_page=3")
        
        if repos_response.status_code == 200:
            repos = repos_response.json()
            
            if repos:
                print("\nHere are their 3 most recently updated projects:\n")
                for i, repo in enumerate(repos, 1):
                    stars = repo['stargazers_count']
                    forks = repo['forks_count']
                    print(f"Project {i}: {repo['name']}")
                    print(f"   Stars: {stars}   Forks: {forks}")
                    if repo['description']:
                        desc = repo['description']
                        if len(desc) > 60:
                            desc = desc[:60] + "..."
                        print(f"   Description: {desc}")
                    print()
            else:
                print("This user doesn't have any public repositories yet.")
        else:
            print("Hmm, couldn't fetch their repository data at the moment.")

    elif response.status_code == 404:
        print(f"Sorry, I couldn't find a GitHub user named '{username}'. Are you sure that's correct?")

    else:
        print(f"Oops, something went wrong. The server returned status code: {response.status_code}. Please try again later.")

print("\nThanks for using the GitHub profile viewer!")

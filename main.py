import requests
from datetime import datetime

username = input("Enter GitHub username: ")

if not username:
    print("You didn't enter a username.")
else:
    url = f"https://api.github.com/users/{username}"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        print("\n==============================")
        print("       GITHUB PROFILE")
        print("==============================")

        print(f"Username: {data['login']}")
        print(f"Name: {data['name'] or 'Not provided'}")
        print(f"Followers: {data['followers']}")
        print(f"Following: {data['following']}")
        print(f"Public repositories: {data['public_repos']}")
        
        # Added: Account creation date
        created_at = datetime.strptime(data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        print(f"Account created: {created_at.strftime('%B %d, %Y')}")
        
        # Added: Bio if available
        if data['bio']:
            print(f"Bio: {data['bio']}")
        
        # Added: Company if available
        if data['company']:
            print(f"Company: {data['company']}")
        
        print("==============================")

    elif response.status_code == 404:
        print("GitHub user not found.")

    else:
        print(f"Something went wrong. Status code: {response.status_code}")

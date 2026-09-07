username = input("Enter GitHub username: ").strip()

if not username:
    print("Username cannot be empty.")
else:
    url = f"https://api.github.com/users/{username}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            # Everything related to the GitHub profile
            # stays INSIDE this if block.

            print(f"Username: {data.get('login')}")
            print(f"Name: {data.get('name')}")
            print(f"Bio: {data.get('bio')}")
            print(f"Followers: {data.get('followers')}")
            print(f"Following: {data.get('following')}")
            print(f"Public repositories: {data.get('public_repos')}")

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

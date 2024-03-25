import json
import os
import openai
import requests
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
# You have to add .env


def generate_jokes(result_array):
    openai.api_key = os.getenv("API_CHATPGT")
    jokes_data = []

    for result in result_array[:25]:
        title = result["Title"]
        url = result["Link"]
        jokes = []

        prompt = (
            f"Make a joke but short finishing the title of the joke. "
            f"For example, act as a late night host and finish the title of the news with a short joke. "
            f'My title: "{title}"'
        )

        joke_title = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            stop=None,
            n=4,
        )

        for choice in joke_title["choices"]:
            jokes.append(choice["message"]["content"].strip())

        joke_content = joke_title["choices"][0]["message"]["content"]
        jokes.append(joke_content)

        jokes_data.append(
            {"title": title, "url": url, "jokes": jokes, "manual_jokes": []}
        )

    return jokes_data


def lambda_handler(event, context):
    website = os.getenv("WEBSITE")
    result_array = web_scraping(website)
    jokes_data = generate_jokes(result_array)

    response_body = {"statusCode": 200, "body": json.dumps(jokes_data)}

    return response_body


def web_scraping(website):

    result = requests.get(website)

    if result.status_code == 200:

        content = result.text

        soup = BeautifulSoup(content, "html.parser")

        all_links = soup.find_all("a")
        filtered_links = [link for link in all_links if link.text.endswith("...")]

        links_data = []

        for link in filtered_links:
            link_data = {}
            link_data["Link"] = link["href"]
            link_data["Title"] = link.text
            links_data.append(link_data)

        return links_data
    else:
        print("Error fetching the page:", result.status_code)


print(lambda_handler({}, {}))

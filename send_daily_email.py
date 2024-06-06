from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To
import boto3
import os
from dotenv import load_dotenv
import json

# Load .env file
load_dotenv()

dynamodb_client = boto3.resource('dynamodb')
table = dynamodb_client.Table('themasonnetwork_drudgescrape')
subscribers_table = dynamodb_client.Table('themasonnetwork_subscribers')

def get_subscribers():
    subscribers = []
    for entry in subscribers_table.scan()["Items"]:
        subscribers.append(entry["user_email"])
    return subscribers

def get_article_for_emailsending():
    articles = []
    for entry in table.scan()["Items"]:
        article_object = {
            "url": entry["newsUrl"],
            "article": entry["newsOriginalTitle"],
        }
        articles.append(article_object)
    return articles

def send_email():
    articles = get_article_for_emailsending()
    # # Get the parent directory of the current script
    # parent_dir = os.path.dirname(os.path.abspath(__file__))
    # email_template_dir = os.path.join(parent_dir, "..", "email_template")

    # # Construct the relative path to the HTML file
    # html_file_path = os.path.join(email_template_dir, "email_template.html")

    html_file_path = os.path.join("email_template.html")

    # Open the HTML file
    with open(html_file_path, "r") as file:
        html_content = file.read()
        
    # Create a string representation of the articles
    articles_html = ""
    for item_article in articles:
        articles_html += '<div style="margin-bottom: 1rem;"><p style="font-size: 22px;color: #204e01; margin: 0px;">' + item_article["article"] + '</p><a href="' + item_article["url"] + '">' + item_article["url"] + '</a></div>'

    final_html_content = html_content.replace("{{tags}}", articles_html)

    subscribers = get_subscribers()

    count = 0

    for to_email in subscribers:
        message = Mail( 
                    from_email='hello@multilyser.com',
                    to_emails=[To(to_email), To('hello@multilyser.com')],
                    subject='Summarizing Websites Result',
                    is_multiple=True,
                    html_content=final_html_content
                )

        try:
            sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
            sg = SendGridAPIClient(api_key = sendgrid_api_key)
            response = sg.send(message)
            print(f'Email sent to {to_email}\n')
            count += 1
        except Exception as e:
            print(e)    

    return {
        'statusCode': 200,
        'body': json.dumps({'message': f'Email sent to {count} users successfully'})
    }


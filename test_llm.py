import requests
import csv

def main():
    # List of questions to ask
    questions = [
        "What is the capital of France?", 
        "Who wrote '1984'?",
        "What is the largest planet in our solar system?",
        "What is the boiling point of water?",
        "Who painted the Mona Lisa?"
    ]

    # Prepare CSV file
    with open('responses.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Question", "Response"])

        # Get responses for each question
        for question in questions:
            try:
                # Create prompt data for the API
                data = {
                    "model": "llama-3.2-1b-instruct",  # Model name as configured in LM Studio
                    "messages": [{"role": "user", "content": question}],
                    "temperature": 0.7
                }

                # Send request to the LM Studio API
                response = requests.post("http://127.0.0.1:1234/v1/chat/completions", json=data)

                # Check if request was successful
                if response.status_code == 200:
                    response_data = response.json()
                    answer = response_data['choices'][0]['message']['content']
                    writer.writerow([question, answer])
                    print(f"Question: {question}\nResponse: {answer}\n")
                else:
                    print(f"Error: Received status code {response.status_code} with message {response.text}")

            except Exception as e:
                print(f"Error processing question '{question}': {str(e)}")

if __name__ == "__main__":
    main()

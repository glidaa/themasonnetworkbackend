# About Us

This is a news website that scrapes news articles and generates humorous headlines. The website features a daily email subscription service, social media sharing capabilities, and an admin panel for managing and editing generated headlines. Additionally, the platform includes functionality for training a machine learning model based on user interactions with the jokes. The implementation utilizes Python for backend processing and Next.js for the frontend interface.

## Project Description

The project is designed to automate the process of scraping news articles, generating humorous content, and managing user interactions. It leverages AWS services for deployment and scalability, ensuring a robust and efficient system.

## Local Setup

This section provides instructions for setting up the local environment, including Docker, the database, and the code.

### Prerequisites

- Docker and Docker Compose installed on your machine.
- Python 3.8 or higher installed.
- AWS credentials configured for accessing DynamoDB in the Sydney region.

### Local Setup Instructions

1. **Setting Up Docker**

   - Build and Run the Docker Container:

     Navigate to the project directory and run the following command to build and start the Docker container:

     ```bash
     docker-compose up --build
     ```

     This will start the Flask server exposing the LLaMA model on port 8000.

2. **Configuring the Database**

   - Ensure AWS Credentials:

     Make sure your AWS credentials are set up to access DynamoDB in the Sydney region. You can configure this using the `create_aws_config.py` script.

   - Create DynamoDB Tables:

     Run the `setup_db.py` script to create the necessary DynamoDB tables:

     ```bash
     python setup_db.py
     ```

3. **Running the Scraper**

   - Activate the Virtual Environment:

     Depending on your operating system, activate the virtual environment:

     - **Linux:**

       ```bash
       source ./venv/bin/activate
       ```

     - **Windows:**

       ```bash
       source ./venv/Scripts/activate
       ```

   - Run the Scraper:

     Execute the `run_scrape_news.sh` script to start the news scraper:

     ```bash
     ./run_scrape_news.sh
     ```

### Model Files

Ensure the following model files are available in `C:/Users/username/weights/llama/text`:

- **Model Files (safetensors or pth):**
  - `model-00001-of-00004.safetensors`
  - `model-00002-of-00004.safetensors`
  - `model-00003-of-00004.safetensors`
  - `model-00004-of-00004.safetensors`
  - Or, if downloaded in a different format: `consolidated.00.pth`, etc.

- **Configuration and Metadata Files:**
  - `config.json`: Defines model configuration.
  - `generation_config.json`: Contains generation-specific configurations.
  - `special_tokens_map.json`: Maps special tokens.
  - `tokenizer_config.json`: Configuration for the tokenizer.
  - `tokenizer.model`: Contains tokenization rules.

- **Additional Metadata:**
  - `.gitattributes`
  - `USE_POLICY.md`: Model use policy information.

## Local LLM

To start the LMS server, follow these steps:

1. **Visit LM Studio**: [lmstudio.ai](https://lmstudio.ai)

2. **Start the LMS Server**:

   Run the following command to start the LMS server:

   ```bash
   python -m lms start
   lms server start
   ```

   This will initialize the server and make it accessible locally.

## Development Environment

The development environment is set up to facilitate efficient coding and testing. It includes:

- **Python**: Used for backend processing and scripting.
- **Next.js**: Utilized for the frontend interface.
- **AWS Services**: Deployed on AWS Lambda and Lightsail for scalability and reliability.

Ensure all dependencies are installed and configured correctly to maintain a smooth development workflow.

## Admin Interface

### Running the Admin Interface

1. **Start the Flask Server**:

   Navigate to the `admin` directory and run the following command to start the Flask server:

   ```bash
   python server.py
   ```

   This will start the server on `http://localhost:5000`.

2. **Access the Admin Page**:

   Open your web browser and go to:

   ```
   http://localhost:5000/admin/index.html
   ```

   This page will display the live data from the DynamoDB database.

### Clearing the Database

To clear the data from the DynamoDB table, run the following script:

```bash
python admin/clear_database.py
```

This will delete all entries from the `themasonnetwork_drudgescrape` table.

## Testing the Server

To test the LLM server, run the following command:

```bash
python test_llm.py
```

This will verify that the LLM server is running and accessible.

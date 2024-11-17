#!/bin/bash

# Set up logging
LOG_FILE="scraper_log_$(date +'%Y%m%d_%H%M%S').log"

# Set PYTHONPATH to include the current directory
export PYTHONPATH=$(pwd)

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux environment (server)
    source ./venv/bin/activate
elif [[ "$OSTYPE" == "msys" ]]; then
    # Windows environment (local)
    source ./venv/Scripts/activate
else
    echo "Unsupported OS type: $OSTYPE" | tee -a $LOG_FILE
    exit 1
fi

echo "Running news scraper..." | tee -a $LOG_FILE
python ./news_processor/main.py 2>&1 | tee -a $LOG_FILE

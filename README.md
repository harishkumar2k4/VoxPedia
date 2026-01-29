# Task 1: Data Collection

This module is responsible for identifying the most relevant knowledge source for a given topic and extracting its content for the local knowledge base.

## Features
- Topic Search: Dynamically identifies the closest matching Wikipedia article for any user query using the wikipedia search API.

- Content Extraction: Scrapes the full text, title, and URL of the identified article.

- Automatic Disambiguation: Handles cases where a search term may refer to multiple topics (e.g., "Python") by automatically selecting the most probable match.

- Structured Storage: Sanitizes article titles to create safe filenames and saves the content as a UTF-8 encoded .txt file.

## How to Run
- Navigate to the root directory and run the script via the command line:
  python src/wiki_scraper.py "Your Topic Here"

## Observations and Challenges
- Observations: I found that while the wikipedia library is efficient, passing specific search queries (e.g., "Python programming language") significantly improves the quality of the retrieved text compared to broad terms.

- Challenges: The primary challenge was handling DisambiguationErrors. I implemented a nested try-except block to catch these errors and automatically proceed with the first suggested option to ensure the pipeline remains autonomous and doesn't crash on broad queries.

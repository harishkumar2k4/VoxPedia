import argparse
import wikipedia
import os
import sys

def get_wiki_content(query):
    """
    Searches Wikipedia for the query and extracts the content.
    """
    try:
        # Search for the topic; results=1 for the top match
        search_results = wikipedia.search(query, results=1)

        if not search_results:
            return None, None, None

        article_title = search_results[0]
        # auto_suggest=False ensures we get the exact title found
        page = wikipedia.page(article_title, auto_suggest=False)

        return page.title, page.url, page.content

    except wikipedia.exceptions.DisambiguationError as e:
        # Resolve ambiguity by picking the first suggestion
        try:
            page = wikipedia.page(e.options[0], auto_suggest=False)
            return page.title, page.url, page.content
        except:
            print(f"Ambiguous term '{query}'. Could not resolve automatically.")
            return None, None, None
    except (wikipedia.exceptions.PageError, Exception) as e:
        print(f"An error occurred: {e}")
        return None, None, None

def save_to_file(title, text):
    """
    Saves text to a .txt file inside a 'data/' directory.
    """
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Sanitize title for filename
    safe_title = "".join([c for c in title if c.isalnum() or c == ' ']).strip()
    filename = os.path.join("data", f"{safe_title.replace(' ', '_')}.txt")

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)

    return filename

def main():
    parser = argparse.ArgumentParser(description="Search and scrape Wikipedia articles.")
    parser.add_argument("query", type=str, help="The topic to search for")

    args = parser.parse_args()
    
    print(f"Searching Wikipedia for: '{args.query}'...")
    title, url, content = get_wiki_content(args.query)

    if title and content:
        print(f"Found: {title}\nURL: {url}")
        filepath = save_to_file(title, content)
        print(f"Success! Content saved to '{filepath}'")
    else:
        print("Could not retrieve article content.")

if __name__ == "__main__":
    main()

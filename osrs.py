#!/usr/bin/env python3
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def get_wiki_info(search_term):
    url = f"https://oldschool.runescape.wiki/w/{quote(search_term)}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Get the page URL (in case of redirects)
    page_url = response.url
    
    # Get the first paragraph
    first_p = soup.find('p')
    first_paragraph = first_p.text.strip() if first_p else "No content found."
    
    # Check for infobox
    infobox = soup.find('table', class_=lambda x: x and 'infobox' in x)
    if not infobox:
        return page_url, first_paragraph, "No infobox found."
    
    info = []
    current_subheader = "General"  # Start with a "General" section

    for row in infobox.find_all('tr'):
        th = row.find('th')
        tds = row.find_all('td')

        if th and 'infobox-subheader' in th.get('class', []):
            current_subheader = th.text.strip()
            info.append(f"\n--- {current_subheader} ---")
        elif th:
            key = th.text.strip()
            value = " ".join(td.text.strip() for td in tds if td.text.strip())
            
            # Special handling for "Assigned by" or similar image-based fields
            if not value:
                links = row.find_all('a')
                value = ", ".join(link.get('title', link.text) for link in links if link.get('title') or link.text)
            
            # Handle cases where value might be in a nested structure
            if not value:
                value = " ".join(row.stripped_strings)
            
            if value:
                info.append(f"{key}: {value}")
        elif all('infobox-nested' in td.get('class', []) for td in tds):
            for td in tds:
                key = td.get('data-attr-param', '').capitalize()
                value = td.text.strip()
                if key and value:
                    info.append(f"{key}: {value}")
    
    return page_url, first_paragraph, "\n".join(info) if info else "No relevant information found in infobox."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./osrs_wiki.py <search_term>")
        sys.exit(1)
    
    search_term = " ".join(sys.argv[1:])
    print(f"Searching for: {search_term}")
    page_url, first_paragraph, infobox_info = get_wiki_info(search_term)
    
    print(f"\n# Page URL: {page_url}")
    print(f"\n## Summary: {first_paragraph}")
    print(f"\n### Infobox Information:")
    print(infobox_info)
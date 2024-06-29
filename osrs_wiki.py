#!/usr/bin/env python3
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


def get_wiki_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    page_url = response.url
    
    first_p = soup.find('p')
    first_paragraph = first_p.text.strip() if first_p else "No content found."

    # Check for disambiguation page
    if "may refer to:" in first_paragraph:
        options = []
        content_div = soup.find('div', class_='mw-parser-output')
        if content_div:
            for i, li in enumerate(content_div.find('ul').find_all('li', recursive=False), 1):
                link = li.find('a')
                if link:
                    options.append((i, link.text, link['href'], li.text))
        return page_url, first_paragraph, options, True  # True indicates it's a disambiguation page

    # If not a disambiguation page, process as before
    infobox = soup.find('table', class_=lambda x: x and 'infobox' in x)
    if not infobox:
        return page_url, first_paragraph, None, False  # Return None instead of a string message
    
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
    
    return page_url, first_paragraph, "\n".join(info) if info else None, False

def format_infobox(infobox_info):
    table = Table(title="# Infobox Information #", show_header=True, header_style="bold magenta")
    table.add_column("Section", style="cyan", no_wrap=True)
    table.add_column("Key", style="green")
    table.add_column("Value", style="yellow")

    current_section = "General"
    last_displayed_section = None
    for line in infobox_info.split('\n'):
        if line.startswith('---'):
            current_section = line.strip('- ')
        elif ': ' in line:
            key, value = line.split(': ', 1)
            section_to_display = current_section if current_section != last_displayed_section else ""
            table.add_row(section_to_display, key, value)
            last_displayed_section = current_section

    return table
def process_search(search_term):
    url = f"https://oldschool.runescape.wiki/w/{quote(search_term)}"
    while True:
        page_url, first_paragraph, info, is_disambiguation = get_wiki_info(url)
        
        if not is_disambiguation:
            return page_url, first_paragraph, info
        
        console.print(Panel(first_paragraph, title="Disambiguation", expand=False))
        table = Table(title="Options", show_header=True, header_style="bold magenta")
        table.add_column("Number", style="cyan", no_wrap=True)
        table.add_column("Option", style="green")
        table.add_column("Description", style="yellow")
        
        for num, title, href, description in info:
            table.add_row(str(num), title, description)
        
        console.print(table)
        
        choice = console.input("[bold green]Enter the number of your choice (or 'q' to quit): [/bold green]")
        if choice.lower() == 'q':
            console.print("[bold red]Exiting.[/bold red]")
            sys.exit(0)
        
        try:
            choice = int(choice)
            if 1 <= choice <= len(info):
                url = f"https://oldschool.runescape.wiki{info[choice-1][2]}"
            else:
                console.print("[bold red]Invalid choice. Please try again.[/bold red]")
        except ValueError:
            console.print("[bold red]Invalid input. Please enter a number or 'q' to quit.[/bold red]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./osrs_wiki.py <search_term>")
        sys.exit(1)
    
    search_term = " ".join(sys.argv[1:])
    console = Console()
    console.print(f"[bold blue]Searching for:[/bold blue] {search_term}")
    
    page_url, first_paragraph, infobox_info = process_search(search_term)
    
    console.print(Panel(f"[link={page_url}]{page_url}[/link]", title="Page URL", expand=False))
    console.print(Panel(first_paragraph, title="Summary", expand=False))
    
    if infobox_info:
        console.print(format_infobox(infobox_info))
    # else:
    #     console.print("[yellow]No infobox information found for this page.[/yellow]")
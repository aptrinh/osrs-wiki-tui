#!/usr/bin/env python3
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

HEADERS = {"User-Agent": "osrs-wiki-tui (https://github.com/aptrinh/osrs-wiki-tui)"}


def get_info(url):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 404:
        return r.url, None, None, False
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    page_url = r.url

    first_p = None
    for p in soup.find_all('p'):
        if p.text.strip():
            first_p = p
            break
    summary = first_p.text.strip() if first_p else "No content found."

    if "may refer to:" in summary:
        options = []
        content = soup.find('div', class_='mw-parser-output')
        if content:
            for i, li in enumerate(content.find('ul').find_all('li', recursive=False), 1):
                link = li.find('a')
                if link:
                    options.append((i, link.text, link['href'], li.text))
        return page_url, summary, options, True

    infobox = soup.find('table', class_=lambda x: x and 'infobox' in x)
    if not infobox:
        return page_url, summary, None, False

    info = []
    for row in infobox.find_all('tr'):
        th = row.find('th')
        tds = row.find_all('td')
        if th and 'infobox-subheader' in th.get('class', []):
            info.append(f"\n--- {th.text.strip()} ---")
        elif th:
            key = th.text.strip()
            value = " ".join(td.text.strip() for td in tds if td.text.strip())
            if not value:
                links = row.find_all('a')
                value = ", ".join(l.get('title', l.text) for l in links if l.get('title') or l.text)
            if not value:
                value = " ".join(row.stripped_strings)
            if value:
                info.append(f"{key}: {value}")
        elif tds and all('infobox-nested' in td.get('class', []) for td in tds):
            for td in tds:
                key = td.get('data-attr-param', '').capitalize()
                value = td.text.strip()
                if key and value:
                    info.append(f"{key}: {value}")

    return page_url, summary, "\n".join(info) if info else None, False


def fmt_box(info):
    table = Table(title="# Infobox Information #", show_header=True, header_style="bold magenta")
    table.add_column("Section", style="cyan", no_wrap=True)
    table.add_column("Key", style="green")
    table.add_column("Value", style="yellow")

    section = "General"
    last = None
    for line in info.split('\n'):
        if line.startswith('---'):
            section = line.strip('- ')
        elif ': ' in line:
            key, value = line.split(': ', 1)
            shown = section if section != last else ""
            table.add_row(shown, key, value)
            last = section
    return table


def search(term):
    encoded = quote(term).replace('+', '%2B')
    url = f"https://oldschool.runescape.wiki/w/{encoded}"

    while True:
        try:
            page_url, summary, info, disambig = get_info(url)
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Error accessing the wiki: {e}[/bold red]")
            return None, None, None

        if summary is None:
            console.print(f"[bold red]Page not found:[/bold red] {page_url}")
            return None, None, None

        if not disambig:
            return page_url, summary, info

        console.print(Panel(summary, title="Disambiguation", expand=False))
        table = Table(title="Options", show_header=True, header_style="bold magenta")
        table.add_column("Number", style="cyan", no_wrap=True)
        table.add_column("Option", style="green")
        table.add_column("Description", style="yellow")
        for num, title, href, desc in info:
            table.add_row(str(num), title, desc)
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

    term = " ".join(sys.argv[1:])
    console = Console()
    console.print(f"[bold blue]Searching for:[/bold blue] {term}")

    page_url, summary, box = search(term)
    if page_url is None:
        sys.exit(1)

    console.print(Panel(f"[link={page_url}]{page_url}[/link]", title="Page URL", expand=False))
    console.print(Panel(summary, title="Summary", expand=False))
    if box:
        console.print(fmt_box(box))
    else:
        console.print("[yellow]No infobox information found for this page.[/yellow]")
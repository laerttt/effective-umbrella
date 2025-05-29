from debug import log_info, log_error
from time import sleep
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup as bs4
from tqdm import tqdm  # Import tqdm for progress bars


def get_totalPagination(url: str) -> int:
    """
    Retrieve the total number of pagination pages from the given URL.

    Args:
        url (str): The URL to fetch and parse for pagination links.

    Returns:
        int: The total number of pages found from pagination links.
             Returns 0 if pagination is not found or an error occurs.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        log_error(f'Error fetching totalPagination: {e}')
        return 0

    soup = bs4(response.text, 'html.parser')
    # Select pagination <a> tags in the container
    a_tags = soup.select('body > div#content > div.container > div > ul > li > a')
    # Reverse to get last page link first
    a_tags = list(reversed(a_tags))
    totalPagination_pattern = re.compile(r'page=(\d+)$')
    try:
        href = a_tags[0]['href']
        match = totalPagination_pattern.search(href)
        if match:
            return int(match.group(1))
        else:
            return 0
    except (IndexError, TypeError) as e:
        log_error(f'Error parsing totalPagination: {e}')
        return 0


def get_list(pageNumber: int, url: str) -> list:
    """
    Fetch all href links from a specific pagination page.

    Args:
        pageNumber (int): The page number to fetch.
        url (str): The base URL to append the page parameter to.

    Returns:
        list: A list of href strings extracted from the page.
              Returns an empty list if the request fails.
    """
    subUrl = url + '&page=' + str(pageNumber)
    try:
        response = requests.get(subUrl, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        log_error(f'Error fetching page {pageNumber}: {e}')
        return []

    soup = bs4(response.text, 'html.parser')
    # Select relevant <a> tags containing hrefs
    a_tags = soup.select('body > div#content > div.container > div > div > div > div > p > a')
    hrefs = [tag.get('href') for tag in a_tags if tag.get('href')]
    return hrefs


def get_fullList(totalPagination: int, url: str, saveList: str) -> list:
    """
    Collect hrefs from all pagination pages and save incrementally to a CSV file.

    Args:
        totalPagination (int): Total number of pagination pages to process.
        url (str): The base URL to paginate.
        saveList (str): Filename prefix (without extension) to save hrefs CSV.

    Returns:
        list: A combined list of all href strings collected.
    """
    full_list = []
    # Create or overwrite CSV file with header
    pd.DataFrame(columns=['href']).to_csv(f'{saveList}.csv', index=False)

    if totalPagination == 0:
        # No pagination detected; fetch only the first page
        hrefs = get_list(pageNumber=1, url=url)
        full_list.extend(hrefs)
        pd.DataFrame(hrefs, columns=['href']).to_csv(f'{saveList}.csv', mode='a', header=False, index=False)
        log_info(f'No pagination detected. Fetched {len(hrefs)} hrefs from page 1.')
    else:
        # Iterate pages with tqdm progress bar for visual feedback
        for pageNumber in tqdm(range(1, totalPagination + 1), desc='Getting lists', unit='page'):
            sleep(2)  # polite delay to avoid hammering server
            hrefs = get_list(pageNumber=pageNumber, url=url)
            full_list.extend(hrefs)
            # Append hrefs of current page to CSV without headers
            pd.DataFrame(hrefs, columns=['href']).to_csv(f'{saveList}.csv', mode='a', header=False, index=False)

    log_info(f'Total hrefs fetched: {len(full_list)}')
    return full_list


def decode_cfemail(cfemail: str) -> str:
    """
    Decode Cloudflare's email protection obfuscated hex string.

    Args:
        cfemail (str): Hex string from data-cfemail attribute.

    Returns:
        str: Decoded plain email address.
    """
    r = int(cfemail[:2], 16)
    email = ''.join(
        chr(int(cfemail[i:i + 2], 16) ^ r)
        for i in range(2, len(cfemail), 2)
    )
    return email


def get_email(response_text: str) -> list:
    """
    Extract and decode all Cloudflare-protected email addresses from HTML content.

    Args:
        response_text (str): HTML content of the page.

    Returns:
        list: List of decoded email addresses found.
    """
    soup = bs4(response_text, 'html.parser')
    encoded = soup.select('a.__cf_email__')
    emails = []
    for item in encoded:
        try:
            emails.append(decode_cfemail(item['data-cfemail']))
        except KeyError:
            # Could log a warning here if needed
            pass
    return emails


def get_name(response_text: str) -> str:
    """
    Extract a person's name or title from the page content.

    Args:
        response_text (str): HTML content of the page.

    Returns:
        str: Extracted name text or empty string if not found.
    """
    soup = bs4(response_text, 'html.parser')
    name_tag = soup.select_one('body > div#content > div.container > h2.title-divider > span')
    return name_tag.text if name_tag else ''


def fetch_and_save(baseUrl: str, url_paths: list, csv_filename: str) -> None:
    """
    Fetch pages for each href, extract names and emails, and save them incrementally to a CSV file.

    Args:
        baseUrl (str): Base URL to prepend to each href path.
        url_paths (list): List of href paths to fetch.
        csv_filename (str): CSV file to save extracted data.
    """
    # Create or overwrite CSV file with headers
    pd.DataFrame(columns=['name', 'email']).to_csv(csv_filename, index=False)

    # Use tqdm for fetching progress bar
    for idx, item in enumerate(tqdm(url_paths, desc='Fetching emails', unit='url'), 1):
        full_url = baseUrl + item
        log_info(f'Fetching URL ({idx}/{len(url_paths)}): {full_url}')

        try:
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            log_error(f'Error fetching URL {full_url}: {e}')
            continue

        name = get_name(response.text)
        email_list = get_email(response.text)

        if not email_list:
            # Save record with empty email if none found
            df = pd.DataFrame([[name, '']], columns=['name', 'email'])
            df.to_csv(csv_filename, mode='a', header=False, index=False)
        else:
            # Save each email with associated name
            for email in email_list:
                df = pd.DataFrame([[name, email]], columns=['name', 'email'])
                df.to_csv(csv_filename, mode='a', header=False, index=False)

        sleep(1)  # Polite delay between requests


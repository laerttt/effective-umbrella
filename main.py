from debug import log_info, log_error
from time import sleep
import requests
import argparse
import helpers
import pandas as pd
import json
from tqdm import tqdm 
import pyfiglet


def main():
    """
    Main function to run the scraper.

    Parses command-line arguments to select a subdomain by index from a JSON file,
    then scrapes data from paginated pages of the selected subdomain on url.

    It fetches all hrefs from pagination, extracts names and emails from each page,
    and saves the results incrementally to a CSV file.

    Handles errors gracefully and provides progress feedback via tqdm.
    """

    ascii_banner = pyfiglet.figlet_format("Simple Scraper")
    print(ascii_banner)
    # Setup command-line argument parser
    parser = argparse.ArgumentParser(description="Simple Scraper")
    parser.add_argument(
        '--index', '-i', type=int,
        help='Subdomain index from JSON file',
        required=True
    )
    parser.add_argument(
        '--output', '-o', type=str,
        help='Output CSV file',
        default=None
    )
    args = parser.parse_args()

    # Load subdomains from JSON file
    jsonFile = 'subdomains.json'
    with open(jsonFile, 'r', encoding='utf-8') as f:
        subdomains = json.load(f)

    # Validate index argument is within bounds
    if args.index < 0 or args.index >= len(subdomains['data']):
        log_error(f"Invalid index: {args.index}. Must be between 0 and {len(subdomains['data'])-1}.")
        return

    # Select subdomain by index
    subdomain = subdomains['data'][args.index]
    baseUrl = "https:/exampleURL.com"
    path = subdomain['path']
    fileName = args.output if args.output else f"{subdomain['name']}.csv"
    url = baseUrl + path

    log_info(f"Starting scraper for: {url}")

    # Get total number of pagination pages
    totalPagination = helpers.get_totalPagination(url)
    if totalPagination == 0:
        log_error("No pagination detected or failed to fetch total pages.")

    log_info(f"Total pages: {totalPagination}")

    # Fetch all hrefs from paginated pages and save list CSV
    href_list_file = f"{subdomain['name']}_list.csv"
    hrefs = helpers.get_fullList(
        totalPagination=totalPagination,
        url=url,
        saveList=subdomain['name'] + "_list"
    )

    # Stop if no hrefs found
    if not hrefs:
        log_error("No hrefs found to process.")
        return

    log_info(f"Total hrefs found: {len(hrefs)}")

    # Initialize output CSV with headers
    pd.DataFrame(columns=['name', 'email']).to_csv(fileName, index=False)

    # Process each href with progress bar via tqdm
    for idx, item in enumerate(tqdm(hrefs, desc='Processing hrefs', unit='href'), 1):
        full_url = baseUrl + item

        try:
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            log_error(f"Request failed: {full_url} - {e}")
            continue

        # Extract name and emails from the page
        name = helpers.get_name(response.text)
        emails = helpers.get_email(response.text)

        # Save data to CSV, one row per email (or empty if none found)
        if not emails:
            df = pd.DataFrame([[name, '']], columns=['name', 'email'])
            df.to_csv(fileName, mode='a', header=False, index=False)
        else:
            for email in emails:
                df = pd.DataFrame([[name, email]], columns=['name', 'email'])
                df.to_csv(fileName, mode='a', header=False, index=False)

        # Polite delay between requests
        sleep(1)

    log_info(f"Data saved to {fileName}")


if __name__ == "__main__":
    main()

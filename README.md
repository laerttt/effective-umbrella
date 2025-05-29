Sure! Here's a concise `README.md` for your scraper project:


# Simple Scraper

A Python scraper to extract names and emails from paginated web pages on url.

## Features
- Automatically handles pagination
- Extracts names and Cloudflare-protected emails
- Saves results to CSV
- Shows progress with a nice progress bar (using `tqdm`)

## Requirements
- Python 3.7+
- `requests`
- `pandas`
- `beautifulsoup4`
- `tqdm`

Install dependencies with:

```bash
pip install -r requirements.txt
````

## Usage

Prepare a `subdomains.json` file listing target subdomains and paths.

Run the scraper specifying the subdomain index:

```bash
python main.py -i 0
```

Optionally, specify output CSV filename:

```bash
python main.py -i 0 -o output.csv
```

Results will be saved in CSV format with `name` and `email` columns.

---

Feel free to extend or modify this scraper as needed.


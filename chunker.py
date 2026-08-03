"""
chunker.py - Task 2.2: Data Cleaner & Text Chunking (Improved Strategy)

Reads raw HTML files scraped from Groww AMC pages and extracts
structured, semantically meaningful chunks for the RAG pipeline.

Key improvements:
  1. Strips boilerplate navigation, sidebar, and footer HTML before extraction.
  2. Extracts structured sections (AMC overview, fund table, key info) separately.
  3. Creates one chunk per fund to avoid splitting data mid-row.
  4. Includes JSON-LD FAQ data when available.
"""

import os
import json
from bs4 import BeautifulSoup

RAW_DATA_DIR = "./data/raw"
PROCESSED_DATA_DIR = "./data/processed"
REVIEW_DATA_DIR = "./data/review"
OUTPUT_FILE = os.path.join(PROCESSED_DATA_DIR, "chunks.json")


def get_url_from_filename(filename):
    """Reconstructs the original URL from the saved filename."""
    basename = filename.replace(".html", "")
    return f"https://groww.in/mutual-funds/amc/{basename}"


def get_amc_name(soup):
    """Extracts AMC name from the page title."""
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        return title_tag.string.split(' - ')[0].strip()
    return "Unknown AMC"


def extract_faq_data(soup, source_url, amc_name):
    """Extracts FAQ data from JSON-LD structured data (before script removal)."""
    chunks = []
    for script in soup.find_all('script'):
        text = script.string or ''
        if 'FAQPage' in text:
            try:
                data = json.loads(text)
                for entity in data.get('mainEntity', []):
                    question = entity.get('name', '')
                    answer_html = entity.get('acceptedAnswer', {}).get('text', '')
                    answer_soup = BeautifulSoup(answer_html, 'html.parser')
                    answer = answer_soup.get_text(' ', strip=True)
                    if question and answer:
                        chunks.append({
                            "text": f"Q: {question}\nA: {answer}",
                            "metadata": {
                                "source": source_url,
                                "section": "faq",
                                "amc_name": amc_name
                            }
                        })
            except json.JSONDecodeError:
                pass
    return chunks


def extract_amc_overview(main_content, source_url, amc_name):
    """Extracts AMC AUM, number of schemes, age, and description."""
    parts = [f"AMC: {amc_name}"]

    # AUM, No of Schemes, AMC Age
    info_container = main_content.find('div', class_=lambda c: c and 'infoContainer' in c)
    if info_container:
        info_text = info_container.get_text(' ', strip=True)
        parts.append(f"Overview: {info_text}")

    # Description paragraph(s)
    for p in main_content.find_all('p'):
        text = p.get_text(strip=True)
        if len(text) > 80 and any(kw in text for kw in ['AMC', 'Asset Management', 'mutual fund', 'Mutual Fund', 'founded', 'subsidiary']):
            parts.append(f"Description: {text}")
            break

    # Additional description paragraphs
    desc_div = main_content.find('div', class_=lambda c: c and 'descriptionDiv' in c)
    if desc_div:
        for p in desc_div.find_all('p'):
            text = p.get_text(strip=True)
            if text and text not in parts[-1] if parts else True:
                parts.append(text)

    if len(parts) > 1:  # More than just the AMC name
        return {
            "text": "\n".join(parts),
            "metadata": {
                "source": source_url,
                "section": "amc_overview",
                "amc_name": amc_name
            }
        }
    return None


def extract_key_information(main_content, source_url, amc_name):
    """Extracts the key information table (incorporation date, sponsor, CEO, etc.)."""
    for table in main_content.find_all('table'):
        text = table.get_text(' ', strip=True)
        if 'Mutual fund name' in text or 'Incorporation Date' in text:
            rows = table.find_all('tr')
            info_lines = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    info_lines.append(f"{key}: {value}")

            if info_lines:
                return {
                    "text": f"Key Information about {amc_name}\n" + "\n".join(info_lines),
                    "metadata": {
                        "source": source_url,
                        "section": "key_information",
                        "amc_name": amc_name
                    }
                }
    return None


def extract_fund_table(main_content, source_url, amc_name):
    """Extracts each fund from the main fund listing table as a separate chunk."""
    chunks = []

    for table in main_content.find_all('table'):
        headers_row = table.find('tr')
        if not headers_row:
            continue

        header_cells = headers_row.find_all(['th', 'td'])
        headers = [h.get_text(strip=True) for h in header_cells]

        # Identify the main fund table by checking for expected columns
        if 'Fund Name' not in headers or 'NAV' not in headers:
            continue

        rows = table.find_all('tr')[1:]
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue

            cell_values = [c.get_text(strip=True) for c in cells]
            fund_data = dict(zip(headers, cell_values))

            fund_name = fund_data.get('Fund Name', 'Unknown Fund')

            # Build a readable text chunk for this fund
            text_parts = [f"Fund: {fund_name} ({amc_name})"]
            for key in ['Category', 'Risk', 'NAV', 'Expense Ratio',
                        '1Y Returns', '3Y Returns', '5Y Returns',
                        '7Y Returns', '10Y Returns', 'Rating',
                        'Fund Size (in Cr)', 'Exit Load']:
                val = fund_data.get(key, '--')
                if val and val != '--':
                    text_parts.append(f"{key}: {val}")

            chunks.append({
                "text": "\n".join(text_parts),
                "metadata": {
                    "source": source_url,
                    "section": "fund_data",
                    "fund_name": fund_name,
                    "amc_name": amc_name
                }
            })

        # Only process the first matching fund table
        if chunks:
            break

    return chunks


def extract_fund_details(main_content, source_url, amc_name):
    """Extracts individual fund detail cards (min investment, AUM, description)."""
    chunks = []

    for table in main_content.find_all('table'):
        text = table.get_text(' ', strip=True)
        # These are the small 3-row tables: Min Investment Amt, AUM, 1Y Returns
        if 'Min Investment Amt' not in text or 'AUM' not in text:
            continue

        rows = table.find_all('tr')
        detail_lines = []
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) == 2:
                detail_lines.append(f"{cells[0].get_text(strip=True)}: {cells[1].get_text(strip=True)}")

        if not detail_lines:
            continue

        # Find the fund name from a preceding heading
        fund_name = "Unknown Fund"
        prev = table.find_previous(['h2', 'h3'])
        if prev:
            heading_text = prev.get_text(strip=True)
            if 'Fund' in heading_text:
                fund_name = heading_text

        # Find fund description
        description = ""
        # Look for "Fund Performance:" text near the table
        for sibling in table.find_all_previous(['div', 'p', 'span']):
            sib_text = sibling.get_text(' ', strip=True)
            if 'Fund Performance:' in sib_text and len(sib_text) < 500:
                description = sib_text
                break

        text_content = f"Fund Details: {fund_name}\n"
        if description:
            text_content += f"{description}\n"
        text_content += "\n".join(detail_lines)

        chunks.append({
            "text": text_content,
            "metadata": {
                "source": source_url,
                "section": "fund_details",
                "fund_name": fund_name,
                "amc_name": amc_name
            }
        })

    return chunks


def process_file(filepath, source_url):
    """Processes a single HTML file and returns structured chunks."""
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract AMC name and FAQ BEFORE any DOM modifications
    amc_name = get_amc_name(soup)
    faq_chunks = extract_faq_data(soup, source_url, amc_name)

    # Find the main content area
    main = soup.find('div', id='amcMainPage')
    if not main:
        return faq_chunks

    # Find the layout-main div (actual content, not sidebar)
    layout_main = main.find('div', class_='layout-main')
    # Fallback: use the entire amcMainPage if layout-main not found
    content_area = layout_main if layout_main else main

    chunks = []

    # 1. AMC Overview
    overview = extract_amc_overview(content_area, source_url, amc_name)
    if overview:
        chunks.append(overview)

    # 2. Key Information
    key_info = extract_key_information(content_area, source_url, amc_name)
    if key_info:
        chunks.append(key_info)

    # 3. Fund Table (one chunk per fund)
    fund_chunks = extract_fund_table(content_area, source_url, amc_name)
    chunks.extend(fund_chunks)

    # 4. Individual Fund Details
    detail_chunks = extract_fund_details(content_area, source_url, amc_name)
    chunks.extend(detail_chunks)

    # 5. FAQ Data
    chunks.extend(faq_chunks)

    return chunks


def save_review_file(chunks, filename, review_dir):
    """Saves a human-readable review file for a set of chunks."""
    review_filename = filename.replace(".html", "_review.md")
    review_filepath = os.path.join(review_dir, review_filename)

    with open(review_filepath, 'w', encoding='utf-8') as f:
        if chunks:
            amc_name = chunks[0].get('metadata', {}).get('amc_name', 'Unknown')
            source = chunks[0].get('metadata', {}).get('source', '')
            f.write(f"# Review: {amc_name}\n")
            f.write(f"**Source**: {source}\n")
            f.write(f"**Total Chunks**: {len(chunks)}\n\n")

        for i, chunk in enumerate(chunks, 1):
            section = chunk.get('metadata', {}).get('section', 'unknown')
            fund = chunk.get('metadata', {}).get('fund_name', '')
            label = f"[{section}]"
            if fund:
                label += f" {fund}"
            f.write(f"## Chunk {i} {label}\n")
            f.write(f"```text\n{chunk['text']}\n```\n\n")

    return review_filepath


def process_and_chunk():
    """Main entry point: reads raw HTML, extracts structured chunks, saves outputs."""
    if not os.path.exists(RAW_DATA_DIR):
        print(f"Error: Raw data directory {RAW_DATA_DIR} not found.")
        return

    for directory in [PROCESSED_DATA_DIR, REVIEW_DATA_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

    print("Starting Data Cleaner & Chunker (Task 2.2 - Improved Strategy)...")

    all_chunks = []

    for filename in sorted(os.listdir(RAW_DATA_DIR)):
        if not filename.endswith(".html"):
            continue

        filepath = os.path.join(RAW_DATA_DIR, filename)
        source_url = get_url_from_filename(filename)

        print(f"Processing: {filename}")

        chunks = process_file(filepath, source_url)

        # Count sections
        sections = {}
        for c in chunks:
            s = c.get('metadata', {}).get('section', 'unknown')
            sections[s] = sections.get(s, 0) + 1
        section_summary = ", ".join(f"{k}: {v}" for k, v in sections.items())

        print(f"  -> {len(chunks)} chunks ({section_summary})")

        # Save review file
        review_path = save_review_file(chunks, filename, REVIEW_DATA_DIR)
        print(f"  -> Review: {review_path}")

        all_chunks.extend(chunks)

    print(f"\nTotal chunks created: {len(all_chunks)}")

    # Summary by section type
    section_totals = {}
    for c in all_chunks:
        s = c.get('metadata', {}).get('section', 'unknown')
        section_totals[s] = section_totals.get(s, 0) + 1
    print("Section breakdown:")
    for s, count in section_totals.items():
        print(f"  {s}: {count}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\nSaved chunked data to {OUTPUT_FILE}")


if __name__ == "__main__":
    process_and_chunk()

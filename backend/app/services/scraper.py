"""
Web scraper using Playwright to handle JS-heavy pages.
Extracts terpene data and COA links from cannabis product pages.
"""

import re
import hashlib
import json
from typing import Optional, List, Dict
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
from app.models.schemas import ScrapedData, Totals

# Common terpene names and variations
TERPENE_PATTERNS = {
    r'(?:beta[_\s-]?)?myrcene': 'myrcene',
    r'd[_\s-]?limonene|limonene': 'limonene',
    r'(?:beta[_\s-]?)?caryophyllene': 'caryophyllene',
    r'(?:alpha|α)[_\s-]?pinene': 'alpha_pinene',
    r'(?:beta|β)[_\s-]?pinene': 'beta_pinene',
    r'terpinolene': 'terpinolene',
    r'humulene': 'humulene',
    r'linalool': 'linalool',
    r'(?:beta|β)[_\s-]?ocimene|ocimene': 'ocimene',
}

# Patterns for COA detection
COA_LINK_PATTERNS = [
    r'certificate.*analysis',
    r'lab.*results?',
    r'coa',
    r'test.*results?',
    r'analysis.*certificate',
]

async def get_dutchie_iframe(page: Page) -> Optional[Page]:
    """
    Check for Dutchie iframe and return the iframe's page context.
    Dutchie menus are often embedded in iframes.
    """
    try:
        # Look for iframes with 'dutchie' in the src
        iframes = page.frames
        for frame in iframes:
            url = frame.url
            if 'dutchie.com' in url:
                print(f"Found Dutchie iframe: {url}")
                return frame
    except Exception as e:
        print(f"Iframe detection note: {e}")

    return None

async def handle_age_verification(page: Page) -> None:
    """
    Handle age verification popups common on cannabis dispensary sites.
    Looks for and clicks common age gate buttons.
    """
    try:
        # Wait for popup to appear
        await page.wait_for_timeout(2000)

        # Strategy 1: Use Playwright's built-in text selector (most reliable)
        age_patterns = [
            'text=/yes.*i.*am/i',
            'text=/enter/i',
            'text=/continue/i',
            'text=/i.*21/i',
            'text=/i.*18/i',
            'text=/confirm/i',
            'text=/agree/i',
        ]

        for pattern in age_patterns:
            try:
                element = await page.query_selector(pattern)
                if element:
                    await element.click()
                    print(f"Clicked age gate with pattern: {pattern}")
                    await page.wait_for_timeout(2000)
                    return
            except:
                continue

        # Strategy 2: Look for buttons/links with specific text
        all_buttons = await page.query_selector_all("button, a, [role='button']")
        for button in all_buttons:
            try:
                text = (await button.inner_text()).lower()
                if any(word in text for word in ['yes', 'enter', 'i am 21', 'i am 18', 'continue', 'confirm']):
                    await button.click()
                    print(f"Clicked age button: {text}")
                    await page.wait_for_timeout(2000)
                    return
            except:
                continue

    except Exception as e:
        print(f"Age verification note: {e}")
        pass

async def scrape_url(url: str) -> ScrapedData:
    """
    Scrape a URL using Playwright to handle JS-rendered content.

    Args:
        url: The URL to scrape

    Returns:
        ScrapedData object with extracted information
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Navigate and wait for JS to load
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)  # Wait for initial load

            # Handle age verification popups
            await handle_age_verification(page)

            # Wait for content to load after dismissing popup
            await page.wait_for_timeout(3000)

            # Check for Dutchie iframe and switch to it if present
            iframe_page = await get_dutchie_iframe(page)
            if iframe_page:
                print("Found Dutchie iframe, scraping from embedded menu...")
                page = iframe_page
                await page.wait_for_timeout(3000)

            # Get page content
            html_content = await page.content()
            html_hash = hashlib.md5(html_content.encode()).hexdigest()

            # Extract data
            strain_name = await extract_strain_name(page, html_content)
            terpenes = await extract_terpenes(page, html_content)
            totals = await extract_totals(page, html_content)
            coa_links = await extract_coa_links(page, html_content, url)

            await browser.close()

            return ScrapedData(
                strain_name=strain_name,
                terpenes=terpenes,
                totals=totals,
                coa_links=coa_links,
                html_hash=html_hash
            )

        except Exception as e:
            await browser.close()
            raise Exception(f"Scraping failed: {str(e)}")

async def extract_strain_name(page: Page, html: str) -> Optional[str]:
    """Extract strain name from various page elements."""
    soup = BeautifulSoup(html, 'html.parser')

    # Try page title
    title = await page.title()
    if title:
        # Clean up common suffixes
        clean_title = re.sub(r'\s*[\|\-–]\s*.*$', '', title)
        if clean_title and len(clean_title) > 2:
            return clean_title.strip()

    # Try h1
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)

    # Try JSON-LD structured data
    json_ld = soup.find('script', type='application/ld+json')
    if json_ld:
        try:
            data = json.loads(json_ld.string)
            if isinstance(data, dict) and 'name' in data:
                return data['name']
        except:
            pass

    # Try meta tags
    meta_product = soup.find('meta', property='og:title')
    if meta_product and meta_product.get('content'):
        return meta_product['content']

    return None

async def extract_terpenes(page: Page, html: str) -> Dict[str, float]:
    """Extract terpene data from page content."""
    soup = BeautifulSoup(html, 'html.parser')
    terpenes = {}

    # Strategy 1: Look for styled-components / Dutchie menu patterns
    # Look for elements with class names like "terpene__Name" or similar
    terpene_elements = soup.find_all(class_=re.compile(r'terpene.*name', re.I))
    if terpene_elements:
        for elem in terpene_elements:
            terp_name = elem.get_text(strip=True).lower()
            # Look for value nearby (sibling, parent, or next elements)
            parent = elem.parent
            if parent:
                # Search in parent for percentage
                parent_text = parent.get_text()
                value_match = re.search(r'(\d+\.?\d*)\s*%', parent_text)
                if value_match:
                    value = float(value_match.group(1))
                    # Normalize terpene name
                    for pattern, standard_name in TERPENE_PATTERNS.items():
                        if re.search(pattern, terp_name, re.I):
                            if value > 10:
                                value = value / 100
                            terpenes[standard_name] = value
                            break

    # Strategy 2: Use Playwright to query dynamic elements
    try:
        # Look for terpene data that might be in dynamic elements
        terpene_containers = await page.query_selector_all('[class*="terpene"], [class*="Terpene"]')
        for container in terpene_containers:
            text = await container.inner_text()
            # Extract terpene name and value from text
            for pattern, standard_name in TERPENE_PATTERNS.items():
                if re.search(pattern, text, re.I):
                    value_match = re.search(r'(\d+\.?\d*)\s*%', text)
                    if value_match:
                        value = float(value_match.group(1))
                        if value > 10:
                            value = value / 100
                        terpenes[standard_name] = value
    except:
        pass  # Fallback to HTML parsing if Playwright query fails

    # Strategy 3: Original regex-based extraction
    if not terpenes:
        text = soup.get_text()
        for pattern, standard_name in TERPENE_PATTERNS.items():
            matches = re.finditer(
                rf'{pattern}\s*:?\s*(\d+\.?\d*)\s*(%|mg/g)?',
                text,
                re.IGNORECASE
            )
            for match in matches:
                value = float(match.group(1))
                if value > 10:
                    value = value / 100
                terpenes[standard_name] = value
                break

    return terpenes

async def extract_totals(page: Page, html: str) -> Totals:
    """Extract total terpenes and cannabinoid data."""
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()

    totals = Totals()

    # Total terpenes
    total_terp_match = re.search(
        r'total\s+terpene[s]?\s*:?\s*(\d+\.?\d*)\s*%?',
        text,
        re.IGNORECASE
    )
    if total_terp_match:
        totals.total_terpenes = float(total_terp_match.group(1))

    # THC/THCa
    thc_match = re.search(r'(?<!a)\bthc\b\s*:?\s*(\d+\.?\d*)\s*%?', text, re.IGNORECASE)
    if thc_match:
        totals.thc = float(thc_match.group(1))

    thca_match = re.search(r'thca\s*:?\s*(\d+\.?\d*)\s*%?', text, re.IGNORECASE)
    if thca_match:
        totals.thca = float(thca_match.group(1))

    # CBD/CBDa
    cbd_match = re.search(r'(?<!a)\bcbd\b\s*:?\s*(\d+\.?\d*)\s*%?', text, re.IGNORECASE)
    if cbd_match:
        totals.cbd = float(cbd_match.group(1))

    cbda_match = re.search(r'cbda\s*:?\s*(\d+\.?\d*)\s*%?', text, re.IGNORECASE)
    if cbda_match:
        totals.cbda = float(cbda_match.group(1))

    return totals

async def extract_coa_links(page: Page, html: str, base_url: str) -> List[str]:
    """Extract COA links from the page."""
    soup = BeautifulSoup(html, 'html.parser')
    coa_links = []

    # Find all links
    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.get_text(strip=True).lower()

        # Check if link text or href matches COA patterns
        is_coa = False
        for pattern in COA_LINK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE) or re.search(pattern, href, re.IGNORECASE):
                is_coa = True
                break

        # Also check for PDF links
        if href.endswith('.pdf'):
            is_coa = True

        if is_coa:
            # Make absolute URL
            if href.startswith('http'):
                coa_links.append(href)
            elif href.startswith('//'):
                coa_links.append('https:' + href)
            else:
                # Relative URL - combine with base
                from urllib.parse import urljoin
                coa_links.append(urljoin(base_url, href))

    # Look for QR codes that might link to COAs
    # (This is a placeholder - actual QR detection would require image processing)
    qr_images = soup.find_all('img', src=re.compile(r'qr|certificate', re.IGNORECASE))
    # Could integrate a QR decoder here in the future

    return list(set(coa_links))  # Remove duplicates

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
    # Store intercepted API data
    intercepted_data = {'product': None, 'responses': []}

    async def handle_response(response):
        """Intercept and capture API responses, especially from Dutchie."""
        try:
            url = response.url

            # Log ALL Dutchie responses for debugging
            if 'dutchie.com' in url:
                print(f"Dutchie response detected: {url} (status: {response.status})")

            # Capture Dutchie API calls (GraphQL and REST)
            if 'dutchie.com' in url and response.status == 200:
                # Look for product data in GraphQL or API endpoints
                if any(keyword in url.lower() for keyword in ['graphql', 'api', 'product', 'menu']):
                    try:
                        data = await response.json()
                        print(f"✓ Intercepted Dutchie API call: {url}")
                        print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                        intercepted_data['responses'].append({
                            'url': url,
                            'data': data
                        })
                        # Try to find product data in response
                        if isinstance(data, dict):
                            # Prioritize IndividualFilteredProduct - this is the main product details API
                            if 'IndividualFilteredProduct' in url:
                                intercepted_data['product'] = data.get('data', data)
                                print(f"  *** PRIORITY: Found IndividualFilteredProduct response ***")
                            # GraphQL responses often have 'data' key - but don't overwrite if we already have priority data
                            elif 'product' not in intercepted_data and 'data' in data:
                                intercepted_data['product'] = data['data']
                                print(f"  Found 'data' key in response")
                            # Some APIs return product directly
                            elif 'product' not in intercepted_data and 'product' in data:
                                intercepted_data['product'] = data['product']
                                print(f"  Found 'product' key in response")
                            elif 'product' not in intercepted_data and 'products' in data:
                                intercepted_data['product'] = data
                                print(f"  Found 'products' key in response")
                    except Exception as json_err:
                        print(f"  Could not parse as JSON: {json_err}")
        except Exception as e:
            print(f"Response handler error: {e}")

    async with async_playwright() as p:
        # Launch in headed mode with stealth settings to bypass anti-bot detection
        # Runs on virtual display via Xvfb (no actual window)
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--window-size=1920,1080',
            ]
        )

        # Create context with realistic settings
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/Chicago',
        )

        page = await context.new_page()

        # Mask webdriver detection
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Overwrite the `plugins` property to use a custom getter
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Overwrite the `languages` property to use a custom getter
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        # Set up response interception before navigation
        page.on("response", handle_response)

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
            else:
                # Try to find Dutchie embed URL in page source and navigate directly
                print("No Dutchie iframe found, checking for embed URL in source...")
                html_content_temp = await page.content()

                # Debug: Check if 'dutchie' appears anywhere in the page
                dutchie_count = html_content_temp.lower().count('dutchie')
                print(f"Found 'dutchie' {dutchie_count} times in page HTML")

                # Try to find any Dutchie-related content
                dutchie_matches = re.findall(r'[^\s]*dutchie[^\s]*', html_content_temp, re.I)
                if dutchie_matches:
                    print(f"Dutchie-related strings found: {dutchie_matches[:5]}")  # Show first 5

                dutchie_embed_match = re.search(
                    r'https://dutchie\.com/embedded-menu/[^\s\'"]+',
                    html_content_temp
                )
                if dutchie_embed_match:
                    dutchie_url = dutchie_embed_match.group(0)
                    print(f"Found Dutchie embed URL: {dutchie_url}")
                    print("Navigating directly to Dutchie menu...")
                    await page.goto(dutchie_url, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(5000)  # Wait for Dutchie menu to load
                else:
                    print("No Dutchie embed URL found in page source")

            # Get page content
            html_content = await page.content()
            html_hash = hashlib.md5(html_content.encode()).hexdigest()

            # Extract data (pass intercepted API data)
            strain_name = await extract_strain_name(page, html_content)
            terpenes = await extract_terpenes(page, html_content, intercepted_data)
            totals = await extract_totals(page, html_content, intercepted_data)
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

def extract_terpenes_from_api(data: dict) -> Dict[str, float]:
    """
    Extract terpene data from API response (Dutchie GraphQL/REST).
    Recursively searches through nested data structures.
    """
    import json
    print(f"DEBUG: API data to extract terpenes from: {json.dumps(data, default=str)[:1000]}")
    terpenes = {}

    def search_for_terpenes(obj, depth=0):
        """Recursively search for terpene data in nested structures."""
        if depth > 10:  # Prevent infinite recursion
            return

        if isinstance(obj, dict):
            # Look for terpene-related keys
            for key, value in obj.items():
                key_lower = key.lower()

                # Found a terpenes array or object
                if 'terpene' in key_lower and isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                extract_terpene_item(item)
                    elif isinstance(value, dict):
                        extract_terpene_item(value)

                # Recurse into nested structures
                elif isinstance(value, (dict, list)):
                    search_for_terpenes(value, depth + 1)

        elif isinstance(obj, list):
            for item in obj:
                search_for_terpenes(item, depth + 1)

    def extract_terpene_item(item: dict):
        """Extract a single terpene name and value from an API item."""
        name = None
        value = None

        # Look for name field (various possible keys)
        for name_key in ['name', 'terpene', 'terpeneName', 'label', 'type']:
            if name_key in item:
                name = str(item[name_key]).lower()
                break

        # Look for value field (various possible keys)
        for value_key in ['value', 'percentage', 'amount', 'percent', 'concentration']:
            if value_key in item:
                try:
                    raw_value = float(item[value_key])
                    print(f"DEBUG: Found terpene '{name}' with raw value {raw_value} from key '{value_key}'")
                    # API values are percentages, convert to fractions
                    # Dutchie returns values like 1.13 meaning 1.13%
                    value = raw_value / 100
                    print(f"DEBUG: Converted to fraction: {value}")
                    break
                except (ValueError, TypeError):
                    pass

        # If we found both name and value, try to match to standard names
        if name and value is not None:
            for pattern, standard_name in TERPENE_PATTERNS.items():
                if re.search(pattern, name, re.I):
                    terpenes[standard_name] = value
                    print(f"DEBUG: Stored {standard_name} = {value}")
                    break

    # Start recursive search
    search_for_terpenes(data)

    return terpenes

async def extract_strain_name(page: Page, html: str) -> Optional[str]:
    """Extract strain name from various page elements."""
    soup = BeautifulSoup(html, 'html.parser')

    # Dutchie-specific: Look for product name in common Dutchie patterns
    # Try data attributes or specific classes
    dutchie_name_selectors = [
        '[data-testid="product-name"]',
        '[class*="ProductName"]',
        '[class*="product-name"]',
        'h1[class*="product"]',
        'h1[class*="Product"]',
    ]

    for selector in dutchie_name_selectors:
        try:
            elem = await page.query_selector(selector)
            if elem:
                name = await elem.inner_text()
                print(f"DEBUG: Selector '{selector}' found: '{name}'")
                if name and len(name.strip()) > 2:
                    # For Dutchie pages with "|" in the name, extract the strain
                    if '|' in name and len(name.split('|')) >= 2:
                        parts = [p.strip() for p in name.split('|')]
                        print(f"DEBUG: Pipe-separated parts: {parts}")

                        # Determine format based on first part:
                        # Format 1: "Brand: Type | Strain Name | Size" (GDF) → use parts[1]
                        # Format 2: "Strain Name | Bud Type" (High Profile) → use parts[0]
                        if ':' in parts[0] or len(parts) >= 3:
                            # Multi-part with brand/type prefix - use second part
                            strain_part = parts[1]
                            print(f"DEBUG: Detected format with brand prefix, using parts[1]")
                        else:
                            # Simple "Strain | Type" format - use first part
                            strain_part = parts[0]
                            print(f"DEBUG: Detected simple format, using parts[0]")

                        # Clean up package numbers (#01, #02, etc.)
                        strain_part = re.sub(r'\s*#\d+.*$', '', strain_part)
                        print(f"DEBUG: Extracted strain from pipe-separated format: '{strain_part}'")
                        if strain_part and len(strain_part) > 2:
                            return strain_part.strip()

                    # Clean up product type suffixes (fallback)
                    name = re.sub(r'\s*[\|\-–].*$', '', name)
                    name = re.sub(r'\s+(flower|bud|strain|cannabis)$', '', name, flags=re.I)
                    print(f"DEBUG: Cleaned name: '{name}'")
                    return name.strip()
        except Exception as e:
            print(f"DEBUG: Selector '{selector}' failed: {e}")
            pass

    # Try page title
    title = await page.title()
    if title:
        print(f"DEBUG: Page title: '{title}'")
        print(f"DEBUG: Page URL: '{page.url}'")

        # Dutchie-specific: Title format is "Brand: Type | Strain Name | Size"
        # Extract the second segment (strain name)
        if '|' in title and ('dutchie' in page.url.lower() or 'dtche[product]' in page.url):
            print(f"DEBUG: Dutchie title format detected")
            parts = [p.strip() for p in title.split('|')]
            print(f"DEBUG: Title parts: {parts}")
            if len(parts) >= 2:
                # Second part is the strain name
                strain_part = parts[1]
                # Clean up package numbers (#01, #02, etc.)
                strain_part = re.sub(r'\s*#\d+.*$', '', strain_part)
                print(f"DEBUG: Extracted strain name: '{strain_part}'")
                if strain_part and len(strain_part) > 2:
                    return strain_part.strip()

        # Fallback: Clean up common suffixes
        clean_title = re.sub(r'\s*[\|\-–]\s*.*$', '', title)
        print(f"DEBUG: Fallback clean_title: '{clean_title}'")
        if clean_title and len(clean_title) > 2:
            return clean_title.strip()

    # Try h1
    h1 = soup.find('h1')
    if h1:
        h1_text = h1.get_text(strip=True)
        # Clean product type suffixes
        h1_text = re.sub(r'\s+(flower|bud|strain|cannabis)$', '', h1_text, flags=re.I)
        return h1_text

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

    # Last resort: extract from URL for Dutchie
    current_url = page.url
    if 'dutchie' in current_url.lower() or 'dtche[product]' in current_url:
        # Extract product ID from URL like: gdf-flower-gaschata-01-3-5g
        product_match = re.search(r'product[/=]([^&/?]+)', current_url, re.I)
        if product_match:
            product_id = product_match.group(1)
            # Clean up product ID to extract strain name
            # Remove common prefixes (gdf-, dispensary codes)
            name = re.sub(r'^[a-z]{2,4}[-_](flower|concentr|extract)[-_]', '', product_id, flags=re.I)
            # Remove weight/package info (01-3-5g, 3-5g, etc.)
            name = re.sub(r'[-_]\d+[-_.]\d+[-_.]?\d*[a-z]*$', '', name, flags=re.I)
            # Replace hyphens/underscores with spaces
            name = name.replace('-', ' ').replace('_', ' ')
            # Capitalize words
            name = ' '.join(word.capitalize() for word in name.split())
            if name and len(name) > 2:
                return name

    return None

async def extract_terpenes(page: Page, html: str, intercepted_data: dict = None) -> Dict[str, float]:
    """Extract terpene data from API responses or page content."""
    terpenes = {}

    # Strategy 0: Check intercepted API data first (most reliable for Dutchie)
    if intercepted_data and intercepted_data.get('product'):
        print("Attempting to extract terpenes from intercepted API data...")
        api_terpenes = extract_terpenes_from_api(intercepted_data['product'])
        if api_terpenes:
            print(f"Successfully extracted {len(api_terpenes)} terpenes from API data")
            return api_terpenes
        else:
            print("No terpenes found in API data, falling back to DOM scraping...")

    # If no API data, fall back to DOM scraping
    print("DEBUG: Starting DOM scraping for terpenes...")
    soup = BeautifulSoup(html, 'html.parser')

    # Strategy 1: Look for styled-components / Dutchie menu patterns
    # Look for elements with class names like "terpene__Name" or similar
    print("DEBUG: Strategy 1 - Looking for terpene class elements...")
    terpene_elements = soup.find_all(class_=re.compile(r'terpene.*name', re.I))
    print(f"DEBUG: Found {len(terpene_elements)} terpene elements")
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
                    # Value is extracted from text with %, so it's a percentage - convert to fraction
                    value = value / 100
                    # Normalize terpene name
                    for pattern, standard_name in TERPENE_PATTERNS.items():
                        if re.search(pattern, terp_name, re.I):
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
                        # Value extracted with %, convert to fraction
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
                unit = match.group(2)
                # If value has % or mg/g unit, or is > 10, it's a percentage
                if unit == '%' or value > 10:
                    value = value / 100
                terpenes[standard_name] = value
                break

    return terpenes

def extract_totals_from_api(data: dict) -> Totals:
    """
    Extract cannabinoid totals from API response (Dutchie GraphQL/REST).
    Recursively searches through nested data structures.
    """
    totals = Totals()
    found_values = {}

    def search_for_cannabinoids(obj, depth=0):
        """Recursively search for cannabinoid data in nested structures."""
        if depth > 10:  # Prevent infinite recursion
            return

        if isinstance(obj, dict):
            for key, value in obj.items():
                key_lower = key.lower()

                # Look for cannabinoid arrays or objects
                if 'cannabinoid' in key_lower and isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                extract_cannabinoid_item(item)
                    elif isinstance(value, dict):
                        extract_cannabinoid_item(value)

                # Also look for direct fields like thc, cbd, etc.
                elif key_lower in ['thc', 'thca', 'thcv', 'cbd', 'cbda', 'cbdv',
                                   'cbn', 'cbg', 'cbgm', 'cbgv', 'cbc', 'cbcv',
                                   'cbv', 'cbe', 'cbt', 'cbl', 'totalterpenes', 'total_terpenes']:
                    try:
                        val = float(value)
                        # Dutchie API returns percentage values (e.g., 24.45 = 24.45%)
                        # Convert to fraction (e.g., 0.2445 = 24.45%)
                        if val > 1:  # If > 1, it's a percentage value that needs conversion
                            val = val / 100
                        found_values[key_lower] = val
                    except (ValueError, TypeError):
                        pass

                # Recurse into nested structures
                elif isinstance(value, (dict, list)):
                    search_for_cannabinoids(value, depth + 1)

        elif isinstance(obj, list):
            for item in obj:
                search_for_cannabinoids(item, depth + 1)

    def extract_cannabinoid_item(item: dict):
        """Extract cannabinoid name and value from an API item."""
        name = None
        value = None

        # Look for name field
        for name_key in ['name', 'cannabinoid', 'type', 'label']:
            if name_key in item:
                name = str(item[name_key]).lower()
                break

        # Look for value field
        for value_key in ['value', 'percentage', 'amount', 'percent']:
            if value_key in item:
                try:
                    value = float(item[value_key])
                    # Dutchie API returns percentage values
                    # Convert to fraction if > 1 (e.g., 24.45 → 0.2445)
                    if value > 1:
                        value = value / 100
                    break
                except (ValueError, TypeError):
                    pass

        # Map to standard names (check longer names first to avoid false matches)
        if name and value is not None:
            name_clean = name.replace(' ', '').replace('-', '').replace('_', '').lower()

            # Match cannabinoids (order matters - check longer strings first)
            if 'totalterpenes' in name_clean or ('terpene' in name_clean and 'total' in name_clean):
                found_values['total_terpenes'] = value
            elif 'thca' in name_clean:
                found_values['thca'] = value
            elif 'thcv' in name_clean:
                found_values['thcv'] = value
            elif 'thc' in name_clean:
                found_values['thc'] = value
            elif 'cbda' in name_clean:
                found_values['cbda'] = value
            elif 'cbdv' in name_clean:
                found_values['cbdv'] = value
            elif 'cbd' in name_clean:
                found_values['cbd'] = value
            elif 'cbgm' in name_clean:
                found_values['cbgm'] = value
            elif 'cbgv' in name_clean:
                found_values['cbgv'] = value
            elif 'cbg' in name_clean:
                found_values['cbg'] = value
            elif 'cbcv' in name_clean:
                found_values['cbcv'] = value
            elif 'cbc' in name_clean:
                found_values['cbc'] = value
            elif 'cbn' in name_clean:
                found_values['cbn'] = value
            elif 'cbv' in name_clean:
                found_values['cbv'] = value
            elif 'cbe' in name_clean:
                found_values['cbe'] = value
            elif 'cbt' in name_clean:
                found_values['cbt'] = value
            elif 'cbl' in name_clean:
                found_values['cbl'] = value

    # Start recursive search
    search_for_cannabinoids(data)

    # Assign found values to Totals object
    for key in ['thc', 'thca', 'thcv', 'cbd', 'cbda', 'cbdv',
                'cbn', 'cbg', 'cbgm', 'cbgv', 'cbc', 'cbcv',
                'cbv', 'cbe', 'cbt', 'cbl', 'total_terpenes']:
        if key in found_values:
            setattr(totals, key, found_values[key])

    # Handle alternative key names
    if 'totalterpenes' in found_values and not totals.total_terpenes:
        totals.total_terpenes = found_values['totalterpenes']

    return totals

async def extract_totals(page: Page, html: str, intercepted_data: dict = None) -> Totals:
    """Extract total terpenes and cannabinoid data from API or page content."""
    # Strategy 0: Check intercepted API data first
    if intercepted_data and intercepted_data.get('product'):
        print("Attempting to extract totals from intercepted API data...")
        api_totals = extract_totals_from_api(intercepted_data['product'])
        # Check if we found any data
        if (api_totals.thc or api_totals.thca or api_totals.cbd or
            api_totals.cbda or api_totals.total_terpenes):
            print("Successfully extracted cannabinoid data from API")
            return api_totals

    # If no API data, fall back to DOM scraping
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

    # Extract all cannabinoids systematically (order matters - check longer names first)
    cannabinoid_patterns = [
        ('thca', r'\bthca\b'),
        ('thcv', r'\bthcv\b'),
        ('thc', r'(?<!a)(?<!v)\bthc\b'),  # Negative lookbehind to avoid matching thca/thcv
        ('cbda', r'\bcbda\b'),
        ('cbdv', r'\bcbdv\b'),
        ('cbd', r'(?<!a)(?<!v)\bcbd\b'),
        ('cbgm', r'\bcbgm\b'),
        ('cbgv', r'\bcbgv\b'),
        ('cbg', r'(?<!m)(?<!v)\bcbg\b'),
        ('cbcv', r'\bcbcv\b'),
        ('cbc', r'(?<!v)\bcbc\b'),
        ('cbn', r'\bcbn\b'),
        ('cbv', r'\bcbv\b'),
        ('cbe', r'\bcbe\b'),
        ('cbt', r'\bcbt\b'),
        ('cbl', r'\bcbl\b'),
    ]

    for field_name, pattern in cannabinoid_patterns:
        match = re.search(rf'{pattern}\s*:?\s*(\d+\.?\d*)\s*%?', text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            # Convert percentage to fraction if needed (e.g., 24.45 → 0.2445)
            if value > 1:
                value = value / 100
            setattr(totals, field_name, value)

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

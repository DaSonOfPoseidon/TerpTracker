# Ideas

## Core Improvements

### Testing & Reliability

- CI/CD pipeline (GitHub Actions) for automated test runs on PR
- End-to-end tests with Playwright for the full analysis flow
- Test coverage reporting and minimum coverage thresholds

### Additional Scraper Support

- Vendor-specific parsers for Weedmaps, Leafly, Jane, iHeartJane
- Currently Dutchie-focused — other platforms have different DOM structures
- Each parser extracts terpenes, cannabinoids, strain name, and COA links
- Fallback to generic regex extraction for unknown sites

## Analysis & Classification

### Strain Recommendations

- "If you liked X, try Y" based on similar terpene profiles
- Use the 50k+ strain DB to find nearest-neighbor matches by terpene vector distance
- Filter recommendations by availability, category, or specific terpene preferences
- Could power a "Similar Strains" section on every result card

### Strain Comparison

- Side-by-side terpene profile comparison for 2-3 strains
- Radar charts overlaid to visualize differences at a glance
- Highlight key differentiators (e.g. "Strain A has 3x more Limonene")
- Compare SDP categories, cannabinoid ratios, and expected effects

## User Experience

### Search History & Favorites

- localStorage-backed recent searches on the homepage
- Favorites/bookmarks list (pre-accounts, local-only; synced once accounts exist)
- Quick re-analyze button for previous searches
- Clear history option for privacy

### Search Results UX

- After any search (URL or strain name), show a "Mark as Tried" button on the results page
- Lets users quickly build their tried list from normal usage
- Marking as tried immediately prompts: did you like it or not?
- If disliked, allow free-text notes explaining why
- Extract keywords from dislike notes (e.g. "too sleepy", "harsh", "anxiety")
- Use those keywords to surface "why you may not like this strain" warnings on similar strains

### Shareable Results

- Permalink URLs for analysis results (e.g. `/results/{hash}`)
- Share buttons for social media (Twitter/X, Reddit, etc.)
- Export result card as image or PDF for offline sharing
- OG meta tags for rich link previews when sharing URLs

### Supported Sites Guide

- Document which dispensary sites work well (Dutchie-powered stores)
- Which sites partially work and what data to expect
- Help users understand what URLs to paste and what results look like
- Community-contributed list of confirmed working URLs

### Stats Dashboard

- Public stats page: total strains in DB, category distribution pie chart
- Most-analyzed strains leaderboard, newest additions
- Breakdown by data source (dataset vs user-submitted vs API)
- Fun stats: most common dominant terpene, rarest profiles, etc.

## Accounts & Personalization

### User Accounts

- User registration and login
- Ability to like and dislike strains
- Saved preferences used to predict whether a user would enjoy a strain
- Minimum info needed to allow users to create accounts? What considerations are needed

### Receipt Upload

- Users can upload dispensary receipts (image/photo)
- OCR/image processing extracts strain names from the receipt
- Matched strains get added to the user's "tried" list automatically
- Prompt user to rate each strain immediately after processing
- Unrated strains stay in "tried" list until the user goes back and rates yay or nay

## Stretch Goals

### Browser Extension

- Works with Dutchie webstore pages
- Shows SDP strain type in realtime on listing pages (ideal)/ in a popup (if we can't do DOM injection)
- Indicates whether the user would likely enjoy each strain based on their saved likes/dislikes

### PWA / Offline

- Add service worker for offline access to previously viewed results
- Fix missing PWA icons (manifest exists but icons may be incomplete)
- Add "Add to Home Screen" prompt on mobile
- Cache the strain autocomplete index for offline fuzzy search

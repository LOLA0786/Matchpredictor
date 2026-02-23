"""
OddsPortal scraper using Playwright (handles JavaScript rendering).
"""
import asyncio, csv, time
from pathlib import Path
from playwright.async_api import async_playwright
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import DATA_RAW

OUTPUT_DIR = DATA_RAW / "oddsportal"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

URLS = {
    "ipl_2024": "https://www.oddsportal.com/cricket/india/indian-premier-league-2024/results/",
    "ipl_2023": "https://www.oddsportal.com/cricket/india/indian-premier-league-2023/results/",
    "t20wc_2024": "https://www.oddsportal.com/cricket/world/icc-men-s-t20-world-cup-2024/results/",
}

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page    = await browser.new_page()

        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

        all_matches = []

        for league, url in URLS.items():
            print(f"\n  Scraping: {league}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)

                # Scroll to load all matches
                for _ in range(5):
                    await page.keyboard.press("End")
                    await page.wait_for_timeout(1000)

                # Extract rows
                rows = await page.query_selector_all("div[class*='eventRow']")
                print(f"  Found {len(rows)} match rows")

                for row in rows:
                    try:
                        # Teams
                        teams = await row.query_selector_all("a[class*='participant']")
                        if len(teams) < 2:
                            continue
                        t1 = await teams[0].inner_text()
                        t2 = await teams[1].inner_text()

                        # Odds
                        odds_els = await row.query_selector_all("div[class*='odds'] p, span[class*='oddsValue']")
                        odds = []
                        for el in odds_els[:2]:
                            txt = await el.inner_text()
                            odds.append(txt.strip())

                        # Date
                        date_el = await row.query_selector("div[class*='date']")
                        date = await date_el.inner_text() if date_el else ""

                        # Match link
                        link_el = await row.query_selector("a[href*='/cricket/']")
                        href = await link_el.get_attribute("href") if link_el else ""

                        match = {
                            "league":   league,
                            "date":     date.strip(),
                            "team1":    t1.strip(),
                            "team2":    t2.strip(),
                            "odds_t1":  odds[0] if odds else "",
                            "odds_t2":  odds[1] if len(odds) > 1 else "",
                            "url":      f"https://www.oddsportal.com{href}",
                        }
                        all_matches.append(match)

                    except Exception:
                        continue

                await asyncio.sleep(3)

            except Exception as e:
                print(f"  Error: {e}")
                continue

        await browser.close()

        # Save
        if all_matches:
            out = OUTPUT_DIR / "all_cricket_odds.csv"
            with open(out, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=all_matches[0].keys())
                writer.writeheader()
                writer.writerows(all_matches)
            print(f"\n  Saved {len(all_matches)} matches to {out}")
        else:
            print("\n  No matches found — OddsPortal may need login or different selectors")

        return all_matches

if __name__ == "__main__":
    asyncio.run(scrape())

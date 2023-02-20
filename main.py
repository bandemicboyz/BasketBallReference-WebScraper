
import time
import os
from playwright.sync_api import sync_playwright,TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
SEASONS = list(range(2016,2023))
#must create these directories
DATA_DIR = "data"
STANDINGS_DIR = os.path.join(DATA_DIR, "standings")
SCORES_DIR = os.path.join(DATA_DIR, "scores")

#Function to retrieve the html will intercept any images to imporve performance of scraping
def get_html(url,selector,sleep = 5,retries = 3):
    html = None
    for i in range(1,retries+1):
        time.sleep(sleep*i)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.route('**/*', intercept)
                page.goto(url)
                print(page.title())
                html = page.inner_html(selector)
        except PlaywrightTimeout:
            print(f'time out on this page {url}')
            continue
        else:
            break
    return html

#function to intercept traffic. easily customized
def intercept(route,request):
    if request.resource_type in {'image'}:
        route.abort()
    else:
        route.continue_()

#this scrapes through each month in a season and collects each game then will save to the standings directory initialized ealrier
def scrape_season(season):
    url = f"https://www.basketball-reference.com/leagues/NBA_{season}_games.html"
    html = get_html(url, "#content .filter")
    # print(html)
    soup = BeautifulSoup(html,features="html.parser")
    links = soup.find_all("a")
    standings_pages = [f"https://www.basketball-reference.com{l['href']}" for l in links]

    for url in standings_pages:
        save_path = os.path.join(STANDINGS_DIR, url.split("/")[-1])
        if os.path.exists(save_path):
            continue

        html = get_html(url, "#all_schedule")
        with open(save_path, "w+",encoding="utf-8") as f:
            f.write(str(html))


for season in SEASONS:
    scrape_season(season)

standings_files = os.listdir(STANDINGS_DIR)

#function to iterate through every game in the standings file and collect the box score of each game
def scrape_game(standings_file):
    with open(standings_file, 'r') as f:
        html = f.read()

    soup = BeautifulSoup(html,features="html.parser")
    links = soup.find_all("a")
    hrefs = [l.get('href') for l in links]
    box_scores = [f"https://www.basketball-reference.com{l}" for l in hrefs if l and "boxscore" in l and '.html' in l]

    for url in box_scores:
        save_path = os.path.join(SCORES_DIR, url.split("/")[-1])
        if os.path.exists(save_path):
            continue

        html = get_html(url, "#content")
        if not html:
            continue
        with open(save_path, "w+",encoding="utf-8") as f:
            f.write(html)

for season in SEASONS:
    files = [s for s in standings_files if str(season) in s]

    for f in files:
        filepath = os.path.join(STANDINGS_DIR, f)

        scrape_game(filepath)




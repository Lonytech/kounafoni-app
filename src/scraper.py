import unicodedata
from pathlib import Path

import dateparser
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from models import ScrapDate


class MaliJetDataScraper:
    def __init__(self, date_range: ScrapDate):
        self.date_range = date_range
        self.begin_date = date_range.begin_date
        self.end_date = date_range.end_date
        self.columns = ["title", "source_paper", "date", "link", "content"]

    @staticmethod
    def get_soup_parser(url):
        response = requests.get(url)
        return BeautifulSoup(response.text, "html.parser")

    def get_mali_jet_page_list_of_articles(self, num_page):
        soup = self.get_soup_parser(
            url=f"https://malijet.com/a_la_une_du_mali/?page={num_page}"
        )
        articles = soup.find("div", id="v_container").find_all("div", class_="card")
        titles, source_papers, dates, links = [], [], [], []
        print("Getting list of articles...")
        for article in tqdm(articles[:-1]):
            header = article.find("div", class_="card-header")
            link = header.find("a", href=True)
            title = (
                None
                if not header
                else unicodedata.normalize("NFKD", header.text.strip().split("\n")[-1])
            )
            infos = article.find("div", class_="card-body")
            infos = None if not infos else infos.text.strip().split("\n")

            titles.append(title)
            source_papers.append(None if not infos else infos[0])
            dates.append(
                None
                if not infos or not dateparser.parse(infos[1])
                else dateparser.parse(infos[1]).date()
            )
            links.append(unicodedata.normalize("NFKD", link["href"]))
            # print("*"*100)
        return pd.DataFrame(
            {
                "title": titles,
                "source_paper": source_papers,
                "date": dates,
                "link": links,
            }
        )

    def fetch_article_content(self, article_link):
        soup = self.get_soup_parser(url=article_link)

        # get content
        content = " ".join(
            paragraph.text
            for paragraph in soup.find_all("div", dir="auto")
            if not paragraph.text.isspace()
        )

        # TODO : We must implement a way to parse the article's author and return it as a tuple with "content"
        # author = ""

        if content != "":
            return content
        else:
            large_paragraphs = (
                soup.find("div", class_="card-header")
                .text.split("Date : ")[1]
                .split("À lire aussi \n\n\n")
            )
            if len(large_paragraphs) > 1:
                large_paragraphs[1] = large_paragraphs[1].split("\n\n\n\n")[
                    -1
                ]  # take the text after "A lire aussi"
            final_content = " ".join(large_paragraphs)
            return (
                unicodedata.normalize("NFKD", " ".join(final_content.split("\n")[1:]))
                .strip()
                .replace("     ", " ")
            )

    def get_new_articles(self, save_directory):
        # Collecting a list of articles
        page_number = 1
        articles_to_fetch_df = pd.DataFrame(columns=self.columns)

        current_date = self.end_date
        while self.begin_date <= current_date:
            print(f"fetching article from page {page_number} ...")
            articles_to_fetch_df = pd.concat(
                [
                    articles_to_fetch_df,
                    self.get_mali_jet_page_list_of_articles(page_number),
                ]
            )
            page_number += 1
            current_date = articles_to_fetch_df.date.min()

        # Selecting new subset and scraping them
        subset_fetching_articles_df = articles_to_fetch_df.query(
            "date >= @self.begin_date and date <= @self.end_date"
        ).copy()
        article_contents, new_titles = [], []
        read_source = pd.read_csv(save_directory, sep="\t")

        # check on dataframe source
        if read_source.empty:
            existing_article_titles = []
        else:
            existing_article_titles = read_source["title"].tolist()

        for _, row in tqdm(
            subset_fetching_articles_df.iterrows(),
            total=subset_fetching_articles_df.shape[0],
        ):
            if row.title not in existing_article_titles:
                new_titles.append(row.title)
                article_contents.append(self.fetch_article_content(row.link))
        if article_contents:
            print("New articles found, writing article contents to file...")
            subset_fetching_articles_df.query("title in @new_titles").assign(
                content=article_contents
            ).to_csv(save_directory, mode="a", sep="\t", index=False, header=False)
        else:
            print("No new articles found, skipping...")


if __name__ == "__main__":
    START_DATE = "2024-05-22"
    END_DATE = dateparser.date.datetime.today().date()

    scraper = MaliJetDataScraper(
        date_range=ScrapDate(end_date=END_DATE, begin_date=START_DATE)
    )

    CSV_DIR = Path(__file__).parents[1] / "data" / "malijet" / "source.csv"

    if not CSV_DIR.exists():
        if not CSV_DIR.parent.exists():
            CSV_DIR.parent.mkdir(parents=True)
        pd.DataFrame(columns=scraper.columns).to_csv(CSV_DIR, sep="\t", index=False)
    scraper.get_new_articles(save_directory=CSV_DIR)

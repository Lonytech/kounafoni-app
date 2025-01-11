import unicodedata
from datetime import date, datetime
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
    def get_soup_parser(url: str) -> BeautifulSoup:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/75.0.3770.80 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        return BeautifulSoup(response.text, "html.parser")

    @staticmethod
    def date_encoding_replacer(date_text: str) -> str:
        replace_map = {
            "ao�t": "août",
            "f�vrier": "février",
            "d�cembre": "décembre",
        }
        for k, v in replace_map.items():
            date_text = date_text.replace(k, v)
        return date_text

    @staticmethod
    def find_associated_path(list_of_dates: list[date]) -> dict[date, Path]:
        date_path_map = dict()
        for d in set(list_of_dates):
            date_path_map[d] = (
                Path(__file__).parents[1]
                / "data"
                / "malijet"
                / f"{d.year}"
                / f"{d.month:02d}"
                / f"{d.day:02d}.csv"
            )
        return date_path_map

    def get_mali_jet_page_list_of_articles(self, num_page: int) -> pd.DataFrame:
        soup = self.get_soup_parser(
            url=f"https://malijet.com/a_la_une_du_mali/?page={num_page}"
        )
        print(f"https://malijet.com/a_la_une_du_mali/?page={num_page}")
        print(soup)
        print(soup.find("div"))
        print(soup.find("div", id="v_container"))
        articles = soup.find("div", id="v_container").find_all("div", class_="card")

        # init necessary variables
        titles: list[str | None] = []
        source_papers: list[str | None] = []
        dates: list[date | None] = []
        links: list[str] = []
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
            infos = (
                None
                if not infos
                else [info for info in infos.text.strip().split("\n") if info != ""]
            )

            titles.append(title)
            source_papers.append(None if not infos else infos[0])
            if not infos or not dateparser.parse(self.date_encoding_replacer(infos[1])):
                dates.append(None)
            else:
                found_date = dateparser.parse(self.date_encoding_replacer(infos[1]))
                if found_date:
                    dates.append(found_date.date())
            links.append(unicodedata.normalize("NFKD", link["href"]))

        return pd.DataFrame(
            {
                "title": titles,
                "source_paper": source_papers,
                "date": dates,
                "link": links,
            }
        )

    def fetch_article_content(self, article_link: str) -> str:
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

    def get_new_articles(self) -> None:
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
            articles_to_fetch_df["date"] = pd.to_datetime(
                articles_to_fetch_df["date"]
            ).dt.date

            current_date = articles_to_fetch_df["date"].min()

        # Selecting new subset and scraping them
        subset_fetching_articles_df = articles_to_fetch_df.query(
            "date >= @self.begin_date and date <= @self.end_date"
        ).copy()
        new_titles = []
        date_path_map = self.find_associated_path(
            subset_fetching_articles_df["date"].tolist()
        )

        for _, row in tqdm(
            subset_fetching_articles_df.iterrows(),
            total=subset_fetching_articles_df.shape[0],
        ):
            current_saving_path = date_path_map[row["date"]]
            if current_saving_path.exists():
                existing_article_titles = pd.read_csv(
                    current_saving_path, sep="\t"
                ).title.tolist()
            else:
                # build directory if it doesn't exist
                current_saving_path.parent.mkdir(parents=True, exist_ok=True)
                existing_article_titles = list()

            if row.title not in existing_article_titles:
                new_title = row.title
                article_content = self.fetch_article_content(row.link)

                # store titles of articles
                new_titles.append(row.title)

                print(
                    f"New article found : « {new_title[:50]}... », writing article content to file..."
                )
                is_header_required_as_first_article = not bool(
                    existing_article_titles
                )  # write header only if it is the first article of this specific date

                # get the first article if multiple same title founds and save it
                subset_fetching_articles_df.query("title==@new_title").head(1).assign(
                    content=[article_content]
                ).to_csv(
                    current_saving_path,
                    mode="a",
                    sep="\t",
                    index=False,
                    header=is_header_required_as_first_article,
                )
        if new_titles:
            print(
                f"\n --- {len(new_titles)} new articles successfully written to files in 'data' directory... ---"
            )
        else:
            print("\n --- No new articles found. ---")


if __name__ == "__main__":
    START_DATE = datetime.strptime("2024-09-24", "%Y-%m-%d").date()
    END_DATE = date.today()

    scraper = MaliJetDataScraper(
        date_range=ScrapDate(end_date=END_DATE, begin_date=START_DATE)
    )

    # get all articles "A la Une" from Malijet in the date range given
    scraper.get_new_articles()

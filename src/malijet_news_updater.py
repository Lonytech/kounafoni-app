from datetime import date, timedelta

from scraper import MaliJetDataScraper, ScrapDate

if __name__ == "__main__":

    # Set the range to [yesterday - today] to not forget any article
    today_date = date.today()
    yesterday_date = today_date - timedelta(days=1)

    scraper = MaliJetDataScraper(
        date_range=ScrapDate(end_date=today_date, begin_date=yesterday_date)
    )

    # get all articles "A la Une" from Malijet in the date range given and save them
    scraper.get_new_articles()

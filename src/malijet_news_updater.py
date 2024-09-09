from datetime import date

import dateparser

from scraper import MaliJetDataScraper, ScrapDate

if __name__ == "__main__":

    # Set the range to [yesterday - today] to not forget any article
    # today_date = date.today()
    # yesterday_date = today_date - timedelta(days=1)
    begin_date = "2024-01-01"
    end_date = "2024-09-09"

    begin_date = dateparser.parse(begin_date).date()
    end_date = dateparser.parse(end_date).date()

    scraper = MaliJetDataScraper(
        date_range=ScrapDate(end_date=end_date, begin_date=begin_date)
    )

    # get all articles "A la Une" from Malijet in the date range given and save them
    scraper.get_new_articles()

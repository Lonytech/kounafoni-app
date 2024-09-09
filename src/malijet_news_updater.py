import glob
import os
from datetime import date, timedelta

from google.cloud import storage

from scraper import MaliJetDataScraper, ScrapDate


def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # Initialize a Google Cloud Storage client
    storage_client = storage.Client()
    # storage_client = storage.Client.from_service_account_json("lonytech-github-actions-sa-key.json")

    # Get the bucket
    # bucket = storage_client.bucket(bucket_name)
    bucket = storage_client.get_bucket(bucket_name)

    # Create a blob (object) in the bucket
    blob = bucket.blob(destination_blob_name)

    # Upload the file to GCS
    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")


def upload_directory_to_gcs(
    directory_path: str, dest_bucket_name: str, dest_blob_name: str
):
    rel_paths = glob.glob(directory_path + "/**", recursive=True)
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(dest_bucket_name)
    print("Uploading article files to bucket...")
    for local_file in rel_paths:
        remote_path = f'{dest_blob_name}/{"/".join(local_file.split(os.sep)[1:])}'
        if os.path.isfile(local_file):
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_file)


if __name__ == "__main__":

    # Set the range to [yesterday - today] to not forget any article
    # today_date = date.today()
    # yesterday_date = today_date - timedelta(days=1)
    begin_date = "2024-01-01"
    end_date = "2024-01-01"

    scraper = MaliJetDataScraper(
        date_range=ScrapDate(end_date=end_date, begin_date=begin_date)
    )

    # get all articles "A la Une" from Malijet in the date range given
    scraper.get_new_articles()

    # Calling upload functions for the whole directory
    # upload_directory_to_gcs(
    #     directory_path="data/malijet",
    #     dest_bucket_name="kounafonia-news",
    #     dest_blob_name="data",
    # )

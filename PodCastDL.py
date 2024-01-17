import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

def get_feed_xml(feed_url):
    try:
        response = requests.get(feed_url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching feed: {e}")
        return None

def parse_feed(feed_xml):
    return BeautifulSoup(feed_xml, 'xml')

def create_download_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def extract_enclosure_urls(soup):
    return [enclosure['url'] for enclosure in soup.find_all('enclosure')]

def extract_titles_and_guids(soup):
    titles = [title.text.strip().replace(':', ' -').replace('&amp;', '&') for title in soup.find_all('title')]
    guids = [guid.text.strip() for guid in soup.find_all('guid')]
    return titles, guids

def download_episode(url, title, guid, folder, feed, podarchive_file):
    after_slash = url.split('/')[-1]
    file_name = after_slash.split('?')[0]
    file_extension = file_name.split('.')[-1]
    new_file_name = f"{title}.{file_extension}"

    if f"{feed} • {guid}" in open(podarchive_file).read():
        print(f"Skipping episode \"{title}\" because it has already been downloaded.")
    else:
        print(f"Preparing to download episode \"{title}\" as \"{new_file_name}\"...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            file_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            with tqdm(total=file_size, unit='B', unit_scale=True, desc=title, ncols=80) as progress_bar:
                with open(os.path.join(folder, new_file_name), 'wb') as file:
                    for chunk in response.iter_content(chunk_size=block_size):
                        file.write(chunk)
                        progress_bar.update(len(chunk))
            with open(podarchive_file, 'a') as archive_file:
                archive_file.write(f"{feed} • {guid}\n")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading episode \"{title}\": {e}")

def main():
    # Optional Variables
    FEED = 'http://myfeed.com/rss'
    FOLDER = '/PATH/TO/MY/FOLDER'

    # Input RSS feed URL
    feed_url = input("Enter the RSS feed URL: ") or FEED  # Use FEED if input is empty

    # Create download folder named 'downloaded_podcast'
    folder = 'downloaded_podcast'

    # Check if feed is empty
    if not feed_url:
        print("Error: No feed specified")
        exit()

    # Create destination folder if it doesn't exist
    create_download_folder(folder)

    retry_count = 1
    feed_xml = None

    while not feed_xml and retry_count <= 10:
        feed_xml = get_feed_xml(feed_url)
        retry_count += 1

    if not feed_xml:
        exit()

    soup = parse_feed(feed_xml)

    # Extract data from the feed
    url_list = extract_enclosure_urls(soup)
    title_list, guid_list = extract_titles_and_guids(soup)

    # Set the maximum number of episodes to download
    max_episodes = 9999999

    # Ensure the existence of the podarchive.txt file
    podarchive_file = 'podarchive.txt'
    if not os.path.exists(podarchive_file):
        with open(podarchive_file, 'w'):
            pass

    # User input for start and end episode values
    start_episode = int(input("Enter the start episode (default is 1): ") or 1)
    end_episode = int(input("Enter the end episode (default is maximum): ") or max_episodes)

    for i, url in enumerate(url_list):
        if i >= end_episode:
            break
        if i < start_episode - 1:
            continue

        download_episode(url, title_list[i], guid_list[i], folder, feed_url, podarchive_file)

    print("All downloads complete.")

if __name__ == "__main__":
    main()

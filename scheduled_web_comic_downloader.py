"""Scheduled comic downloader

Write a program that checks the websites of several web comics and automatically
downloads the images if the comic was updated since the program’s last visit.

Your operating system’s scheduler (Scheduled Tasks on Windows, launchd on OS X,
and cron on Linux) can run your Python program once a day.

The Python program itself can download the comic and then copy it to your desktop
so that it is easy to find. This will free you from having to check the website
yourself to see whether it has updated.

For scheduling, use launchd in Mac OS:
https://davidhamann.de/2018/03/13/setting-up-a-launchagent-macos-cron/

Note:
    This only downloads from http://www.lefthandedtoons.com/
    All websites are different, depending on HTML DOMs/tags and class names.

"""
import datetime, shelve, re, bs4, requests, os


def get_soup(url_arg: str) -> bs4.BeautifulSoup:
    """
    Get soup
    Downloads given url with 'requests' and
    converts it to bs4.BeautifulSoup
    :param url_arg: String with url to soupify
    :return: BeautifulSoup object of given URL
    """
    print(f'Downloading page {url_arg}...')
    req = requests.get(url_arg)
    req.raise_for_status()
    return bs4.BeautifulSoup(req.text, 'lxml')


def compare_timestamps(timestamp_arg:str, shelf_arg:shelve.open, url_arg:str) -> bool:
    """
    Compare timestamp of current comic to last downloaded comic
    timestamp of given URL.
    :param timestamp_arg: String with date in 'Month DD, YYYY' format
    :param shelf_arg: 'shelve' object with URLs as keys and 'datetime.date' as values
    :param url_arg: String of given URL
    :return: True if comic's timestamp is after saved timestamp, False otherwise
    """
    comic_date = datetime.datetime.strptime(timestamp_arg, '%B %d, %Y').date()
    shelf_date = shelf_arg[url_arg]
    if comic_date > shelf_date:
        return True
    return False


def check_key(shelf_arg:shelve.open, url_arg:str) -> bool:
    """
    Check if given URL is a key in the given shelf
    :param shelf_arg: 'shelve' obj with URLs as keys
    :param url_arg:
    :return: True if the URL is in the shelf
    """
    keys = shelf_arg.keys()
    if url_arg in keys:
        return True
    return False


def save_comic(comic_url_arg:str, shelf_arg:shelve.open, url_arg:str)->None:
    """
    Downloads given comic URL and saves to desktop
    Update download time of given website URL in given shelf.
    :param comic_url_arg: String URL of comic image
    :param shelf_arg:
    :param url_arg: String URL of website
    :return: None. Comic image is saved to desktop.
    """
    print(f'Downloading image {comic_url_arg}...')
    comic_req = requests.get(comic_url_arg)
    comic_req.raise_for_status()

    # Save
    image_file = open(os.path.join(os.path.expanduser('~/Desktop'), os.path.basename(comic_url_arg)),'wb')
    for chunk in comic_req.iter_content(100000):
        image_file.write(chunk)
    image_file.close()

    now = datetime.datetime.now().date()
    shelf_arg[url_arg] = now
    return None


def main():
    comic_shelf = shelve.open('comic')

    # Download page
    url = 'http://www.lefthandedtoons.com'
    soup = get_soup(url)

    # Get comic url in case it needs to be downloaded
    image_element = soup.select('.comicimage')
    comic_url = image_element[0].get('src')

    # Compare page's timestamp to shelve's
    comit_title_element = soup.select('.comictitlearea')
    if not comit_title_element:
        print('Can not find comic timestampe.')
    else:
        title_text = comit_title_element[0].getText()
        match = re.search('\w+ \d+, \d{4}', title_text)
        if not check_key(comic_shelf, url) or compare_timestamps(match.group(), comic_shelf, url):
            save_comic(comic_url, comic_shelf, url)
    comic_shelf.close()


if __name__ == '__main__':
    main()
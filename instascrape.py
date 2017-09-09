import re
import sys
from datetime import datetime
from time import sleep

import requests

from database import Database

# Don't hammer the proxy!
RATE_LIMIT = 1.5  # seconds


def main():
    user = sys.argv[1]
    db = Database(user)

    proxy = get_proxy()

    session = requests.Session()
    session.headers.update({
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/56.0.2924.87 Safari/537.36'),
        'Origin': 'https://www.instagram.com',
        'Referer': 'https://www.instagram.com/'
    })

    js_user = get_json(session, user, proxy, request='user')
    parse_user(js_user, db)

    total_posts = js_user['user']['media']['count']
    end_cursor = ''
    counter = 0

    while True:
        js_media = get_json(session, user, proxy, end_cursor, request='media')

        post_count = len(js_media['items'])
        for post in range(post_count):
            code = js_media['items'][post]['code']
            post_type = js_media['items'][post]['type']
            timestamp = int(js_media['items'][post]['created_time'])
            date = date_format(timestamp)

            try:
                location = js_media['items'][post]['location']['name']
            except TypeError:
                location = None

            try:
                caption = js_media['items'][post]['caption']['text']
            except TypeError:
                caption = None

            try:
                likes = js_media['items'][post]['likes']['count']
            except TypeError:
                likes = None

            db.write_media(date, post_type, code, likes, location, caption)

            counter += 1
            print(f'{counter}/{total_posts}: {code}')

        if js_media['more_available'] is False:
            return db.commit()
        else:
            end_cursor = js_media['items'][-1]['id']

        sleep(RATE_LIMIT)


def parse_user(js, db):
    """Parse out data from user JSON page and write to user DB table

    :param js: JSON from ?__a=1 user page
    :param db: Database object

    """
    if js['user']['is_private']:
        sys.exit(f'\n[!] Private user\n')

    id = int(js['user']['id'])
    full_name = js['user']['full_name']
    username = js['user']['username']
    bio = js['user']['biography']
    followers = int(js['user']['followed_by']['count'])
    following = int(js['user']['follows']['count'])

    db.write_user(id, full_name, username, bio, followers, following)


def get_proxy():
    print('\n[?] Proxy usage is mandatory to avoid an IP ban.')
    print('[?] Check out for https://www.us-proxy.org for a list.')
    while True:
        proxy = input('[+] Enter proxy: ')
        if not proxy:
            return None

        proxy_pattern = '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\:\d{2,5}$'
        if re.search(proxy_pattern, proxy):
            proxy = {'https': proxy}
            return proxy
        else:
            print('\n[!] Proxy must be in format address:port')


def get_json(session, user, proxy, end_cursor='', request='media'):
    """Retrieve JSON from Instagram

    :param session: Request session to pool connections
    :param user: Instagram user
    :param proxy: The proxy
    :param end_cursor: Indicates the next set of posts to retrieve.
        Example: ?max_id=123456789 means retrieve the next posts AFTER that ID.
    :param reqest: Specify a /media request, or a ?__a=1 user page request

    :returns: JSON response from Instagram

    """
    if request is 'media':
        url = f'https://www.instagram.com/{user}/media/'
        if end_cursor:
            url += f'?max_id={end_cursor}'
    elif request is 'user':
        url = f'https://www.instagram.com/{user}/?__a=1'

    while True:
        try:
            resp = session.get(url, proxies=proxy, timeout=10)
            if resp.status_code == 403:
                print(f'\n[!] Forbidden (403)\007')
                proxy = get_proxy()
            else:
                break
        except (requests.exceptions.ProxyError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectTimeout):
            print('\n[!] Proxy error\007')
            proxy = get_proxy()

    if resp.status_code == 404:
        sys.exit(f'\n[!] User {user} is 404\n')

    try:
        return resp.json()
    except Exception as e:
        sys.exit(f'\n[!] Can\'t decode JSON response\n{e}\n')


def date_format(timestamp: int):
    """Format post timestamp as strftime

    :param timestamp: Timestamp found in json
    :returns: Strftime '2017-09-09 16:48'

    Timestamp is pre-converted to local time by Instagram's servers!

    """
    time = datetime.fromtimestamp(timestamp)
    date = time.strftime('%Y-%m-%d %H:%M')
    return date


if __name__ == '__main__':

    main()

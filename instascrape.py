import argparse
import re
from datetime import datetime
from time import sleep

import requests
import tzlocal

from database import Database


class Instascrape:
    """Scrape data from an instagram user, writing the results to a local db"""

    def __init__(self):
        """Pool connections in order to reduce hanshake packets"""
        args = self.get_args()
        self.user = args.user
        self.proxy = {'https': args.proxy} if args.proxy else None

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/'
        })

    def get_args(self):
        """Parse CLI arguments"""
        parser = argparse.ArgumentParser(description='Instagram post to tumblr')
        parser.add_argument('user', help='Instagram user')
        parser.add_argument('--proxy', help='Proxy support. Addr:Port (192.168.0.1:8080) - Must be HTTPS capable!')
        args = parser.parse_args()

        if args.proxy:
            proxy_pattern = '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\:\d{2,5}$'
            if not re.search(proxy_pattern, args.proxy):
                raise SystemExit(f'\n[!] Error: Proxy must be in the format Address:Port (e.g. 192.168.0.1:8080)\n')
        return args

    def get_json(self, end_cursor=''):
        """Retrieve json from instagram
        
        :param end_cursor: The post id that indicates the next set of posts to retrieve.
                    e.g. ?max_id=123456789 means retrieve the next posts AFTER that ID.
        :returns: json

        """
        url = f'https://www.instagram.com/{self.user}/media/'
        if end_cursor:
            url += f'?max_id={end_cursor}'
        try:
            resp = self.session.get(url, proxies=self.proxy, timeout=10)
        except Exception as e:
            raise SystemExit(f'\n{e}\n')

        if not self.session.headers.get('csrftoken'):
            self.session.headers.update({
                'csrftoken': resp.cookies['csrftoken']
            })

        return resp.json()

    def scrape(self):
        """Loop to scrape data from each json response"""
        end_cursor = ''
        counter = 1
        db = Database(self.user)

        while True:
            js = self.get_json(end_cursor)

            posts = len(js['items'])
            if posts == 0:
                raise SystemExit(f'\nBad/Private User!\n')

            for post in range(posts):
                code = js['items'][post]['code']
                post_type = js['items'][post]['type']
                timestamp = js['items'][post]['created_time']
                date = self.date_format(timestamp)

                try:
                    location = js['items'][post]['location']['name']
                except TypeError:
                    location = None

                try:
                    caption = js['items'][post]['caption']['text'] or None
                except TypeError:
                    caption = None

                try:
                    likes = js['items'][post]['likes']['count']
                except TypeError:
                    likes = None

                db.write(date, post_type, code, likes, location, caption)

                print(f'{counter} - {code}')
                counter += 1

            if js['more_available'] is False:
                return print('\nFinished\n')
            else:
                end_cursor = js['items'][-1]['id']
                if self.proxy:
                    sleep(2)
                else:
                    sleep(6)

    def date_format(self, timestamp):
        """Convert unix timestamp (GMT) to local timezone

        :param timestamp: Unix timestamp (epoch) found in json

        tzlocal module allows conversion to correct day based on local timezone
        e.g. 2AM GMT is actually 6-8 hours earlier in the USA, and a different date

        """
        unix_timestamp = float(timestamp)
        local_timezone = tzlocal.get_localzone()
        local_time = datetime.fromtimestamp(unix_timestamp, local_timezone)
        date = local_time.strftime('%b,%d,%Y')
        return date


if __name__ == '__main__':

    insta = Instascrape()
    insta.scrape()

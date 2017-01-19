import json
import re
import sqlite3
from datetime import datetime
from time import sleep

import requests
import tzlocal

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0'
RATE_LIMIT = 6  # seconds


class Instagram():
    """Instagram user scraper without an API"""

    def __init__(self, user):
        """Initialize the tcp session, database, and other variables

        :param user: The Instagram username

        counter, total_posts, and total_likes are used purely for terminal print out.

        """
        self.session = requests.Session()  # Pool connections so same csrftoken is used
        self.db = Database()
        self.user = user
        self.counter = 0
        self.total_posts = 0
        self.total_likes = 0

    def start(self):
        """Establish variables that will be needed to POST our queries

        We need the end_cursor and user_id to build our first POST payload.
        We need the token so Instagram will allow us to query.

        :returns: Passes POST variables to first_twelve then post_query

        The first 12 posts are found in the initial GET html
        (json formatted inside <script> tags) so we need to parse them out.

        """
        resp = self.session.get(f'https://www.instagram.com/{self.user}/',
                                headers={'user-agent': USER_AGENT})

        if self.bad_username(resp):
            raise SystemExit

        user_id = re.findall(r'owner[":\s{id]+[0-9]+', resp.text)[0][16:]
        end_cursor = re.findall(r'end_cursor\"\:\s\"[0-9]+', resp.text)[0][14:]
        token = resp.cookies['csrftoken']
        headers = {
            'User-Agent': USER_AGENT,
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
            'x-csrftoken': token
        }
        return self.first_twelve(resp.text, user_id, end_cursor, headers)

    def bad_username(self, resp):
        """Check for a private profile or 404 link.

        :param resp: The requests response object
        :returns: True if private or 404, ending the program

        """
        if re.findall(r'is\_private\"\:\strue', resp.text):
            print(f'\nUser {self.user} is private!\n')
            return True
        elif resp.status_code == 404:
            print(f'\nUser {self.user} doesn\'t exist!\n')
            return True

    def first_twelve(self, html, user_id, end_cursor, headers):
        """Parse out the first 12 posts found in the intial GET html

        :param html: The html (string)
        :returns: Required POST variables to post_query

        This method is necessary because the json of the first 12 posts
        is formatted differently than the POST response json.

        """
        jaysun = re.findall(r'sharedData.+\<\/', html)
        jaysun = jaysun[0][13:-3]  # trim so it starts/ends with curly brackets
        j = json.loads(jaysun)  # convert to a dict

        # Traversing deeply nested json makes code look cluttered
        post_count = len(j['entry_data']['ProfilePage'][0]['user']['media']['nodes'])
        self.total_posts = j['entry_data']['ProfilePage'][0]['user']['media']['count']

        for post in range(post_count):
            code = j['entry_data']['ProfilePage'][0]['user']['media']['nodes'][post]['code']
            likes = int(j['entry_data']['ProfilePage'][0]['user']['media']['nodes'][post]['likes']['count'])
            comment_count = int(j['entry_data']['ProfilePage'][0]['user']['media']['nodes'][post]['comments']['count'])

            # likes and comment_count keys are always present even if zero,
            # but caption key will be absent if no caption exists, so except it
            try:
                caption = j['entry_data']['ProfilePage'][0]['user']['media']['nodes'][post]['caption']
            except KeyError:
                caption = None

            timestamp = j['entry_data']['ProfilePage'][0]['user']['media']['nodes'][post]['date']
            date = self.date_format(timestamp)

            self.total_likes += likes
            self.counter += 1
            print(f'{self.counter}/{self.total_posts}')

            self.db.write(date, code, likes, comment_count, caption)

        return self.post_query(user_id, end_cursor, headers)

    def post_query(self, user_id, end_cursor, headers):
        """POST query to receive 12 posts at a time

        :param user_id: Instagram user id from initial GET html
        :param end_cursor: Tells Instagram which posts to send next
        :param headers: The HTTP headers with csrftoken

        If the POST json response includes the key 'has_next_page' set to True,
        then perform another POST query using the updated end_cursor

        """
        while True:
            print('\n[+] Grabbing 12 more posts\n')
            sleep(RATE_LIMIT)

            # A behemoth appears
            payload = f'q=ig_user({user_id})+%7B+media.after({end_cursor}%2C+12)+%7B%0A++count%2C%0A++nodes+%7B%0A++++caption%2C%0A++++code%2C%0A++++comments+%7B%0A++++++count%0A++++%7D%2C%0A++++date%2C%0A++++dimensions+%7B%0A++++++height%2C%0A++++++width%0A++++%7D%2C%0A++++display_src%2C%0A++++id%2C%0A++++is_video%2C%0A++++likes+%7B%0A++++++count%0A++++%7D%2C%0A++++owner+%7B%0A++++++id%0A++++%7D%2C%0A++++thumbnail_src%0A++%7D%2C%0A++page_info%0A%7D%0A+%7D&ref=users%3A%3Ashow'

            resp = self.session.post('https://www.instagram.com/query/', headers=headers, data=payload)
            end_cursor = self.parse_json(resp.json())
            if end_cursor is False:
                print('\nFinished!')
                print(f'Counted {self.total_likes} total likes\n')
                return  # End program

    def parse_json(self, j):
        """Parse json found in POST response

        :param j: The json
        :returns: False if has_next_page is False
        :returns: The next end_cursor if has_next_page is True

        """
        post_count = len(j['media']['nodes'])  # will be 12 unless it's the last page
        for post in range(post_count):
            code = j['media']['nodes'][post]['code']
            likes = int(j['media']['nodes'][post]['likes']['count'])
            comment_count = int(j['media']['nodes'][post]['comments']['count'])

            # likes and comment_count keys are always present even if zero,
            # but caption key will be absent if no caption exists, so except it
            try:
                caption = j['media']['nodes'][post]['caption']
            except KeyError:
                caption = None

            timestamp = j['media']['nodes'][post]['date']
            date = self.date_format(timestamp)

            self.counter += 1
            self.total_likes += likes
            print(f'{self.counter}/{self.total_posts}')

            self.db.write(date, code, likes, comment_count, caption)

        end_cursor = j['media']['page_info']['end_cursor']
        has_next_page = j['media']['page_info']['has_next_page']
        return end_cursor if has_next_page else False

    def date_format(self, timestamp):
        """Convert unix timestamp (GMT) to local timezone

        Called only when a new post is written to the db

        :param timestamp: Unix timestamp found in json

        tzlocal module allows conversion to correct day based on local timezone
        e.g. 2AM GMT is actually 6,7,8 hours earlier in the USA, and a different date

        """
        unix_timestamp = float(timestamp)
        local_timezone = tzlocal.get_localzone()
        local_time = datetime.fromtimestamp(unix_timestamp, local_timezone)
        date = local_time.strftime('%b,%d,%Y')
        return date


class Database:
    """Write instagram posts to database"""

    def __init__(self):
        """Instantiate the database"""
        self.conn = sqlite3.connect(f'{user_account}.db')
        self.cur = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Create tables if they don't already exist"""
        self.cur.execute('CREATE TABLE IF NOT EXISTS users(date TEXT, code TEXT, likes INT, comment_count INT, caption TEXT)')

    def write(self, date, code, likes, comment_count, caption):
        """Insert entries into Database

        :param code: The instagram share link code (instagram.com/p/{code]})
        :param likes: The number of likes the post has
        :param date: The date the post was created

        """
        self.cur.execute('INSERT INTO users VALUES(?, ?, ?, ?, ?)', (date, code, likes, comment_count, caption))
        self.conn.commit()


if __name__ == '__main__':

    user_account = input('Instagram user: ')
    insta = Instagram(user_account)
    insta.start()

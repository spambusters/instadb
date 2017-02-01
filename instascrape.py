import json
import re
import sqlite3
from datetime import datetime
from time import sleep

import requests
import tzlocal

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0'
RATE_LIMIT = 6  # seconds
RETRIEVE = 12  # posts retrieved each loop


class Instagram():
    """Instagram user scraper without an API"""

    def __init__(self, user):
        """Instantiate the TCP session, database, and other variables

        :param user: The Instagram username

        """
        self.db = Database()
        self.user = user
        self.session = requests.Session()  # Pool connections so same csrftoken is used
        self.counter = 0
        self.total_posts = 0

    def start(self):
        """Establish variables that will be needed to POST our queries

        We need the user_id to build our POST payloads.
        We need the csrftoken so Instagram will allow us to query.

        :returns: Passes POST variables to post query loop

        """
        resp = self.session.get(f'https://www.instagram.com/{self.user}/',
                                headers={'user-agent': USER_AGENT})

        if self.bad_username(resp):
            raise SystemExit

        user_id = re.findall(r'owner[":\s{id]+[0-9]+', resp.text)[0][16:]
        token = resp.cookies['csrftoken']
        headers = {
            'User-Agent': USER_AGENT,
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
            'x-csrftoken': token
        }
        self.total_posts =  self.get_total_posts(resp.text)
        return self.post_query(user_id, headers)

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

    def get_total_posts(self, html):
        """Retrieve the total post count from an Instagram user_account

        :param html: The html (string) from the instagram.com/{user} page
        :returns: total post count

        The total post count is embedded in the instagram.com/{user} html,
        formatted as json data inside <script> tags.

        """
        jaysun = re.findall(r'sharedData.+\<\/', html)
        jaysun = jaysun[0][13:-3]  # trim so it starts/ends with curly brackets
        j = json.loads(jaysun)  # convert to a dict
        return j['entry_data']['ProfilePage'][0]['user']['media']['count']

    def post_query(self, user_id, headers):
        """POST query to receive 12 posts at a time

        :param user_id: Instagram user id from initial GET html
        :param headers: The HTTP headers with csrftoken

        If the POST json response includes the key 'has_next_page' set to True,
        then perform another POST query using the updated end_cursor

        Initialize an invalid end_cursor, causing Instagram to default
        retrieve the first 12 posts. From that JSON response we'll
        get the correct end_cursor needed for the next 12 posts.

        """
        end_cursor = 1234567890
        while True:
            # A behemoth appears
            payload = f'q=ig_user({user_id})+%7B+media.after({end_cursor}%2C+{RETRIEVE})+%7B%0A++count%2C%0A++nodes+%7B%0A++++caption%2C%0A++++code%2C%0A++++comments+%7B%0A++++++count%0A++++%7D%2C%0A++++date%2C%0A++++dimensions+%7B%0A++++++height%2C%0A++++++width%0A++++%7D%2C%0A++++display_src%2C%0A++++id%2C%0A++++is_video%2C%0A++++likes+%7B%0A++++++count%0A++++%7D%2C%0A++++owner+%7B%0A++++++id%0A++++%7D%2C%0A++++thumbnail_src%0A++%7D%2C%0A++page_info%0A%7D%0A+%7D&ref=users%3A%3Ashow'

            resp = self.session.post('https://www.instagram.com/query/', headers=headers, data=payload)
            end_cursor = self.parse_json(resp.json())
            if end_cursor is None:
                print('\nFinished!\n')
                break
            print('\n[+] Grabbing more posts\n')
            sleep(RATE_LIMIT)

    def parse_json(self, j):
        """Parse json found in POST response

        :param j: The json
        :returns: False if has_next_page is False
        :returns: The next end_cursor if has_next_page is True

        """
        post_count = len(j['media']['nodes'])  # 12 unless it's the last page
        for post in range(post_count):
            code = j['media']['nodes'][post]['code']
            likes = int(j['media']['nodes'][post]['likes']['count'])
            comment_count = int(j['media']['nodes'][post]['comments']['count'])

            # likes and comment_count keys are always present even if zero,
            # but caption key is only present if caption exists, so except it
            try:
                caption = j['media']['nodes'][post]['caption']
            except KeyError:
                caption = None

            timestamp = j['media']['nodes'][post]['date']
            date = self.date_format(timestamp)

            self.counter += 1
            print(f'{self.counter}/{self.total_posts}')

            self.db.write(date, code, likes, comment_count, caption)

        end_cursor = j['media']['page_info']['end_cursor']
        has_next_page = j['media']['page_info']['has_next_page']
        return end_cursor if has_next_page else None

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
        """Initialize the database"""
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

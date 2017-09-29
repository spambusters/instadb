from datetime import datetime


class Posts:
    """This object holds and accesses the JSON for each page of posts"""

    def __init__(self, js):
        self.js = js

    def num_posts(self):
        """Returns how many posts are in the JSON (default 20)"""
        return len(self.js['items'])

    def date(self, post_num):
        """Return the post date in "2017-12-31 12:30" format"""
        timestamp = int(self.js['items'][post_num]['created_time'])
        time = datetime.fromtimestamp(timestamp)
        date = time.strftime('%Y-%m-%d %H:%M')
        return date

    def post_type(self, post_num):
        """Return the post type (video, photo, or carousel)"""
        return self.js['items'][post_num]['type']

    def code(self, post_num):
        """Return the post shortcode aka share link

        Example:
        https://www.instagram.com/p/{shortcode}/ <--

        """
        return self.js['items'][post_num]['code']

    def likes(self, post_num):
        """Return the number of likes for a post"""
        try:
            likes = self.js['items'][post_num]['likes']['count']
        except TypeError:
            likes = None
        return likes

    def location(self, post_num):
        """Return the post tagged location"""
        try:
            location = self.js['items'][post_num]['location']['name']
        except TypeError:
            location = None
        return location

    def caption(self, post_num):
        """Return the post caption"""
        try:
            caption = self.js['items'][post_num]['caption']['text']
        except TypeError:
            caption = None
        return caption

    def media(self, post_num):
        """Return the post media link (mp4 or jpg)"""
        if 'video' in self.post_type(post_num):
            media = self.js['items'][post_num]['videos']['standard_resolution']['url']
        else:
            img_url = self.js['items'][post_num]['images']['standard_resolution']['url']
            media = img_url.replace('p640x640/', '').replace('s640x640/', '')
        return media

    def more_available(self):
        """Determine if another page of posts is available. True or False"""
        return self.js['more_available']

    def end_cursor(self, post_num):
        """The ID for the post

        Each post will have one, so we'll use the ID from the last post on the
        page to determine which set of posts to retrieve next.

        Example:
        https://www.instagram.com/user/media/?max_id={end_cursor} <--

        """
        return self.js['items'][post_num]['id']

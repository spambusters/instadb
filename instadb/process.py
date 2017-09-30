from datetime import datetime

class Posts:
    """This class holds and accesses the JSON for each page of posts"""

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
        """Return the post media link(s) (mp4 or jpg)

        Carousel posts will return multiple URLs separated by commas.

        """
        post_type = self.post_type(post_num)
        if post_type == 'video':
            media = self.js['items'][post_num]['videos']['standard_resolution']['url']
        elif post_type == 'carousel':
            media = self.carousel_media(post_num)
        else:
            img_url = self.js['items'][post_num]['images']['standard_resolution']['url']
            media = self.clean_img_url(img_url)
        return media

    def carousel_media(self, post_num):
        """Carousel media is its own nested list, so parse out the media
        URLs and return them"""
        media_files = []
        carousel = self.js['items'][post_num]['carousel_media']
        slides = len(carousel)

        for slide in range(slides):
            media_type = carousel[slide]['type']
            if media_type == 'image':
                img_url = media = carousel[slide]['images']['standard_resolution']['url']
                media = self.clean_img_url(img_url)
            elif media_type == 'video':
                media = carousel[slide]['videos']['standard_resolution']['url']
            media_files.append(media)

        # Convert to string for DB
        return (',').join(media_files)

    @staticmethod
    def clean_img_url(img_url):
        """Remove stuff from the image URL that makes it a smaller resolution

        Raw URL:
        https://scontent-atl3-1.cdninstagram.com/t51.2885-15/sh0.08/e35/p640x640/22071003_183507078861288_1653982254898085888_n.jpg

        Cleaned URL:
        https://scontent-atl3-1.cdninstagram.com/t51.2885-15/sh0.08/e35/22071003_183507078861288_1653982254898085888_n.jpg

        Returns:
        Full size image URL

        """
        cleaned_url = img_url.replace('p640x640/', '').replace('s640x640/', '')
        return cleaned_url

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

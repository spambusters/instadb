import os
import sqlite3


class Database:
    """Write Instagram posts to database"""

    def __init__(self, user):
        """Initialize the database"""
        self.conn = sqlite3.connect('{}.db'.format(user))
        self.cur = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Create database table for posts"""
        self.cur.execute(('CREATE TABLE IF NOT EXISTS posts('
                          'date TEXT,'
                          'type TEXT,'
                          'code TEXT,'
                          'likes INT,'
                          'location TEXT,'
                          'caption TEXT,'
                          'media TEXT)'))

    def existing_entry(self, code):
        """Check if a post shortcode already exists in the database"""
        self.cur.execute('SELECT * FROM posts WHERE code="{}"'.format(code))
        post_exists = self.cur.fetchone()
        if post_exists:
            return True

    def write(self, date: str, post_type: str, code: str, likes: int,
              location: str, caption: str, media_files: list):
        """Insert a post into the posts table

        date: Post date & time (2017:08:04 16:12:01)
        post_type: Post type (image, video, carousel)
        code: Post share link code (instagram.com/p/{code]})
        likes: Post likes count
        location: Post tagged location
        caption: Post caption
        media: Post media URL (mp4, jpg)

        """
        print('Adding new db entry: {}'.format(code))
        self.cur.execute('INSERT INTO posts VALUES(?, ?, ?, ?, ?, ?, ?)',
                         (date, post_type, code, likes, location,
                          caption, (',').join(media_files)))
        self.conn.commit()

    def likes_changed(self, code, ig_likes):
        """Check if the likes count for a post needs to be updated

        code: The Instagram shortcode
        ig_likes: The latest likes count from the Instagram post
        returns: True if db likes count needs to be updated

        """
        self.cur.execute('SELECT * FROM posts WHERE code="{}"'.format(code))
        post_exists = self.cur.fetchone()
        if post_exists:
            db_likes = post_exists[3]
        else:
            db_likes = 0
        if ig_likes != db_likes:
            return True

    def update_likes(self, code, ig_likes):
        """Update an existing db entry's likes count

        code: The Instagram shortcode
        ig_likes: The latest likes count from the Instagram post

        """
        print('Updating db likes count for entry: {}'.format(code))
        self.cur.execute('UPDATE posts SET likes=? WHERE code=?',
                         (ig_likes, code))
        self.conn.commit()

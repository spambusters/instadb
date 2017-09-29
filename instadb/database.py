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

    def write(self, date: str, post_type: str, code: str, likes: int,
              location: str, caption: str, media: str):
        """Insert post into media table

        date: Post date & time (2017-08-04 16:12)
        post_type: Post type (image, video, carousel)
        code: Post share link code (instagram.com/p/{code]})
        likes: Post likes count
        location: Post tagged location
        caption: Post caption
        media: Post media URL (mp4, jpg)

        """
        self.cur.execute('INSERT INTO posts VALUES(?, ?, ?, ?, ?, ?, ?)',
                         (date, post_type, code, likes, location,
                          caption, media))
        self.conn.commit()

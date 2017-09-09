import sqlite3


class Database:
    """Write instagram posts to database"""

    def __init__(self, user):
        """Initialize the database"""
        self.conn = sqlite3.connect(f'{user}.db')
        self.cur = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cur.execute(('CREATE TABLE IF NOT EXISTS user('
                          'id INT,'
                          'full_name TEXT,'
                          'username TEXT,'
                          'bio TEXT,'
                          'followers INT,'
                          'following TEXT)'))
        self.cur.execute(('CREATE TABLE IF NOT EXISTS media('
                          'date TEXT,'
                          'type TEXT,'
                          'code TEXT,'
                          'likes INT,'
                          'location TEXT,'
                          'caption TEXT)'))

    def write_user(self,
                   id: int,
                   full_name: str,
                   username: str,
                   bio: str,
                   followers: int,
                   following: int):
        """Insert info into user table"""
        self.cur.execute('INSERT INTO user VALUES(?, ?, ?, ?, ?, ?)',
                         (id, full_name, username, bio, followers, following))
        self.conn.commit()

    def write_media(self,
                    date: str,
                    post_type: str,
                    code: str,
                    likes: int,
                    location: str,
                    caption: str):
        """Insert post into media table

        :param date: Post date & time (2017-08-04 16:12)
        :param post_type: Post type (image, video)
        :param code: Post share link code (instagram.com/p/{code]})
        :param likes: Post likes count
        :param location: Post tagged location
        :param caption: Post caption

        """
        self.cur.execute('INSERT INTO media VALUES(?, ?, ?, ?, ?, ?)',
                         (date, post_type, code, likes, location, caption))
        self.conn.commit()

    def commit(self):
        """Commit all DB changes"""
        self.conn.commit()
        self.conn.close()
        return print('\nFinished\n')

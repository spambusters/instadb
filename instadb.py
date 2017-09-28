import argparse
from time import sleep

from database import Database
from network import Retrieve, check_proxy_format
from process import Posts


def parse_args():
    """Parse arguments from CLI"""
    parser = argparse.ArgumentParser(
        description='Backup an Instagram user to a local sqlite3 database')
    parser.add_argument(
        'user',
        help="Instagram user")
    parser.add_argument(
        '-p', '--proxy',
        help='Proxy must be in the format address:port')
    parser.add_argument(
        '-r', '--rate-limit',
        help='Seconds between Instagram requests (default 1)',
        type=int,
        default=1)
    args = parser.parse_args()

    if args.proxy:
        args.proxy = check_proxy_format(args.proxy)

    return args


def main(user: str, proxy: str, rate_limit: int):
    """Backup an Instagram user's posts to a local sqlite3 database"""
    retrieve = Retrieve(user, proxy)
    db = Database(user)

    counter = 0
    end_cursor = ''
    posts_remaining = True

    print('\nProcessing {}...'.format(user))

    while posts_remaining:
        js = retrieve.get_json(end_cursor)
        posts = Posts(js)
        num_posts = posts.num_posts()

        for post in range(num_posts):
            date = posts.date(post)
            post_type = posts.post_type(post)
            code = posts.code(post)
            likes = posts.likes(post)
            location = posts.location(post)
            caption = posts.caption(post)
            media = posts.media(post)
            end_cursor = posts.end_cursor(post)

            db.write(date, post_type, code, likes, location, caption, media)

            counter += 1
            print('\r{} - {}'.format(counter, code), end='')

        if posts.more_available():
            sleep(rate_limit)
        else:
            posts_remaining = False

    print('\n\nFinished\n')


if __name__ == '__main__':

    ARGS = parse_args()

    try:
        main(ARGS.user, ARGS.proxy, ARGS.rate_limit)
    except KeyboardInterrupt:
        raise SystemExit('\n[!] Interrupted by user\n')

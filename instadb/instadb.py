import argparse
import os
from time import sleep

from database import Database
from metadata import Metadata
from network import Retrieve, correct_proxy_format
from parsejson import JsonPage


def parse_args():
    """Parse arguments from CLI"""
    parser = argparse.ArgumentParser(
        description='Download an Instagram user\'s media plus metadata')
    parser.add_argument(
        'user',
        help='Instagram user')
    parser.add_argument(
        '--proxy',
        help='Proxy must be in the format address:port')
    parser.add_argument(
        '--rate-limit',
        help='Seconds between Instagram requests (default: %(default)s)',
        type=int,
        metavar='LIMIT',  # shortens RATE_LIMIT to LIMIT in --help output
        default=1)
    parser.add_argument(
        '--likes',
        help='Only download media with at least this many likes',
        type=int)
    media_group = parser.add_mutually_exclusive_group()
    media_group.add_argument(
        '--photos',
        help='Only download photos',
        action='store_true'
    )
    media_group.add_argument(
        '--videos',
        help='Only download videos',
        action='store_true'
    )
    parser.add_argument(
        '--path',
        help=('Custom path for saving local files. (default: "$USER/Downloads/instadb/$ig_user/")'),
        metavar='PATH')
    parser.add_argument(
        '--new',
        help=('Only download new media files'),
        action='store_true'
    )

    metadata = parser.add_argument_group('Metadata')
    metadata.add_argument(
        '--tags',
        help=('Space separated media tags (default: [user, "instagram"])'),
        nargs='+',
        metavar='')
    metadata.add_argument(
        '--db',
        help='Write user metadata to an Sqlite3 database',
        action='store_true',
        dest="write_db"
    )
    metadata.add_argument(
        '--only-db',
        help="Skip downloading media files",
        action='store_true'
    )

    args = parser.parse_args()

    if args.proxy:
        if not correct_proxy_format(args.proxy):
            parser.error('\n[!] {} is not address:port\n'.format(args.proxy))
        else:
            args.proxy = {'https': args.proxy}  # format required by requests

    if not args.tags:
        # Add defaults
        #
        # Can't do default=[user, 'instagram'] in --tags add_argument
        # because how would we get the args.user value before parsing?
        args.tags = [args.user, 'instagram']

    return args


def main(user: str, proxy: dict, rate_limit: int, custom_path: str, tags: list,
         min_likes_required: int, only_photos=False, only_videos=False,
         only_new_files=False, write_db=False, only_db=False):
    """Download an Instagram user's media plus metadata

    user: Instagram user
    proxy: Needs to be in requests format -- {'https': '192.168.0.1:8080'}
    rate_limit: Seconds between Instagram requests
    custom_path: Optional custom path for saving media files.
                 Default path is "$USER/Downloads/instadb/$ig_user/"
    tags: List of tags used for metadata
    min_likes_required: Only download media with at least this many likes
    only_photos: Only download photos
    only_videos: Only download videos
    only_new_files: Only download new media files
    write_db: Write user metadata to an Sqlite3 database
    only_db: Skip downloading media files

    """
    retrieve = Retrieve(proxy)
    base_url = 'https://www.instagram.com/{}/media/'.format(user)
    mk_downloads_dir(user, custom_path)

    if write_db or only_db:
        db = Database(user)

    post_counter = 0
    end_cursor = ''
    posts_remaining = True

    while posts_remaining:
        # Let's print some animated progress dots (...)
        print('\nGrabbing 20 posts', end='')
        for i in range(3):
            print('.', end='', flush=True)
            sleep(rate_limit / 3)
        print('\n')

        resp = retrieve.get(base_url, end_cursor)
        posts = JsonPage(resp)
        num_posts = posts.num_posts()

        for post in range(num_posts):
            post_counter += 1

            date = posts.date(post)
            post_type = posts.post_type(post)
            code = posts.code(post)
            likes = posts.likes(post)
            location = posts.location(post)
            caption = posts.caption(post)
            media_files = posts.media(post)
            end_cursor = posts.end_cursor(post)

            if (write_db or only_db) and db.existing_entry(code) and only_new_files:
                print('No more new files!')
                posts_remaining = False
                continue  # to next post. after these 20, program will end
            elif (write_db or only_db) and not db.existing_entry(code):
                db.write(date, post_type, code, likes, location, caption, media_files)
            elif (write_db or only_db) and db.likes_changed(code, likes):
                db.update_likes(code, likes)

            if only_db:
                print('{}: {} - {}'.format(post_counter, user, code))
                continue  # to next post, skipping the media download

            if min_likes_required and likes < min_likes_required:
                continue  # to next post

            # This should reset each post iteration, but shouldn't be reset
            # each media file iteration, so establish it outside media loop.
            carousel_counter = 1

            for media in media_files:
                file_ext = media.split('.')[-1]
                filename = '{} - {}.{}'.format(user, code, file_ext)

                if post_type == 'carousel':
                    # Insert a counter in the filename after the shortcode
                    #
                    # Example:
                    # sportscenter - BaXyursFd2k (1).jpg
                    # sportscenter - BaXyursFd2k (2).mp4
                    # sportscenter - BaXyursFd2k (3).jpg
                    filename = filename.replace('.{}'.format(file_ext),
                                                ' ({}).{}'.format(carousel_counter,
                                                                  file_ext))
                    carousel_counter += 1

                # Place this logic after carousel counter increment.
                # If later on we don't specify just --photos or --videos, the
                # missing files that are filled in will be correctly numbered.
                if only_photos and file_ext != 'jpg':
                    continue  # to next media file
                if only_videos and file_ext != 'mp4':
                    continue  # to next media file

                if not os.path.exists(filename):
                    data = retrieve.get(media)
                    with open(filename, 'wb') as file:
                        file.write(data.content)
                    print('{}: {}'.format(post_counter, filename))
                    Metadata(user, filename, date, code, caption, tags)
                    sleep(rate_limit)  # between each (.mp4, .jpg) request
                elif only_new_files:
                    print('No more new files!')
                    posts_remaining = False
                else:
                    print('{}: {} already exists!'.format(post_counter, filename))

        if not posts.more_available():
            posts_remaining = False

    print('\nFinished\n')


def mk_downloads_dir(user, custom_path):
    """Create the downloads directory for the Instagram user.

    user: The Instagram user
    custom_path: An optional custom path defined by the --path CLI arg
                 Default path is "$USER/Downloads/instadb/$ig_user/"

    """
    if custom_path:
        downloads_dir = custom_path
    else:
        downloads_dir = os.path.expanduser(os.path.join('~', 'Downloads', 'instadb', user))
    try:
        os.makedirs(downloads_dir, exist_ok=True)
    except PermissionError:
        raise SystemExit('\n[!] PermissionError creating downloads folder "{}"\n'.format(downloads_dir))
    os.chdir(downloads_dir)


if __name__ == '__main__':

    ARGS = parse_args()
    try:
        main(ARGS.user, ARGS.proxy, ARGS.rate_limit, ARGS.path, ARGS.tags,
             ARGS.likes, ARGS.photos, ARGS.videos, ARGS.new, ARGS.write_db,
             ARGS.only_db)
    except KeyboardInterrupt:
        raise SystemExit('\n\n[!] Interrupted by user\n')

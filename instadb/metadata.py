import os
import re
import string
import subprocess

try:
    from mutagen.mp4 import MP4, MP4StreamInfoError
except ImportError:
    raise SystemExit('\n[!] Mutagen not installed\npip3 install mutagen\n')


def process_video(filename: str, user: str, date=None, caption=None,
                  tags=None, code=None):
    """Use Mutagen to embed metadata to a video file

    filename: This can be a cwd file or a full PATH
        Example: 'image.jpg' or '/home/you/Pictures/image.jpg'

    user: Username
        Example: 'sportscenter'

    date: Formatted as YYYY:MM:DD HH:MM:SS
        Example: '2016:12:25 06:03:49'

    caption: Caption
        Example: 'This is a caption'

    tags: List of tags.
        Example: ['single tag'] or ['multiple', 'tags']

    code: Add an Instagram shortcode to the title
        Example: 'BapbIcAFsCL'

    """
    title = user
    if code:
        title += ' - {}'.format(code)

    try:
        video = MP4(filename)
    except MP4StreamInfoError:
        print('\n[!] Can\'t write tags for {}'.format(filename))
        print('[!] It probably didn\'t download correctly\n')
        return

    video.delete()  # existing metadata

    video['\xa9nam'] = title

    if caption:
        video['desc'] = caption
        video['ldes'] = caption  # Long
        video['\xa9cmt'] = caption[:255]  # Comment

    if date and correct_date_format(date):
        video['purd'] = date  # Purchase Date
        video['\xa9day'] = date.split(':')[0]  # Year

    if tags and isinstance(tags, list):
        video['\xa9gen'] = ','.join(tags)  # Genres
        video['keyw'] = ','.join(tags)  # Podcast Keywords

    video['\xa9ART'] = user  # Arist
    video['cprt'] = user  # Copyright
    video['----:com.apple.iTunes:iTunMOVI'] = xml_tags(user)  # Actor

    video.save()


def xml_tags(user):
    """Build XML tags for a video file

    Only XML we're doing right now is for the "Actor" (user)

    """
    output = ('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC '
              '"-//Apple//DTD PLIST 1.0//EN" '
              '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
              '<plist version="1.0"><dict>\n')
    output += '<key>cast</key><array>\n'
    output += '<dict><key>name</key><string>{}</string></dict>\n'.format(user)
    output += '</array>\n'
    output += '</dict></plist>\n'

    # String must be made into bytes or Mutagen throws a fit
    return output.encode('UTF-8')


def process_image(filename: str, user: str, date=None, caption=None,
                  tags=None, code=None):
    """Use exiftool to embed metadata to an image file

    filename: This can be a cwd file or a full PATH
        Example: 'image.jpg' or '/home/you/Pictures/image.jpg'

    user: Username
        Example: 'sportscenter'

    date: Formatted as YYYY:MM:DD HH:MM:SS
        Example: '2016:12:25 06:03:49'

    caption: Caption
        Example: 'This is a caption'

    tags: List of tags.
        Example: ['single tag'] or ['multiple', 'tags']

    code: Add an Instagram shortcode to the title
        Example: 'BapbIcAFsCL'

    """
    if not os.path.exists(filename):
        raise SystemExit('\n[!] Can\'t find {}\n'.format(filename))

    title = user
    if code:
        title += ' - {}'.format(code)

    try:
        subprocess.run(['exiftool', '{}'.format(filename),
                        '-XPSubject={}'.format(user),  # Exif
                        '-XPAuthor={}'.format(user),  # Exif
                        '-Artist={}'.format(user),  # Exif
                        '-Credit={}'.format(user),  # Iptc
                        '-Copyright={}'.format(user),  # Exif
                        '-Headline={}'.format(title),  # Iptc
                        '-Title={}'.format(title),  # XMP
                        '-overwrite_original', '-q'])
    except FileNotFoundError:
        raise SystemExit('\n[!] Can\'t find exiftool in the system PATH. '
                         'Did you install it?\n')

    if tags and isinstance(tags, list):
        for tag in tags:
            subprocess.run(['exiftool', '{}'.format(filename),
                            '-Keywords+={}'.format(tag),  # Iptc
                            '-overwrite_original', '-q'])

    if caption:
        caption = remove_unicode(caption)
        subprocess.run(['exiftool', '{}'.format(filename),
                        '-UserComment={}'.format(caption),  # Exif
                        '-Description={}'.format(caption),  # XMP
                        '-Caption={}'.format(caption),  # Iptc
                        '-XPComment={}'.format(caption),  # Exif
                        '-overwrite_original', '-q'])

    if date and correct_date_format(date):
        subprocess.run(['exiftool', '{}'.format(filename),
                        '-DateTimeOriginal={}'.format(date),  # Exif
                        '-overwrite_original', '-q'])
        # Set the modification date.
        #
        # This has to be done separate from -DateTimeOriginal
        # being added or else it doesn't work.
        subprocess.run(['exiftool', '{}'.format(filename),
                        '-FileModifyDate<DateTimeOriginal',
                        '-overwrite_original', '-q'])


def remove_unicode(caption):
    """Remove emojis and other unicode from metadata caption for photos

    XMP can handle emojis, but Exif UserComment can't. This is what's used by
    Shotwell to display captions, and unicode makes it blank.

    """
    bad_chars = [char for char in caption if char not in string.printable]
    if bad_chars:
        for char in bad_chars:
            caption = caption.replace(char, '')
    return caption


def correct_date_format(date):
    """Check if provided date is correctly formatted as YYYY:MM:DD HH:MM:SS"""
    date_pattern = r'^\d{4}\:\d{2}:\d{2}\s\d{2}:\d{2}:\d{2}$'
    if re.search(date_pattern, date):
        return True

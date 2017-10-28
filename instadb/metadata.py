import subprocess
import string

try:
    from mutagen.mp4 import MP4
except ImportError:
    raise SystemExit('\n[!] Mutagen not installed\npip3 install mutagen\n')


class Metadata:
    """Process a downloaded media file by writing its metadata"""

    def __init__(self, user, filename, date, code, caption, tags):
        """
        I'm only interested in the namespace aspect of this class, not the
        OOP-ness. So instead of instantiating it with Metadata(), THEN calling
        a method, I'm gonna save code by calling the method from this init.

        Hashtag not best practices, but oh well :)

        """
        self.user = user
        self.filename = filename
        self.date = date
        self.code = code
        self.caption = caption

        # Remove emojis for now
        # XMP can handle them, but Exif UserComment can't
        bad_chars = [char for char in caption if char not in string.printable]
        if bad_chars:
            for char in bad_chars:
                self.caption = self.caption.replace(char, '')

        self.title = '{} - {}'.format(user, code)
        self.tags = tags if tags else []  # in case user specified empty --tags
        self.file_ext = self.filename.split('.')[-1]

        # Call one of the methods
        if self.file_ext == 'mp4':
            self.process_video()
        elif self.file_ext == 'jpg':
            self.process_image()

    def process_video(self):
        """Add Mutagen metadata to a downloaded video file"""
        video = MP4(self.filename)
        video.delete()  # existing metadata

        # Title
        video['\xa9nam'] = self.title

        # Description
        try:
            video['desc'] = self.caption
            video['ldes'] = self.caption  # Long
            video['\xa9cmt'] = self.caption[:255]  # Comment
        except TypeError:  # No caption
            pass

        # Date
        video['purd'] = self.date  # Purchase Date
        video['\xa9day'] = self.date.split(':')[0]  # Year

        # Genres (tags)
        video['\xa9gen'] = ','.join(self.tags)  # Genres
        video['keyw'] = ','.join(self.tags)  # Podcast Keywords

        # User
        video['\xa9ART'] = self.user  # Arist
        video['cprt'] = self.user  # Copyright
        video['----:com.apple.iTunes:iTunMOVI'] = self.xml_tags()  # Actor

        video.save()

    def xml_tags(self):
        """Build XML tags for a video file

        Only XML we're doing right now is for the "Actor" (user)

        """
        output = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict>\n'
        output += '<key>cast</key><array>\n'
        output += '<dict><key>name</key><string>{}</string></dict>\n'.format(self.user)
        output += '</array>\n'
        output += '</dict></plist>\n'

        # String must be made into bytes or Mutagen throws a fit
        return output.encode('UTF-8')


    def process_image(self):
        """Add exiftool metadata to a downloaded image file"""
        try:
            # Write the keywords (tags)
            for tag in self.tags:
                subprocess.run(['exiftool', '{}'.format(self.filename),
                                '-Keywords+={}'.format(tag),  # Iptc
                                '-overwrite_original', '-q'])

            subprocess.run(['exiftool', '{}'.format(self.filename),
                            '-XPSubject={}'.format(self.user),  # Exif
                            '-XPAuthor={}'.format(self.user),  # Exif
                            '-Artist={}'.format(self.user),  # Exif
                            '-Credit={}'.format(self.user),  # Iptc
                            '-Copyright={}'.format(self.user),  # Exif
                            '-Headline={}'.format(self.title),  # Iptc
                            '-Title={}'.format(self.title),  # XMP
                            '-Comment={}'.format(self.caption),
                            '-UserComment={}'.format(self.caption),  # Exif
                            '-Description={}'.format(self.caption),  # XMP
                            '-Caption={}'.format(self.caption),  # Iptc
                            '-XPComment={}'.format(self.caption),  # Exif
                            '-DateTimeOriginal={}'.format(self.date),  # Exif
                            '-overwrite_original', '-q'])

            # Finally, set the modification date
            subprocess.run(['exiftool', '{}'.format(self.filename),
                            '-FileModifyDate<DateTimeOriginal',
                            '-overwrite_original', '-q'])
        except FileNotFoundError:
            raise SystemExit('\n[!] Can\'t find exiftool in the system PATH. '
                             'Did you install it?\n')

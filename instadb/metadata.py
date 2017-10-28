import subprocess

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
            subprocess.run(['exiftool', f'{self.filename}',
                            f'-IFD0:XPSubject={self.user}',
                            f'-IFD0:XPAuthor={self.user}',
                            f'-IFD0:Artist={self.user}',
                            f'-IFD0:Copyright={self.user}',
                            f'-IPTC:Credit={self.user}',
                            f'-IPTC:CopyrightNotice={self.user}',
                            f'-ExifIFD:OwnerName={self.user}',
                            f'-IFD0:ImageDescription={self.title}',
                            f'-IPTC:Headline={self.title}',
                            f'-ExifIFD:UserComment={self.caption}',
                            f'-IFD0:XPComment={self.caption}',
                            f'-ExifIFD:DateTimeOriginal={self.date}',
                            f'-IFD0:ModifyDate={self.date}',
                            '-overwrite_original', '-q'])
        except FileNotFoundError:
            raise SystemExit('\n[!] Can\'t find exiftool in the system PATH. Did you install it?\n')

        # Write the keywords (tags)
        for tag in self.tags:
            subprocess.run(['exiftool', f'{self.filename}',
                            f'-IPTC:Keywords+={tag}',
                            '-overwrite_original', '-q'])

        # Finally, set the modification date
        subprocess.run(['exiftool', f'{self.filename}',
                        '-FileModifyDate<DateTimeOriginal',
                        '-overwrite_original', '-q'])

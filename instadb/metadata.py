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
        self.tags = tags
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
        """Add Exiv2 metadata to a downloaded image file"""
        # Tags
        for tag in self.tags:
            try:
                subprocess.run(['exiv2', '-M', 'add Iptc.Application2.Keywords String {}'.format(tag), self.filename])
            except FileNotFoundError:
                raise SystemExit('\n[!] Can\'t tag photos\n[!] Exiv2 not found in PATH. Did you install it?\n')

        # Title
        subprocess.run(['exiv2', '-M', 'add Iptc.Application2.Caption String {}'.format(self.title), self.filename])
        subprocess.run(['exiv2', '-M', 'add Exif.Image.ImageDescription {}'.format(self.title), self.filename])
        subprocess.run(['exiv2', '-M', 'add Iptc.Application2.Headline {}'.format(self.title), self.filename])

        # Description
        subprocess.run(['exiv2', '-M', 'add Exif.Photo.UserComment {}'.format(self.caption), self.filename])
        subprocess.run(['exiv2', '-M', 'add Exif.Image.ImageDescription {}'.format(self.caption), self.filename])
        subprocess.run(['exiv2', '-M', 'add Iptc.Application2.Caption {}'.format(self.caption), self.filename])

        # User
        subprocess.run(['exiv2', '-M', 'add Exif.Image.Artist {}'.format(self.user), self.filename])
        subprocess.run(['exiv2', '-M', 'add Exif.Photo.CameraOwnerName {}'.format(self.user), self.filename])
        subprocess.run(['exiv2', '-M', 'add Exif.Image.Copyright {}'.format(self.user), self.filename])
        subprocess.run(['exiv2', '-M', 'add Iptc.Application2.Writer {}'.format(self.user), self.filename])
        subprocess.run(['exiv2', '-M', 'add Iptc.Application2.Subject {}'.format(self.user), self.filename])
        subprocess.run(['exiv2', '-M', 'add Iptc.Application2.Credit {}'.format(self.user), self.filename])
        subprocess.run(['exiv2', '-M', 'add Iptc.Application2.Copyright {}'.format(self.user), self.filename])

        # Write EXIF time
        subprocess.run(['exiv2', '-M', 'add Exif.Photo.DateTimeOriginal {}'.format(self.date), self.filename])
        subprocess.run(['exiv2', '-M', 'add Exif.Image.DateTime {}'.format(self.date), self.filename])
        # Change file time to EXIF time
        subprocess.run(['exiv2', '-T', self.filename])

import re

try:
    import requests
except ImportError:
    raise SystemExit('\n[!] Requests not installed\npip3 install requests\n')


def correct_proxy_format(proxy):
    """Check if a proxy is correctly formatted as address:port

    Example:
    192.168.0.1:8080

    Returns:
    True if correct, False if incorrect

    """
    proxy_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\:\d{2,5}$'
    if re.search(proxy_pattern, proxy):
        return True


class Retrieve:
    """Wrapper around a requests Session() so I can set default headers, proxy,
       etc for all requests.

    """
    USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) '
                  'Gecko/20100101 Firefox/52.0')

    def __init__(self, proxy: dict):
        """
        proxy: Needs to be in requests format -- {'https': '192.168.0.1:8080'}

        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/'
        })
        self.proxy = proxy if proxy else None

    def get(self, url, end_cursor=''):
        """GET either a JSON page or a media file

        end_cusor: Used by Instagram for pagination
        Example:
        https://www.instagram.com/user/media/?max_id={end_cursor} <--

        returns: False if the URL is 404'd

        """
        if end_cursor:
            url += '?max_id={}'.format(end_cursor)

        while True:
            try:
                resp = self.session.get(url, timeout=7, proxies=self.proxy)
                if resp.status_code not in [200, 404]:
                    print('\n[!] {}\n\007'.format(resp.status_code))
                    self.proxy = self.new_proxy()
                else:
                    break
            except requests.exceptions.RequestException as error:  # Catch all
                print('\n{}\007'.format(error))
                self.proxy = self.new_proxy()

        if resp.status_code == 404:
            print('\n[!] {} is 404\n'.format(url))
            return False

        return resp

    def new_proxy(self):
        """Enter a new proxy"""
        while True:
            proxy = input('\nEnter a proxy or type "exit"\n> ').lower().strip()
            if proxy == "exit":
                raise SystemExit('\n[!] Exited\n')
            elif not correct_proxy_format(proxy):
                print('\n[!] Proxy must be in format address:port')
            else:
                # Clear out of old csrftoken so Instagram
                # doesn't know we're the same person.
                self.session.cookies.clear()
                return {'https': proxy}  # format required by requests module

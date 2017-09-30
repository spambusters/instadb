import re

import requests

USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) '
              'Gecko/20100101 Firefox/52.0')


def check_proxy_format(proxy):
    """Check if a proxy is correctly formatted as address:port

    Example:
    192.168.0.1:8080

    Returns:
    A dictionary as required by requests module

    """
    proxy_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\:\d{2,5}$'
    if re.search(proxy_pattern, proxy):
        return {'https': proxy}
    else:
        raise SystemExit('\n[!] {} is not address:port\n'.format(proxy))


class Retrieve:
    """Wrapper around a requests Session() so I can set default
    headers, proxy, etc for all Instagram requests.

    FYI I have object'ified this simple task so that future features (such as
    downloading media to local storage) can be easily implemented.

    """

    def __init__(self, user, proxy):
        """Instantiate base Session that will be used for all connections"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/'
        })
        self.user = user
        self.proxy = proxy if proxy else None
        self.base_url = 'https://www.instagram.com/{}/media/'.format(self.user)

    def get_json(self, end_cursor=''):
        """Retrieve JSON for a page of Instagram posts (default 20 posts)"""
        url = self.base_url
        if end_cursor:
            url += '?max_id={}'.format(end_cursor)

        try:
            resp = self.session.get(url, proxies=self.proxy, timeout=10)
        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout):
            raise SystemExit('\n[!] Connection timeout\n')
        except requests.exceptions.ProxyError:
            raise SystemExit('\n[!] Proxy error\n')

        if resp.status_code == 404:
            raise SystemExit('\n[!] User {} is 404\n'.format(self.user))

        return resp.json()

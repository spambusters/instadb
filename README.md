# instascrape
Instagram user data scraping, with proxy support!

## Requirements
1. Python 3.6
2. sqlite3
3. Requests module `pip3.6 install requests`
4. tzlocal module `pip3.6 install tzlocal`

## Usage
```
instascrape.py [-h] [--proxy PROXY] user

positional arguments:
  user           Instagram user

optional arguments:
  -h, --help     show this help message and exit
  --proxy PROXY  Proxy support. Addr:Port (192.168.0.1:8080) - Must be HTTPS
                 capable!
```

## Output  
Posts are written to a local database. The database file will be named after the scraped instagram user - e.g. `okcthunder.db`  

This is an sqlite3 database, so I suggest using [DB Browser for SQLite](http://sqlitebrowser.org/) for easy navigation.  
It will allow you to sort by e.g. likes count to find the most popular post.

![alt text](https://i.imgur.com/KCynhHT.png)

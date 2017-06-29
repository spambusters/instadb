# instascrape
Instagram user data scraping, with proxy support!

## Requirements
1. Python 3.6
2. sqlite3
3. Requests module `pip install requests`
4. tzlocal module `pip install tzlocal`

## Usage
```
instascrape.py [-h] [--proxy PROXY] user

positional arguments:
  user           Instagram user

optional arguments:
  -h, --help     show this help message and exit
  --proxy PROXY  address:port (192.168.0.1:8080) - must be HTTPS
                 capable!
```

## Output  
Posts are written to a local database named after the scraped user. e.g.,  
https://www.instagram.com/sportscenter/ will be `sportscenter.db`  

This is an sqlite3 database, so I suggest using [DB Browser for SQLite](http://sqlitebrowser.org/) for easy navigation.  
It will allow you to sort columns by e.g. likes to find the most popular post.

![alt text](https://i.imgur.com/prNgHo7.png)

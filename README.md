# instadb  
Backup an Instagram user's posts to a local sqlite3 database. API-free and with proxy support!  

#### Note: This script doesn't download media files (yet)

## Requirements
1. Python 3
2. Requests module `pip install requests`  

## Usage
```
instadb.py [-h] [-p PROXY] [-r RATE_LIMIT] user

positional arguments:
  user                  Instagram user

optional arguments:
  -h, --help            show this help message and exit
  -p, --proxy           Proxy must be in the format address:port
  -r, --rate-limit      Seconds between Instagram requests (default 1)
```  

## Output  
Posts are written to a local database named after the scraped user. e.g.,  
https://www.instagram.com/sportscenter/ will be `sportscenter.db`  

The database is saved in `$USER/Downloads/instadb`  

This is an sqlite3 database, so I suggest using [DB Browser for SQLite](http://sqlitebrowser.org/) for browsing.  
It allows you to sort columns! e.g. Sort by likes to find the most popular post.  

![alt text](https://i.imgur.com/wA8frS2.png)

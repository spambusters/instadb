# instascrape
Instagram user data scraping, with proxy support!

#### Note: This script doesn't download images (yet)

## Requirements
1. Python 3.6
2. sqlite3
3. Requests module `pip install requests`  

## Usage
```
instascrape.py user
```  

## Output  
Posts are written to a local database named after the scraped user. e.g.,  
https://www.instagram.com/sportscenter/ will be `sportscenter.db`  

This is an sqlite3 database, so I suggest using [DB Browser for SQLite](http://sqlitebrowser.org/) for easy navigation.  
It allows you to sort columns e.g. sort likes to find the most popular post.  

![alt text](https://i.imgur.com/uxvNDZu.png)

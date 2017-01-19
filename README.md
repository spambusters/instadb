# instascrape
Retrieve instagram posts and write them to a database without using an API

## Requirements
1. Python 3.6
2. sqlite3
3. Requests module `pip3.6 install requests`
4. tzlocal module `pip3.6 install tzlocal`

## Usage
`python3.6 instascraper.py`  

Simply enter the Instagram username when prompted.  
12 posts are grabbed per request, and the default rate limit can be changed:  

`RATE_LIMIT = 6  # seconds`  

## Output  
Posts are written to a local database created in the same folder as instascraper.py. The database file will be named after the scraped instagram user - e.g. `sportscenter.db`  

Each post has the following data written to the db:  
* post date
* share link code (e.g. instagram.com/p/`BPaG7ecBQIO`)
* likes count
* comment count
* caption    

This is an sqlite3 database, so I suggest using [DB Browser for SQLite](http://sqlitebrowser.org/) for easy navigation. It will allow you to sort by e.g. likes count to find the most popular post.

![alt text](https://i.imgur.com/N2vXhsz.png)

## Why  
Just a fun project to better understand python as well as things like csrftoken(s) in a POST request.

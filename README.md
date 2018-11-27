# wikihistory

_Scrape history of wikipedia articles and explore their distributional properties._

## Usage

```
pipenv install
```

This will create a virtualenv to work with and install all dependencies. Notable requirements include `scrapy`, and later on probably `pandas`. 

To run the crawler, use 

```
pipenv shell
scrapy crawl history
```
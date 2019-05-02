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

To save the output in a file, use the `-o` option. To specify the categories to parse use the `-a cats="all,the,cats"` option. So the complete command could look like this:

```
scrapy crawl history -o results/complete.json -a cats="Geschichte_der_Malerei,Rechtsextremismus,Kernenergie"
```

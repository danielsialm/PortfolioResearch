# Monthly Market PDF Parser

Code to scrape the portfolio stock information from the Ohio State Teacher Retirement System.

## Utilization
for 2006-2019
run `python3 parse.py <YEAR>` to scrape the stocks from that year where `<YEAR>` indicates the directory that contains the necessary information to properly scrape (see **Reference**)
for 2001-2005 use `parse2.py`

#### Flags
`-q1` early stop for program, stops after splitting by pages
`-q2` early stop for program, stops after splitting by account

#### Output
Along with outputting information about the pages and accounts, the scraped stocks can be found in the `stock_data.txt` file.\
The following information is included, separated by semi-colons
1. Fund name
2. Date
3. Security Name
4. CUSIP
5. MarketVal
6. Type
7. Shares
8. AccountName
9. AccountID
10. Internal Indicator

### Finished Years: 
2001, 2002, 2003, 2004, 2005, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019

### Concerns:
Note: Real Estate names cut off (e.g. 2007 312)
2009 - AI-VC has a random 0, unsure if shares or misinput
2013 page 104 - how to scrape
2014 - only has summary
double check aggregates

## Reference

### indices.txt
used to indicate the different column headers and the order that the information is in
(reading the pdf has the column information out of order)

### lengths.txt
used to indicate which accounts follow which column header format

### supplements.txt
used to indicate where information is missing either by whole columns or individual cells in the table
also indicates which pages to skip over in the pdf
also indicates which portfolios are missing type information (typeID)
also indicates how account information is set up

### output_pages
outputs each individual (not-ignored) page read from the pdf into a text file

### output_accounts
outputs each account and all its subsequent stock information into a text file

### readme.txt
important information for supplemental information and changes that are not handled by the code
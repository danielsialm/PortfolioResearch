# Monthly Market PDF Parser

Code to scrape the portfolio stock information from the Ohio State Teacher Retirement System.

## Utilization
run `python3 parse.py <YEAR>` to scrape the stocks from that year
#### Flags
`-a` indicates that for this year, account names come after 'Portfolio' rather than before (used in 2019)\
`-q` early stop for program, stops after splitting by account (used to debug type splits)

### Finished Years: 
2007, 2008

### Concerns:
2019 - page 52 what to scrape?\
Note: Real Estate names cut off (e.g. 2007 312)

## Reference

### indices.txt
used to indicate the different column headers and the order that the information is in
(reading the pdf has the column information out of order)

### lengths.txt
used to indicate which accounts follow which column header format

### supplements.txt
used to indicate where information is missing either by whole columns or individual cells in the table
also indicates which pages to skip over in the pdf

### output_pages
outputs each individual (not-ignored) page read from the pdf into a text file

### output_accounts
outputs each account and all its subsequent stock information into a text file

### readme.txt
important information for supplemental information and changes that are not handled by the code
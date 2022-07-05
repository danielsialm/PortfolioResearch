from sre_constants import IN
import fitz
import os
import shutil
import sys
import re

from numpy import Inf

DEBUG = False

class stock():
  def __init__(self):
    self.fund_name = "Ohio_STR"
    self.date = ""
    self.security_name = ""
    self.CUSIP = ""
    self.marketVal = ""
    self.type = ""
    self.shares = ""
    self.account_name = ""
    self.account_id = ""
    self.group_name = ""
  
  def __str__(self):
    return (self.fund_name + ';' + 
      self.date + ';' + 
      self.security_name + ';' + 
      self.CUSIP + ';' + 
      self.marketVal + ';' + 
      self.type + ';' + 
      self.shares + ';' + 
      self.account_name + ';' + 
      self.account_id + ';' + 
      ('1' if "Internal" in self.group_name else '0'))

class type_info():
  def __init__(self, name):
    self.name = name
    self.infoLen = None
    self.secNameIdx = -1
    self.cusipIdx = -1
    self.marketValIdx = -1
    self.sharesIdx = -1
    self.accName = ""
    self.accID = ""
    self.groupName = ""
    self.date = ""

def parse_stock(text: list[str], thisTypeInfo: type_info) -> stock:
  text.append('')         # -1 indicates idx does not exist, so last item of list is ''
  thisStock = stock()
  thisStock.date = thisTypeInfo.date
  thisStock.security_name = text[thisTypeInfo.secNameIdx]
  thisStock.CUSIP = text[thisTypeInfo.cusipIdx]
  thisStock.marketVal = text[thisTypeInfo.marketValIdx]
  thisStock.type = thisTypeInfo.name
  thisStock.shares = text[thisTypeInfo.sharesIdx]
  thisStock.account_name = thisTypeInfo.accName
  thisStock.account_id = thisTypeInfo.accID
  thisStock.group_name = thisTypeInfo.groupName
  return thisStock

# find a way to figure out how long each stock is?
def split_stocks(input: list[str], type_supp_info, thisTypeInfo: type_info) -> list[stock]:
  numColMissing = len([x for x in type_supp_info if x[1] == []]) if type_supp_info else 0
  numDataMissing = sum([len(x[1]) for x in type_supp_info if x[1] != []]) if type_supp_info else 0
  try:
    numCol = int(thisTypeInfo.infoLen.split("_")[0])
    numStocks = int((len(input) + numDataMissing) / (numCol - numColMissing))
  except:
    print("supp data missing for " + thisTypeInfo.name)
    return []

  stocks = []
  for i in range(numStocks):
    if type_supp_info:
      for colName, indices in type_supp_info:
        if (indices and i in indices) or not indices:
          input.insert(i*numCol + INDICES[thisTypeInfo.infoLen][colName], '')
    stocks.append(parse_stock(input[numCol*i : numCol*(i+1)], thisTypeInfo))
  return stocks

# returns a dictionary of the different types and their (parsed) stocks, for an account
def split_type(text, date, accName, accID, group, acc_supp_info, infoLen) -> dict[str, list[stock]]:
  indices_type = [i for i, x in enumerate(text) if x == "Instrument:"]

  # clean up page breaks when type changes
  currentType = ""
  offset = 0
  for idx in indices_type:
    typeName = text[idx + 1 - offset]
    if typeName == currentType:
      del text[idx-offset:idx+3-offset]
      offset += 3
    currentType = typeName

  indices_type = [i for i, x in enumerate(text) if x == "Instrument:"]

  # parse different stocks under type, store as dictionary
  typeDict = {}
  for i in range(len(indices_type)):
    startIdx = indices_type[i] + 3
    typeName = text[indices_type[i] + 1]
    typeID = text[indices_type[i] + 2]
    try:
      endIdx = text.index(typeName + '  TOTAL')
    except:
      print(accName)
      exit()

    typeInfo = type_info(typeName)
    typeInfo.accID = accID
    typeInfo.accName = accName
    typeInfo.groupName = group
    typeInfo.date = date
    typeInfo.infoLen = infoLen
    typeInfo.secNameIdx = INDICES[infoLen]['DESCRIPTION']
    typeInfo.cusipIdx = INDICES[infoLen]['IDENTIFIER']
    typeInfo.marketValIdx = INDICES[infoLen]['MARKET VALUE']
    typeInfo.sharesIdx = INDICES[infoLen]['SHARES']
    type_supp_info = None
    type_supp_info = acc_supp_info[typeID] if acc_supp_info and typeID in acc_supp_info else None
    typeDict[typeName] = split_stocks(text[startIdx: endIdx], type_supp_info, typeInfo)
    if DEBUG: print("Finished", typeName)
  return typeDict

# separate by account
# accountID : (accountName, groupName, cleanedText)
def split_account(pages):
  accounts = {}
  for page in pages:
    hasPort = page[-2][:10] == "Portfolio:"
    if hasPort:
      accountLine = page[-2][11:]
      accountName = accountLine[accountLine.index(" "):].strip()
      accountID = accountLine[:accountLine.index(" ")].strip()
      groupName = page[-3][7:]
    else:
      # no portfolio
      groupName = page[-2][7:]
      accountName = ""
      accountID = ""
    
    try:
      start = page.index("Portfolio:") + 1
    except:
      print('ignored ' + page[0])
      continue

    cleanedText = page[start:(-3 if hasPort else -2)]
    if accountID in accounts:
      cleanedText = accounts[accountID][2] + cleanedText
    accounts[accountID] = (accountName, groupName, cleanedText)
  return accounts


#########################################################################################
INDICES_4A = { 'DESCRIPTION': 1, 
               'IDENTIFIER': 2, 
               'BOOK VALUE': 0, 
               'MARKET VALUE': 3,
               'SHARES': -1 }

INDICES_5A = { 'DESCRIPTION': 2, 
               'IDENTIFIER': 3,
               'TICKER': 0,
               'BOOK VALUE': 1, 
               'MARKET VALUE': 4,
               'SHARES': -1 }

INDICES_6A = { 'DESCRIPTION': 3, 
               'IDENTIFIER': 4, 
               'PRICE': 2, 
               'SHARES': 1,
               'BOOK VALUE': 0,
               'MARKET VALUE': 5}

INDICES_6B = { 'DESCRIPTION': 3, 
               'IDENTIFIER': 4, 
               'TICKER': 0, 
               'SHARES': 2,
               'BOOK VALUE': 1,
               'MARKET VALUE': 5}

INDICES_7A = { 'DESCRIPTION': 4, 
               'IDENTIFIER': 5, 
               'TICKER': 0, 
               'PRICE': 3, 
               'SHARES': 2,
               'BOOK VALUE': 1,
               'MARKET VALUE': 6}

INDICES_7B = { 'DESCRIPTION': 2, 
               'IDENTIFIER': 4, 
               'YIELD': 5, 
               'F': 3, 
               'SHARES': 1,
               'BOOK VALUE': 0,
               'MARKET VALUE': 6}

INDICES_8A = { 'DESCRIPTION': 4, 
               'IDENTIFIER': 5, 
               'YIELD': 6, 
               'COUPON': 3, 
               'MATURITY': 2,
               'SHARES': 1,
               'BOOK VALUE': 0,
               'MARKET VALUE': 7}

INDICES_9A = { 'DESCRIPTION': 5, 
               'IDENTIFIER': 6, 
               'YIELD': 7, 
               'COUPON': 4, 
               'MATURITY': 3,
               'PRICE': 2,
               'SHARES': 1,
               'BOOK VALUE': 0,
               'MARKET VALUE': 8}

INDICES_11A = {'DESCRIPTION': 6, 
               'IDENTIFIER': 8, 
               'RATING': 0,
               'YIELD': 9, 
               'COUPON': 5,
               'F': 7, 
               'MATURITY': 4,
               'PRICE': 3,
               'SHARES': 2,
               'BOOK VALUE': 1,
               'MARKET VALUE': 10}

INDICES = { '4_A': INDICES_4A,
            '5_A': INDICES_5A,
            '6_A': INDICES_6A, '6_B': INDICES_6B,
            '7_A': INDICES_7A, '7_B': INDICES_7B,
            '8_A': INDICES_8A, 
            '9_A': INDICES_9A, 
            '11_A': INDICES_11A}

SRC_DIR = os.path.join(os.getcwd(), sys.argv[1])

'''
Supplement file format:
first line - pages to exclude
subsequent lines - data to add
ACCID;TYPE; which col to add data under;(optional: list specific indices)

stored: map typeID to list of tuples (column to add data, indices (empty list means all))
LIST OF TUPLES ORDERED BY INDEX FOUND IN PDF
'''
supp_file = open(os.path.join(SRC_DIR, "supplements.txt"), 'r')
excludePages = []
for x in supp_file.readline().strip().split(';'):
  if '-' in x:
    start = int(x[0:x.index('-')])
    end = int(x[x.index('-') + 1:])
    excludePages += list(range(start,end + 1))
  else:
    excludePages.append(int(x))
supp_data = {}
for x in supp_file.read().strip().split('\n'):
  info = x.split(';')
  this_accid = info[0]
  this_typeid = info[1]
  this_col = info[2]
  this_idxs = [int(x) for x in info[3:]]
  if this_accid not in supp_data:
    supp_data[this_accid] = {}
  if this_typeid not in supp_data[this_accid]:
    supp_data[this_accid][this_typeid] = []
  supp_data[this_accid][this_typeid].append((this_col, this_idxs))

with fitz.open(os.path.join(SRC_DIR, "MonthlyMarket.pdf")) as doc:
  pages = []
  pageNum = 1
  for page in doc:
    if pageNum not in excludePages:
      pages.append([x.strip() for x in page.get_text().split('\n')])
    pageNum += 1
date = pages[0][5][6:]

LENGTH_DIR = os.path.join(SRC_DIR, "lengths.txt")
length_provided = os.path.getsize(LENGTH_DIR) > 0
info_len = {}
if length_provided:
  with open(LENGTH_DIR, 'r') as f:
    for x in f.read().strip().split('\n'):
      thisAccID, thisInfoLen = x.split(';')
      info_len[thisAccID] = thisInfoLen

# display the pages
DST_DIR = os.path.join(SRC_DIR, "output_pages")
if os.path.exists(DST_DIR):
  shutil.rmtree(DST_DIR)
os.makedirs(DST_DIR)
for x in pages:
  pageNum = x[0].split(' ')[1]
  out = open(os.path.join(DST_DIR, "page" + pageNum + ".txt"), 'w')
  out.write('\n'.join(x))
  out.close()

# split pdf into different accounts
accounts = split_account(pages)

# display the accounts
DST_DIR = os.path.join(SRC_DIR, "output_accounts")
if os.path.exists(DST_DIR):
  shutil.rmtree(DST_DIR)
os.makedirs(DST_DIR)
i = 0
for x in accounts:
  out = open(os.path.join(DST_DIR, "account_" + x + ".txt"), 'w')
  out.write('\n'.join(accounts[x][2]))
  out.close()
  i += 1

# per account, split by type, read the stock
stocks = []
for accID in accounts:
  accountName = accounts[accID][0]
  groupName = accounts[accID][1]
  text = accounts[accID][2]
  typeDict = split_type(text, date, accountName, accID, groupName, supp_data[accID] if accID in supp_data else None, info_len[accID])
  for type in typeDict:
    stocks += typeDict[type]
  if DEBUG: print("Account Finished", accountName)

stocks = map(str, stocks)

DST_DIR = os.path.join(SRC_DIR, "output")
if os.path.exists(DST_DIR):
  shutil.rmtree(DST_DIR)
os.makedirs(DST_DIR)
out = open(os.path.join(DST_DIR, "stock_data" + ".txt"), 'w')
out.write('\n'.join(stocks))
out.close()


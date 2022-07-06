import fitz
import os
import shutil
import argparse

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
    numCol = int(thisTypeInfo.infoLen.split("-")[0])
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

'''
returns a dictionary of the different types and a list of their (parsed) stocks, for an account
needed - proper supp info, length info, and indics
'''
def split_type(text, date, accName, accID, group, acc_supp_info, infoLen) -> dict[str, list[stock]]:
  # clean up page breaks when type changes
  indices_type = [i for i, x in enumerate(text) if x == "Instrument:"]
  currentType = ""
  offset = 0
  for idx in indices_type:
    typeName = text[idx + 1 - offset]
    if typeName == currentType:
      del text[idx-offset:idx+3-offset]
      offset += 3
    currentType = typeName
  
  # parse different stocks under type, store as dictionary
  indices_type = [i for i, x in enumerate(text) if x == "Instrument:"]
  typeDict = {}
  for i in range(len(indices_type)):
    startIdx = indices_type[i] + 3
    typeName = text[indices_type[i] + 1]
    typeID = text[indices_type[i] + 2]
    try:
      endIdx = text.index(typeName + '  TOTAL')
    except:
      print(typeName, "in", accName, "has no corresponding TOTAL")
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
  return typeDict

'''
separate by account
returns dictionary of form
accountID : (accountName, groupName, cleanedText)
'''
def split_account(pages, isAfter):
  accounts = {}
  for page in pages:
    try:
      start = page.index("Portfolio:") + (3 if isAfter else 1)
    except:
      print('ignored ' + page[0])
      continue
    
    accountName = page[start-(2 if isAfter else 3)]
    accountID = page[start-(1 if isAfter else 2)]

    groupName = page[-3][7:]
    cleanedText = page[start:-3]
    if accountID in accounts:
      cleanedText = accounts[accountID][2] + cleanedText
    accounts[accountID] = (accountName, groupName, cleanedText)
  return accounts

'''
indices file format:
name;security name idx;cusip idx;shares idx;market val idx
'''
def parse_indices_file(FILE_LOC):
  idx_file = open(FILE_LOC, 'r')
  idxDict = {}
  for x in idx_file.read().strip().split('\n'):
    name, info = x.split(';')
    colInfoDict = {}
    for colinfo in info.strip().split(','):
      colname, colidx = colinfo.split(':')
      colInfoDict[colname] = int(colidx)
    idxDict[name] = colInfoDict
  idx_file.close()
  return idxDict


'''
Supplement file format:
first line - pages to exclude
subsequent lines - data to add
ACCID;TYPE; which col to add data under;(optional: list specific indices)

stored: map typeID to list of tuples (column to add data, indices (empty list means all))
LIST OF TUPLES ORDERED BY INDEX FOUND IN PDF
'''
def parse_supp_file(FILE_LOC):
  supp_file = open(FILE_LOC, 'r')
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
  supp_file.close()
  return excludePages, supp_data

'''
lengths file format:
accID;column header name
'''
def parse_length_file(FILE_LOC):
  info_len = {}
  with open(FILE_LOC, 'r') as f:
    for x in f.read().strip().split('\n'):
      thisAccID, thisInfoLen = x.split(';')
      info_len[thisAccID] = thisInfoLen
  return info_len

# creates/replaces a new directory if not there
def make_dir(DST_DIR):
  if os.path.exists(DST_DIR):
    shutil.rmtree(DST_DIR)
  os.makedirs(DST_DIR)

# output the pages into different files
def output_pages(pages):
  DST_DIR = os.path.join(SRC_DIR, "output_pages")
  make_dir(DST_DIR)
  for x in pages:
    pageNum = x[0].split(' ')[1]
    out = open(os.path.join(DST_DIR, "page" + pageNum + ".txt"), 'w')
    out.write('\n'.join(x))
    out.close()

def output_account(accounts):
  DST_DIR = os.path.join(SRC_DIR, "output_accounts")
  make_dir(DST_DIR)
  for x in accounts:
    out = open(os.path.join(DST_DIR, "account_" + x + ".txt"), 'w')
    out.write('\n'.join(accounts[x][2]))
    out.close()


'''-----------------------------------------------------------------------------------'''

# get command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("source")
parser.add_argument('-a', '--after', default=False, action=argparse.BooleanOptionalAction)
parser.add_argument('-q', '--quitaccount', default=False, action=argparse.BooleanOptionalAction)
parser.add_argument('-s', '--supphelp', default=False, action=argparse.BooleanOptionalAction)
args = parser.parse_args()

SRC_DIR = os.path.join(os.getcwd(), args.source)

# load in information from text files
INDICES = parse_indices_file(os.path.join(SRC_DIR, "indices.txt"))
excludePages, supp_data = parse_supp_file(os.path.join(SRC_DIR, "supplements.txt"))
info_len = parse_length_file(os.path.join(SRC_DIR, "lengths.txt"))


# read the pdf
with fitz.open(os.path.join(SRC_DIR, "MonthlyMarket.pdf")) as doc:
  pages = []
  pageNum = 1
  for page in doc:
    if pageNum not in excludePages:
      pages.append([x.strip() for x in page.get_text().split('\n')])
    pageNum += 1
date = pages[0][5][6:]
# display the pages
output_pages(pages)

# split pdf into different accounts
accounts = split_account(pages, args.after)
# display the accounts
output_account(accounts)

# per account, split by type, read the stock
stocks = []
for accID in accounts:
  accountName, groupName, text = accounts[accID]
  typeDict = split_type(text, date, accountName, accID, groupName, 
                        supp_data[accID] if accID in supp_data else None, info_len[accID])
  for type in typeDict:
    stocks += typeDict[type]

# output stocks
stocks = map(str, stocks)
out = open(os.path.join(SRC_DIR, "stock_data" + ".txt"), 'w')
out.write('\n'.join(stocks))
out.close()


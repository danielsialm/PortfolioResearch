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
    self.typeName = name
    self.typeID = id
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
  thisStock.type = thisTypeInfo.typeName
  thisStock.shares = text[thisTypeInfo.sharesIdx]
  thisStock.account_name = thisTypeInfo.accName
  thisStock.account_id = thisTypeInfo.accID
  thisStock.group_name = thisTypeInfo.groupName
  return thisStock

# find a way to figure out how long each stock is?
def split_stocks(stock_input: list[str], type_supp_info, thisTypeInfo: type_info) -> list[stock]:
  oldLen = len(stock_input)
  numColMissing = len([x for x in type_supp_info if (x[1] == [] or x[1][0] < 0)]) if type_supp_info else 0
  numDataDiff = sum([(len(x[1]) if x[1][0] > 0 else -len(x[1])) for x in type_supp_info if x[1] != []]) if type_supp_info else 0
  numCol = int(thisTypeInfo.infoLen.split("-")[0])
  if (len(stock_input) + numDataDiff) % (numCol - numColMissing) != 0:
    print("supp data missing for " + thisTypeInfo.typeID + " in " + thisTypeInfo.accID)
    print(len(stock_input), numColMissing, numDataDiff)
    return []
  numStocks = (len(stock_input) + numDataDiff) // (numCol - numColMissing)

  stocks = []
  count = 0
  for i in range(1, numStocks + 1):
    if type_supp_info:
      for colName, indices in type_supp_info:
        # three cases to insert: no indices specified, at index to insert, not the negative index
        if not indices or i in indices or (indices[0] < 0 and -i not in indices):
          count += 1
          stock_input.insert(numCol * (i-1) + INDICES[thisTypeInfo.infoLen][colName], '')
    stock_info = stock_input[numCol*(i-1) : numCol*i]
    try:
      stocks.append(parse_stock(stock_info, thisTypeInfo))
    except:
      print('parse stock failed', thisTypeInfo.accID, thisTypeInfo.typeID, stock_info)
  
  if type_supp_info:
    totalMissingData = numStocks * numCol - oldLen
    if(totalMissingData != count):
      print('data added mismatch for ' + thisTypeInfo.typeID + " in " + thisTypeInfo.accID)
      print('expected:', numDataDiff, '+', numColMissing,'*', numStocks, '=', totalMissingData, 'actual:', count)
  return stocks

'''
returns a dictionary of the different types and a list of their (parsed) stocks, for an account
needed - proper supp info, length info, and indics
'''
def split_type(text, date, accName, accID, group, acc_supp_info, infoLen, noTypeID) -> dict[str, list[stock]]:
  # 'add' typeID if missing
  if noTypeID:
    indices_type = [i for i, x in enumerate(text) if x == "Instrument:"]
    indices_type.reverse()
    for idx in indices_type:
      typeName = text[idx + 1]
      text.insert(idx+1, typeName)
  
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
    typeInfo.typeID = typeID
    typeInfo.accID = accID
    typeInfo.accName = accName
    typeInfo.groupName = group
    typeInfo.date = date
    typeInfo.infoLen = infoLen
    try:
      typeInfo.secNameIdx = INDICES[infoLen]['DESCRIPTION']
      typeInfo.cusipIdx = INDICES[infoLen]['IDENTIFIER']
      typeInfo.marketValIdx = INDICES[infoLen]['MARKET VALUE']
      typeInfo.sharesIdx = INDICES[infoLen]['SHARES']
    except KeyError:
      if infoLen not in UNSPEC_IDX:
        UNSPEC_IDX.append(infoLen)
        print(infoLen + " has no specified indices")
      continue
    type_supp_info = None
    type_supp_info = acc_supp_info[typeID] if acc_supp_info and typeID in acc_supp_info else None
    typeDict[typeName] = split_stocks(text[startIdx: endIdx], type_supp_info, typeInfo)
  return typeDict

'''
separate by account
returns dictionary of form
accountID : (accountName, groupName, cleanedText)
'''
def split_account(pages, accOffsets):
  accounts = {}
  for page in pages:
    try:
      portIDX = page.index('Portfolio:')
    except:
      print('ignored ' + page[0])
      continue
    del page[portIDX]
    
    accountName = page[portIDX + accOffsets[0]]
    accountID = page[portIDX + accOffsets[1]]
    start = portIDX + accOffsets[2]

    end = -1
    for i in range(len(page)-1, -1, -1):
      if 'Group:' in page[i]:
        end = i
        break
    assert end != -1
    groupName = page[end][7:]
    cleanedText = page[start:end]
    if accountID in accounts:
      cleanedText = accounts[accountID][2] + cleanedText
    accounts[accountID] = (accountName, groupName, cleanedText)
  return accounts

'''
indices file format:
name;security name idx;cusip idx;shares idx;market val idx
'''
def parse_indices_file(FILE_LOC):
  if not (os.path.isfile(FILE_LOC) and os.path.getsize(FILE_LOC) > 0):
    return {}

  idx_file = open(FILE_LOC, 'r')
  idxDict = {}
  for x in idx_file.read().strip().split('\n'):
    if x == '':
      continue
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
second line - portfolios with missing instrument info
third line - account offsets accountName, accID, start
subsequent lines - data to add
ACCID;TYPE; which col to add data under;(optional: list specific indices 
- positive indices need info negative indices have info despite the column missing info)


stored: map typeID to list of tuples (column to add data, indices (empty list means all))
'''


def parse_supp_file(FILE_LOC, account_lengths):
  if not (os.path.isfile(FILE_LOC) and os.path.getsize(FILE_LOC) > 0):
    return [], [], (-2,-1,0), {}

  supp_file = open(FILE_LOC, 'r')
  # parse excluded pages
  excludePages = []
  for x in supp_file.readline().strip().split(';'):
    if '-' in x:
      start = int(x[0:x.index('-')])
      end = int(x[x.index('-') + 1:])
      excludePages += list(range(start,end + 1))
    else:
      excludePages.append(int(x))

  # parse portfolios that are missing typeids
  missingTypeID = supp_file.readline().strip().split(';')
  missingTypeID = [] if missingTypeID[0] == '' else missingTypeID

  # parse account offsets
  accOffsets = tuple(supp_file.readline().strip().split(';'))
  if len(accOffsets) != 3:
    accOffsets = (-2,-1,0)
  else:
    accOffsets = tuple(map(int,accOffsets))

  # create data structure for missing cells
  supp_data = {}
  for x in supp_file.read().strip().split('\n'):
    if x == '':
      continue
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

  # sort by column index order so inserting is correct (sort tuple list by column name index)
  if account_lengths and INDICES:
    for this_accid in supp_data:
      infoLen = account_lengths[this_accid]
      for this_typeid in supp_data[this_accid]:
        if this_typeid in INDICES:
          supp_data[this_accid][this_typeid].sort(key=lambda x:INDICES[infoLen][x[0]])
  return excludePages, missingTypeID, accOffsets, supp_data



'''
lengths file format:
accID;column header name
'''
def parse_length_file(FILE_LOC):
  if not (os.path.isfile(FILE_LOC) and os.path.getsize(FILE_LOC) > 0):
    return {}

  info_len = {}
  with open(FILE_LOC, 'r') as f:
    for x in f.read().strip().split('\n'):
      if x == '':
        continue
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
UNSPEC_IDX = []

# get command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("source")
parser.add_argument('-q', '--quitaccount', default=False, action=argparse.BooleanOptionalAction)
args = parser.parse_args()

SRC_DIR = os.path.join(os.getcwd(), args.source)

# load in information from text files
INDICES = parse_indices_file(os.path.join(SRC_DIR, "indices.txt"))
account_lengths = parse_length_file(os.path.join(SRC_DIR, "lengths.txt"))
excludePages, missingTypeID, accOffsets, supp_data = parse_supp_file(os.path.join(SRC_DIR, "supplements.txt"), account_lengths)

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
accounts = split_account(pages, accOffsets)
# display the accounts
output_account(accounts)

if args.quitaccount:
  exit()

# per account, split by type, read the stock
stocks = []
for accID in accounts:
  accountName, groupName, text = accounts[accID]
  try:
    infoLen = account_lengths[accID]
  except KeyError:
    infoLen = input("length for " + accID + ";")
    f = open(os.path.join(SRC_DIR, "lengths.txt"), 'a')
    f.write(accID + ';' + infoLen + '\n')
  typeDict = split_type(text, date, accountName, accID, groupName, 
                        supp_data[accID] if accID in supp_data else None,
                        infoLen, accID in missingTypeID)
  for type in typeDict:
    stocks += typeDict[type]
if UNSPEC_IDX:
  print('indices missing: ' + ' '.join(UNSPEC_IDX))


# output stocks
stocks = map(str, stocks)
out = open(os.path.join(SRC_DIR, "stock_data" + ".txt"), 'w')
out.write('\n'.join(stocks))
out.close()


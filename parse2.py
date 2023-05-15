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

'''
given str of stock lines, returns parsed value
'''
def split_stocks(date, typeName, accountName, accID, groupName, indices, stock_input):
  stocks = []
  for stockLine in stock_input:
    thisStock = stock()
    thisStock.date = date
    thisStock.security_name = stockLine[0:30].strip()
    thisStock.CUSIP = "" if indices[0] == -1 else stockLine[indices[0]:indices[0]+12].strip()
    thisStock.marketVal = "" if indices[2] == -1 else stockLine[indices[2]:].strip()
    thisStock.type = typeName
    thisStock.shares = "" if indices[1] == -1 else stockLine[indices[1]:indices[1]+14].strip()
    thisStock.account_name = accountName
    thisStock.account_id = accID
    thisStock.group_name = groupName
    stocks.append(thisStock)
  return stocks

'''
returns a dictionary of the different types (for a single account)
and a list of their (parsed) stocks

text - array where each element is a line
typeDict - dictionary mapping the type name to an array of stocks
'''
def split_type(date, accountName, accID, groupName, indices, text):
  typeDict = {}

  indices_type_start = [i for i, x in enumerate(text) if "Instrument -" in x]
  indices_type_end = [i for i, x in enumerate(text) if "Instrument Total" in x]

  # find all unnecessary indicies
  indices_type_remove = []
  for i in range(len(indices_type_end)):
    index_end = indices_type_end[i]
    while (i+1) < len(indices_type_start) and indices_type_start[i+1] < index_end:
      indices_type_remove.append(indices_type_start[i+1])
      indices_type_start.pop(i+1)

  for i in range(len(indices_type_remove) - 1, -1, -1):
    for _ in range(3):
      text.pop(indices_type_remove[i]-1)

  # parsing stocks by type
  indices_type_start = [i for i, x in enumerate(text) if "Instrument -" in x]
  indices_type_end = [i for i, x in enumerate(text) if "Instrument Total" in x]
  for i in range(len(indices_type_start)):
    startIdx = indices_type_start[i] + 2
    typeSplit = [x for x in text[indices_type_start[i]][12:].strip().split(" ") if x != ""]
    typeID = typeSplit[0]
    typeName = " ".join(typeSplit[1:])
    endIdx = indices_type_end[i] - 1

    typeDict[typeID] = split_stocks(date, typeName, accountName, accID, groupName, indices, text[startIdx: endIdx])
  
  return typeDict


'''
separate by account
returns dictionary of form
accountID : (accountName, groupName, (cusipIdx, shareIdx, mktValIdx), cleanedText)
'''
def split_account(pages):
  accounts = {}
  for pageTup in pages:
    page = pageTup[1]
    accLine = page[8][13:].split(' ')
    groupName = page[7:]
    accountName = ' '.join([x for x in accLine[1:] if x != ""])
    accountID = accLine[0]
    cleanedText = page[9:]

    # get information about indecies
    if accountID not in accounts:
      try: 
        cusipIdx = page[4].index("Identifier") - 1
      except:
        print("Identifier not found in", accountName)
        cusipIdx = -1
      try:
        sharesIdx = page[4].index("Par/Shares") - 3
      except:
        print("Shares not found in", accountName)
        sharesIdx = -1
      try:
        mktValIdx = page[4].index("Market Value")
      except:
        print("Market Value not found in", accountName)
        mktValIdx = -1
    else:
      cleanedText = accounts[accountID][3] + cleanedText
      
    accounts[accountID] = (accountName, groupName, (cusipIdx, sharesIdx, mktValIdx), cleanedText)
  return accounts


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
    pageNum = str(x[0])
    out = open(os.path.join(DST_DIR, "page" + pageNum + ".txt"), 'w')
    out.write('\n'.join(x[1]))
    out.close()

def output_account(accounts):
  DST_DIR = os.path.join(SRC_DIR, "output_accounts")
  make_dir(DST_DIR)
  for x in accounts:
    out = open(os.path.join(DST_DIR, "account_" + x + ".txt"), 'w')
    out.write('\n'.join(accounts[x][3]))
    out.close()


'''-----------------------------------------------------------------------------------'''
# Group - line 8
# Portfolio - line 9
# Instrument - line 10

# get command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("source")
parser.add_argument('-q1', '--quitpages', default=False, action=argparse.BooleanOptionalAction)
parser.add_argument('-q2', '--quitaccount', default=False, action=argparse.BooleanOptionalAction)
args = parser.parse_args()

SRC_DIR = os.path.join(os.getcwd(), args.source)

# read the pdf
with fitz.open(os.path.join(SRC_DIR, "MonthlyMarket.pdf")) as doc:
  pages = []
  pageNum = 1
  for page in doc:
    pages.append((pageNum, [x.strip() for x in page.get_text().split('\n')]))
    pageNum += 1
# display the pages
print('Pages:', len(pages))
output_pages(pages)

if args.quitpages:
  exit()

# split pdf into different accounts
accounts = split_account(pages)
# display the accounts
output_account(accounts)

if args.quitaccount:
  exit()




# per account, split by type, read the stock
stocks = []
for accID in accounts:
  accountName, groupName, indices, text = accounts[accID]
  typeDict = split_type("12/31/" + args.source, accountName, accID, groupName, indices, text)
  for type in typeDict:
    stocks += typeDict[type]
  

# output stocks
stocks = map(str, stocks)
out = open(os.path.join(SRC_DIR, "stock_data" + ".txt"), 'w')
out.write('\n'.join(stocks))
out.close()
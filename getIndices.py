'''
(bad) helper program to make it easier to write index information

run this after running parse.py -q
'''
import os

def parse_length_file_by_type(FILE_LOC):
  if not (os.path.isfile(FILE_LOC) and os.path.getsize(FILE_LOC) > 0):
    return []

  info_len = {}
  with open(FILE_LOC, 'r') as f:
    for x in f.read().strip().split('\n'):
      if x == '':
        continue
      thisAccID, thisInfoLen = x.split(';')
      if thisInfoLen not in info_len:
        info_len[thisInfoLen] = []
      info_len[thisInfoLen].append(thisAccID)
  return info_len

def get_info(thisAccID, infoLen):
  ACC_DIR = os.path.join(SRC_DIR, "output_accounts", 'account_' + thisAccID + '.txt')
  with open(ACC_DIR, 'r') as f:
    print(thisAccID)
    lst = f.read().split('\n')
    if (len(lst) > 30):
      lst = lst[:30]
    print('\n'.join(lst))
    print()



src = input("source dir? ")
# get the different column types
SRC_DIR = os.path.join(os.getcwd(), src)
col_types = parse_length_file_by_type(os.path.join(SRC_DIR, "lengths.txt"))
print(col_types)

f = open(os.path.join(SRC_DIR, 'indices.txt'), 'w')
# ask the specific indices for each column type
for col in col_types:
  # select a good portfolio to use
  next = False
  length = int(col.split('-')[0])
  i = 0
  while not next:
    print('\033c', end = "")
    print("info for", col)
    get_info(col_types[col][i], length)
    next = input("Enter for this? (y/n): ").lower() == 'y'
    i = (i + 1) % len(col_types[col])

  # ask information about the indices
  f.write(col + ';')
  for i in range(length):
    colname = input("column " + str(i+1) + " name: ")
    index = input(colname + " index: ")
    f.write(colname + ':' + index)
    if i != (length - 1):
      f.write(',')
  f.write('\n')
  
  

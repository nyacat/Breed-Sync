#!/usr/bin/python

import requests
import re
import urllib3
import hashlib
import os
import logging
import threading
import time
from bs4 import BeautifulSoup

#init
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
mainURL = 'https://breed.hackpascal.net/'
workDir = './'
md5File = 'md5sum.txt'
md5Dict = {}

#log
logging.getLogger("requests").setLevel(logging.WARNING)

logging.basicConfig(filename=workDir + 'sync.log.txt', filemode='w', level=logging.INFO, format='[%(levelname)s] (%(threadName)-10s) %(message)s',)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s'))
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)


def getBreedList():
  logging.debug("Getting File List!")
  try:
    r = requests.get(mainURL, verify=False)
  except:
    logging.error('Unknow error excepted! May network error!')
    return

  soup = BeautifulSoup(r.text, "html.parser")

  breeds = []
  for link in soup.find_all(href=re.compile("bin|zip|txt")):
     breeds.append(link.get('href'))
  logging.debug("Done!")
  return breeds


def getMD5Dict():
  logging.debug("Getting MD5 List!")
  try:
    tmp = requests.get(mainURL + md5File, verify=False).text.strip().split('\n')
  except:
    logging.error('Unknow error excepted! May network error!')
    return

  global md5Dict
  for md5 in tmp:
    md5Dict[md5.split()[1]] = md5.split()[0]

  logging.debug("Done!")


def checkHash(breed):
  newMD5 = hashlib.md5(open(workDir + breed, 'rb').read()).hexdigest()
  if breed in md5Dict:
    logging.info('File ' + breed + ' Exist in Hash Data! Checking...')
    if md5Dict[breed] == newMD5:
      return True
    else:
      return False
  else:
    logging.warning(breed + " Not Found in Hash File!")
    logging.warning('Maybe New File...Saving File: '+ breed)
    return True


def downloadBreed(breed):
  r = requests.get(mainURL + breed, verify = False)
  logging.info('Downloading File: ' + breed)
  with open(workDir + breed, "wb") as binFile:
    binFile.write(r.content)
  if checkHash(breed):
    logging.info('Hash of ' + breed + ' OK!')
  else:
    os.remove(workDir + breed)
    logging.waring(breed + ' Hash Fail')

def chunkWorker(chunk, chunkNow, chunkAll):
  for myJob in chunk:
    myThread = threading.Thread(name='No.'+str(chunk.index(myJob)+1)+' '+str(chunkNow)+'-'+str(chunkAll)+' '+myJob, target=downloadBreed, args=(myJob, ))
    myThread.start()
    time.sleep(0.1)

if __name__ == '__main__':
  getMD5Dict()
  delay = 1
  chunkSize = 7
  breedList = getBreedList()
  chunkedLists = [breedList[i:i + chunkSize] for i in xrange(0, len(breedList), chunkSize)]

  for chunk in chunkedLists:
    logging.info('Working on Chunk '+str(chunkedLists.index(chunk) + 1)+' OF '+str(len(chunkedLists)))
    chunkWorker(chunk, chunkedLists.index(chunk)+1, len(chunkedLists))
    logging.info("Delaying for "+str(delay)+"s")
    time.sleep(delay)

# -*- coding: utf-8 -*-
import zipfile
import os
import re
import shutil
import sys

# Set global parameters
temp_directory = 'outdir'
zip_file = 'e2_hanssettings_kabelNL.zip'

def get_name(filedata):
   name = re.findall("^#NAME (.*)", filedata)
   result = re.sub(',', '.', name[0])
   return result

def remove_separators(string):
   # Replace ' - ' for a space. In VLC a hyphen-minus is a separator between Title and Author.
   result = re.sub(' - ', ' ', string)
   # Replace ',' for a '.'. In VLC a comma is a separator between Title and Author.
   result = re.sub(',', '.', result)
   return result

def url_decoding(encoded_url):
   result = encoded_url.replace('%3a',':')
   # Sometimes an URL is ended with a newline. Remove it.
   result = re.sub('%0d', '', result)
   return result
   
# Extract ZIP file
try:
   fh = open(zip_file,'rb')
except IOError:
   print("There was an error opening the file: " + zip_file)
   sys.exit()
zfile = zipfile.ZipFile(fh)
zfile.extractall(temp_directory)
fh.close()

# Create temporary folder
if not os.path.exists(temp_directory):
   os.mkdir(temp_directory)
       
# Determine the bouquet list order
basepath = temp_directory + '/e2_hanssettings_kabelNL/'
stream_files = os.listdir(basepath)
bouquets_tv = open(basepath + 'bouquets.tv','rb')
filedata = bouquets_tv.readlines()
newlist = list()
for line in filedata:
   pattern = "\"(.*)\""
   match = re.search(pattern, line)
   if match:
      result = match.group()
      result = result.strip('\"')
      newlist.append(result)
bouquets_tv.close()

# Generate the m3u8 file
print("#EXTM3U")
for entry in newlist:
   if os.path.isfile(os.path.join(basepath, entry)) and re.search("stream",entry):
      bouquet_file = open(basepath + entry,"r") 
      filedata = bouquet_file.readlines()
      bouquet_name = get_name(filedata[0])
      index = 0
      print("#EXTINF:-1 group-title=\"" + bouquet_name +"\",++" + bouquet_name + "++")
      print("null")
      for line in filedata:
         # Line is stream
         if re.search('#SERVICE 4097:0', line):
            result = re.search("#DESCRIPTION (.*)",filedata[index + 1].strip())
            result = remove_separators(result.group(1))
            print("#EXTINF:-1 group-title=\"" + bouquet_name +"\"," + result)
            # Strip the 'SERVICE' text and the newline
            result = re.search("#SERVICE [0-9a-fA-F{1,}:]+(.*):",line.strip())
            url = url_decoding(result.group(1))
            print(url)
         # Line is placeholder
         if re.search('#SERVICE 1:64', line):
            result = re.search("#DESCRIPTION (.*)",filedata[index + 1].strip())
            result = remove_separators(result.group(1))
            print("#EXTINF:-1 group-title=\"" + bouquet_name +"\"," + result)
            print("null")
         index += 1
      bouquet_file.close()
# Remove the temporay folder 'outdir'
if os.path.exists(temp_directory):
   shutil.rmtree(temp_directory)

# -*- coding: utf-8 -*-
import zipfile
import os
import re
import shutil
import sys
import argparse

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--file", required=True,
                help="input name of the enigma2 zip file")
ap.add_argument('-t', "--tv", action='store_true', dest="boolean_tv",
                help="only tv stations in output", default=False)
ap.add_argument('-r', "--radio", action='store_true', dest="boolean_radio",
                help="only radio stations in output", default=False)
ap.add_argument('-c', "--choice", action='store_true', dest="boolean_choice",
                help="choose bouquets for output", default=False)
ap.add_argument('--version', action='version', version='%(prog)s 20200206')
args = vars(ap.parse_args())

# Set global parameters
temp_directory = 'out_dir'
zip_file = format(args["file"])


def get_name(file_data):
    name = re.findall("^#NAME (.*)", file_data)
    result = re.sub(',', '.', name[0])
    return result


def remove_separators(string):
    # Replace ' - ' for a space. In VLC a hyphen-minus is a separator between Title and Author.
    result = re.sub(' - ', ' ', string)
    # Replace ',' for a '.'. In VLC a comma is a separator between Title and Author.
    result = re.sub(',', '.', result)
    return result


def url_decoding(encoded_url):
    result = encoded_url.replace('%3a', ':')
    # Sometimes an URL is ended with a newline. Remove it.
    result = re.sub('%0d', '', result)
    return result


def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


# Create temporary folder
if not os.path.exists(temp_directory):
    os.mkdir(temp_directory)

# Extract ZIP file
try:
    fh = open(zip_file, 'rb')
except IOError:
    print("There was an error opening the file: " + zip_file)
    sys.exit()
zfile = zipfile.ZipFile(fh)
zfile.extractall(temp_directory)
fh.close()

# Determine the bouquet list order
os.walk(temp_directory)
sub_directory = next(os.walk(temp_directory))[1][0]
base_path = temp_directory + '/' + sub_directory + '/'
stream_files = os.listdir(base_path)
bouquets_tv = open(base_path + 'bouquets.tv', 'rb')
bouquets_radio = open(base_path + 'bouquets.radio', 'rb')

file_data = []
if args["boolean_tv"]:
    file_data += bouquets_tv.readlines()
    bouquets_tv.close()
if args["boolean_radio"]:
    file_data += bouquets_radio.readlines()
    bouquets_radio.close()
if not args["boolean_tv"] and not args["boolean_radio"]:
    file_data += bouquets_tv.readlines()
    bouquets_tv.close()
    file_data += bouquets_radio.readlines()
    bouquets_radio.close()

new_list = []
for line in file_data:
    pattern = "\"(.*)\""
    match = re.search(pattern, line)
    if match:
        search_result = match.group()
        search_result = search_result.strip('\"')
        new_list.append(search_result)

# Generate the m3u8 file
# Open new file
outfile = open("out.m3u8", "w")
outfile.write("#EXTM3U" + "\n")

for entry in new_list:
    if os.path.isfile(os.path.join(base_path, entry)) and re.search("stream", entry):
        bouquet_file = open(base_path + entry, "r")
        file_data = bouquet_file.readlines()
        bouquet_name = get_name(file_data[0])
        if args["boolean_choice"]:
            answer = query_yes_no("Add :" + bouquet_name)
        else:
            answer = True
        index = 0
        if answer:
            outfile.write("#EXTINF:-1 group-title=\"" + bouquet_name + "\",++" + bouquet_name + "++" + "\n")
            outfile.write("null" + "\n")
        for line in file_data:
            # Line is stream
            if re.search('#SERVICE 4097:0', line):
                search_result = re.search("#DESCRIPTION (.*)", file_data[index + 1].strip())
                search_result = remove_separators(search_result.group(1))
                if answer:
                    outfile.write("#EXTINF:-1 group-title=\"" + bouquet_name + "\"," + search_result + "\n")
                # Strip the 'SERVICE' text and the newline
                search_result = re.search("#SERVICE [0-9a-fA-F{1,}:]+(.*):", line.strip())
                url = url_decoding(search_result.group(1))
                if answer:
                    outfile.write(url + "\n")
            # Line is placeholder
            if re.search('#SERVICE 1:64', line):
                search_result = re.search("#DESCRIPTION (.*)", file_data[index + 1].strip())
                search_result = remove_separators(search_result.group(1))
                if answer:
                    outfile.write("#EXTINF:-1 group-title=\"" + bouquet_name + "\"," + search_result + "\n")
                    outfile.write("127.0.0.1" + "\n")
            index += 1
        bouquet_file.close()

outfile.close()
print ("File 'out.m3u8' generated!")

# Remove the temporary folder 'out_dir'
if os.path.exists(temp_directory):
    shutil.rmtree(temp_directory)

'''
This script requires: `grep` and `curl`

It will scan your spec docx for fourcc's and look if those are occuring somewhere in the code.
It will also load most recent fourcc's from mp4ra and check if they are actually registered.
If you have .doc files plese save them as .docx first. doc's are not supported.

example usage:

check all specs
python3 checkCoverage.py  --text ~/Box/MPEG/14496-30_timedText/w16794-TextOf-14496-30-2ndEd.docx \
                          --mp4 ~/Box/MPEG/14496-14_MP4/w17593_FDIS14496-14_F7+COR1+AMD1-R1-ITTF.docx \
                          --nal ~/Box/MPEG/14496-15_NAL/14496-15_5th.docx \
                          --heif ~/Box/MPEG/23008-12_HEIF/w18310_23008-12_Ed2_FDIS+COR1_R1.docx \
                          --isobmff ~/Box/MPEG/14496-12_ISOBMFF/14496-12_6th.docx

check specific fourcc's by providing a comma separated values:
python3 checkCoverage.py -i init,avc1,ftyp
'''

import sys
import re
import subprocess
import argparse
from docx2python import docx2python
import csv, io
import operator

__author__ = "Dimitri Podborski"
__version__ = "0.1"

def print_message(msg):
    print("\n" + "#" * 70)
    print("### " + str(msg))
    print("#" * 70 + "\n")

def command_to_string(command):
  cmd = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
  cmd_out, cmd_err = cmd.communicate()
  if not cmd_err == None:
    print("ERROR while executing {}\n\nstderr:\n{}".format(command, cmd_err))
    sys.exit(-1)
  return cmd_out.decode("utf-8") 

def get_fourccs_software(full_text):
  fourccs = []
  sources = []
  for line in full_text.splitlines():
    temp = re.search(r'MP4_FOUR_CHAR_CODE(.*?)\)', line).group(1)
    temp = temp.replace('(', '')
    temp = temp.replace(',', '')
    temp = temp.strip()
    if not temp[0] == '\'':
      continue
    fcc = temp[1] + temp[5] + temp[9] + temp[13]
    fourccs.append(fcc)
    line = line.replace('\t', ' ')
    line = re.sub(' +', ' ', line)
    sources.append(line)
  return {  'fourccs': fourccs,
            'sources': sources }

def get_sources(fcc, fccs):
  retVal = []
  sources = fccs.get('sources')
  full_list = fccs.get('fourccs')
  for i in range(len(full_list)):
    if full_list[i] == fcc:
      retVal.append(sources[i])
  return retVal

def get_fourccs_docx(filepath):
  fourccs = []
  sources = []
  descriptions = []
  doc_obj = docx2python(filepath)

  for line in doc_obj.body[0]:
    for n in range(7):
      if len(line[n][0]) == 4:
        fourccs.append(line[n][0])
        break
    sources.append(line[7][0].replace('\u200e', ''))
    descriptions.append(line[8][0])

  return {  'fourccs': fourccs,
            'sources': sources,
            'descriptions': descriptions }


def check_isobmff_light(args, fccs):
  docx_data = get_fourccs_docx("isobmff_table1.docx")

  docx_fccs = docx_data.get('fourccs')
  docx_srcs = docx_data.get('sources')
  docx_descr = docx_data.get('descriptions')

  not_implemented = []
  implemented = []

  for i in range(len(docx_fccs)):
    supported = get_sources(docx_fccs[i], fccs)
    if not supported:
      not_implemented.append('{}\t Sec.: {}\t\t{}'.format(docx_fccs[i], docx_srcs[i], docx_descr[i]))
    else:
      implemented.append('{}\t{}'.format(docx_fccs[i], supported[0]))
      for n in range(1, len(supported)):
        implemented.append('    \t{}'.format(supported[n]))

  if args.v:
    print("{} of {} fourccs are implemented:".format(len(implemented), len(not_implemented)+len(implemented)))
    for line in implemented:
      print(line)
  print("\n\n{} of {} fourccs are not implemented yet:".format(len(not_implemented), len(not_implemented)+len(implemented)))
  for line in not_implemented:
    print(line)

def process_fccs(fccs):
  block_list = [' or ', ' to ', '.mp4', ', ‘C', 'A’, ', '?vc?', '1111', 'NOTE', 'tier']
  fccs = list(set(fccs)) # remove dups
  fccs.sort() # sort
  fccs = [x.replace(u'\u00A0', ' ') for x in fccs if x not in block_list] # filter + replace no-break spaces
  return fccs


def check_full_doc(filepath, fccs_sw, verbose = False, mp4ra = None, spec = None):
  if not filepath:
    return
  if not filepath[-4:] == 'docx':
    print("WARNING: {} is not a docx file and will be ignored.".format(filepath))
    return  

  doc_obj = docx2python(filepath)

  pattern = r'(\'|"|‘|’)(.{4})(\'|"|‘|’)'
  matches = re.findall(pattern, doc_obj.text)

  fccs_doc = [items[1] for items in matches]
  fccs_doc = process_fccs(fccs_doc)

  if not mp4ra:
    if verbose:
      print("FCC \tSTATUS\tLOCATION")
    else:
      print("FCC \tSTATUS")
    for fcc in fccs_doc:
      found_sources = get_sources(fcc, fccs_sw)
      if not found_sources:
        print("{}\tNO".format(fcc))
      elif verbose:
        print("{}\tOK\t{}".format(fcc, found_sources[0]))
        for n in range(1, len(found_sources)):
          print("    \t  \t{}".format(found_sources[n]))
  else:
    not_supported_fccs = [] # those are not yet implemented
    supported_fccs = [] # those are implemented
    for fcc in fccs_doc:
      found_sources = get_sources(fcc, fccs_sw)
      if not found_sources:
        not_supported_fccs.append(fcc)
      else:
        supported_fccs.append([fcc, found_sources])

    # go through each not supported 4cc and look for it in mp4ra tables
    list_to_print = []
    for fcc in not_supported_fccs:
      found_at_mp4ra = False
      for key in mp4ra:
        if key == 'excluded':
          continue
        mp4ra_entry = [x for x in mp4ra[key] if x[0] == fcc]
        if len(mp4ra_entry) == 1:
          list_to_print.append([fcc, mp4ra_entry[0][1], key, mp4ra_entry[0][2], mp4ra_entry[0][3], mp4ra_entry[0][4], mp4ra_entry[0][5]])
          found_at_mp4ra = True
        elif len(mp4ra_entry) > 1:
          print_message("WARNING: mp4ra csv has more than one 4CC in the same file. This should never happen! '{}' in '{}'".format(fcc, key))
          sys.exit(-1)
      if not found_at_mp4ra:
        mp4ra_excluded = [x for x in mp4ra['excluded'] if x[0] == fcc]
        if len(mp4ra_excluded) == 0:
          print("NOTE: it seems that '{}' is not yet registered at mp4ra.".format(fcc))
    
    list_to_print = sorted(list_to_print, key = operator.itemgetter(2, 0))
    print('{:<8}{:<14}{:<18}{}'.format('FCC', 'SPEC', 'CETEGORY', 'DESCRIPTION'))
    for entry in list_to_print:
      print('{:<8}{:<14}{:<18}{}'.format(entry[0], entry[1], entry[2], entry[3]))


def get_mp4ra_fccs():
  print_message("Get all fccs from mp4ra")

  boxes = get_mp4ra_csvs(['boxes-qt.csv', 'boxes-udta.csv', 'boxes.csv'])
  brands = get_mp4ra_csvs(['brands.csv'])
  checksum_types = get_mp4ra_csvs(['checksum-types.csv'])
  color_types = get_mp4ra_csvs(['color-types.csv'])
  data_references = get_mp4ra_csvs(['data-references.csv'])
  entity_groups = get_mp4ra_csvs(['entity-groups.csv'])
  handlers = get_mp4ra_csvs(['handlers.csv'])
  item_properties = get_mp4ra_csvs(['item-properties.csv'])
  item_references = get_mp4ra_csvs(['item-references.csv'])
  item_types = get_mp4ra_csvs(['item-types.csv'])
  multiview_attributes = get_mp4ra_csvs(['multiview-attributes.csv'])
  sample_entries = get_mp4ra_csvs(['sample-entries-boxes.csv', 'sample-entries-qt.csv', 'sample-entries.csv'])
  sample_groups = get_mp4ra_csvs(['sample-groups.csv'])
  schemes = get_mp4ra_csvs(['schemes.csv'])
  track_groups = get_mp4ra_csvs(['track-groups.csv'])
  track_references = get_mp4ra_csvs(['track-references-qt.csv', 'track-references.csv'])
  track_selection = get_mp4ra_csvs(['track-selection.csv'])
  excluded = get_mp4ra_csvs(['knownduplicates.csv', 'oti.csv', 'stream-types.csv', 'textualcontent.csv', 'unlisted.csv'])

  return {
    'handler': handlers,
    'box': boxes,
    'sample_entry': sample_entries,
    'brand': brands,
    'scheme': schemes,
    'track_group': track_groups,
    'sample_group': sample_groups,
    'entity_group': entity_groups,
    'track_selection': track_selection,
    'track_reference': track_references,
    'item_reference': item_references,
    'data_reference': data_references,
    'item_property': item_properties,
    'item_type': item_types,
    'checksum_type': checksum_types,
    'color_type': color_types,
    'multiview_attr': multiview_attributes,
    'excluded': excluded
    }

# returns a list of entries like this: [4cc, spec, description, handle, object_type, type]
def get_mp4ra_csvs(files_array):
  retVal = []
  base_url = 'https://raw.githubusercontent.com/mp4ra/mp4ra.github.io/dev/CSV/'
  
  for f in files_array:
    url = base_url + f
    print("Download: {}".format(url))

    alltext = command_to_string('curl -s ' + url)

    csvReader = csv.DictReader(io.StringIO(alltext))
    headers = csvReader.fieldnames
    if 'code' in headers:
      for row in csvReader:
        csvCode = row['code'].replace('$20', ' ')
        if 'description' in headers:
          csvDesc = row['description']
        else:
          csvDesc = ''
        if 'specification' in headers:
          csvSpec = row['specification']
        else:
          csvSpec = ''
        if 'handler' in headers:
          csvHandle = row['handler']
        else:
          csvHandle = ''
        if 'ObjectType' in headers:
          csvObjectType = row['ObjectType']
        else:
          csvObjectType = ''
        if 'type' in headers:
          csvType = row['type']
        else:
          csvType = ''
        retVal.append([csvCode, csvSpec, csvDesc, csvHandle, csvObjectType, csvType])
  return retVal

def main():
  print_message("Coverage analyzer version {}".format(__version__))
  print("run -h to see more options\n\n")

  parser = argparse.ArgumentParser( formatter_class=argparse.RawTextHelpFormatter,
                                    description="Check what is implemented in the softwre. Check the following specs:\n"
                                                "ISO/IEC 14496-12 - isobmff\n"
                                                "ISO/IEC 14496-14 - mp4\n"
                                                "ISO/IEC 14496-15 - nal\n"
                                                "ISO/IEC 14496-30 - text\n"
                                                "ISO/IEC 23008-12 - heif")
  parser.add_argument("-i", help="Check specific fourcc's, separate multiple with commas, use _ for spaces.")
  parser.add_argument("-r", help="Root directory of the software", default="IsoLib")
  parser.add_argument("-v", help="Show more infos", action='store_true')
  parser.add_argument("--isobmff", help="Path to ISO/IEC 14496-12 spec docx file")
  parser.add_argument("--mp4", help="Path to ISO/IEC 14496-14 spec docx file")
  parser.add_argument("--nal", help="Path to ISO/IEC 14496-15 spec docx file")
  parser.add_argument("--text", help="Path to ISO/IEC 14496-30 spec docx file")
  parser.add_argument("--heif", help="Path to ISO/IEC 23008-12 spec docx file")
  args = parser.parse_args()

  command = 'grep -rnw ' + args.r + ' --include=\*.{cpp,c,cc,cs,h,hpp} -e "MP4_FOUR_CHAR_CODE"'
  grep_text = command_to_string( command )
  fccs_sw = get_fourccs_software( grep_text )

  # user only wants to check specific fourcc's
  if args.i:
    print("FCC \tSTATUS\tLOCATION")
    for fcc in args.i.split(','):
      fcc = fcc.replace('_', ' ')
      found = get_sources(fcc, fccs_sw)
      if not found:
        print("{}\tNO".format(fcc))
      else:
        print("{}\tOK\t{}".format(fcc, found[0]))
        for n in range(1, len(found)):
          print("    \t  \t{}".format(found[n]))
    sys.exit(-1)

  mp4ra = get_mp4ra_fccs()
  
  if not args.isobmff == None:
    print_message("Check coverage of ISO/IEC 14496-12")
    check_full_doc(args.isobmff, fccs_sw, args.v, mp4ra, "ISO")
  else:
    print_message("Check coverage of ISO/IEC 14496-12 (light mode)")
    print("only checking Table 1 located in isobmff_table1.docx")
    check_isobmff_light(args, fccs_sw)
  if not args.mp4 == None:
    print_message("Check coverage of ISO/IEC 14496-14")
    check_full_doc(args.mp4, fccs_sw, args.v, mp4ra, "MP4")
  if not args.nal == None:
    print_message("Check coverage of ISO/IEC 14496-15")
    check_full_doc(args.nal, fccs_sw, args.v, mp4ra, "NAL")
  if not args.text == None:
    print_message("Check coverage of ISO/IEC 14496-30")
    check_full_doc(args.text, fccs_sw, args.v, mp4ra, "ISO-Text")
  if not args.heif == None:
    print_message("Check coverage of ISO/IEC 23008-12")
    check_full_doc(args.heif, fccs_sw, args.v, mp4ra, "HEIF")

# run
if __name__ == '__main__':
  sys.exit(main())

import sys
import re
import subprocess
import argparse
from docx2python import docx2python

__author__ = "Dimitri Podborski"
__version__ = "0.1"
__status__ = "Development"

def print_message(msg):
    print("\n" + "#" * 80)
    print("### " + str(msg))
    print("#" * 80 + "\n")

def command_to_string(command):
  cmd = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
  cmd_out, cmd_err = cmd.communicate()
  if not cmd_err == None:
    print("ERROR while executing {}\n\nstderr:\n{}".format(command, cmd_err))
    sys.exit(-1)
  return cmd_out.decode("utf-8") 

def get_fourccs(full_text):
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

def find_fcc(fcc, fccs):
  sources = fccs.get('sources')
  retVal = []
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


def check_isobmff(args, fccs):
  print_message("Check coverage of ISO/IEC 14496-12")

  if not args.isobmff:
    print("No isobmff docx file specified. \nRun light mode while only checking Table 1 located in isobmff_table1.docx")
    docx_data = get_fourccs_docx("isobmff_table1.docx")
  else:
    docx_data = get_fourccs_docx(args.isobmff)

  docx_fccs = docx_data.get('fourccs')
  docx_srcs = docx_data.get('sources')
  docx_descr = docx_data.get('descriptions')

  not_implemented = []
  implemented = []

  for i in range(len(docx_fccs)):
    supported = find_fcc(docx_fccs[i], fccs)
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

def check_mp4(args, fccs):
  if not args.mp4:
    return
  print_message("Check coverage of ISO/IEC 14496-14")
  print("TBD")

def check_nal(args, fccs):
  if not args.nal:
    return
  print_message("Check coverage of ISO/IEC 14496-15")
  print("TBD")

def check_text(args, fccs):
  if not args.text:
    return
  print_message("Check coverage of ISO/IEC 14496-30")
  print("TBD")

def check_heif(args, fccs):
  if not args.heif:
    return
  print_message("Check coverage of ISO/IEC 23008-12")
  print("TBD")

def main():
  print("Coverage analyzer version {}".format(__version__))
  print("run -h to see more options\n\n")

  parser = argparse.ArgumentParser( formatter_class=argparse.RawTextHelpFormatter,
                                    description="Check what is implemented in the softwre. Check the following specs:\n"
                                                "ISO/IEC 14496-12 - isobmff\n"
                                                "ISO/IEC 14496-14 - mp4\n"
                                                "ISO/IEC 14496-15 - nal\n"
                                                "ISO/IEC 14496-30 - text\n"
                                                "ISO/IEC 23008-12 - heif")
  parser.add_argument("-i", help="Check specific fourcc's, separate multiple with commas, use _ for spaces.")
  parser.add_argument("-v", help="Show more infos", action='store_true')
  parser.add_argument("--isobmff", help="Path to ISO/IEC 14496-12 spec docx file")
  parser.add_argument("--mp4", help="Path to ISO/IEC 14496-14 spec docx file")
  parser.add_argument("--nal", help="Path to ISO/IEC 14496-15 spec docx file")
  parser.add_argument("--text", help="Path to ISO/IEC 14496-30 spec docx file")
  parser.add_argument("--heif", help="Path to ISO/IEC 23008-12 spec docx file")
  args = parser.parse_args()

  command = 'grep -rnw IsoLib --include=\*.{cpp,c,cc,cs,h,hpp} -e "MP4_FOUR_CHAR_CODE"'
  grep_text = command_to_string( command )
  fccs = get_fourccs( grep_text )

  # user only wants to check specific fourcc's
  if args.i:
    print("FCC \tSTATUS\tLOCATION")
    for fcc in args.i.split(','):
      fcc = fcc.replace('_', ' ')
      found = find_fcc(fcc, fccs)
      if not found:
        print("{}\tNO".format(fcc))
      else:
        print("{}\tOK\t{}".format(fcc, found[0]))
        for n in range(1, len(found)):
          print("    \t  \t{}".format(found[n]))
    sys.exit(-1)

  check_isobmff(args, fccs)
  check_mp4(args, fccs)
  check_nal(args, fccs)
  check_text(args, fccs)
  check_heif(args, fccs)

# run
if __name__ == '__main__':
  sys.exit(main())

import sys
import re
import subprocess
from docx2python import docx2python

__author__ = "Dimitri Podborski"
__version__ = "0.1"
__status__ = "Development"


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

def main():
  print("Coverage analyzer version {}\n".format(__version__))

  command = 'grep -rnw IsoLib/libisomediafile --include=\*.{cpp,c,cc,cs,h,hpp} -e "MP4_FOUR_CHAR_CODE"'
  libonly = command_to_string( command )
  fccs = get_fourccs( libonly )

  docx_data = get_fourccs_docx("isobmff_boxes_6thEd.docx")
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
      implemented.append('{}\t{}'.format(docx_fccs[i], supported))

  print("{} of {} fourccs are implemented:".format(len(implemented), len(not_implemented)+len(implemented)))
  for line in implemented:
    print(line)
  print("\n\n{} of {} fourccs are not implemented yet:".format(len(not_implemented), len(not_implemented)+len(implemented)))
  for line in not_implemented:
    print(line)

# run
if __name__ == '__main__':
  sys.exit(main())

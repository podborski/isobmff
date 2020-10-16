import subprocess
import sys
import os



# all `ffmpeg -pix_fmts` with Output flag set
ffmpeg_output_fmts = [
  'yuv420p',
  'yuyv422',
  'rgb24',
  'bgr24',
  'yuv422p',
  'yuv444p',
  'yuv410p',
  'yuv411p',
  'gray',
  'monow',
  'monob',
  'yuvj420p',
  'yuvj422p',
  'yuvj444p',
  'uyvy422',
  'bgr8',
  'bgr4',
  'bgr4_byte',
  'rgb8',
  'rgb4',
  'rgb4_byte',
  'nv12',
  'nv21',
  'argb',
  'rgba',
  'abgr',
  'bgra',
  'gray16be',
  'gray16le',
  'yuv440p',
  'yuvj440p',
  'yuva420p',
  'rgb48be',
  'rgb48le',
  'rgb565be',
  'rgb565le',
  'rgb555be',
  'rgb555le',
  'bgr565be',
  'bgr565le',
  'bgr555be',
  'bgr555le',
  'yuv420p16le',
  'yuv420p16be',
  'yuv422p16le',
  'yuv422p16be',
  'yuv444p16le',
  'yuv444p16be',
  'rgb444le',
  'rgb444be',
  'bgr444le',
  'bgr444be',
  'ya8',
  'bgr48be',
  'bgr48le',
  'yuv420p9be',
  'yuv420p9le',
  'yuv420p10be',
  'yuv420p10le',
  'yuv422p10be',
  'yuv422p10le',
  'yuv444p9be',
  'yuv444p9le',
  'yuv444p10be',
  'yuv444p10le',
  'yuv422p9be',
  'yuv422p9le',
  'gbrp',
  'gbrp9be',
  'gbrp9le',
  'gbrp10be',
  'gbrp10le',
  'gbrp16be',
  'gbrp16le',
  'yuva422p',
  'yuva444p',
  'yuva420p9be',
  'yuva420p9le',
  'yuva422p9be',
  'yuva422p9le',
  'yuva444p9be',
  'yuva444p9le',
  'yuva420p10be',
  'yuva420p10le',
  'yuva422p10be',
  'yuva422p10le',
  'yuva444p10be',
  'yuva444p10le',
  'yuva420p16be',
  'yuva420p16le',
  'yuva422p16be',
  'yuva422p16le',
  'yuva444p16be',
  'yuva444p16le',
  'xyz12le',
  'xyz12be',
  'rgba64be',
  'rgba64le',
  'bgra64be',
  'bgra64le',
  'yvyu422',
  'ya16be',
  'ya16le',
  'gbrap',
  'gbrap16be',
  'gbrap16le',
  '0rgb',
  'rgb0',
  '0bgr',
  'bgr0',
  'yuv420p12be',
  'yuv420p12le',
  'yuv420p14be',
  'yuv420p14le',
  'yuv422p12be',
  'yuv422p12le',
  'yuv422p14be',
  'yuv422p14le',
  'yuv444p12be',
  'yuv444p12le',
  'yuv444p14be',
  'yuv444p14le',
  'gbrp12be',
  'gbrp12le',
  'gbrp14be',
  'gbrp14le',
  'yuvj411p',
  'yuv440p10le',
  'yuv440p10be',
  'yuv440p12le',
  'yuv440p12be',
  'ayuv64le',
  'p010le',
  'p010be',
  'gbrap12be',
  'gbrap12le',
  'gbrap10be',
  'gbrap10le',
  'gray12be',
  'gray12le',
  'gray10be',
  'gray10le',
  'p016le',
  'p016be',
  'gray9be',
  'gray9le',
  'gbrpf32be',
  'gbrpf32le',
  'gbrapf32be',
  'gbrapf32le',
  'gray14be',
  'gray14le',
  'grayf32be',
  'grayf32le',
  'yuva422p12be',
  'yuva422p12le',
  'yuva444p12be',
  'yuva444p12le',
  'nv24',
  'nv42'
]

# 4CC to uncompressed file mapping
format_to_file = [
  ['2vuy', 'uyvy422_qcif.raw'],
  ['yuv2', 'yuyv422_qcif.raw'],
  ['v308', 'rgb24_qcif.raw'],       # ffmpeg can't generate packed CrYCb, I take packed RGB
  ['v408', 'rgba_qcif.raw'],        # ffmpeg can't generate packed CbYCrA, I take packed RGBA
  ['v216', 'uyvy422_qcif.raw'],     # ... packed k422YpCbCr16CodecType 32bpp, I take uyvy422 with 16bpp
  ['v410', 'rgba_qcif.raw'],        # ... packed k444YpCbCr10CodecType, I take rgba instead
  ['v210', 'yuv422p10be_qcif.raw'], # ... packed k422YpCbCr10CodecType,
  ['raw ', 'rgb24_qcif.raw'],
  ['j420', 'yuv420p_qcif.raw'],
  ['I420', 'yuv420p_qcif.raw'],
  ['IYUV', 'yuv420p_qcif.raw'],
  ['yv12', 'yuv420p_qcif.raw'],
  ['YVYU', 'yvyu422_qcif.raw'],
  ['RGBA', 'rgba_qcif.raw'],
  ['ABGR', 'abgr_qcif.raw']
]

def command_to_string(command):
  cmd = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
  cmd_out, cmd_err = cmd.communicate()
  if not cmd_err == None:
    print("ERROR while executing {}\n\nstderr:\n{}".format(command, cmd_err))
    sys.exit(-1)
  return cmd_out.decode("utf-8")

def create_uncompressed_files(root_dir):
  banner = '\nGenerate {} uncompressed files:'.format(len(ffmpeg_output_fmts))
  print(banner)
  print('-'*len(banner))
  if not os.path.exists(root_dir):
    os.makedirs(root_dir)

  for fmt in ffmpeg_output_fmts:
    print('Uncompressed format ' + fmt)
    out_file = os.path.join(root_dir, fmt+'_qcif.raw')
    cmd = 'ffmpeg -y -loglevel panic -hide_banner -f lavfi -i testsrc=duration=2:size=qcif:rate=30 -s qcif -pix_fmt {} -f rawvideo {}'.format(fmt, out_file)
    command_to_string(cmd)

def package_uncompressed_files(in_dir, out_dir):
  banner = '\nPackage {} uncompressed files:'.format(len(format_to_file))
  print(banner)
  print('-'*len(banner))
  if not os.path.exists(in_dir):
    os.makedirs(in_dir)
  if not os.path.exists(out_dir):
    os.makedirs(out_dir)
  for fmt, raw_file in format_to_file:
    print("Package {:<20} to mov with 4CC='{}'".format(raw_file, fmt))
    in_file = os.path.join(in_dir, raw_file)
    out_file = os.path.join(out_dir, fmt.replace(' ', '_') + '.mov')
    cmd = "./bin/raw2mov {} {} -w 176 -h 144 -c '{}' -p 2".format(in_file, out_file, fmt)
    command_to_string(cmd)

create_uncompressed_files('./bin/uncompressed')
package_uncompressed_files('./bin/uncompressed', './bin/packaged')
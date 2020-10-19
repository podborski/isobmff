import subprocess
import sys
import os
import struct

width = 176
height = 144

# all `ffmpeg -pix_fmts` with Output flag set
ffmpeg_output_fmts = [ 
  'yuv420p', 'yuyv422', 'rgb24', 'bgr24', 'yuv422p', 'yuv444p', 'yuv410p', 'yuv411p', 'gray', 'monow', 'monob',
  'yuvj420p', 'yuvj422p', 'yuvj444p', 'uyvy422', 'bgr8', 'bgr4', 'bgr4_byte', 'rgb8', 'rgb4', 'rgb4_byte', 'nv12', 'nv21',
  'argb', 'rgba', 'abgr', 'bgra', 'gray16be', 'gray16le', 'yuv440p', 'yuvj440p', 'yuva420p', 'rgb48be', 'rgb48le', 'rgb565be',
  'rgb565le', 'rgb555be', 'rgb555le', 'bgr565be', 'bgr565le', 'bgr555be', 'bgr555le', 'yuv420p16le', 'yuv420p16be', 'yuv422p16le', 'yuv422p16be', 
  'yuv444p16le', 'yuv444p16be', 'rgb444le', 'rgb444be', 'bgr444le', 'bgr444be', 'ya8', 'bgr48be', 'bgr48le', 'yuv420p9be', 'yuv420p9le', 'yuv420p10be',
  'yuv420p10le', 'yuv422p10be', 'yuv422p10le', 'yuv444p9be', 'yuv444p9le', 'yuv444p10be', 'yuv444p10le', 'yuv422p9be', 'yuv422p9le', 'gbrp', 'gbrp9be', 'gbrp9le',
  'gbrp10be', 'gbrp10le', 'gbrp16be', 'gbrp16le', 'yuva422p', 'yuva444p', 'yuva420p9be', 'yuva420p9le', 'yuva422p9be', 'yuva422p9le', 'yuva444p9be', 'yuva444p9le',
  'yuva420p10be', 'yuva420p10le', 'yuva422p10be', 'yuva422p10le', 'yuva444p10be', 'yuva444p10le', 'yuva420p16be', 'yuva420p16le', 'yuva422p16be', 'yuva422p16le', 'yuva444p16be', 
  'yuva444p16le', 'xyz12le', 'xyz12be', 'rgba64be', 'rgba64le', 'bgra64be', 'bgra64le', 'yvyu422', 'ya16be', 'ya16le', 'gbrap', 'gbrap16be',
  'gbrap16le', '0rgb', 'rgb0', '0bgr', 'bgr0', 'yuv420p12be', 'yuv420p12le', 'yuv420p14be', 'yuv420p14le', 'yuv422p12be', 'yuv422p12le', 'yuv422p14be',
  'yuv422p14le', 'yuv444p12be', 'yuv444p12le', 'yuv444p14be', 'yuv444p14le', 'gbrp12be', 'gbrp12le', 'gbrp14be', 'gbrp14le', 'yuvj411p', 'yuv440p10le', 'yuv440p10be',
  'yuv440p12le', 'yuv440p12be', 'ayuv64le', 'p010le', 'p010be', 'gbrap12be', 'gbrap12le', 'gbrap10be', 'gbrap10le', 'gray12be', 'gray12le', 'gray10be',
  'gray10le', 'p016le', 'p016be', 'gray9be', 'gray9le', 'gbrpf32be', 'gbrpf32le', 'gbrapf32be', 'gbrapf32le', 'gray14be', 'gray14le', 'grayf32be',
  'grayf32le', 'yuva422p12be', 'yuva422p12le', 'yuva444p12be', 'yuva444p12le', 'nv24', 'nv42'
]

gst_output_fmts = [ 
  'AYUV64', 'ARGB64', 'GBRA_12LE', 'GBRA_12BE', 'Y412_LE', 'Y412_BE', 'A444_10LE', 'GBRA_10LE', 'A444_10BE', 'GBRA_10BE', 'A422_10LE', 'A422_10BE',
  'A420_10LE', 'A420_10BE', 'RGB10A2_LE', 'BGR10A2_LE', 'Y410', 'GBRA', 'ABGR', 'VUYA', 'BGRA', 'AYUV', 'ARGB', 'RGBA',
  'A420', 'Y444_16LE', 'Y444_16BE', 'v216', 'P016_LE', 'P016_BE', 'Y444_12LE', 'GBR_12LE', 'Y444_12BE', 'GBR_12BE', 'I422_12LE', 'I422_12BE',
  'Y212_LE', 'Y212_BE', 'I420_12LE', 'I420_12BE', 'P012_LE', 'P012_BE', 'Y444_10LE', 'GBR_10LE', 'Y444_10BE', 'GBR_10BE', 'r210', 'I422_10LE',
  'I422_10BE', 'NV16_10LE32', 'Y210', 'v210', 'UYVP', 'I420_10LE', 'I420_10BE', 'P010_10LE', 'NV12_10LE32', 'NV12_10LE40', 'P010_10BE', 'Y444',
  'GBR', 'NV24', 'xBGR', 'BGRx', 'xRGB', 'RGBx', 'BGR', 'IYU2', 'v308', 'RGB', 'Y42B', 'NV61',
  'NV16', 'VYUY', 'UYVY', 'YVYU', 'YUY2', 'I420', 'YV12', 'NV21', 'NV12', 'NV12_64Z32', 'NV12_4L4', 'NV12_32L32',
  'Y41B', 'IYU1', 'YVU9', 'YUV9', 'RGB16', 'BGR16', 'RGB15', 'BGR15', 'RGB8P', 'GRAY16_LE', 'GRAY16_BE', 'GRAY10_LE32', 'GRAY8'
]

def command_to_string(command):
  cmd = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
  cmd_out, cmd_err = cmd.communicate()
  if not cmd_err == None:
    print("ERROR while executing {}\n\nstderr:\n{}".format(command, cmd_err))
    sys.exit(-1)
  return cmd_out.decode("utf-8")

def create_uncompressed_files_ffmpeg(root_dir):
  banner = '\nGenerate {} uncompressed files with ffmpeg:'.format(len(ffmpeg_output_fmts))
  print(banner)
  print('-'*len(banner))
  if not os.path.exists(root_dir):
    os.makedirs(root_dir)
  # create all uncompressed files which ffmpeg supports
  for fmt in ffmpeg_output_fmts:
    print('Uncompressed format ' + fmt)
    out_file = os.path.join(root_dir, 'ffmpeg_{}_{}x{}.raw'.format(fmt, width, height))
    cmd = 'ffmpeg -y -loglevel panic -hide_banner -f lavfi -i testsrc=duration=2:size={}x{}:rate=30 -s qcif -pix_fmt {} -f rawvideo {}'.format(width, height, fmt, out_file)
    command_to_string(cmd)

def create_uncompressed_files_gstreamer(root_dir):
  banner = '\nGenerate {} uncompressed files with gstreamer:'.format(len(ffmpeg_output_fmts))
  print(banner)
  print('-'*len(banner))
  if not os.path.exists(root_dir):
    os.makedirs(root_dir)
  # create all uncompressed files which gstreamer supports
  for fmt in gst_output_fmts:
    print('Uncompressed format ' + fmt)
    out_file = os.path.join(root_dir, 'gst_{}_{}x{}.raw'.format(fmt, width, height))
    cmd = 'gst-launch-1.0 videotestsrc num-buffers=60 ! videoconvert ! video/x-raw,format={}, width={}, height={} ! filesink location={}'.format(fmt, width, height, out_file)
    command_to_string(cmd)

def package_uncompressed_files(in_dir, out_dir, fcc_to_fmt):
  banner = '\nPackage {} uncompressed files:'.format(len(fcc_to_fmt))
  print(banner)
  print('-'*len(banner))
  if not os.path.exists(in_dir):
    os.makedirs(in_dir)
  if not os.path.exists(out_dir):
    os.makedirs(out_dir)
  for fourcc, pix_fmt in fcc_to_fmt:
    print("Package {:<10} to mov with 4CC='{}'".format(pix_fmt, fourcc))
    in_file = os.path.join(in_dir, '{}_{}x{}.raw'.format(pix_fmt, width, height))
    out_file = os.path.join(out_dir, fourcc.replace(' ', '_') + '_' + pix_fmt + '.mov')
    cmd = "./bin/raw2mov {} {} -w 176 -h 144 -c '{}' -p 2".format(in_file, out_file, fourcc)
    command_to_string(cmd)

# planar yuv444 to packed uyv444 as described in icefloe for v308
def create_v308(yuv444p_file, out_file):
  if not os.path.exists(yuv444p_file):
    print('Error: YUV 4:4:4 file \'{}\' does not exist'.format(yuv444p_file))
    return
  print('Create uncompressed format v308')
  with open(yuv444p_file, 'rb') as binary_file_in:
    data_in = binary_file_in.read()
    data_out = bytearray(len(data_in))
    res = width*height
    frames = int(len(data_in) / (res*3))
    for f in range(0, frames):
      frame_data = data_in[f*res*3:(f+1)*res*3]
      for n in range(0, res):
        data_out[f*res*3 + n*3+0] = frame_data[res*1+n] # u
        data_out[f*res*3 + n*3+1] = frame_data[res*0+n] # y
        data_out[f*res*3 + n*3+2] = frame_data[res*2+n] # v
    with open(out_file, 'wb') as binary_file_out:
      binary_file_out.write(data_out)

# planar yuv444 to packed vyua4444 as described in icefloe for v408
def create_v408(yuv444p_file, out_file):
  if not os.path.exists(yuv444p_file):
    print('Error: YUV 4:4:4 file \'{}\' does not exist'.format(yuv444p_file))
    return
  print('Create uncompressed format v408')
  with open(yuv444p_file, 'rb') as binary_file_in:
    data_in = binary_file_in.read()
    res = width*height
    frames = int(len(data_in) / (res*3))
    data_out = bytearray(res*4*frames)
    for f in range(0, frames):
      frame_data = data_in[f*res*3:(f+1)*res*3]
      for n in range(0, res):
        y = frame_data[res*0+n]
        u = frame_data[res*1+n]
        v = frame_data[res*2+n]
        data_out[f*res*4 + n*4+0] = v
        data_out[f*res*4 + n*4+1] = y
        data_out[f*res*4 + n*4+2] = u
        data_out[f*res*4 + n*4+3] = 255
    with open(out_file, 'wb') as binary_file_out:
      binary_file_out.write(data_out)

# v216
def create_v216(yuv422p16le_file, out_file):
  if not os.path.exists(yuv422p16le_file):
    print('Error: YUV 4:2:0 file \'{}\' does not exist'.format(yuv422p16le_file))
    return
  print('Create uncompressed format v216')
  with open(yuv422p16le_file, 'rb') as binary_file_in:
    data_in = binary_file_in.read()
    res = width*height
    frames = int(len(data_in) / (res*3))
    data_out = bytearray(res*4*frames)
    for f in range(0, frames):
      frame_data = data_in[f*res*3:(f+1)*res*3]
      for n in range(0, res):
        y = frame_data[res*0+n]
        u = frame_data[res*1+n]
        v = frame_data[res*2+n]
        data_out[f*res*4 + n*4+0] = v
        data_out[f*res*4 + n*4+1] = y
        data_out[f*res*4 + n*4+2] = u
        data_out[f*res*4 + n*4+3] = 255
    with open(out_file, 'wb') as binary_file_out:
      binary_file_out.write(data_out)


# 1. CREATE uncompressed files
create_uncompressed_files_ffmpeg('./bin/uncompressed')
create_uncompressed_files_gstreamer('./bin/uncompressed')
yuv444p_in = './bin/uncompressed/ffmpeg_yuv444p_{}x{}.raw'.format(width, height)
create_v308(yuv444p_in, './bin/uncompressed/v308_uyv444_{}x{}.raw'.format(width, height))   # v308: ffmpeg can't generate packed CrYCb so I create one myself
create_v408(yuv444p_in, './bin/uncompressed/v408_vyua4444_{}x{}.raw'.format(width, height)) # v408: ffmpeg can't generate packed CbYCrA so I create one myself

### 2. PACKAGE
# 4CC to pixel format mapping
fcc_to_fmt = [
  ['2vuy', 'ffmpeg_uyvy422'],
  ['yuv2', 'ffmpeg_yuyv422'],
  ['v308', 'v308_uyv444'],
  ['v308', 'gst_v308'],
  ['v408', 'v408_vyua4444'],
  ['v216', 'ffmpeg_uyvy422'],      # ... packed k422YpCbCr16CodecType 32bpp, I take uyvy422 with 16bpp       yuv422p16le
  ['v216', 'gst_v216'],
  ['v410', 'ffmpeg_rgba'],         # ... packed k444YpCbCr10CodecType, I take rgba instead
  ['v410', 'gst_Y410'],
  ['v210', 'ffmpeg_yuv422p10be'],  # ... packed k422YpCbCr10CodecType,
  ['v210', 'gst_v210'], 
  ['raw ', 'ffmpeg_rgb24'],
  ['j420', 'ffmpeg_yuv420p'],
  ['I420', 'ffmpeg_yuv420p'],
  ['IYUV', 'ffmpeg_yuv420p'],
  ['yv12', 'ffmpeg_yuv420p'],
  ['YVYU', 'ffmpeg_yvyu422'],
  ['RGBA', 'ffmpeg_rgba'],
  ['ABGR', 'ffmpeg_abgr']
]
package_uncompressed_files('./bin/uncompressed', './bin/packaged', fcc_to_fmt)
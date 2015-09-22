# Copyright (C) 2009 The Android Open Source Project
# Copyright (c) 2011, Code Aurora Forum. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Emit commands needed for QCOM devices during OTA installation
(installing the radio image)."""

import common
import re

try:
  from hashlib import sha1 as sha1
except ImportError:
  from sha import sha as sha1

def GetRadioFiles(z):
  out = {}
  for info in z.infolist():
    if info.filename.startswith("RADIO/") and (info.filename.__len__() > len("RADIO/")):
      fn = "RADIO/" + info.filename[6:]
      out[fn] = fn
  return out

def GetAmssFiles(z):
  out = {}
  for info in z.infolist():
    if info.filename.startswith("sys_boot/") and (info.filename.__len__() > len("sys_boot/")):
      fn = "sys_boot/" + info.filename[9:]
      out[fn] = fn
  return out

def LoadRadioFiles(z):
  """Load all the files from RADIO/... in a given target-files
  ZipFile, and return a dict of {filename: File object}."""
  out = {}
  for info in z.infolist():
    if info.filename.startswith("RADIO/"):
      basefilename = info.filename[6:]
      fn = ""
      # AMSS raw images flashed in AP side
      if basefilename.startswith("AMSS") and basefilename.endswith("mbn"):
        fn = "sys_boot/image/" + basefilename
      # Other raw radio images flashed in AP side
      elif basefilename.endswith("bin") or basefilename.endswith("BIN"):
        fn = basefilename
      # Encrypted radio images
      elif basefilename.endswith("enc") or basefilename.endswith("ENC"):
        fn = basefilename
      else:
        print "Warning: unexpected radio file:" + basefilename
      data = z.read(info.filename)
      out[fn] = common.File(fn, data)
  return out


def FullOTA_Assertions(info):
  AddBootloaderAssertion(info, info.input_zip)


def IncrementalOTA_Assertions(info):
  #TODO: Implement device specific asserstions.
  print "Loading target radio file..."
  target_data = LoadRadioFiles(info.target_zip)
  print "Loading source radio file..."
  source_data = LoadRadioFiles(info.source_zip)

  verbatim_targets = []
  info.radio_list = []
  patch_list = []
  diffs = []
  largest_source_size = 0
  for fn in sorted(target_data.keys()):
    tf = target_data[fn]
    assert fn == tf.name
    sf = source_data.get(fn, None)

    if sf is None or fn in info.require_verbatim or fn.endswith("bin") or fn.endswith("BIN"):
      # This file should be included verbatim
      if fn in info.prohibit_verbatim:
        raise common.ExternalError("\"%s\" must be sent verbatim" % (fn,))
      print "add full update file", fn, "verbatim"
      tf.AddToZip(info.output_zip)
      verbatim_targets.append((fn, tf.size))
      info.radio_whole_list.append((tf.name, tf, sf, tf.size, tf.sha1))
    elif tf.sha1 != sf.sha1:
      # File is different; consider sending as a patch
      print "change file", sf.name, sf.sha1
      diffs.append(common.Difference(tf, sf))
    else:
      print "no change file", sf.name, sf.sha1
      # Target file identical to source.
      pass

  common.ComputeDifferences(diffs)

  for diff in diffs:
    tf, sf, d = diff.GetPatch()
    if d is None or len(d) > tf.size * info.patch_threshold:
      # patch is almost as big as the file; don't bother patching
      tf.AddToZip(info.output_zip)
      verbatim_targets.append((tf.name, tf.size))
      info.radio_whole_list.append((tf.name, tf, sf, tf.size, common.sha1(d).hexdigest()))
    else:
      common.ZipWriteStr(info.output_zip, "patch/" + tf.name + ".p", d)
      info.radio_list.append((tf.name, tf, sf, tf.size, common.sha1(d).hexdigest()))
      largest_source_size = max(largest_source_size, sf.size)
  print info.radio_whole_list
  print info.radio_list
  return

def IncrementalOTA_VerifyEnd(info):
  info.script.Mount("/sys_boot")
  for fn, tf, sf, size, patch_sha in info.radio_list:
    info.script.PatchCheck("/"+fn, tf.sha1, sf.sha1)
  return

def AddBootloaderAssertion(info, input_zip):
  android_info = input_zip.read("OTA/android-info.txt")
  m = re.search(r"require\s+version-bootloader\s*=\s*(\S+)", android_info)
  if m:
    bootloaders = m.group(1).split("|")
    if "*" not in bootloaders:
      info.script.AssertSomeBootloader(*bootloaders)
    info.metadata["pre-bootloader"] = m.group(1)

def CheckRadiotarget(info, mount_point):
    fstab = info.script.info.get("fstab", None)
    if fstab:
      p = fstab[mount_point]
      info.script.AppendExtra('assert(qcom.set_radio("%s"));' %
                         (p.fs_type))

# path: defination file path in output zip
# data: Amss file data
# Assuming the file is extracted to /sys_boot/image
def InstallAmss(path, info, data):
  start = path.rfind("/")
  fn = path[start:]
  info.script.AppendExtra('package_extract_file("%s", "/sys_boot/image/%s");' %(path, fn))
  radio_img = data
  common.ZipWriteStr(info.output_zip, path, radio_img)
  info.script.FileCheck("/sys_boot/image/%s" % fn , sha1(radio_img).hexdigest())
  return

# Full update radio files
# Path: path in input zip
def InstallRadio(path, info):
  print "Installing radio file:" + path
  start = path.rfind("/")
  end = path.rfind(".")
  mount_point = path[start:end]
# Path in output zip
  dest_path = path[start+1:]


  if mount_point.startswith("/AMSS"):
    print "AMSS found:" + path
    #AMSS full image is written into sys_boot/image
    dest_path = "sys_boot/image/" + dest_path
    InstallAmss(dest_path, info, info.input_zip.read(path))
    return
  fstab = info.script.info.get("fstab", None)

  if mount_point not in fstab:
    return

  info.script.Print("Writing %s" % dest_path)
  info.script.WriteRawImage(mount_point, dest_path);
  radio_img = info.input_zip.read(path)
  img_size = len(radio_img)
  print dest_path + " img_size:" + str(img_size)

  info.script.VerifyPartition("EMMC:" + fstab[mount_point].device + ":" + str(len(radio_img)) + ":" + sha1(radio_img).hexdigest())
  common.ZipWriteStr(info.output_zip, dest_path, radio_img)


def InstallRadioOld(radio_img, api_version, input_zip, fn, info):
  fn2 = fn[6:]
  fn3 = "/sdcard/radio/" + fn2
  common.ZipWriteStr(info.output_zip, fn2, radio_img)

  if api_version >= 3:
    if (fn2.endswith("ENC") or fn2.endswith("enc")):
        info.script.AppendExtra(('''
assert(package_extract_file("%s", "%s"));
''' %(fn2,fn3) % locals()).lstrip())
        common.ZipWriteStr(info.output_zip, fn2, radio_img)
    else:
        fstab = info.script.info.get("fstab", None)
        if fn2 not in fstab:
            return
        info.script.WriteRawImage(fn2, fn2);
        common.ZipWriteStr(info.output_zip, fn2, radio_img)
        return
  elif info.input_version >= 2:
    info.script.AppendExtra(
        'write_firmware_image("PACKAGE:radio.img", "radio");')
    common.ZipWriteStr(info.output_zip, fn2, radio_img)
  else:
    info.script.AppendExtra(
        ('assert(package_extract_file("radio.img", "/tmp/radio.img"),\n'
         '       write_firmware_image("/tmp/radio.img", "radio"));\n'))
    common.ZipWriteStr(info.output_zip, fn2, radio_img)


def FullOTA_InstallEnd(info):
  files = GetRadioFiles(info.input_zip)
  if files == {}:
    print "warning sha: no radio image in input target_files; not flashing radio"
    return

  enc_file = "false";

  info.script.Print("Writing radio image...")
  info.script.Mount("/sys_boot")
  for f in files:
    if (f.endswith("ENC") or f.endswith("enc")):
      radio_img = info.input_zip.read(f)
      InstallRadioOld(radio_img, info.input_version, info.input_zip, f, info)
      enc_file = "true"
    if (f.endswith("bin") or f.endswith("BIN") or f.endswith("mbn") or f.endswith("MBN")):
      InstallRadio(f, info)
  info.script.UnmountAll()
  if (enc_file == "true"):
    CheckRadiotarget(info, "/recovery")
  return



def IncrementalOTA_InstallEnd(info):
  #TODO: Implement device specific asserstions.
  print "begin radio-update: IncrementalOTA_InstallEnd."
  info.script.Print("Patching radio files...")
  for item in info.radio_list:
    fn, tf, sf, size, _ = item
    info.script.ApplyPatch("/"+fn, "-", tf.size, tf.sha1, sf.sha1, "patch/"+fn+".p")

  print "Whole radio list:"
  print info.radio_whole_list
  for item in info.radio_whole_list:
    fn, tf, sf, tsize, tsha1 = item

    # Get the basename
    start = fn.rfind("/")
    end = fn.rfind(".")
    if start < 0 :
      mount_point = "/" + fn[0:end]
    else:
      mount_point = fn[start:end]
    # This happends when the file is in the root directory
    fstab = info.script.info.get("fstab", None)
    if mount_point in fstab:
      print fn + " found in fstab"
      info.script.Print("Writing %s" % fn)
      info.script.WriteRawImage(mount_point, fn);
      info.script.VerifyPartition("EMMC:" + fstab[mount_point].device + ":" + str(tsize) + ":" + tsha1)
    elif mount_point.startswith("/AMSS"):
      print fn + " is an AMSS file"
      InstallAmss(fn, info, tf.data)
  return

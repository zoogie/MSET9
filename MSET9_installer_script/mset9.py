#!/usr/bin/python3
import abc, os, platform, time, binascii

VERSION = "v1.2c"

def prgood(content):
	print(f"[\033[0;32m✓\033[0m] {content}")

def prbad(content):
	print(f"[\033[0;91mX\033[0m] {content}")

def prinfo(content):
	print(f"[*] {content}")

def cleanup(remount=False):
	pass

def exitOnEnter(errCode = 0, remount=False):
	cleanup(remount)
	input("[*] Press Enter to exit...")
	exit(errCode)

# wrapper for fs operations. can use pyfilesystem2 directly,
# but try to avoid extra dependency on non-darwin system
class FSWrapper(metaclass=abc.ABCMeta):
	@abc.abstractmethod
	def exists(self, path):
		pass
	@abc.abstractmethod
	def mkdir(self, path):
		pass
	@abc.abstractmethod
	def open(self, path, mode='r'):
		pass
	@abc.abstractmethod
	def getsize(self, path):
		pass
	@abc.abstractmethod
	def remove(self, path):
		pass
	@abc.abstractmethod
	def rename(self, src, dst):
		pass
	@abc.abstractmethod
	def rmtree(self, path):
		pass
	@abc.abstractmethod
	def copytree(self, src, dst):
		pass
	@abc.abstractmethod
	def walk(self, path, topdown=False):
		pass
	@abc.abstractmethod
	def is_writable(self):
		pass
	@abc.abstractmethod
	def ensurespace(self, size):
		pass
	@abc.abstractmethod
	def close(self):
		pass
	@abc.abstractmethod
	def reload(self):
		pass
	@abc.abstractmethod
	def print_root(self):
		pass

def remove_extra():
	pass

osver = platform.system()
thisfile = os.path.abspath(__file__)
systmp = None

if osver == "Darwin":
	# ======== macOS / iOS? ========
	import sys

	tmpprefix = "mset9-macos-run-"

	def is_ios():
		machine = os.uname().machine
		return any(machine.startswith(e) for e in ["iPhone", "iPad"])

	def tmp_cleanup():
		global tmpprefix, systmp
		prinfo("Removing temporary folders...")
		import tempfile, shutil
		if systmp is None:
			systmp = tempfile.gettempdir()
		for dirname in os.listdir(systmp):
			if dirname.startswith(tmpprefix):
				shutil.rmtree(f"{systmp}/{dirname}")
		prinfo("Temporary folders removed!")

	def run_diskutil_and_wait(command, dev):
		import subprocess
		if type(command) != list:
			command = [command]
		return subprocess.run(["diskutil", *command, dev], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode

	if len(sys.argv) < 2:
		if not thisfile.startswith("/Volumes/"):
			prbad("Error 01: Couldn't find Nintendo 3DS folder! Ensure that you are running this script from the root of the SD card.")
			# should we add some macos specific message?
			exitOnEnter()
		prinfo("Resolving device...")
		device = None
		devid = os.stat(thisfile).st_dev
		for devname in os.listdir("/dev"):
			if not devname.startswith("disk"):
				continue
			devpath = f"/dev/{devname}"
			if os.stat(devpath).st_rdev == devid:
				device = devpath
				break
		if device is None:
			#prbad("Error :")
			prbad("Can't find matching device, this shouldn't happen...")
			exitOnEnter()

		prinfo("Finding previous temporary folder...")
		import shutil, tempfile, time
		systmp = tempfile.gettempdir()
		tmpdir = None
		for dirname in os.listdir(systmp):
			if dirname.startswith(tmpprefix):
				dirpath = f"{systmp}/{dirname}"
				script = f"{dirpath}/mset9.py"
				if os.path.exists(script) and os.stat(script).st_mtime > os.stat(thisfile).st_mtime:
					tmpdir = dirpath
					break
				else:
					shutil.rmtree(dirpath)
		if tmpdir is None:
			prinfo("Creating temporary folder...")
			tmpdir = tempfile.mkdtemp(prefix=tmpprefix)
			shutil.copyfile(thisfile, f"{tmpdir}/mset9.py")

		prinfo("Trying to unmount SD card...")
		ret = run_diskutil_and_wait(["umount", "force"], device)

		if ret == 1:
			prbad("Error 16: Unable to unmount SD card.")
			prinfo("Please ensure there's no other app using your SD card.")
			#tmp_cleanup()
			exitOnEnter()

		os.execlp(sys.executable, sys.executable, f"{tmpdir}/mset9.py", device)
		prbad("WTF???")

	device = sys.argv[1]
	if len(sys.argv) == 3:
		systmp = sys.argv[2]
	if not os.path.exists(device):
		prbad("Error 13: Device doesn't exist.")
		prinfo("Ensure your SD card is inserted properly.")
		prinfo("Also, don't eject SD card itself in disk utility, unmount the partition only.")
		#tmp_cleanup()
		exitOnEnter()

	# auto venv
	venv_path = os.path.dirname(thisfile)
	venv_bin = f"{venv_path}/bin"
	venv_py = f"{venv_bin}/python3"

	def check_ios_py_entitlement(path):
		import subprocess
		import xml.etree.ElementTree as ET
		try:
			result = subprocess.run(["ldid", "-e", path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
			if result.returncode != 0:
				prbad("Error #: Fail to check venv python ios entitlement")
				prinfo(f"ldid error (ret={result.returncode})")
				tmp_cleanup()
				exitOnEnter()
				#return False
			tree = ET.fromstring(result.stdout)
			result = 0  # 0: not found    1: wait key
			for child in tree.find("./dict"):
				if child.tag == "key" and child.text == "com.apple.private.security.disk-device-access":
					result = 1
				elif result == 0:
					if child.tag == "true":
						result = True
						break
					elif child.tag == "false":
						result = False
						break
					else:
						result = 0  # not valid, reset

			if result == 0 or result == 1:
				return False

			return result

		except FileNotFoundError:
			return None

	def fix_ios_py_entitlement(path):
		import subprocess

		basepath = os.path.dirname(path)

		if os.path.islink(path):
			import shutil
			realpy = os.path.join(basepath, os.readlink(path))
			os.remove(path)
			shutil.copyfile(realpy, path)
			shutil.copymode(realpy, path)

		entaddxml = os.path.join(basepath, "entadd.xml")
		with open(entaddxml, "w") as f:
			f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
			f.write('<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n')
			f.write('<plist version="1.0">\n')
			f.write('<dict>\n')
			f.write('\t<key>com.apple.private.security.disk-device-access</key>\n')
			f.write('\t<true/>\n')
			f.write('</dict>\n')
			f.write('</plist>\n')

		try:
			args = ["ldid", "-M", f"-S{entaddxml}", path]
			result = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
			if result.returncode != 0:
				prbad("Error #: Fail to modify venv python ios entitlement")
				prinfo(f"ldid ret={result.returncode}")
				prinfo("Message:")
				prinfo(result.stderr)

		except FileNotFoundError:
			prbad("Error #: Fail to modify venv python ios entitlement")
			prinfo("wtf? ldid disappeared?")
			tmp_cleanup()
			exitOnEnter()

	def activate_venv():
		global venv_path, venv_bin, venv_py, device, systmp
		import site

		# assuming it's fine if ldid doesn't exist
		if is_ios() and check_ios_py_entitlement(venv_py) == False:
			prinfo("fixing entitlement...")
			fix_ios_py_entitlement(venv_py)

		os.environ["PATH"] = os.pathsep.join([venv_bin, *os.environ.get("PATH", "").split(os.pathsep)])
		os.environ["VIRTUAL_ENV"] = venv_path
		os.environ["VIRTUAL_ENV_PROMPT"] = "(mset9)"

		#if systmp is None:
		#	os.execlp(py_exec, venv_py, __file__, device)
		#else:
		#	os.execlp(py_exec, venv_py, __file__, device, systmp)

		prev_length = len(sys.path)
		ver = sys.version_info
		ver_path = f"python{ver.major}.{ver.minor}"
		path = os.path.realpath(os.path.join(venv_path, "lib", ver_path, "site-packages"))
		site.addsitedir(path)
		sys.path[:] = sys.path[prev_length:] + sys.path[0:prev_length]
		sys.real_prefix = sys.prefix
		sys.prefix = venv_path

	def setup_venv():
		import venv, subprocess
		if "VIRTUAL_ENV" not in os.environ:
			if os.path.exists(venv_bin):
				import shutil
				shutil.rmtree(venv_bin)
			venv.create(venv_path, with_pip=True)
		subprocess.run([venv_py, "-mensurepip"], cwd=venv_path)
		subprocess.run([venv_py, "-mpip", "install", "pyfatfs"], cwd=venv_path)
		activate_venv()

	if "VIRTUAL_ENV" not in os.environ:
		if os.path.exists(venv_py):
			prinfo("venv found, activate it...")
			activate_venv()
		elif is_ios():
			have_perm = check_ios_py_entitlement(sys.executable)
			if have_perm == None:
				prinfo("ldid not found, assume your python have proper entitlement")
				prinfo("if fail later, please install ldid or fix your python manually")
				prinfo("(require entitlement com.apple.private.security.disk-device-access)")
			elif not have_perm:
				prinfo("need entitlement fix, setting up venv for fixing automatically...")
				setup_venv()

	try:
		from pyfatfs.PyFatFS import PyFatFS
	except ModuleNotFoundError:
		prinfo("PyFatFS not found, setting up venv for installing automatically...")
		setup_venv()
		from pyfatfs.PyFatFS import PyFatFS

	# self elevate
	if os.getuid() != 0:
		# run with osascript won't have raw disk access by default...
		# thanks for the perfect security of macos
		#args = [sys.executable, thisfile, device]
		#escaped_args = map(lambda x: f"\\\"{x}\\\"", args)
		#cmd = " ".join(escaped_args)
		#osascript = " ".join([
		#	f"do shell script \"{cmd}\"",
		#	"with administrator privileges",
		#	"without altering line endings"
		#])
		#try:
		#	os.execlp("osascript", "osascript", "-e", osascript)
		prinfo("Input the password of your computer if prompted.")
		prinfo("(It won't show anything while you're typing, just type it blindly)")
		try:
			import tempfile
			os.execlp("sudo", "sudo", sys.executable, thisfile, device, tempfile.gettempdir())
		except:
			prbad("Error 17: Root privilege is required.")
			#tmp_cleanup()
			exitOnEnter(remount=True)

	from pyfatfs.PyFatFS import PyFatFS
	from pyfatfs.FATDirectoryEntry import FATDirectoryEntry, make_lfn_entry
	from pyfatfs.EightDotThree import EightDotThree
	from pyfatfs._exceptions import PyFATException, NotAnLFNEntryException
	import struct, errno

	def _search_entry(self, name):
		name = name.upper()
		dirs, files, _ = self.get_entries()
		for entry in dirs+files:
			try:
				if entry.get_long_name().upper() == name:
					return entry
			except NotAnLFNEntryException:
				pass
			if entry.get_short_name() == name:
				return entry

		raise PyFATException(f'Cannot find entry {name}',
							 errno=errno.ENOENT)
	FATDirectoryEntry._search_entry = _search_entry

	def make_8dot3_name(dir_name, parent_dir_entry):
		dirs, files, _ = parent_dir_entry.get_entries()
		dir_entries = [e.get_short_name() for e in dirs + files]
		extsep = "."
		def map_chars(name: bytes) -> bytes:
			_name: bytes = b''
			for b in struct.unpack(f"{len(name)}c", name):
				if b == b' ':
					_name += b''
				elif ord(b) in EightDotThree.INVALID_CHARACTERS:
					_name += b'_'
				else:
					_name += b
			return _name
		dir_name = dir_name.upper()
		# Shorten to 8 chars; strip invalid characters
		basename = os.path.splitext(dir_name)[0][0:8].strip()
		if basename.isascii():
			basename = basename.encode("ascii", errors="replace")
			basename = map_chars(basename).decode("ascii")
		else:
			basename = "HAX8D3FN"
		# Shorten to 3 chars; strip invalid characters
		extname = os.path.splitext(dir_name)[1][1:4].strip()
		if basename.isascii():
			extname = extname.encode("ascii", errors="replace")
			extname = map_chars(extname).decode("ascii")
		elif len(extname) != 0:
			extname = "HAX"
		if len(extname) == 0:
			extsep = ""
		# Loop until suiting name is found
		i = 0
		while len(str(i)) + 1 <= 7:
			if i > 0:
				maxlen = 8 - (1 + len(str(i)))
				basename = f"{basename[0:maxlen]}~{i}"
			short_name = f"{basename}{extsep}{extname}"
			if short_name not in dir_entries:
				return short_name
			i += 1
		raise PyFATException("Cannot generate 8dot3 filename, "
							 "unable to find suiting short file name.",
							 errno=errno.EEXIST)
	EightDotThree.make_8dot3_name = staticmethod(make_8dot3_name)

	class FatFS(FSWrapper):
		def __init__(self, device):
			self.device = device
			self.reload()
		def exists(self, path):
			return self.fs.exists(path)
		def mkdir(self, path):
			self.fs.makedir(path)
		def open(self, path, mode='r'):
			return self.fs.open(path, mode)
		def getsize(self, path):
			return self.fs.getsize(path)
		def remove(self, path):
			self.fs.remove(path)
		def rename(self, src, dst):
			srcdir, srcname = f"/{src}".rstrip("/").rsplit("/", 1)
			dstdir, dstname = f"/{dst}".rstrip("/").rsplit("/", 1)
			if srcdir == dstdir and all(not EightDotThree.is_8dot3_conform(n) for n in [srcname, dstname]):
				# cursed rename, lfn and same folder only
				pdentry = self.fs._get_dir_entry(srcdir)
				dentry = pdentry._search_entry(srcname)
				lfn_entry = make_lfn_entry(dstname, dentry.name)
				dentry.set_lfn_entry(lfn_entry)
				self.fs.fs.update_directory_entry(pdentry)
				self.fs.fs.flush_fat()
			elif self.fs.getinfo(src).is_dir:
				self.fs.movedir(src, dst, create=True)
			else:
				self.fs.move(src, dst, create=True)
		def rmtree(self, path):
			self.fs.removetree(path)
		def copytree(self, src, dst):
			self.fs.copydir(src, dst, create=True)
		def walk(self, path, topdown=False):  # topdown is ignored
			for dir_path, dirs, files in self.fs.walk(path):
				yield dir_path, list(map(lambda x: x.name, dirs)), list(map(lambda x: x.name, files))
		def is_writable(self):
			try:
				with self.open("test.txt", "w") as f:
					f.write("test")
					f.close()
				self.remove("test.txt")
				return True
			except:
				return False
		def ensurespace(self, size):
			try:
				first = self.fs.fs.allocate_bytes(size)[0]
				self.fs.fs.free_cluster_chain(first)
				return True
			except PyFATException:
				return False
		def close(self):
			try:
				self.fs.close()
			except AttributeError:
				pass
		def reload(self):
			self.close()
			self.fs = PyFatFS(filename=self.device)
		def print_root(self):
			pass

	try:
		fs = FatFS(device)
	except PyFATException as e:
		msg = str(e)
		if "Cannot open" in msg:
			prbad("Error 14: Can't open device.")
			prinfo("Please ensure your SD card is unmounted in disk utility.")
			if is_ios():
				prinfo("might also be ios entitlement issue")
				prinfo("please install ldid or fix your python manually")
				prinfo("(require entitlement com.apple.private.security.disk-device-access)")
		elif "Invalid" in msg:
			prbad("Error 15: Not FAT32 formatted or corrupted filesystem.")
			prinfo("Please ensure your SD card is properly formatted")
			prinfo("Consult: https://wiki.hacks.guide/wiki/Formatting_an_SD_card")
		#tmp_cleanup()
		exitOnEnter()

	def remove_extra():
		tmp_cleanup()

	def cleanup(remount=False):
		global fs, device
		fs.close()
		if remount and not is_ios():
			prinfo("Trying to remount SD card...")
			run_diskutil_and_wait("mount", device)
		#tmp_cleanup()


else:
	# ======== Windows / Linux ========
	import shutil

	class OSFS(FSWrapper):
		def __init__(self, root):
			self.root = root
			self.reload()
		def abs(self, path):
			return os.path.join(self.root, path)
		def exists(self, path):
			return os.path.exists(self.abs(path))
		def mkdir(self, path):
			os.mkdir(self.abs(path))
		def open(self, path, mode='r'):
			return open(self.abs(path), mode)
		def getsize(self, path):
			return os.path.getsize(self.abs(path))
		def remove(self, path):
			os.remove(self.abs(path))
		def rename(self, src, dst):
			os.rename(self.abs(src), self.abs(dst))
		def rmtree(self, path):
			shutil.rmtree(self.abs(path))
		def copytree(self, src, dst):
			shutil.copytree(self.abs(src), self.abs(dst))
		def walk(self, path, topdown=False):
			return os.walk(self.abs(path), topdown=topdown)
		def is_writable(self):
			writable = os.access(self.root, os.W_OK)
			try: # Bodge for windows
				with open("test.txt", "w") as f:
					f.write("test")
					f.close()
				os.remove("test.txt")
			except:
				writable = False
			return writable
		def ensurespace(self, size):
			return shutil.disk_usage(self.root).free >= size
		def close(self):
			pass
		def reload(self):
			try:
				os.chdir(self.root)
			except Exception:
				prbad("Error 09: Couldn't reapply working directory, is SD card reinserted?")
				exitOnEnter()
		def print_root(self):
			prinfo(f"Current dir: {self.root}")


	fs = OSFS(os.path.dirname(thisfile))

def clearScreen():
	if osver == "Windows":
		os.system("cls")
	else:
		os.system("clear")

# Section: insureRoot
if not fs.exists("Nintendo 3DS/"):
	prbad("Error 01: Couldn't find Nintendo 3DS folder! Ensure that you are running this script from the root of the SD card.")
	prbad("If that doesn't work, eject the SD card, and put it back in your console. Turn it on and off again, then rerun this script.")
	fs.print_root()
	exitOnEnter()

# Section: sdWritable
def writeProtectCheck():
	global fs
	prinfo("Checking if SD card is writeable...")
	if not fs.is_writable():
		prbad("Error 02: Your SD card is write protected! If using a full size SD card, ensure that the lock switch is facing upwards.")
		prinfo("Visual aid: https://nintendohomebrew.com/assets/img/nhmemes/sdlock.png")
		exitOnEnter()
	else:
		prgood("SD card is writeable!")

# Section: SD card free space
# ensure 16MB free space
if not fs.ensurespace(16777216):
	prbad(f"Error 06: You need at least 16MB free space on your SD card, you have {(freeSpace / 1000000):.2f} bytes!")
	prinfo("Please free up some space and try again.")
	exitOnEnter()

clearScreen()
print(f"MSET9 {VERSION} SETUP by zoogie, Aven and DannyAAM")
print("What is your console model and version?")
print("Old 3DS has two shoulder buttons (L and R)")
print("New 3DS has four shoulder buttons (L, R, ZL, ZR)")
print("\n-- Please type in a number then hit return --\n")
print("Enter one of these four numbers!")
print("Enter 1 for: Old 3DS, 11.8.0 to 11.17.0")
print("Enter 2 for: New 3DS, 11.8.0 to 11.17.0")
print("Enter 3 for: Old 3DS, 11.4.0 to 11.7.0")
print("Enter 4 for: New 3DS, 11.4.0 to 11.7.0")

encodedId1s = {
	1: "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A0871A0050899CE0408730064006D00630000900A0862003900",
	2: "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A0871A005085DCE0408730064006D00630000900A0862003900",
	3: "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A08499E050899CC0408730064006D00630000900A0862003900",
	4: "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A08459E050881CC0408730064006D00630000900A0862003900"
}
hackedId1Encoded, consoleModel, consoleFirmware = "", "", ""
while 1:
	try:
		sysModelVerSelect = input(">>> ")
		if sysModelVerSelect.startswith("11"):
			prbad("Don't type the firmware version, just the selection number!")
			sysModelVerSelect = 42
		sysModelVerSelect = int(sysModelVerSelect)
	except KeyboardInterrupt:
		print()
		prgood("Goodbye!")
		exitOnEnter(remount=True)
	except:
		sysModelVerSelect = 42
	if sysModelVerSelect == 1:
		hackedId1Encoded = encodedId1s[1]
		consoleModel = "OLD3DS"
		consoleFirmware = "11.8-11.17"
		break

	if sysModelVerSelect == 2:
		hackedId1Encoded = encodedId1s[2]
		consoleModel = "NEW3DS"
		consoleFirmware = "11.8-11.17"
		break

	if sysModelVerSelect == 3:
		hackedId1Encoded = encodedId1s[3]
		consoleModel = "OLD3DS"
		consoleFirmware = "11.4-11.7"
		break

	if sysModelVerSelect == 4:
		hackedId1Encoded = encodedId1s[4]
		consoleModel = "NEW3DS"
		consoleFirmware = "11.4-11.7"
		break

	else:
		prbad("Invalid input, try again. Valid inputs: 1, 2, 3, 4")

trigger = "002F003A.txt"  # all 3ds ":/" in hex
hackedId1 = bytes.fromhex(hackedId1Encoded).decode("utf-16le")  # ID1 - arm injected payload in readable format
id1 = ""
id0 = ""
realId1Path = ""

extdataRoot = ""
realId1BackupTag = "_user-id1"
id0Count = 0
id1Count = 0
id0List = []

homeMenuExtdata = [0x8F, 0x98, 0x82, 0xA1, 0xA9, 0xB1]  # us,eu,jp,ch,kr,tw
miiMakerExtdata = [0x217, 0x227, 0x207, 0x267, 0x277, 0x287]  # us,eu,jp,ch,kr,tw

# make a table so we can print regions based on what hex code from the above is found
regionTable = {
	0x8F: "USA Region",
	0x98: "EUR Region",
	0x82: "JPN Region",
	0xA1: "CHN Region",
	0xA9: "KOR Region",
	0xB1: "TWN Region"
}				

homeDataPath, miiDataPath, homeHex, miiHex = "", "", 0x0, 0x0
def sanity():
	global fs, haxState, realId1Path, id0, id1, homeDataPath, miiDataPath, homeHex, miiHex
	menuExtdataGood = False
	miiExtdataGood = False

	print()
	prinfo("Performing sanity checks...")

	writeProtectCheck()

	prinfo("Ensuring extracted files exist...")
	fileSanity = 0
	fileSanity += softcheck("boot9strap/boot9strap.firm", 0, 0x08129C1F, 1)
	fileSanity += softcheck("boot.firm", retval = 1)
	fileSanity += softcheck("boot.3dsx", retval = 1)
	fileSanity += softcheck("b9", retval = 1)
	fileSanity += softcheck("SafeB9S.bin", retval = 1)
	if fileSanity > 0:
		prbad("Error 08: One or more files are missing or malformed!")
		prinfo("Please re-extract the MSET9 zip file, overwriting any existing files when prompted.")
		exitOnEnter()
	prgood("All files look good!")

	prinfo("Checking databases...")
	checkTitledb = softcheck(realId1Path + "/dbs/title.db", 0x31E400, 0, 1)
	checkImportdb = softcheck(realId1Path + "/dbs/import.db", 0x31E400, 0, 1)
	if checkTitledb or checkImportdb:
		prbad("Error 10: Database(s) malformed or missing!")
		if not (
			fs.exists(realId1Path + "/dbs/import.db")
			or fs.exists(realId1Path + "/dbs/title.db")
		):
			if not fs.exists(realId1Path + "/dbs"):
				fs.mkdir(realId1Path + "/dbs")
			if checkTitledb:
				fs.open(realId1Path + "/dbs/title.db", "x").close()
			if checkImportdb:
				fs.open(realId1Path + "/dbs/import.db", "x").close()

			prinfo("Created empty databases.")
		prinfo("Please initialize the title database by navigating to System Settings -> Data Management -> Nintendo 3DS -> Software -> Reset, then rerun this script.")
		prinfo("Visual guide: https://3ds.hacks.guide/images/screenshots/database-reset.jpg")
		exitOnEnter()
	else:
		prgood("Databases look good!")
	
	if fs.exists(realId1Path + "/extdata/" + trigger):
		prinfo("Removing stale trigger...")
		fs.remove(realId1Path + "/extdata/" + trigger)
	
	extdataRoot = realId1Path + "/extdata/00000000"

	prinfo("Checking for HOME Menu extdata...")
	for i in homeMenuExtdata:
		extdataRegionCheck = extdataRoot + f"/{i:08X}"
		if fs.exists(extdataRegionCheck):
			prgood(f"Detected {regionTable[i]} HOME Menu data!")
			homeHex = i
			homeDataPath = extdataRegionCheck
			menuExtdataGood = True
			break
	
	if not menuExtdataGood:
		prbad("Error 04: No HOME Menu data!")
		prinfo("Your SD is not formatted properly, or isn't being read by the console.")
		prinfo("Please go to https://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9 for instructions.")
		prinfo("If you need help, join Nintendo Homebrew on Discord: https://discord.gg/nintendohomebrew")
		exitOnEnter()
	
	prinfo("Checking for Mii Maker extdata...")
	for i in miiMakerExtdata:
		extdataRegionCheck = extdataRoot + f"/{i:08X}"
		if fs.exists(extdataRegionCheck):
			prgood("Found Mii Maker data!")
			miiHex = i
			miiDataPath = extdataRegionCheck
			miiExtdataGood = True
			break
	
	if not miiExtdataGood:
		prbad("Error 05: No Mii Maker data!")
		prinfo("Please go to https://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9 for instructions.")
		exitOnEnter()

def injection():
	global fs, realId1Path, id1

	if not fs.exists(id0 + "/" + hackedId1):
		prinfo("Creating hacked ID1...")
		hackedId1Path = id0 + "/" + hackedId1
		fs.mkdir(hackedId1Path)
		fs.mkdir(hackedId1Path + "/extdata")
		fs.mkdir(hackedId1Path + "/extdata/00000000")
	else:
		prinfo("Reusing existing hacked ID1...")
		hackedId1Path = id0 + "/" + hackedId1

	if not fs.exists(hackedId1Path + "/dbs"):
		prinfo("Copying databases to hacked ID1...")
		fs.copytree(realId1Path + "/dbs", hackedId1Path + "/dbs")

	prinfo("Copying extdata to hacked ID1...")
	if not fs.exists(hackedId1Path + f"/extdata/00000000/{homeHex:08X}"):
		fs.copytree(homeDataPath, hackedId1Path + f"/extdata/00000000/{homeHex:08X}")
	if not fs.exists(hackedId1Path + f"/extdata/00000000/{miiHex:08X}"):
		fs.copytree(miiDataPath, hackedId1Path + f"/extdata/00000000/{miiHex:08X}")

	prinfo("Injecting trigger file...")
	triggerFilePath = id0 + "/" + hackedId1 + "/extdata/" + trigger
	if not fs.exists(triggerFilePath):
		with fs.open(triggerFilePath, "w") as f:
			f.write("plz be haxxed mister arm9, thx")
			f.close()
	
	if fs.exists(realId1Path) and realId1BackupTag not in realId1Path:
		prinfo("Backing up real ID1...")
		fs.rename(realId1Path, realId1Path + realId1BackupTag)
		id1 += realId1BackupTag
		realId1Path = f"{id0}/{id1}"
	else:
		prinfo("Skipping backup because a backup already exists!")


	prgood("MSET9 successfully injected!")

def remove():
	global fs, realId1Path, id0, id1
	prinfo("Removing MSET9...")

	if fs.exists(realId1Path) and realId1BackupTag in realId1Path:
		prinfo("Renaming original Id1...")
		fs.rename(realId1Path, id0 + "/" + id1[:32])
	else: 
		prgood("Nothing to remove!")
		return
	
	# print(id1_path, id1_root+"/"+id1[:32])
	for id1Index in range(1,5): # Attempt to remove *all* hacked id1s
		maybeHackedId = bytes.fromhex(encodedId1s[id1Index]).decode("utf-16le")
		if fs.exists(id0 + "/" + maybeHackedId):
			prinfo("Deleting hacked ID1...")
			fs.rmtree(id0 + "/" + maybeHackedId)
	id1 = id1[:32]
	realId1Path = id0 + "/" + id1
	prgood("Successfully removed MSET9!")

def softcheck(keyfile, expectedSize = None, crc32 = None, retval = 0):
	global fs
	filename = keyfile.rsplit("/")[-1]
	if not fs.exists(keyfile):
		prbad(f"{filename} does not exist on SD card!")
		return retval
	if expectedSize:
		fileSize = fs.getsize(keyfile)
		if expectedSize != fileSize:
			prbad(f"{filename} is size {fileSize:,} bytes, not expected {expectedSize:,} bytes")
			return retval
	elif crc32:
		with fs.open(keyfile, "rb") as f:
			checksum = binascii.crc32(f.read())
			if crc32 != checksum:
				prbad(f"{filename} was not recognized as the correct file")
				f.close()
				return retval
			f.close()
	prgood(f"{filename} looks good!")
	return 0

# Section: sdwalk
for root, dirs, files in fs.walk("Nintendo 3DS/", topdown=True):

	for name in dirs:
		# If the name doesn't contain sdmc (Ignores MSET9 exploit folder)
		if "sdmc" not in name and len(name[:32]) == 32:
			try:
				# Check to see if the file name encodes as an int (is hex only)
				hexVerify = int(name[:32], 16)
			except:
				continue
			if type(hexVerify) is int:
				# Check if the folder (which is either id1 or id0) has the extdata folder
				# if it does, it's an id1 folder
				if fs.exists(os.path.join(root, name) + "/extdata"):
					id1Count += 1
					id1 = name
					id0 = root
					realId1Path = os.path.join(root, name)

				# Otherwise, add it to the id0 list because we need to make sure we only have one id0
				else:
					if len(name) == 32:
						id0Count += 1
						id0List.append(os.path.join(root, name))

	for name in dirs: # Run the check for existing install after figuring out the structure
		# Check if we have an MSET9 Hacked id1 folder
		if "sdmc" in name and len(name) == 32:
		# If the MSET9 folder doesn't match the proper haxid1 for the selected console version
			if hackedId1 != name:
				prbad("Error 03: Don't change console model/version in the middle of MSET9!")
				prbad("Please restart the setup.")
				remove()
				exitOnEnter()


prinfo("Detected ID0(s):")
for i in id0List:
	prinfo(i)
print()
if id0Count != 1:
	prbad(f"Error 07: You don't have 1 ID0 in your Nintendo 3DS folder, you have {id0Count}!")
	prinfo("Consult: https://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9 for help!")
	exitOnEnter()

if id1Count != 1:
	prbad(f"Error 12: You don't have 1 ID1 in your Nintendo 3DS folder, you have {id1Count}!")
	prinfo("Consult: https://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9 for help!")
	exitOnEnter()

clearScreen()
print(f"MSET9 {VERSION} SETUP by zoogie, Aven and DannyAAM")
print(f"Using {consoleModel} {consoleFirmware}")

print("\n-- Please type in a number then hit return --\n")
print("↓ Input one of these numbers!")
print("1. Perform sanity checks")
print("2. Inject MSET9 payload")
print("3. Remove MSET9")
print("4. Exit")

while 1:
	try:
		sysModelVerSelect = int(input(">>> "))
	except KeyboardInterrupt:
		sysModelVerSelect = 4 # exit on Ctrl+C
		print()
	except:
		sysModelVerSelect = 42

	fs.reload()

	if sysModelVerSelect == 1:
		sanity()
		prgood("Everything appears to be functional!\n")
		exitOnEnter()
	elif sysModelVerSelect == 2:
		sanity()
		injection()
		exitOnEnter()
	elif sysModelVerSelect == 3:
		remove()
		remove_extra()
		exitOnEnter(remount=True)
	elif sysModelVerSelect == 4 or "exit":
		break
	else:
		prinfo("Invalid input, try again. Valid inputs: 1, 2, 3, 4")

cleanup(remount=True)
prgood("Goodbye!")
time.sleep(2)

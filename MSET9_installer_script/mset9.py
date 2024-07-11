#!/usr/bin/python3
import abc, sys, os, platform, time, pathlib, binascii

VERSION = "v1.2c"

def prgood(content):
	# print(f"[\033[0;32m✓\033[0m] {content}")
	# so that people aren't confused by the [?]. stupid Windows.
	print(f"[\033[0;32mOK\033[0m] {content}")

def prbad(content):
	print(f"[\033[0;91mXX\033[0m] {content}")

def prinfo(content):
	print(f"[--] {content}")

def cleanup(remount=False):
	pass

def exitOnEnter(errCode = 0, remount=False):
	cleanup(remount)
	input("[--] Press Enter to exit...")
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
scriptroot = os.path.dirname(thisfile)
systmp = None

systemroot = pathlib.Path(sys.executable).anchor # Never hardcode C:. My Windows drive letter is E:, my SD card or USB drive is often C:.
if os.stat(scriptroot).st_dev == os.stat(systemroot).st_dev:
	prbad("Error 01: Script is not running on your SD card!")
	prinfo(f"Current location: {scriptroot}")
	exitOnEnter()

def dig_for_root():
	import shutil
	global thisfile, scriptroot

	if not os.path.ismount(scriptroot):
		root = scriptroot
		while not os.path.ismount(root) and root != os.path.dirname(root):
			root = os.path.dirname(root)

		for f in ["SafeB9S.bin", "b9", "boot.firm", "boot.3dsx", "boot9strap/", "mset9.py", "mset9.bat", "mset9.command", "_INSTRUCTIONS.txt", "errors.txt"]:
			try:
				shutil.move(os.path.join(scriptroot, f), os.path.join(root, f))
			except:
				pass # The sanity checks will deal with that. I just don't want the exception to terminate the script.

		with open(os.path.join(scriptroot, "Note from MSET9.txt"), "w") as f:
			f.write("Hey!\n")
			f.write("All the MSET9 files have been moved to the root of your SD card.\n\n")

			f.write("\"What is the 'root of my SD card'...?\"\n")
			f.write("The root is 'not inside any folder'.\n")
			f.write("This is where you can see your 'Nintendo 3DS' folder. (It is not inside the Nintendo 3DS folder itself!)\n\n")

			f.write("Reference image: https://3ds.hacks.guide/images/screenshots/onboarding/sdroot.png\n\n")

			f.write(f"At the time of writing, the root of your SD card is at: '{root}'. Check it out!\n")
			f.close()

		scriptroot = root
		thisfile = os.path.join(scriptroot, "mset9.py")

if osver == "Darwin":
	# ======== macOS / iOS? ========

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
		if not scriptroot.startswith("/Volumes/"):
			prbad("Error 01: Couldn't find Nintendo 3DS folder! Ensure that you are running this script from the root of the SD card.")
			# should we add some macos specific message?
			exitOnEnter()

		dig_for_root()
		prinfo("Resolving device...")
		device = None
		devid = os.stat(scriptroot).st_dev
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
		def isdir(self, path):
			return self.fs.getinfo(path).is_dir
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
		def listdir(self, path):
			return self.fs.listdir(path)
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
		def isdir(self, path):
			return os.path.isdir(self.abs(path))
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
		def listdir(self, path):
			return os.listdir(path)
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
				prbad("Error 08: Couldn't reapply working directory, is SD card reinserted?")
				exitOnEnter()
		def print_root(self):
			prinfo(f"Current dir: {self.root}")

	dig_for_root()
	fs = OSFS(scriptroot)

def clearScreen():
	if osver == "Windows":
		os.system("cls")
	else:
		os.system("clear")

# -1: Cancelled
def getInput(options):
	if type(options) == range:
		options = [*options, (options[-1] + 1)]

	while 1:
		try:
			opt = int(input(">>> "))
		except KeyboardInterrupt:
			print()
			return -1
		except EOFError:
			print()
			return -1
		except ValueError:
			opt = 0xFFFFFFFF

		if opt not in options:
			prbad(f"Invalid input, try again. Valid inputs: {str.join(', ', (str(i) for i in options))}")
			continue

		return opt

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
if not fs.ensurespace(16 * 1024 * 1024):
	#prbad(f"Error 06: You need at least 16MB free space on your SD card, you have {(freeSpace / 1000000):.2f} bytes!")
	prbad("Error 06: You need at least 16MB free space on your SD card!")
	prinfo("Please free up some space and try again.")
	exitOnEnter()

clearScreen()
print(f"MSET9 {VERSION} SETUP by zoogie, Aven and DannyAAM")
print("What is your console model and version?")
print("Old 3DS has two shoulder buttons (L and R)")
print("New 3DS has four shoulder buttons (L, R, ZL, ZR)")

print("\n-- Please type in a number then hit return --\n")

consoleNames = {
	1: "Old 3DS/2DS, 11.8.0 to 11.17.0",
	2: "New 3DS/2DS, 11.8.0 to 11.17.0",
	3: "Old 3DS/2DS, 11.4.0 to 11.7.0",
	4: "New 3DS/2DS, 11.4.0 to 11.7.0"
}

print("Enter one of these four numbers!")
for i in consoleNames:
	print(f"Enter {i} for: {consoleNames[i]}")

# print("Enter 1 for: Old 3DS/2DS, 11.8.0 to 11.17.0")
# print("Enter 2 for: New 3DS/2DS, 11.8.0 to 11.17.0")
# print("Enter 3 for: Old 3DS/2DS, 11.4.0 to 11.7.0")
# print("Enter 4 for: New 3DS/2DS, 11.4.0 to 11.7.0")

encodedID1s = {
	1: "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A0871A0050899CE0408730064006D00630000900A0862003900",
	2: "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A0871A005085DCE0408730064006D00630000900A0862003900",
	3: "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A08499E050899CC0408730064006D00630000900A0862003900",
	4: "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A08459E050881CC0408730064006D00630000900A0862003900"
}

consoleIndex = getInput(range(1, 4))
if consoleIndex < 0:
	prgood("Goodbye!")
	exitOnEnter(remount=True)

ID0, ID0Count, ID1, ID1Count = "", 0, "", 0

haxStates = ["\033[30;1mID1 not created\033[0m", "\033[33;1mNot ready - sanity check failed\033[0m", "\033[32mReady\033[0m", "\033[32;1mInjected\033[0m", "\033[32mRemoved trigger file\033[0m"]
haxState = 0

realID1Path = ""
realID1BackupTag = "_user-id1"

hackedID1 = bytes.fromhex(encodedID1s[consoleIndex]).decode("utf-16le")  # ID1 - arm injected payload in readable format
hackedID1Path = ""

homeMenuExtdata = [0x8F,  0x98,  0x82,  0xA1,  0xA9,  0xB1]  # us,eu,jp,ch,kr,tw
miiMakerExtdata = [0x217, 0x227, 0x207, 0x267, 0x277, 0x287]  # us,eu,jp,ch,kr,tw
trigger = "002F003A.txt"  # all 3ds ":/" in hex format
triggerFilePath = ""

def createHaxID1():
	global fs, ID0, hackedID1Path, realID1Path, realID1BackupTag

	print("\033[0;33m=== DISCLAIMER ===\033[0m") # 5;33m? The blinking is awesome but I also don't want to frighten users lol
	print()
	print("This process will temporarily reset all your 3DS data.")
	print("All your applications and themes will disappear.")
	print("This is perfectly normal, and if everything goes right, it will re-appear")
	print("at the end of the process.")
	print()
	print("In any case, it is highly recommended to make a backup of your SD card's contents to a folder on your PC.")
	print("(Especially the 'Nintendo 3DS' folder.)")
	print()

	if osver == "Linux": # ...
		print("(on Linux, things like to not go right - please ensure that your SD card is mounted with the 'utf8' option.)")
		print()

	print("Input '1' again to confirm.")
	print("Input '2' to cancel.")
	time.sleep(3)
	if getInput(range(1, 2)) != 1:
		print()
		prinfo("Cancelled.")
		exitOnEnter(remount=True)

	hackedID1Path = ID0 + "/" + hackedID1

	try:
		prinfo("Creating hacked ID1...")
		fs.mkdir(hackedID1Path)
		prinfo("Creating dummy databases...")
		fs.mkdir(hackedID1Path + "/dbs")
		fs.open (hackedID1Path + "/dbs/title.db", "w").close()
		fs.open (hackedID1Path + "/dbs/import.db", "w").close()
	except Exception as exc:
		if isinstance(exc, OSError) and osver == "Windows" and exc.winerror == 234: # WinError 234 my love
			prbad("Error 18: Windows locale settings are broken!")
			prinfo("Consult https://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9 for instructions.")
			prinfo("If you need help, join Nintendo Homebrew on Discord: https://discord.gg/nintendohomebrew")
		elif isinstance(exc, OSError) and osver == "Linux" and exc.errno == 22: # Don't want this message to display on Windows if it ever manages to
			prbad("Failed to create hacked ID1!") # Give this an error number?
			prbad(f"Error details: {str(exc)}")
			prinfo("Please unmount your SD card and remount it with the 'utf8' option.") # Should we do this ourself? Like look at macOS
		else:
			prbad("An unknown error occured!")
			prbad(f"Error details: {str(exc)}")
			prinfo("Join Nintendo Homebrew on Discord for help: https://discord.gg/nintendohomebrew")

		exitOnEnter()

	if not realID1Path.endswith(realID1BackupTag):
		prinfo("Backing up original ID1...")
		fs.rename(realID1Path, realID1Path + realID1BackupTag)

	prgood("Created hacked ID1.")
	exitOnEnter()

titleDatabasesGood = False
menuExtdataGood = False
miiExtdataGood = False

def sanity():
	global fs, hackedID1Path, titleDatabasesGood, menuExtdataGood, miiExtdataGood

	prinfo("Checking databases...")
	checkTitledb  = softcheck(hackedID1Path + "/dbs/title.db",  0x31E400)
	checkImportdb = softcheck(hackedID1Path + "/dbs/import.db", 0x31E400)
	titleDatabasesGood = not (checkTitledb or checkImportdb)
	if not titleDatabasesGood:
		# Stub them both. I'm not sure how the console acts if title.db is fine but not import. Someone had that happen, once
		fs.open(hackedID1Path + "/dbs/title.db",  "w").close()
		fs.open(hackedID1Path + "/dbs/import.db", "w").close()

	prinfo("Checking for HOME Menu extdata...")
	for i in homeMenuExtdata:
		extdataRegionCheck = hackedID1Path + f"/extdata/00000000/{i:08X}"
		if fs.exists(extdataRegionCheck):
			menuExtdataGood = True
			break
	
	prinfo("Checking for Mii Maker extdata...")
	for i in miiMakerExtdata:
		extdataRegionCheck = hackedID1Path + f"/extdata/00000000/{i:08X}"
		if fs.exists(extdataRegionCheck):
			miiExtdataGood = True
			break

	return menuExtdataGood and miiExtdataGood and titleDatabasesGood

def sanityReport():
	if not menuExtdataGood:
		prbad("HOME menu extdata: Missing!")
		prinfo("Please power on your console with your SD inserted, then check again.")
		prinfo("If this does not work, your SD card may need to be reformatted.")
	else:
		prgood("HOME menu extdata: OK!")

	print()

	if not miiExtdataGood:
		prbad("Mii Maker extdata: Missing!")
		prinfo("Please power on your console with your SD inserted, then launch Mii Maker.")
	else:
		prgood("Mii Maker extdata: OK!")

	print()

	if not titleDatabasesGood:
		prbad("Title database: Not initialized!")
		prinfo("Please power on your console with your SD inserted, open System Setttings,")
		prinfo("navigate to Data Management -> Nintendo 3DS -> Software, then select Reset.")
	else:
		prgood("Title database: OK!")

	print()

def injection():
	global fs, haxState, hackedID1Path, trigger

	triggerFilePath = hackedID1Path + "/extdata/" + trigger

	if fs.exists(triggerFilePath):
		fs.remove(triggerFilePath)
		haxState = 4
		prgood("Removed trigger file.")
		return

	prinfo("Injecting trigger file...")
	with fs.open(triggerFilePath, 'w') as f:
		#f.write("not so useless FAT-fs null deref")
		f.write("pls be haxxed mister arm9, thx")
		f.close()

	prgood("MSET9 successfully injected!")
	exitOnEnter()

def remove():
	global fs, ID0, ID1, hackedID1Path, realID1Path, realID1BackupTag, titleDatabasesGood

	prinfo("Removing MSET9...")

	if hackedID1Path and fs.exists(hackedID1Path):
		if not fs.exists(realID1Path + "/dbs") and titleDatabasesGood:
			prinfo("Moving databases to user ID1...")
			fs.rename(hackedID1Path + "/dbs", realID1Path + "/dbs")

		prinfo("Deleting hacked ID1...")
		fs.rmtree(hackedID1Path)

	if fs.exists(realID1Path) and realID1Path.endswith(realID1BackupTag):
		prinfo("Renaming original ID1...")
		fs.rename(realID1Path, ID0 + "/" + ID1[:32])
		ID1 = ID1[:32]
		realID1Path = ID0 + "/" + ID1

	haxState = 0
	prgood("Successfully removed MSET9!")

def softcheck(keyfile, expectedSize = None, crc32 = None):
	global fs
	filename = keyfile.rsplit("/")[-1]

	if not fs.exists(keyfile):
		prbad(f"{filename} does not exist on SD card!")
		return 1

	fileSize = fs.getsize(keyfile)
	if not fileSize:
		prbad(f"{filename} is an empty file!")
		return 1
	elif expectedSize and fileSize != expectedSize:
		prbad(f"{filename} is size {fileSize:,} bytes, not expected {expectedSize:,} bytes")
		return 1

	if crc32:
		with fs.open(keyfile, "rb") as f:
			checksum = binascii.crc32(f.read())
			f.close()
			if crc32 != checksum:
				prbad(f"{filename} was not recognized as the correct file")
				return 1

	prgood(f"{filename} looks good!")
	return 0

def is3DSID(name):
	if not len(name) == 32:
		return False

	try:
		hex_test = int(name, 0x10)
	except:
		return False

	return True


# Section: Sanity checks A (global files required for exploit)
writeProtectCheck()

prinfo("Ensuring extracted files exist...")

fileSanity = 0
fileSanity += softcheck("boot9strap/boot9strap.firm", crc32=0x08129C1F)
fileSanity += softcheck("boot.firm")
fileSanity += softcheck("boot.3dsx")
fileSanity += softcheck("b9")
fileSanity += softcheck("SafeB9S.bin")

if fileSanity > 0:
	prbad("Error 07: One or more files are missing or malformed!")
	prinfo("Please re-extract the MSET9 zip file, overwriting any existing files when prompted.")
	exitOnEnter()

# prgood("All files look good!")

# Section: sdwalk
for dirname in fs.listdir("Nintendo 3DS/"):
	fullpath = "Nintendo 3DS/" + dirname

	if not fs.isdir(fullpath):
		prinfo(f"Found file in Nintendo 3DS folder? '{dirname}'")
		continue

	if not is3DSID(dirname):
		continue

	prinfo(f"Detected ID0: {dirname}")
	ID0 = fullpath
	ID0Count += 1

if ID0Count != 1:
	prbad(f"Error 04: You don't have 1 ID0 in your Nintendo 3DS folder, you have {ID0Count}!")
	prinfo("Consult: https://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9 for help!")
	exitOnEnter()

for dirname in fs.listdir(ID0):
	fullpath = ID0 + "/" + dirname

	if not fs.isdir(fullpath):
		prinfo(f"Found file in ID0 folder? '{dirname}'")
		continue

	if is3DSID(dirname) or (dirname[32:] == realID1BackupTag and is3DSID(dirname[:32])):
		prinfo(f"Detected ID1: {dirname}")
		ID1 = dirname
		realID1Path = ID0 + "/" + ID1
		ID1Count += 1
	elif "sdmc" in dirname and len(dirname) == 32:
		currentHaxID1enc = dirname.encode("utf-16le").hex().upper()
		currentHaxID1index = 0

		for haxID1index in encodedID1s:
			if currentHaxID1enc == encodedID1s[haxID1index]:
				currentHaxID1index = haxID1index
				break

		if currentHaxID1index == 0 or (hackedID1Path and fs.exists(hackedID1Path)): # shouldn't happen
			prbad("Unrecognized/duplicate hacked ID1 in ID0 folder, removing!")
			fs.rmtree(fullpath)
		elif currentHaxID1index != consoleIndex:
			prbad("Error 03: Don't change console model/version in the middle of MSET9!")
			print(f"Earlier, you selected: '[{currentHaxID1index}.] {consoleNames[currentHaxID1index]}'")
			print(f"Now, you selected:     '[{consoleIndex}.] {consoleNames[consoleIndex]}'")
			print()
			print("Please re-enter the number for your console model and version.")

			choice = getInput([consoleIndex, currentHaxID1index])
			if choice < 0:
				prinfo("Cancelled.")
				hackedID1Path = fullpath
				remove()
				exitOnEnter()

			elif choice == currentHaxID1index:
				consoleIndex = currentHaxID1index
				hackedID1 = dirname

			elif choice == consoleIndex:
				fs.rename(fullpath, ID0 + "/" + hackedID1)

		hackedID1Path = ID0 + "/" + hackedID1
		haxState = 1 # Not ready.

		if fs.exists(hackedID1Path + "/extdata/" + trigger):
			triggerFilePath = hackedID1Path + "/extdata/" + trigger
			haxState = 3 # Injected.
		elif sanity():
			haxState = 2 # Ready!

if ID1Count != 1:
	prbad(f"Error 05: You don't have 1 ID1 in your Nintendo 3DS folder, you have {ID1Count}!")
	prinfo("Consult: https://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9 for help!")
	exitOnEnter()

def mainMenu():
	clearScreen()
	print(f"MSET9 {VERSION} SETUP by zoogie, Aven and DannyAAM")
	print(f"Using {consoleNames[consoleIndex]}")
	print()
	print(f"Current MSET9 state: {haxStates[haxState]}")
	fs.print_root();

	print("\n-- Please type in a number then hit return --\n")

	print("↓ Input one of these numbers!")

	# Not ready (1) - Check for problems
	# Ready (2) - Inject
	# Injected (3) - Remove inject
	optionlabel = {
		0: "Create MSET9 ID1",
		1: "Perform sanity checks",
		2: "Inject MSET9 trigger",
		3: "Remove MSET9 trigger",
	}

	if haxState != 4:
		print(f"{haxState + 1}. {optionlabel[haxState]}")
	if haxState > 0 and haxState != 3:
		print("5. Remove MSET9")

	print("0. Exit")

	while 1:
		optSelect = getInput([haxState + 1, 5, 0])

		fs.reload() # (?)

		if optSelect <= 0:
			break

		elif optSelect == 1: # Create hacked ID1
			createHaxID1()
			exitOnEnter()

		elif optSelect == 2: # Perform sanity checks
			sanityReport()
			exitOnEnter()

		elif optSelect == 3: # Inject trigger file
			injection()
			exitOnEnter()

		elif optSelect == 4: # Remove trigger file
			injection()
			time.sleep(3)
			return mainMenu()

		elif optSelect == 5: # Remove MSET9
			if haxState <= 0:
				prinfo("Nothing to do.")
				continue
			if haxState == 3:
				prbad("Can't do that now!")
				continue

			remove()
			remove_extra() # (?)
			exitOnEnter(remount=True)

mainMenu()
cleanup(remount=True)
prgood("Goodbye!")
time.sleep(2)

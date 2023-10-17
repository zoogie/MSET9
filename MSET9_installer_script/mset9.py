#!/usr/bin/python3
import os, platform, time, shutil, binascii

VERSION = "v1.1"

def prgood(content):
	print(f"[\033[0;32m✓\033[0m] {content}")

def prbad(content):
	print(f"[\033[0;91mX\033[0m] {content}")

def prinfo(content):
	print(f"[*] {content}")

def exitOnEnter(errCode = 0):
	input("[*] Press Enter to exit...")
	exit(errCode)

osver = platform.system()

if osver == "Darwin":
	prbad("Error 11: macOS is not supported!")
	prinfo("Please use a Windows or Linux computer.")
	exitOnEnter()

def clearScreen():
	if osver == "Windows":
		os.system("cls")
	else:
		os.system("clear")

cwd = os.path.dirname(os.path.abspath(__file__))
try:
	os.chdir(cwd)
except Exception:
	prbad("Failed to set cwd: " + cwd)
	prbad("This should pretty much never happen. try running the script again.")
	exitOnEnter()

# Section: insureRoot
if not os.path.exists("Nintendo 3DS/"):
	prbad("Error 01: Couldn't find Nintendo 3DS folder! Make sure you are running in the SD Card root!")
	prbad("If that doesn't work, eject the SD card, and put it back in your console. Turn it on and off again, then restart the script.")
	prinfo(f"Current dir: {cwd}")
	exitOnEnter()

# Section: sdWritable
def writeProtectCheck():
	prinfo("Checking if SD card is writeable...")
	writeable = os.access(cwd, os.W_OK)
	try: # Bodge for windows
		with open("test.txt", "w") as f:
			f.write("test")
			f.close()
		os.remove("test.txt")
	except:
		writeable = False

	if not writeable:
		prbad("Error 02: Your sd is write protected! Please ensure the switch on the side of your SD card is facing upwards.")
		prinfo("Visual aid: https://nintendohomebrew.com/assets/img/nhmemes/sdlock.png")
		exitOnEnter()
	else:
		prgood("SD card is writeable!")

# Section: SD card free space
# ensure 16MB free space
freeSpace = shutil.disk_usage(cwd).free
if freeSpace < 16777216:
	prbad(f"Error 06: You need at least 16MB free space on your SD card, you have {(freeSpace / 1000000):.2f} bytes!")
	prinfo("Please free up some space and try again.")
	exitOnEnter()

clearScreen()
print(f"MSET9 {VERSION} SETUP by zoogie and Aven")
print("What is your console model and version?")
print("Old 3DS has two shoulder buttons (L and R)")
print("New 3DS has four shoulder buttons (L, R, ZL, ZR)")
print("\n-- Please type in a number then hit return --\n")
print("↓ Input one of these Numbers!")
print("1. Old 3DS, 11.8.0 to 11.17.0")
print("2. New 3DS, 11.8.0 to 11.17.0")
print("3. Old 3DS, 11.4.0 to 11.7.0")
print("4. New 3DS, 11.4.0 to 11.7.0")

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
		exitOnEnter()
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
		prbad("Invalid input, try again.")

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
	global haxState, realId1Path, id0, id1, homeDataPath, miiDataPath, homeHex, miiHex
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
		prinfo("Please extract the MSET9 zip file again, being sure to Overwrite any files.")
		exitOnEnter()
	prgood("All files look good!")

	prinfo("Checking databases...")
	checkTitledb = softcheck(realId1Path + "/dbs/title.db", 0x31E400, 0, 1)
	checkImportdb = softcheck(realId1Path + "/dbs/import.db", 0x31E400, 0, 1)
	if checkTitledb or checkImportdb:
		prbad("Error 10: Database(s) malformed or missing!")
		if not (
			os.path.exists(realId1Path + "/dbs/import.db")
			or os.path.exists(realId1Path + "/dbs/title.db")
		):
			if not os.path.exists(realId1Path + "/dbs"):
				os.mkdir(realId1Path + "/dbs")
			if checkTitledb:
				open(realId1Path + "/dbs/title.db", "x").close()
			if checkImportdb:
				open(realId1Path + "/dbs/import.db", "x").close()

			prinfo("Created empty databases.")
		prinfo("please reset the database files in settings -> data management -> nintendo 3ds -> software first before coming back!")
		prinfo("Visual guide: https://3ds.hacks.guide/images/screenshots/database-reset.jpg")
		exitOnEnter()
	else:
		prgood("Databases look good!")
	
	if os.path.exists(realId1Path + "/extdata/" + trigger):
		prinfo("Removing stale trigger...")
		os.remove(realId1Path + "/extdata/" + trigger)
	
	extdataRoot = realId1Path + "/extdata/00000000"

	prinfo("Checking for home menu extdata...")
	for i in homeMenuExtdata:
		extdataRegionCheck = extdataRoot + f"/{i:08X}"
		if os.path.exists(extdataRegionCheck):
			prgood(f"Detected {regionTable[i]} home data!")
			homeHex = i
			homeDataPath = extdataRegionCheck
			menuExtdataGood = True
			break
	
	if not menuExtdataGood:
		prbad("Error 04: No Home Menu Data!")
		prinfo("This shouldn't really happen, Put the sd card back in your console.")
		prinfo("Turn it on and off again, then restart the script.")
		prinfo("For assistance, come visit us: https://discord.gg/nintendohomebrew")
		exitOnEnter()
	
	prinfo("Checking for mii maker extdata...")
	for i in miiMakerExtdata:
		extdataRegionCheck = extdataRoot + f"/{i:08X}"
		if os.path.exists(extdataRegionCheck):
			prgood("Found mii maker data!")
			miiHex = i
			miiDataPath = extdataRegionCheck
			miiExtdataGood = True
			break
	
	if not miiExtdataGood:
		prbad("Error 05: No Mii Maker Data!")
		prinfo("Please go to https://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9 for instructions.")
		exitOnEnter()

def injection():
	global realId1Path, id1

	if not os.path.exists(id0 + "/" + hackedId1):
		prinfo("Creating hacked Id1...")
		hackedId1Path = id0 + "/" + hackedId1
		os.mkdir(hackedId1Path)
		os.mkdir(hackedId1Path + "/extdata")
		os.mkdir(hackedId1Path + "/extdata/00000000")
	else:
		prinfo("Reusing existing hacked Id1...")
		hackedId1Path = id0 + "/" + hackedId1

	if not os.path.exists(hackedId1Path + "/dbs"):
		prinfo("Copying databases to hacked Id1...")
		shutil.copytree(realId1Path + "/dbs", hackedId1Path + "/dbs")

	prinfo("Copying extdata to hacked Id1...")
	if not os.path.exists(hackedId1Path + f"/extdata/00000000/{homeHex:08X}"):
		shutil.copytree(homeDataPath, hackedId1Path + f"/extdata/00000000/{homeHex:08X}")
	if not os.path.exists(hackedId1Path + f"/extdata/00000000/{miiHex:08X}"):
		shutil.copytree(miiDataPath, hackedId1Path + f"/extdata/00000000/{miiHex:08X}")

	prinfo("Injecting trigger file...")
	triggerFilePath = id0 + "/" + hackedId1 + "/extdata/" + trigger
	if not os.path.exists(triggerFilePath):
		with open(triggerFilePath, "w") as f:
			f.write("plz be haxxed mister arm9, thx")
			f.close()
	
	if os.path.exists(realId1Path) and realId1BackupTag not in realId1Path:
		prinfo("Backing up real Id1..."):
		os.rename(realId1Path, realId1Path + realId1BackupTag)
		id1 += realId1BackupTag
		realId1Path = f"{id0}/{id1}"
	else:
		prinfo("Skipping backup because a backup already exists!")


	prgood("MSET9 successfully injected!")

def remove():
	global realId1Path, id0, id1
	prinfo("Removing MSET9...")

	if os.path.exists(realId1Path) and realId1BackupTag in realId1Path:
		prinfo("Renaming original Id1...")
		os.rename(realId1Path, id0 + "/" + id1[:32])
	else: 
		prgood("Nothing to remove!")
		return
	
	# print(id1_path, id1_root+"/"+id1[:32])
	for id1Index in range(1,5): # Attempt to remove *all* hacked id1s
		maybeHackedId = bytes.fromhex(encodedId1s[id1Index]).decode("utf-16le")
		if os.path.exists(id0 + "/" + maybeHackedId):
			prinfo("Deleting hacked Id1...")
			shutil.rmtree(id0 + "/" + maybeHackedId)
	id1 = id1[:32]
	realId1Path = id0 + "/" + id1
	prgood("Successfully removed MSET9!")

def softcheck(keyfile, expectedSize = None, crc32 = None, retval = 0):
	shortname = keyfile.rsplit("/")[-1]
	if not os.path.exists(keyfile):
		prbad(f"{shortname} does not exist on SD card!")
		return retval
	elif expectedSize:
		fileSize = os.path.getsize(keyfile)
		if expectedSize != fileSize:
			prbad(f"{shortname} is size {fileSize:,} bytes, not expected {expectedSize:,} bytes")
			return retval
	elif crc32:
		with open(keyfile, "rb") as f:
			checksum = binascii.crc32(f.read())
			if crc32 != checksum:
				prbad(f"{shortname} was not recognized as the correct file")
				f.close()
				return retval
			f.close()
	prgood(f"{shortname} looks good!")
	return 0

def reapplyWorkingDir():
	try:
		os.chdir(cwd)
		return True
	except Exception:
		prbad("Error 09: Couldn't reapply working directory, is sdcard reinserted?")
		return False

# Section: sdwalk
for root, dirs, files in os.walk("Nintendo 3DS/", topdown=True):

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
				if os.path.exists(os.path.join(root, name) + "/extdata"):
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
		# CHeck if we have an MSET9 Hacked id1 folder
		if "sdmc" in name and len(name) == 32:
		# If the MSET9 folder doesn't match the proper haxid1 for the selected console version
			if hackedId1 != name:
				prbad("Error 03: don't change console version in the middle of MSET9!")
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
print(f"MSET9 {VERSION} SETUP by zoogie and Aven")
print(f"Using {consoleModel} {consoleFirmware}")

print("\n-- Please type in a number then hit return --\n")
print("↓ Input one of these Numbers!")
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

	try:
		os.chdir(cwd)
	except Exception:
		prbad("Error 09: Couldn't reapply working directory, is sdcard reinserted?")
		exitOnEnter()

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
		exitOnEnter()
	elif sysModelVerSelect == 4 or "exit":
		prgood("Goodbye!")
		break
	else:
		prinfo("Invalid input, try again.")

time.sleep(2)
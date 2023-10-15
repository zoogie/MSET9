#!/usr/bin/python3
import os, sys, platform, time, shutil, binascii

VERSION = "v1.1"

def clearScreen():
	if platform.system() == "Windows":
		os.system("cls")
	else:
		os.system("clear")

def prgood(content):
	print(f"[\033[0;32m✓\033[0m] {content}")

def prbad(content):
	print(f"[\033[0;91mX\033[0m] {content}")

def prinfo(content):
	print(f"[*] {content}")

cwd = os.path.dirname(os.path.abspath(__file__))
print(cwd)
try:
	os.chdir(cwd)
except Exception:
	prbad("Error 11: Failed to set cwd: " + cwd)
	exit(1)

clearScreen()
print(f"MSET9 {VERSION} SETUP by zoogie")
print("What is your console model and version?")
print("Old 3DS has two shoulder buttons (L and R)")
print("New 3DS has four shoulder buttons (L, R, ZL, ZR)")
print("\n-- Please type in a number then hit return --\n")
print("1. Old 3DS, 11.8.0 to 11.17.0")
print("2. New 3DS, 11.8.0 to 11.17.0")
print("3. Old 3DS, 11.4.0 to 11.7.0")
print("4. New 3DS, 11.4.0 to 11.7.0")

hackedId1Encoded, consoleModel, consoleFirmware = "", "", ""
while 1:
	try:
		sysModelVerSelect = int(input(">>> "))
	except KeyboardInterrupt:
		print()
		prgood("Goodbye!")
		exit()
	except:
		sysModelVerSelect = 42
	if sysModelVerSelect == 1:
		hackedId1Encoded = "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A0871A0050899CE0408730064006D00630000900A0862003900"
		consoleModel = "OLD3DS"
		consoleFirmware = "11.8-11.17"
		break

	if sysModelVerSelect == 2:
		hackedId1Encoded = "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A0871A005085DCE0408730064006D00630000900A0862003900"
		consoleModel = "NEW3DS"
		consoleFirmware = "11.8-11.17"
		break

	if sysModelVerSelect == 3:
		hackedId1Encoded = "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A08499E050899CC0408730064006D00630000900A0862003900"
		consoleModel = "OLD3DS"
		consoleFirmware = "11.4-11.7"
		break

	if sysModelVerSelect == 4:
		hackedId1Encoded = "FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A08459E050881CC0408730064006D00630000900A0862003900"
		consoleModel = "NEW3DS"
		consoleFirmware = "11.4-11.7"
		break

	else:
		print("Invalid input, try again.")

trigger = "002F003A.txt"  # all 3ds ":/" in hex
hackedId1 = bytes.fromhex(hackedId1Encoded).decode("utf-16le")  # ID1 - arm injected payload in readable format
id1 = ""
id0 = ""
realId1Path = ""

extdataRoot = ""
realId1BackupTag = "_user-id1"
haxState = 0  # 0 setup state, 1 hax state
id0Count = 0
id0List = []
shouldRemoveHax = 0

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

# Section: insureRoot
if not os.path.exists("Nintendo 3DS/"):
	prbad("Error 1: Are you sure you're running this script from the root of your SD card (right next to 'Nintendo 3DS')? You need to!")
	prinfo(f"Current dir: {cwd}")
	time.sleep(10)
	sys.exit(0)

# Section: sdWritable
writeable = os.access(cwd, os.W_OK)
if not writeable:
	prbad("Error 2: Your sd is write protected! Please ensure the switch on the side of your SD card is facing upwards.")
	prinfo("Visual aid: https://nintendohomebrew.com/assets/img/nhmemes/sdlock.png")
	time.sleep(10)
	sys.exit(0)

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
					id1 = name
					id0 = root
					realId1Path = os.path.join(root, name)

					if realId1BackupTag in name:
						haxState = 1

				# Otherwise, add it to the id0 list because we need to make sure we only have one id0
				else:
					id0Count += 1
					id0List.append(os.path.join(root, name))

		# CHeck if we have an MSET9 Hacked id1 folder
		if "sdmc" in name and len(name) == 32:
			# If the MSET9 folder doesn't match the proper haxid1 for the selected console version
			if hackedId1 != name:
				prbad("Error 3: don't change console version in the middle of MSET9!")
				prbad("Make sure to run option 4, Remove MSET9 before you change modes!")
				time.sleep(2)
				prinfo("Removing mismatched haxid1...")
				shutil.rmtree(os.path.join(root, name))
				prgood("done.")
				time.sleep(3)
				shouldRemoveHax = 1

homeDataPath, miiDataPath, homeHex, miiHex = "", "", 0x0, 0x0
def sanity():
	global haxState, realId1Path, id0, id1, homeDataPath, miiDataPath, homeHex, miiHex
	menuExtdataGood = False
	miiExtdataGood = False

	print()
	prinfo("Performing sanity checks...")

	prinfo("Ensuring extracted files exist...")
	check("boot9strap/boot9strap.firm", 0, 0x08129C1F)
	check("boot.firm")
	check("boot.3dsx")
	check("b9")
	check("SafeB9S.bin")
	prgood("All files look good!")

	prinfo("Checking databases...")
	checkTitledb = softcheck(realId1Path + "/dbs/title.db", 0x31E400, 0, 1)
	checkImportdb = softcheck(realId1Path + "/dbs/import.db", 0x31E400, 0, 1)
	if checkTitledb or checkImportdb:
		prbad("Error 13: Database(s) malformed or missing!")
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
		sys.exit(0)
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
		prbad("Error 4: No Home Menu Data!")
		prinfo("This shouldn't really happen, Put the sd card back in your console.")
		prinfo("Turn it on and off again, then restart the script.")
		sys.exit(0)
	
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
		prbad("Err 5: No Mii Maker Data!")
		prinfo("Please go to https://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9 for instructions.")
		sys.exit(0)

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
	shutil.copytree(homeDataPath, hackedId1Path + f"/extdata/00000000/{homeHex:08X}")
	shutil.copytree(miiDataPath, hackedId1Path + f"/extdata/00000000/{miiHex:08X}")

	if os.path.exists(realId1Path):
		prinfo("Backing up real Id1...")
		os.rename(realId1Path, realId1Path + realId1BackupTag)
	
	id1 += realId1BackupTag
	realId1Path = f"{id0}/{id1}"

	prinfo("Injecting trigger file...")
	triggerFilePath = id0 + "/" + hackedId1 + "/extdata/" + trigger
	if not os.path.exists(triggerFilePath):
		with open(triggerFilePath, "w") as f:
			f.write("plz be haxxed mister arm9, thx")
			f.close()
	prgood("Done.")

def delete():
	prinfo("Deleting trigger file...")
	triggerFilePath = id0 + "/" + hackedId1 + "/extdata/" + trigger
	if os.path.exists(triggerFilePath):
		os.remove(triggerFilePath)
		prgood("done.")
	prinfo("Nothing to remove!")

def remove():
	global haxState, realId1Path, id0, id1
	prinfo("Removing MSET9...")
	if not os.path.exists(id0 + "/" + hackedId1) and (os.path.exists(realId1Path) and realId1BackupTag not in realId1Path):
		prinfo("Nothing to remove!")
		return

	if os.path.exists(realId1Path) and realId1BackupTag in realId1Path:
		prinfo("Renaming original Id1...")
		os.rename(realId1Path, id0 + "/" + id1[:32])
	# print(id1_path, id1_root+"/"+id1[:32])
	if os.path.exists(id0 + "/" + hackedId1):
		prinfo("Deleting hacked Id1...")
		shutil.rmtree(id0 + "/" + hackedId1)
	id1 = id1[:32]
	realId1Path = id0 + "/" + id1
	haxState = 0
	prgood("done.")

def softcheck(keyfile, expectedSize, crc32, retval):
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

def check(keyfile, expectedSize = None, crc32 = None):
	shortname = keyfile.rsplit("/")[-1]
	if not os.path.exists(keyfile):
		prbad(f"Error 8: {shortname} does not exist on SD card!")
		prinfo("Please extract the MSET9 zip file again, being sure to Overwrite any files.")
		sys.exit(0)
	elif expectedSize:
		fileSize = os.path.getsize(keyfile)
		if expectedSize != fileSize:
			prbad(f"Error 9: {shortname} is size {fileSize:,} bytes, not expected {expectedSize:,} bytes")
			prinfo("Please extract the MSET9 zip file again, being sure to Overwrite any files.")
			sys.exit(0)
	elif crc32:
		with open(keyfile, "rb") as f:
			checksum = binascii.crc32(f.read())
			if crc32 != checksum:
				prbad(f"Error 10: {shortname} was not recognized as the correct file")
				prinfo("Please extract the MSET9 zip file again, being sure to Overwrite any files.")
				f.close()
				sys.exit(0)
			f.close()

prinfo("Detected ID0(s):")
for i in id0List:
	prinfo(i)
print()
if id0Count != 1:
	prbad(f"Error 7: You don't have 1 ID0 in your Nintendo 3DS folder, you have {id0Count}!")
	prinfo("Consult:\nhttps://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9\nfor help!")
	sys.exit(0)

def reapplyWorkingDir():
	try:
		os.chdir(cwd)
		return True
	except Exception:
		prbad("Error 12: Couldn't reapply cwd, is sdcard reinserted?")
		return False

clearScreen()
print(f"MSET9 {VERSION} SETUP by zoogie")
print(f"Using {consoleModel} {consoleFirmware}")

print("\n-- Please type in a number then hit return --\n")
print("1. Perform sanity checks")
print("2. Inject MSET9 exploit")
print(f"3. Delete trigger file {trigger}")
print("4. Manually Remove MSET9")
print("5. Exit")

while 1:
	try:
		sysModelVerSelect = int(input(">>> "))
	except KeyboardInterrupt:
		sysModelVerSelect = 5 # exit on Ctrl+C
		print()
	except:
		sysModelVerSelect = 42

	# Separated to maybe fix removable bug
	if not reapplyWorkingDir():
		continue #already prints error if fail

	if sysModelVerSelect == 1:
		sanity()
		prgood("Looking good!\n")
	elif sysModelVerSelect == 2:
		sanity()
		injection()
	elif sysModelVerSelect == 3:
		delete()
	elif sysModelVerSelect == 4:
		remove()
	elif sysModelVerSelect == 5 or "exit":
		prgood("Goodbye!")
		break
	else:
		prinfo("Invalid input, try again.")

time.sleep(2)
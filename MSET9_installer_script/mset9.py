#!/usr/bin/python3
import os, sys, platform, time, shutil, binascii

VERSION = "v1.1"

cwd = os.path.dirname(os.path.abspath(__file__))
print(cwd)
try:
	os.chdir(cwd)
except Exception:
	print("Error 11: Failed to set cwd: " + cwd)
	exit(1)

def clearScreen():
	if platform.system() == "Windows":
		os.system("cls")
	else:
		os.system("clear")

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
		sysModelVerSelect = int(input(">>>"))
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

# Make sure we're running from the right spot
if not os.path.exists("Nintendo 3DS/"):
	print("Error 1: Are you sure you're running this script from the root of your SD card (right next to 'Nintendo 3DS')? You need to!")
	print(f"Current dir: {cwd}")
	time.sleep(10)
	sys.exit(0)

writeable = os.access(cwd, os.W_OK)
if not writeable:
	print("Error 2: Your sd is write protected! Please ensure the switch on the side of your SD card is facing upwards.")
	print("Visual aid: https://nintendohomebrew.com/assets/img/nhmemes/sdlock.png")
	time.sleep(10)
	sys.exit(0)


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
				print("Error 3: don't change console version in the middle of MSET9!")
				print("Make sure to run option 4, Remove MSET9 before you change modes!")
				time.sleep(2)
				print("Removing mismatched haxid1...")
				shutil.rmtree(os.path.join(root, name))
				print("done.")
				time.sleep(3)
				shouldRemoveHax = 1


def setup():
	global haxState, realId1Path, id0, id1
	menuExtdataGood = False
	miiExtdataGood = False
	homeDataPath = ""
	miiDataPath = ""


	# Ensure we aren't already configured.
	print("Setting up...")
	if haxState:
		print("Already setup, run option 2!")
		return
	
	# Ensure data management databases exist
	checkTitledb = softcheck(realId1Path + "/dbs/title.db", 0x31E400, 0, 1)
	checkImportdb = softcheck(realId1Path + "/dbs/import.db", 0x31E400, 0, 1)
	if checkTitledb or checkImportdb:
		if not (
			os.path.exists(realId1Path + "/dbs/import.db")
			or os.path.exists(realId1Path + "/dbs/title.db")
		):
			dbGenInput = input(("Create empty databases now? (type yes/no)")).lower()
			if dbGenInput == "yes" or "y":
				if not os.path.exists(realId1Path + "/dbs"):
					os.mkdir(realId1Path + "/dbs")
				if checkTitledb:
					open(realId1Path + "/dbs/title.db", "x").close()
				if checkImportdb:
					open(realId1Path + "/dbs/import.db", "x").close()

				print("Created empty databases.")
			else:
				print("Didn't create empty databases.")
		print("please reset the database files in settings -> data management -> nintendo 3ds -> software first before coming back!")
		print("Visual guide: https://3ds.hacks.guide/images/screenshots/database-reset.jpg")
		sys.exit(0)

	if os.path.exists(realId1Path + "/extdata/" + trigger):
		os.remove(realId1Path + "/extdata/" + trigger)

	extdataRoot = realId1Path + "/extdata/00000000"

	for i in homeMenuExtdata:
		extdataRegionCheck = extdataRoot + f"/{i:08X}"
		if os.path.exists(extdataRegionCheck):
			#print(temp,hackedId1Path+f"/extdata/00000000/{i:08X}")
			homeDataPath = extdataRegionCheck
			menuExtdataGood = True
			break
	
	if not menuExtdataGood:
		print("Error 4: No Home Menu Data!")
		print("This shouldn't really happen, Put the sd card back in your console.")
		print("Press the home settings icon in the top left, then resume from Section I step 7.")
		sys.exit(0)

	for i in miiMakerExtdata:
		extdataRegionCheck = extdataRoot + f"/{i:08X}"
		if os.path.exists(extdataRegionCheck):
			#shutil.copytree(temp, hackedId1Path + f"/extdata/00000000/{i:08X}")
			miiDataPath = extdataRegionCheck
			miiExtdataGood = True
			break

	if not miiExtdataGood:
		print("Err 5: No Mii Maker Data!")
		print("Please go to https://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9 for instructions.")
		sys.exit(0)

	# Currently: make this error safe
	# Create the hacked id1 folder
	if not os.path.exists(id0 + "/" + hackedId1):
		hackedId1Path = id0 + "/" + hackedId1
		os.mkdir(hackedId1Path)
		os.mkdir(hackedId1Path + "/extdata")
		os.mkdir(hackedId1Path + "/extdata/00000000")


	if not os.path.exists(hackedId1Path + "/dbs"):
		shutil.copytree(realId1Path + "/dbs", hackedId1Path + "/dbs")

	# *now* we can copy the extdata to the hacked path instead of failing with a half copied folder
	shutil.copytree(homeDataPath, hackedId1Path + f"/extdata/00000000/{i:08X}")
	shutil.copytree(miiDataPath, hackedId1Path + f"/extdata/00000000/{i:08X}")


	if os.path.exists(realId1Path):
		os.rename(realId1Path, realId1Path + realId1BackupTag)

	id1 += realId1BackupTag
	realId1Path = f"{id0}/{id1}"
	haxState = 1
	print("done.")


def inject():
	if haxState == 0:
		print("Please run option 2 first!")
		return

	print("Injecting... ", end="")
	triggerFilePath = id0 + "/" + hackedId1 + "/extdata/" + trigger
	if not os.path.exists(triggerFilePath):
		with open(triggerFilePath, "w") as f:
			f.write("plz be haxxed mister arm9, thx")
			f.close()
	print("done.")


def delete():
	if haxState == 0:
		print("Run option 1 first!")
		return
	print("Deleting... ")
	triggerFilePath = id0 + "/" + hackedId1 + "/extdata/" + trigger
	if os.path.exists(triggerFilePath):
		os.remove(triggerFilePath)
	print("done.")


def remove():
	global haxState, realId1Path, id0, id1
	print("Removing... ", end="")
	if not os.path.exists(id0 + "/" + hackedId1) and (os.path.exists(realId1Path) and realId1BackupTag not in realId1Path):
		print("Nothing to remove!")
		return
	if os.path.exists(realId1Path) and realId1BackupTag in realId1Path:
		os.rename(realId1Path, id0 + "/" + id1[:32])
	# print(id1_path, id1_root+"/"+id1[:32])
	if os.path.exists(id0 + "/" + hackedId1):
		shutil.rmtree(id0 + "/" + hackedId1)
	id1 = id1[:32]
	realId1Path = id0 + "/" + id1
	haxState = 0
	print("done.")


def softcheck(keyfile, expectedSize, crc32, retval):
	if not os.path.exists(keyfile):
		print(f"{keyfile} does not exist on SD card!")
		return retval
	elif expectedSize:
		fileSize = os.path.getsize(keyfile)
		if expectedSize != fileSize:
			print(f"{keyfile} is size {fileSize:,} bytes, not expected {expectedSize:,} bytes")
			return retval
	elif crc32:
		with open(keyfile, "rb") as f:
			checksum = binascii.crc32(f.read())
			if crc32 != checksum:
				print(f"{keyfile} was not recognized as the correct file")
				f.close()
				return retval
			f.close()
	return 0

# Checks if the file exists, and optionally checks the size and crc32
def check(keyfile, expectedSize = None, crc32 = None):
	if not os.path.exists(keyfile):
		print(f"Error 8: {keyfile} does not exist on SD card!")
		sys.exit(0)
	elif expectedSize:
		fileSize = os.path.getsize(keyfile)
		if expectedSize != fileSize:
			print(f"Error 9: {keyfile} is size {fileSize:,} bytes, not expected {expectedSize:,} bytes")
			sys.exit(0)
	elif crc32:
		with open(keyfile, "rb") as f:
			checksum = binascii.crc32(f.read())
			if crc32 != checksum:
				print(f"Error 10: {keyfile} was not recognized as the correct file")
				f.close()
				sys.exit(0)
			f.close()


def reapplyWorkingDir():
	try:
		os.chdir(cwd)
		return True
	except Exception:
		print("Error 12: Couldn't reapply cwd, is sdcard reinserted?")
		return False

if shouldRemoveHax:
	remove()

# Ensure we have the required files (people extracted the entire zip to their sdcard)
check("boot9strap/boot9strap.firm", 0, 0x08129C1F)
# check("Nintendo 3DS/Private/00020400/phtcache.bin", 0x7f53c, 0)
check("boot.firm")
check("boot.3dsx")
check("b9")
check("SafeB9S.bin")

if id0Count == 0:
	print("Error 6: You're supposed to be running this on the 3DS SD card root!")
	print(f"NOT {cwd}")
	time.sleep(10)
	sys.exit(0)

print("Detected ID0(s):")
for i in id0List:
	print(i)
print("")
if id0Count != 1:
	print(f"Error 7: You don't have 1 ID0 in your Nintendo 3DS folder, you have {id0Count}!")
	print("Consult:\nhttps://3ds.hacks.guide/troubleshooting#installing-boot9strap-mset9\nfor help!")
	sys.exit(0)

clearScreen()
print(f"MSET9 {VERSION} SETUP by zoogie")
print(f"Using {consoleModel} {consoleFirmware}")

print("\n-- Please type in a number then hit return --\n")
print("1. Setup MSET9")
print(f"2. Inject trigger file {trigger}")
print(f"3. Delete trigger file {trigger}")
print("4. Remove MSET9, DO NOT FORGET to run this after you finish the exploit!")
print("5. Exit")

while 1:
	try:
		sysModelVerSelect = int(input(">>>"))
	except:
		sysModelVerSelect = 42

	# Separated to maybe fix removable bug
	if not reapplyWorkingDir():
		continue #already prints error if fail

	if sysModelVerSelect == 1:
		setup()
	elif sysModelVerSelect == 2:
		inject()
	elif sysModelVerSelect == 3:
		delete()
	elif sysModelVerSelect == 4:
		remove()
	elif sysModelVerSelect == 5:
		print("Goodbye!")
		break
	else:
		print("Invalid input, try again.")

time.sleep(2)

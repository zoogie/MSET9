#!/usr/bin/python3
import os,sys,platform,time,shutil,binascii
VERSION="v2beta"

p=platform.system()
if p == 'Windows':	#0-win, 1-lin, 2-mac, x-win   lol go with the market leader i guess
	OPSYS=0
elif p == 'Linux':
	OPSYS=1
elif p == 'Darwin': 
	OPSYS=2
else:
	OPSYS=0
cwd = os.path.dirname(os.path.abspath(__file__))  
print(cwd)
try:
	os.chdir(cwd)
except Exception:
	print("Failed to set cwd: " + cwd)
	exit(1)

trigger="002F003A.txt"    #all 3ds ":/"

#old3ds 11.8-11.17
#id1_haxstr="FFFFFFFA119907488546696508A10122054B984768465946FFAA171C4346034CA047B84700900A0871A0050899CE0408730064006D00630000900A0862003900" 
id1_haxstr="FFFFFFFA119907488546696508A10122054B984768465946C0AA171C4346034CA047B84700900A0871A0050899CE0408730064006D00630000900A0862003900" 

haxid1=bytes.fromhex(id1_haxstr) #ID1 - arm injected payload in readable format
haxid1=haxid1.decode("utf-16le")
haxid1_path=""
id1=""
id1_root=""
id1_path=""

ext_root=""
oldtag="_oldid1"
mode=0 #0 setup state, 1 hax state
id0_count=0

home_menu=[0x8f,0x98,0x82,0xA1,0xA9,0xB1]  #us,eu,jp,ch,kr,tw
mii_maker=[0x217,0x227,0x207,0x267,0x277,0x287] #us,eu,jp,ch,kr,tw

if not os.path.exists("Nintendo 3DS/"):
	print("Are you sure you're running this script from the root of your SD card (right next to 'Nintendo 3DS')? You need to!")
	print("Current dir: %s" % cwd)
	time.sleep(10)
	sys.exit(0)
	

for root, dirs, files in os.walk("Nintendo 3DS/", topdown=True):
	for name in files:
		pass
	for name in dirs:
		if haxid1 not in name and len(name[:32]) == 32:
			try:
				temp=int(name[:32],16)
			except:
				continue
			if type(temp) is int:
				if os.path.exists(os.path.join(root, name)+"/extdata"):
					id1=name
					id1_root=root
					id1_path=os.path.join(root, name)
					if oldtag in name:
						mode=1
				else:
					id0_count+=1


def setup():
	global mode, id1_path, id1_root, id1
	menu_ok=0
	mii_ok=0
	print("Setting up...", end='')
	if mode:
		print("Already setup!")
		return
	check(id1_path+"/dbs/title.db", 0x31e400, 0)
	check(id1_path+"/dbs/import.db", 0x31e400, 0)
	if os.path.exists(id1_path+"/extdata/"+trigger):
		os.remove(id1_path+"/extdata/"+trigger)
	if not os.path.exists(id1_root+"/"+haxid1):
		haxid1_path=id1_root+"/"+haxid1
		os.mkdir(haxid1_path)
		os.mkdir(haxid1_path+"/extdata")
		os.mkdir(haxid1_path+"/extdata/00000000")
	if not os.path.exists(haxid1_path+"/dbs"):
		shutil.copytree(id1_path+"/dbs",haxid1_path+"/dbs")
	
	ext_root=id1_path+"/extdata/00000000"
	
	for i in home_menu:
		temp=ext_root+"/%08X" % i
		if os.path.exists(temp):
			#print(temp,haxid1_path+"/extdata/00000000/%08X" % i)
			shutil.copytree(temp,haxid1_path+"/extdata/00000000/%08X" % i)
			menu_ok+=1
	assert(menu_ok==1)
	for i in mii_maker:
		temp=ext_root+"/%08X" % i
		if os.path.exists(temp):
			shutil.copytree(temp,haxid1_path+"/extdata/00000000/%08X" % i)	
			mii_ok+=1
	assert(mii_ok==1)
	
	if os.path.exists(id1_path):
		os.rename(id1_path, id1_path+oldtag)
	id1+=oldtag
	id1_path=id1_root+"/"+id1
	mode=1
	print(" done.")
		
def inject():
	if mode==0:
		print("Run setup first!")	
		return
	print("Injecting...", end='')
	trigger_path=id1_root+"/"+haxid1+"/extdata/"+trigger
	if not os.path.exists(trigger_path):
		with open(trigger_path,"w") as f:
			f.write("plz be haxxed mister arm9, thx")
			f.close()
	print(" done.")

def delete():
	if mode==0:
		print("Run setup first!")	
		return
	print("Deleting...", end='')
	trigger_path=id1_root+"/"+haxid1+"/extdata/"+trigger
	if os.path.exists(trigger_path):
		os.remove(trigger_path)
	print(" done.")

def remove():
	global mode, id1_path, id1_root, id1
	print("Removing...", end='')
	if not os.path.exists(id1_root+"/"+haxid1) and (os.path.exists(id1_path) and oldtag not in id1_path):
		print("Nothing to remove!")
		return
	if os.path.exists(id1_path) and oldtag in id1_path:
		os.rename(id1_path, id1_root+"/"+id1[:32])
	#print(id1_path, id1_root+"/"+id1[:32])
	if os.path.exists(id1_root+"/"+haxid1):
		shutil.rmtree(id1_root+"/"+haxid1)
	id1=id1[:32]
	id1_path=id1_root+"/"+id1
	mode=0
	print(" done.")

def check(keyfile, size, crc32):
		if not os.path.exists(keyfile):
			print("%s \ndoes not exist on SD card!" % keyfile)
			sys.exit(0)
		elif size:
			s=os.path.getsize(keyfile)
			if size != s:
				print("%s \nis size %08X, not expected %08X" % (keyfile,s,size))
				sys.exit(0)
		elif crc32:
			with open(keyfile,"rb") as f:
				temp=f.read()
			c=binascii.crc32(temp)
			if crc32 != c:
				print("%s \n was not recognized as the correct file" % keyfile)
				sys.exit(0)

def reapply_cwd():
	try:
		os.chdir(cwd)
		return True
	except Exception:
		print("Couldn't reapply cwd, is sdcard reinserted?")
		return False

check("boot9strap/boot9strap.firm", 0, 0x08129c1f)
#check("Nintendo 3DS/Private/00020400/phtcache.bin", 0x7f53c, 0)
check("boot.firm", 0, 0)
check("boot.3dsx", 0, 0)
check("b9", 0, 0)
if id0_count == 0:
	print("\nYou're supposed to be running this on the 3DS SD card!")
	print("NOT \n%s" % cwd)
	time.sleep(10)
	sys.exit(0)
assert(id0_count == 1)

if OPSYS == 0:				#windows
	_ = os.system('cls')
else:						#linux or mac
	_ = os.system('clear')
	
print("MSET9 %s SETUP by zoogie" % VERSION)

print("-- Please type in a number then hit return --\n")
print("1. Setup MSET9")
print("2. Inject trigger file %s" % trigger)
print("3. Delete trigger file %s" % trigger)
print("4. Remove MSET9, restore original ID1")
print("5. Exit")

while 1:
	try:
		command = int(input('>>>'))
	except:
		command = 42

	if command >=1 and command <= 4 and not reapply_cwd():
		continue # reapply_cwd already prints error if fail
	
	if command   == 1:
		setup()
	elif command == 2:
		inject()
	elif command == 3:
		delete()	
	elif command == 4:
		remove()
	elif command == 5:
		print("Goodbye!")
		break
	else:
		print("What you say?")

time.sleep(2)

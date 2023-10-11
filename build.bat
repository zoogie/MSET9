cd ID1gen && make clean && make && cd..
python id1gen.py
cd usr2arm9ldr && make clean && make && cd ..
cp usr2arm9ldr/build/arm9.bin out/b9
pause
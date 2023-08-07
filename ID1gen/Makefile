HAXNAME := ID1gen

all:	ID1gen.bin

clean:
	rm -f $(HAXNAME).elf $(HAXNAME).bin

$(HAXNAME).bin: $(HAXNAME).elf
	arm-none-eabi-objcopy -O binary $(HAXNAME).elf $(HAXNAME).bin

$(HAXNAME).elf:	$(HAXNAME).s
	arm-none-eabi-gcc -x assembler-with-cpp -nostartfiles -nostdlib -Ttext=0x00000000 $< -o $(HAXNAME).elf


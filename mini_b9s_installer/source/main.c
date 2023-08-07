/*
*   main.c
*/
#include <string.h>
#include "types.h"
#include "fs.h"
#include "crypto.h"
//#include "draw.h"
//#include "screen.h"
//#include "b9s.h"
//#include "cache.h"
#include "i2c.h"
//#include "utils.h"
#include "fatfs/sdmmc/sdmmc.h"

//#include "firm.h"
//#include "boot9strap.h"
//#include "boot.h"
//#include "install.h"

#define CFG_UNITINFO        (*(vu8  *)0x10010010)
#define REG_GPUBUF_TOP      (*(vu32 *)0x10400468)
#define REG_GPUBUF_TOP2     (*(vu32 *)0x1040046C)
#define REG_GPUBUF_BOT      (*(vu32 *)0x10400568)
#define REG_GPUBUF_BOT2     (*(vu32 *)0x1040056C)

#define ISDEVUNIT    (CFG_UNITINFO != 0)
#define CRC32_RETAIL 0x08129c1f
#define REBOOT i2cWriteRegister(I2C_DEV_MCU,0x20,1<<2)
#define SHUTDOWN i2cWriteRegister(I2C_DEV_MCU,0x20,1<<0)

u32 crc32(u8 *data, int size)
{
  u32 r = ~0; u8 *end = data + size;
 
  while(data < end)
  {
    r ^= *data++;
 
    for(int i = 0; i < 8; i++)
    {
      u32 t = ~((r&1) - 1); r = (r>>1) ^ (0xEDB88320 & t); 
    }
  }
 
  return ~r;
}
/*
void svcSleepThread(s64 nansecs){
	
	asm("svc 9\n");
	asm("bx lr\n");
}

int selfcheck(){
	u32 minib9s=0x23F00000;
	if(crc32((u8*)minib9s, 0x10000-4) != *(u32*)(minib9s+0x10000-4)) return 1;
	return 0;
}
*/
/*
void messageScreen(u32 duration, char *message){
	for(u32 i=0x80000;i<0x180000;i+=4){
			*(u32*)(0x20000000 + i)=0xffffffff;

	}
	u32 charskip = 0x2000;
	for(u32 j=0; j<duration; j++){
		for(u32 i=0x80000;i<0x180000;i+=charskip){
			*(u32*)0x23FFFE00=0x20000000 + i;							
			drawString(message, 0, 0, 0);
		}
	}
	
}

void colorScreen(u8 shade){
	u8 *framebuff=fb->top_left;
	u32 size=(240*400*3)*8; //trying to slow screendraw down a bit to look more dramatic
	for(u32 i=0; i<size;i++){
		framebuff[i/8]=shade;
	}
}
*/
/*
void drawStringCenter(char *str, u8 row){
	int x=(400-(strlen(str)*8))/2;
	if(x<0 || x>=200) {drawString("WHAT IS WRONG WITH THE ELF", 0,30,0); return;}
	drawString(str, x, row*8, 0);
}


struct _fb {
    u8 *top_left;
    u8 *top_right;
    u8 *bottom;
};

static const struct _fb defaultFbs[2] = {
    {
        .top_left  = (u8 *)0x18000000,
        .top_right = (u8 *)0x18000000,
        .bottom    = (u8 *)0x18046500,
    },
    {
        .top_left  = (u8 *)0x18000000,
        .top_right = (u8 *)0x18000000,
        .bottom    = (u8 *)0x18046500,
    },
};
*/

void Reboot(){
	REBOOT;    //reboot system, success condition
	while(1);
}

void Shutdown(){
	SHUTDOWN;  //power down, error condition
	while(1);
}

void main(void)
{
	if(ISDEVUNIT) Shutdown();
	
	u32 size=0x3e00;
	u8 *b9s=(u8*)0x23300000;
	u8 *b9s2=(b9s+=size);

	sdmmc_sdcard_init();
	mountSd();
	
	memset(b9s, 0, size);
	memset(b9s2, 0, size);
	
	u32 rd = fileRead(b9s, "/boot9strap/boot9strap.firm", size, 0);
	unmountSd();
	
	ctrNandInit();
	readFirm0(b9s2, size);
	
	if(memcmp(b9s2, "FIRM", 4)) Shutdown();    //if nand rw isn't working, shutdown system as precaution
	if(!memcmp(b9s2+0x3D, "B9S", 3)) Reboot(); //if b9s firm already installed, reboot since goal achieved already
	
	if( (rd == size) && (crc32(b9s, size) == CRC32_RETAIL) ){ 
	
		writeFirm(b9s, false, size);
		
		for(int i=0; i<5; i++){  //read back firm and check our work, rewriting firm if necessary. times 5.
			readFirm0(b9s2, size);
			if(crc32(b9s2, size) != CRC32_RETAIL){
				writeFirm(b9s, false, size);
			}
			else{
				Reboot();    //reboot system, success condition
			}
		}
	}
	
	Shutdown();
}
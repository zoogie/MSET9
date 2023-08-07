/*
*   memory.c
*
*   memcpy, memset32 and memcmp adapted from https://github.com/mid-kid/CakesForeveryWan/blob/557a8e8605ab3ee173af6497486e8f22c261d0e2/source/memfuncs.c
*/

#include "memory.h"

void memcpy(void *dest, const void *src, u32 size)
{
    u8 *destc = (u8 *)dest;
    const u8 *srcc = (const u8 *)src;

    for(u32 i = 0; i < size; i++)
        destc[i] = srcc[i];
}

void memset32(void *dest, u32 filler, u32 size)
{
    u32 *dest32 = (u32 *)dest;

    for(u32 i = 0; i < size / 4; i++)
        dest32[i] = filler;
}

int memcmp(const void *buf1, const void *buf2, u32 size)
{
    const u8 *buf1c = (const u8 *)buf1,
             *buf2c = (const u8 *)buf2;

    for(u32 i = 0; i < size; i++)
    {
        int cmp = buf1c[i] - buf2c[i];
        if(cmp != 0) return cmp;
    }

    return 0;
}
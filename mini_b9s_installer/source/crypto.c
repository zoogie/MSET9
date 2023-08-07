/*
*   crypto.c
*
*   Crypto libs from http://github.com/b1l1s/ctr
*/

#include "crypto.h"
#include "memory.h"
#include "fatfs/sdmmc/sdmmc.h"

/****************************************************************
*                  Crypto libs
****************************************************************/

/* original version by megazig */

#ifndef __thumb__
#define BSWAP32(x) {\
    __asm__\
    (\
        "eor r1, %1, %1, ror #16\n\t"\
        "bic r1, r1, #0xFF0000\n\t"\
        "mov %0, %1, ror #8\n\t"\
        "eor %0, %0, r1, lsr #8\n\t"\
        :"=r"(x)\
        :"0"(x)\
        :"r1"\
    );\
};

#define ADD_u128_u32(u128_0, u128_1, u128_2, u128_3, u32_0) {\
__asm__\
    (\
        "adds %0, %4\n\t"\
        "addcss %1, %1, #1\n\t"\
        "addcss %2, %2, #1\n\t"\
        "addcs %3, %3, #1\n\t"\
        : "+r"(u128_0), "+r"(u128_1), "+r"(u128_2), "+r"(u128_3)\
        : "r"(u32_0)\
        : "cc"\
    );\
}
#else
#define BSWAP32(x) {x = __builtin_bswap32(x);}

#define ADD_u128_u32(u128_0, u128_1, u128_2, u128_3, u32_0) {\
__asm__\
    (\
        "mov r4, #0\n\t"\
        "add %0, %0, %4\n\t"\
        "adc %1, %1, r4\n\t"\
        "adc %2, %2, r4\n\t"\
        "adc %3, %3, r4\n\t"\
        : "+r"(u128_0), "+r"(u128_1), "+r"(u128_2), "+r"(u128_3)\
        : "r"(u32_0)\
        : "cc", "r4"\
    );\
}
#endif /*__thumb__*/

static void aes_setkey(u8 keyslot, const void *key, u32 keyType, u32 mode)
{
    if(keyslot <= 0x03) return; //Ignore TWL keys for now
    u32 *key32 = (u32 *)key;
    *REG_AESCNT = (*REG_AESCNT & ~(AES_CNT_INPUT_ENDIAN | AES_CNT_INPUT_ORDER)) | mode;
    *REG_AESKEYCNT = (*REG_AESKEYCNT >> 6 << 6) | keyslot | AES_KEYCNT_WRITE;

    REG_AESKEYFIFO[keyType] = key32[0];
    REG_AESKEYFIFO[keyType] = key32[1];
    REG_AESKEYFIFO[keyType] = key32[2];
    REG_AESKEYFIFO[keyType] = key32[3];
}

static void aes_use_keyslot(u8 keyslot)
{
    if(keyslot > 0x3F)
        return;

    *REG_AESKEYSEL = keyslot;
    *REG_AESCNT = *REG_AESCNT | 0x04000000; /* mystery bit */
}

static void aes_setiv(const void *iv, u32 mode)
{
    const u32 *iv32 = (const u32 *)iv;
    *REG_AESCNT = (*REG_AESCNT & ~(AES_CNT_INPUT_ENDIAN | AES_CNT_INPUT_ORDER)) | mode;

    //Word order for IV can't be changed in REG_AESCNT and always default to reversed
    if(mode & AES_INPUT_NORMAL)
    {
        REG_AESCTR[0] = iv32[3];
        REG_AESCTR[1] = iv32[2];
        REG_AESCTR[2] = iv32[1];
        REG_AESCTR[3] = iv32[0];
    }
    else
    {
        REG_AESCTR[0] = iv32[0];
        REG_AESCTR[1] = iv32[1];
        REG_AESCTR[2] = iv32[2];
        REG_AESCTR[3] = iv32[3];
    }
}

static void aes_advctr(void *ctr, u32 val, u32 mode)
{
    u32 *ctr32 = (u32 *)ctr;

    int i;
    if(mode & AES_INPUT_BE)
    {
        for(i = 0; i < 4; ++i) //Endian swap
            BSWAP32(ctr32[i]);
    }

    if(mode & AES_INPUT_NORMAL)
    {
        ADD_u128_u32(ctr32[3], ctr32[2], ctr32[1], ctr32[0], val);
    }
    else
    {
        ADD_u128_u32(ctr32[0], ctr32[1], ctr32[2], ctr32[3], val);
    }

    if(mode & AES_INPUT_BE)
    {
        for(i = 0; i < 4; ++i) //Endian swap
            BSWAP32(ctr32[i]);
    }
}

static void aes_change_ctrmode(void *ctr, u32 fromMode, u32 toMode)
{
    u32 *ctr32 = (u32 *)ctr;
    int i;
    if((fromMode ^ toMode) & AES_CNT_INPUT_ENDIAN)
    {
        for(i = 0; i < 4; ++i)
            BSWAP32(ctr32[i]);
    }

    if((fromMode ^ toMode) & AES_CNT_INPUT_ORDER)
    {
        u32 temp = ctr32[0];
        ctr32[0] = ctr32[3];
        ctr32[3] = temp;

        temp = ctr32[1];
        ctr32[1] = ctr32[2];
        ctr32[2] = temp;
    }
}

static void aes_batch(void *dst, const void *src, u32 blockCount)
{
    *REG_AESBLKCNT = blockCount << 16;
    *REG_AESCNT |=  AES_CNT_START;

    const u32 *src32    = (const u32 *)src;
    u32 *dst32          = (u32 *)dst;

    u32 wbc = blockCount;
    u32 rbc = blockCount;

    while(rbc)
    {
        if(wbc && ((*REG_AESCNT & 0x1F) <= 0xC)) //There's space for at least 4 ints
        {
            *REG_AESWRFIFO = *src32++;
            *REG_AESWRFIFO = *src32++;
            *REG_AESWRFIFO = *src32++;
            *REG_AESWRFIFO = *src32++;
            wbc--;
        }

        if(rbc && ((*REG_AESCNT & (0x1F << 0x5)) >= (0x4 << 0x5))) //At least 4 ints available for read
        {
            *dst32++ = *REG_AESRDFIFO;
            *dst32++ = *REG_AESRDFIFO;
            *dst32++ = *REG_AESRDFIFO;
            *dst32++ = *REG_AESRDFIFO;
            rbc--;
        }
    }
}

static void aes(void *dst, const void *src, u32 blockCount, void *iv, u32 mode, u32 ivMode)
{
    *REG_AESCNT =   mode |
                    AES_CNT_INPUT_ORDER | AES_CNT_OUTPUT_ORDER |
                    AES_CNT_INPUT_ENDIAN | AES_CNT_OUTPUT_ENDIAN |
                    AES_CNT_FLUSH_READ | AES_CNT_FLUSH_WRITE;

    u32 blocks;
    while(blockCount != 0)
    {
        if((mode & AES_ALL_MODES) != AES_ECB_ENCRYPT_MODE
        && (mode & AES_ALL_MODES) != AES_ECB_DECRYPT_MODE)
            aes_setiv(iv, ivMode);

        blocks = (blockCount >= 0xFFFF) ? 0xFFFF : blockCount;

        //Save the last block for the next decryption CBC batch's iv
        if((mode & AES_ALL_MODES) == AES_CBC_DECRYPT_MODE)
        {
            memcpy(iv, src + (blocks - 1) * AES_BLOCK_SIZE, AES_BLOCK_SIZE);
            aes_change_ctrmode(iv, AES_INPUT_BE | AES_INPUT_NORMAL, ivMode);
        }

        //Process the current batch
        aes_batch(dst, src, blocks);

        //Save the last block for the next encryption CBC batch's iv
        if((mode & AES_ALL_MODES) == AES_CBC_ENCRYPT_MODE)
        {
            memcpy(iv, dst + (blocks - 1) * AES_BLOCK_SIZE, AES_BLOCK_SIZE);
            aes_change_ctrmode(iv, AES_INPUT_BE | AES_INPUT_NORMAL, ivMode);
        }

        //Advance counter for CTR mode
        else if((mode & AES_ALL_MODES) == AES_CTR_MODE)
            aes_advctr(iv, blocks, ivMode);

        src += blocks * AES_BLOCK_SIZE;
        dst += blocks * AES_BLOCK_SIZE;
        blockCount -= blocks;
    }
}

static void sha_wait_idle()
{
    while(*REG_SHA_CNT & 1);
}

static void sha(void *res, const void *src, u32 size, u32 mode)
{
    sha_wait_idle();
    *REG_SHA_CNT = mode | SHA_CNT_OUTPUT_ENDIAN | SHA_NORMAL_ROUND;

    const u32 *src32 = (const u32 *)src;
    int i;
    while(size >= 0x40)
    {
        sha_wait_idle();
        for(i = 0; i < 4; ++i)
        {
            *REG_SHA_INFIFO = *src32++;
            *REG_SHA_INFIFO = *src32++;
            *REG_SHA_INFIFO = *src32++;
            *REG_SHA_INFIFO = *src32++;
        }

        size -= 0x40;
    }

    sha_wait_idle();
    memcpy((void *)REG_SHA_INFIFO, src32, size);

    *REG_SHA_CNT = (*REG_SHA_CNT & ~SHA_NORMAL_ROUND) | SHA_FINAL_ROUND;

    while(*REG_SHA_CNT & SHA_FINAL_ROUND);
    sha_wait_idle();

    u32 hashSize = SHA_256_HASH_SIZE;
    if(mode == SHA_224_MODE)
        hashSize = SHA_224_HASH_SIZE;
    else if(mode == SHA_1_MODE)
        hashSize = SHA_1_HASH_SIZE;

    memcpy(res, (void *)REG_SHA_HASH, hashSize);
}

/*****************************************************************/

static u8 __attribute__((aligned(4))) nandCtr[AES_BLOCK_SIZE];
static u8 nandSlot;
static u32 fatStart;
__attribute__((aligned(4))) const u8 key2s[5][AES_BLOCK_SIZE] = {
    {0x42, 0x3F, 0x81, 0x7A, 0x23, 0x52, 0x58, 0x31, 0x6E, 0x75, 0x8E, 0x3A, 0x39, 0x43, 0x2E, 0xD0},
    {0xA5, 0x25, 0x87, 0x11, 0x8F, 0x42, 0x9F, 0x3D, 0x65, 0x1D, 0xDD, 0x58, 0x0B, 0x6D, 0xF2, 0x17},
    {0x65, 0x29, 0x3E, 0x12, 0x56, 0x0C, 0x0B, 0xD1, 0xDD, 0xB5, 0x63, 0x1C, 0xB6, 0xD9, 0x52, 0x75},
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3B, 0xF5, 0xF6},
    {0x08, 0x24, 0xD3, 0xCB, 0x4A, 0xE9, 0x4D, 0x62, 0x4D, 0xAA, 0x52, 0x60, 0x47, 0xC5, 0x93, 0x94}
},
                                     devKey2s[2][AES_BLOCK_SIZE] = {
    {0xFF, 0x77, 0xA0, 0x9A, 0x99, 0x81, 0xE9, 0x48, 0xEC, 0x51, 0xC9, 0x32, 0x5D, 0x14, 0xEC, 0x25},
    {0x59, 0x5B, 0x98, 0x5B, 0xD7, 0x74, 0x58, 0x7F, 0x89, 0x30, 0x85, 0x70, 0xD6, 0x24, 0x49, 0x1E}
};

void getNandCtr(void)
{
    __attribute__((aligned(4))) u8 cid[AES_BLOCK_SIZE],
                                   shaSum[SHA_256_HASH_SIZE];

    sdmmc_get_cid(1, (u32 *)cid);
    sha(shaSum, cid, sizeof(cid), SHA_256_MODE);
    memcpy(nandCtr, shaSum, sizeof(nandCtr));
}

int ctrNandInit(void)
{
    getNandCtr();

    if(ISN3DS)
    {
        __attribute__((aligned(4))) u8 keyY0x5[AES_BLOCK_SIZE] = {0x4D, 0x80, 0x4F, 0x4E, 0x99, 0x90, 0x19, 0x46, 0x13, 0xA2, 0x04, 0xAC, 0x58, 0x44, 0x60, 0xBE};
        aes_setkey(0x05, keyY0x5, AES_KEYY, AES_INPUT_BE | AES_INPUT_NORMAL);

        nandSlot = 0x05;
        fatStart = 0x5CAD7;
    }
    else
    {
        nandSlot = 0x04;
        fatStart = 0x5CAE5;
    }
	return 0;
}

int ctrNandRead(u32 sector, u32 sectorCount, u8 *outbuf)
{
    __attribute__((aligned(4))) u8 tmpCtr[sizeof(nandCtr)];
    memcpy(tmpCtr, nandCtr, sizeof(nandCtr));
    aes_advctr(tmpCtr, ((sector + fatStart) * 0x200) / AES_BLOCK_SIZE, AES_INPUT_BE | AES_INPUT_NORMAL);

    //Read from NAND
    int result = sdmmc_nand_readsectors(sector + fatStart, sectorCount, outbuf);

    //Decrypt
    aes_use_keyslot(nandSlot);
    aes(outbuf, outbuf, sectorCount * 0x200 / AES_BLOCK_SIZE, tmpCtr, AES_CTR_MODE, AES_INPUT_BE | AES_INPUT_NORMAL);

    return result;
}

void readFirm0(u8 *outbuf, u32 size)
{
    __attribute__((aligned(4))) u8 tmpCtr[sizeof(nandCtr)];
    memcpy(tmpCtr, nandCtr, sizeof(nandCtr));
    aes_advctr(tmpCtr, 0x0B130000 / AES_BLOCK_SIZE, AES_INPUT_BE | AES_INPUT_NORMAL);

    //Read from NAND
    sdmmc_nand_readsectors(0x0B130000 / 0x200, size / 0x200, outbuf);

    //Decrypt
    aes_use_keyslot(0x06);
    aes(outbuf, outbuf, size / AES_BLOCK_SIZE, tmpCtr, AES_CTR_MODE, AES_INPUT_BE | AES_INPUT_NORMAL);
}

void readFirm1(u8 *outbuf, u32 size)
{
    __attribute__((aligned(4))) u8 tmpCtr[sizeof(nandCtr)];
    memcpy(tmpCtr, nandCtr, sizeof(nandCtr));
    aes_advctr(tmpCtr, 0x0B530000 / AES_BLOCK_SIZE, AES_INPUT_BE | AES_INPUT_NORMAL);

    //Read from NAND
    sdmmc_nand_readsectors(0x0B530000 / 0x200, size / 0x200, outbuf);

    //Decrypt
    aes_use_keyslot(0x06);
    aes(outbuf, outbuf, size / AES_BLOCK_SIZE, tmpCtr, AES_CTR_MODE, AES_INPUT_BE | AES_INPUT_NORMAL);
}

void writeFirm(u8 *inbuf, bool isFirm1, u32 size)
{
    u32 offset = isFirm1 ? 0x0B530000 : 0x0B130000;
    __attribute__((aligned(4))) u8 tmpCtr[sizeof(nandCtr)];
    memcpy(tmpCtr, nandCtr, sizeof(nandCtr));
	aes_advctr(tmpCtr, offset / AES_BLOCK_SIZE, AES_INPUT_BE | AES_INPUT_NORMAL);
	aes_use_keyslot(0x06);
	u8 buf[0x200];
	
	for(int i=0;i<size;i+=0x200){
		//aes_advctr(tmpCtr, (offset +i) / AES_BLOCK_SIZE, AES_INPUT_BE | AES_INPUT_NORMAL);

		//Encrypt
		aes(buf, inbuf + i, 0x200 / AES_BLOCK_SIZE, tmpCtr, AES_CTR_MODE, AES_INPUT_BE | AES_INPUT_NORMAL);

		//Write to NAND
		sdmmc_nand_writesectors((offset + i) / 0x200, 1, buf);
	}

}

void setupKeyslot0x11(const void *otp)
{
    __attribute__((aligned(4))) u8 shasum[SHA_256_HASH_SIZE];

    //If booting via A9LH, use the leftover contents of the SHA register
    if(ISA9LH) memcpy(shasum, (void *)REG_SHA_HASH, sizeof(shasum));

    //Otherwise, calculate the otp.bin hash
    else sha(shasum, otp, 0x90, SHA_256_MODE);

    //Set keyX and keyY
    aes_setkey(0x11, shasum, AES_KEYX, AES_INPUT_BE | AES_INPUT_NORMAL);
    aes_setkey(0x11, shasum + AES_BLOCK_SIZE, AES_KEYY, AES_INPUT_BE | AES_INPUT_NORMAL);
}

void generateSector(u8 *keySector, u32 mode)
{
    //Inject key2
    switch(mode)
    {
        case 0:
            memcpy(keySector + AES_BLOCK_SIZE, !ISDEVUNIT ? key2s[1] : devKey2s[1], AES_BLOCK_SIZE);
            break;
        case 1:
            memcpy(keySector + AES_BLOCK_SIZE, keySector, AES_BLOCK_SIZE);
            return;
        case 2:
            memcpy(keySector + AES_BLOCK_SIZE, !ISDEVUNIT ? key2s[0] : devKey2s[0], AES_BLOCK_SIZE);
            break;
    }

    //Encrypt key sector
    aes_use_keyslot(0x11);
    for(u32 i = 0; i < 32; i++)
        aes(keySector + (AES_BLOCK_SIZE * i), keySector + (AES_BLOCK_SIZE * i), 1, NULL, AES_ECB_ENCRYPT_MODE, 0);
}

void getSector(u8 *keySector)
{
    //Read keysector from NAND
    sdmmc_nand_readsectors(0x96, 1, keySector);

    if(!ISA9LH && !ISDEVUNIT) return;

    //Decrypt key sector
    aes_use_keyslot(0x11);
    for(u32 i = 0; i < 32; i++)
        aes(keySector + (AES_BLOCK_SIZE * i), keySector + (AES_BLOCK_SIZE * i), 1, NULL, AES_ECB_DECRYPT_MODE, 0);
}

bool verifyHash(const void *data, u32 size, const u8 *hash)
{
    __attribute__((aligned(4))) u8 shasum[SHA_256_HASH_SIZE];
    sha(shasum, data, size, SHA_256_MODE);

    return memcmp(shasum, hash, sizeof(shasum)) == 0;
}

u32 decryptExeFs(Cxi *cxi)
{
    u32 exeFsSize = 0;

    if(memcmp(cxi->ncch.magic, "NCCH", 4) != 0) return exeFsSize;

    u8 *exeFsOffset = (u8 *)cxi + (cxi->ncch.exeFsOffset + 1) * 0x200;
    exeFsSize = (cxi->ncch.exeFsSize - 1) * 0x200;
    __attribute__((aligned(4))) u8 ncchCtr[AES_BLOCK_SIZE] = {0};

    for(u32 i = 0; i < 8; i++)
        ncchCtr[7 - i] = cxi->ncch.partitionId[i];
    ncchCtr[8] = 2;

    aes_setkey(0x2C, cxi, AES_KEYY, AES_INPUT_BE | AES_INPUT_NORMAL);
    aes_advctr(ncchCtr, 0x200 / AES_BLOCK_SIZE, AES_INPUT_BE | AES_INPUT_NORMAL);
    aes_use_keyslot(0x2C);
    aes(cxi, exeFsOffset, exeFsSize / AES_BLOCK_SIZE, ncchCtr, AES_CTR_MODE, AES_INPUT_BE | AES_INPUT_NORMAL);

    if(memcmp(cxi, "FIRM", 4) != 0) exeFsSize = 0;

    return exeFsSize;
}

void setupKeyslots(void)
{
    //Setup 0x24 KeyY
    __attribute__((aligned(4))) static const u8 keyY0x24[AES_BLOCK_SIZE] = {0x74, 0xCA, 0x07, 0x48, 0x84, 0xF4, 0x22, 0x8D, 0xEB, 0x2A, 0x1C, 0xA7, 0x2D, 0x28, 0x77, 0x62};
    aes_setkey(0x24, keyY0x24, AES_KEYY, AES_INPUT_BE | AES_INPUT_NORMAL);

    //Setup 0x25 KeyX and 0x2F KeyY
    __attribute__((aligned(4))) static const u8 keyX0x25s[2][AES_BLOCK_SIZE] = {
        {0xCE, 0xE7, 0xD8, 0xAB, 0x30, 0xC0, 0x0D, 0xAE, 0x85, 0x0E, 0xF5, 0xE3, 0x82, 0xAC, 0x5A, 0xF3},
        {0x81, 0x90, 0x7A, 0x4B, 0x6F, 0x1B, 0x47, 0x32, 0x3A, 0x67, 0x79, 0x74, 0xCE, 0x4A, 0xD7, 0x1B}
    },
                                                keyY0x2Fs[2][AES_BLOCK_SIZE] = {
        {0xC3, 0x69, 0xBA, 0xA2, 0x1E, 0x18, 0x8A, 0x88, 0xA9, 0xAA, 0x94, 0xE5, 0x50, 0x6A, 0x9F, 0x16},
        {0x73, 0x25, 0xC4, 0xEB, 0x14, 0x3A, 0x0D, 0x5F, 0x5D, 0xB6, 0xE5, 0xC5, 0x7A, 0x21, 0x95, 0xAC}
    };

    aes_setkey(0x25, keyX0x25s[ISDEVUNIT ? 1 : 0], AES_KEYX, AES_INPUT_BE | AES_INPUT_NORMAL);
    aes_setkey(0x2F, keyY0x2Fs[ISDEVUNIT ? 1 : 0], AES_KEYY, AES_INPUT_BE | AES_INPUT_NORMAL);

    if(ISN3DS) 
    {
        //Setup 0x05 KeyY
        __attribute__((aligned(4))) static const u8 keyY0x5[AES_BLOCK_SIZE] =  {0x4D, 0x80, 0x4F, 0x4E, 0x99, 0x90, 0x19, 0x46, 0x13, 0xA2, 0x04, 0xAC, 0x58, 0x44, 0x60, 0xBE};
        aes_setkey(0x05, keyY0x5,  AES_KEYY, AES_INPUT_BE | AES_INPUT_NORMAL);
    }

    //Setup TWL keys
    //twlConsoleInfoInit();

    //Set 0x11 keyslot
    __attribute__((aligned(4))) static const u8 key1s[2][AES_BLOCK_SIZE] = {
        {0x07, 0x29, 0x44, 0x38, 0xF8, 0xC9, 0x75, 0x93, 0xAA, 0x0E, 0x4A, 0xB4, 0xAE, 0x84, 0xC1, 0xD8},
        {0xA2, 0xF4, 0x00, 0x3C, 0x7A, 0x95, 0x10, 0x25, 0xDF, 0x4E, 0x9E, 0x74, 0xE3, 0x0C, 0x92, 0x99}
    },
                                                key2s[2][AES_BLOCK_SIZE] = {
        {0x42, 0x3F, 0x81, 0x7A, 0x23, 0x52, 0x58, 0x31, 0x6E, 0x75, 0x8E, 0x3A, 0x39, 0x43, 0x2E, 0xD0},
        {0xFF, 0x77, 0xA0, 0x9A, 0x99, 0x81, 0xE9, 0x48, 0xEC, 0x51, 0xC9, 0x32, 0x5D, 0x14, 0xEC, 0x25}
    };


    __attribute__((aligned(4))) u8 keyBlocks[2][AES_BLOCK_SIZE] = {
        {0xA4, 0x8D, 0xE4, 0xF1, 0x0B, 0x36, 0x44, 0xAA, 0x90, 0x31, 0x28, 0xFF, 0x4D, 0xCA, 0x76, 0xDF},
        {0xDD, 0xDA, 0xA4, 0xC6, 0x2C, 0xC4, 0x50, 0xE9, 0xDA, 0xB6, 0x9B, 0x0D, 0x9D, 0x2A, 0x21, 0x98}
    },                             decKey[AES_BLOCK_SIZE];

    //Initialize Key 0x18    
    aes_setkey(0x11, key1s[ISDEVUNIT ? 1 : 0], AES_KEYNORMAL, AES_INPUT_BE | AES_INPUT_NORMAL);
    aes_use_keyslot(0x11);
    aes(decKey, keyBlocks[0], 1, NULL, AES_ECB_DECRYPT_MODE, 0);
    aes_setkey(0x18, decKey, AES_KEYX, AES_INPUT_BE | AES_INPUT_NORMAL);

    //Initialize Key 0x19-0x1F
    aes_setkey(0x11, key2s[ISDEVUNIT ? 1 : 0], AES_KEYNORMAL, AES_INPUT_BE | AES_INPUT_NORMAL);
    aes_use_keyslot(0x11);
    for(u8 slot = 0x19; slot < 0x20; slot++, keyBlocks[1][0xF]++)
    {
        aes(decKey, keyBlocks[1], 1, NULL, AES_ECB_DECRYPT_MODE, 0);
        aes_setkey(slot, decKey, AES_KEYX, AES_INPUT_BE | AES_INPUT_NORMAL);
    }
}
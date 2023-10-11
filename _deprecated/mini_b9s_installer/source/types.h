/*
*   types.h
*/

#pragma once

#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>

//Common data types
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
typedef int64_t s64;
typedef volatile u8 vu8;
typedef volatile u16 vu16;
typedef volatile u32 vu32;
typedef volatile u64 vu64;

#define CFG_UNITINFO   (*(vu8  *)0x10010010)
#define PDN_MPCORE_CFG (*(vu32 *)0x10140FFC)
#define PDN_SPI_CNT    (*(vu32 *)0x101401C0)

#define ISN3DS    (PDN_MPCORE_CFG == 7)
#define ISDEVUNIT (CFG_UNITINFO != 0)
#define ISA9LH    (!PDN_SPI_CNT)

#include "3dsheaders.h"
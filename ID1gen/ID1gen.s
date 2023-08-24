	.arm
	.text
	.cpu arm946e-s
	.arch armv5te

#define GARBAGE 0x44444444

.global _start
start:
				blx .+4
				@adr r12, thumb_section+1			@this is legal? lol, whatever we save 4 bytes
				@bx r12
				
.thumb
thumb_section:
				ldr r1, [sp,#0x44]                    	@colon_slash that cannot be displayed in PC folder but exists in stack at fixed offset
				ldr r0, =0x080A9000
				mov sp, r0
				@mov r0, sp		      		@this  d9000
				str r1, [r5,#(colon_slash-start+0x1c)]  @lets overwrite 00440044 below with :/ as a workaround
				adr r1, filename
				mov r2, #1                            	@openflag
						
				ldr r3, =0x0805A071 @fopen 11.17 (thumb)
				blx r3
							
				mov r0, sp          @this
				mov r1, r11         @ read_size
				add r2, sp, #0x3fc  @ dest
				mov r7, r2          @ save dest for later branch
				mov r3, r8 	    @ size

				ldr r4, =0x0804ce99 @fread 11.17 (thumb) @804ce5c (doubles as size arg)
				blx r4
				

				blx r7
				@.byte 0x48, 0x48
				@.word 0x480048 @paddings
				@bkpt
.pool			

filename:	
				.word 0x640073,0x63006d @ "sdmc"
colon_slash:
				.word 0x080A9000 @ ":/" during runtime anyway
end_of_all_things:
				.word 0x390062 @ "b9" our two letter filename to confuse the masses. hopefully next char is null, as Black Cat testifies.
				
				@if we need more space, we can pool the FS addresses after sdmc:/ and use those as filenames, saving 4 bytes at the expense of style.




/*
this:
.fill 16,4,0
*/



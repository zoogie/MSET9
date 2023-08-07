# MSET9

## Thanks 
- Luigoalma for some asm help in ID1gen!

## What it is
This is an ARM9 primary exploit for 3DS that can be launched with only filename data added to the inserted SD card. 

## How does it work
When FS_EnumerateExtData is called by MSET (System Settings) to parse 3DS extdata IDs for Data Managment, a file that starts with 8 hex digits can crash ARM9 if placed directly inside the extdata directory. It can crash in various ways based on subtleties in the way the user triggers the crash event.<br>

While mostly leading to null derefs, in one specific context, ARM9 jumps directly to the ID1 string being held nearby in ARM9 memory. Serendipitously, the 3DS doesn't discern what characters are used for the ID1 directory name on the SD, only requiring exactly 32 chars. This allows the attacker to insert arm instructions into the unicode ID1 dirname and take control of ARM9, and thus, full control of the 3DS.

## Can I do it?
-- You need an old3ds, latest firm (new3ds will be coming soon)
-- A spare SD card you can format to blank (this will likely change too, I just don't want people screwing their main sd card up in these early days).
-- Windows PC (this should be expanded after the exploit leaves beta)

## Directions
In release archive. It may seem long and complex but it really isn't that bad. People who have trouble following directions will struggle though.<br>
There's a lot of room for improvement regarding ease-of-use.

## FAQ

Q: This installs boot9strap and writes to NAND?<br>
A: Yes! What else ya gonna do with ARM9 control, a9lh? pastaCFW? :p<br>
Q: That sounds dangerous, Zoogie!<br>
A: Yeah, it kinda is but the scene's been doing this dangerous stuff for years. Just sit out the beta phase if concerned.<br>
Q: Wait, why are you sending my 3DS online with the browser?<br>
A: The ID1 stage0 payload only allows for 0x40 bytes of instructions. Very small. Using the browser to "spray" fcram with a stage1 payload is a practical solution. Still, I'd like to add a completely offline stage1 solution in the future.<br>
Q: So you hacked the browser again Zoogie, nice job!<br>
A: No, no, no, it's just being used for data transport.<br>
Q: That file that triggers the exploit ... it kinda looks like an fcram address?<br>
A: It is. Another convenient fact of that file (besides triggering the overall crash) is that the first 8 chars of that hex filename are converted to a u32 that happens to exist 0x4c past SP, so I can use it in stage0 to jump to the fcram target of my choice without recompiling the ID1 mini payload. It's optional to do that though. I could instead call it F00D43D5 in tribute to a certain other recently RIP'd exploit :p.<br>
Q: You suggested in the hack explanation above that FS_EnumerateExtData is the responsible function for allowing the crash in MSET/ARM9, could this be called in userland homebrew to take over ARM9?<br>
A: Maybe? I briefly played around with this very idea, but was unable to find a crash context that I could control, unlike the pre-userland method described above. Maybe this could be an exercise for the dedicated user to explore and flesh out this potential variant of MSET9! It could be useful down the line.<br>
Fun fact: The 8 digit hex file, if left in extdata, will also crash FBI when selecting the "Ext Save Data" option in its main menu. It's the only homebrew I know that calls FS_EnumerateExtData.
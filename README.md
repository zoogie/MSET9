# MSET9

## Thanks 
- Luigoalma for some asm help in ID1gen!
- Aspargas2 (the Black Cat) for asm help in ID1gen as well!
- TuxSH for some good suggestions and advice!

## What it is
This is an ARM9 primary exploit for 3DS that can be launched with only filename data added to the inserted SD card. 

## How does it work
When FS_EnumerateExtData is called by MSET (System Settings) to parse 3DS extdata IDs for Data Managment, a file that starts with 8 hex digits can crash ARM9 if placed directly inside the extdata directory. It can crash in various ways based on subtleties in the way the user triggers the crash event.<br>

While mostly leading to null derefs, in one specific context, ARM9 jumps directly to the ID1 string being held nearby in ARM9 memory. By chance, the 3DS doesn't discern what characters are used for the ID1 directory name on the SD, only requiring exactly 32 chars. This allows the attacker to insert arm instructions into the unicode ID1 dirname and take control of ARM9, and thus, full control of the 3DS.

## Can I do it?
-- You need an old3ds, latest firm (new3ds will be coming at some point)<br>
-- A spare SD card you can format to blank (this will likely change too, I just don't want people screwing their main sd card up in these early days).<br>
-- Windows/Linux PC (this might be expanded to MAC at some point)<br>

## Directions
In release archive. It may seem long and complex but it really isn't that bad. People who have trouble following directions will struggle though.<br>
There's a lot of room for improvement regarding ease-of-use.

## Troubleshooting
- [mset9.py shows error ".../title.db doesn't exist on sd card"?] Inside sdmc:/Nintendo 3DS/ID0/ID1/dbs, create empty files title.db and import.db. You need to create the dbs folder first. Now go to System Settings -> Data Management -> Nintendo 3DS -> Software and say yes to the prompts to build your database files. Now redo everything from the start.

## FAQ

Q: This installs boot9strap and writes to NAND?<br>
A: Yes! What else ya gonna do with ARM9 control, a9lh? pastaCFW? :p<br>
Q: That sounds dangerous, Zoogie!<br>
A: Yeah, it kinda is but the scene's been doing this dangerous stuff for years. Just sit out the beta phase if concerned.<br>
Q: That file that triggers the exploit (002F003A.txt) ... it kinda looks like ... some virtual address, huh?<br>
A: It's the characters ":/", something we can't display in a typical file/folder name. A convenient fact of that file (besides triggering the overall crash) is that the first 8 chars of that hex filename are converted to a u32 that happens to exist 0x44 past SP, so I can use it to plug in the missing chars in the payload filepath "sdmc??b9", and keep the PC's OS happy.<br>
Q: You suggested in the hack explanation above that FS_EnumerateExtData is the responsible function for allowing the crash in MSET/ARM9, could this be called in userland homebrew to take over ARM9?<br>
A: Maybe? I briefly played around with this very idea, but was unable to find a crash context that I could control, unlike the pre-userland method described above. Maybe this could be an exercise for the dedicated user to explore and flesh out this potential variant of MSET9! It could be useful down the line.<br>
Fun fact: The 8 digit hex file, if left in extdata, will also crash FBI when selecting the "Ext Save Data" option in its main menu. It's the only homebrew I know that calls FS_EnumerateExtData.
Q: Why doesn't this work on MAC?<br>
A: Because it refuses to render the following unicode craziness: ￿﫿餑䠇䚅敩ꄈ∁䬅䞘䙨䙙꫿ᰗ䙃䰃䞠䞸退ࠊꁱࠅ캙ࠄsdmc退ࠊb9<br>
( ͡° ͜ʖ ͡°)<br>
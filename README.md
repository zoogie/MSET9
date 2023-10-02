# MSET9

## Thanks 
- Luigoalma for some asm help in ID1gen!
- Aspargas2 (the Black Cat) for asm help in ID1gen as well!
- TuxSH for usr2arm9ldr and some good advice!

[MSET9 in action](https://zoogie.github.io/web/m9/(%20%CD%A1%C2%B0%20%CD%9C%CA%96%20%CD%A1%C2%B0).webm)

## What it is
This is an ARM9 primary exploit for 3DS that can be launched with only filename data added to the inserted SD card. 

## How does it work
When FS_EnumerateExtData is called by MSET (System Settings) to parse 3DS extdata IDs for Data Managment, a file that starts with 8 hex digits can crash ARM9 if placed directly inside the extdata directory. It can crash in various ways based on subtleties in the way the user triggers the crash event.<br>

While mostly leading to null derefs, in one specific context, ARM9 jumps directly to the ID1 string being held nearby in ARM9 memory. By chance, the 3DS doesn't discern what characters are used for the ID1 directory name on the SD, only requiring exactly 32 chars. This allows an attacker to insert arm instructions into the unicode ID1 dirname and take control of ARM9, and thus, full control of the 3DS.

## Can I do it?
-- You need an old3ds 11.8-11.17, any region (new3ds will be coming at some point)<br>
-- A USB to SD reader<br>
-- Windows/Linux PC (this might be expanded to MAC at some point)<br>

## Directions
In release archive. It may seem long and complex but it really isn't that bad. People who have trouble following directions will struggle though.<br>

## Troubleshooting
- [mset9.py shows error ".../title.db doesn't exist on sd card"?] Inside sdmc:/Nintendo 3DS/ID0/ID1/dbs, create empty files title.db and import.db. You need to create the dbs folder first. Now go to System Settings -> Data Management -> Nintendo 3DS -> Software and say yes to the prompts to build your database files. Now redo everything from the start.
- [Swirling System Settings loop] This is just a general crash of arm9. Did you follow the instructions.txt EXACTLY? Are you running an old3ds 11.8-11.17?
- [Nothing happens when I reinstert card - just shows mii maker icon] Did you try option 2 on mset9.py on step 6? Go back to step
- [Still can't get it to work] In some stubborn cases, it might be better to just start fresh with a spare blank SD card. For that, follow these steps:
1. Format the spare SD card with SD formatter.<br>
2. Put SD card into 3DS and turn on, wait for menu data to format automatically.<br>
3. Go to Mii Maker and launch it, wait for extdata format, then exit. Turn off 3DS.<br>
4. Take out SD card, put in computer and create the following two empty files (and dbs folder if needed):<br>
sdmc:/Nintendo 3DS/aaaabbbbccccdddd1111222233334444/aaaabbbbccccdddd1111222233334444/dbs/title.db<br>
sdmc:/Nintendo 3DS/aaaabbbbccccdddd1111222233334444/aaaabbbbccccdddd1111222233334444/dbs/import.db<br>
(the long hex number folder names above are just examples, yours will be different)<br>
5. Put SD card back in the 3DS and go to System Settings -> Data Management -> Nintendo 3DS -> Software and agree to the prompts to rebuild the database.<br>
6. Proceed to step 1 on instructions.txt.<br>

## FAQ

Q: This installs boot9strap and writes to NAND?<br>
  A: Yes! What else ya gonna do with ARM9 control, a9lh? pastaCFW? sketchy tetris clones" :p<br>
Q: That sounds dangerous, Zoogie!<br>
  A: Yeah, it kinda is but the scene's been doing this dangerous stuff for years. Just sit out the beta phase if concerned.<br>
Q: What happens if I fail to uninstall the exploit when I'm done?<br>
  A: You'll have trouble launching previously installed titles, in addition to random crashes in FBI and System Settings. So make sure to clean up the exploit! (option 4 in the mset9.py menu does this)<br>
  
(the rest of this is more FYI than anything important)<br>

Q: That file that triggers the exploit (002F003A.txt) ... it kinda looks like ... some virtual address, huh?<br>
  A: It's the characters ":/", something we can't display in a typical file/folder name. A convenient fact of that file (besides triggering the overall crash) is that the first 8 chars of that hex filename are converted to a u32 that happens to exist 0x44 past SP, so I can use it to plug in the missing chars in the payload filepath "sdmc??b9", and keep the PC's OS happy.<br>
Q: You suggested in the hack explanation above that FS_EnumerateExtData is the responsible function for allowing the crash in MSET/ARM9, could this be called in userland homebrew to take over ARM9?<br>
  A: Maybe? I briefly played around with this very idea, but was unable to find a crash context that I could control, unlike the pre-userland method MSET9 is. Maybe this could be an exercise for the dedicated user to explore and flesh out this potential variant of MSET9! It could be useful down the line.<br>
  Fun fact: The 8 digit hex file, if left in extdata, will also crash FBI when selecting the "Ext Save Data" option in its main menu. It's the only homebrew I know that calls FS_EnumerateExtData.<br>
Q: You shortened SafeB9SInstaller.bin to SafeB9S.bin, why?
  A: Keeps FAT's 8.3 filename standard which avoids Long File Names, and thus enables significant space savings in the FatFs library. "B9" is also used for the same reason albeit not FatFs related. Small code footprint is of paramount importance everywhere in this exploit.<br>
Q: Why doesn't this work on MAC?<br>
  A: Because it refuses to render the following unicode craziness: ￿﫿餑䠇䚅敩ꄈ∁䬅䞘䙨䙙꫿ᰗ䙃䰃䞠䞸退ࠊꁱࠅ캙ࠄsdmc退ࠊb9<br>
  ( ͡° ͜ʖ ͡°)<br>

## Additional Thanks
These are repos containing homebrew binaries included in the release archive. Many thanks to the authors.<br>
https://github.com/LumaTeam/Luma3DS<br>
https://github.com/d0k3/GodMode9<br>
https://github.com/d0k3/SafeB9SInstaller (renamed SafeB9S.bin)<br>
https://github.com/devkitPro/3ds-hbmenu<br>
https://github.com/SciresM/boot9strap<br>
https://github.com/Steveice10/FBI<br>

# MSET9

## Thanks 
- Luigoalma for some asm help in ID1gen!
- Aspargas2 (the Black Cat) for asm help in ID1gen as well!
- TuxSH for [usr2arm9ldr](https://github.com/TuxSH/usr2arm9ldr) and some good advice!
- ToxicAven for substantial mset9.py improvements!
- Danny8376 for adding macOS support!

[MSET9 in action](https://zoogie.github.io/web/m9/(%20%CD%A1%C2%B0%20%CD%9C%CA%96%20%CD%A1%C2%B0).webm)

## What it is
This is an ARM9 primary exploit for 3DS that can be launched with only filename data added to the inserted SD card. 

## How does it work
In the implementation for FSPXI:EnumerateExtSaveData (called by MSET to parse 3DS extdata IDs for Data Management), the return value of the process9 internal function call to open a directory (when enumerating contents of the extdata directory) was not checked. Therefore, if the call fails, an uninitialised pointer on stack will be used for a vtable call.<br>

As such, a <em>file</em> (instead of an expected folder) that starts with 8 hex digits can crash process9 if placed directly inside the extdata directory. It can crash in various ways based on subtle differences in the way the user triggers the crash event.<br>

While mostly leading to null derefs, in one specific context, process9 jumps directly to an ID1 string being held in ARM9 memory. Surprisingly, the 3DS doesn't discern what characters are used for the ID1 directory name on the SD, only requiring exactly 32 chars. This allows the attacker to insert arm instructions into the unicode ID1 dirname and take control of the ARM9, and thus, full control of the 3DS.<br>
Source: [3Dbrew](https://www.3dbrew.org/wiki/3DS_System_Flaws#Process9)

## Can I do it?
-- You need a 3ds 11.4-11.17, any region (probably, haven't tested them all)<br>
-- A USB to SD reader<br>
-- Windows/MAC/Linux PC (this might be expanded to chromeOS and/or Android at some point, if possible)<br>

## Directions
In release archive or, preferably, [3DS Hacks Guide- MSET9](https://3ds.hacks.guide/installing-boot9strap-(mset9).html).<br>

## Troubleshooting
https://3ds.hacks.guide/troubleshooting-mset9.html

## FAQ

- Q: This installs boot9strap and writes to NAND?<br>
  A: Yes! What else ya gonna do with ARM9 control, a9lh? pastaCFW? sketchy tetris clones" :p
- Q: That sounds dangerous, Zoogie!<br>
  A: Yeah, it kinda is but the scene's been doing this dangerous stuff for years. Just sit out the beta phase if concerned.
- Q: What happens if I fail to uninstall the exploit when I'm done?<br>
  A: You'll have trouble launching previously installed titles, in addition to random crashes in FBI and System Settings. So make sure to clean up the exploit! (option 4 in the mset9.py menu does this)
- Q: How to compile?<br>
  A: Look up fopen/fread offsets in offsets.txt for your firmware and model of 3ds. Copy over the existing fopen/fread addresses in id1gen/id1gen.s with the addresses you picked. In root, run build.bat. Take the long hex string in out/haxID1_output.txt and place it in "encodedId1s" (pick one) in MSET9_installer_script/mset9.py. A decoded ID1 dir will also be in out/<32 chars of whatever>.
  
(the rest of this is more FYI than anything important)

- Q: That file that triggers the exploit (002F003A.txt) ... it kinda looks like ... some virtual address, huh?<br>
  A: It's the characters ":/", something we can't display in a typical file/folder name. A convenient fact of that file (besides triggering the overall crash) is that the first 8 chars of that hex filename are converted to a u32 that happens to exist 0x44 past SP, so I can use it to plug in the missing chars in the payload filepath "sdmc??b9", and keep the PC's OS happy.
- Q: You suggested in the hack explanation above that FS_EnumerateExtData is the responsible function for allowing the crash in MSET/ARM9, could this be called in userland homebrew to take over ARM9?<br>
  A: Maybe? I briefly played around with this very idea, but was unable to find a crash context that I could control, unlike the pre-userland method MSET9 is. Maybe this could be an exercise for the dedicated user to explore and flesh out this potential variant of MSET9! It could be useful down the line.<br>
  Fun fact: The 8 digit hex file, if left in extdata, will also crash FBI when selecting the "Ext Save Data" option in its main menu. It's the only homebrew I know that calls FS_EnumerateExtData.
- Q: You shortened SafeB9SInstaller.bin to SafeB9S.bin, why?<br>
  A: Keeps FAT's 8.3 filename standard which avoids Long File Names, and thus enables significant space savings in the FatFs library. "B9" is also used for the same reason albeit not FatFs related. Small code footprint is of paramount importance everywhere in this exploit.
- Q: Why does this only work on 11.4+?<br>
  A: It actually works 3.0+, but those old firms don't need to be supported due to the big guide using other exploits for that range.
- Q: What happened on 3.0 that made mset9 work?<br>
  A: On the 3.0 native firm refactor, Nintendo introduced a regression that allows the exploit to work (an unchecked function return).
- Q: Why is supporting some non-3ds OS's difficult?<br>
  A: Because they don't like the funky unicode craziness:<br> ￿﫿餑䠇䚅敩ꄈ∁䬅䞘䙨䙙꫿ᰗ䙃䰃䞠䞸退ࠊꁱࠅ캙ࠄsdmc退ࠊb9<br>
  ( ͡° ͜ʖ ͡°)

## Additional Thanks
These are repos containing homebrew binaries included in the release archive. Many thanks to the authors.<br>
https://github.com/LumaTeam/Luma3DS<br>
https://github.com/d0k3/GodMode9<br>
https://github.com/d0k3/SafeB9SInstaller (renamed SafeB9S.bin)<br>
https://github.com/devkitPro/3ds-hbmenu<br>
https://github.com/SciresM/boot9strap<br>
https://github.com/Steveice10/FBI<br>

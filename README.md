# openmw-snapshot-tool

License: GPLv3 (see LICENSE for more information)

Author: DandyTush

## Motivation

This tool is useful if you:
1. Use one machine to configure mods, and a different machine to play the game
2. Want to experiment with new mods without worrying about breaking a working set
3. Like to meticulously back up everything
4. Want to keep your mods synced between your devices so your save filse are always valid
5. Want to easily switch between many different installs, like vanilla Morrowind, Starwind, a modlist for your favorite tes3-mp server, etc.

## Background

As of version 0.48, OpenMW generally deals with one installation at a time, assuming that all of your mods are installed in one place. There is a concept of a "Content List" in the launcher, but this is just a way to toggle a subset of the mods you have installed.

There is also a concept of a "portable install" in OpenMW in which you can point the launcher to different conguration and data directories. `openmw-snapshot-tool` complements and can likely utilize this concept.

Some tools like Vortex or [Mod Organizer 2](https://github.com/ModOrganizer2/modorganizer/releases) (MO2) can help you manage multiple modlists. MO2 is especially robust, and rather elegant in that it presents your mod installation as a virtual filesystem. I enjoy using MO2, but I wanted something slightly different. MO2 comes with its own complexity and its use is actually discouraged in modding-openmw.com (see: [modding-openmw.com FAQ](https://modding-openmw.com/faq/tooling) )

## Basic Flow

`openmw-snapshot-tool` provides an alternative way to manage OpenMW installations. The user can:
1. Set up OpenMW mods as usual, perhaps by following [modding-openmw.com](https://modding-openmw.com/).
2. Run OpenMW, tests the game, and decide that the mods and settings are acceptable
3. Run `openmw-snapshot-tool make ...` to capture this installation as a snapshot
4. Move or copy the snapshot anywhere
5. On any other device, run `openmw-snapshot-tool activate ...` to activate the snapshot. OpenMW on that device will now use the snapshot.   

### Continuing to mod an installation after making a snapshot

After you run  `openmw-snapshot-tool activate ...` on any device (whether it was your original device or one that you copied the snapshot to), the OpenMW configurations will now point to the *snapshot* rather than the original game files.

This means if you delete or move the snapshot, your game will break.

It also means if you want to continue modding your game, you can make changes to the *snapshot's* data directory, while modifying OpenMW's config files. Then, if you're satisfied with those additional changes, feel free to make another snapshot.

### Using OpenMW portable installs

`openmw-snapshot-tool activate` will by default modify your primary OpenMW configurations. So running this command will have consequences.

You can also tell `openmw-snapshot-tool` to create or update a configuration somewhere else. You should be able to use this in conjunction with OpenMW portable installs. That way you can activate snapshots to your heart's delight without impacting anything. There is an example below.

Portable installs are tricky to use with Steam Deck / flatpacks but it should be possible.

## Examples

Note that these examples go from Windows to a Steam Deck, but you can create or activate snapshots on any platform.

### Making a snapshot on Windows
```
python.exe ./openmw-snapshot-tool.py make --base-directory H:\mw-snapshots --snapshot-name Morrowind-20240712
```

### Running the snapshot on Steam Deck
Let's say you made that snapshot on Windows and copied it over to your Steam Deck. You can make a new shell script like this on your Deck, name it something like `Morrowind-20240712.sh` and give it execute permissions with `chmod +x`. Add this script to Steam as a non-steam game, and use it to run OpenMW with this specific snapshot. The author used this to easily have Starwind and Morrowind running side-by-side.
```
#!/bin/bash
python3 ./openmw-snapshot-tool.py activate --base-directory /home/deck/games/mw-snapshots --snapshot-name Morrowind-20240712
/usr/bin/flatpack run --command=openmw-launcher org.openmw.OpenMW
```

### Using portable install
Activating the snapshot so that it can be referenced by a OpenMW portable install. This way, the default configuration will not be modified.
This is what it would look like for a normal Linux install. Doing this with flatpack could get tricky because of entitlements and how arguments are passed.
```
# Assuming snapshot has been copied to ~/games/mw-snapshots/Morrowind-20240712
# PORTABLE_INSTALL_DIR can be anywhere, really
PORTABLE_INSTALL_DIR=~/games/mw-snapshots/Morrowind-20240712/portable-install
mkdir -p $PORTABLE_INSTALL_DIR
python3 ./openmw-snapshot-tool.py activate -b ~/games/mw-snapshots -n Morrowind-20240712 --openmw-config-dir $PORTABLE_INSTALL_DIR

# Now you can run OpenMW with:
PORTABLE_INSTALL_DIR=~/games/mw-snapshots/Morrowind-20240712/portable-install
openmw --replace=config --config $PORTABLE_INSTALL_DIR --user-data $PORTABLE_INSTALL_DIR
```

## Installing openmw-snapshot-tool

1. Install latest Python 3: https://www.python.org/downloads/ - For Windows users you don't have to fully install Python, you can also download a "Windows embeddable package" and use that to invoke the script.
2. Download the `openmw-snapshot-tool.py` script from https://github.com/DandyTush/openmw-snapshot-tool
3. Just run the tool using `python3`. There are no extra libraries to install, so `pip` is not necessary.

## Implementation Details

Snapshots are directories. The directories can be zipped, moved and copied wherever, then unzipped and activated.

**When a snapshot is activated, the config files will point to data on the snapshot itself. If you activate then delete a snapshot, the game will not be playable.**

The snapshot directories contain:
- A `delimiter` file that tells the tool which path separator was used (`\` or `/`) which is useful when activating snapshots on different platofrms.
- A `config` directory which is a copy of the OpenMW config directory from its source.
- - Save games are removed; this tool is not meant to persist or manage saved games, particularly to avoid overwriting a newer save when a snapshot is activated.
- - The `openmw.cfg` file is changed such that the data directories become relative, rather than absolute paths. In an original `openmw.cfg` data lines might look like: `data="C:\Morrowind\Data Files"`. In a snapshot they will look like `data="Data Files"`
- - Nav meshes are included and can contribute to the snapshot size.
- A `data` directory which includes all of the data pointed to by the original `openmw.cfg`.
- - The script will walk through all of the data directories referenced by the original `openmw.cfg` and find a common base directory. It will recursively copy any data referenced by the original `openmw.cfg` into this new `data` directory in the snapshot, preserving the directory structure.
- - Base game files will be copied. So you will have a copy of Bloodmoon, Tribunal, etc for every snapshot. This is intentional for two reasons: Sharing or skipping base game data would make the tool more complicated, and by keeping all of the data in a snapshot, you can make a new OpenMW installation without having to go through the Morrowind installer. It uses an extra couple gigabytes per snapshot which is literally $0.03 of hard disk space. I am open to introducing a little complexity if someone really cares about those extra few gigabytes. 

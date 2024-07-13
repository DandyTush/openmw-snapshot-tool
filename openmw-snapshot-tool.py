# https://github.com/DandyTush/openmw-snapshot-tool
# License: GPLv3 (see LICENSE for more information)

import argparse
from enum import Enum
import os
import re
import shutil

class Mode(Enum):
    MAKE = "make"
    ACTIVATE = "activate"

    def __str__(self):
        return self.value
 
def mode_type(mode_str):
    try:
        return Mode[mode_str.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError(f"Invalid mode: {mode_str}. Valid modes are: {', '.join([mode.value for mode in Mode])}")
        
def platform_type(platform_str):
    try:
        return Platform[platform_str.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError(f"Invalid platform: {platform_str}. Valid platform are: {', '.join([platform.value for platform in Platform])}")

def valid_directory(dir_str):
    if not os.path.isdir(dir_str):
        raise argparse.ArgumentTypeError(f"Invalid directory: {dir_str} does not exist.")
    return dir_str

parser = argparse.ArgumentParser(description="A tool for managing snapshots of OpenMW mod configurations")

parser.add_argument(
    "mode",
    type=mode_type,
    choices=list(Mode),
    help=f"Mode of operation. Valid modes are: {', '.join([mode.value for mode in Mode])}"
)

parser.add_argument(
    "--base-directory", "-b",
    type=valid_directory,
    required=True,
    help="Base directory to make or activate snapshots. This directory must exist. Individual snapshots are directories within this base directory."
)

parser.add_argument(
    "--snapshot-name", "-n",
    type=str,
    required=True,
    help="Snapshot name, which is a directory within the base directory. Will be created if mode is `make`. Will be utilized if mode is `activate`."
)

DIR_HELP=r"""OpenMW config directory. Specifically the directory that contains settings.cfg and openmw.cfg. 
The config files here will be used to create a snapshot or will be overwritten when restoring a snapshot. 
On Windows this will be `%USERPROFILE%\Documents\My Games\OpenMW`. On Linux, if openMW is installed via flatpack (like on the Steam Deck), 
this will be `$HOME/.var/app/org.openmw.OpenMW/config/openmw`. For other Linux installs it will be `$HOME/.config/openmw`. 
On Mac it will be `$HOME/Library/Preferences/openmw`. If this argument is not specified, the tool will 
automatically search for it. See https://openmw.readthedocs.io/en/stable/reference/modding/paths.html for more info."""

parser.add_argument(
    "--openmw-config-dir", "-o",
    type=valid_directory,
    required=False,
    default=None,
    help=DIR_HELP
)

args = parser.parse_args()

def get_documents_path():
    return os.path.join(os.environ['USERPROFILE'], 'Documents', 'My Games', 'OpenMW')

INSTALL_ERROR_MESSAGE = "Could not find a valid OpenMW installation. Please install OpenMW and go through the setup wizard using the launcher. You may need to set a configuration path using `--openmw-config-dir`"

def get_config_dir() -> str:
    if args.openmw_config_dir is not None:
        print(f"Using config directory provided by argument: '{args.openmw_config_dir}'")
        return args.openmw_config_dir
    try_dirs = []
    if 'HOME' in os.environ:
        try_dirs = [["linux flatpack", os.path.join(os.environ['HOME'], '.var/app/org.openmw.OpenMW/config/openmw')],
        ["linux", os.path.join(os.environ['HOME'], '.config/openmw')],
        ["mac", os.path.join(os.environ['HOME'], 'Library/Preferences/openmw')]]
    if 'USERPROFILE' in os.environ:
        try_dirs.append(["windows", os.path.join(os.environ['USERPROFILE'], 'Documents', 'My Games', 'OpenMW')])
    for platform, path in try_dirs:
        if os.path.isdir(path):
            print(f"Found a standard OpenMW install at path: '{path}', inferring platform to be {platform}")
            found_config_dir = path
            return path
    raise FileNotFoundError(INSTALL_ERROR_MESSAGE)

found_config_dir = get_config_dir()

def read_file_lines(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.readlines()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found. "+INSTALL_ERROR_MESSAGE)
    except IOError as e:
        print(f"Error reading file '{file_path}': {e}")

system_openmw_file = os.path.join(found_config_dir, 'openmw.cfg')

def read_system_openmw_file():
    config_dir = found_config_dir
    return read_file_lines(system_openmw_file)

# Check that the openmw.cfg file exists
read_system_openmw_file()


r"""
flatpack:

Saves:
/home/deck/.var/app/org.openmw.OpenMW/data/openmw/saves
/home/deck/.var/app/org.openmw.OpenMW/data/openmw/screenshots
/home/deck/.var/app/org.openmw.OpenMW/config/openmw/openmw.cfg
/home/deck/.var/app/org.openmw.OpenMW/config/openmw/settings.cfg

Windows:
C:\Users\dylan\Documents\My Games\OpenMW\openmw.cfg
C:\Users\dylan\Documents\My Games\OpenMW\settings.cfg
C:\Users\dylan\Documents\My Games\OpenMW\saves

"""

snapshot_dir = os.path.join(args.base_directory, args.snapshot_name)
print(f"Using base directory {args.base_directory}, snapshot name {args.snapshot_name}")
print(f"Using snapshot directory {snapshot_dir}")
snapshot_data_dir = os.path.join(snapshot_dir, "data")
snapshot_config_dir = os.path.join(snapshot_dir, "config")
print(f"Snapshot data at {snapshot_data_dir}. Snapshot config at {snapshot_config_dir}")

cfg_data_pattern=r"data=\"(.*)\"$"

def get_data_paths():
    data_paths = []
    for line in read_system_openmw_file():
        match=re.match(cfg_data_pattern, line)
        if match != None:
            data_paths.append(match.group(1))
    return data_paths
            
def get_base_data_path():
    data_paths = get_data_paths()
    shortest_path = min(data_paths, key=len)
    for length in range(len(shortest_path)):
        test_char = shortest_path[length]
        for path in data_paths:
            if path[length] != test_char:
                return shortest_path[0:length]
    return shortest_path

def copytree_overwrite_manual(source, destination, overwrite=False):
    try:
        # Recursively iterate through the source directory
        for root, dirs, files in os.walk(source):
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(destination, os.path.relpath(src_file, source))
                
                # Check if the file already exists in the destination
                if overwrite or not os.path.exists(dst_file):
                    # Create directories if they don't exist
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(src_file, dst_file)
                    print(f"Copied {src_file} to {dst_file}")
                else:
                    print(f"Ignored {src_file} (already exists)")

        
        print(f"Successfully copied from {source} to {destination}")
    except FileNotFoundError:
        print(f"Error: Source directory '{source}' not found.")
    except IOError as e:
        print(f"Error copying from '{source}' to '{destination}': {e}")

delim_file = os.path.join(snapshot_dir, 'delimiter')

def replace_and_save_file(file_path, old_str, new_str):
    try:
        # Read the original file content
        with open(file_path, 'r') as file:
            file_content = file.read()

        # Perform replacement
        modified_content = file_content.replace(old_str, new_str)

        # Write the modified content back to the same file
        with open(file_path, 'w') as file:
            file.write(modified_content)

        print(f"Replacement and save successful for file: {file_path}")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except IOError as e:
        print(f"Error reading or writing file '{file_path}': {e}")

if args.mode == Mode.MAKE:
    if os.path.isdir(snapshot_dir):
        print("Snapshot already exists. Specify a new snapshot name.")
        #TODO
        #exit(-1)
    print("Creating snapshot data and config directories...")
    os.makedirs(snapshot_dir, exist_ok=False)
    
    print(f"Copying config tree from {found_config_dir} to {snapshot_config_dir}")
    
    shutil.copytree(found_config_dir, snapshot_config_dir)
    
    maybe_save_dir = os.path.join(snapshot_config_dir, 'saves')
    print(f"Removing save files from snapshot if they exist - please back these up separately")
    if os.path.isdir(maybe_save_dir):
        print(f"Saves found in {maybe_save_dir}, removing")
        shutil.rmtree(maybe_save_dir)
    
    data_basedir = get_base_data_path()
    for existing_path in get_data_paths():
        data_subdir = existing_path[len(data_basedir):]
        data_new_full = os.path.join(snapshot_data_dir, data_subdir)
        print(f"Copying data from {existing_path} to {data_new_full}")
        copytree_overwrite_manual(existing_path, data_new_full, overwrite=False)

    try:
        with open(delim_file, 'w') as file:
            file.write(os.sep)
        print(f"Wrote path delimiter file")
    except IOError as e:
        print(f"Error writing to file '{delim_file}': {e}")
        exit()
    
    print("Removing basedir from openmw.cfg")
    snapshot_cfg = os.path.join(snapshot_config_dir, "openmw.cfg")
    replace_and_save_file(snapshot_cfg, 'data="'+data_basedir, 'data="')

elif args.mode == Mode.ACTIVATE:
    with open(delim_file, 'r') as file:
        snapshot_delim = file.read()
    print(f"Copying config tree from {snapshot_config_dir} to {found_config_dir}")
    
    copytree_overwrite_manual(snapshot_config_dir, found_config_dir, overwrite=True)
    
    print(f"Setting data directories to point to files under {snapshot_data_dir}")
    replace_and_save_file(system_openmw_file, 'data="', 'data="'+snapshot_data_dir+snapshot_delim)
    
    print(f"Updating path delimiter")
    replace_and_save_file(system_openmw_file, snapshot_delim, os.sep)
    
else:
    print("Unknown mode")
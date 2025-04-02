#!/usr/bin/env python3
import os
import re

# ANSI color codes for decoration
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"

# Emojis
CHECK = "✅"
CROSS = "❌"
FIRE  = "🔥"
INFO  = "ℹ️"

def normalize_gun_name(gun_name):
    """
    Normalize a gun name by:
      1. Removing any level details (splitting at "(")
      2. Converting to lowercase
      3. Removing punctuation (e.g., apostrophes, hyphens)
      4. Collapsing extra spaces

    This ensures that, for example, "Hornet's Nest - M762" and "Hornets Nest - M762"
    both become "hornets nest m762".
    """
    # Remove level details and convert to lowercase.
    name = gun_name.split(" (")[0].strip().lower()
    # Remove punctuation.
    name = re.sub(r"[^\w\s]", "", name)
    # Collapse multiple spaces.
    name = " ".join(name.split())
    return name

def parse_guns(guns_file):
    """
    Reads guns.txt and returns a list of dictionaries, each with:
      - 'hex': the normal hex string (from column 2)
      - 'gun_name': the full gun name (from column 3)
      - 'normalized': the normalized gun name (for matching)
    """
    guns_list = []
    with open(guns_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 3:
                continue
            entry = {
                'hex': parts[1],
                'gun_name': parts[2],
                'normalized': normalize_gun_name(parts[2])
            }
            guns_list.append(entry)
    return guns_list

def parse_changelog(changelog_file):
    """
    Reads changelog.txt and returns a set of normalized gun names 
    from lines starting with "Source Gun:" or "Target Gun:".
    """
    excluded = set()
    with open(changelog_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("Source Gun:"):
                gun = line[len("Source Gun:"):].strip()
                excluded.add(normalize_gun_name(gun))
            elif line.startswith("Target Gun:"):
                gun = line[len("Target Gun:"):].strip()
                excluded.add(normalize_gun_name(gun))
    return excluded

def parse_longhex(longhex_file):
    """
    Reads longhex.txt and returns a dictionary mapping the full gun name (as in longhex.txt)
    to its longhex string.
    """
    lh = {}
    with open(longhex_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 2:
                continue
            lh[parts[0]] = parts[1]
    return lh

def process_files(files_dir, guns_list, combined_excluded, longhex_dict):
    """
    Process files in files_dir according to three branches:
    
      Branch 1: If file base name is exactly one of {"00065947", "00065948", "00065949"}:
          → Null longhex values (for leveled guns only, i.e. gun name contains "(Lv")
      
      Branch 2: If file base name contains "00061":
          → Null normal hex (from guns.txt) but only for leveled guns 
             (i.e. gun's full gun_name contains "(Lv", case-insensitive)
      
      Branch 3: Otherwise:
          → Null normal hex (from guns.txt) for all guns.
      
    In all branches, skip guns whose normalized name is in combined_excluded.
    A log is generated and saved as log.txt in files_dir.
    """
    exception_files = {"00065947", "00065948", "00065949"}
    
    total_normal_replacements = 0
    total_longhex_replacements = 0
    total_files_modified = 0
    log_entries = []
    log_entries.append("Log of Hex Replacements (Normal and Longhex):")
    log_entries.append("=" * 50)
    log_entries.append("")
    
    for root, _, files in os.walk(files_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_base = os.path.splitext(file)[0]
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
            except Exception as e:
                print(f"{RED}{CROSS} Error reading {file_path}: {e}{RESET}")
                continue
            
            modified = False
            file_log = []  # Log for this file
            
            # Branch 1: Files exactly "00065947", "00065948", "00065949" → process longhex for leveled guns.
            if file_base in exception_files:
                for lh_gun, lh_val in longhex_dict.items():
                    if "(lv" not in lh_gun.lower():
                        continue
                    if normalize_gun_name(lh_gun) in combined_excluded:
                        continue
                    try:
                        lh_bytes = bytes.fromhex(lh_val)
                    except ValueError:
                        print(f"{RED}{CROSS} Invalid longhex '{lh_val}' for gun '{lh_gun}' in {file_path}{RESET}")
                        continue
                    null_bytes = b'\x00' * len(lh_bytes)
                    if lh_bytes in data:
                        data = data.replace(lh_bytes, null_bytes)
                        modified = True
                        total_longhex_replacements += 1
                        file_log.append(f"   - {lh_gun}: replaced longhex {lh_val}")
            
            # Branch 2: Files with "00061" in the name → process normal hex for leveled guns only.
            elif "00061" in file_base:
                for gun in guns_list:
                    if "(lv" not in gun['gun_name'].lower():
                        continue
                    if gun['normalized'] in combined_excluded:
                        continue
                    try:
                        hex_bytes = bytes.fromhex(gun['hex'])
                    except ValueError:
                        print(f"{RED}{CROSS} Invalid hex '{gun['hex']}' for gun '{gun['gun_name']}' in {file_path}{RESET}")
                        continue
                    null_bytes = b'\x00' * len(hex_bytes)
                    if hex_bytes in data:
                        data = data.replace(hex_bytes, null_bytes)
                        modified = True
                        total_normal_replacements += 1
                        file_log.append(f"   - {gun['gun_name']}: replaced normal hex {gun['hex']}")
            
            # Branch 3: All other files → process normal hex for all guns.
            else:
                for gun in guns_list:
                    if gun['normalized'] in combined_excluded:
                        continue
                    try:
                        hex_bytes = bytes.fromhex(gun['hex'])
                    except ValueError:
                        print(f"{RED}{CROSS} Invalid hex '{gun['hex']}' for gun '{gun['gun_name']}' in {file_path}{RESET}")
                        continue
                    null_bytes = b'\x00' * len(hex_bytes)
                    if hex_bytes in data:
                        data = data.replace(hex_bytes, null_bytes)
                        modified = True
                        total_normal_replacements += 1
                        file_log.append(f"   - {gun['gun_name']}: replaced normal hex {gun['hex']}")
            
            if modified:
                try:
                    with open(file_path, 'wb') as f:
                        f.write(data)
                    total_files_modified += 1
                    print(f"{GREEN}{CHECK} Modified {file_path}{RESET}")
                    log_entries.append(f"File: {file_path}")
                    log_entries.extend(file_log)
                    log_entries.append("")  # Separator
                except Exception as e:
                    print(f"{RED}{CROSS} Error writing {file_path}: {e}{RESET}")
    
    # Write log.txt in files_dir.
    log_file_path = os.path.join(files_dir, "log.txt")
    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write("\n".join(log_entries))
        print(f"\n{CYAN}{INFO} Log file 'log.txt' generated in {files_dir}.{RESET}")
    except Exception as e:
        print(f"{RED}{CROSS} Error writing log file: {e}{RESET}")
    
    # Summary
    print(f"\n{YELLOW}Summary:{RESET}")
    print(f"{YELLOW}Total files modified: {total_files_modified}{RESET}")
    print(f"{YELLOW}Total normal hex replacements: {total_normal_replacements}{RESET}")
    print(f"{YELLOW}Total longhex replacements: {total_longhex_replacements}{RESET}")

def main():
# Hard-coded file paths based on your provided locations:
    guns_file = r"/storage/emulated/0/FILES_OBB/TXT/guns.txt"
    longhex_file = r"/storage/emulated/0/FILES_OBB/TXT/longhex.txt"
    changelog_file = r"/storage/emulated/0/FILES_OBB/REPACK_OBB/SIZEFIXGUN/changelog.txt"
    files_dir = r"/storage/emulated/0/FILES_OBB/REPACK_OBB/SIZEFIXGUN/"
    
    guns_list = parse_guns(guns_file)
    changelog_excluded = parse_changelog(changelog_file)
    
    # Determine forbidden guns based on "default" or "hit effect" in the name.
    forbidden = set()
    for gun in guns_list:
        if "default" in gun['gun_name'].lower() or "hit effect" in gun['gun_name'].lower():
            forbidden.add(gun['normalized'])
    
    # Display exclusions.
    print(f"{CYAN}{FIRE} Changelog Excluded Guns:{RESET}")
    if changelog_excluded:
        for gun in changelog_excluded:
            print(f"  {RED}{CROSS} {gun}{RESET}")
    else:
        print(f"  {GREEN}{CHECK} None{RESET}")
    
    if forbidden:
        print(f"{CYAN}{FIRE} Normal and Hit effect guns excluded{RESET}")
    else:
        print(f"{CYAN}{FIRE} Normal and Hit effect guns not found{RESET}")
    
    # Combine exclusions.
    combined_excluded = set(changelog_excluded)
    combined_excluded.update(forbidden)
    
    # Display processing counts.
    total_all = len(guns_list)
    total_excluded = len(combined_excluded)
    print(f"\n{CYAN}{FIRE} Total Guns in guns.txt: {total_all}{RESET}")
    print(f"{CYAN}{FIRE} Total Excluded Guns: {total_excluded}{RESET}")
    
    longhex_dict = parse_longhex(longhex_file)
    process_files(files_dir, guns_list, combined_excluded, longhex_dict)

if __name__ == "__main__":
    main()

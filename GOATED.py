import os
import re
import json
from colorama import Fore, Style, init

# Initialize colorama for colorful output
init(autoreset=True)

# Global counters for serial numbering in each mod section
mod_counters = {"Gun Skins": 0, "Hit Effect": 0, "Lootbox": 0, "Icon": 0}

CONFIG_FILE = "directories.json"

# ===============================
# Directory & Config Functions
# ===============================
def get_directories():
    """
    Return the required directories with predefined paths:
      1. Gun Skins: /storage/emulated/0/FILES_OBB/GUN_SKIN/
      2. Hit Effect: /storage/emulated/0/FILES_OBB/HIT_EFFECT/
      3. Lootbox: /storage/emulated/0/FILES_OBB/LOOTBOX_DATS/
      4. Icon: /storage/emulated/0/FILES_OBB/ICON_MOD/
      5. Repack (destination folder): /storage/emulated/0/FILES_OBB/REPACK_OBB/
      6. Skin Index file path (used only for icon modding): /storage/emulated/0/FILES_OBB/TXT/skin_index.txt
    """
    dirs = {
        "gun_skins": "/storage/emulated/0/FILES_OBB/GUN_SKIN/",
        "hit_effect": "/storage/emulated/0/FILES_OBB/HIT_EFFECT/",
        "lootbox": "/storage/emulated/0/FILES_OBB/LOOTBOX_DATS/",
        "icon": "/storage/emulated/0/FILES_OBB/ICON_MOD/",
        "repack": "/storage/emulated/0/FILES_OBB/REPACK_OBB/",
        "skin_index": "/storage/emulated/0/FILES_OBB/TXT/skin_index.txt"
    }
    return dirs

def save_directories(dirs):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(dirs, f, indent=4)
        print(Fore.GREEN + f"✅ Saved directories to '{CONFIG_FILE}'.")
    except Exception as e:
        print(Fore.RED + f"❌ Error saving directories: {e}")

def load_directories():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
            required = ["gun_skins", "hit_effect", "lootbox", "icon", "repack", "skin_index"]
            if all(k in data for k in required):
                return data
        return None
    except Exception as e:
        print(Fore.RED + f"❌ Error loading directories: {e}")
        return None

# ===============================
# Helper Function for Gun Decoration
# ===============================
def decorate_gun_name(gun):
    """
    Decorate a gun's name with a special color and a unique emoji for level 1 to 8.
    """
    name = gun['name']
    match = re.search(r'\(Lv\. ?(\d+)\)', name)
    if match:
        level = int(match.group(1))
        level_colors = {
            1: Fore.RED,
            2: Fore.MAGENTA,
            3: Fore.YELLOW,
            4: Fore.CYAN,
            5: Fore.LIGHTRED_EX,
            6: Fore.LIGHTMAGENTA_EX,
            7: Fore.LIGHTYELLOW_EX,
            8: Fore.LIGHTCYAN_EX
        }
        level_emojis = {
            1: "🔥",
            2: "😈",
            3: "💀",
            4: "👹",
            5: "🤘",
            6: "⚡",
            7: "☠️",
            8: "🦇"
        }
        color = level_colors.get(level, Fore.WHITE)
        emoji = level_emojis.get(level, "")
        return f"{color}{name} {emoji}{Style.RESET_ALL}"
    else:
        return f"{Fore.WHITE}{name}{Style.RESET_ALL}"

# ===============================
# Function to Clean Gun Name for Changelog
# ===============================
def clean_gun_name_for_changelog(gun_name):
    gun_name = re.sub(r'^\d+m\s*', '', gun_name)
    gun_name = re.sub(r'[^\w\s()-]', '', gun_name)
    return gun_name.strip()

# ===============================
# Gun Data Functions
# ===============================
def read_guns_file(txt_file):
    """Read guns.txt and return a list of gun entries."""
    try:
        with open(txt_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        guns = []
        for line in lines:
            parts = line.strip().split(" | ")
            if len(parts) >= 3:
                guns.append({
                    "id": parts[0],
                    "hex": parts[1].lower(),
                    "name": parts[2]
                })
        return guns
    except Exception as e:
        print(Fore.RED + f"❌ Error reading {txt_file}: {e}")
        return []

def find_matching_guns(guns, query):
    query = query.lower()
    return [gun for gun in guns if query in gun["name"].lower()]

# ===============================
# Skin Index Parsing & Fuzzy Matching
# ===============================
def parse_skin_index_file(file_path):
    index_dict = {}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            current_category = None
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("###"):
                    current_category = line[3:].strip()
                else:
                    if " - " in line:
                        name_part, idx_part = line.rsplit(" - ", 1)
                        gun_name = name_part.strip()
                        index_hex = idx_part.strip().lower()
                        index_dict[gun_name.lower()] = index_hex
        print(Fore.GREEN + f"✅ Parsed skin index file '{file_path}' with {len(index_dict)} entries.")
    except Exception as e:
        print(Fore.RED + f"❌ Error parsing skin index file '{file_path}': {e}")
    return index_dict

def normalize_gun_name(name):
    name = name.lower()
    for ch in ["-", "(", ")", ",", ".", "'"]:
        name = name.replace(ch, " ")
    return " ".join(name.split())

def get_skin_index_for_gun(skin_index_dict, gun_name):
    norm_gun = normalize_gun_name(gun_name)
    for key, value in skin_index_dict.items():
        norm_key = normalize_gun_name(key)
        if norm_gun in norm_key or norm_key in norm_gun:
            return value
    return None

# ===============================
# Hex and Index Functions
# ===============================
def replace_index(file_path, source_index_hex, target_index_hex):
    try:
        with open(file_path, 'rb') as f:
            data = f.read().hex()
        data = data.replace(source_index_hex, target_index_hex)
        with open(file_path, 'wb') as f:
            f.write(bytes.fromhex(data))
        print(Fore.GREEN + f"✅ Replaced index hex '{source_index_hex}' -> '{target_index_hex}' in file '{file_path}'.")
    except Exception as e:
        print(Fore.RED + f"❌ Error replacing index hex in file '{file_path}': {e}")

def replace_hex(file_path, source_hex, target_hex):
    try:
        with open(file_path, 'rb') as f:
            data = f.read().hex()
        data = data.replace(source_hex.replace(" ", ""), target_hex.replace(" ", ""))
        with open(file_path, 'wb') as f:
            f.write(bytes.fromhex(data))
        print(Fore.GREEN + f"✅ Replaced hex '{source_hex}' -> '{target_hex}' in '{os.path.basename(file_path)}'.")
    except Exception as e:
        print(Fore.RED + f"❌ Error replacing hex in file '{file_path}': {e}")

# ===============================
# File Copying Function (Bulk Mode)
# ===============================
def copy_files_to_repack_mod(mod_type, src_dir, repack_folder, condition_hexes, file_modtype_map):
    files_copied = []
    for file_name in os.listdir(src_dir):
        src_file_path = os.path.join(src_dir, file_name)
        if not os.path.isfile(src_file_path):
            continue
        dest_file_path = os.path.join(repack_folder, file_name)
        # If file already exists, check if it already has one of the condition hex values
        if os.path.exists(dest_file_path):
            try:
                with open(dest_file_path, "rb") as f:
                    dest_data = f.read().hex()
                if any(hex_val in dest_data for hex_val in condition_hexes):
                    file_modtype_map[file_name] = mod_type
                    continue
            except Exception:
                pass
        try:
            with open(src_file_path, "rb") as f:
                src_data = f.read().hex()
        except Exception:
            continue
        if not any(hex_val in src_data for hex_val in condition_hexes):
            continue
        with open(src_file_path, "rb") as src, open(dest_file_path, "wb") as dst:
            dst.write(src.read())
        files_copied.append(file_name)
        file_modtype_map[file_name] = mod_type
    if files_copied:
        print(Fore.GREEN + f"✅ Copied {len(files_copied)} file(s) from {mod_type} into repack folder.")
    return files_copied

# ===============================
# Modding Functions for Each Part
# ===============================
def revert_mod_gun_skin_files(file_paths, source_hex, target_hex, source_gun, target_gun):
    global mod_counters
    log_msgs = []
    modified_files = []
    source_long = None
    for file_path in file_paths:
        try:
            with open(file_path, "rb") as f:
                data = f.read().hex()
            pos_source = data.find(source_hex)
            if pos_source != -1:
                available = 10 if pos_source >= 10 else pos_source
                source_long = data[pos_source - available: pos_source + len(source_hex)]
                print(Fore.GREEN + f"✅ [Gun Skins] Extracted 'long hex' from '{os.path.basename(file_path)}'")
                break
        except Exception as e:
            print(Fore.RED + f"❌ Error reading file '{os.path.basename(file_path)}': {e}")
    if source_long is None:
        print(Fore.YELLOW + f"⚠️ [Gun Skins] Source hex '{source_hex}' not found in any file.")
        return None, []
    total_replacements = 0
    for file_path in file_paths:
        try:
            with open(file_path, "rb") as f:
                data = f.read().hex()
            replacements = []
            for m in re.finditer(re.escape(target_hex), data):
                pos = m.start()
                if pos < 10:
                    continue
                replacements.append((pos - 10, pos + len(target_hex)))
            if replacements:
                new_data = data
                for start, end in sorted(replacements, key=lambda x: x[0], reverse=True):
                    new_data = new_data[:start] + source_long + new_data[end:]
                total_replacements += 1
                with open(file_path, "wb") as f:
                    f.write(bytes.fromhex(new_data))
                mod_counters["Gun Skins"] += 1
                log_entry = (
                    "==============================\n"
                    f"{mod_counters['Gun Skins']}. Mod Type: Gun Skins\n"
                    f"File: {os.path.basename(file_path)}\n"
                    f"Source Gun: {clean_gun_name_for_changelog(source_gun['name'])} \n"
                    f"Target Gun: {clean_gun_name_for_changelog(target_gun['name'])} \n"
                    f"Replaced {len(replacements)} occurrence(s) with long hex: {source_long}\n"
                    "=============================="
                )
                print(Fore.GREEN + "✅ " + log_entry)
                log_msgs.append(log_entry)
                modified_files.append(os.path.basename(file_path))
        except Exception as e:
            print(Fore.RED + f"❌ Error processing file '{os.path.basename(file_path)}': {e}")
    if total_replacements > 0:
        return log_msgs, modified_files
    else:
        print(Fore.YELLOW + f"⚠️ [Gun Skins] No valid occurrences of target hex '{target_hex}' found in any file.")
        return None, []

def mod_hit_effect_file(file_path, source_hex, target_hex, source_gun, target_gun):
    global mod_counters
    try:
        with open(file_path, "rb") as f:
            data = f.read().hex()
        if source_hex not in data:
            return None
        new_data = data.replace(source_hex, target_hex)
        if new_data == data:
            return None
        with open(file_path, "wb") as f:
            f.write(bytes.fromhex(new_data))
        mod_counters["Hit Effect"] += 1
        log_entry = (
            "==============================\n"
            f"{mod_counters['Hit Effect']}. Mod Type: Hit Effect\n"
            f"File: {os.path.basename(file_path)}\n"
            f"Source Gun: {clean_gun_name_for_changelog(source_gun['name'])} \n"
            f"Target Gun: {clean_gun_name_for_changelog(target_gun['name'])} \n"
            f"Replaced hex: {source_hex} with {target_hex}\n"
            "=============================="
        )
        print(Fore.GREEN + "✅ " + log_entry)
        return log_entry
    except Exception as e:
        print(Fore.RED + f"❌ Error in Hit Effect mod for '{os.path.basename(file_path)}': {e}")
        return None

def mod_lootbox_file(file_path, source_hex, target_hex, source_gun, target_gun):
    global mod_counters
    try:
        with open(file_path, "rb") as f:
            data = f.read().hex()
        if source_hex not in data:
            return None
        new_data = data.replace(source_hex, target_hex)
        if new_data == data:
            return None
        with open(file_path, "wb") as f:
            f.write(bytes.fromhex(new_data))
        mod_counters["Lootbox"] += 1
        log_entry = (
            "==============================\n"
            f"{mod_counters['Lootbox']}. Mod Type: Lootbox\n"
            f"File: {os.path.basename(file_path)}\n"
            f"Source Gun: {clean_gun_name_for_changelog(source_gun['name'])} \n"
            f"Target Gun: {clean_gun_name_for_changelog(target_gun['name'])} \n"
            f"Replaced hex: {source_hex} with {target_hex}\n"
            "=============================="
        )
        print(Fore.GREEN + "✅ " + log_entry)
        return log_entry
    except Exception as e:
        print(Fore.RED + f"❌ Error in Lootbox mod for '{os.path.basename(file_path)}': {e}")
        return None

def mod_icon_file(file_path, source_hex, target_hex, source_index_hex, target_index_hex, source_gun, target_gun):
    global mod_counters
    try:
        with open(file_path, "rb") as f:
            data = f.read().hex()
        if source_hex not in data:
            return None
        intervals = []
        for match in re.finditer(re.escape(source_hex), data):
            pos = match.start()
            start_interval = max(0, pos - 100)
            intervals.append((start_interval, pos))
        def replace_index_if_in_zone(match):
            pos = match.start()
            for start, end in intervals:
                if start <= pos < end:
                    return target_index_hex
            return match.group(0)
        new_data = re.sub(re.escape(source_index_hex), replace_index_if_in_zone, data)
        new_data = new_data.replace(source_hex, target_hex)
        if new_data == data:
            return None
        with open(file_path, "wb") as f:
            f.write(bytes.fromhex(new_data))
        mod_counters["Icon"] += 1
        log_entry = (
            "==============================\n"
            f"{mod_counters['Icon']}. Mod Type: Icon\n"
            f"File: {os.path.basename(file_path)}\n"
            f"Source Gun: {clean_gun_name_for_changelog(source_gun['name'])} \n"
            f"Target Gun: {clean_gun_name_for_changelog(target_gun['name'])} \n"
            f"Source Index: {source_index_hex}\n"
            f"Target Index: {target_index_hex}\n"
            f"Replaced hex: {source_hex} with {target_hex}\n"
            "=============================="
        )
        print(Fore.GREEN + "✅ " + log_entry)
        return log_entry
    except Exception as e:
        print(Fore.RED + f"❌ Error in Icon mod for '{os.path.basename(file_path)}': {e}")
        return None

# ===============================
# Bulk Modding Function
# ===============================
def bulk_modding(guns, dirs, skin_index_dict):
    repack_folder = dirs["repack"]
    global_changelog = []
    # Use one file_modtype_map for the entire bulk session
    file_modtype_map = {}
    print(Fore.CYAN + "\n🔍 BULK MODDING MODE 🔍")
    print("Enter pairs of gun IDs in the format: SOURCE_GUN_ID,TARGET_GUN_ID")
    print("Enter 'q' on a new line when finished:")
    pairs = []
    while True:
        line = input().strip()
        if line.lower() == "q":
            break
        if not line:
            continue
        parts = line.split(",")
        if len(parts) != 2:
            print(Fore.RED + "❌ Invalid format. Please use: SOURCE_GUN_ID,TARGET_GUN_ID")
            continue
        pairs.append((parts[0].strip(), parts[1].strip()))
    
    # Process each pair; do not clear the repack folder between pairs.
    for source_id, target_id in pairs:
        source_gun = next((g for g in guns if g["id"] == source_id), None)
        target_gun = next((g for g in guns if g["id"] == target_id), None)
        if not source_gun:
            print(Fore.RED + f"❌ Source gun with ID {source_id} not found. Skipping pair.")
            continue
        if not target_gun:
            print(Fore.RED + f"❌ Target gun with ID {target_id} not found. Skipping pair.")
            continue

        print(Fore.YELLOW + f"\nProcessing pair: {decorate_gun_name(source_gun)}  ->  {decorate_gun_name(target_gun)}")
        source_hex = source_gun["hex"]
        target_hex = target_gun["hex"]

        target_hex_hit = target_hex
        if target_gun["name"].startswith("Default"):
            base_name = target_gun["name"].replace("Default", "").strip()
            hit_effect_gun = next((gun for gun in guns if "Hit effect" in gun["name"] and base_name in gun["name"]), None)
            if hit_effect_gun:
                print(Fore.GREEN + f"✅ Target gun is 'Default'. Using Hit Effect version: {decorate_gun_name(hit_effect_gun)}")
                target_hex_hit = hit_effect_gun["hex"]
            else:
                print(Fore.YELLOW + f"⚠️ Could not find Hit Effect version for '{target_gun['name']}'. Using Default version.")

        source_hex_hit = source_hex
        if "Lv." in source_gun["name"]:
            base_name = source_gun["name"].split(" (Lv.")[0].strip()
            for gun in guns:
                if base_name in gun["name"] and "(Lv. 5)" in gun["name"]:
                    source_hex_hit = gun["hex"]
                    print(Fore.GREEN + f"✅ Using level 5 hex for Hit Effect modding: {source_hex_hit}")
                    break

        # In bulk modding, copy files only if not already present with required hex codes.
        mod_types = ["gun_skins", "hit_effect", "lootbox", "icon"]
        for mod in mod_types:
            src_dir = dirs.get(mod)
            if not src_dir or not os.path.exists(src_dir):
                print(Fore.RED + f"❌ Directory for {mod} not found. Skipping.")
                continue
            copy_files_to_repack_mod(mod, src_dir, repack_folder, [source_hex, target_hex], file_modtype_map)

        modified_files = set()
        gun_skin_files = [os.path.join(repack_folder, f) for f, mod in file_modtype_map.items() if mod == "gun_skins"]
        if gun_skin_files:
            log_msgs, mod_files = revert_mod_gun_skin_files(gun_skin_files, source_hex, target_hex, source_gun, target_gun)
            if log_msgs:
                global_changelog.extend(log_msgs)
                modified_files.update(mod_files)

        for file_name in os.listdir(repack_folder):
            file_path = os.path.join(repack_folder, file_name)
            if not os.path.isfile(file_path):
                continue
            if file_modtype_map.get(file_name) == "gun_skins":
                continue
            mod_type = file_modtype_map.get(file_name)
            log_entry = None
            if mod_type == "hit_effect":
                log_entry = mod_hit_effect_file(file_path, source_hex_hit, target_hex_hit, source_gun, target_gun)
            elif mod_type == "lootbox":
                log_entry = mod_lootbox_file(file_path, source_hex, target_hex, source_gun, target_gun)
            elif mod_type == "icon":
                target_skin_index = get_skin_index_for_gun(skin_index_dict, target_gun["name"])
                source_skin_index = get_skin_index_for_gun(skin_index_dict, source_gun["name"])
                if target_skin_index is None or source_skin_index is None:
                    continue
                log_entry = mod_icon_file(file_path, source_hex, target_hex, source_skin_index, target_skin_index, source_gun, target_gun)
            if log_entry:
                global_changelog.append(log_entry)
                modified_files.add(file_name)
    
    # After processing all pairs, clean up the repack folder:
    # Keep only files that are present in the changelog.
    changelog_files = set()
    for entry in global_changelog:
        match = re.search(r"File:\s*(.+)", entry)
        if match:
            changelog_files.add(match.group(1).strip())
    for file_name in os.listdir(repack_folder):
        if file_name == "changelog.txt":
            continue
        file_path = os.path.join(repack_folder, file_name)
        if not os.path.isfile(file_path):
            continue
        if file_name not in changelog_files:
            try:
                os.remove(file_path)
            except Exception:
                pass
    
    changelog_path = os.path.join(repack_folder, "changelog.txt")
    if global_changelog:
        try:
            with open(changelog_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(global_changelog))
            print(Fore.GREEN + "\n🎉 Bulk modding complete. Changelog saved at:")
            print(f"   {changelog_path}\n")
        except Exception as e:
            print(Fore.RED + f"❌ Error writing changelog: {e}")
    else:
        print(Fore.YELLOW + "\n⚠️ No changes were made in bulk modding.")
    
    print(Fore.GREEN + "\n👋 Bulk modding complete. Returning to mode selection...\n")

# ===============================
# Normal Modding Function
# ===============================
def normal_modding(guns, dirs, skin_index_dict):
    repack_folder = dirs["repack"]
    global_changelog = []
    if not os.path.exists(repack_folder):
        os.makedirs(repack_folder, exist_ok=True)
    file_modtype_map = {}
    while True:
        changelog_path = os.path.join(repack_folder, "changelog.txt")
        if os.path.exists(changelog_path):
            try:
                with open(changelog_path, "r", encoding="utf-8") as f:
                    global_changelog = f.read().split("\n\n")
            except Exception as e:
                print(Fore.RED + f"❌ Error reading changelog: {e}")
                global_changelog = []
        else:
            global_changelog = []
    
        changelog_files = set()
        for entry in global_changelog:
            match = re.search(r"File:\s*(.+)", entry)
            if match:
                file_name = match.group(1).strip()
                changelog_files.add(file_name)
    
        for file_name in os.listdir(repack_folder):
            file_path = os.path.join(repack_folder, file_name)
            if file_name == "changelog.txt":
                continue
            if file_name not in changelog_files and os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
    
        file_modtype_map.clear()
    
        while True:
            print(Fore.CYAN + "\n🔍 Select Source and Target Guns 🔍\n")
            source_query = input("🎯 Enter the name of the source gun: ").strip()
            source_matches = find_matching_guns(guns, source_query)
            if not source_matches:
                print(Fore.RED + "❌ No matching source guns found. Try again.")
                continue
            print(Fore.YELLOW + "\nMatching source guns:")
            for i, gun in enumerate(source_matches):
                print(f"  {i+1}. {decorate_gun_name(gun)} ({gun['hex']})")
            try:
                source_choice = int(input("👉 Choose the source gun by number: ")) - 1
                source_gun = source_matches[source_choice]
            except Exception:
                print(Fore.RED + "❌ Invalid choice. Try again.")
                continue
    
            target_query = input("\n🎯 Enter the name of the target gun: ").strip()
            target_matches = find_matching_guns(guns, target_query)
            if not target_matches:
                print(Fore.RED + "❌ No matching target guns found. Try again.")
                continue
            print(Fore.YELLOW + "\nMatching target guns:")
            for i, gun in enumerate(target_matches):
                print(f"  {i+1}. {decorate_gun_name(gun)} ({gun['hex']})")
            try:
                target_choice = int(input("👉 Choose the target gun by number: ")) - 1
                target_gun = target_matches[target_choice]
            except Exception:
                print(Fore.RED + "❌ Invalid choice. Try again.")
                continue
    
            source_hex = source_gun['hex']
            target_hex = target_gun['hex']
    
            target_hex_hit = target_hex
            if target_gun["name"].startswith("Default"):
                base_name = target_gun["name"].replace("Default", "").strip()
                hit_effect_gun = next((gun for gun in guns if "Hit effect" in gun["name"] and base_name in gun["name"]), None)
                if hit_effect_gun:
                    print(Fore.GREEN + f"✅ Target gun is 'Default'. Using Hit Effect version: {decorate_gun_name(hit_effect_gun)} ({hit_effect_gun['hex']})")
                    target_hex_hit = hit_effect_gun["hex"]
                else:
                    print(Fore.YELLOW + f"⚠️ Could not find Hit Effect version for '{target_gun['name']}'. Using Default version.")
    
            print(Fore.GREEN + f"\n🔍 Selected Source: {decorate_gun_name(source_gun)} ")
            print(Fore.GREEN + f"🔍 Selected Target: {decorate_gun_name(target_gun)} \n")
            break
    
        source_hex_hit = source_hex
        if "Lv." in source_gun["name"]:
            base_name = source_gun["name"].split(" (Lv.")[0].strip()
            for gun in guns:
                if base_name in gun["name"] and "(Lv. 5)" in gun["name"]:
                    source_hex_hit = gun["hex"]
                    print(Fore.GREEN + f"✅ Using level 5 hex for Hit Effect modding: {source_hex_hit}")
                    break
    
        mod_types = ["gun_skins", "hit_effect", "lootbox", "icon"]
        for mod in mod_types:
            src_dir = dirs.get(mod)
            if not src_dir or not os.path.exists(src_dir):
                print(Fore.RED + f"❌ Directory for {mod} not found. Skipping.")
                continue
            copy_files_to_repack_mod(mod, src_dir, repack_folder, [source_hex, target_hex], file_modtype_map)
    
        modified_files = set()
    
        gun_skin_files = [os.path.join(repack_folder, f) for f, mod in file_modtype_map.items() if mod == "gun_skins"]
        if gun_skin_files:
            log_msgs, mod_files = revert_mod_gun_skin_files(gun_skin_files, source_hex, target_hex, source_gun, target_gun)
            if log_msgs:
                global_changelog.extend(log_msgs)
                modified_files.update(mod_files)
    
        for file_name in os.listdir(repack_folder):
            file_path = os.path.join(repack_folder, file_name)
            if not os.path.isfile(file_path):
                continue
            if file_modtype_map.get(file_name) == "gun_skins":
                continue
            mod_type = file_modtype_map.get(file_name)
            log_entry = None
            if mod_type == "hit_effect":
                log_entry = mod_hit_effect_file(file_path, source_hex_hit, target_hex_hit, source_gun, target_gun)
            elif mod_type == "lootbox":
                log_entry = mod_lootbox_file(file_path, source_hex, target_hex, source_gun, target_gun)
            elif mod_type == "icon":
                target_skin_index = get_skin_index_for_gun(skin_index_dict, target_gun["name"])
                source_skin_index = get_skin_index_for_gun(skin_index_dict, source_gun["name"])
                if target_skin_index is None or source_skin_index is None:
                    continue
                log_entry = mod_icon_file(file_path, source_hex, target_hex, source_skin_index, target_skin_index, source_gun, target_gun)
            if log_entry:
                global_changelog.append(log_entry)
                modified_files.add(file_name)
    
        for file_name in os.listdir(repack_folder):
            if file_name == "changelog.txt":
                continue
            file_path = os.path.join(repack_folder, file_name)
            if not os.path.isfile(file_path):
                continue
            if file_name not in file_modtype_map or file_name not in modified_files:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
    
        if global_changelog:
            try:
                with open(changelog_path, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(global_changelog))
                print(Fore.GREEN + "\n🎉 Modding complete. Changelog saved at:")
                print(f"   {changelog_path}\n")
            except Exception as e:
                print(Fore.RED + f"❌ Error writing changelog: {e}")
        else:
            print(Fore.YELLOW + "\n⚠️ No changes were made.")
    
        choice = input("\n🔄 Do you want to mod more skins in Normal mode? (y/n): ").strip().lower()
        if choice not in ("y", "yes"):
            print(Fore.GREEN + "Returning to main menu...\n")
            break
        else:
            print(Fore.CYAN + "🔄 Starting a new modding session...\n")

# ===============================
# Main Function (Mode Selection)
# ===============================
def main():
    print(Style.BRIGHT + Fore.GREEN + "\n🎮 Game Skin Modding Tool Starting...\n")
    dirs = load_directories()
    if not dirs:
        dirs = get_directories()
        save_directories(dirs)
    else:
        print(Fore.GREEN + "✅ Loaded saved directories from config.")
    
    txt_file = "/storage/emulated/0/FILES_OBB/TXT/guns.txt"
    if not os.path.exists(txt_file):
        print(Fore.RED + "❌ Error: 'guns.txt' not found at the specified location!")
        return
    guns = read_guns_file(txt_file)
    if not guns:
        print(Fore.RED + "❌ No gun entries found in 'guns.txt'.")
        return
    skin_index_path = dirs.get("skin_index")
    skin_index_dict = {}
    if skin_index_path and os.path.exists(skin_index_path):
        skin_index_dict = parse_skin_index_file(skin_index_path)
    else:
        print(Fore.RED + "❌ Skin Index file not found. Icon modding will not work properly.")
    
    while True:
        print(Fore.CYAN + "\nSelect Modding Mode:")
        print("1: BULK MODDING")
        print("2: NORMAL MODDING")
        print("q: Quit")
        mode = input("👉 Enter 1, 2, or q: ").strip().lower()
        if mode == "q":
            print(Fore.GREEN + "👋 Exiting the tool. Goodbye!")
            break
        elif mode == "1":
            bulk_modding(guns, dirs, skin_index_dict)
        elif mode == "2":
            normal_modding(guns, dirs, skin_index_dict)
        else:
            print(Fore.RED + "❌ Invalid option. Please try again.")

if __name__ == "__main__":
    main()

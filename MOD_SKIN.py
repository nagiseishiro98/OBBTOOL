import os
import re
from colorama import Fore, Back, Style, init
import sys

# Initialize colorama
init(autoreset=True)

# =========================== DIRECTORY PATHS ===========================
BASE_DIR = r"/storage/emulated/0/FILES_OBB/MOD_ANY ICON"
TXT_DIR = os.path.join(BASE_DIR, "TXT")
ICON_MOD_DIR = r"/storage/emulated/0/FILES_OBB/ICON_MOD/"
REPACK_OBB_DIR = r"/storage/emulated/0/FILES_OBB/REPACK_OBB/REPACKANYICON/"
INDEX_FILE_PATH = os.path.join(TXT_DIR, "index.txt")
CHANGELOG_PATH = os.path.join(REPACK_OBB_DIR, "changelog.txt")

# Global list to track changes
changelog_entries = []

# =========================== CHANGELOG ===========================
def write_changelog():
    """Writes accumulated changes to changelog.txt.
    Each log entry shows the mod replacement along with the TXT file used and,
    if applicable, the index replacement details or failure reason."""
    mod_type_counts = {}
    file_exists = os.path.exists(CHANGELOG_PATH)
    with open(CHANGELOG_PATH, "a", encoding="utf-8") as f:
        if not file_exists:
            f.write("🌟 Mod Tool Changelog 🌟\n")
            f.write("==============================\n\n")
        
        for entry in changelog_entries:
            mod_type = entry["mod_type"]
            mod_type_counts[mod_type] = mod_type_counts.get(mod_type, 0) + 1
            current_count = mod_type_counts[mod_type]
            
            f.write("==============================\n")
            f.write(f"{current_count}. Mod Type: {mod_type}\n")
            f.write(f"TXT USED: {entry['source_file']}\n")
            f.write(f"File: {entry['file_name']}\n")
            f.write(f"Source Item: {entry['source_item']}\n")
            f.write(f"Target Item: {entry['target_item']}\n")
            f.write(f"Replaced hex: {entry['source_hex']} with {entry['target_hex']}\n")
            if entry.get('index_occurrences', 0) > 0:
                f.write(f"Index replaced: {entry['source_index']} with {entry['target_index']} ({entry['index_occurrences']} occurrence(s))\n")
            elif entry.get('index_failure_reason'):
                f.write(f"Index replacement failed: {entry['index_failure_reason']}\n")
            f.write("==============================\n\n")

# =========================== MOD SELECTION ===========================
def select_txt_file():
    """Let user select which TXT file (mod category) to use."""
    txt_files = [f for f in os.listdir(TXT_DIR) if f.lower().endswith('.txt') and f.lower() != 'index.txt']
    if not txt_files:
        print(f"{Fore.RED}🚨 No TXT files found in {TXT_DIR}")
        return None, None
    print(f"\n{Fore.CYAN}📁 Available Mod Categories:")
    for idx, file in enumerate(txt_files, 1):
        print(f"{Fore.YELLOW}{idx}. {file.replace('.txt', '').title()}")
    while True:
        try:
            choice = int(input(f"\n{Fore.CYAN}🎚️ Select category (1-{len(txt_files)}): "))
            if 1 <= choice <= len(txt_files):
                selected_file = os.path.join(TXT_DIR, txt_files[choice-1])
                mod_type = txt_files[choice-1].replace('.txt', '').title()
                return selected_file, mod_type
            print(f"{Fore.RED}❌ Invalid choice. Try again.")
        except ValueError:
            print(f"{Fore.RED}❌ Please enter a valid number.")

def fetch_mod_data(file_path):
    """
    Reads the mod file and returns a dictionary of mod data.
    Each line should be in the format: SkinID | ModHex | SkinName.
    Data is stored as key=ModHex and value={'description': SkinID, 'skin_name': SkinName}.
    """
    mod_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                parts = line.strip().split(" | ")
                if len(parts) >= 3:
                    skin_id = parts[0].strip()
                    mod_hex = parts[1].strip()
                    skin_name = parts[2].strip()
                    mod_data[mod_hex] = {
                        'description': skin_id,
                        'skin_name': skin_name
                    }
                elif len(parts) >= 2:
                    skin_id = parts[0].strip()
                    mod_hex = parts[1].strip()
                    mod_data[mod_hex] = {
                        'description': skin_id,
                        'skin_name': ""
                    }
    except FileNotFoundError:
        print(f"{Fore.RED}🚨 Error: File not found at path: {file_path}")
    except UnicodeDecodeError:
        print(f"{Fore.RED}🚨 Error: Unable to decode the file at path: {file_path}")
    return mod_data

def fetch_index_hex_from_file(file_path):
    """
    Reads the index file (format: Skin Name - HexCode) and returns a dictionary.
    If an outfit name appears multiple times, stores a list of hex codes.
    """
    index_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                parts = line.strip().split(' - ')
                if len(parts) == 2:
                    name = parts[0].strip()
                    hex_val = parts[1].strip()
                    if name in index_data:
                        index_data[name].append(hex_val)
                    else:
                        index_data[name] = [hex_val]
    except FileNotFoundError:
        print(f"{Fore.RED}🚨 Index file not found!")
    return index_data

# =========================== PROCESS MODS ===========================
def process_mods(directory_path, hex_pairs, output_path, item_replacements, index_hex_data, mod_type, txt_file):
    """
    For each file in directory_path:
      - Uses an existing modified file (in output_path) as the starting point if available.
      - Finds the first and second occurrences of the source mod hex.
      - Replaces ONLY the SECOND occurrence with the target mod hex.
      - Then, for the index replacement, it looks for the source index hex only in a window
        that starts 30 bytes (60 hex characters) before the FIRST occurrence of the source mod hex.
        Within that window, it replaces only the FIRST occurrence of the source index hex with the target index hex.
      - If the source index hex is not found in the window, it will try all candidates for that outfit.
      - Logs the changes, including a failure reason if the index replacement did not occur.
    """
    modified_files = 0
    for file_name in os.listdir(directory_path):
        original_file_path = os.path.join(directory_path, file_name)
        if os.path.isfile(original_file_path):
            modded_file_path = os.path.join(output_path, file_name)
            read_path = modded_file_path if os.path.exists(modded_file_path) else original_file_path

            with open(read_path, 'rb') as f:
                content_bytes = f.read()
            hex_data = content_bytes.hex()
            file_modified = False

            for idx, (mod_source_hex, mod_target_hex) in enumerate(hex_pairs):
                item1, item2 = item_replacements[idx]
                occ = hex_data.count(mod_source_hex)
                mod_replaced = 0
                if occ >= 2:
                    first_index = hex_data.find(mod_source_hex)
                    second_index = hex_data.find(mod_source_hex, first_index + len(mod_source_hex))
                    if second_index != -1:
                        hex_data = hex_data[:second_index] + mod_target_hex + hex_data[second_index+len(mod_source_hex):]
                        mod_replaced = 1
                        file_modified = True

                    # Index replacement with fallback to alternate candidates
                    index_failure_reason = ""
                    if mod_replaced:
                        if not (item1 in index_hex_data and item2 in index_hex_data):
                            idx_occ = 0
                            index_failure_reason = "One or both index outfit names not found in index file."
                        else:
                            # For source, try all candidates
                            source_index_candidates = index_hex_data[item1]
                            # For target, take the first candidate (or you could also add a fallback here)
                            target_index_candidates = index_hex_data[item2]
                            target_index_hex = target_index_candidates[0]
                            window_start = max(0, first_index - 60)
                            window_end = first_index  # window before the first occurrence
                            window = hex_data[window_start:window_end]
                            found = False
                            for candidate in source_index_candidates:
                                if candidate in window:
                                    source_index_hex = candidate
                                    found = True
                                    break
                            if found:
                                new_window = window.replace(source_index_hex, target_index_hex, 1)
                                hex_data = hex_data[:window_start] + new_window + hex_data[window_end:]
                                idx_occ = 1
                            else:
                                idx_occ = 0
                                index_failure_reason = "Source index hex not found in expected window for any candidate."
                    else:
                        idx_occ = 0
                        index_failure_reason = ""

                    if mod_replaced:
                        changelog_entries.append({
                            'mod_type': mod_type,
                            'source_file': os.path.basename(txt_file),
                            'file_name': file_name,
                            'source_item': f"{item1} ({mod_source_hex})",
                            'target_item': f"{item2} ({mod_target_hex})",
                            'source_hex': mod_source_hex,
                            'target_hex': mod_target_hex,
                            'source_index': source_index_hex if mod_replaced and idx_occ else 'N/A',
                            'target_index': target_index_hex if mod_replaced and idx_occ else 'N/A',
                            'occurrences': mod_replaced,
                            'index_occurrences': idx_occ,
                            'index_failure_reason': index_failure_reason
                        })

            if file_modified:
                updated_data = bytes.fromhex(hex_data)
                os.makedirs(output_path, exist_ok=True)
                output_file_path = os.path.join(output_path, file_name)
                with open(output_file_path, 'wb') as f:
                    f.write(updated_data)
                modified_files += 1
    return modified_files

# =========================== HELPER: SINGLE PAIR SELECTION ===========================
def select_mod_option(mod_data):
    """Search and select an item from mod data by matching description (SkinID) or skin name.
       Returns (mod_hex, skin_name)."""
    search_term = input(f"\n{Fore.CYAN}🔍 Search item: ").lower()
    results = {}
    for hex_val, details in mod_data.items():
        if search_term in details['description'].lower() or search_term in details['skin_name'].lower():
            results[hex_val] = details
    if not results:
        print(f"{Fore.RED}🔍 No matches found!")
        return None, None
    print(f"\n{Fore.GREEN}📋 Results:")
    for idx, (hex_val, details) in enumerate(results.items(), 1):
        print(f"{Fore.CYAN}{idx}. {details['description']} - {details['skin_name']} ({hex_val})")
    while True:
        try:
            choice = int(input(f"\n{Fore.CYAN}🔢 Select item (1-{len(results)}): "))
            if 1 <= choice <= len(results):
                chosen_hex = list(results.keys())[choice-1]
                return chosen_hex, results[chosen_hex]['skin_name']
            print(f"{Fore.RED}❌ Invalid selection!")
        except ValueError:
            print(f"{Fore.RED}❌ Please enter a number!")

# =========================== MAIN FLOW ===========================
def mod_tool():
    print(f"\n{Fore.CYAN}🌟 Welcome to PUBG Mod Tool v2.0 🌟{Style.RESET_ALL}")
    
    txt_file, mod_type = select_txt_file()
    if not txt_file:
        return

    print(f"\n{Fore.YELLOW}⚙️ Loading {mod_type} data...")
    mod_data = fetch_mod_data(txt_file)
    if not mod_data:
        print(f"{Fore.RED}🚨 Failed to load mod data")
        return

    index_data = fetch_index_hex_from_file(INDEX_FILE_PATH)
    
    hex_pairs = []         # List of tuples: (source mod hex, target mod hex)
    item_replacements = [] # List of tuples: (source skin name, target skin name)

    if os.path.basename(txt_file).lower() == "all.txt":
        while True:
            print(f"\n{Fore.CYAN}🛠️ Current Mod Type: {mod_type}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}1. Add new replacement pair (search)")
            print("2. Bulk add skins by ID (sourceID,targetID)")
            print("q. Finish and apply modifications")
            choice = input(f"\n{Fore.CYAN}❔ Your choice (1,2,q): ").lower()
            if choice == '1':
                print(f"\n{Fore.CYAN}🔍 Select source item to replace:")
                hex1, id1 = select_mod_option(mod_data)
                if not hex1:
                    continue
                print(f"\n{Fore.CYAN}🎯 Select target replacement item:")
                hex2, id2 = select_mod_option(mod_data)
                if not hex2:
                    continue
                hex_pairs.append((hex1, hex2))
                item_replacements.append((id1, id2))
                print(f"\n{Fore.GREEN}✅ Added replacement: {id1} → {id2}")
            elif choice == '2':
                # Read bulk input until user types 'q'
                print(f"\n{Fore.CYAN}Enter bulk skin ID pairs (sourceID,targetID), one per line.")
                print("Type 'q' and press Enter on a new line when finished.")
                lines = []
                while True:
                    line = input().strip()
                    if line.lower() == 'q':
                        break
                    lines.append(line)
                for line in lines:
                    if not line:
                        continue
                    if ',' not in line:
                        print(f"{Fore.RED}❌ Format error. Use: sourceID,targetID")
                        continue
                    src_id, tgt_id = [s.strip() for s in line.split(',', 1)]
                    src_hex = None
                    tgt_hex = None
                    src_name = None
                    tgt_name = None
                    for mod_hex, data in mod_data.items():
                        if data["description"] == src_id:
                            src_hex = mod_hex
                            src_name = data["skin_name"]
                        if data["description"] == tgt_id:
                            tgt_hex = mod_hex
                            tgt_name = data["skin_name"]
                    if not src_hex or not tgt_hex:
                        print(f"{Fore.RED}❌ One or both skin IDs not found in the TXT data.")
                    else:
                        hex_pairs.append((src_hex, tgt_hex))
                        item_replacements.append((src_name, tgt_name))
                        print(f"{Fore.GREEN}✅ Added bulk replacement: {src_id} → {tgt_id}")
            elif choice == 'q':
                if not hex_pairs:
                    print(f"{Fore.RED}🚨 No replacements added!")
                    continue
                break
            else:
                print(f"{Fore.RED}❌ Invalid choice!")
    else:
        while True:
            print(f"\n{Fore.CYAN}🛠️ Current Mod Type: {mod_type}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}1. Add new replacement pair")
            print("2. Finish and apply modifications")
            choice = input(f"\n{Fore.CYAN}❔ Your choice (1-2): ")
            if choice == '1':
                print(f"\n{Fore.CYAN}🔍 Select source item to replace:")
                hex1, id1 = select_mod_option(mod_data)
                if not hex1:
                    continue
                print(f"\n{Fore.CYAN}🎯 Select target replacement item:")
                hex2, id2 = select_mod_option(mod_data)
                if not hex2:
                    continue
                hex_pairs.append((hex1, hex2))
                item_replacements.append((id1, id2))
                print(f"\n{Fore.GREEN}✅ Added replacement: {id1} → {id2}")
            elif choice == '2':
                if not hex_pairs:
                    print(f"{Fore.RED}🚨 No replacements added!")
                    continue
                break
            else:
                print(f"{Fore.RED}❌ Invalid choice!")
    
    if hex_pairs:
        total_modified = process_mods(ICON_MOD_DIR, hex_pairs, REPACK_OBB_DIR, 
                                      item_replacements, index_data, mod_type, txt_file)
        write_changelog()
        print(f"\n{Fore.GREEN}🎉 Successfully modified {total_modified} files!")
        print(f"{Fore.CYAN}📝 Changelog updated at: {CHANGELOG_PATH}")
    else:
        print(f"{Fore.RED}🚨 No modifications applied!")

# =========================== RUN ===========================
if __name__ == "__main__":
    mod_tool()

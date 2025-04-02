import os
import json
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Define file paths
TXT_DIR = "/storage/emulated/0/FILES_OBB/MOD_CAR/TXT/"
DAT_DIR = "/storage/emulated/0/FILES_OBB/MOD_CAR/DATS/"
REPACK_DIR = "/storage/emulated/0/FILES_OBB/REPACK_OBB/REPACK/"

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def load_txt_files():
    """Load all .txt files from the specified TXT directory."""
    if not os.path.exists(TXT_DIR):
        print(f"{Fore.RED}❌ Error: TXT directory not found: {TXT_DIR}{Style.RESET_ALL}")
        return []
    return [f for f in os.listdir(TXT_DIR) if f.endswith('.txt')]

def display_txt_files(txt_files):
    """Display .txt files with numbered options."""
    print(f"\n{Fore.CYAN}📂 Available vehicle files:{Style.RESET_ALL}")
    for idx, file in enumerate(txt_files, 1):
        print(f"{Fore.YELLOW}{idx}. {file.upper().replace('.TXT', '')}{Style.RESET_ALL}")
    while True:
        choice = input(f"\n{Fore.GREEN}🚗 Choose a file by number: {Style.RESET_ALL}").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(txt_files):
            return os.path.join(TXT_DIR, txt_files[int(choice)-1])
        print(f"{Fore.RED}❌ Invalid choice. Try again.{Style.RESET_ALL}")

def load_vehicle_data(file_path):
    """
    Load vehicle data from .txt file.
    Expected format per line: ID | HEX | Vehicle Name
    Malformed lines are silently skipped.
    """
    vehicles = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(' | ')
                if len(parts) == 3:
                    vehicle_id, hex_code, name = parts
                    vehicles.append({'id': vehicle_id.strip(), 'hex': hex_code.lower().strip(), 'name': name.strip()})
                # Silently skip lines that do not match the expected format
        if not vehicles:
            print(f"{Fore.RED}❌ Error: No valid vehicle data found in {file_path}!{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error reading file {file_path}: {e}{Style.RESET_ALL}")
    return vehicles

def select_vehicle(vehicles, prompt):
    """Vehicle selection with explicit input options."""
    print(f"\n{Fore.CYAN}{prompt}{Style.RESET_ALL}")
    while True:
        print(f"{Fore.MAGENTA}🔍 Choose input method:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1. Enter HEX directly{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}2. Search by vehicle name{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}3. Show full list and pick by number{Style.RESET_ALL}")
        choice = input(f"{Fore.GREEN}Your choice (1/2/3): {Style.RESET_ALL}").strip()
        
        if choice == '1':  # HEX input
            hex_input = input(f"{Fore.GREEN}Enter vehicle HEX: {Style.RESET_ALL}").lower().strip()
            for v in vehicles:
                if v['hex'] == hex_input:
                    return v['hex']
            print(f"{Fore.RED}❌ HEX not found. Try again.{Style.RESET_ALL}")
            
        elif choice == '2':  # Name search
            search_term = input(f"{Fore.GREEN}Enter vehicle name: {Style.RESET_ALL}").lower().strip()
            matches = [v for v in vehicles if search_term in v['name'].lower()]
            if not matches:
                print(f"{Fore.RED}❌ No matches. Try again.{Style.RESET_ALL}")
                continue
            for idx, v in enumerate(matches, 1):
                print(f"{Fore.YELLOW}{idx}. {v['name']} ({v['hex']}){Style.RESET_ALL}")
            while True:
                pick = input(f"{Fore.GREEN}Choose match by number: {Style.RESET_ALL}").strip()
                if pick.isdigit() and 1 <= int(pick) <= len(matches):
                    return matches[int(pick)-1]['hex']
                print(f"{Fore.RED}❌ Invalid choice. Try again.{Style.RESET_ALL}")
                
        elif choice == '3':  # Full list
            print(f"\n{Fore.CYAN}📋 Full vehicle list:{Style.RESET_ALL}")
            for idx, v in enumerate(vehicles, 1):
                print(f"{Fore.YELLOW}{idx}. {v['name']} ({v['hex']}){Style.RESET_ALL}")
            while True:
                pick = input(f"{Fore.GREEN}Choose vehicle by number: {Style.RESET_ALL}").strip()
                if pick.isdigit() and 1 <= int(pick) <= len(vehicles):
                    return vehicles[int(pick)-1]['hex']
                print(f"{Fore.RED}❌ Invalid choice. Try again.{Style.RESET_ALL}")
                
        else:
            print(f"{Fore.RED}❌ Invalid option. Please choose 1, 2, or 3.{Style.RESET_ALL}")

def modify_dat_file(source_dat, skin_hex, target_hex, revert=False):
    """Modify .dat file with proper offset handling."""
    try:
        with open(source_dat, 'rb') as f:
            data = bytearray(f.read())
        skin_bytes = bytes.fromhex(skin_hex)
        target_bytes = bytes.fromhex(target_hex)
        skin_pos = data.find(skin_bytes)
        target_pos = data.find(target_bytes)
        if skin_pos == -1 or target_pos == -1:
            print(f"\n{Fore.RED}❌ ERROR: One or both HEX values not found in .dat file{Style.RESET_ALL}")
            print(f"{Fore.RED}Missing: {'Skin HEX' if skin_pos == -1 else 'Target HEX'}{Style.RESET_ALL}")
            return None, None, None
        offset = 8
        try:
            skin_original_bytes = data[skin_pos-offset : skin_pos-offset+2]
            target_original_bytes = data[target_pos-offset : target_pos-offset+2]
        except IndexError:
            print(f"\n{Fore.RED}❌ ERROR: Invalid position calculation. HEX might be too close to start of file.{Style.RESET_ALL}")
            return None, None, None
        if revert:
            print(f"\n{Fore.GREEN}🔄 Reverting: {Fore.YELLOW}{skin_original_bytes.hex()} ➡️ {target_original_bytes.hex()}{Style.RESET_ALL}")
            data[skin_pos-offset : skin_pos-offset+2] = skin_original_bytes
        else:
            print(f"\n{Fore.GREEN}🔄 Replacement: {Fore.YELLOW}{skin_original_bytes.hex()} ➡️ {target_original_bytes.hex()}{Style.RESET_ALL}")
            data[skin_pos-offset : skin_pos-offset+2] = target_original_bytes
        os.makedirs(REPACK_DIR, exist_ok=True)
        output_path = os.path.join(REPACK_DIR, os.path.basename(source_dat))
        with open(output_path, 'wb') as f:
            f.write(data)
        print(f"{Fore.GREEN}✅ Successfully saved modified file to: {Fore.YELLOW}{output_path}{Style.RESET_ALL}")
        return output_path, skin_original_bytes.hex(), target_original_bytes.hex()
    except Exception as e:
        print(f"{Fore.RED}❌ Error modifying .dat file: {e}{Style.RESET_ALL}")
        return None, None, None

def load_changes_history():
    """Load changes history from a JSON file."""
    history_file = "changes_history.json"
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = f.read()
                if data.strip():
                    return json.loads(data)
                else:
                    print(f"{Fore.YELLOW}⚠️ Warning: Changes history file is empty. Starting with no history.{Style.RESET_ALL}")
                    return []
        except json.JSONDecodeError:
            print(f"{Fore.RED}❌ Error: Changes history file is corrupted. Starting with no history.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.YELLOW}⚠️ Warning: No changes history file found. Starting with no history.{Style.RESET_ALL}")
        return []

def save_changes_history(changes):
    """Save changes history to a JSON file."""
    history_file = "changes_history.json"
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(changes, f, indent=4)

def fresh_start(dat_files):
    """Perform a fresh start by copying the original .dat file to the repack folder."""
    if not dat_files:
        print(f"{Fore.RED}❌ Error: No .dat file found in the directory.{Style.RESET_ALL}")
        return None
    original_dat = dat_files[0]
    repack_dat = os.path.join(REPACK_DIR, os.path.basename(original_dat))
    os.makedirs(REPACK_DIR, exist_ok=True)
    if os.path.exists(repack_dat):
        os.remove(repack_dat)
    try:
        with open(original_dat, 'rb') as src, open(repack_dat, 'wb') as dst:
            dst.write(src.read())
        print(f"{Fore.GREEN}✅ Fresh start completed. Original .dat file copied to repack folder.{Style.RESET_ALL}")
        return repack_dat
    except Exception as e:
        print(f"{Fore.RED}❌ Error performing fresh start: {e}{Style.RESET_ALL}")
        return None

def display_changes_summary(changes, title="SUMMARY OF CHANGES"):
    """Display a summary of all changes made."""
    clear_screen()
    print(f"\n{Fore.CYAN}=== {title} ==={Style.RESET_ALL}")
    if not changes:
        print(f"{Fore.YELLOW}No changes were made.{Style.RESET_ALL}")
        return
    for idx, change in enumerate(changes, 1):
        print(f"{Fore.CYAN}{idx}. {Style.RESET_ALL}"
              f"{Fore.YELLOW}Skin Applied: {change['skin_name']} ({change['skin_hex']}){Style.RESET_ALL}\n"
              f"{Fore.YELLOW}Target Vehicle: {change['target_name']} ({change['target_hex']}){Style.RESET_ALL}\n"
              f"{Fore.GREEN}Modified File: {change['modified_file']}{Style.RESET_ALL}\n"
              f"{Fore.MAGENTA}Change Details: {Fore.YELLOW}{change['original_skin_hex']} ➡️ {change['new_skin_hex']}{Style.RESET_ALL}\n")
    print(f"{Fore.GREEN}✅ All changes have been saved successfully.{Style.RESET_ALL}")

def revert_changes(changes):
    """Allow the user to revert multiple changes by selecting numbers separated by commas."""
    while True:
        choice = input(f"\n{Fore.GREEN}Enter the numbers of the changes to revert (comma-separated, e.g., 1,2,3), or type 'q' to quit: {Style.RESET_ALL}").strip()
        if choice.lower() == 'q':
            return False
        selected_indices = []
        try:
            selected_indices = [int(num.strip()) for num in choice.split(",") if num.strip().isdigit()]
            selected_indices = [idx for idx in selected_indices if 1 <= idx <= len(changes)]
        except ValueError:
            print(f"{Fore.RED}❌ Invalid input. Please enter valid numbers separated by commas.{Style.RESET_ALL}")
            continue
        if not selected_indices:
            print(f"{Fore.RED}❌ No valid changes selected. Try again.{Style.RESET_ALL}")
            continue
        reverted_changes = []
        for idx in sorted(selected_indices, reverse=True):
            change_to_revert = changes[idx - 1]
            print(f"\n{Fore.CYAN}Reverting change: {Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Skin: {change_to_revert['skin_name']} ({change_to_revert['skin_hex']}){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Target: {change_to_revert['target_name']} ({change_to_revert['target_hex']}){Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}Change Details: {Fore.YELLOW}{change_to_revert['original_skin_hex']} ➡️ {change_to_revert['new_skin_hex']}{Style.RESET_ALL}")
            modify_dat_file(change_to_revert['modified_file'], 
                            change_to_revert['skin_hex'], 
                            change_to_revert['target_hex'], 
                            revert=True)
            reverted_changes.append(change_to_revert)
            del changes[idx - 1]
        display_changes_summary(reverted_changes, title="REVERTED CHANGES")
        print(f"{Fore.GREEN}✅ Changes reverted successfully.{Style.RESET_ALL}")
        return True

def bulk_modding(dat_files):
    """
    Perform bulk modding using a list of source and target IDs.
    Always starts fresh and uses the TXT file named ALL.txt.
    """
    clear_screen()
    # Always perform a fresh start
    dat_file = fresh_start(dat_files)
    if dat_file is None:
        return

    # Use the fixed file ALL.txt from the TXT directory
    all_txt_path = os.path.join(TXT_DIR, "ALL.txt")
    if not os.path.exists(all_txt_path):
        print(f"{Fore.RED}❌ Error: ALL.txt not found in {TXT_DIR}{Style.RESET_ALL}")
        input(f"{Fore.YELLOW}Press Enter to exit Bulk Modding...{Style.RESET_ALL}")
        return

    vehicles = load_vehicle_data(all_txt_path)
    
    # Gather bulk entries from user
    print(f"\n{Fore.CYAN}Enter bulk modding pairs (SOURCE ID, TARGET ID), one per line.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Example: 402213,401985{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Enter 'q' on a new line to finish input.{Style.RESET_ALL}")
    bulk_entries = []
    while True:
        line = input().strip()
        if line.lower() == 'q':
            break
        if ',' in line:
            parts = line.split(',')
            if len(parts) == 2:
                source_id = parts[0].strip()
                target_id = parts[1].strip()
                bulk_entries.append((source_id, target_id))
            else:
                print(f"{Fore.RED}❌ Invalid format. Please enter exactly two values separated by a comma.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Invalid format. Use comma-separated values (e.g., 402213,401985).{Style.RESET_ALL}")
    
    changes_made = []
    # Process each bulk entry
    for source_id, target_id in bulk_entries:
        source_vehicle = next((v for v in vehicles if v['id'] == source_id), None)
        target_vehicle = next((v for v in vehicles if v['id'] == target_id), None)
        if not source_vehicle or not target_vehicle:
            missing = source_id if not source_vehicle else target_id
            print(f"{Fore.RED}❌ Vehicle with ID {missing} not found. Skipping this entry.{Style.RESET_ALL}")
            continue
        
        source_hex = source_vehicle['hex']
        target_hex = target_vehicle['hex']
        print(f"\n{Fore.CYAN}Processing: {source_vehicle['name']} ({source_hex}) -> {target_vehicle['name']} ({target_hex}){Style.RESET_ALL}")
        modified_file, original_skin_hex, new_skin_hex = modify_dat_file(dat_file, source_hex, target_hex)
        if modified_file:
            changes_made.append({
                'skin_name': source_vehicle['name'],
                'skin_hex': source_hex,
                'target_name': target_vehicle['name'],
                'target_hex': target_hex,
                'modified_file': modified_file,
                'original_skin_hex': original_skin_hex,
                'new_skin_hex': new_skin_hex
            })
            # Update dat_file for subsequent changes
            dat_file = modified_file
    
    display_changes_summary(changes_made)
    save_changes_history(changes_made)
    input(f"\n{Fore.YELLOW}Press Enter to exit Bulk Modding...{Style.RESET_ALL}")

def main():
    clear_screen()
    print(f"{Fore.CYAN}🚗 Vehicle Skin Swapper 🎨{Style.RESET_ALL}")
    print(f"{Fore.CYAN}-------------------------{Style.RESET_ALL}")
    
    # Load required files
    txt_files = load_txt_files()
    dat_files = [os.path.join(DAT_DIR, f) for f in os.listdir(DAT_DIR) if f.endswith('.dat')]
    
    if not txt_files or not dat_files:
        print(f"{Fore.RED}❌ Error: Missing required files (.txt and/or .dat){Style.RESET_ALL}")
        input(f"{Fore.YELLOW}Press Enter to exit...{Style.RESET_ALL}")
        return
    
    # Updated Start Options: Bulk Modding now appears as option 3.
    while True:
        print(f"\n{Fore.CYAN}=== START OPTIONS ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1. Fresh Start{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}2. Continue from Last Saved{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}3. Bulk Modding (using ALL.txt){Style.RESET_ALL}")
        choice = input(f"{Fore.GREEN}Your choice (1/2/3): {Style.RESET_ALL}").strip()
        if choice == '1':
            dat_file = fresh_start(dat_files)
            changes_made = []
            break
        elif choice == '2':
            repack_dat = os.path.join(REPACK_DIR, os.path.basename(dat_files[0]))
            if not os.path.exists(repack_dat):
                print(f"{Fore.RED}❌ Error: No saved .dat file found in the repack folder. Starting fresh...{Style.RESET_ALL}")
                dat_file = fresh_start(dat_files)
            else:
                dat_file = repack_dat
            changes_made = []
            break
        elif choice == '3':
            bulk_modding(dat_files)
            return  # Exit main after bulk modding.
        else:
            print(f"{Fore.RED}❌ Invalid choice. Try again.{Style.RESET_ALL}")
    
    # Single modding loop
    while True:
        txt_file = display_txt_files(txt_files)
        vehicles = load_vehicle_data(txt_file)
        clear_screen()
        print(f"{Fore.CYAN}=== SKIN SELECTION ==={Style.RESET_ALL}")
        skin_hex = select_vehicle(vehicles, "Choose the SKIN you want to apply:")
        skin_name = next((v['name'] for v in vehicles if v['hex'] == skin_hex), "Unknown")
        clear_screen()
        print(f"{Fore.CYAN}=== TARGET VEHICLE ==={Style.RESET_ALL}")
        target_hex = select_vehicle(vehicles, "Choose vehicle to apply the skin to:")
        target_name = next((v['name'] for v in vehicles if v['hex'] == target_hex), "Unknown")
        modified_file, original_skin_hex, new_skin_hex = modify_dat_file(dat_file, skin_hex, target_hex)
        if modified_file:
            changes_made.append({
                'skin_name': skin_name,
                'skin_hex': skin_hex,
                'target_name': target_name,
                'target_hex': target_hex,
                'modified_file': modified_file,
                'original_skin_hex': original_skin_hex,
                'new_skin_hex': new_skin_hex
            })
            dat_file = modified_file
        if input(f"\n{Fore.GREEN}Make another change? (y/n): {Style.RESET_ALL}").lower() != 'y':
            break
        clear_screen()
    
    display_changes_summary(changes_made)
    while True:
        if not changes_made:
            print(f"{Fore.YELLOW}No changes left to revert.{Style.RESET_ALL}")
            break
        if input(f"\n{Fore.GREEN}Would you like to revert any changes? (y/n): {Style.RESET_ALL}").lower() != 'y':
            break
        if not revert_changes(changes_made):
            break
    
    save_changes_history(changes_made)
    if input(f"\n{Fore.GREEN}Would you like to add more skins? (y/n): {Style.RESET_ALL}").lower() == 'y':
        main()
    else:
        print(f"\n{Fore.CYAN}👋 Thank you for using the Vehicle Skin Swapper! 🚗🎨✨{Style.RESET_ALL}")
        input(f"{Fore.YELLOW}Press Enter to exit...{Style.RESET_ALL}")

if __name__ == "__main__":
    main()

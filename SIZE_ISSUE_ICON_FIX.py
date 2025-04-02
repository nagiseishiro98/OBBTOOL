import os
import re
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

# ---------------------------
# Configuration
# ---------------------------
TXT_DIR = r"/storage/emulated/0/FILES_OBB/MOD_ANY ICON/TXT"
REPACK_DIR = r"/storage/emulated/0/FILES_OBB/REPACK_OBB/SIZEICONFIX/"

# ---------------------------
# Helper: Find all occurrences of a byte sequence in a bytes object.
# ---------------------------
def find_all_occurrences(data, sub):
    positions = []
    start = 0
    while True:
        pos = data.find(sub, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1
    return positions

# ---------------------------
# Helper: Parse a changelog block.
# ---------------------------
def parse_changelog_block(block):
    repack_file_match = re.search(r"File:\s*(.+)", block)
    source_item_match = re.search(r"Source Item:\s*(.+?)\s*\(([\da-fA-F]+)\)", block)
    target_item_match = re.search(r"Target Item:\s*(.+?)\s*\(([\da-fA-F]+)\)", block)
    if not (repack_file_match and source_item_match and target_item_match):
        return None
    repack_filename = repack_file_match.group(1).strip()
    source_name = source_item_match.group(1).strip().lower()
    source_hex = source_item_match.group(2).strip().lower()
    target_name = target_item_match.group(1).strip().lower()
    target_hex = target_item_match.group(2).strip().lower()
    hex_exclusions = {source_hex, target_hex}
    name_exclusions = {source_name, target_name}
    index_exclusions = set()
    index_replaced_match = re.search(r"Index replaced:\s*(\w+)\s+with\s+(\w+)", block)
    if index_replaced_match:
        index_exclusions.update({ index_replaced_match.group(1).strip().lower(),
                                  index_replaced_match.group(2).strip().lower() })
    return {
        "repack_filename": repack_filename,
        "hex_exclusions": hex_exclusions,
        "index_exclusions": index_exclusions,
        "name_exclusions": name_exclusions
    }

# ---------------------------
# Helper: Load valid hex codes from ALL.txt.
# ---------------------------
def load_valid_hexes():
    valid_hexes = {}
    txt_filename = "ALL.txt"
    txt_path = os.path.join(TXT_DIR, txt_filename)
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 3:
                hex_val = parts[1].strip().lower()
                skin_name = parts[2].strip()
                valid_hexes[hex_val] = skin_name
    return valid_hexes

# ---------------------------
# Main Process
# ---------------------------
def process_changelog():
    # Read changelog file.
    changelog_path = os.path.join(REPACK_DIR, "changelog.txt")
    with open(changelog_path, "r", encoding="utf-8") as f:
        changelog_content = f.read()
    
    # Split into blocks.
    blocks = [block.strip() for block in changelog_content.split("==============================") if block.strip()]
    
    # Group modifications by repack file.
    file_groups = {}  # key: repack filename; value: { path, content, hex_exclusions, index_exclusions, name_exclusions }
    for block in blocks:
        data = parse_changelog_block(block)
        if not data:
            continue
        repack_filename = data["repack_filename"]
        if repack_filename not in file_groups:
            repack_file_path = os.path.join(REPACK_DIR, repack_filename)
            with open(repack_file_path, "rb") as repack_file:
                content = repack_file.read()
            file_groups[repack_filename] = {
                "path": repack_file_path,
                "content": content,
                "hex_exclusions": set(),
                "index_exclusions": set(),
                "name_exclusions": set()
            }
        file_groups[repack_filename]["hex_exclusions"].update(data["hex_exclusions"])
        file_groups[repack_filename]["index_exclusions"].update(data["index_exclusions"])
        file_groups[repack_filename]["name_exclusions"].update(data["name_exclusions"])
    
    valid_hexes = load_valid_hexes()
    # For reporting: track name-based exclusions.
    name_based_exclusions = {}

    # Dictionary to record which hex values were nulled for each file (with counts).
    nulled_hexes_by_file = {}
    
    for repack_filename, group in file_groups.items():
        original_content = group["content"]  # Backup of original file content.
        content = group["content"]
        unified_exclusions = group["hex_exclusions"].union(group["index_exclusions"])
        total_replacements = 0
        # Use a dictionary to record each nulled hex and its count.
        nulled_hexes = {}
        
        # Process each valid hex from ALL.txt.
        for hex_code, skin_name in valid_hexes.items():
            # Skip if the hex code is explicitly excluded.
            if hex_code in unified_exclusions:
                continue
            # Also skip if the skin name matches any name exclusion (case-insensitive substring check).
            lower_skin_name = skin_name.lower()
            skip_by_name = False
            for excl in group["name_exclusions"]:
                if excl in lower_skin_name or lower_skin_name in excl:
                    skip_by_name = True
                    name_based_exclusions.setdefault(repack_filename, set()).add(skin_name)
                    break
            if skip_by_name:
                continue
            try:
                hex_bytes = bytes.fromhex(hex_code)
            except ValueError:
                continue
            null_bytes = b'\x00' * len(hex_bytes)
            occurrences = content.count(hex_bytes)
            if occurrences > 0:
                content = content.replace(hex_bytes, null_bytes)
                total_replacements += occurrences
                nulled_hexes[hex_code] = occurrences
        
        # Now, restore any excluded hex values from the original content.
        for ex in unified_exclusions:
            try:
                ex_bytes = bytes.fromhex(ex)
            except ValueError:
                continue
            positions = find_all_occurrences(original_content, ex_bytes)
            for pos in positions:
                content = content[:pos] + ex_bytes + content[pos+len(ex_bytes):]
        
        # Write the final content back to file.
        with open(group["path"], "wb") as repack_file:
            repack_file.write(content)
        
        # Save the nulled hex report for this file.
        nulled_hexes_by_file[repack_filename] = nulled_hexes
        
        # Prepare summary lists for console output.
        excluded_by_hex = [valid_hexes.get(x, x) for x in sorted(group["hex_exclusions"])]
        excluded_index = [valid_hexes.get(x, x) for x in sorted(group["index_exclusions"])]
        excluded_by_name = sorted(name_based_exclusions.get(repack_filename, []))
        
        print(f"{Fore.CYAN}Processed File: {repack_filename}")
        print(f"{Fore.RED}Total skins nulled: {total_replacements}")
        print(f"{Fore.YELLOW}Excluded (by hex): {', '.join(excluded_by_hex) if excluded_by_hex else 'None'}")
        print(f"{Fore.YELLOW}Excluded (index): {', '.join(excluded_index) if excluded_index else 'None'}")
        print(f"{Fore.YELLOW}Excluded (by name matching): {', '.join(excluded_by_name) if excluded_by_name else 'None'}")
        print(Style.RESET_ALL + "-------------------------------------------------")
    
    # ---------------------------
    # Write null.txt report in the repack folder.
    # ---------------------------
    report_lines = []
    report_lines.append("Null Hex Values Report")
    report_lines.append("======================\n")
    
    for repack_filename, nulled_hexes in nulled_hexes_by_file.items():
        report_lines.append(f"File: {repack_filename}")
        if nulled_hexes:
            # Write one line per hex value.
            for hex_code, count in sorted(nulled_hexes.items()):
                skin_name = valid_hexes.get(hex_code, "Unknown")
                report_lines.append(f"  {skin_name} ({hex_code}) : {count}")
        else:
            report_lines.append("  Nulled Hex Values: None")
        report_lines.append("")  # Blank line for separation

    null_report_path = os.path.join(REPACK_DIR, "null.txt")
    with open(null_report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    
    print(f"{Fore.GREEN}Null report written to: {null_report_path}")
    
if __name__ == "__main__":
    process_changelog()

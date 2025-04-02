import os
import time
from termcolor import colored
from colorama import Fore

# Function to clear the screen
def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

# Function to display text with vertical color cycling
def color_cycled_text(text):
    """Displays the provided text in a vertical color cycling pattern."""
    colors = ['yellow', 'green', 'cyan', 'magenta', 'light_magenta', 'red']
    for i, line in enumerate(text.splitlines()):
        colored_line = "".join(colored(char, colors[j % len(colors)], attrs=['bold']) for j, char in enumerate(line))
        print(colored_line)

def display_tool_name():
    """Display the tool name in rainbow colors with vertical color cycling."""
    clear_screen()  # Clear the screen before displaying the tool name
    
    tool_name = """

 █████╗░██████╗░█████╗░  
██╔══██╗██╔══██╗██╔══██╗  
██║░░██║██████╦╝██████╦╝  
██║░░██║██╔══██╗██╔══██╗  
╚█████╔╝██████╦╝██████╦╝  
╚════╝░╚═════╝░╚═════╝░
    """
    # Apply vertical color cycling to the tool name
    color_cycled_text(tool_name)

    # Print the tag below in cyan
    print(colored("                   @UNKNWON", 'cyan', attrs=['bold']))

# Define paths
BASE_PATH = "/storage/emulated/0/FILES_OBB/AUTO_THEME/"
FILES_PATH = os.path.join(BASE_PATH, "FILES")
RESULT_PATH = "/storage/emulated/0/FILES_OBB/REPACK_OBB/REPACK/"  # Updated result path
TXT_PATH = os.path.join(BASE_PATH, "TXT")
LOBBY_FILE = os.path.join(TXT_PATH, "lobby.txt")
DEF_FILE = os.path.join(TXT_PATH, "def.txt")

# Function to read the default index from def.txt
def read_def_index():
    try:
        with open(DEF_FILE, "r") as file:
            for line in file:
                if "Index" in line:
                    return line.split(":")[1].strip()
        print(colored("Index not found in def.txt.", 'yellow'))
        return None
    except FileNotFoundError:
        print(colored("def.txt not found.", 'red'))
        return None

# Function to read lobbies from lobby.txt
def read_lobbies():
    lobbies = []
    try:
        with open(LOBBY_FILE, "r") as file:
            for line in file:
                parts = line.strip().split("|")
                if len(parts) == 3:
                    lobbies.append((parts[1].strip(), parts[2].strip()))  # Hex and Name
        return lobbies
    except FileNotFoundError:
        print(colored("lobby.txt not found.", 'red'))
        return None

# Function to replace the index in hex files
def replace_index_in_files(hex_sequence, new_index):
    try:
        for filename in os.listdir(FILES_PATH):
            file_path = os.path.join(FILES_PATH, filename)

            with open(file_path, "rb") as file:
                file_data = file.read()

            # Convert inputs to bytes
            new_index_bytes = bytes.fromhex(new_index)
            hex_bytes = bytes.fromhex(hex_sequence)

            # Look for the pattern and replace the index
            updated_data = bytearray(file_data)
            found = False

            # Loop through the data to find the pattern starting from the last byte
            for i in range(len(file_data) - len(hex_bytes), 7, -1):  # Start 8 bytes before the hex
                # Check if the hex sequence matches at the current position
                if file_data[i:i + len(hex_bytes)] == hex_bytes:
                    # Extract the index byte 8 bytes before the hex sequence (starting from i-8)
                    index_byte = file_data[i - 8]

                    # Replace the found index with the new index
                    updated_data[i - 8] = new_index_bytes[0]  # Replace the single byte index
                    found = True

                    print(colored(f"Modified {filename}: Replaced index {index_byte:02x} with {new_index} for hex sequence {hex_sequence}.", 'green'))

            # Save the updated file
            result_path = os.path.join(RESULT_PATH, filename)
            with open(result_path, "wb") as file:
                file.write(updated_data)

            if not found:
                print(colored(f"No matching pattern found in {filename}.", 'yellow'))
    except Exception as e:
        print(colored(f"Error: {e}", 'red'))

# Main menu
def main_menu():
    while True:
        display_tool_name()
        color_cycled_text("\nDARKSIDE")
        print(colored("1] MOD LOBBY", 'yellow', attrs=['bold']))
        print(colored("2] QUIT", 'green', attrs=['bold']))
        choice = input(colored("Choose an option: ", 'magenta', attrs=['bold']))

        if choice == "1":
            lobbies = read_lobbies()
            def_index = read_def_index()

            if not lobbies or not def_index:
                print(colored("Required files or data missing.", 'red'))
                continue

            color_cycled_text("\nAvailable Lobbies:")
            for i, (_, name) in enumerate(lobbies, 1):
                print(colored(f"{i}. {name}", 'green'))

            lobby_choice = input(colored("Select a lobby theme by number: ", 'magenta', attrs=['bold']))

            try:
                lobby_choice = int(lobby_choice) - 1
                if 0 <= lobby_choice < len(lobbies):
                    lobby_hex, lobby_name = lobbies[lobby_choice]
                    print(colored(f"Modding lobby theme: {lobby_name}", 'yellow'))
                    replace_index_in_files(lobby_hex, def_index)
                else:
                    print(colored("Invalid selection.", 'red'))
            except ValueError:
                print(colored("Invalid input. Please enter a number.", 'red'))

        elif choice == "2":
            print(colored("Exiting the program. Goodbye!", 'yellow'))
            break
        else:
            print(colored("Invalid choice. Please try again.", 'red'))

# Run the script
if __name__ == "__main__":
    main_menu()
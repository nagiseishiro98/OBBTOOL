import os

# Permanent paths
SOURCE_DIR = "/storage/emulated/0/FILES_OBB/CREDIT_MOD/dats/"
OUTPUT_DIR = "/storage/emulated/0/FILES_OBB/REPACK_OBB/REPACK/"

def read_binary_file(file_path):
    """Reads the content of a binary file."""
    try:
        with open(file_path, 'rb') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None

def write_binary_file(file_path, data):
    """Writes data to a binary file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the output directory exists
        with open(file_path, 'wb') as file:
            file.write(data)
        print(f"Modified file saved to: {file_path}")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")

def replace_string_in_binary(file_path, old_text, new_text):
    """Replaces a string in a binary file."""
    # Read the binary file
    binary_data = read_binary_file(file_path)
    if binary_data is None:
        return False

    # Convert the strings to bytes
    old_bytes = old_text.encode('utf-8')
    new_bytes = new_text.encode('utf-8')

    # Check if the old text exists in the binary data
    if old_bytes not in binary_data:
        return False

    # Replace the old text with the new text
    new_binary_data = binary_data.replace(old_bytes, new_bytes.ljust(len(old_bytes), b'\x00'))

    # Write the updated binary data to the output directory
    file_name = os.path.basename(file_path)
    output_file_path = os.path.join(OUTPUT_DIR, file_name)
    write_binary_file(output_file_path, new_binary_data)
    return True

def main():
    while True:
        print("\nMenu:")
        print("1. MOD CREDIT")
        print("2. QUIT")
        choice = input("Enter your choice (1 or 2): ").strip()

        if choice == '1':
            text_to_find = input("Enter The Text to Find 🔍: ").strip()
            if not text_to_find:
                print("Error: Text to find cannot be empty. Please try again.")
                continue

            # List all .dat files in the source directory
            try:
                dat_files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.dat')]
                if not dat_files:
                    print("No .dat files found in the source directory.")
                    continue

                found = False
                for dat_file in dat_files:
                    file_path = os.path.join(SOURCE_DIR, dat_file)
                    binary_data = read_binary_file(file_path)

                    if binary_data and text_to_find.encode('utf-8') in binary_data:
                        print(f"Text '{text_to_find}' FOUND in file: {dat_file}")
                        found = True

                        while True:
                            new_text = input("Enter Your Credit Text🔍: ").strip()
                            if not new_text:
                                print("Error: New text cannot be empty. Please try again.")
                                continue

                            success = replace_string_in_binary(file_path, text_to_find, new_text)
                            if success:
                                print(f"CREDIT SUCCESSFULLY ADDED 💀")
                                break
                            else:
                                print("An unexpected error occurred while replacing the text. Please try again.")

                if not found:
                    print(f"Text '{text_to_find}' was NOT FOUND in any .dat file.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

        elif choice == '2':
            print("Exiting the program. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()
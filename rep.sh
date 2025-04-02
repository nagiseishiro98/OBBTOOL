
#!/bin/bash
# ------------------------------------------------------------
# Variables & Colors
# ------------------------------------------------------------
NOCOLOR='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
LIGHTGREEN='\033[1;32m'

# Define directories based on your instructions
ORIGINAL_DIR="/storage/emulated/0/FILES_OBB/ORIGINAL"
tx="${ORIGINAL_DIR}/OBB"
dobb="${tx}/output"
REPACK_DIR="/storage/emulated/0/FILES_OBB/REPACK_OBB"

# ------------------------------------------------------------
# Check for Python 'rich' module
# ------------------------------------------------------------
python3 -c "import rich" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: The Python 'rich' module is not installed. Please install it with 'pip3 install rich'.${NOCOLOR}"
    exit 1
fi

# ------------------------------------------------------------
# Setup required directories
# ------------------------------------------------------------
mkdir -p "$ORIGINAL_DIR" "$tx" "$dobb" "$REPACK_DIR"

# ------------------------------------------------------------
# Smooth Loading Animation using rich
# ------------------------------------------------------------
function rich_loading_animation {
    local message="$1"
    local duration="${2:-2}"  # duration in seconds, default is 2 seconds
    python3 - <<EOF
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
import time
duration = float("$duration")
with Progress(SpinnerColumn(), BarColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
    task = progress.add_task("$message", total=100)
    for i in range(100):
        time.sleep(duration/100)
        progress.update(task, advance=1)
EOF
}

# ------------------------------------------------------------
# Helper Functions (sizeupdown and fnsh remain unchanged)
# ------------------------------------------------------------
function sizeupdown {
    cd "$dobb" || exit
    obbsize=$(cat "$tx/sizeobb.ini")
    count=$(printf $(du -b *.obb.zip))
    if [ $count -lt $obbsize ]; then
        while [ $count -lt $obbsize ]; do
            truncate -s+1 *.zip
            printf "$count\n"
            let count=count+1
        done
    else
        while [ $count -gt $obbsize ]; do
            truncate -s-1 *.zip
            printf "$count\n"
            let count=count-1
        done
    fi
}

function fnsh {
    cd "$dobb" || exit
    obbsize=$(cat "$tx/sizeobb.ini")
    count=$(printf $(du -b *.zip))
    if [ $count -lt $obbsize ]; then
        while [ $count -lt $obbsize ]; do
            truncate -s+100 *.zip
            printf "$count\n"
            let count=count+100
        done
        sizeupdown
    else
        while [ $count -gt $obbsize ]; do
            truncate -s-100 *.zip
            printf "$count\n"
            let count=count-100
        done
        sizeupdown
    fi
}

# ------------------------------------------------------------
# Repackobb Function (updated to exclude current directory)
# ------------------------------------------------------------
function repackobb {
    printf "\n"
    echo -e "${YELLOW}Starting RePacking OBB Files.${NOCOLOR}"
    cd "$dobb" || exit
    mv "$tx"/*zip "$dobb" 2>/dev/null
    obbnm=$(find . -maxdepth 1 -name "*zip")
    # Exclude the current directory (".") from the list:
    obbdir=$(find . -maxdepth 1 -type d ! -name ".")
    zip -u -0 $obbnm
    fnsh
    printf "\n\n"
    cd "$dobb" || exit
    obbsize=$(cat "$tx/sizeobb.ini")
    four=$(printf $(du -b *zip))
    five=$(expr $obbsize - $four)
    six=$(expr $five / 8)
    mv $(for file in *.zip; do basename "$file" .obb.zip; done;).obb.zip $(for file in *.zip; do basename "$file" .obb.zip; done;).obb
    rm -rf "$tx/sizeobb.ini"
    rm -rf $obbdir
    echo -e "${LIGHTGREEN}FINISH${NOCOLOR}"
    printf "\n"
}

# ------------------------------------------------------------
# Unpackobb Function (unchanged)
# ------------------------------------------------------------
function unpackobb {
    printf "\n"
    echo -e "${YELLOW}Starting UnPacking OBB files...${NOCOLOR}"
    cd "$dobb" || exit
    for f in *obb; do
        [ -e "$f" ] && mv "$f" "$f.zip"
    done
    echo $(printf $(du -b *.obb.zip)) > "$tx/sizeobb.ini"
    printf "\n\n"
    unzip *.obb.zip
    sleep 1
    mv *.obb.zip "$tx" 2>/dev/null
    printf "\n\n"
    echo -e "${LIGHTGREEN}DONE.${NOCOLOR}"
    printf "\n"
}

# ------------------------------------------------------------
# Main Process: repak_obb
# ------------------------------------------------------------
function repak_obb {
    echo -e "${GREEN}=== STARTING OBB REPACK PROCESS ===${NOCOLOR}"
    
    # --- Pre-check and cleanup ---
    echo -e "${YELLOW}Checking and cleaning previous outputs...${NOCOLOR}"
    # Delete any existing .obb files in the output folder
    if compgen -G "$dobb"/*.obb > /dev/null; then
        rm -f "$dobb"/*.obb
        echo -e "${YELLOW}Previous OBB files deleted from ${dobb}.${NOCOLOR}"
    fi
    # Delete previous mini_obb.pak in the repack folder
    if [ -f "${REPACK_DIR}/mini_obb.pak" ]; then
        rm -f "${REPACK_DIR}/mini_obb.pak"
        echo -e "${YELLOW}Existing mini_obb.pak deleted from ${REPACK_DIR}.${NOCOLOR}"
    fi
    # Delete any existing .zip files in the OBB folder
    if compgen -G "$tx"/*.zip > /dev/null; then
        rm -f "$tx"/*.zip
        echo -e "${YELLOW}Previous zip files deleted from ${tx}.${NOCOLOR}"
    fi
    # Delete sizeobb.ini in the OBB folder if it exists
    if [ -f "$tx/sizeobb.ini" ]; then
        rm -f "$tx/sizeobb.ini"
        echo -e "${YELLOW}sizeobb.ini deleted from ${tx}.${NOCOLOR}"
    fi
    # Delete the folder 'ShadowTrackerExtra' in the output folder if it exists
    if [ -d "$dobb/ShadowTrackerExtra" ]; then
        rm -rf "$dobb/ShadowTrackerExtra"
        echo -e "${YELLOW}Folder 'ShadowTrackerExtra' deleted from ${dobb}.${NOCOLOR}"
    fi
    rich_loading_animation "Cleaning up" 1

    # Step 1: Copy original OBB file(s) to output folder
    echo -e "${YELLOW}Copying original OBB file(s) from ${ORIGINAL_DIR} to ${dobb}...${NOCOLOR}"
    rich_loading_animation "Copying Files" 2
    cp "$ORIGINAL_DIR"/*.obb "$dobb"/ 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: No .obb file found in ${ORIGINAL_DIR}.${NOCOLOR}"
        exit 1
    fi

    # Step 2: Unpack the OBB file(s)
    echo -e "${YELLOW}Unpacking OBB file(s)...${NOCOLOR}"
    rich_loading_animation "Unpacking Files" 2
    cd "$dobb" || exit
    unpackobb

    # Step 3: Copy mini_obb.pak from unpacked folder to repack folder
    PAK_SRC="${dobb}/ShadowTrackerExtra/Content/Paks/mini_obb.pak"
    if [ ! -f "$PAK_SRC" ]; then
        echo -e "${RED}Error: mini_obb.pak not found at ${PAK_SRC}.${NOCOLOR}"
        exit 1
    fi
    echo -e "${YELLOW}Copying mini_obb.pak to repack folder ${REPACK_DIR}...${NOCOLOR}"
    rich_loading_animation "Copying mini_obb.pak" 2
    cp "$PAK_SRC" "${REPACK_DIR}/" 2>/dev/null

    # Step 4: Repack mini_obb.pak using quickbms
    echo -e "${YELLOW}Repacking mini_obb.pak using quickbms...${NOCOLOR}"
    rich_loading_animation "Repacking mini_obb.pak" 2
    qemu-i386 "$PREFIX/share/quickbms/quickbms" -w -r -r ~/repak.bms "${REPACK_DIR}/mini_obb.pak" "${REPACK_DIR}/"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: quickbms repack command failed.${NOCOLOR}"
        exit 1
    fi

    # Step 5: Overwrite the original mini_obb.pak with the repacked one
    echo -e "${YELLOW}Replacing original mini_obb.pak with repacked version...${NOCOLOR}"
    rich_loading_animation "Replacing mini_obb.pak" 2
    cp "${REPACK_DIR}/mini_obb.pak" "$PAK_SRC"
    
    # Step 6: Repack the full OBB using repackobb
    echo -e "${YELLOW}Repacking full OBB file...${NOCOLOR}"
    rich_loading_animation "Repacking Full OBB" 2
    repackobb

    echo -e "${GREEN}=== OBB Repack Process Completed Successfully ===${NOCOLOR}"
}

# ------------------------------------------------------------
# Execute the process
# ------------------------------------------------------------
repak_obb

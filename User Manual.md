This page is dedicated to teach users how to use Ultimate Free Space Finder (UFSF).

# Installation
[Python](https://www.python.org/downloads/)
1. Go to the link and select the version for your OS.
2. After installation, you can run the program.
   
# Opening and Saving a ROM
1. Navigate to "File" at the top of the program.
2. Select "Load Last ROM" to load the last ROM you opened with the program.
3. Select "Open ROM" to select a ROM from your files to load into the program.
4. Select "Save ROM" to save edits from the hex editor to your ROM.

Note: A backup of your ROM will be created at the same location.

# Using the Hex Editor
1. On the "Hex Editor" tab (also the landing page), you will see the Hex Editor.
2. You can click a set of bytes and it will highlight your selection.
3. Any changes made in the hex editor can be saved in the File Menu.
4. ASCII viewer is on the right.

# Using the Free Space Finder
1. Format: Changing this option will automatically format the start of your offsets into the selected mode (0x, $, plain) for whatever tool you are using.
2. Search Type: Changing this option will allow you to search for different bytes when searching for free space (00, FF).
3. Start Offset: This is where you want the ROM to start searching for data. Clicking inside the Hex Viewer will automatically update this value.
4. Free Space Size: This is the requested side of free space to search for (in bytes).
5. Skip Interval: This value allows you to add extra bytes to the end of your search value (in bytes). Basically, it allows you to leave headroom for data that may need expansion.
6. Find Free Space (Button): Click this to search for Free Space. Clicking this button will automatically take you to your offset in the Hex Editor.
7. Go to Offset: This value allows you to jump to a location in the Hex Editor. Clicking inside the Hex Viewer automatically updates this value.
8. Scroll to Offset (Button): Click this to navigate to the offset you have filled in. Will also highlight the offset when navigation is finished.

# Search Results
When you click the "Find Free Space" button, you will see data populate in the "Search Results" field.
1. Start: This is your offset where free space begins. You will input this value into whatever tool you're using to allocate the free space.
2. End: This is where your free space ends. Note that this **includes** your skip interval as well.
3. Skip interval: This is how many bytes were added to your request size during the search.
4. Total Allocation: The sum of size request and skip interval.
5. Total free block size: This is the total amount of space until free space ends, from the beginning of your offset. Going beyond this data will overwrite other data on the ROM.
6. Reamining in block: This is how much free space is remaining after subtracting your total allocation from the total free block size.
7. Next available offset: This is the offset after your total allocation.
8. Block extends to: This is the last address in the entire free block (after your allocation).

# TOOLS (OFFSET CALCULATOR)
1. Open the Offset Calculator by clicking on Tools -> Offset Calculator.
2. Format: Changing this option will format your search to use the requested value (0x, $, plain)
3. Start Offset: This is the offset you'd like to start your search at.
4. Byte Count: The total number of bytes you'd like to search after your start offset.
5. Byte Type: The type of free space to look for.
6. Calculate (Button): Select this button to get the results of your search.
7. Results:
   1. End Offset: Your start offset + number of bytes you requested
   2. Result: Free(blue)/Used(red). Script will notify you if the offset range is free or used.
8. Offset A: The offset to start your search at.
9. Offset B: The offset to end your search at.
10. Calculate Bytes Between (Button): Select this button to get the results of your search.
11. Results:
    1. Byte Difference: The total number of bytes between your offsets.
    2. Result: Free(blue)/Used(red). Script will notify you if the offset range is free or used.
12. Dec/Hex Converter
    1. Decimal: Putting a value in decimal format will update the hex value with the converted result.
    2. Hex: Putting a value in hex format will update the decimal value with the converted result.
   
 # TOOLS (ERASE OFFSET RANGE)   
 1. By Offset Range
    1. Start Offset: Enter the start of your offset range you'd like to erase.
    2. End Offset: Enter the end of your offset range you'd like to erase.
    3. Format: Select the type of bytes to clear the range with (FF/00).
    4. Erase (Button): Erase the selected range with the format you've selected.
 2. By Byte Count
    1. Start Offset: Enter the start of your offset range you'd like to erase.
    2. #of Bytes: Enter the number of bytes you'd like to erase following your start offset.
    3. Format: Select the type of bytes to clear the range with (FF/00).
    4. Erase (Button): Erase the selected range with the format you've selected.
 3. To Save your changes, you must manually navigate to File -> Save ROM. A backup of your old ROM will be created.

    Note: This gives the user the chance to verify their changes in the hex viewer before saving the changes.

 # Script Editor (WIP)
 1. Gray panel on the left indicates which line your script is on. Only lines with data will be numbered.
 2. Select Script: Select a script from the dropdownlist to insert at the bottom of the script (if any data exists).
 3. Wrap Messages (Button): Wraps all messages in the script for you.
 4. Flag: Which flag to use. User will need to find a free flag using online documentation.
 5. Item_ID: Which item to give, use, etc.
 6. Qty: how many of that item to give, use, etc.
 7. Species: Pokémon to use for the script.
 8. Level: Level of the Pokémon.

    Note: The script Editor currently does not compile or decompile. Hence the "WIP".

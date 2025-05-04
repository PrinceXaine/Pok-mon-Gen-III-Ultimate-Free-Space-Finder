# Pok-mon-Gen-III-Ultimate-Free-Space-Finder
Pokémon Gen III Hex Editor, Free Space Finder and Script Generator (WIP)

![image](https://github.com/user-attachments/assets/2c0804d8-8b36-4bd5-928b-78e0acda6f4d)


# ABOUT
This is a Pokémon Gen III Hex Viewer and Free Space Finder written in Python. 
> Provides the user with a free space finder that doesn't require closing other applications.
> 
> The ability to see, calculate and modify offsets in real time.
> 
> Provides the user with an easy way to free up space by erasing offset data no longer used by the ROM.

# WHAT THIS PROGRAM OFFERS
1. The ability to SEE the offsets you are editing in real time via a Hex Editor.
2. The ability to manually search offsets for free data if needed.
3. Automatically jumps to the offset the program has designated as "Free" so you can verify the data is free and not in critical space.

![image](https://github.com/user-attachments/assets/f7cece80-b5af-44c6-b8ac-1214d2508cd1)


4. When free space is found, it will also give you data: 

![image](https://github.com/user-attachments/assets/788cdc15-83ee-49da-970e-40e646b9f6ec)


5. Using the "Offset Calculator" in tools, you can:

   5a. Calculate the offset end location to view if the space is free or used.

   ![image](https://github.com/user-attachments/assets/36d88da0-70fe-44a2-8a3a-9a8ec13ffeee)

   5b. Enter a known range to calculate the number of bytes and if the range is free.   

   ![image](https://github.com/user-attachments/assets/2b7583be-b183-4f4b-a40f-3cf7a15c8592)

   5c. Comes with a Hex to Decimal or Decimal to Hex converter (same as free space finder)

   ![image](https://github.com/user-attachments/assets/e16c2fd0-8a3f-43e3-a0f3-04f7c5632347)

7. Using the "Erase Offset Range" in tools, you can:
   
   6a. By Offset Range -> Declare a specific range between start and end offsets to fill with FF/00.

   ![image](https://github.com/user-attachments/assets/f1709ed1-c9af-42d1-b2d8-053f9ec807f0)

   6b. By Byte Count -> Declare a number of bytes from the start offset to fill with FF/00.

   ![image](https://github.com/user-attachments/assets/d92631b2-ed3d-4741-b43a-2810d21b416d)


Script Editor Features:
1. You can insert scripts into the script editor. This is a WIP feature and shouldn't replace XSE or PKSV.

![image](https://github.com/user-attachments/assets/0cb3df55-8440-4b1a-b203-a19c643731c1)
![image](https://github.com/user-attachments/assets/7efdbec5-ac3f-40d6-8d59-7ae6a4d0c305)


2. You can wrap all messages in the script with the "Wrap Messages" button. This will automatically parse if the text already has line and page breaks.

![image](https://github.com/user-attachments/assets/97c22356-1048-41e9-a86c-4c19e0133409)
![image](https://github.com/user-attachments/assets/19cc092c-018b-484f-9bad-befd31f5fa98)


# Requirements:
1. You will need to install Python.

# Known Bugs:
1. Issues with Tkinter emulating control positions.

    > Due to how the script handles loading in the ROM, some of the controls used to navigate the hex viewer desync. You can always jump accurately to an offset, but until I am able to fix this issue, I recommend just being careful with what you do in the editor after scrolling, using the mouse wheel, etc. Before I updated the script, it took between 7-10 seconds to load after pressing the "open ROM" button. Now it takes a fraction of a second. I am actively working to resolve this issue but it's proven to be challenging and I do not have an ETA as of yet. ALWAYS jump to an offset before editing using the "edit offset" button.

# Future Updates:
1. Working on the script editor.
2. Bugfixes

# User Notice:
1. Please note that this tool was built for Pokémon Fire Red, but should work fine for just about any other .gba game (except the script editor).

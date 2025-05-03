# Pok-mon-Gen-III-Ultimate-Free-Space-Finder
Pokémon Gen III Hex Editor, Free Space Finder and Script Generator (WIP)
![image](https://github.com/user-attachments/assets/56ba22f0-cb6b-4bb8-be1f-b0ac9891975a)

>> Newest Update: Added viewport buffering and significantly increased the loading speed of the application.
![image](https://github.com/user-attachments/assets/8aa0bdd5-cc4d-4081-a6bc-e1b252cba7da)

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

![image](https://github.com/user-attachments/assets/65a027ce-a929-4508-9ecf-79ecd34c60a0)


4. When free space is found, it will also give you the ending offset:   
![image](https://github.com/user-attachments/assets/21aec4c4-d9eb-413e-9767-4b1f864dacf7)

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

# Future Updates:
1. Working on the script editor.
2. Bugfixes

# User Notice:
1. Please note that this tool was built for Pokémon Fire Red, but should work fine for just about any other application (except the script editor).

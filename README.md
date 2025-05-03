# Pok-mon-Gen-III-Ultimate-Free-Space-Finder
Pokémon Gen III (Fire Red) Hex Editor, Free Space Finder and Script Generator (WIP)
![image](https://github.com/user-attachments/assets/56ba22f0-cb6b-4bb8-be1f-b0ac9891975a)

This is a Pokémon Gen III Hex Viewer and Free Space Finder written in Python. 
I got annoyed when I was trying to work on my Fire Red hack and the tools to find a free offset are relatively barebones and don't really offer a way of viewing the offsets you're editing directly.

# What this program offers:
1. The ability to SEE the offsets you are editing in real time.
2. The ability to manually search offsets for free data.
3. Automatically jumps to the offset the program has designated as "Free" so you can verify the data is free and not in critical space.
4. When free space is found, it will also give you the ending offset:   
![image](https://github.com/user-attachments/assets/21aec4c4-d9eb-413e-9767-4b1f864dacf7)
5. If for whatever reason you're not using the program to find free space for you, you can also use the calculator in the "tools" menu to enter in whatever offset another program has designated for you, input a byte size and it will return where the offset ends. You can use this data to manually search and see if it doesn't end in free space.

![image](https://github.com/user-attachments/assets/954aaf5e-53a4-4c23-a6c2-acfc15dc2f15)
![image](https://github.com/user-attachments/assets/02669d12-224f-4688-8e2b-56873f889f24)

6. You can calculate the difference between two offsets.
   
![image](https://github.com/user-attachments/assets/97f7e28a-a566-4dc9-988b-8dd5c6cecb4e)

7. The dropdown (present on the main screen and in the offset calculator) allow you to change the leading characters of your offset (00, 0x, $).
  
![image](https://github.com/user-attachments/assets/10b8801e-c196-4f00-ab38-c95bc77dc0fa)


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

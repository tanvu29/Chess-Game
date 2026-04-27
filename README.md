Notes: 
- This README is written for the Windows environment

1. Start a Unity session

2. Clone this repo into /work/pi_softdes26_olin_edu/[YOUR DIRECTORY] 
- If you are not already in this directory, open the terminal and run: cd /work/pi_softdes26_olin_edu/[YOUR DIRECTORY]
- Once you are in /work/pi_softdes26_olin_edu/[YOUR DIRECTORY], run this command: git clone https://github.com/tanvu29/Chess-Game.git
- You should now see a folder called "Chess-Game in the Explorer sidebar
<img width="1424" height="356" alt="image" src="https://github.com/user-attachments/assets/a6b4034e-c488-4f47-8fb9-9a19c3ea3e4d" />

3. Make virtual environment
- In the terminal, run:
python -m venv venv
source venv\Scripts\activate       
pip install -r requirements.txt


4. Download Stockfish
Stockfish is a free and open-source chess engine.
Download it here: https://stockfishchess.org/download/
- Select download option for windows - this downloads a zip file called "stockfish-windows-x86-64-avx2.zip"
- This zip should now be in your Downloads folder. Right click the .zip and select "Extract All"
- In the menu that pops up, select your Downloads folder as the destination. Click "Extract"
<img width="700" height="583" alt="image" src="https://github.com/user-attachments/assets/2d8d488d-0313-4d2f-b7dc-202fe8a63e74" />
- There should now be a folder called "stockfish" in Downloads
- 

- You should now see a folder called "stockfish" inside of Chess-Game 

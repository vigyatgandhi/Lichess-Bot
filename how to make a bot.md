How To Make a BOT IN ?
By Vigyat Gandhi
An example of a bot is BOTbotBOTbotBOTrobot.

you can find the repository you need here https://github.com/vigyatgandhi/Lichess-Bot

You can find the code of the bot in my repository

Step 1: Creating A Lichess Account
Create an account on lichess.org

Step 2: Create an API Token
After creating an account go to https://lichess.org/account/oauth/token and select all options for the API. Copy your code and keep it safe. Do not share it.

Step 3: Change your account to the BOT status
Open Your terminal and type the following code

curl -d '' https://lichess.org/api/bot/account/upgrade \-H "Authorization: Bearer YOUR_TOKEN_HERE"

Step 4: Installing stockfish (the brains)
Go to https://stockfishchess.org/ and download best suitable version for your computer

Step 5: Install python
Mac
You will already have it, check with running following command in terminal

which python3
/usr/bin/python3
Windows
Once you're done installing python you have to go to your terminal and type the following command


    #Pip Install Requests

    pip install berserk python-chess

FYI Berserk is lichess'own library for API

Step 5 changing the code
change the API,Bot username, and stockfish path to your own bots' things

https://github.com/vigyatgandhi/Lichess-Bot/blob/main/lichess-bot.py this is the code i have made use it to run the bot

Step 6 running the bot
First open Lichess with your BOT account Then Open CMD and run

Python lichess-bot.py
(If you named the file something else it wont work. Use lichess-bot.py or any name but add .py at the end. IF you added your own name then run that instead of LichessBOT.py) This will run your BOT, you can now Challenge it, it will accept and play on Stockfish!

Thanks for reading!!!

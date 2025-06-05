# Ar4Asd1-BOT
Do you need to make a Lichess BOT? There is a step by step Guide and code for the making of it

Other engine -
https://github.com/Arkeno-Org/ChessEngine

---

*Step 1 - Make a Lichess Account*

Create a Lichess Account on Lichess.org
___

*Step 2 - Create a API*

After creating an account go to https://lichess.org/account/oauth/token and select all options for the API. Copy your code and keep it safe. Do not share it.

___

*Step 3 - upgrading to a BOT Account*

You need to Open CMD or Windows Powershell and run this commad

> curl -d '' lichess.org/api/bot/account/upgrade -H "Authorization: Bearer DeletethisandPasterYourAPITokenCodeHere"

Remeber to replace "DeletethisandPasterYourAPITokenCodeHere" with your API Token.

If CMD Replies with 
>ok}true

You have a BOT Account!

___

*Step 4 - Installing*

Install

Stockfish (Click More Options to see More Options for Windows Make sure to see if you can run the stockfish By Checking with a Programmer/AI)

https://stockfishchess.org/download/

For  Stockfish I had installed one which my Laptop Couldn't work with so I had to install another I used POPCNT.

And you need to install python in Program Files in Your PC. Python 3.13.2 or Higher works

https://Python.org

Go to CMD Again and do

>Pip Install Requests
>pip install berserk python-chess

___

*Step 5 - Modifying Code*

Copy the file Code.py and change the code where you need to. (API, BOT Username, Stockfish Path) 

Before doing this ask AI to run a saftey check on the code if you don't think the code is safe. 

After replacing all the placeholders with your API, BOT Username and Stockfish Path, save the file as "LichessBOT.py"

___

*Step 6 - Running*

First open Lichess with your BOT account

Then Open CMD and run 

>Python LichessBOT.py

(If you named the file something else it wont work. Use LichessBOT.py or any name but add .py at the end. IF you added your own name then run that instead of LichessBOT.py)

This will run your BOT, you can now Challenge it, it will accept and play on Stockfish!


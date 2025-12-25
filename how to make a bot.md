How To Make a BOT IN LICHESS?
By Vigyat Gandhi

An example of a bot is BOTbotBOTbotBOTrobot—basically what happens when chess meets a sugar-addicted algorithm that never sleeps.

You can find the repository you need here: https://github.com/vigyatgandhi/Lichess-Bot

You can find the code of the bot in my repository.
Step 1: Creating A Lichess Account

Create an account on lichess.org—but don't actually play any games on it, or your bot will cry bot tears. Name it something epic like "PawnMuncher3000" because your bot needs a personality crisis too. Think of it as creating a superhero's secret lair before the superhero even exists. Plot twist: the superhero is an algorithm with zero chill and anger management issues.
Step 2: Create an API Token

After creating an account, go to https://lichess.org/account/oauth/token and select ALL options for the API like you're robbing a candy store. Copy your code and keep it safer than your Netflix password—seriously, don't share it unless you want hackers controlling your bot overlord. You just gave them the skeleton key to your digital chess empire. Congratulations, genius.
Step 3: Change your account to the BOT status

Open Your terminal (that scary black box with white text that makes you feel like a Hollywood hacker) and type the following code:

text
curl -d '' https://lichess.org/api/bot/account/upgrade -H "Authorization: Bearer YOUR_TOKEN_HERE"

If this works, congrats! Your account just got the "I'm a Bot" superpower. If it fails? Double-check your spelling—bots hate typos more than they hate blunders. Pro tip: If you copied-pasted wrong, don't blame the code. Blame yourself. The code is perfect; humans are chaos incarnate.
Step 4: Installing stockfish (the brains)

Go to https://stockfishchess.org/ and download the best suitable version for your computer. Stockfish is basically like hiring Magnus Carlsen's clone but making him work for free. That's a steal! Pick your flavor:

    Windows Users: Download the Windows version (obviously)

    Mac Users: Download the macOS version (also obvious, but you'd be surprised)

    Linux Nerds: You already know what to do; stop pretending you don't

This is the mega-brain powering your chess robot. It will destroy your dreams faster than you can say "check."
Step 5: Install python

Mac
You will already have it, check with running following command in terminal:

text
which python3
/usr/bin/python3

If you see the path, congrats! You're basically a wizard already.

Windows
Once you're done installing python you have to go to your terminal and type the following command:

text
pip install berserk python-chess

What's happening here? You're downloading two things:

    Berserk: Lichess's official library (fancy way to say "toolkit"). FYI Berserk is lichess's own library for API—and yes, it's named after anime because developers have hobbies too.

    Python-chess: A library that understands chess so your bot doesn't play like a confused toddler who just discovered the board.

Step 6: Changing the code

Change the API, Bot username, and stockfish path to your own bot's things. Go to https://github.com/vigyatgandhi/Lichess-Bot/blob/main/lichess-bot.py—this is the code I have made use it to run the bot. This is your bot's soul—the actual code that makes everything work.

Example for Windows:

text
stockfish_path = "C:/Users/YourName/Downloads/stockfish.exe"
api_token = "your_super_secret_token_123"
bot_username = "CheckmateMcSarcasmBot"

Example for Mac:

text
stockfish_path = "/usr/local/bin/stockfish"
api_token = "your_super_secret_token_123"
bot_username = "CheckmateMcSarcasmBot"

Pro Tip: If you mess this up, your bot plays like it learned chess from TikTok videos. Don't be that person. If you forget the path or token, your bot will throw an absolute tantrum and refuse to exist.
Step 7: Running the bot

First open Lichess with your BOT account. Then Open CMD and run:

text
Python lichess-bot.py

(If you named the file something else it won't work. Use lichess-bot.py or any name but add .py at the end. IF you added your own name then run that instead of lichess-bot.py)

This will run your BOT, you can now Challenge it, it will accept and play on Stockfish! Get ready to watch Stockfish absolutely demolish your chess dreams faster than you can say "check." Enjoy getting destroyed by your own creation—it's character-building! (And hilarious for everyone else watching.)

Reality Check: If you're expecting to win? LOL. Stockfish is basically playing 4D chess while you're stuck in checkers. Prepare yourself for digital humiliation.

Thanks for reading!!!

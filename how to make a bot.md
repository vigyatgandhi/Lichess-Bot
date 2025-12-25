# How To Make a BOT IN LICHESS?
## By Vigyat Gandhi

An example of a bot is BOTbotBOTbotBOTrobot - basically what happens when chess meets a sugar-addicted algorithm that never sleeps. Think of it like building a droid from Star Wars, except this one actually listens to commands (unlike R2-D2 or C1-10P).

Here is my github repo with the code you need  https://github.com/vigyatgandhi/Lichess-Bot

---

## Step 1: Creating A Lichess Account

Create an account on lichess.org - but *don't actually play any games on it*, or your bot will cry bot tears. Name it something epic like "YodaTheChessmaster" or "LukeStockfishWalker" because your bot needs a personality crisis too. Think of it as building your own LEGO droid before the actual programming happens. Plot twist: the droid is an algorithm with zero chill and more power than the Empire's death star.

---

## Step 2: Create an API Token

After creating an account, go to https://lichess.org/account/oauth/token and select ALL options for the API like you're collecting all the Infinity Stones. Copy your code and keep it safer than the Death Star plans - seriously, don't share it unless you want the hackers controlling your bot overlord. You just gave them the skeleton key to your digital chess empire. Congratulations, you just created a new identity for your little chess droid.

---

## Step 3: Change your account to the BOT status

Open Your terminal or Command prompt (that scary black box with white text that makes you feel like you're hacking into the Imperial fleet's computer systems) and type the following code:

```
curl -d '' https://lichess.org/api/bot/account/upgrade -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

If this works, congrats! Your account just got the "I'm a Bot" superpower - basically the Force, but for chess. 

If it fails? Double-check your spelling - bots hate typos more than Anakin hates sand. Pro tip: If you copied-pasted wrong, don't blame the code. Blame yourself. The code is perfect; humans are chaos incarnate (no cap, that's straight-up brainrot energy).

---

## Step 4: Installing stockfish (the brains)

Go to https://stockfishchess.org/ and download the best suitable version for your computer. 

Stockfish is basically like summoning a Jedi Master who plays with your opponent's pieces - it'll blow you over with mind-blowing moves! Pick your flavor:

- **Windows Users:** Download the Windows version (the boring minifig choice)
- **Mac Users:** Download the macOS version (the sleek LEGO Technic version)
- **Linux Nerds:** You already know what to do; stop pretending you don't (the custom-built droid route)

This is the mega-brain powering your chess robot. It will destroy your dreams faster than you can say "check" (or "This is the Way" if you're feeling the Star Wars brainrot).

---

## Step 5: Install python


You will already have it, check with running following command in terminal:

```
which python3
/usr/bin/python3
```

If you see the path, congrats! You're basically a Jedi Master of coding already. The Force is strong with this one.

If you don't have one install from https://www.python.org/downloads/ 

Once you're done installing python you have to go to your terminal and type the following command:

```
pip install berserk python-chess
```

**What's happening here?** You're downloading two things:
- **Berserk:** Lichess's official library (fancy way to say "toolkit"). FYI Berserk is lichess's own library for API - it's named after anime because developers have hobbies too, just like how we all have brainrot energy for our favorite franchises.
- **Python-chess:** A library that understands chess so your bot doesn't play like a confused LEGO minifigure trying to bowl a cricket ball. It's the difference between a random shot and a perfect six-wicket strategy.

Note: Some linux environments throw error on installing python packages globally, use following command to bypass it

```
pip install berserk python-chess --break-system-packages
```


---

## Step 6: Changing the code

Change the API, Bot username, and stockfish path to your own bot's things. Go to https://github.com/vigyatgandhi/Lichess-Bot/blob/main/lichess-bot.py - this is the code I have made use it to run the bot. This is your bot's soul - the actual code that makes everything work. It's like assembling a LEGO Star Wars ship: get the instructions right, or you'll end up with a confused droid.

**Example for Windows:**
```
stockfish_path = "C:/Users/YourName/Downloads/stockfish.exe"
api_token = "your_super_secret_token_123"
bot_username = "YodaTheChessmaster"
```

**Example for Mac:**
```
stockfish_path = "/usr/local/bin/stockfish"
api_token = "your_super_secret_token_123"
bot_username = "LukeStockfishWalker"
```

Pro Tip: If you mess this up, your bot plays like it learned chess from TikTok videos (peak brainrot). Don't be that person. If you forget the path or token, your bot will throw an absolute tantrum and refuse to exist - very Anakin Skywalker of it, honestly.

---

## Step 7: Running the bot

First open Lichess with your BOT account. Then Open CMD and run:

```
python3 lichess-bot.py
```

This will run your BOT, you can now Challenge it, it will accept and play on Stockfish! Get ready to watch Stockfish absolutely *demolish* your chess dreams faster than the Death Star destroys Alderaan. It's like watching a cricket pro face a toddler with a bat - absolutely merciless. Enjoy getting destroyed by your own creation - it's character-building! (And hilarious for everyone else watching, peak brainrot comedy.)

**Reality Check:** If you're expecting to win? LOL. Stockfish is basically playing 4D chess (like a Jedi reading the future) while you're stuck in checkers mode with the intelligence of a confused LEGO minifigure. Prepare yourself for digital humiliation. May the Force NOT be with you, because the Force (Stockfish) will destroy you.

---

**Thanks for reading!!!**
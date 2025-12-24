# Lichess Chess Bot

A Python bot for [Lichess.org](https://lichess.org) that accepts challenges, plays chess using the Stockfish engine, and manages multiple games concurrently [web:1][web:13]. Licensed under GNU Affero GPL v3.

## Features
- Accepts filtered challenges (speeds: rapid/blitz/classical; variants: standard).
- Computes moves with Stockfish (depth 15, ~10-30s/move) via UCI [web:14].
- Concurrent game handling with threading.
- Detailed logging (general, per-game) and stats.json tracking (last 1000 games).
- Idle behavior: joins lichess-bot tournaments or posts open casual challenges (5min+5s) [web:13].
- Daily bot-vs-bot game limits.

## Prerequisites
- Python 3.9+ [web:7][web:21].
- Stockfish binary [web:6][web:14].
- Lichess account upgraded to bot [web:2][web:3].

## Setup
1. Install dependencies:  
   ```
   pip install berserk chess
   ```  
   [web:7]

2. Download Stockfish:  
   - Official binaries: https://stockfishchess.org/download/ [web:14].  
   - Linux (e.g., Ubuntu): `sudo apt install stockfish` (path: `/usr/games/stockfish`).  
   - Verify: Run `./stockfish uci` in terminal.

3. Create Lichess bot token and upgrade account:  
   - Go to https://lichess.org/account/oauth/token, select bot scopes (Play, Challenge, etc.) [web:2].  
   - Upgrade: `curl -X POST "https://lichess.org/api/bot/account/upgrade" -H "Authorization: Bearer YOUR_TOKEN"` [web:3].

4. Run script once to generate `lichess_bot.conf`, then edit:  
   - `lichess: bot_username` and `bot_api_token`.  
   - `engine: stockfish_path` (full executable path).  
   - Optional: `behavior` (speeds, variants, limits).

## Usage
```
python lichess-bot.py [--conf lichess_bot.conf]
```
- Monitors events, auto-accepts/declines challenges.  
- Logs to `lichess_bot.log`; per-game to `game_*.log`; stats to `stats.json`.  
- Graceful shutdown with Ctrl+C [web:22].

## Configuration Options
| Section | Key | Description | Default |
|---------|-----|-------------|---------|
| lichess | bot_username | Bot's Lichess username | Ar4Asd1-BOT |
| lichess | bot_api_token | OAuth token | (empty) |
| engine | stockfish_path | Stockfish executable | (empty) |
| behavior | accept_speeds | Comma-separated: rapid,blitz,classical | rapid,blitz,classical |
| behavior | accept_variants | e.g., standard | standard |
| behavior | bot_daily_limit | Max bot games/day | 100 |

## License
GNU Affero General Public License v3. See code header [web:13].


[1](https://github.com/EmptikBest/lichess-bot-1/blob/master/README.md)
[2](https://github.com/lichess-bot-devs/lichess-bot)
[3](https://github.com/Rowan441/StarterLichessBot)
[4](https://github.com/cyanfish/python-lichess)
[5](https://github.com/lichess-org/berserk)
[6](https://www.youtube.com/watch?v=dAGDOwzwTj4)
[7](https://github.com/rhgrant10/berserk)
[8](https://github.com/Torom/BotLi)
[9](https://github.com/lichess-bot-devs/lichess-bot/wiki/Configure-lichess-bot)
[10](https://github.com/lichess-org/berserk/blob/master/CHANGELOG.rst)
[11](https://github.com/cheran-senthil/SultanKhan2)
[12](https://lichess.org/forum/lichess-feedback/is-there-a-detailed-user-guide-for-stockfish-on-lichess-)
[13](https://lichess.org/@/BerserkEngine)
[14](https://github.com/oivas000/lichess-bot/blob/master/README.md)
[15](https://www.youtube.com/watch?v=k4aXwk_VQVw)
[16](https://github.com/mkomon/uberserk)
[17](https://github.com/The-bot-makers/Lichess-bot)
[18](https://lichess.org/@/JumpingHorsey/blog/how-to-make-a-lichess-bot/pb6O3Tl8)
[19](https://berserk.readthedocs.io/en/master/readme.html)
[20](https://github.com/LeelaChess/lichess-bot-1)
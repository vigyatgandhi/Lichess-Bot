"""
Lichess Chess Bot
=================

Copyright (C) 2025 Vigyat Gandhi

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
# argparse: Helps parse command-line arguments, like specifying a config file path.
import berserk
# berserk: A Python library to interact with Lichess.org API, handling authentication and game streams.
import chess
# chess: Library for chess board manipulation, move validation, and game state (e.g., checkmate detection).
import chess.engine
# chess.engine: Interface to connect external chess engines like Stockfish for move calculation.
import configparser
# configparser: Reads/writes simple .ini-style config files for bot settings.
import json
# json: Handles JSON data for stats storage and API events.
import logging
from logging.handlers import RotatingFileHandler
# logging & RotatingFileHandler: Logs bot activity to console/files, rotates logs to prevent huge files.
import os
# os: Checks files exist, gets current directory.
import multiprocessing
# multiprocessing: Determines CPU core count for engine configuration.
import signal
# signal: Catches shutdown signals (Ctrl+C) for clean exit.
import sys
# sys: System-specific parameters, like executable path.
import time
# time: Delays/sleeps in loops.
import threading
# threading: Runs multiple game threads simultaneously without blocking.
import random
# random: Shuffles candidate lists for fair challenging.
from datetime import datetime, timedelta
# datetime: Timestamps for logs/games.

# ─── DEFAULT CONFIGURATION ─────────────────────────────────────────────
# This sets up default values for the bot's settings file.
DEFAULT_CONF = "lichess_bot.conf"


def load_config(conf_path):
    """
    Loads the bot's configuration from a file (like lichess_bot.conf).
    
    If the file doesn't exist, creates one with sensible defaults:
    - Lichess details: bot username, API token (get from lichess.org), base URL.
    - Engine: Path to Stockfish executable (download from stockfishchess.org).
    - Logging: Log file and rotation size.
    - Behavior: Allowed game speeds (rapid=10-60min, blitz=3-10min), variants (standard chess),
                idle time before challenging others, daily game limits vs bots.
    
    """
    config = configparser.ConfigParser()
    # Defaults for Lichess connection
    config['lichess'] = {
        'bot_username': '<your-bot-username>',  # Fill this with your bot's username
        'bot_api_token': '',  # Fill this from lichess.org/my-account/oauth-token
        'base_url': 'https://lichess.org'
    }
    # Stockfish engine path (must be installed locally)
    # Stockfish engine depth parameter made configurable via play_game function parameter
    config['engine'] = {
        'stockfish_path': '',  # e.g., '/usr/local/bin/stockfish'
        'depth': '15'  # Default depth for Stockfish
    }
    # Logging setup
    config['logging'] = {
        'general_log': 'lichess_bot.log',
        'rotate_kb': '1024'  # Rotate log at 1MB
    }
    # Game acceptance rules
    config['behavior'] = {
        'accept_speeds': 'rapid,blitz,classical',  # Comma-separated time controls
        'accept_variants': 'standard',  # Chess variants like standard only
        'idle_seconds': '60',  # Wait this long when idle to challenge others
        # comma-separated usernames to consider challenging when idle
        'idle_candidates': '',
        'bot_daily_limit': '100'  # Max games per day vs other bots
    }

    if os.path.exists(conf_path):
        config.read(conf_path)
    else:
        # Write sample config for user to edit
        with open(conf_path, 'w') as f:
            config.write(f)
        config.read(conf_path)

    return config


def setup_logging(log_file, rotate_kb, username=None):
    """
    Sets up logging to console and rotating file.
    
    Logs include timestamp, process ID, log level, username, and message.
    Rotating prevents logs from growing forever (keeps 5 backups).
    Returns a logger adapter that prefixes every log with the bot's username.
    
    Think of this as the bot's diary—tracks what it does, errors, for debugging.
    """
    base_logger = logging.getLogger('lichess_bot')
    base_logger.setLevel(logging.DEBUG)
    # Formatter adds PID and username for traceability
    formatter = logging.Formatter('%(asctime)s %(process)d %(levelname)s %(username)s: %(message)s')

    # Console handler: Prints to terminal
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    base_logger.addHandler(ch)

    # File handler: Rotating logs
    fh = RotatingFileHandler(log_file, maxBytes=rotate_kb * 1024, backupCount=5)
    fh.setFormatter(formatter)
    base_logger.addHandler(fh)

    # Adapter injects username into all logs
    return logging.LoggerAdapter(base_logger, {'username': username or ''})


class BotState:
    """
    Tracks bot's game history and stats in a JSON file (stats.json).
    
    Handles concurrent access (thread-safe) with a lock.
    Keeps last 1000 games to avoid bloat.
    Counts daily games vs other bots for limits.
    
    Like a scorecard—records wins/losses/draws, opponents, for reviewing performance.
    """
    def __init__(self, stats_file='stats.json'):
        self.lock = threading.Lock()  # Prevents data corruption from multiple threads
        self.stats_file = stats_file
        self.load()

    def load(self):
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {'games': []}

    def save(self):
        with self.lock:
            with open(self.stats_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)

    def add_game(self, record):
        with self.lock:
            self.data['games'].append(record)
            # Keep only recent 1000 games
            self.data['games'] = self.data['games'][-1000:]
        self.save()

    def bot_games_today(self, bot_username):
        today = datetime.utcnow().date()
        with self.lock:
            return sum(1 for g in self.data['games']
                       if g.get('is_bot') and datetime.fromisoformat(g['start_time']).date() == today)


def game_log_filename(game_id, opponent, ts_iso=None):
    """
    Generates a stable filename for per-game logs.
    
    Uses ISO timestamp from game start (UTC) to avoid timezone issues.
    Sanitizes opponent name (no / or spaces).
    Format: game_YYYYMMDDTHHMMSSZ_opponent_gameid.log
    
    Each game gets its own diary file for detailed move-by-move review.
    """
    # Use provided ISO timestamp for stability
    if ts_iso:
        try:
            ts = datetime.fromisoformat(ts_iso).strftime('%Y%m%dT%H%M%SZ')
        except Exception:
            ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    else:
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    safe_opp = (opponent or 'unknown').replace('/', '_').replace(' ', '_')
    return f"game_{ts}_{safe_opp}_{game_id}.log"

#make depth configurable via parameter from config file
def play_game(client, engine_path, game_id, bot_username, logger, state: BotState, config_depth,max_hash_size):
    """
    Main game loop for a single game.
    
    Streams game events from Lichess (moves, status).
    Uses Stockfish engine to compute best moves (depth=30: thinks ~10-30sec).
    Logs moves to per-game file, updates stats.
    Handles bot as white/black, game over (mate/resign/etc.).
    
    This is the brain—watches the board, thinks with Stockfish AI, plays moves.
    FEN: A string snapshot of the chess board (files ranks pieces).
    """
    logger.info(f"Starting game {game_id}")
    # Launch Stockfish engine process
    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        #change cpu core count based on current system capabilities
        # use 50% of total physical ram for hash size allocation or max_hash_size from config, whichever is lower
        memory_bytes = os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')
        memory_mb = memory_bytes // (1024 * 1024)
        max_hash_mb = min(max_hash_size, memory_mb // 2)
        cpu_count = multiprocessing.cpu_count()
        # use all the brains we can get!
        # Give it a large notebook to remember all those fancy chess moves. Don't skimp!
        engine.configure({
            "Threads": max(1, cpu_count),  
            "Hash": max_hash_mb    
        })
        logger.info("Stockfish powered up with %d cores and %d MB hash!", max(1, cpu_count), max_hash_mb)  # Bragging rights activated.

    except Exception as e:
        logger.exception("Failed to open engine: %s", e)
        return

    board = chess.Board()  # Current chess board state
    bot_color = None  # 'white' or 'black'
    game_log = None
    white_name = None
    black_name = None
    last_moves_count = 0
    time_control = None
    game_record = {
        'game_id': game_id,
        'start_time': datetime.utcnow().isoformat(),
        'end_time': None,
        'moves': [],
        'opponent': None,
        'variant': None,
        'speed': None,
        'is_bot': False  # Set later if opponent is BOT
    }
    # post a chat message introducing bot username and polite greeting
    try:
        logger.info("Posting welcome message in game %s", game_id)
        client.bots.post_message(game_id, f"Hello! I'm {bot_username}. I was created by Vigyat. I am available at github vigyatgandhi/Lichess-Bot")
    except Exception as e:
        logger.exception("Failed to post welcome message: %s", e)

    try:
        # Stream game events forever (until over)
        for event in client.bots.stream_game_state(game_id):
            etype = event.get('type')
            # Log raw event to per-game log
            if game_log:
                try:
                    game_log.info('Event: %s', json.dumps(event, default=str))
                except Exception:
                    game_log.info('Event: %s', str(event))
            
            if etype == 'gameFull':
                # Initial full game info
                white = event.get('white')
                black = event.get('black')
                if white and white.get('name', '').lower() == bot_username.lower():
                    bot_color = 'white'
                    opponent = black.get('name')
                elif black and black.get('name', '').lower() == bot_username.lower():
                    bot_color = 'black'
                    opponent = white.get('name')
                else:
                    logger.error('Bot username not found among players; exiting game %s', game_id)
                    break

                white_name = white.get('name') if white else None
                black_name = black.get('name') if black else None

                game_record['opponent'] = opponent
                game_record['variant'] = event.get('variant', {}).get('key')
                game_record['speed'] = event.get('speed')
                # Parse time control (e.g., 300s+5s -> 5m+5s)
                clock = event.get('clock') or event.get('timeControl')
                if isinstance(clock, dict):
                    try:
                        initial = int(clock.get('initial', 0)) // 1000
                        increment = int(clock.get('increment', 0))
                        if initial % 60 == 0:
                            time_control = f"{initial//60}m+{increment}s"
                        else:
                            time_control = f"{initial}s+{increment}s"
                    except Exception:
                        time_control = str(clock)
                elif clock:
                    time_control = str(clock)
                
                # Setup per-game logger once
                if game_log is None:
                    fname = game_log_filename(game_id, opponent or 'unknown', game_record.get('start_time'))
                    base_game_logger = logging.getLogger(f'game_{game_id}')
                    fh = logging.FileHandler(fname)
                    fh.setFormatter(logging.Formatter('%(asctime)s %(process)d %(username)s %(message)s'))
                    base_game_logger.addHandler(fh)
                    base_game_logger.setLevel(logging.INFO)
                    game_log = logging.LoggerAdapter(base_game_logger, {'username': bot_username})
                    game_log.info('Game started %s vs %s', bot_username, opponent)

            elif etype == 'gameState':
                # Update board from move list (UCI format: e2e4)
                moves = event.get('moves', '')
                board = chess.Board()
                moves_list = moves.split() if moves else []
                if moves_list:
                    for m in moves_list:
                        board.push_uci(m)

                # Log new moves with timestamps, player clocks
                if game_log:
                    # Helper: Format ms to readable time (mm:ss)
                    def fmt_time(ms):
                        try:
                            s = int(ms) // 1000
                            h, rem = divmod(s, 3600)
                            m, sec = divmod(rem, 60)
                            if h:
                                return f"{h:d}:{m:02d}:{sec:02d}"
                            return f"{m:d}:{sec:02d}"
                        except Exception:
                            return str(ms)

                    # Log only new moves
                    for i in range(last_moves_count, len(moves_list)):
                        move = moves_list[i]
                        ply = i + 1  # Move number (1,2,3...)
                        player_color = 'white' if i % 2 == 0 else 'black'
                        player_name = white_name if player_color == 'white' else black_name
                        tc_display = time_control or 'unknown'
                        ts = datetime.utcnow().isoformat()
                        game_log.info('%s: move %d %s(%s+%s) %s', ts, ply, player_name, ply, tc_display, move)
                    last_moves_count = len(moves_list)

            else:
                continue

            # Check local game over (stalemate, etc.)
            if board.is_game_over():
                result = board.result() if hasattr(board, 'result') else 'unknown'
                logger.info('Game %s over, result %s', game_id, result)
                if game_log:
                    game_log.info('Game over detected locally, result: %s', result)
                break

            # Check event status (resign, timeout)
            status = event.get('status')
            if status:
                winner = event.get('winner') or event.get('winnerColor')
                logger.info('Game %s status update: %s (winner=%s)', game_id, status, winner)
                if game_log:
                    game_log.info('Status update: %s (winner=%s)', status, winner)
                # Terminal statuses
                if status in ('mate', 'resign', 'timeout', 'outoftime', 'draw', 'aborted', 'stalemate', 'cheat', 'variantEnd'):
                    break

            # Bot's turn? Compute and play move
            if bot_color and ((board.turn == chess.WHITE and bot_color == 'white') or
                              (board.turn == chess.BLACK and bot_color == 'black')):
                logger.info('My turn in game %s. FEN: %s', game_id, board.fen())
                try:
                    #Dynamic depth adjustment based on remaining time, make brain work faster under time pressure
                    remaining_time = None
                    clocks = event.get('clocks', {})
                    if bot_color == 'white':
                        remaining_time = clocks.get('white')
                    else:
                        remaining_time = clocks.get('black')
                    if remaining_time is not None and remaining_time < 10000:
                        depth_to_use = min(5, config_depth)
                    elif remaining_time is not None and remaining_time < 30000:
                        depth_to_use = min(8, config_depth)
                    elif remaining_time is not None and remaining_time < 60000:
                        depth_to_use = min(12, config_depth)
                    else:
                        depth_to_use = config_depth 
                    result = engine.play(board, chess.engine.Limit(depth=depth_to_use))
                    best_move = result.move
                    if best_move in board.legal_moves:
                        client.bots.make_move(game_id, best_move.uci())
                        board.push(best_move)
                        logger.info('Played move %s in %s', best_move.uci(), game_id)
                        if game_log:
                            game_log.info('Played %s', best_move.uci())
                            game_record['moves'].append({'ply': len(game_record['moves']) + 1,
                                                         'move': best_move.uci(),
                                                         'time': datetime.utcnow().isoformat()})
                    else:
                        logger.warning('Engine suggested illegal move %s', best_move)
                except Exception as e:
                    logger.exception('Error while making move: %s', e)

            time.sleep(1)  # Poll delay

    except berserk.exceptions.ResponseError as e:
        if '429' in str(e):
            logger.warning('Game stream 429 mid-game!!! ; wait 10s')
            time.sleep(10)
        else:
            raise
    finally:
        # Cleanup
        try:
            engine.quit()
        except Exception:
            pass
        game_record['end_time'] = datetime.utcnow().isoformat()
        # Mark as bot if opponent title=BOT
        # Note: is_bot set based on challenger title in accept_challenge
        state.add_game(game_record)
        if game_log:
            base_game_logger = game_log.logger if isinstance(game_log, logging.LoggerAdapter) else game_log
            for h in list(base_game_logger.handlers):
                try:
                    h.close()
                    base_game_logger.removeHandler(h)
                except Exception:
                    pass
        logger.info('Exiting game thread %s', game_id)


def accept_challenge_allowed(challenge, config, state: BotState, logger, bot_username):
    """
    Decides if a challenge should be accepted.
    
    Checks: allowed speed/variant, daily bot game limit.
    Rejects politely via logs.
    
    Filters challenges—only plays allowed game types to avoid endless casual games.
    """
    # Allowed speeds/variants from config
    speeds = [s.strip().lower() for s in config.get('behavior', 'accept_speeds').split(',')]
    variants = [v.strip().lower() for v in config.get('behavior', 'accept_variants').split(',')]
    speed = (challenge.get('speed') or '').lower()
    variant = (challenge.get('variant') or {}).get('key', '').lower()
    challenger = challenge.get('challenger', {}).get('name')
    is_bot = challenge.get('challenger', {}).get('title', '') == 'BOT' or challenge.get('isBot', False)
    # Reject bad variant
    if variant and variant not in variants:
        logger.info('Rejecting challenge from %s: variant %s not allowed', challenger, variant)
        return False
    # Reject bad speed
    if speed and speed not in speeds:
        logger.info('Rejecting challenge from %s: speed %s not allowed', challenger, speed)
        return False

    # Bot daily limit
    if is_bot:
        limit = int(config.get('behavior', 'bot_daily_limit'))
        if state.bot_games_today(bot_username) >= limit:
            logger.info('Rejecting challenge from %s: bot daily limit reached', challenger)
            return False

    return True

def has_active_game(game_id, logger):
    for t in threading.enumerate():
        if t.name == f'game-{game_id}' and t.is_alive():
            logger.info('Game %s already running, skipping', game_id)
            return True
    return False

def event_loop(config, logger, state: BotState):
    """
    Main event listener loop.
    
    Connects to Lichess stream for challenges/game starts.
    Accepts/declines based on rules, spawns game threads.
    Starts idle challenger thread (Posts open challange when free).
    Retries on errors (backoff, 429 rate limit).
    
    The bot's ears—listens for "play me?" or "game started!", responds.
    """
    token = config.get('lichess', 'bot_api_token')
    base_url = config.get('lichess', 'base_url')
    bot_username = config.get('lichess', 'bot_username')
    engine_path = config.get('engine', 'stockfish_path')
    config_depth = config.getint('engine', 'depth', fallback=15)
    max_hash_size = config.getint('engine', 'max_hash_size', fallback=256)    


    session = berserk.TokenSession(token)
    client = berserk.Client(session=session, base_url=base_url)

    # Idle challenger config
    idle_seconds = int(config.get('behavior', 'idle_seconds'))

    def has_active_games():
        # Check for running game threads
        for t in threading.enumerate():
            try:
                if t.name.startswith('game-') and t.is_alive():
                    return True
            except Exception:
                continue
        return False

    def idle_loop():
        """Background thread:open challange when no games active."""
        backoff = 5
        while True:
            try:
                time.sleep(idle_seconds)
                if has_active_games():
                    logger.debug('Idle challenger: active games present, skipping challenge')
                    continue

                time.sleep(2)  # Small delay before challenging
                # Post open challange with https://lichess-org.github.io/berserk/api.html#berserk.clients.Challenges.create_open
                try:
                    client.challenges.create_open(
                        rated=False,
                        clock_limit=300,
                        clock_increment=5,
                        variant='standard'
                    )
                    logger.info('Posted open challenge')
                except Exception as e:
                    logger.exception('Failed to post open challenge: %s', e)

            except Exception as e:
                logger.exception('Idle challenger encountered error: %s', e)
                time.sleep(backoff)
                backoff = min(backoff * 2, 300)

    # Start idle thread
    threading.Thread(target=idle_loop, daemon=True, name='idle-challenger').start()

    backoff = 5
    while True:
        try:
            stream = client.bots.stream_incoming_events()
            for event in stream:
                etype = event.get('type')
                if etype == 'challenge':
                    challenge = event.get('challenge', {})
                    challenger_name = challenge.get('challenger', {}).get('name')
                    logger.info('Received challenge from %s', challenger_name)
                    if accept_challenge_allowed(challenge, config, state, logger, bot_username):
                        try:
                            client.bots.accept_challenge(challenge['id'])
                            logger.info('Accepted challenge %s from %s', challenge['id'], challenger_name)
                            # Mark upcoming game as vs bot if applicable
                        except Exception as e:
                            logger.exception('Could not accept challenge: %s', e)
                    else:
                        try:
                            client.bots.decline_challenge(challenge['id'])
                            logger.info('Declined challenge %s from %s', challenge['id'], challenger_name)
                        except Exception:
                            logger.info('Could not auto-decline challenge %s', challenge.get('id'))

                elif etype == 'gameStart':
                    game_id = event.get('game', {}).get('id')
                    #check if this game has already been started on another thread 
                    # to avoid duplicate start events starting multiple threads
                    # This check helps prevent HTTP 429 errors due to rapid multiple connections
                    if has_active_game(game_id, logger): continue

                    logger.info('Game started: %s', game_id)
                    t = threading.Thread(target=play_game, args=(client, engine_path, game_id, bot_username, logger, state, config_depth, max_hash_size), daemon=True, name=f'game-{game_id}')
                    t.start()

                elif etype == "gameFinish":
                    game = event.get('game', {})
                    game_id = game.get('id')
                    status = game.get('status')
                    winner = game.get('winner')
                    logger.info('Game %s finished: status=%s, winner=%s', game_id, status, winner)
                else:
                    logger.debug('Unhandled event type %s', etype)

            backoff = 5
        except Exception as e:
            err = str(e)
            if '429' in err:
                logger.warning('HTTP 429 received; waiting 70 seconds')
                #log url of the request that caused 429 if possible, otherwise dump exception details into a string
                logger.warning('429 error details: %s', str(e))
                time.sleep(70)
                backoff = 5
            else:
                logger.exception('Error in event loop: %s', e)
                logger.info('Retrying in %s seconds', backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)


def main():
    """
    Entry point: Parses args, loads config/logs, starts event loop.
    
    Handles shutdown signals gracefully (logs, flushes).
    Note: Contains a placeholder idle_loop (does nothing)—real one in event_loop.
    
    Run with `lichess-bot.py --conf lichess_bot.conf`. Edit conf first!
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf', help='Path to config file', default=DEFAULT_CONF)
    args = parser.parse_args()

    config = load_config(args.conf)
    rotate_kb = int(config.get('logging', 'rotate_kb'))
    log_file = config.get('logging', 'general_log')
    logger = setup_logging(log_file, rotate_kb, config.get('lichess', 'bot_username'))

    # Startup logs
    logger.info('Bot starting as %s', config.get('lichess', 'bot_username'))
    logger.info('Startup: conf=%s cwd=%s python=%s', args.conf, os.getcwd(), sys.executable)
    logger.info('Lichess base_url=%s stockfish=%s', config.get('lichess', 'base_url'), config.get('engine', 'stockfish_path'))

    # Graceful shutdown

    def _handle_exit(signum, frame):
        logger.info('SIG%s shutdown (pid %d)', signum, os.getpid())  # Use adapter logger
        # Flush all
        base_logger = logger.logger if hasattr(logger, 'logger') else logger
        for h in base_logger.handlers[:]:
            h.flush()
            h.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_exit)
    signal.signal(signal.SIGTERM, _handle_exit)
    state = BotState()


    try:
        event_loop(config, logger, state)
    except Exception as e:
        logger.exception('Fatal error in main event loop: %s', e)
    finally:
        logger.info('Bot stopped (pid %d)', os.getpid())


if __name__ == '__main__':
    main()

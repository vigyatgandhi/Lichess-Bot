import argparse
import berserk
import chess
import chess.engine
import configparser
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import signal
import sys
import time
import threading
import random
from datetime import datetime, timedelta

# ─── DEFAULT CONFIGURATION ─────────────────────────────────────────────
DEFAULT_CONF = "lichess_bot.conf"


def load_config(conf_path):
    config = configparser.ConfigParser()
    # Defaults
    config['lichess'] = {
        'bot_username': 'Ar4Asd1-BOT',
        'bot_api_token': '',
        'base_url': 'https://lichess.org'
    }
    config['engine'] = {
        'stockfish_path': ''
    }
    config['logging'] = {
        'general_log': 'lichess_bot.log',
        'rotate_kb': '1024'
    }
    config['behavior'] = {
        'accept_speeds': 'rapid,blitz,classical',
        'accept_variants': 'standard',
        'idle_seconds': '60',
        # comma-separated usernames to consider challenging when idle
        'idle_candidates': '',
        'bot_daily_limit': '100'
    }

    if os.path.exists(conf_path):
        config.read(conf_path)
    else:
        # write a sample config so user can edit
        with open(conf_path, 'w') as f:
            config.write(f)
        config.read(conf_path)

    return config


def setup_logging(log_file, rotate_kb, username=None):
    base_logger = logging.getLogger('lichess_bot')
    base_logger.setLevel(logging.INFO)
    # include PID and username in every log line
    formatter = logging.Formatter('%(asctime)s %(process)d %(levelname)s %(username)s: %(message)s')

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    base_logger.addHandler(ch)

    # Rotating file handler
    fh = RotatingFileHandler(log_file, maxBytes=rotate_kb * 1024, backupCount=5)
    fh.setFormatter(formatter)
    base_logger.addHandler(fh)

    # return an adapter that adds username to every record
    return logging.LoggerAdapter(base_logger, {'username': username or ''})


class BotState:
    def __init__(self, stats_file='stats.json'):
        self.lock = threading.Lock()
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
            # keep only recent 1000 games in memory
            self.data['games'] = self.data['games'][-1000:]
        self.save()

    def bot_games_today(self, bot_username):
        today = datetime.utcnow().date()
        with self.lock:
            return sum(1 for g in self.data['games']
                       if g.get('is_bot') and datetime.fromisoformat(g['start_time']).date() == today)


def game_log_filename(game_id, opponent, ts_iso=None):
    # Use provided ISO timestamp (from game_record start_time) to keep filename stable
    if ts_iso:
        try:
            ts = datetime.fromisoformat(ts_iso).strftime('%Y%m%dT%H%M%SZ')
        except Exception:
            ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    else:
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    safe_opp = (opponent or 'unknown').replace('/', '_').replace(' ', '_')
    return f"game_{ts}_{safe_opp}_{game_id}.log"


def play_game(client, engine_path, game_id, bot_username, logger, state: BotState, depth=15):
    logger.info(f"Starting game {game_id}")
    # Open engine
    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as e:
        logger.exception("Failed to open engine: %s", e)
        return

    board = chess.Board()
    bot_color = None
    game_log = None
    white_name = None
    black_name = None
    last_moves_count = 0
    time_control = None
    white_name = None
    black_name = None
    last_moves_count = 0
    game_record = {
        'game_id': game_id,
        'start_time': datetime.utcnow().isoformat(),
        'end_time': None,
        'moves': [],
        'opponent': None,
        'variant': None,
        'speed': None,
        'is_bot': False
    }

    try:
        for event in client.bots.stream_game_state(game_id):
            etype = event.get('type')
            # log raw event into per-game log if available
            if game_log:
                try:
                    game_log.info('Event: %s', json.dumps(event, default=str))
                except Exception:
                    game_log.info('Event: %s', str(event))
            if etype == 'gameFull':
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
                # capture time control if present
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
                # create per-game log (include PID) once and keep filename stable using game start_time
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
                moves = event.get('moves', '')
                board = chess.Board()
                moves_list = moves.split() if moves else []
                if moves_list:
                    for m in moves_list:
                        board.push_uci(m)

                # push new moves to game log with timestamp, move index, player name and player clock
                if game_log:
                    # helper to format milliseconds to mm:ss or hh:mm:ss
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

                    # detect new moves since last seen
                    for i in range(last_moves_count, len(moves_list)):
                        move = moves_list[i]
                        ply = i + 1
                        player_color = 'white' if i % 2 == 0 else 'black'
                        player_name = white_name if player_color == 'white' else black_name
                        # build game-time as MoveNumber + TimeControl
                        tc_display = time_control or 'unknown'
                        ts = datetime.utcnow().isoformat()
                        game_log.info('%s: move %d %s(%s+%s) %s', ts, ply, player_name, ply, tc_display, move)
                    last_moves_count = len(moves_list)

            else:
                continue

            # detect game over using board or event status
            if board.is_game_over():
                result = board.result() if hasattr(board, 'result') else 'unknown'
                logger.info('Game %s over, result %s', game_id, result)
                if game_log:
                    game_log.info('Game over detected locally, result: %s', result)
                break

            # also detect status/winner from event payloads (resign/abort/offline/timeout)
            status = event.get('status')
            if status:
                winner = event.get('winner') or event.get('winnerColor')
                logger.info('Game %s status update: %s (winner=%s)', game_id, status, winner)
                if game_log:
                    game_log.info('Status update: %s (winner=%s)', status, winner)
                # treat terminal statuses as game over
                if status in ('mate', 'resign', 'timeout', 'outoftime', 'draw', 'aborted', 'stalemate', 'cheat', 'variantEnd'):
                    break

            # If it's our turn
            if bot_color and ((board.turn == chess.WHITE and bot_color == 'white') or
                              (board.turn == chess.BLACK and bot_color == 'black')):
                logger.info('My turn in game %s. FEN: %s', game_id, board.fen())
                try:
                    result = engine.play(board, chess.engine.Limit(depth=depth))
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

            time.sleep(1)

    finally:
        try:
            engine.quit()
        except Exception:
            pass
        game_record['end_time'] = datetime.utcnow().isoformat()
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
    # challenge dict expected to have 'speed' and 'variant' (with 'key') and challenger info
    speeds = [s.strip().lower() for s in config.get('behavior', 'accept_speeds').split(',')]
    variants = [v.strip().lower() for v in config.get('behavior', 'accept_variants').split(',')]
    speed = (challenge.get('speed') or '').lower()
    variant = (challenge.get('variant') or {}).get('key', '').lower()
    challenger = challenge.get('challenger', {}).get('name')
    is_bot = challenge.get('challenger', {}).get('title', '') == 'BOT' or challenge.get('isBot', False)

    # reject disallowed variants
    if variant and variant not in variants:
        logger.info('Rejecting challenge from %s: variant %s not allowed', challenger, variant)
        return False
    # reject disallowed speeds
    if speed and speed not in speeds:
        logger.info('Rejecting challenge from %s: speed %s not allowed', challenger, speed)
        return False

    # enforce bot daily limits
    if is_bot:
        limit = int(config.get('behavior', 'bot_daily_limit'))
        if state.bot_games_today(bot_username) >= limit:
            logger.info('Rejecting challenge from %s: bot daily limit reached', challenger)
            return False

    return True


def event_loop(config, logger, state: BotState):
    token = config.get('lichess', 'bot_api_token')
    base_url = config.get('lichess', 'base_url')
    bot_username = config.get('lichess', 'bot_username')
    engine_path = config.get('engine', 'stockfish_path')

    session = berserk.TokenSession(token)
    client = berserk.Client(session=session, base_url=base_url)

    # start idle challenger thread here so it can use the same client/session
    idle_seconds = int(config.get('behavior', 'idle_seconds'))
    idle_candidates_raw = config.get('behavior', 'idle_candidates').strip()
    idle_candidates = [c.strip() for c in idle_candidates_raw.split(',') if c.strip()]

    def has_active_games():
        # any running threads named 'game-<id>' indicate active games
        for t in threading.enumerate():
            try:
                if t.name.startswith('game-') and t.is_alive():
                    return True
            except Exception:
                continue
        return False

    def idle_loop():
        backoff = 5
        while True:
            try:
                time.sleep(idle_seconds)
                # skip if there are active games
                if has_active_games():
                    logger.debug('Idle challenger: active games present, skipping challenge')
                    continue

                if not idle_candidates:
                    logger.debug('Idle challenger: no candidates configured')
                    continue

                # choose random candidate order to avoid always hitting same user
                candidates = idle_candidates[:]
                random.shuffle(candidates)

                for candidate in candidates:
                    if not candidate or candidate.lower() == bot_username.lower():
                        continue
                    try:
                        logger.info('Idle challenger: attempting to challenge %s', candidate)
                        # First, attempt to use high-level berserk API if available
                        tried = False
                        if hasattr(client, 'challenges') and hasattr(client.challenges, 'create'):
                            # try a common argument set; some berserk versions accept keywords
                            try:
                                client.challenges.create(candidate, rated=False, clock_limit=300, clock_increment=5, variant='standard')
                                logger.info('Issued challenge to %s via client.challenges.create', candidate)
                                tried = True
                                break
                            except TypeError:
                                # fallback to positional
                                try:
                                    client.challenges.create(candidate, False, 300, 5, 'standard')
                                    logger.info('Issued challenge to %s via client.challenges.create (positional)', candidate)
                                    tried = True
                                    break
                                except Exception as e:
                                    logger.debug('client.challenges.create positional failed: %s', e)

                        # If high-level API not available or failed, try posting directly via session if supported
                        if not tried and hasattr(session, 'post'):
                            # Lichess challenge endpoint: POST /api/challenge/{username}
                            url = f"{base_url}/api/challenge/{candidate}"
                            payload = {'rated': 'false', 'clock.limit': '300', 'clock.increment': '5', 'variant': 'standard', 'color': 'random'}
                            try:
                                r = session.post(url, data=payload)
                                if hasattr(r, 'status_code') and 200 <= r.status_code < 300:
                                    logger.info('Issued challenge to %s via direct POST (status=%s)', candidate, r.status_code)
                                    break
                                else:
                                    logger.info('Direct POST challenge to %s failed (status=%s): %s', candidate, getattr(r, 'status_code', None), getattr(r, 'text', ''))
                            except Exception as e:
                                logger.debug('Direct POST challenge to %s error: %s', candidate, e)

                    except Exception as e:
                        logger.exception('Idle challenger error while trying %s: %s', candidate, e)

            except Exception as e:
                logger.exception('Idle challenger encountered error: %s', e)
                time.sleep(backoff)
                backoff = min(backoff * 2, 300)

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
                    logger.info('Game started: %s', game_id)
                    t = threading.Thread(target=play_game, args=(client, engine_path, game_id, bot_username, logger, state), daemon=True, name=f'game-{game_id}')
                    t.start()
                else:
                    logger.debug('Unhandled event type %s', etype)

            backoff = 5
        except Exception as e:
            err = str(e)
            if '429' in err:
                logger.warning('HTTP 429 received; waiting 60 seconds')
                time.sleep(60)
                backoff = 5
            else:
                logger.exception('Error in event loop: %s', e)
                logger.info('Retrying in %s seconds', backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf', help='Path to config file', default=DEFAULT_CONF)
    args = parser.parse_args()

    config = load_config(args.conf)
    rotate_kb = int(config.get('logging', 'rotate_kb'))
    log_file = config.get('logging', 'general_log')
    logger = setup_logging(log_file, rotate_kb, config.get('lichess', 'bot_username'))

    # Log startup metadata including config path, cwd, python executable and engine path
    logger.info('Bot starting as %s', config.get('lichess', 'bot_username'))
    logger.info('Startup: conf=%s cwd=%s python=%s', args.conf, os.getcwd(), sys.executable)
    logger.info('Lichess base_url=%s stockfish=%s', config.get('lichess', 'base_url'), config.get('engine', 'stockfish_path'))

    # signal handlers for graceful shutdown logging
    def _handle_exit(signum, frame):
        base_logger = logger.logger if isinstance(logger, logging.LoggerAdapter) else logger
        base_logger.info('Received signal %s, shutting down (pid %d)', signum, os.getpid())
        try:
            # flush handlers
            for h in list(base_logger.handlers):
                try:
                    h.flush()
                except Exception:
                    pass
        finally:
            sys.exit(0)

    signal.signal(signal.SIGINT, _handle_exit)
    signal.signal(signal.SIGTERM, _handle_exit)
    state = BotState()

    # start idle challenger thread (placeholder: can be implemented to search online players)
    idle_seconds = int(config.get('behavior', 'idle_seconds'))
    def idle_loop():
        while True:
            logger.debug('Idle loop sleeping %s seconds', idle_seconds)
            time.sleep(idle_seconds)
            # Placeholder: search for online players and challenge them.
            # Implementing a safe generic online-search requires calling Lichess endpoints
            # not directly exposed by every berserk client version; leaving as a TODO.
            logger.debug('Idle loop tick - search and challenge not implemented')

    threading.Thread(target=idle_loop, daemon=True).start()

    try:
        event_loop(config, logger, state)
    except Exception as e:
        logger.exception('Fatal error in main event loop: %s', e)
    finally:
        logger.info('Bot stopped (pid %d)', os.getpid())


if __name__ == '__main__':
    main()

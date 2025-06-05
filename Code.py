import berserk
import chess
import chess.engine
import time
import threading

# ─── CONFIGURATION CONSTANTS ──────────────────────────────────────────
BOT_USERNAME = "Ar4Asd1-BOT"  # <-- Replace with Your Lichess bot username
BOT_API_TOKEN = "EnterYourAPIFromLichess"  # <-- Replace with your actual Lichess API token
LICHESS_BASE_URL = "https://lichess.org"  # <-- Base Lichess URL

# Set the path to your Stockfish executable
STOCKFISH_PATH =

#Quick Note (Delete this whole line after reading.) Ask a programmer/AI if your stockfish isn't working. sometimes you need add (r") before and also name the application in stockfish to "stockfish.exe" if you ddo tell the AI/Proggrammer that.
# ─── SETUP LICHESS CLIENT ─────────────────────────────────────────────
session = berserk.TokenSession(BOT_API_TOKEN)
client = berserk.Client(session=session, base_url=LICHESS_BASE_URL)

# ─── FUNCTION: PLAY A GAME WITH STOCKFISH ENGINE ──────────────────────
def play_game(game_id):
    """
    Connects to a Lichess game specified by game_id, determines the bot's color,
    and plays using Stockfish engine when it's the bot's turn.
    """
    bot_color = None
    print(f"Starting game {game_id}")

    # Open Stockfish engine
    try:
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    except Exception as e:
        print("Failed to open engine:", e)
        return

    board = chess.Board()  # Default board setup

    # Send welcome message when game starts
    try:
        time.sleep(2)  # Wait 2 seconds to make sure chat is available
        client.bots.write_in_chat(game_id, "Hello! I am Ar4Asd1-BOT. Good luck and have fun! 🤖♟️")
        print("Welcome message sent!")
    except Exception as chat_error:
        print("Failed to send welcome message:", chat_error)

    # Loop to listen for game events
    for event in client.bots.stream_game_state(game_id):
        if event["type"] == "gameFull":
            if "white" in event and "black" in event:
                if event["white"]["name"].lower() == BOT_USERNAME.lower():
                    bot_color = "white"
                elif event["black"]["name"].lower() == BOT_USERNAME.lower():
                    bot_color = "black"
                else:
                    print("Bot username not found in game participants!")
                    engine.quit()
                    return

            # Handle FEN (fix "startpos" issue)
            initial_fen = event.get("initialFen")
            if initial_fen == "startpos":
                board = chess.Board()
            else:
                board = chess.Board(initial_fen)

        elif event["type"] == "gameState":
            moves = event.get("moves", "")
            board = chess.Board()
            if moves:
                for move in moves.split():
                    board.push_uci(move)
        else:
            continue

        if board.is_game_over():
            print("Game over:", game_id)
            break

        if bot_color and ((board.turn == chess.WHITE and bot_color == "white") or
                          (board.turn == chess.BLACK and bot_color == "black")):
            print(f"My turn in game {game_id}. Board FEN: {board.fen()}")
            try:
                result = engine.play(board, chess.engine.Limit(depth=15))
                best_move = result.move

                # Validate move before sending it
                if best_move in board.legal_moves:
                    client.bots.make_move(game_id, best_move.uci())
                    board.push(best_move)
                    print("Played move:", best_move.uci())
                else:
                    print(f"Invalid move suggested: {best_move.uci()} - Skipping move")
            except Exception as e:
                print("Error while making move:", e)

        time.sleep(1)  # Pause briefly before the next iteration

    engine.quit()
    print("Exiting game thread:", game_id)

# ─── FUNCTION: EVENT LOOP TO HANDLE CHALLENGES & GAME STARTS ──────────────────
def event_loop():
    """
    Connects to Lichess events and listens for incoming challenges and game start events.
    It uses a backoff mechanism if errors occur (like HTTP 429).
    """
    backoff = 5  # Start with a 5-second delay in case of errors
    while True:
        try:
            stream = client.bots.stream_incoming_events()
            for event in stream:
                if event["type"] == "challenge":
                    challenge = event["challenge"]
                    print(f"Received challenge from {challenge['challenger']['name']}")
                    try:
                        client.bots.accept_challenge(challenge["id"])
                        print(f"Accepted challenge: {challenge['id']}")
                    except Exception as acc_err:
                        print("Could not accept challenge:", acc_err)

                elif event["type"] == "gameStart":
                    game_id = event["game"]["id"]
                    print("Game started. Game ID:", game_id)
                    threading.Thread(target=play_game, args=(game_id,), daemon=True).start()
                else:
                    print("Unrecognized event type:", event["type"])

            backoff = 5
        except Exception as e:
            error_message = str(e)
            if "429" in error_message:
                print("HTTP 429 received: Too Many Requests. Waiting 60 seconds before reconnecting.")
                time.sleep(60)
                backoff = 5
            else:
                print("Error in event loop:", e)
                print(f"Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)  # Exponential backoff capped at 60 seconds

# ─── MAIN FUNCTION ─────────────────────────────────────────────────────
def main():
    print("Bot starting as", BOT_USERNAME)
    event_loop()

if __name__ == "__main__":
    main()

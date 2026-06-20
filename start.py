import sys
import customtkinter as ctk
from tkinter import messagebox, Canvas
import random
import json
import os
import time
import math
import datetime
from datetime import date
try:
    import winsound # Windows only
    SOUND_ENABLED = True
except ImportError:
    SOUND_ENABLED = False

# ================= SETTINGS =================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

THEMES = {
    "Cyberpunk": {"accent": "#00F5FF", "bg1": "#050816", "bg2": "#190033", "pink": "#FF00FF", "green": "#39FF14", "purple": "#7C3AED", "purple_hover": "#9333EA"},
    "Matrix": {"accent": "#39FF14", "bg1": "#001100", "bg2": "#002200", "pink": "#00FF88", "green": "#39FF14", "purple": "#00AA00", "purple_hover": "#00CC00"},
    "Neon": {"accent": "#FF00FF", "bg1": "#1A0033", "bg2": "#330066", "pink": "#FF66FF", "green": "#00FFFF", "purple": "#9D00FF", "purple_hover": "#B833FF"},
    "Retro": {"accent": "#FFB000", "bg1": "#2B1B00", "bg2": "#4D2F00", "pink": "#FF6B35", "green": "#C2FF05", "purple": "#FF8C00", "purple_hover": "#FFA500"},
    "PinkBlack": {"accent": "#FF1493", "bg1": "#000000", "bg2": "#1A001A", "pink": "#FF69B4", "green": "#FF00FF", "purple": "#C71585", "purple_hover": "#FF1493"}
}

WHITE = "#FFFFFF"
ORANGE = "#FF6B35"
RED = "#FF073A"
GOLD = "#FFD700"

STATS_FILE = "stats.json"

# ================= STATS =================
DEFAULT_STATS = {
    "player_name": "Player1",
    "games_played": 0,
    "highest_score": 0,
    "best_streak": 0,
    "total_attempts": 0,
    "fastest_time": None,
    "achievements": [],
    "points": 0,
    "daily_seed": "",
    "daily_high": 0,
    "leaderboard": [],
    "theme": "PinkBlack"
}

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                data = json.load(f)
                for key in DEFAULT_STATS:
                    if key not in data:
                        data[key] = DEFAULT_STATS[key]
                return data
        except:
            return DEFAULT_STATS.copy()
    return DEFAULT_STATS.copy()

def save_stats():
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

stats = load_stats()

# Load theme colors after stats
theme = THEMES[stats["theme"]]
CYAN = theme["accent"]
PINK = theme["pink"]
GREEN = theme["green"]
PURPLE = theme["purple"]
PURPLE_HOVER = theme["purple_hover"]

# ================= GAME VARIABLES =================
difficulty_ranges = {"Easy": 50, "Normal": 100, "Hard": 500, "Insane": 1000}
current_difficulty = "Normal"
max_number = difficulty_ranges[current_difficulty]
min_number = 1
secret_number = random.randint(min_number, max_number)
attempts = 0
current_streak = 0
hints_used = 0
max_hints = 3
start_time = 0
guess_history = []
game_mode = "normal"
double_points_active = False

# Multiplayer
mp_players = ["P1", "P2"]
mp_turn = 0
mp_attempts = {}
mp_winner = None

# Bot
bot_low, bot_high = 1, 100
bot_attempts = 0
bot_delay = 1200

# Music
music_on = False

# ================= MAIN WINDOW =================
root = ctk.CTk()
root.title("⚡ Number Guessing Arena Pro")
root.geometry("1100x750")
root.resizable(True, True)
root.minsize(900, 650)

bg_canvas = Canvas(root, highlightthickness=0)
bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

# Fixed: only resize on root window events, not child widgets
def on_resize(event):
    if event.widget == root:
        try:
            bg_canvas.configure(width=root.winfo_width(), height=root.winfo_height())
        except:
            pass

root.bind("<Configure>", on_resize)

# ================= ANIMATED BACKGROUND =================
bg_phase = 0
def animate_background():
    global bg_phase
    bg_phase += 0.02
    t = THEMES[stats["theme"]]
    r1, g1, b1 = tuple(int(t["bg1"][i:i+2], 16) for i in (1, 3, 5))
    r2, g2, b2 = tuple(int(t["bg2"][i:i+2], 16) for i in (1, 3, 5))
    factor = (math.sin(bg_phase) + 1) / 2
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    color = f"#{r:02x}{g:02x}{b:02x}"
    bg_canvas.configure(bg=color)
    root.after(50, animate_background)

# ================= PARTICLE EFFECT =================
particles = []
def create_particles(x, y):
    for _ in range(25):
        particles.append({
            "x": x, "y": y,
            "vx": random.uniform(-5, 5),
            "vy": random.uniform(-9, -3),
            "life": 35,
            "id": bg_canvas.create_oval(x, y, x+7, y+7, fill=CYAN, outline="")
        })

def update_particles():
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.35
        p["life"] -= 1
        bg_canvas.coords(p["id"], p["x"], p["y"], p["x"]+7, p["y"]+7)
        if p["life"] <= 0:
            bg_canvas.delete(p["id"])
            particles.remove(p)
    if particles:
        root.after(30, update_particles)

# ================= SOUND & MUSIC =================
def play_sound(type):
    if not SOUND_ENABLED:
        return
    if type == "correct":
        winsound.Beep(1200, 120)
        winsound.Beep(1500, 180)
    elif type == "wrong":
        winsound.Beep(400, 100)
    elif type == "hint":
        winsound.Beep(800, 80)
    elif type == "click":
        winsound.Beep(1000, 50)

def play_ambient_loop():
    if not music_on or not SOUND_ENABLED:
        return
    notes = [440, 554, 659, 554, 740, 659, 554, 440]
    for i, freq in enumerate(notes):
        root.after(i*250, lambda f=freq: winsound.Beep(f, 180))
    root.after(2200, play_ambient_loop)

def toggle_music():
    global music_on
    music_on = not music_on
    music_btn.configure(text=f"🎵 Music: {'ON' if music_on else 'OFF'}")
    if music_on:
        play_ambient_loop()

# ================= THEME =================
def apply_theme(name):
    global theme, CYAN, PINK, GREEN, PURPLE, PURPLE_HOVER
    stats["theme"] = name
    theme = THEMES[name]
    CYAN = theme["accent"]
    PINK = theme["pink"]
    GREEN = theme["green"]
    PURPLE = theme["purple"]
    PURPLE_HOVER = theme["purple_hover"]
    save_stats()
    # Update key widgets
    for w in [title, game_title, result_title, rank_label]:
        w.configure(text_color=CYAN)
    for w in [subtitle, streak_label, best_streak_label, history_box, tip_box]:
        w.configure(text_color=PINK)
    for w in [description, attempt_label, tip_label]:
        w.configure(text_color=GREEN)
    # Update buttons
    start_solo_btn.configure(fg_color=PURPLE, hover_color=PURPLE_HOVER)
    check_btn.configure(fg_color=PURPLE, hover_color=PURPLE_HOVER)
    play_again_btn.configure(fg_color=PURPLE, hover_color=PURPLE_HOVER)

# ================= LEADERBOARD =================
# ================= LEADERBOARD =================
def update_leaderboard(name, score, time_taken, mode):
    stats["leaderboard"].append({
        "name": name,
        "score": score,
        "time": round(time_taken, 1),
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "mode": mode
    })
    stats["leaderboard"] = sorted(
        stats["leaderboard"],
        key=lambda x: (-x["score"], x["time"])
    )[:10]
    save_stats()

def show_leaderboard():
    lb = ctk.CTkToplevel(root)
    lb.title("🏆 Leaderboard")
    lb.geometry("500x400")
    lb.configure(fg_color=THEMES[stats["theme"]]["bg1"])
    lb.resizable(False, False)
    lb.transient(root) # Keep on top of main window
    lb.grab_set() # Modal - user must close it
    lb.focus_set() # Force focus

    ctk.CTkLabel(lb, text="🏆 TOP 10 ARENA CHAMPIONS",
                 font=("Bahnschrift", 20, "bold"), text_color=CYAN).pack(pady=10)

    if not stats["leaderboard"]:
        ctk.CTkLabel(lb, text="No scores yet. Be the first!",
                     font=("Consolas", 16), text_color=WHITE).pack(pady=20)
        ctk.CTkButton(lb, text="Close", command=lb.destroy).pack(pady=10)
        return

    # Scrollable frame for leaderboard
    scroll_frame = ctk.CTkScrollableFrame(lb, width=450, height=280)
    scroll_frame.pack(pady=5, padx=10, fill="both", expand=True)

    for i, entry in enumerate(stats["leaderboard"], 1):
        text = f"{i}. {entry['name']} - {entry['score']}pts - {entry['time']}s - {entry['mode']}"
        ctk.CTkLabel(scroll_frame, text=text, font=("Consolas", 14),
                     text_color=WHITE, anchor="w").pack(anchor="w", padx=10, pady=2)

    ctk.CTkButton(lb, text="Close", command=lb.destroy).pack(pady=10)
# ================= SCORING =================
def get_difficulty_multiplier():
    return {"Easy": 1.0, "Normal": 1.5, "Hard": 2.0, "Insane": 3.0}[current_difficulty]

def calculate_score(attempts, time_taken, hints_used):
    base_ranges = {50: 5, 100: 8, 500: 12, 1000: 15, "custom": 20}
    rng = max_number - min_number + 1
    max_att = base_ranges.get(rng, 20)

    if attempts <= max_att * 0.3:
        score = 100
    elif attempts <= max_att * 0.6:
        score = 80
    elif attempts <= max_att:
        score = 60
    else:
        score = 40

    if time_taken < 30: score += 20
    elif time_taken < 60: score += 10

    score -= hints_used * 10
    score = int(score * get_difficulty_multiplier())

    if game_mode == "daily": score = int(score * 1.2)
    if game_mode == "custom" and rng > 500: score = int(score * 1.5)
    if double_points_active: score *= 2

    return max(score, 10)

def get_rank(score):
    if score >= 300: return "💎 GODLIKE"
    elif score >= 200: return "🔱 LEGEND"
    elif score >= 110: return "🥇 MASTER GUESSER"
    elif score >= 70: return "🥈 EXPERT"
    elif score >= 50: return "🥉 INTERMEDIATE"
    else: return "🎯 BEGINNER"

def get_tip(attempts):
    if attempts <= 3: return "Excellent! Your strategy is highly efficient."
    elif attempts <= 6: return "Great job! Keep narrowing the range quickly."
    elif attempts <= 10: return "Try using binary search logic."
    else: return "Start from the middle and eliminate half the range each time."

def check_achievements(score, time_taken, attempts):
    new_achievements = []
    checks = [
        (score >= 300, "Godlike"),
        (attempts == 1, "Psychic"),
        (time_taken < 10, "Speed Demon"),
        (stats["games_played"] >= 10, "Persistent"),
        (stats["games_played"] >= 50, "Veteran"),
        (current_streak >= 5, "Unstoppable")
    ]
    for cond, name in checks:
        if cond and name not in stats["achievements"]:
            new_achievements.append(name)

    for ach in new_achievements:
        stats["achievements"].append(ach)
        messagebox.showinfo("🏆 Achievement Unlocked!", f"You unlocked: {ach}")

# ================= POWER-UPS =================
def buy_powerup(powerup):
    costs = {"reveal": 50, "double": 100, "skip": 30}
    if stats["points"] < costs[powerup]:
        messagebox.showinfo("Shop", "Not enough points!")
        return False
    stats["points"] -= costs[powerup]
    points_shop_label.configure(text=f"💰 Points: {stats['points']}")
    save_stats()
    play_sound("click")
    return True

def use_reveal_range():
    if not buy_powerup("reveal"): return
    low = max(min_number, secret_number - 10)
    high = min(min_number + max_number - 1, secret_number + 10)
    messagebox.showinfo("Reveal Range", f"Number is between {low} and {high}")

def use_double_points():
    global double_points_active
    if buy_powerup("double"):
        double_points_active = True
        messagebox.showinfo("Double Points", "Next win gives 2x points!")

def use_skip_turn():
    if game_mode!= "multiplayer":
        messagebox.showinfo("Shop", "Skip Turn only works in Multiplayer!")
        return
    if buy_powerup("skip"):
        next_mp_turn()

# ================= FRAME MANAGEMENT =================
def show_frame(frame):
    for f in (start_frame, game_frame, result_frame):
        f.place_forget()
    frame.place(relx=0.5, rely=0.5, anchor="center")

# ================= EXIT HANDLER =================
def exit_game():
    confirm = messagebox.askyesno(
        "⚠ Exit Confirmation",
        "Are you sure you want to leave the Digital Arena?\n\nYour statistics and progress have been saved."
    )
    if confirm:
        save_stats()
        root.destroy()

def add_exit_button(frame):
    exit_x = ctk.CTkButton(frame, text="❌", width=40, height=40,
                           fg_color="#E11D48", hover_color="#BE123C",
                           font=("Arial", 18, "bold"), command=exit_game)
    exit_x.place(relx=0.98, rely=0.02, anchor="ne")

# ================= GAME MODE SETUP =================
def set_difficulty(choice):
    global current_difficulty, max_number, min_number
    current_difficulty = choice
    max_number = difficulty_ranges[choice]
    min_number = 1
    difficulty_label.configure(text=f"Mode: {choice} | Range: {min_number}-{min_number+max_number-1}")

def set_name():
    dialog = ctk.CTkInputDialog(text="Enter your player name:", title="Name")
    name = dialog.get_input()
    if name:
        stats["player_name"] = name[:12]
        name_label.configure(text=f"Player: {stats['player_name']}")
        save_stats()

def reset_game_vars():
    global secret_number, attempts, hints_used, start_time, guess_history
    global mp_winner, double_points_active, bot_low, bot_high, bot_attempts
    secret_number = random.randint(min_number, min_number + max_number - 1)
    attempts = 0
    hints_used = 0
    guess_history = []
    start_time = time.time()
    mp_winner = None
    double_points_active = False
    bot_low, bot_high = min_number, min_number + max_number - 1
    bot_attempts = 0

def start_game():
    reset_game_vars()
    attempt_label.configure(text="Attempts: 0")
    result_label.configure(text="Waiting for your guess...", text_color=CYAN)
    hint_btn.configure(text=f"💡 HINT ({max_hints - hints_used})")
    guess_entry.delete(0, "end")
    update_history_display()
    instruction.configure(text=f"Enter a number between {min_number} and {min_number+max_number-1}")

    if game_mode == "multiplayer":
        turn_label.configure(text=f"Turn: {mp_players[mp_turn]}")
        turn_label.pack(pady=5)
    else:
        turn_label.pack_forget()

    if game_mode == "vsbot":
        bot_label.pack(pady=5)
        bot_guess()
    else:
        bot_label.pack_forget()

    show_frame(game_frame)
    play_sound("click")

def start_daily():
    global game_mode, secret_number, max_number, min_number
    game_mode = "daily"
    today = str(date.today())
    random.seed(today)
    min_number = 1
    max_number = 100
    secret_number = random.randint(min_number, max_number)
    random.seed()
    start_game()

def start_custom_range():
    dialog = ctk.CTkInputDialog(text="Enter min,max e.g. 200,800:", title="Custom Range")
    try:
        min_n, max_n = map(int, dialog.get_input().split(","))
        if min_n >= max_n or min_n < 1: raise ValueError
        global game_mode, max_number, min_number
        game_mode = "custom"
        min_number = min_n
        max_number = max_n - min_n + 1
        start_game()
    except:
        messagebox.showerror("Error", "Invalid range. Use: min,max")

def start_multiplayer():
    global game_mode, mp_players, mp_turn, mp_attempts
    dialog = ctk.CTkInputDialog(text="Enter 2-4 player names comma-separated:", title="Multiplayer")
    names = dialog.get_input()
    if not names: return
    mp_players = [n.strip()[:8] for n in names.split(",") if n.strip()][:4]
    if len(mp_players) < 2:
        messagebox.showerror("Error", "Need at least 2 players")
        return
    mp_turn = 0
    mp_attempts = {p: 0 for p in mp_players}
    game_mode = "multiplayer"
    start_game()

def start_vsbot():
    global game_mode
    game_mode = "vsbot"
    start_game()

# ================= GAME LOGIC =================
def use_hint():
    global hints_used
    if hints_used >= max_hints:
        messagebox.showwarning("No Hints Left", "You've used all your hints!")
        return
    hints_used += 1
    hint_btn.configure(text=f"💡 HINT ({max_hints - hints_used})")
    play_sound("hint")

    hints = []
    hints.append("Even" if secret_number % 2 == 0 else "Odd")
    if secret_number > 1:
        is_prime = all(secret_number % i!= 0 for i in range(2, int(secret_number**0.5) + 1))
        if is_prime: hints.append("Prime number")
    digit_sum = sum(int(d) for d in str(secret_number))
    hints.append(f"Digit sum: {digit_sum}")
    if secret_number % 5 == 0: hints.append("Divisible by 5")
    messagebox.showinfo("💡 Hint", f"Here's a clue: {random.choice(hints)}")

def update_history_display():
    history_text = "📜 Last Guesses:\n"
    for g, res in guess_history[-5:]:
        history_text += f"{g} → {res}\n"
    history_box.configure(text=history_text)

def next_mp_turn():
    global mp_turn
    mp_turn = (mp_turn + 1) % len(mp_players)
    turn_label.configure(text=f"Turn: {mp_players[mp_turn]}")

def bot_guess():
    global bot_low, bot_high, bot_attempts
    if bot_low > bot_high or game_mode!= "vsbot": return
    bot_attempts += 1
    guess = (bot_low + bot_high) // 2
    bot_label.configure(text=f"🤖 Bot guesses: {guess} | Attempts: {bot_attempts}")
    if guess < secret_number:
        bot_low = guess + 1
    elif guess > secret_number:
        bot_high = guess - 1
    else:
        bot_label.configure(text=f"🤖 Bot wins in {bot_attempts}!")
        return
    root.after(bot_delay, bot_guess)

def check_guess():
    global attempts, current_streak, mp_winner
    try:
        guess = int(guess_entry.get())
        if guess < min_number or guess > min_number + max_number - 1:
            messagebox.showwarning("Invalid Input", f"Enter a number between {min_number} and {min_number+max_number-1}.")
            return

        attempts += 1
        if game_mode == "multiplayer":
            mp_attempts[mp_players[mp_turn]] += 1
            attempt_label.configure(text=f"Attempts: {mp_attempts[mp_players[mp_turn]]} | Total: {attempts}")
        else:
            attempt_label.configure(text=f"Attempts: {attempts}")

        if guess < secret_number:
            result_label.configure(text="📉 TOO LOW!", text_color=ORANGE)
            guess_history.append((guess, "LOW"))
            play_sound("wrong")
            if game_mode == "multiplayer": next_mp_turn()
            if game_mode == "vsbot": bot_low = max(bot_low, guess + 1)
        elif guess > secret_number:
            result_label.configure(text="📈 TOO HIGH!", text_color=RED)
            guess_history.append((guess, "HIGH"))
            play_sound("wrong")
            if game_mode == "multiplayer": next_mp_turn()
            if game_mode == "vsbot": bot_high = min(bot_high, guess - 1)
        else:
            current_streak += 1
            time_taken = time.time() - start_time
            score = calculate_score(attempts, time_taken, hints_used)
            guess_history.append((guess, "CORRECT"))
            play_sound("correct")
            create_particles(550, 375)
            update_particles()

            # Update stats
            stats["games_played"] += 1
            stats["total_attempts"] += attempts
            if score > stats["highest_score"]:
                stats["highest_score"] = score
            if current_streak > stats["best_streak"]:
                stats["best_streak"] = current_streak
            if stats["fastest_time"] is None or time_taken < stats["fastest_time"]:
                stats["fastest_time"] = time_taken
            if game_mode == "daily" and score > stats["daily_high"]:
                stats["daily_high"] = score

            if game_mode == "multiplayer":
                mp_winner = mp_players[mp_turn]

            check_achievements(score, time_taken, attempts)
            award_points(score)
            update_leaderboard(stats["player_name"], score, time_taken, game_mode)
            save_stats()
            display_results(score, time_taken)

        update_history_display()
        guess_entry.delete(0, "end")
    except ValueError:
        messagebox.showwarning("Invalid Input", "Please enter a valid number.")

def award_points(score):
    earned = score // 10
    stats["points"] += earned
    points_label.configure(text=f"+{earned} points! Total: {stats['points']}")
    points_shop_label.configure(text=f"💰 Points: {stats['points']}")

def display_results(score, time_taken):
    global double_points_active
    avg_attempts = stats["total_attempts"] / stats["games_played"] if stats["games_played"] > 0 else 0
    fastest = f"{stats['fastest_time']:.1f}s" if stats['fastest_time'] else "N/A"
    ach_text = ", ".join(stats['achievements']) if stats['achievements'] else "None"

    winner_text = f"🏆 Winner: {mp_winner}" if game_mode == "multiplayer" else ""

    score_label.configure(text=f"🏆 Score: {score}")
    attempts_result.configure(text=f"🎯 Attempts: {attempts}")
    time_label.configure(text=f"⏱ Time: {time_taken:.1f}s")
    streak_label.configure(text=f"🔥 Streak: {current_streak}")
    best_streak_label.configure(text=f"⭐ Best Streak: {stats['best_streak']}")
    rank_label.configure(text=f"Rank: {get_rank(score)}")
    tip_label.configure(text=f"💡 Tip:\n{get_tip(attempts)}")
    winner_label.configure(text=winner_text)

    stats_label.configure(
        text=(f"📊 STATISTICS\n\n"
              f"Games Played : {stats['games_played']}\n"
              f"Highest Score : {stats['highest_score']}\n"
              f"Daily High : {stats['daily_high']}\n"
              f"Average Attempts : {avg_attempts:.2f}\n"
              f"Fastest Time : {fastest}\n"
              f"Achievements : {ach_text}")
    )
    double_points_active = False
    show_frame(result_frame)

# ================= START PAGE =================
start_frame = ctk.CTkFrame(root, fg_color="transparent", width=1000, height=700)
add_exit_button(start_frame)

title = ctk.CTkLabel(start_frame, text="⚡ NUMBER GUESSING ARENA PRO ⚡",
                     font=("Bahnschrift", 34, "bold"), text_color=CYAN)
title.pack(pady=(40, 15))

subtitle = ctk.CTkLabel(start_frame, text="ENTER THE DIGITAL ARENA",
                        font=("Consolas", 20, "bold"), text_color=PINK)
subtitle.pack()

description = ctk.CTkLabel(start_frame, text="""🎯 Multiple modes: Solo, Daily, Multiplayer, Vs Bot
🏆 Dynamic scoring + time bonuses
🔥 Build streaks & unlock achievements
💡 Strategic hints & power-ups shop
🏅 Global leaderboard with themes""",
    font=("Consolas", 16), text_color=GREEN, justify="center")
description.pack(pady=20)

name_label = ctk.CTkLabel(start_frame, text=f"Player: {stats['player_name']}",
                          font=("Consolas", 16, "bold"), text_color=WHITE)
name_label.pack()

ctk.CTkButton(start_frame, text="✏ Change Name", width=150, command=set_name).pack(pady=5)

difficulty_label = ctk.CTkLabel(start_frame, text=f"Mode: {current_difficulty} | Range: 1-{max_number}",
                                font=("Consolas", 16, "bold"), text_color=WHITE)
difficulty_label.pack(pady=10)

difficulty_menu = ctk.CTkOptionMenu(start_frame, values=list(difficulty_ranges.keys()),
                                    command=set_difficulty, width=200, height=40,
                                    font=("Bahnschrift", 16), dropdown_font=("Bahnschrift", 16))
difficulty_menu.set(current_difficulty)
difficulty_menu.pack()

mode_frame = ctk.CTkFrame(start_frame, fg_color="transparent")
mode_frame.pack(pady=15)

start_solo_btn = ctk.CTkButton(mode_frame, text="▶ SOLO GAME", width=180, height=45, fg_color=PURPLE,
              hover_color=PURPLE_HOVER, font=("Bahnschrift", 16, "bold"),
              command=lambda: [setattr(sys.modules[__name__], 'game_mode', 'normal'), start_game()])
start_solo_btn.grid(row=0, column=0, padx=5, pady=5)

ctk.CTkButton(mode_frame, text="📅 Daily Challenge", width=180, height=45,
              fg_color="#0EA5E9", command=start_daily).grid(row=0, column=1, padx=5, pady=5)

ctk.CTkButton(mode_frame, text="👥 Multiplayer", width=180, height=45,
              fg_color="#10B981", command=start_multiplayer).grid(row=1, column=0, padx=5, pady=5)

ctk.CTkButton(mode_frame, text="🤖 Vs Bot", width=180, height=45,
              fg_color="#F59E0B", command=start_vsbot).grid(row=1, column=1, padx=5, pady=5)

ctk.CTkButton(mode_frame, text="🎯 Custom Range", width=180, height=45,
              fg_color="#8B5CF6", command=start_custom_range).grid(row=2, column=0, padx=5, pady=5)

ctk.CTkButton(mode_frame, text="🏆 Leaderboard", width=180, height=45,
              fg_color="#EC4899", command=show_leaderboard).grid(row=2, column=1, padx=5, pady=5)

bottom_frame = ctk.CTkFrame(start_frame, fg_color="transparent")
bottom_frame.pack(pady=10)

theme_menu = ctk.CTkOptionMenu(bottom_frame, values=list(THEMES.keys()),
                               command=apply_theme, width=150)
theme_menu.set(stats["theme"])
theme_menu.grid(row=0, column=0, padx=10)

music_btn = ctk.CTkButton(bottom_frame, text="🎵 Music: OFF", width=150, command=toggle_music)
music_btn.grid(row=0, column=1, padx=10)

# ================= GAME PAGE =================
game_frame = ctk.CTkFrame(root, fg_color="transparent", width=1000, height=700)
add_exit_button(game_frame)

game_title = ctk.CTkLabel(game_frame, text="🎮 GUESS THE NUMBER",
                          font=("Bahnschrift", 30, "bold"), text_color=CYAN)
game_title.pack(pady=15)

turn_label = ctk.CTkLabel(game_frame, text="", font=("Consolas", 18, "bold"), text_color=PINK)
bot_label = ctk.CTkLabel(game_frame, text="", font=("Consolas", 16), text_color=ORANGE)

instruction = ctk.CTkLabel(game_frame, text=f"Enter a number between {min_number} and {min_number+max_number-1}",
                           font=("Consolas", 18), text_color=WHITE)
instruction.pack()

guess_entry = ctk.CTkEntry(game_frame, width=250, height=45, font=("Consolas", 18), justify="center")
guess_entry.pack(pady=10)

btn_frame = ctk.CTkFrame(game_frame, fg_color="transparent")
btn_frame.pack()

check_btn = ctk.CTkButton(btn_frame, text="CHECK GUESS", width=160, height=50,
                          fg_color=PURPLE, hover_color=PURPLE_HOVER,
                          font=("Bahnschrift", 18, "bold"), command=check_guess)
check_btn.grid(row=0, column=0, padx=5)

hint_btn = ctk.CTkButton(btn_frame, text=f"💡 HINT ({max_hints})", width=160, height=50,
                         fg_color="#F59E0B", hover_color="#D97706",
                         font=("Bahnschrift", 16, "bold"), command=use_hint)
hint_btn.grid(row=0, column=1, padx=5)

shop_frame = ctk.CTkFrame(game_frame, fg_color="transparent")
shop_frame.pack(pady=10)

points_shop_label = ctk.CTkLabel(shop_frame, text=f"💰 Points: {stats['points']}",
                                 font=("Consolas", 16, "bold"), text_color=GOLD)
points_shop_label.grid(row=0, columnspan=3, pady=5)

ctk.CTkButton(shop_frame, text="🔍 Reveal Range\n50pts", width=140, height=40,
              command=use_reveal_range).grid(row=1, column=0, padx=3)
ctk.CTkButton(shop_frame, text="⚡ Double Points\n100pts", width=140, height=40,
              command=use_double_points).grid(row=1, column=1, padx=3)
ctk.CTkButton(shop_frame, text="⏭ Skip Turn\n30pts", width=140, height=40,
              command=use_skip_turn).grid(row=1, column=2, padx=3)

attempt_label = ctk.CTkLabel(game_frame, text="Attempts: 0",
                             font=("Consolas", 18, "bold"), text_color=GREEN)
attempt_label.pack(pady=8)

result_label = ctk.CTkLabel(game_frame, text="Waiting for your guess...",
                            font=("Bahnschrift", 18), text_color=CYAN)
result_label.pack(pady=5)

history_box = ctk.CTkLabel(game_frame, text="📜 Last Guesses:\n",
                           font=("Consolas", 14), text_color=PINK, justify="left")
history_box.pack(pady=10)

tip_box = ctk.CTkLabel(game_frame, text="💡 PRO TIP\n\nStart around the middle.\nKeep halving the range!",
                       font=("Consolas", 15), text_color=PINK)
tip_box.pack(pady=10)

# ================= RESULT PAGE =================
result_frame = ctk.CTkFrame(root, fg_color="transparent", width=1000, height=700)
add_exit_button(result_frame)

result_title = ctk.CTkLabel(result_frame, text="🏆 RESULTS DASHBOARD",
                            font=("Bahnschrift", 32, "bold"), text_color=CYAN)
result_title.pack(pady=15)

winner_label = ctk.CTkLabel(result_frame, text="", font=("Bahnschrift", 22, "bold"), text_color=GOLD)
winner_label.pack()

score_label = ctk.CTkLabel(result_frame, text="", font=("Bahnschrift", 24, "bold"), text_color=GREEN)
score_label.pack(pady=5)

points_label = ctk.CTkLabel(result_frame, text="", font=("Consolas", 18, "bold"), text_color=GOLD)
points_label.pack()

time_label = ctk.CTkLabel(result_frame, text="", font=("Consolas", 18), text_color=WHITE)
time_label.pack()

attempts_result = ctk.CTkLabel(result_frame, text="", font=("Consolas", 18), text_color=WHITE)
attempts_result.pack()

streak_label = ctk.CTkLabel(result_frame, text="", font=("Consolas", 18), text_color=PINK)
streak_label.pack()

best_streak_label = ctk.CTkLabel(result_frame, text="", font=("Consolas", 18), text_color=PINK)
best_streak_label.pack()

rank_label = ctk.CTkLabel(result_frame, text="", font=("Bahnschrift", 22, "bold"), text_color=CYAN)
rank_label.pack(pady=8)

tip_label = ctk.CTkLabel(result_frame, text="", font=("Consolas", 15),
                         text_color=GREEN, justify="center")
tip_label.pack(pady=8)

stats_label = ctk.CTkLabel(result_frame, text="", font=("Consolas", 13),
                           text_color=WHITE, justify="center")
stats_label.pack(pady=8)

buttons_frame = ctk.CTkFrame(result_frame, fg_color="transparent")
buttons_frame.pack(pady=12)

play_again_btn = ctk.CTkButton(buttons_frame, text="🔄 PLAY AGAIN", width=160, height=45,
                               fg_color=PURPLE, hover_color=PURPLE_HOVER,
                               font=("Bahnschrift", 15, "bold"), command=start_game)
play_again_btn.grid(row=0, column=0, padx=8)

menu_btn = ctk.CTkButton
menu_btn = ctk.CTkButton(buttons_frame, text="🏠 MAIN MENU", width=160, height=45,
                         fg_color="#0EA5E9", font=("Bahnschrift", 15, "bold"),
                         command=lambda: show_frame(start_frame))
menu_btn.grid(row=0, column=1, padx=8)

exit_btn = ctk.CTkButton(buttons_frame, text="❌ EXIT", width=160, height=45,
                         fg_color="#E11D48", hover_color="#BE123C",
                         font=("Bahnschrift", 15, "bold"), command=exit_game)
exit_btn.grid(row=0, column=2, padx=8)

# ================= KEY BINDING =================
root.bind("<Return>", lambda event: check_guess())

# ================= START =================
animate_background()
apply_theme(stats["theme"])
show_frame(start_frame)
root.mainloop()
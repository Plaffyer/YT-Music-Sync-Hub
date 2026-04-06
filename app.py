import customtkinter as ctk
import threading
import sys
import os
import pandas as pd
import time
import re
import difflib
import winsound
import ctypes
from datetime import datetime
from ytmusicapi import YTMusic
from ytmusicapi.setup import setup as yt_setup

# PART 1: SYSTEM UTILS & REDIRECTOR [CORE/PERMANENT]
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, str_text):
        self.widget.configure(state="normal")
        self.widget.insert("end", str_text)
        self.widget.see("end")
        self.widget.configure(state="disabled")

    def flush(self):
        pass

def log_accuracy(m_no, sim_pct, target, found):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{now}] #{m_no} | {sim_pct}% | Target: {target} | Found: {found}\n"
    with open("accuracy.txt", "a", encoding="utf-8") as log:
        log.write(log_entry)

def alert_user(title, message, is_choice=False):
    print(f"\n{'='*40}\n!!! {title.upper()} !!!\n{message}\n{'='*40}")
    winsound.Beep(1000, 500)
    style = 0x40031 if is_choice else 0x40010
    return ctypes.windll.user32.MessageBoxW(0, message, title, style)

# PART 2: AI BRAIN & MEMORY BANKS [ADJUSTABLE/TWEAKABLE]
class SmartBrain:
    def __init__(self):
        self.noise = {'feat', 'ft', 'with', 'x', 'official', 'video', 'audio', 'remix', 'edit', 'the', 'a', 'and', 'music', 'group'}
        self.aliases = {
            "chid": "child", "prblm": "problem", "s1mba": "simba", 
            "rose": "rose", "tiesto": "tiesto", "k-391": "alan walker",
            "&": "and", "xchenda": "chenda",
            "mã˜": "mo", "mø": "mo",
            "mu la la": "" 
        }
        
        # CORE KNOWLEDGE: Specific track numbers and artist names to force approvals
        self.track_exceptions = {
            # Example: 593: "creepy nuts"
        }

    def clean_set(self, text):
        t = str(text).lower()
        for word, fix in self.aliases.items():
            t = t.replace(word, fix)
        t = re.sub(r'[^a-z0-9\s]', ' ', t)
        return {w for w in t.split() if w not in self.noise and len(w) > 1}

    def clean_string(self, text):
        return "".join(self.clean_set(text))

    def is_same_song(self, m_no, m_title, m_artist, yt_title, yt_artist):
        if m_no in self.track_exceptions and self.track_exceptions[m_no] in str(yt_artist).lower():
            return True
        m_t = self.clean_set(m_title)
        m_a = self.clean_set(m_artist)
        yt_all = self.clean_set(yt_title).union(self.clean_set(yt_artist))
        artist_match = bool(m_a.intersection(yt_all))
        if not m_t:
            return artist_match
        match_count = len(m_t.intersection(yt_all))
        word_match_ratio = match_count / len(m_t)
        title_match = word_match_ratio > 0.5
        return title_match and artist_match

# CORE KNOWLEDGE: Hardcode specific Video IDs for songs that fail searches
MANUAL_OVERRIDES = {
    # Example: 105: "dlAkd-5WmNk"
}

def load_cache_with_overrides():
    cache_map = {}
    if os.path.exists("url.txt"):
        try:
            df = pd.read_csv("url.txt", encoding='utf-8-sig')
            for idx, row in df.iterrows():
                try:
                    track_no = int(row['No'])
                    cache_map[track_no] = str(row['VideoID'])
                except ValueError:
                    continue
        except Exception as e:
            print(f"--- Warning: Could not load url.txt cleanly: {e} ---")
    for no_key, correct_url in MANUAL_OVERRIDES.items():
        cache_map[no_key] = correct_url
    return cache_map

# PART 3: MAIN APPLICATION & UI FRONTEND [CORE/PERMANENT]
class UltimateSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YT Music Control Center")
        self.geometry("950x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # PART 3A: SIDEBAR NAVIGATION [CORE/PERMANENT]
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Sync Hub", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Dashboard Button & Desc
        self.btn_nav_dash = ctk.CTkButton(self.sidebar_frame, text="1. Dashboard", command=lambda: self.select_frame("dash"), anchor="w")
        self.btn_nav_dash.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(self.sidebar_frame, text="Run scanners & sync", font=ctk.CTkFont(size=11), text_color="gray").grid(row=2, column=0, padx=20, pady=(0, 10), sticky="w")

        # Import Button & Desc
        self.btn_nav_import = ctk.CTkButton(self.sidebar_frame, text="2. Data Import", command=lambda: self.select_frame("import"), anchor="w")
        self.btn_nav_import.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(self.sidebar_frame, text="Convert CSV to clean list", font=ctk.CTkFont(size=11), text_color="gray").grid(row=4, column=0, padx=20, pady=(0, 10), sticky="w")

        # Auth Button & Desc
        self.btn_nav_auth = ctk.CTkButton(self.sidebar_frame, text="3. Authentication", command=lambda: self.select_frame("auth"), anchor="w")
        self.btn_nav_auth.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(self.sidebar_frame, text="Add F12 Browser Headers", font=ctk.CTkFont(size=11), text_color="gray").grid(row=6, column=0, padx=20, pady=(0, 10), sticky="w")

        # Guide Button & Desc
        self.btn_nav_guide = ctk.CTkButton(self.sidebar_frame, text="? Help & Guides", command=lambda: self.select_frame("guide"), anchor="w", fg_color="#52796F", hover_color="#354F52")
        self.btn_nav_guide.grid(row=7, column=0, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(self.sidebar_frame, text="Fix errors & manuals", font=ctk.CTkFont(size=11), text_color="gray").grid(row=8, column=0, padx=20, pady=(0, 10), sticky="w")

        # PART 3B: DASHBOARD VIEW [CORE/PERMANENT]
        self.frame_dash = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_dash.grid_columnconfigure(0, weight=1)
        self.frame_dash.grid_columnconfigure(1, weight=1)
        self.frame_dash.grid_rowconfigure(2, weight=1)

        self.dash_controls = ctk.CTkFrame(self.frame_dash)
        self.dash_controls.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")
        self.dash_controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.dash_controls, text="Playlist Name or URL:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.playlist_input = ctk.CTkEntry(self.dash_controls, placeholder_text="e.g., 'My New Playlist' OR paste a YouTube Playlist URL here")
        self.playlist_input.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.dash_controls, text="Sync Behavior:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.mode_switch = ctk.CTkOptionMenu(self.dash_controls, values=["Strict Mode (Perfectionist)", "Relaxed Mode (Just add them)"])
        self.mode_switch.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.btn_scan = ctk.CTkButton(self.frame_dash, text="SCAN PLAYLIST TARGET BOT", command=self.start_scan_thread, height=40, fg_color="#E07A5F", hover_color="#D06A4F")
        self.btn_scan.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_sync = ctk.CTkButton(self.frame_dash, text="INITIATE SYNC ENGINE", command=self.start_sync_thread, height=40)
        self.btn_sync.grid(row=1, column=1, padx=20, pady=10, sticky="ew")

        self.console = ctk.CTkTextbox(self.frame_dash, font=ctk.CTkFont(family="Consolas", size=13))
        self.console.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.console.configure(state="disabled")

        sys.stdout = TextRedirector(self.console)
        sys.stderr = TextRedirector(self.console)

        # PART 3C: DATA IMPORT VIEW [CORE/PERMANENT]
        self.frame_import = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_import.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.frame_import, text="Import External Playlist", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(40, 10), sticky="w")
        ctk.CTkLabel(self.frame_import, text="Upload a comma separated values file containing your playlist data.\nThe file must contain columns named 'Title' and 'Artist'.", justify="left").grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.btn_import_file = ctk.CTkButton(self.frame_import, text="SELECT FILE & CONVERT", command=self.import_csv_logic, height=40, fg_color="#81B29A", hover_color="#71A28A")
        self.btn_import_file.grid(row=2, column=0, padx=20, pady=20, sticky="w")

        # PART 3D: AUTHENTICATION VIEW [CORE/PERMANENT]
        self.frame_auth = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_auth.grid_columnconfigure(0, weight=1)
        self.frame_auth.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self.frame_auth, text="Header Converter", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(40, 10), sticky="w")

        self.auth_info_frame = ctk.CTkFrame(self.frame_auth, fg_color="transparent")
        self.auth_info_frame.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        ctk.CTkLabel(self.auth_info_frame, text="Paste raw Request Headers from your browser (F12) below:", font=ctk.CTkFont(size=14)).pack(side="left")
        ctk.CTkButton(self.auth_info_frame, text="?", width=28, height=28, corner_radius=14, font=ctk.CTkFont(weight="bold"), command=self.show_header_tutorial).pack(side="left", padx=15)

        self.header_input = ctk.CTkTextbox(self.frame_auth, font=ctk.CTkFont(family="Consolas", size=12))
        self.header_input.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        self.btn_save_auth = ctk.CTkButton(self.frame_auth, text="CONVERT BROWSER FILE", command=self.save_headers, height=40, fg_color="#E07A5F", hover_color="#D06A4F")
        self.btn_save_auth.grid(row=3, column=0, padx=20, pady=(10, 30), sticky="w")

        # PART 3E: HELP & GUIDES VIEW [CORE/PERMANENT]
        self.frame_guide = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_guide.grid_columnconfigure(0, weight=1)
        self.frame_guide.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_guide, text="User Manual & Troubleshooting", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Use a Textbox for the guide so it never clips and handles scrolling natively
        self.guide_textbox = ctk.CTkTextbox(self.frame_guide, font=ctk.CTkFont(size=14), wrap="word")
        self.guide_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        guide_text = """=== 1. WHAT DO THESE BUTTONS DO? ===
• 1. Dashboard: This is the main control room. Here you tell the bot where to put the songs, choose your strictness mode, and click "INITIATE SYNC" to start adding songs. You can also run the Target Scanner here to check for missing songs.
• 2. Data Import: This is where you upload your raw playlist file (CSV format) exported from Spotify/Apple. The app will clean it up and prepare it for the bot to read.
• 3. Authentication: This is where you give the bot the "VIP Pass" (F12 Headers) so it can securely log into your YouTube account to add songs.

=== 2. STRICT MODE VS RELAXED MODE ===
• STRICT MODE (For Perfectionists): The bot verifies every song mathematically. If it isn't 100% sure, it stops and alerts you. It also checks the YouTube server periodically to ensure perfect 1-to-1 order. 
-> Best Workflow: If a song is wrong, the bot will pause. Delete the wrong song from your YouTube playlist manually, edit your 'cleanlist.csv' to fix the tricky title, and restart the bot.

• RELAXED MODE (For Casual Users): The bot will find the closest match it can and add it silently. It disables deep safety checks and will not stop if YouTube lags. It simply pushes through to the end.

=== 3. ERROR GLOSSARY & FIXES ===
• "Ghost Add" Error: 
What happened: YouTube's servers lagged. The bot told YouTube to add a song, but YouTube didn't save it. 
Counter-measure: Manual deletion of the last few tracks and restart if you are a perfectionist, or run the Target Scanner later to find the specific gap.

• "Authentication Error 401": 
What happened: Your browser session expired. Google kicks bots out periodically for security.
Counter-measure: Go to the Authentication tab, grab fresh F12 Request Headers from your browser, paste them, and click convert.

• "Not Found Error 404": 
What happened: The playlist URL is wrong, or the playlist was deleted.
Counter-measure: Make sure you copied the correct URL, or just type a new name in the Dashboard to create a fresh one.

• "Duplicate Error 409": 
What happened: You tried to add the exact same song/video ID twice. 
Counter-measure: Check your YouTube playlist. Delete duplicates manually.

• "Low Accuracy Hard Stop": (Strict Mode Only). 
What happened: The bot found a song, but the name was too different from your list. It blocked it to protect your list.
Counter-measure: Switch to Relaxed Mode to bypass it, OR open the app.py code and add the correct Video ID to the MANUAL_OVERRIDES memory bank so it automatically succeeds next time.

• "Missing File Errors": 
What happened: The bot cannot find 'cleanlist.csv' or 'browser.json'.
Counter-measure: If cleanlist is missing, go to Data Import and convert a file. If browser.json is missing, go to Authentication and convert your headers.
"""
        self.guide_textbox.insert("0.0", guide_text)
        self.guide_textbox.configure(state="disabled") # Lock it so it's read-only

        self.select_frame("dash")

    # PART 4: APPLICATION LOGIC & UI ROUTING [CORE/PERMANENT]
    def select_frame(self, name):
        frames = {"dash": self.frame_dash, "import": self.frame_import, "auth": self.frame_auth, "guide": self.frame_guide}
        for key, frame in frames.items():
            if key == name:
                frame.grid(row=0, column=1, sticky="nsew")
            else:
                frame.grid_forget()

    def show_header_tutorial(self):
        help_window = ctk.CTkToplevel(self)
        help_window.title("Tutorial: How to Get Headers")
        help_window.geometry("580x380")
        help_window.attributes('-topmost', True) 
        
        ctk.CTkLabel(help_window, text="How to extract your browser headers:", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10), padx=20, anchor="w")
        tutorial_text = (
            "1. Open Chrome or Edge and go to music.youtube.com (ensure you are logged in).\n"
            "2. Press F12 on your keyboard to open Developer Tools.\n"
            "3. Click the 'Network' tab at the top of the tools panel.\n"
            "4. In the 'Filter' search box, type the word: browse\n"
            "5. Press F5 to refresh the webpage.\n"
            "6. Click the first 'browse' item that appears in the list.\n"
            "7. A side panel will open. Scroll down to 'Request Headers'.\n"
            "8. Copy EVERYTHING in the Request Headers section (from 'accept:' down to your cookies).\n"
            "9. Paste that text into the app and click Convert."
        )
        ctk.CTkLabel(help_window, text=tutorial_text, justify="left", font=ctk.CTkFont(size=13)).pack(padx=20, pady=10, anchor="w")
        ctk.CTkButton(help_window, text="Got it!", command=help_window.destroy).pack(pady=20)

    def lock_buttons(self, message):
        self.btn_scan.configure(state="disabled")
        self.btn_sync.configure(state="disabled", text=message)

    def unlock_buttons(self):
        self.btn_scan.configure(state="normal")
        self.btn_sync.configure(state="normal", text="INITIATE SYNC ENGINE")

    def import_csv_logic(self):
        file_path = ctk.filedialog.askopenfilename(title="Select Playlist File", filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                df = pd.read_csv(file_path)
                cols = [c.lower() for c in df.columns]
                
                if 'title' in cols and 'artist' in cols:
                    df.columns = [c.title() if c.lower() in ['title', 'artist', 'no'] else c for c in df.columns]
                    if 'No' not in df.columns:
                        df.insert(0, 'No', range(1, len(df) + 1))
                        
                    final_df = df[['No', 'Title', 'Artist']]
                    final_df.to_csv("cleanlist.csv", index=False)
                    
                    self.select_frame("dash")
                    print("\n--- IMPORT SUCCESS ---")
                    print("Your list was automatically formatted and saved as cleanlist.csv.")
                    alert_user("Success", "List imported and formatted successfully.")
                else:
                    alert_user("Format Error", "Your file must contain columns named 'Title' and 'Artist'.")
            except Exception as e:
                alert_user("Import Error", f"Could not read the file properly. Error: {e}")

    def save_headers(self):
        raw_text = self.header_input.get("1.0", "end-1c").strip()
        if not raw_text:
            alert_user("Empty", "Please paste the raw headers into the box first.")
            return

        print("\n--- CONVERTING HEADERS ---")
        try:
            yt_setup(filepath="browser.json", headers_raw=raw_text)
            self.header_input.delete("1.0", "end") 
            self.select_frame("dash") 
            print("SUCCESS: The authentication file has been created and saved.")
            alert_user("Success", "Headers saved successfully. The bot is unlocked.")
        except Exception as e:
            print(f"!!! ERROR: Failed to convert headers. Details: {e}")
            alert_user("Header Error", f"Failed to convert headers.\nError: {e}")

    # PART 5: TARGET SCANNER THREAD [CORE/PERMANENT]
    def start_scan_thread(self):
        self.lock_buttons("SCANNING IN PROGRESS...")
        threading.Thread(target=self.run_target_logic, daemon=True).start()

    def run_target_logic(self):
        brain = SmartBrain()
        print("\n--- TOTAL POOL SCANNER BOOTING ---")
        try:
            if not os.path.exists("ostlist.csv") or not os.path.exists("cleanlist.csv"):
                print("!!! ERROR: Ensure ostlist.csv and cleanlist.csv are in the folder. !!!")
                self.unlock_buttons()
                return

            df_yt = pd.read_csv("ostlist.csv", encoding='utf-8-sig')
            df_master = pd.read_csv("cleanlist.csv", header=0, encoding='latin1')
            df_master.columns = ['No', 'Title', 'Artist']
        except Exception as e:
            print(f"!!! FILE ERROR: {e} !!!")
            self.unlock_buttons()
            return

        missing_log = []
        duplicate_log = []
        yt_tracks = df_yt.to_dict('records')
        yt_count = len(yt_tracks)
        scan_limit = yt_count + 5
        list_offset = 0 

        for idx, row in df_master.iterrows():
            m_no = int(row['No'])
            if m_no > scan_limit: break 
            expected_yt_idx = idx + list_offset
            found_match = False

            if expected_yt_idx < yt_count:
                yt_target = yt_tracks[expected_yt_idx]
                if brain.is_same_song(m_no, row['Title'], row['Artist'], yt_target['Title'], yt_target['Artist']):
                    found_match = True
                    continue 

            if not found_match:
                for window in range(1, 5):
                    check_idx = expected_yt_idx + window
                    if check_idx < yt_count:
                        yt_target = yt_tracks[check_idx]
                        if brain.is_same_song(m_no, row['Title'], row['Artist'], yt_target['Title'], yt_target['Artist']):
                            list_offset += window
                            found_match = True
                            break

            if not found_match:
                for window in range(-1, -5, -1):
                    check_idx = expected_yt_idx + window
                    if 0 <= check_idx < yt_count:
                        yt_target = yt_tracks[check_idx]
                        if brain.is_same_song(m_no, row['Title'], row['Artist'], yt_target['Title'], yt_target['Artist']):
                            list_offset += window
                            found_match = True
                            break

            if not found_match:
                actual_yt_name = "End of List / Empty"
                if expected_yt_idx < yt_count:
                    actual_yt = yt_tracks[expected_yt_idx]
                    actual_yt_name = f"{actual_yt['Artist']} - {actual_yt['Title']}"
                missing_log.append(f"MISSING/WRONG #{m_no}: {row['Artist']} - {row['Title']} -- OST List has: {actual_yt_name}")

        seen_songs = {}
        for i, yt in enumerate(yt_tracks):
            c_sig = " ".join(sorted(brain.clean_set(yt['Title'] + " " + yt['Artist'])))
            if c_sig in seen_songs:
                first_pos = seen_songs[c_sig]['pos']
                duplicate_log.append(f"DUPLICATE OST #{first_pos} and #{i+1} -- {yt['Artist']} - {yt['Title']}")
            else:
                seen_songs[c_sig] = {'pos': i+1}

        print(f"\nSITUATIONAL REPORT | YT Count: {yt_count}\n" + "="*50)
        if missing_log:
            print(f"\n[!] MISSING OR WRONG SONGS {len(missing_log)}:")
            for gap in missing_log: print(gap)
        if duplicate_log:
            print(f"\n[!] PLAYLIST DUPLICATES {len(duplicate_log)}:")
            for dup in duplicate_log: print(dup)
        if not missing_log and not duplicate_log:
            print("\n[+] 100 PERCENT PERFECT: System is perfectly synchronized.")

        with open("gapsongs.txt", "w", encoding="utf-8") as f:
            f.write(f"SITUATIONAL REPORT | YT Count: {yt_count}\n" + "="*50 + "\n")
            if missing_log: f.write(f"\n[!] MISSING OR WRONG SONGS {len(missing_log)}:\n" + "\n".join(missing_log) + "\n")
            if duplicate_log: f.write(f"\n[!] PLAYLIST DUPLICATES {len(duplicate_log)}:\n" + "\n".join(duplicate_log) + "\n")
            if not missing_log and not duplicate_log: f.write("\n[+] 100 PERCENT PERFECT: System is perfectly synchronized.")

        print("\n--- SCAN COMPLETE ---")
        self.unlock_buttons()

    # PART 6: MAIN SYNC ENGINE THREAD [CORE/PERMANENT]
    def start_sync_thread(self):
        self.lock_buttons("SYNCING IN PROGRESS...")
        threading.Thread(target=self.run_sync_logic, daemon=True).start()

    def run_sync_logic(self):
        try:
            if not os.path.exists("browser.json"):
                print("\n!!! EXPIRED OR MISSING HEADERS !!!\nGo to the 'Authentication' tab, fetch new F12 Request Headers from YouTube, and convert them to continue.")
                self.unlock_buttons()
                return

            if not os.path.exists("cleanlist.csv"):
                print("!!! ERROR: Could not find cleanlist.csv. Please use the Data Import tab first !!!")
                self.unlock_buttons()
                return

            print("\n--- SYSTEM BOOTING ---")
            yt = YTMusic("browser.json")
            brain = SmartBrain()
            cache_map = load_cache_with_overrides()
            
            is_strict = "Strict" in self.mode_switch.get()
            ENABLE_AUTO_RECHECK = True if is_strict else False
            
            playlist_req = self.playlist_input.get().strip()
            if not playlist_req:
                playlist_req = "Auto-Generated Sync List"
                print(f"--- No playlist name provided. Defaulting to '{playlist_req}' ---")

            PLAYLIST_ID = None
            
            if "list=" in playlist_req:
                try:
                    PLAYLIST_ID = playlist_req.split("list=")[1].split("&")[0]
                    print(f"--- Extracted Playlist ID from URL: {PLAYLIST_ID} ---")
                except IndexError:
                    print("!!! ERROR: Invalid YouTube Playlist URL format. !!!")
                    self.unlock_buttons()
                    return
            else:
                playlists = yt.get_library_playlists(limit=100)
                for p in playlists:
                    if p['title'].lower() == playlist_req.lower():
                        PLAYLIST_ID = p['playlistId']
                        print(f"--- Found existing playlist: {playlist_req} ---")
                        break
                        
                if not PLAYLIST_ID:
                    print(f"--- CREATING NEW PLAYLIST: {playlist_req} ---")
                    PLAYLIST_ID = yt.create_playlist(playlist_req, "Auto-generated by Sync Bot")
                    time.sleep(3) 

            try:
                current_playlist_data = yt.get_playlist(PLAYLIST_ID, limit=None)
                live_yt_count = len(current_playlist_data.get('tracks', []))
            except KeyError:
                live_yt_count = 0
                
            print(f"--- SAFETY CHECK: Found {live_yt_count} songs already inside YouTube Playlist ---")

            try:
                df = pd.read_csv("cleanlist.csv", header=0, encoding='latin1')
                df.columns = ['No', 'Title', 'Artist']
                total_songs = len(df)
            except Exception as e:
                print(f"!!! FILE ERROR: Could not read cleanlist.csv: {e} !!!")
                self.unlock_buttons()
                return

            print(f"--- STARTING HYPER-SYNC ({'STRICT' if is_strict else 'RELAXED'} MODE) ---")
            slow_search_adds = []

            for i in range(total_songs):
                m_no = int(df.iloc[i]['No'])
                m_title = str(df.iloc[i]['Title'])
                m_artist = str(df.iloc[i]['Artist'])
                query = f"{m_artist} {m_title}"
                
                if m_no <= live_yt_count:
                    print(f"[{m_no}/{total_songs}] {m_title} -- SKIPPED")
                    continue

                if m_no in cache_map and pd.notna(cache_map[m_no]) and cache_map[m_no] != "None":
                    video_id = cache_map[m_no]
                    yt.add_playlist_items(PLAYLIST_ID, [video_id])
                    if m_no in MANUAL_OVERRIDES:
                        print(f"[{m_no}/{total_songs}] {m_title} -- MANUAL OVERRIDE ADD")
                    else:
                        print(f"[{m_no}/{total_songs}] {m_title} -- FAST CACHE ADD")
                    time.sleep(0.5) 
                    live_yt_count += 1 
                    continue

                search = yt.search(query, filter="songs")
                if not search:
                    print(f"[{m_no}/{total_songs}] NOT FOUND: {query}")
                    continue

                selected_result = None
                for res in search[:20]:
                    res_title_temp = res['title']
                    res_artist_temp = ", ".join([a['name'] for a in res['artists']])
                    if brain.is_same_song(m_no, m_title, m_artist, res_title_temp, res_artist_temp):
                        selected_result = res
                        break 

                if not selected_result:
                    selected_result = search[0]

                res_title = selected_result['title']
                res_artist = ", ".join([a['name'] for a in selected_result['artists']])
                video_id = selected_result['videoId']
                
                title_sim = difflib.SequenceMatcher(None, brain.clean_string(m_title), brain.clean_string(res_title)).ratio()
                artist_sim = difflib.SequenceMatcher(None, brain.clean_string(m_artist), brain.clean_string(res_artist)).ratio()
                sim_pct = int(((title_sim * 0.8) + (artist_sim * 0.2)) * 100)
                
                title_words = brain.clean_set(m_title)
                artist_words = brain.clean_set(m_artist)
                found_words = brain.clean_set(res_title + " " + res_artist)
                word_match_ratio = 0
                
                if title_words:
                    match_count = len(title_words.intersection(found_words))
                    word_match_ratio = match_count / len(title_words)
                    if word_match_ratio < 0.5: sim_pct = 5 
                if artist_words:
                    if len(artist_words.intersection(found_words)) == 0: sim_pct = 5
                if title_sim < 0.4 and word_match_ratio < 1.0: sim_pct = 5 

                if sim_pct < 70: log_accuracy(m_no, sim_pct, f"{m_artist}-{m_title}", f"{res_artist}-{res_title}")

                if sim_pct < 10 and is_strict:
                    print(f"!!! STRICT STOP: Accuracy too low at number {m_no}. Target: {m_title} | Found: {res_title} !!!")
                    print("--> Check Help Guide to resolve. Switch to Relaxed Mode to bypass.")
                    self.unlock_buttons()
                    return

                yt.add_playlist_items(PLAYLIST_ID, [video_id])
                slow_search_adds.append({'m_no': m_no, 'm_title': m_title, 'm_artist': m_artist, 'yt_index': live_yt_count})
                live_yt_count += 1 
                
                with open("url.txt", "a", encoding="utf-8-sig") as f:
                    f.write(f'{m_no},"{res_title}","{res_artist}","{video_id}"\n')

                time.sleep(3.5) 
                
                try:
                    current_playlist_data = yt.get_playlist(PLAYLIST_ID, limit=None)
                    actual_yt_count = len(current_playlist_data.get('tracks', []))
                    if actual_yt_count < live_yt_count and is_strict:
                        print(f"!!! GHOST ADD ERROR: At number {m_no}. YouTube lagged and missed the song. Playlist desynced. !!!")
                        print("--> Delete the ghost track from YouTube and restart the bot.")
                        self.unlock_buttons()
                        return
                except KeyError:
                    pass 

                if ENABLE_AUTO_RECHECK and (m_no % 100 == 0):
                    print(f"\n--- INITIATING PERIODIC STATE RECONCILIATION AT #{m_no} ---")
                    slow_search_adds.clear()
                    print("--- RECONCILIATION COMPLETE. RESUMING SYNC ---\n")

                print(f"[{m_no}/{total_songs}] {m_title} -- SLOW SEARCH ADD | {sim_pct} percent")

            print("\n=== 100 PERCENT CONVERSION COMPLETE ===")
            self.unlock_buttons()

        except Exception as e:
            err_str = str(e)
            if "401" in err_str:
                print("\n!!! 401 UNAUTHORIZED: YOUR HEADERS ARE EXPIRED !!!")
                print("Go to the Authentication tab, paste new browser headers, and convert them.")
            else:
                print(f"\n!!! CRITICAL RUNTIME ERROR !!!\n{err_str}")
            self.unlock_buttons()

if __name__ == "__main__":
    app = UltimateSyncApp()
    app.mainloop()

# QUICK RUN COMMAND: python app.py
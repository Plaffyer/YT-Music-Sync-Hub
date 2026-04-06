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
        self.track_exceptions = {
            452: "mikeeysmind",
            533: "slushii",
            593: "creepy nuts",
            628: "civ",
            655: "huntr/x"
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

MANUAL_OVERRIDES = {
    105: "dlAkd-5WmNk", 121: "M9KQbrwi7WY", 219: "INo4WtusH10", 233: "9cT-v9NxRsA", 
    238: "3Jgso_CkHxw", 279: "GbM2A6HXnMQ", 302: "fTL3sAxt7-8", 359: "qA6Z41612PU",
    370: "jCZXvdu3gtE", 420: "4Vz3Xzq6-nU", 509: "DbTSPATbcUc", 561: "uNLlckry2vY",
    593: "W0dsUNS4RT8", 599: "6-GspWPOa1U", 616: "z9E3zRjQB_g", 617: "tthafU1Ao40",
    658: "vSU1wdh-TDg"
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

        # PART 3A: SIDEBAR NAVIGATION
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Sync Hub", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_nav_dash = ctk.CTkButton(self.sidebar_frame, text="1. Dashboard", command=lambda: self.select_frame("dash"), anchor="w")
        self.btn_nav_dash.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(self.sidebar_frame, text="Run scanners & sync", font=ctk.CTkFont(size=11), text_color="gray").grid(row=2, column=0, padx=20, pady=(0, 10), sticky="w")

        self.btn_nav_import = ctk.CTkButton(self.sidebar_frame, text="2. Data Import", command=lambda: self.select_frame("import"), anchor="w")
        self.btn_nav_import.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(self.sidebar_frame, text="Convert CSV to clean list", font=ctk.CTkFont(size=11), text_color="gray").grid(row=4, column=0, padx=20, pady=(0, 10), sticky="w")

        self.btn_nav_auth = ctk.CTkButton(self.sidebar_frame, text="3. Authentication", command=lambda: self.select_frame("auth"), anchor="w")
        self.btn_nav_auth.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(self.sidebar_frame, text="Add F12 Browser Headers", font=ctk.CTkFont(size=11), text_color="gray").grid(row=6, column=0, padx=20, pady=(0, 10), sticky="w")

        self.btn_nav_guide = ctk.CTkButton(self.sidebar_frame, text="? Help & Guides", command=lambda: self.select_frame("guide"), anchor="w", fg_color="#52796F", hover_color="#354F52")
        self.btn_nav_guide.grid(row=7, column=0, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(self.sidebar_frame, text="Fix errors & manuals", font=ctk.CTkFont(size=11), text_color="gray").grid(row=8, column=0, padx=20, pady=(0, 10), sticky="w")

        # PART 3B: DASHBOARD VIEW
        self.frame_dash = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_dash.grid_columnconfigure(0, weight=1)
        self.frame_dash.grid_columnconfigure(1, weight=1)
        self.frame_dash.grid_rowconfigure(3, weight=1)

        self.dash_controls = ctk.CTkFrame(self.frame_dash)
        self.dash_controls.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")
        self.dash_controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.dash_controls, text="Playlist Name or URL:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.playlist_input = ctk.CTkEntry(self.dash_controls, placeholder_text="e.g., 'OST All Songs' OR paste URL")
        self.playlist_input.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.dash_controls, text="Sync Behavior:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.mode_switch = ctk.CTkOptionMenu(self.dash_controls, values=["Strict Mode (Perfectionist)", "Relaxed Mode (Just add them)"])
        self.mode_switch.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.btn_scan = ctk.CTkButton(self.frame_dash, text="SCAN PLAYLIST TARGET BOT", command=self.start_scan_thread, height=40, fg_color="#E07A5F", hover_color="#D06A4F")
        self.btn_scan.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(self.frame_dash, text="Checks YouTube vs Local List for gaps/errors", font=ctk.CTkFont(size=11), text_color="gray").grid(row=2, column=0, padx=20, pady=(0, 10))

        self.btn_sync = ctk.CTkButton(self.frame_dash, text="INITIATE SYNC ENGINE", command=self.start_sync_thread, height=40)
        self.btn_sync.grid(row=1, column=1, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(self.frame_dash, text="Begins automated song migration to YouTube", font=ctk.CTkFont(size=11), text_color="gray").grid(row=2, column=1, padx=20, pady=(0, 10))

        self.console = ctk.CTkTextbox(self.frame_dash, font=ctk.CTkFont(family="Consolas", size=13))
        self.console.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.console.configure(state="disabled")

        sys.stdout = TextRedirector(self.console)
        sys.stderr = TextRedirector(self.console)

        # PART 3C: DATA IMPORT VIEW
        self.frame_import = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_import.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.frame_import, text="Import External Playlist", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(40, 10), sticky="w")
        ctk.CTkLabel(self.frame_import, text="Upload a CSV file containing your playlist data (Title & Artist columns required).", justify="left").grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.btn_import_file = ctk.CTkButton(self.frame_import, text="SELECT FILE & CONVERT", command=self.import_csv_logic, height=40, fg_color="#81B29A", hover_color="#71A28A")
        self.btn_import_file.grid(row=2, column=0, padx=20, pady=20, sticky="w")

        # PART 3D: AUTHENTICATION VIEW
        self.frame_auth = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_auth.grid_columnconfigure(0, weight=1)
        self.frame_auth.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self.frame_auth, text="Header Converter", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(40, 10), sticky="w")

        self.auth_info_frame = ctk.CTkFrame(self.frame_auth, fg_color="transparent")
        self.auth_info_frame.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        ctk.CTkLabel(self.auth_info_frame, text="Paste raw Request Headers from browser (F12) below:", font=ctk.CTkFont(size=14)).pack(side="left")
        ctk.CTkButton(self.auth_info_frame, text="?", width=28, height=28, corner_radius=14, font=ctk.CTkFont(weight="bold"), command=self.show_header_tutorial).pack(side="left", padx=15)

        self.header_input = ctk.CTkTextbox(self.frame_auth, font=ctk.CTkFont(family="Consolas", size=12))
        self.header_input.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        self.btn_save_auth = ctk.CTkButton(self.frame_auth, text="CONVERT BROWSER FILE", command=self.save_headers, height=40, fg_color="#E07A5F", hover_color="#D06A4F")
        self.btn_save_auth.grid(row=3, column=0, padx=20, pady=(10, 30), sticky="w")

        # PART 3E: HELP & GUIDES VIEW
        self.frame_guide = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_guide.grid_columnconfigure(0, weight=1)
        self.frame_guide.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_guide, text="User Manual & Troubleshooting", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.guide_textbox = ctk.CTkTextbox(self.frame_guide, font=ctk.CTkFont(size=14), wrap="word")
        self.guide_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        guide_text = """=== 1. INSTALLATION & SETUP ===
To run this application locally, you will need Python installed on your machine.

1. Download this repository.
2. Install the required dependencies:
pip install customtkinter ytmusicapi pandas
3. Run: python app.py

=== 2. HOW TO GET AUTHENTICATION HEADERS (DETAILED) ===
1. Open music.youtube.com (ensure you are logged in).
2. Press F12 -> Network tab.
3. Filter by: browse
4. Refresh (F5).
5. Click 'browse' -> Request Headers -> Copy everything.
6. Paste in Auth tab and click Convert.

=== 3. WHAT DO THESE BUTTONS DO? ===
• 1. Dashboard: Run scanners & sync.
• 2. Data Import: Convert CSV to clean list.
• 3. Authentication: Add F12 Browser Headers.

=== 4. STRICT MODE VS RELAXED MODE ===
• STRICT MODE: Mathematics-based verification. Stops on accuracy errors. Perfect for ensuring order.
• RELAXED MODE: Best guess matching. Fast and silent migration.

=== 5. ERROR GLOSSARY ===
• 401: Headers expired. Get new F12 headers.
• 409: Duplicate song detected.
• Ghost Add: YouTube server lag. Check Target Scanner for gaps.
"""
        self.guide_textbox.insert("0.0", guide_text)
        self.guide_textbox.configure(state="disabled") 

        self.select_frame("dash")

    def select_frame(self, name):
        frames = {"dash": self.frame_dash, "import": self.frame_import, "auth": self.frame_auth, "guide": self.frame_guide}
        for key, frame in frames.items():
            if key == name: frame.grid(row=0, column=1, sticky="nsew")
            else: frame.grid_forget()

    def show_header_tutorial(self):
        help_window = ctk.CTkToplevel(self)
        help_window.title("Tutorial: How to Get Headers")
        help_window.geometry("580x380")
        help_window.attributes('-topmost', True) 
        ctk.CTkLabel(help_window, text="How to extract your browser headers:", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10), padx=20, anchor="w")
        tutorial_text = (
            "1. Open Chrome or Edge -> music.youtube.com\n"
            "2. Press F12 -> Network tab.\n"
            "3. Filter search: browse\n"
            "4. Refresh page (F5).\n"
            "5. Click 'browse' -> Scroll to 'Request Headers'.\n"
            "6. Copy ALL text inside that section and paste in App."
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
                    if 'No' not in df.columns: df.insert(0, 'No', range(1, len(df) + 1))
                    final_df = df[['No', 'Title', 'Artist']]
                    final_df.to_csv("cleanlist.csv", index=False)
                    self.select_frame("dash")
                    alert_user("Success", "List imported successfully.")
                else: alert_user("Format Error", "CSV must contain 'Title' and 'Artist' columns.")
            except Exception as e: alert_user("Import Error", str(e))

    def save_headers(self):
        raw_text = self.header_input.get("1.0", "end-1c").strip()
        if not raw_text: return
        try:
            yt_setup(filepath="browser.json", headers_raw=raw_text)
            self.header_input.delete("1.0", "end") 
            self.select_frame("dash") 
            alert_user("Success", "Bot unlocked.")
        except Exception as e: alert_user("Header Error", str(e))

    def start_scan_thread(self):
        self.lock_buttons("SCANNING...")
        threading.Thread(target=self.run_target_logic, daemon=True).start()

    def run_target_logic(self):
        brain = SmartBrain()
        print("\n--- SCANNER BOOTING ---")
        try:
            if not os.path.exists("browser.json") or not os.path.exists("cleanlist.csv"):
                print("!!! ERROR: Missing browser.json or cleanlist.csv !!!")
                self.unlock_buttons()
                return
            yt = YTMusic("browser.json")
            p_req = self.playlist_input.get().strip() or "OST All Songs"
            PLAYLIST_ID = None
            if "list=" in p_req:
                try: PLAYLIST_ID = p_req.split("list=")[1].split("&")[0]
                except: pass
            else:
                for p in yt.get_library_playlists(limit=100):
                    if p['title'].lower() == p_req.lower():
                        PLAYLIST_ID = p['playlistId']
                        break
            if not PLAYLIST_ID:
                print(f"!!! ERROR: Could not find '{p_req}' !!!")
                self.unlock_buttons()
                return
            tracks = yt.get_playlist(PLAYLIST_ID, limit=None).get('tracks', [])
            yt_tracks = [{"Title": t['title'], "Artist": ", ".join([a['name'] for a in t['artists']])} for t in tracks]
            df_master = pd.read_csv("cleanlist.csv")
            df_master.columns = ['No', 'Title', 'Artist']
            missing, offset = [], 0
            for idx, row in df_master.iterrows():
                m_no = int(row['No'])
                e_idx = idx + offset
                if e_idx < len(yt_tracks):
                    if brain.is_same_song(m_no, row['Title'], row['Artist'], yt_tracks[e_idx]['Title'], yt_tracks[e_idx]['Artist']): continue
                missing.append(f"MISSING #{m_no}: {row['Artist']} - {row['Title']}")
            if missing:
                print("\n[!] GAPS FOUND:")
                for m in missing: print(m)
            else: print("\n[+] 100% PERFECT SYNC.")
            self.unlock_buttons()
        except Exception as e:
            print(f"\n!!! SCANNER ERROR !!!\n{str(e)}")
            self.unlock_buttons()

    def start_sync_thread(self):
        self.lock_buttons("SYNCING...")
        threading.Thread(target=self.run_sync_logic, daemon=True).start()

    def run_sync_logic(self):
        try:
            if not os.path.exists("browser.json") or not os.path.exists("cleanlist.csv"):
                print("!!! ERROR: Missing browser.json or cleanlist.csv !!!")
                self.unlock_buttons()
                return
            yt = YTMusic("browser.json")
            brain = SmartBrain()
            cache = load_cache_with_overrides()
            is_strict = "Strict" in self.mode_switch.get()
            p_req = self.playlist_input.get().strip() or "OST All Songs"
            PLAYLIST_ID = None
            if "list=" in p_req:
                try: PLAYLIST_ID = p_req.split("list=")[1].split("&")[0]
                except: pass
            else:
                for p in yt.get_library_playlists(limit=100):
                    if p['title'].lower() == p_req.lower():
                        PLAYLIST_ID = p['playlistId']
                        break
                if not PLAYLIST_ID:
                    PLAYLIST_ID = yt.create_playlist(p_req, "Sync Hub Auto")
                    time.sleep(3)
            live_count = len(yt.get_playlist(PLAYLIST_ID, limit=None).get('tracks', []))
            df = pd.read_csv("cleanlist.csv")
            df.columns = ['No', 'Title', 'Artist']
            total = len(df)
            for i in range(total):
                m_no, m_title, m_artist = int(df.iloc[i]['No']), str(df.iloc[i]['Title']), str(df.iloc[i]['Artist'])
                if m_no <= live_count:
                    print(f"[{m_no}/{total}] SKIPPED")
                    continue
                v_id = cache.get(m_no)
                if not v_id:
                    s = yt.search(f"{m_artist} {m_title}", filter="songs")
                    if not s: continue
                    v_id = s[0]['videoId']
                yt.add_playlist_items(PLAYLIST_ID, [v_id])
                with open("url.txt", "a") as f: f.write(f'{m_no},"{v_id}"\n')
                time.sleep(3.5)
                print(f"[{m_no}/{total}] ADDED")
            print("\n=== SUCCESS ===")
            self.unlock_buttons()
        except Exception as e:
            print(f"\n!!! ERROR !!!\n{str(e)}")
            self.unlock_buttons()

if __name__ == "__main__":
    app = UltimateSyncApp()
    app.mainloop()

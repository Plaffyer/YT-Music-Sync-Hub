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
            "&": "and", "xchenda": "chenda", "mø": "mo", "mu la la": "" 
        }
        self.track_exceptions = {
            452: "mikeeysmind", 533: "slushii", 593: "creepy nuts", 628: "civ", 655: "huntr/x"
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
        if not m_t: return artist_match
        match_count = len(m_t.intersection(yt_all))
        return (match_count / len(m_t) > 0.5) and artist_match

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
                try: cache_map[int(row['No'])] = str(row['VideoID'])
                except: continue
        except: pass
    for no_key, correct_url in MANUAL_OVERRIDES.items(): cache_map[no_key] = correct_url
    return cache_map

# PART 3: MAIN APPLICATION & UI FRONTEND [CORE/PERMANENT]
class UltimateSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YT Music Sync Hub")
        self.geometry("950x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # PART 3A: SIDEBAR NAVIGATION
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Sync Hub", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.add_nav_btn("1. Dashboard", "Run scanners & sync", 1, "dash")
        self.add_nav_btn("2. Data Import", "Convert CSV to clean list", 3, "import")
        self.add_nav_btn("3. Authentication", "Add F12 Browser Headers", 5, "auth")
        self.add_nav_btn("? Help & Guides", "Fix errors & manuals", 7, "guide", color="#52796F")

        # PART 3B: DASHBOARD VIEW
        self.frame_dash = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_dash.grid_columnconfigure(0, weight=1)
        self.frame_dash.grid_columnconfigure(1, weight=1)
        self.frame_dash.grid_rowconfigure(3, weight=1)

        self.dash_controls = ctk.CTkFrame(self.frame_dash)
        self.dash_controls.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="ew")
        ctk.CTkLabel(self.dash_controls, text="Playlist Name or URL:").grid(row=0, column=0, padx=10, pady=10)
        self.playlist_input = ctk.CTkEntry(self.dash_controls, placeholder_text="e.g., 'OST All Songs' or URL")
        self.playlist_input.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.dash_controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.dash_controls, text="Sync Behavior:").grid(row=1, column=0, padx=10, pady=10)
        self.mode_switch = ctk.CTkOptionMenu(self.dash_controls, values=["Strict Mode (Perfectionist)", "Relaxed Mode (Just add them)"])
        self.mode_switch.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.btn_scan = ctk.CTkButton(self.frame_dash, text="SCAN PLAYLIST TARGET BOT", command=self.start_scan_thread, height=40, fg_color="#E07A5F", hover_color="#D06A4F")
        self.btn_scan.grid(row=1, column=0, padx=20, pady=(10,0), sticky="ew")
        ctk.CTkLabel(self.frame_dash, text="Checks YouTube vs Local List for gaps", font=ctk.CTkFont(size=11), text_color="gray").grid(row=2, column=0, pady=(0,10))

        self.btn_sync = ctk.CTkButton(self.frame_dash, text="INITIATE SYNC ENGINE", command=self.start_sync_thread, height=40)
        self.btn_sync.grid(row=1, column=1, padx=20, pady=(10,0), sticky="ew")
        ctk.CTkLabel(self.frame_dash, text="Begins automated migration to YouTube", font=ctk.CTkFont(size=11), text_color="gray").grid(row=2, column=1, pady=(0,10))

        self.console = ctk.CTkTextbox(self.frame_dash, font=ctk.CTkFont(family="Consolas", size=13))
        self.console.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.console.configure(state="disabled")
        sys.stdout = TextRedirector(self.console)

        # PART 3C: DATA IMPORT VIEW
        self.frame_import = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_import.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.frame_import, text="Import External Playlist", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=40, sticky="w")
        ctk.CTkLabel(self.frame_import, text="This tool automatically fixes typos like 'Tittle' or 'Artis' and maps 'Track Name' headers.", justify="left").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.btn_import_file = ctk.CTkButton(self.frame_import, text="SELECT FILE & CONVERT", command=self.import_csv_logic, height=40, fg_color="#81B29A")
        self.btn_import_file.grid(row=2, column=0, padx=20, pady=20, sticky="w")

        # PART 3D: AUTHENTICATION VIEW
        self.frame_auth = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_auth.grid_columnconfigure(0, weight=1)
        self.frame_auth.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(self.frame_auth, text="Header Converter", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=40, sticky="w")
        self.header_input = ctk.CTkTextbox(self.frame_auth, font=ctk.CTkFont(family="Consolas", size=12))
        self.header_input.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.btn_save_auth = ctk.CTkButton(self.frame_auth, text="CONVERT BROWSER FILE", command=self.save_headers, height=40, fg_color="#E07A5F")
        self.btn_save_auth.grid(row=2, column=0, padx=20, pady=20, sticky="w")

        # PART 3E: HELP & GUIDES
        self.frame_guide = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_guide.grid_columnconfigure(0, weight=1)
        self.frame_guide.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self.frame_guide, text="User Manual", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=20, sticky="w")
        self.guide_textbox = ctk.CTkTextbox(self.frame_guide, font=ctk.CTkFont(size=14), wrap="word")
        self.guide_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.guide_textbox.insert("0.0", "Check GitHub README for detailed F12 header tutorial.")
        self.guide_textbox.configure(state="disabled")

        self.select_frame("dash")

    def add_nav_btn(self, text, desc, row, target, color=None):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, command=lambda: self.select_frame(target), anchor="w")
        if color: btn.configure(fg_color=color)
        btn.grid(row=row, column=0, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(self.sidebar_frame, text=desc, font=ctk.CTkFont(size=11), text_color="gray").grid(row=row+1, column=0, padx=20, pady=(0, 10), sticky="w")

    def select_frame(self, name):
        frames = {"dash": self.frame_dash, "import": self.frame_import, "auth": self.frame_auth, "guide": self.frame_guide}
        for k, f in frames.items():
            if k == name: f.grid(row=0, column=1, sticky="nsew")
            else: f.grid_forget()

    # PART 4: FUZZY IMPORT LOGIC [ADJUSTABLE]
    def import_csv_logic(self):
        file_path = ctk.filedialog.askopenfilename(title="Select Playlist File", filetypes=[("CSV files", "*.csv")])
        if not file_path: return
        try:
            # Load with latin1 to safely handle all symbols
            df = pd.read_csv(file_path, encoding='latin1')
            
            # Keywords to find Title and Artist even with typos
            title_keywords = ["title", "tittle", "song", "track", "name"]
            artist_keywords = ["artist", "artis", "singer", "performer", "band"]
            
            found_title_col = None
            found_artist_col = None

            for col in df.columns:
                c_clean = col.lower().strip()
                # Check for Title matches
                if any(k in c_clean for k in title_keywords):
                    # Prioritize exact word if multiple matches exist
                    found_title_col = col
                # Check for Artist matches
                if any(k in c_clean for k in artist_keywords):
                    found_artist_col = col
            
            if found_title_col and found_artist_col:
                df = df.rename(columns={found_title_col: 'Title', found_artist_col: 'Artist'})
                
                # Create 'No' column based on position
                if 'No' not in df.columns:
                    df.insert(0, 'No', range(1, len(df) + 1))
                
                # Standardize and save
                final_df = df[['No', 'Title', 'Artist']].copy()
                final_df.to_csv("cleanlist.csv", index=False, encoding='utf-8-sig')
                
                self.select_frame("dash")
                print("\n--- IMPORT SUCCESS ---")
                print(f"Standardized: '{found_title_col}' -> Title | '{found_artist_col}' -> Artist")
                alert_user("Success", "List imported and auto-corrected successfully.")
            else:
                alert_user("Format Error", "Could not identify song/artist columns.\nEnsure your CSV headers are clear.")
        except Exception as e: alert_user("Import Error", f"Failed to process file: {str(e)}")

    def save_headers(self):
        raw = self.header_input.get("1.0", "end-1c").strip()
        if not raw: return
        try:
            yt_setup(filepath="browser.json", headers_raw=raw)
            self.header_input.delete("1.0", "end")
            self.select_frame("dash")
            alert_user("Success", "Bot Unlocked.")
        except Exception as e: alert_user("Error", str(e))

    def lock_buttons(self, msg):
        self.btn_scan.configure(state="disabled")
        self.btn_sync.configure(state="disabled", text=msg)

    def unlock_buttons(self):
        self.btn_scan.configure(state="normal")
        self.btn_sync.configure(state="normal", text="INITIATE SYNC ENGINE")

    def start_scan_thread(self):
        self.lock_buttons("SCANNING...")
        threading.Thread(target=self.run_target_logic, daemon=True).start()

    def run_target_logic(self):
        brain = SmartBrain()
        print("\n--- SCANNER BOOTING ---")
        try:
            if not os.path.exists("browser.json") or not os.path.exists("cleanlist.csv"):
                print("!!! ERROR: Missing required files !!!")
                self.unlock_buttons(); return
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
                print(f"!!! ERROR: '{p_req}' not found !!!"); self.unlock_buttons(); return
            
            tracks = yt.get_playlist(PLAYLIST_ID, limit=None).get('tracks', [])
            yt_tracks = [{"Title": t['title'], "Artist": ", ".join([a['name'] for a in t['artists']])} for t in tracks]
            
            df_m = pd.read_csv("cleanlist.csv", encoding='utf-8-sig')
            missing, offset = [], 0
            for idx, row in df_m.iterrows():
                m_no, e_idx = int(row['No']), idx + offset
                if e_idx < len(yt_tracks):
                    if brain.is_same_song(m_no, row['Title'], row['Artist'], yt_tracks[e_idx]['Title'], yt_tracks[e_idx]['Artist']): continue
                missing.append(f"GAP #{m_no}: {row['Artist']} - {row['Title']}")
            
            if missing: 
                print(f"\n[!] GAPS DETECTED ({len(missing)}):")
                for m in missing: print(m)
            else: print("\n[+] 100% PERFECT SYNC.")
            self.unlock_buttons()
        except Exception as e: print(f"\n!!! SCAN ERROR: {str(e)} !!!"); self.unlock_buttons()

    def start_sync_thread(self):
        self.lock_buttons("SYNCING...")
        threading.Thread(target=self.run_sync_logic, daemon=True).start()

    def run_sync_logic(self):
        try:
            if not os.path.exists("browser.json") or not os.path.exists("cleanlist.csv"): 
                self.unlock_buttons(); return
            yt = YTMusic("browser.json")
            brain, cache = SmartBrain(), load_cache_with_overrides()
            is_strict = "Strict" in self.mode_switch.get()
            p_req = self.playlist_input.get().strip() or "OST All Songs"
            
            PLAYLIST_ID = None
            for p in yt.get_library_playlists(limit=100):
                if p['title'].lower() == p_req.lower(): PLAYLIST_ID = p['playlistId']; break
            if not PLAYLIST_ID: 
                PLAYLIST_ID = yt.create_playlist(p_req, "Sync Hub Auto"); time.sleep(3)
            
            live_count = len(yt.get_playlist(PLAYLIST_ID, limit=None).get('tracks', []))
            df = pd.read_csv("cleanlist.csv", encoding='utf-8-sig')
            total = len(df)
            
            print(f"--- STARTING SYNC ({'STRICT' if is_strict else 'RELAXED'}) ---")
            for i in range(total):
                m_no, m_title, m_artist = int(df.iloc[i]['No']), str(df.iloc[i]['Title']), str(df.iloc[i]['Artist'])
                if m_no <= live_count: print(f"[{m_no}/{total}] SKIPPED"); continue
                
                vid = cache.get(m_no)
                if not vid:
                    s = yt.search(f"{m_artist} {m_title}", filter="songs")
                    if not s: continue
                    vid = s[0]['videoId']
                
                yt.add_playlist_items(PLAYLIST_ID, [vid])
                with open("url.txt", "a") as f: f.write(f'{m_no},"{vid}"\n')
                time.sleep(3.5); print(f"[{m_no}/{total}] ADDED")
            print("\n=== SUCCESS ==="); self.unlock_buttons()
        except Exception as e: print(f"\n!!! ERROR: {str(e)} !!!"); self.unlock_buttons()

if __name__ == "__main__":
    app = UltimateSyncApp(); app.mainloop()

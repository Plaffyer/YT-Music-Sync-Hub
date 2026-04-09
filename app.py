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
import json
import shutil
from datetime import datetime
from ytmusicapi import YTMusic

# PART 1: SYSTEM UTILS & REDIRECTOR [CORE/PERMANENT]
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget
    def write(self, str_text):
        self.widget.configure(state="normal")
        self.widget.insert("end", str_text)
        self.widget.see("end")
        self.widget.configure(state="disabled")
    def flush(self): pass

def log_accuracy(m_no, sim_pct, target, found):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{now}] #{m_no} | {sim_pct}% | Target: {target} | Found: {found}\n"
    with open("accuracy.txt", "a", encoding="utf-8") as log:
        log.write(log_entry)

def alert_user(title, message, is_choice=False, is_error=False):
    winsound.Beep(1000, 500)
    if is_choice: style = 0x40024 
    elif is_error: style = 0x40010
    else: style = 0x40040
    return ctypes.windll.user32.MessageBoxW(0, message, title, style)

# PART 2: AI BRAIN & MEMORY [RESTORED FROM MAIN.PY]
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
        self.track_exceptions = {452: "mikeeysmind", 533: "slushii", 593: "creepy nuts", 628: "civ", 655: "huntr/x"}

    def clean_set(self, text):
        t = str(text).lower()
        for word, fix in self.aliases.items(): t = t.replace(word, fix)
        t = re.sub(r'[^a-z0-9\s]', ' ', t)
        return {w for w in t.split() if w not in self.noise and len(w) > 1}

    def clean_string(self, text):
        return "".join(self.clean_set(text))

    def is_same_song(self, m_no, m_title, m_artist, yt_title, yt_artist):
        if m_no in self.track_exceptions and self.track_exceptions[m_no] in str(yt_artist).lower(): return True
        m_t = self.clean_set(m_title)
        m_a = self.clean_set(m_artist)
        yt_all = self.clean_set(yt_title).union(self.clean_set(yt_artist))

        artist_match = bool(m_a.intersection(yt_all))
        if not m_t: return artist_match
        
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
            df = pd.read_csv("url.txt", encoding='utf-8-sig', on_bad_lines='skip')
            for idx, row in df.iterrows():
                try:
                    track_no = int(row['No']) if 'No' in df.columns else int(row.iloc[0])
                    vid_id = str(row['VideoID']) if 'VideoID' in df.columns else str(row.iloc[-1])
                    cache_map[track_no] = vid_id
                except ValueError: continue
        except Exception as e: print(f"--- Warning: Could not load url.txt cleanly: {e} ---")
    for no_key, correct_url in MANUAL_OVERRIDES.items(): cache_map[no_key] = correct_url
    return cache_map

# PART 3: MAIN APPLICATION GUI
class UltimateSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YT Music Sync Hub")
        self.geometry("1100x800")
        ctk.set_appearance_mode("dark")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sync_state = "stopped"
        self.stop_event = threading.Event()
        self.nav_row = 1

        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar_frame, text="Sync Hub", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=30)
        
        self.add_nav_btn("1. Dashboard", "Main Hub", "engine")
        self.add_sub_btn("Engine Controls", "engine")
        self.add_sub_btn("Manual Override", "manual")
        self.add_sub_btn("Download Data", "download")
        self.add_sub_btn("Target Analytics", "scan")
        
        self.add_nav_btn("2. CSV Setup", "Import your list", "import")
        self.add_nav_btn("3. Auth Setup", "Add Headers", "auth")
        self.add_nav_btn("Help & Guides", "App Manual", "guide", color="#52796F")

        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.build_frames()
        self.select_frame("engine")

    def build_frames(self):
        # 1. ENGINE FRAME
        self.frame_engine = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(self.frame_engine, text="Sync Engine Controls", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")
        
        ctrl_box = ctk.CTkFrame(self.frame_engine, fg_color="#2B2B2B")
        ctrl_box.pack(fill="x", pady=10, ipadx=20, ipady=20)
        self.playlist_input = ctk.CTkEntry(ctrl_box, placeholder_text="Playlist Name OR YouTube URL", width=400)
        self.playlist_input.pack(pady=10)
        
        if os.path.exists("last_playlist.txt"):
            with open("last_playlist.txt", "r", encoding="utf-8-sig") as f:
                saved_text = f.read().strip()
                if saved_text: self.playlist_input.insert(0, saved_text)

        self.mode_switch = ctk.CTkOptionMenu(ctrl_box, values=["Strict Mode", "Relaxed Mode"], width=200)
        self.mode_switch.pack(pady=5)
        self.btn_sync = ctk.CTkButton(ctrl_box, text="INITIATE SYNC", command=self.start_sync_thread, height=45, font=ctk.CTkFont(weight="bold"))
        self.btn_sync.pack(pady=15, fill="x", padx=100)
        
        btn_grp = ctk.CTkFrame(ctrl_box, fg_color="transparent")
        btn_grp.pack(pady=5)
        ctk.CTkButton(btn_grp, text="PAUSE", width=100, command=self.pause_sync, fg_color="#D4A373").grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_grp, text="RESUME", width=100, command=self.resume_sync, fg_color="#81B29A").grid(row=0, column=1, padx=10)
        ctk.CTkButton(btn_grp, text="STOP", width=100, command=self.stop_sync, fg_color="#BC4749").grid(row=0, column=2, padx=10)

        self.console = ctk.CTkTextbox(self.frame_engine, font=ctk.CTkFont(family="Consolas", size=13), border_width=2)
        self.console.pack(fill="both", expand=True, pady=(20, 0))
        self.console.configure(state="disabled"); sys.stdout = TextRedirector(self.console)

        # 2. MANUAL OVERRIDE FRAME
        self.frame_manual = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(self.frame_manual, text="Manual Perfection Override", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")
        
        man_box = ctk.CTkFrame(self.frame_manual, fg_color="#2B2B2B")
        man_box.pack(fill="x", pady=10, ipadx=20, ipady=20)
        ctk.CTkLabel(man_box, text="Search by Song Title to find its Number.", font=ctk.CTkFont(size=14)).pack(pady=10)
        self.search_entry = ctk.CTkEntry(man_box, placeholder_text="Song Title...", width=400)
        self.search_entry.pack(pady=10)
        ctk.CTkButton(man_box, text="SEARCH AND VERIFY", command=self.find_and_verify, fg_color="#3D5A80", width=200).pack(pady=10)
        
        ctk.CTkLabel(man_box, text="Paste the exact YouTube Video ID below to force the bot to use it.", font=ctk.CTkFont(size=14)).pack(pady=(30, 10))
        ov_f = ctk.CTkFrame(man_box, fg_color="transparent")
        ov_f.pack(pady=10)
        self.ov_no = ctk.CTkEntry(ov_f, placeholder_text="Song No.", width=100); self.ov_no.grid(row=0, column=0, padx=10)
        self.ov_url = ctk.CTkEntry(ov_f, placeholder_text="YouTube Video ID", width=300); self.ov_url.grid(row=0, column=1, padx=10)
        ctk.CTkButton(ov_f, text="SAVE URL", width=100, command=self.manual_save).grid(row=0, column=2, padx=10)

        # 3. DOWNLOAD FRAME
        self.frame_download = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(self.frame_download, text="Backup and Data Download", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")
        dl_box = ctk.CTkFrame(self.frame_download, fg_color="#2B2B2B")
        dl_box.pack(fill="x", pady=10, ipadx=20, ipady=30)
        ctk.CTkLabel(dl_box, text="Download your live YouTube playlist data into an ostlist.csv file.", font=ctk.CTkFont(size=14)).pack(pady=10)
        self.btn_download = ctk.CTkButton(dl_box, text="DOWNLOAD LIVE DATA", command=self.start_download_thread, fg_color="#3D5A80", height=50, font=ctk.CTkFont(weight="bold"))
        self.btn_download.pack(pady=20)

        # 4. SCAN FRAME
        self.frame_scan = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(self.frame_scan, text="Target Analytics", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")
        sc_box = ctk.CTkFrame(self.frame_scan, fg_color="#2B2B2B")
        sc_box.pack(fill="x", pady=10, ipadx=20, ipady=30)
        ctk.CTkLabel(sc_box, text="Compare your local CSV to the live YouTube playlist to find missing songs.", font=ctk.CTkFont(size=14)).pack(pady=10)
        ctk.CTkButton(sc_box, text="SCAN FOR GAPS", command=self.start_scan_thread, fg_color="#E07A5F", height=50, font=ctk.CTkFont(weight="bold")).pack(pady=20)

        # 5. IMPORT FRAME
        self.frame_import = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(self.frame_import, text="Import CSV List", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")
        imp_box = ctk.CTkFrame(self.frame_import, fg_color="#2B2B2B")
        imp_box.pack(fill="x", pady=10, ipadx=20, ipady=30)
        ctk.CTkLabel(imp_box, text="Select your raw CSV file. The bot will clean and standardize it.", font=ctk.CTkFont(size=14)).pack(pady=10)
        ctk.CTkButton(imp_box, text="SELECT CSV FILE", command=self.import_csv_logic, height=50, font=ctk.CTkFont(weight="bold")).pack(pady=20)

        # 6. AUTH FRAME
        self.frame_auth = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(self.frame_auth, text="Browser Authentication", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 10), anchor="w")
        self.header_input = ctk.CTkTextbox(self.frame_auth, font=ctk.CTkFont(family="Consolas", size=13))
        self.header_input.pack(fill="both", expand=True, pady=10)
        ctk.CTkButton(self.frame_auth, text="CONVERT HEADERS", command=self.save_headers, fg_color="#E07A5F", height=50, font=ctk.CTkFont(weight="bold")).pack(pady=20)

        # 7. GUIDE FRAME
        self.frame_guide = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(self.frame_guide, text="Operating Manual", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")
        self.guide_box = ctk.CTkTextbox(self.frame_guide, wrap="word", font=ctk.CTkFont(size=14))
        self.guide_box.pack(fill="both", expand=True, pady=10)
        self.guide_box.insert("0.0", self.get_full_manual())
        self.guide_box.configure(state="disabled")

        self.all_frames = [self.frame_engine, self.frame_manual, self.frame_download, self.frame_scan, self.frame_import, self.frame_auth, self.frame_guide]

    def add_nav_btn(self, text, desc, target, color=None):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, command=lambda: self.select_frame(target), anchor="w", font=ctk.CTkFont(weight="bold", size=14))
        if color: btn.configure(fg_color=color)
        btn.grid(row=self.nav_row, column=0, padx=20, pady=(20, 0), sticky="ew"); self.nav_row += 1
        ctk.CTkLabel(self.sidebar_frame, text=desc, font=ctk.CTkFont(size=11), text_color="gray").grid(row=self.nav_row, column=0, padx=20, pady=(0, 5), sticky="w"); self.nav_row += 1

    def add_sub_btn(self, text, target):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, command=lambda: self.select_frame(target), anchor="w", height=28, fg_color="#1F1F1F", hover_color="#2B2B2B", border_width=1, border_color="#333333")
        btn.grid(row=self.nav_row, column=0, padx=(35, 20), pady=3, sticky="ew"); self.nav_row += 1

    def select_frame(self, name):
        for f in self.all_frames: f.pack_forget()
        if name == "engine": self.frame_engine.pack(fill="both", expand=True)
        elif name == "manual": self.frame_manual.pack(fill="both", expand=True)
        elif name == "download": self.frame_download.pack(fill="both", expand=True)
        elif name == "scan": self.frame_scan.pack(fill="both", expand=True)
        elif name == "import": self.frame_import.pack(fill="both", expand=True)
        elif name == "auth": self.frame_auth.pack(fill="both", expand=True)
        elif name == "guide": self.frame_guide.pack(fill="both", expand=True)

    def get_full_manual(self):
        return """=== 1. PREPARATION AND HEADERS ===
1. Open music.youtube.com and make sure you are logged in.
2. Press F12 on your keyboard and go to the Network tab.
3. In the filter box type browse. Press F5 to refresh the page.
4. Click the first browse entry in the list.
5. Scroll down to Request Headers and copy the ENTIRE block.
6. Paste it into the Auth Setup page and click Convert.

=== 2. DATA IMPORT ===
Go to CSV Setup and select your exported playlist file.

=== 3. DASHBOARD TARGETING AND URLS ===
You can target a playlist in two ways.
First is by Name. Type a name. If it does not exist the bot creates it.
Second is by URL. Paste the full YouTube Playlist URL directly into the text box. The bot will automatically extract the ID and resume syncing to that exact playlist.

=== 4. MANUAL PERFECTION ===
If the bot picks the wrong version of a song.
1. Go to the Manual Override tab.
2. Search for the song title to find its exact Number from your list.
3. Paste the correct YouTube Video ID.
4. Click Save. The bot will prioritize this link forever.

=== 5. ERROR GLOSSARY ===
Unauthorized Error means your session expired. You need to redo the F12 Headers.
Format Error means ensure you copied from Request Headers and not General.
Gaps Detected means run the Sync Engine again to let the bot fill any missed songs."""

    def resolve_playlist_id(self, yt, user_input):
        txt = user_input.strip()
        if not txt: return None
        if "list=" in txt: return txt.split("list=")[1].split("&")[0]
        if txt.startswith("PL") and len(txt) > 16: return txt
        for p in yt.get_library_playlists(limit=100):
            if p['title'].lower() == txt.lower(): return p['playlistId']
        return None

    def find_and_verify(self):
        query = self.search_entry.get().lower().strip()
        if not query or not os.path.exists("cleanlist.csv"): 
            alert_user("Error", "Please import a CSV first.", is_error=True); return
        df = pd.read_csv("cleanlist.csv", encoding="utf-8-sig")
        match = df[df['Title'].str.lower().str.contains(query, na=False)]
        if not match.empty:
            res = match.iloc[0]
            if alert_user("Confirm", f"Found: #{res['No']} - {res['Title']}. Is this correct?", is_choice=True) == 6:
                self.ov_no.delete(0, 'end'); self.ov_no.insert(0, str(res['No']))
        else: alert_user("Not Found", "No song found with that name.", is_error=True)

    def manual_save(self):
        n, u = self.ov_no.get(), self.ov_url.get()
        if n and u:
            if not os.path.exists("url.txt"):
                with open("url.txt", "w", encoding="utf-8-sig") as f: f.write("No,Title,Artist,VideoID\n")
            with open("url.txt", "a", encoding="utf-8-sig") as f: f.write(f'{n},"Manual Override","User","{u}"\n')
            alert_user("Success", f"Override Saved for Song #{n}.")

    def import_csv_logic(self):
        f = ctk.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not f: return
        try:
            try: df = pd.read_csv(f, encoding='utf-8-sig')
            except: df = pd.read_csv(f, encoding='latin1')
            
            df.columns = [str(c).lower().strip().replace('\ufeff', '') for c in df.columns]
            bt_col = next((c for c in df.columns if any(k in c for k in ['title', 'tittle', 'track', 'song', 'name']) and 'url' not in c), None)
            ba_col = next((c for c in df.columns if any(k in c for k in ['artist', 'artis', 'singer']) and 'url' not in c), None)
            
            if bt_col and ba_col:
                df = df.rename(columns={bt_col: 'Title', ba_col: 'Artist'})
                if 'no' not in df.columns: df.insert(0, 'No', range(1, len(df) + 1))
                else: df = df.rename(columns={'no': 'No'})
                df[['No', 'Title', 'Artist']].to_csv("cleanlist.csv", index=False, encoding='utf-8-sig')
                alert_user("Success", "CSV Imported and Cleaned.", is_error=False)
            elif len(df.columns) >= 2:
                df = df.iloc[:, [0, 1]]; df.columns = ['Title', 'Artist']
                df.insert(0, 'No', range(1, len(df) + 1))
                df[['No', 'Title', 'Artist']].to_csv("cleanlist.csv", index=False, encoding='utf-8-sig')
                alert_user("Success", "CSV Imported via fallback (Columns 1 & 2).", is_error=False)
            else: alert_user("Error", "Could not find Title or Artist columns in your CSV.", is_error=True)
        except Exception as e: alert_user("Error", f"Error reading CSV: {str(e)}", is_error=True)

    def save_headers(self):
        raw = self.header_input.get("1.0", "end").strip()
        req = ["cookie", "user-agent", "accept", "authorization", "x-goog-authuser"]
        d = {l.split(':',1)[0].lower().strip(): l.split(':',1)[1].strip() for l in raw.split('\n') if ':' in l and l.split(':',1)[0].lower().strip() in req}
        if "cookie" in d:
            with open("browser.json", "w", encoding="utf-8-sig") as f: json.dump(d, f, indent=4)
            alert_user("Success", "Bot Authenticated Successfully.")
            self.header_input.delete("1.0", "end")
        else: alert_user("Error", "Missing cookie line in headers.", is_error=True)

    def pause_sync(self): self.sync_state = "paused"; print("\n--- PAUSED ---")
    def resume_sync(self): self.sync_state = "running"; print("\n--- RESUMING ---")
    def stop_sync(self): self.sync_state = "stopped"; self.stop_event.set()
    def lock_buttons(self, m): self.btn_sync.configure(state="disabled", text=m)
    def unlock_buttons(self): self.btn_sync.configure(state="normal", text="INITIATE SYNC")
    
    def start_download_thread(self): 
        self.select_frame("engine")
        threading.Thread(target=self.run_download_logic, daemon=True).start()

    def run_download_logic(self):
        try:
            yt = YTMusic("browser.json")
            p_input = self.playlist_input.get().strip() or "Sync Hub Auto"
            if p_input:
                with open("last_playlist.txt", "w", encoding="utf-8-sig") as f: f.write(p_input)
            p_id = self.resolve_playlist_id(yt, p_input)
            if not p_id:
                print("Download Failed: Playlist not found.")
                return
            tracks = yt.get_playlist(p_id, limit=None).get('tracks', [])
            pd.DataFrame([{"No": i, "Title": t['title']} for i, t in enumerate(tracks, 1)]).to_csv("ostlist.csv", index=False, encoding="utf-8-sig")
            print(f"Successfully Downloaded {len(tracks)} songs to ostlist.csv")
        except Exception as e: print(f"Download Error: {e}")

    def start_scan_thread(self): 
        self.select_frame("engine")
        threading.Thread(target=self.run_target_logic, daemon=True).start()

    def run_target_logic(self):
        brain = SmartBrain()
        try:
            print("Scanning for gaps...")
            yt = YTMusic("browser.json")
            p_input = self.playlist_input.get().strip() or "Sync Hub Auto"
            if p_input:
                with open("last_playlist.txt", "w", encoding="utf-8-sig") as f: f.write(p_input)
            p_id = self.resolve_playlist_id(yt, p_input)
            if not p_id:
                print("Scan Failed: Playlist not found.")
                return
            yt_tracks = yt.get_playlist(p_id, limit=None).get('tracks', [])
            df_m = pd.read_csv("cleanlist.csv", encoding="utf-8-sig")
            missing = False
            for idx, row in df_m.iterrows():
                if idx >= len(yt_tracks) or not brain.is_same_song(row['No'], row['Title'], "N/A", yt_tracks[idx]['title'], "N/A"):
                    print(f"GAP DETECTED: #{row['No']} {row['Title']}")
                    missing = True
            if not missing: print("Playlist is perfectly synchronized.")
        except Exception as e: print(f"Error scanning: {e}")

    def start_sync_thread(self):
        self.stop_event.clear(); self.sync_state = "running"; self.lock_buttons("SYNCING...")
        threading.Thread(target=self.run_sync_logic, daemon=True).start()

    # PART 4: MAIN SYNC ENGINE [RESTORED FROM MAIN.PY]
    def run_sync_logic(self):
        try:
            yt = YTMusic("browser.json")
            brain = SmartBrain()
            
            if not os.path.exists("url.txt"):
                alert_user("Missing File", "Could not find url.txt. Please run download Data first!")
                self.unlock_buttons(); return

            cache_map = load_cache_with_overrides()

            ENABLE_AUTO_RECHECK = True
            LOW_ACCURACY_BEHAVIOR = "ASK" if self.mode_switch.get() == "Strict Mode" else "LOG_ONLY"
            RECHECK_BEHAVIOR = "LOG_ONLY"

            p_input = self.playlist_input.get().strip() or "OST All Songs"
            if p_input:
                with open("last_playlist.txt", "w", encoding="utf-8-sig") as f: f.write(p_input)
                    
            PLAYLIST_ID = self.resolve_playlist_id(yt, p_input)
            if not PLAYLIST_ID:
                print(f"--- CREATING NEW PLAYLIST: {p_input} ---")
                PLAYLIST_ID = yt.create_playlist(p_input, "Auto-generated by Sync Bot")
                time.sleep(3)
            
            try:
                current_playlist_data = yt.get_playlist(PLAYLIST_ID, limit=None)
                live_yt_count = len(current_playlist_data.get('tracks', []))
            except KeyError: live_yt_count = 0
                
            print(f"--- SAFETY CHECK: Found {live_yt_count} songs already inside YouTube Playlist ---")

            df = pd.read_csv("cleanlist.csv", header=0, encoding='utf-8-sig')
            total_songs = len(df)
            print(f"--- STARTING HYPER-SYNC ---")
            
            slow_search_adds = []

            for i in range(total_songs):
                while self.sync_state == "paused": time.sleep(1)
                if self.sync_state == "stopped": break
                
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
                    if m_no in MANUAL_OVERRIDES: print(f"[{m_no}/{total_songs}] {m_title} -- MANUAL OVERRIDE ADD")
                    else: print(f"[{m_no}/{total_songs}] {m_title} -- FAST CACHE ADD")
                    time.sleep(0.5); live_yt_count += 1; continue

                search = yt.search(query, filter="songs")
                if not search:
                    print(f"[{m_no}/{total_songs}] NOT FOUND: {query}")
                    continue

                selected_result = None
                for res in search[:20]:
                    res_title_temp = res['title']
                    res_artist_temp = ", ".join([a['name'] for a in res['artists']])
                    if brain.is_same_song(m_no, m_title, m_artist, res_title_temp, res_artist_temp):
                        selected_result = res; break 

                if not selected_result: selected_result = search[0]

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
                    artist_match_count = len(artist_words.intersection(found_words))
                    if artist_match_count == 0: sim_pct = 5

                if title_sim < 0.4 and word_match_ratio < 1.0: sim_pct = 5 

                if sim_pct < 70: log_accuracy(m_no, sim_pct, f"{m_artist}-{m_title}", f"{res_artist}-{res_title}")

                if sim_pct < 10:
                    alert_user("Hard Stop", f"Accuracy too low at number {m_no}.\nTarget: {m_title}\nFound: {res_title}\nBot stopped to prevent bad data.")
                    self.unlock_buttons(); return

                if 10 <= sim_pct < 30 and LOW_ACCURACY_BEHAVIOR == "HARD_STOP":
                    alert_user("Configured Stop", f"Accuracy is {sim_pct} percent at number {m_no}. Blocked by settings.")
                    self.unlock_buttons(); return

                yt.add_playlist_items(PLAYLIST_ID, [video_id])
                slow_search_adds.append({'m_no': m_no, 'm_title': m_title, 'm_artist': m_artist, 'yt_index': live_yt_count})
                live_yt_count += 1 
                
                if not os.path.exists("url.txt"):
                    with open("url.txt", "w", encoding="utf-8-sig") as f: f.write("No,Title,Artist,VideoID\n")
                with open("url.txt", "a", encoding="utf-8-sig") as f:
                    f.write(f'{m_no},"{res_title}","{res_artist}","{video_id}"\n')

                if 10 <= sim_pct < 30 and LOW_ACCURACY_BEHAVIOR == "ASK":
                    msg = f"VERIFY SONG \nTarget: {m_artist} - {m_title}\nFound: {res_artist} - {res_title}\n\nThe song was ADDED. Check your YT playlist now.\nOK = Continue\nCancel = Stop Bot"
                    if alert_user("Low Accuracy Check", msg, is_choice=True) == 2:
                        print("--- MANUAL STOP BY USER ---")
                        self.unlock_buttons(); return

                time.sleep(3.5) 
                
                try:
                    current_playlist_data = yt.get_playlist(PLAYLIST_ID, limit=None)
                    actual_yt_count = len(current_playlist_data.get('tracks', []))
                    if actual_yt_count < live_yt_count:
                        alert_user("Sync Error", f"Ghost Add at number {m_no}. YouTube missed the song. The playlist is desynced.")
                        self.unlock_buttons(); return
                except KeyError: pass 

                if ENABLE_AUTO_RECHECK and (m_no % 100 == 0):
                    print(f"\n--- INITIATING PERIODIC STATE RECONCILIATION AT #{m_no} ---")
                    if slow_search_adds:
                        print("Checking live playlist integrity...")
                        try:
                            check_data = yt.get_playlist(PLAYLIST_ID, limit=None)
                            check_tracks = check_data.get('tracks', [])
                            for item in slow_search_adds:
                                idx = item['yt_index']
                                if idx < len(check_tracks):
                                    yt_track = check_tracks[idx]
                                    yt_title_chk = yt_track['title']
                                    yt_artist_chk = ", ".join([a['name'] for a in yt_track['artists']])
                                    if not brain.is_same_song(item['m_no'], item['m_title'], item['m_artist'], yt_title_chk, yt_artist_chk):
                                        err_msg = f"!!! RECHECK ERROR AT #{item['m_no']} !!! TARGET: {item['m_title']} | FOUND: {yt_title_chk}"
                                        with open("accuracy.txt", "a", encoding="utf-8") as log: log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {err_msg}\n")
                        except Exception as e: print(f"--- Recheck failed: {e} ---")
                        slow_search_adds.clear()
                    print("--- RECONCILIATION COMPLETE. RESUMING SYNC ---\n")

                print(f"[{m_no}/{total_songs}] {m_title} -- SLOW SEARCH ADD | {sim_pct} percent")
            self.unlock_buttons()
            alert_user("Success", "100 percent Conversion Complete!")
        except Exception as e: 
            print(f"Error: {e}"); self.unlock_buttons()

if __name__ == "__main__":
    app = UltimateSyncApp()
    app.mainloop()

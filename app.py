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
import shutil
import json
from datetime import datetime
from ytmusicapi import YTMusic
from ytmusicapi.setup import setup as yt_setup

# PART 1: SYSTEM UTILS & REDIRECTOR [CORE/PERMANENT]
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget
    def write(self, str_text):
        self.widget.configure(state="normal")
        self.widget.insert("end", str_text); self.widget.see("end")
        self.widget.configure(state="disabled")
    def flush(self): pass

def alert_user(title, message, is_choice=False, is_error=False):
    print(f"\n{'='*40}\n!!! {title.upper()} !!!\n{message}\n{'='*40}")
    winsound.Beep(1000, 500)
    if is_choice: style = 0x40024
    elif is_error: style = 0x40010
    else: style = 0x40040
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
        for word, fix in self.aliases.items(): t = t.replace(word, fix)
        t = re.sub(r'[^a-z0-9\s]', ' ', t)
        return {w for w in t.split() if w not in self.noise and len(w) > 1}

    def is_same_song(self, m_no, m_title, m_artist, yt_title, yt_artist):
        if m_no in self.track_exceptions and self.track_exceptions[m_no] in str(yt_artist).lower():
            return True
        m_t, m_a = self.clean_set(m_title), self.clean_set(m_artist)
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
            # We skip the header or read standard 2-column format
            df = pd.read_csv("url.txt", encoding='utf-8-sig', names=['No', 'VideoID'], on_bad_lines='skip')
            for _, row in df.iterrows():
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
        self.geometry("980x850")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(1, weight=1)

        # STATE MANAGEMENT
        self.sync_state = "stopped" 
        self.stop_event = threading.Event()

        # SIDEBAR
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar_frame, text="Sync Hub", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 30))
        self.add_nav_btn("1. Dashboard", 1, "dash")
        self.add_nav_btn("2. Data Import", 2, "import")
        self.add_nav_btn("3. Authentication", 3, "auth")
        self.add_nav_btn("? Help & Guides", 4, "guide", color="#52796F")

        # DASHBOARD VIEW
        self.frame_dash = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_dash.grid_columnconfigure(0, weight=1); self.frame_dash.grid_columnconfigure(1, weight=1); self.frame_dash.grid_rowconfigure(4, weight=1)
        
        self.dash_controls = ctk.CTkFrame(self.frame_dash); self.dash_controls.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="ew")
        ctk.CTkLabel(self.dash_controls, text="Playlist Name:").grid(row=0, column=0, padx=10, pady=10)
        self.playlist_input = ctk.CTkEntry(self.dash_controls, placeholder_text="e.g., 'OST All Songs'"); self.playlist_input.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.mode_switch = ctk.CTkOptionMenu(self.dash_controls, values=["Strict Mode (Perfectionist)", "Relaxed Mode (Just add them)"]); self.mode_switch.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        self.btn_scan = ctk.CTkButton(self.frame_dash, text="SCAN PLAYLIST TARGET BOT", command=self.start_scan_thread, height=40, fg_color="#E07A5F"); self.btn_scan.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.btn_sync = ctk.CTkButton(self.frame_dash, text="INITIATE SYNC ENGINE", command=self.start_sync_thread, height=40); self.btn_sync.grid(row=1, column=1, padx=20, pady=10, sticky="ew")

        # ENGINE CONTROL PANEL
        self.ctrl_panel = ctk.CTkFrame(self.frame_dash); self.ctrl_panel.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        self.btn_pause = ctk.CTkButton(self.ctrl_panel, text="PAUSE", command=self.pause_sync, width=100, fg_color="#D4A373"); self.btn_pause.grid(row=0, column=0, padx=10, pady=10)
        self.btn_resume = ctk.CTkButton(self.ctrl_panel, text="RESUME", command=self.resume_sync, width=100, fg_color="#81B29A"); self.btn_resume.grid(row=0, column=1, padx=10, pady=10)
        self.btn_stop = ctk.CTkButton(self.ctrl_panel, text="STOP / FORCE STOP", command=self.stop_sync, width=150, fg_color="#BC4749"); self.btn_stop.grid(row=0, column=2, padx=10, pady=10)

        self.console = ctk.CTkTextbox(self.frame_dash, font=ctk.CTkFont(family="Consolas", size=13)); self.console.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.console.configure(state="disabled"); sys.stdout = TextRedirector(self.console)

        # IMPORT VIEW
        self.frame_import = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent"); self.frame_import.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.frame_import, text="Import External Playlist", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=40, sticky="w")
        self.btn_import_file = ctk.CTkButton(self.frame_import, text="SELECT FILE & CONVERT", command=self.import_csv_logic, height=40, fg_color="#81B29A"); self.btn_import_file.grid(row=1, column=0, padx=20, pady=20, sticky="w")

        # AUTH VIEW
        self.frame_auth = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent"); self.frame_auth.grid_columnconfigure(0, weight=1); self.frame_auth.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(self.frame_auth, text="Header Converter", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=40, sticky="w")
        self.header_input = ctk.CTkTextbox(self.frame_auth, height=350); self.header_input.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.btn_save_auth = ctk.CTkButton(self.frame_auth, text="CONVERT BROWSER HEADERS", command=self.save_headers, height=40, fg_color="#E07A5F"); self.btn_save_auth.grid(row=2, column=0, padx=20, pady=20, sticky="w")

        # GUIDE VIEW
        self.frame_guide = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent"); self.frame_guide.grid_columnconfigure(0, weight=1); self.frame_guide.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self.frame_guide, text="Detailed Bot Operating Guide", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=20, sticky="w")
        self.guide_textbox = ctk.CTkTextbox(self.frame_guide, font=ctk.CTkFont(size=14), wrap="word"); self.guide_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.guide_textbox.insert("0.0", self.get_full_manual()); self.guide_textbox.configure(state="disabled")

        self.select_frame("dash")

    def add_nav_btn(self, text, row, target, color=None):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, command=lambda: self.select_frame(target), anchor="w")
        if color: btn.configure(fg_color=color)
        btn.grid(row=row, column=0, padx=20, pady=10, sticky="ew")

    def select_frame(self, name):
        frames = {"dash": self.frame_dash, "import": self.frame_import, "auth": self.frame_auth, "guide": self.frame_guide}
        for k, f in frames.items():
            if k == name: f.grid(row=0, column=1, sticky="nsew")
            else: f.grid_forget()

    def get_full_manual(self):
        return """=== 1. PREPARATION: HEADERS ===
The bot needs browser cookies to log in.
1. Open Opera GX/Chrome -> music.youtube.com (Login).
2. F12 -> Network tab -> Filter 'browse'.
3. Press F5 -> Click first 'browse' -> Request Headers.
4. Copy ALL and paste into 'Authentication' tab -> Convert.

=== 2. DATA IMPORT: CSV ===
1. Export playlist CSV.
2. Go to 'Data Import' -> Select file.
3. Bot standardizes the headers and cleans typos automatically.

=== 3. DASHBOARD: SYNC CONTROLS ===
• SCAN: Compares YouTube vs Local CSV.
• SYNC: Begins automated migration.
• PAUSE: Stops at the next song immediately.
• RESUME: Continues processing.
• STOP: Force kills the current task.

=== 4. ERROR GLOSSARY ===
• '401 Unauthorized': Session died. Redo Headers.
• 'Gaps detected': Run SCAN to see missing song IDs.
• 'Not Responding': Use the FORCE STOP button."""

    def import_csv_logic(self):
        if os.path.exists("cleanlist.csv"):
            if alert_user("Safety", "Backup and Replace existing list?", is_choice=True) != 6: return
            if not os.path.exists("backups"): os.makedirs("backups")
            shutil.copy("cleanlist.csv", f"backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        file_path = ctk.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path: return
        try:
            df = pd.read_csv(file_path, encoding='latin1')
            bt_col, ba_col = None, None
            for col in df.columns:
                c = str(col).lower()
                if any(k in c for k in ['title', 'track', 'song', 'name']) and 'url' not in c: bt_col = col
                if any(k in c for k in ['artist', 'artis', 'singer']) and 'url' not in c: ba_col = col
            if bt_col and ba_col:
                df = df.rename(columns={bt_col: 'Title', ba_col: 'Artist'})
                if 'No' not in df.columns: df.insert(0, 'No', range(1, len(df) + 1))
                df[['No', 'Title', 'Artist']].to_csv("cleanlist.csv", index=False, encoding='utf-8-sig')
                self.select_frame("dash"); alert_user("Success", "Playlist Imported.", is_error=False)
        except Exception as e: alert_user("Error", str(e), is_error=True)

    def save_headers(self):
        raw = self.header_input.get("1.0", "end-1c").strip()
        if not raw: return
        with open("uncleant.txt", "w", encoding="utf-8") as f: f.write(raw)
        lines = [line.strip() for line in raw.split('\n') if line.strip()]
        required = ["cookie", "user-agent", "accept", "authorization", "x-goog-authuser", "x-origin", "origin"]
        headers_dict = {}
        for i in range(len(lines)):
            l_low = lines[i].lower().replace(':', '').strip()
            if l_low in required and i + 1 < len(lines): headers_dict[l_low] = lines[i+1].strip()
            elif ':' in lines[i]:
                parts = lines[i].split(':', 1)
                k_low = parts[0].strip().lower()
                if k_low in required: headers_dict[k_low] = parts[1].strip()
        if not headers_dict: alert_user("Error", "No valid headers found.", is_error=True); return
        with open("clean.txt", "w", encoding="utf-8") as f:
            for k, v in headers_dict.items(): f.write(f"{k}: {v}\n")
        with open("browser.json", "w", encoding="utf-8") as f: json.dump(headers_dict, f, indent=4)
        self.header_input.delete("1.0", "end"); self.select_frame("dash")
        alert_user("Success", "Bot Unlocked.", is_error=False)

    def pause_sync(self): self.sync_state = "paused"; print("\n--- ENGINE PAUSED ---")
    def resume_sync(self): self.sync_state = "running"; print("\n--- ENGINE RESUMING ---")
    def stop_sync(self): 
        self.sync_state = "stopped"
        self.stop_event.set()
        print("\n--- HARD STOP TRIGGERED ---")
        self.unlock_buttons()

    def lock_buttons(self, m):
        self.btn_scan.configure(state="disabled"); self.btn_sync.configure(state="disabled", text=m)
    def unlock_buttons(self):
        self.btn_scan.configure(state="normal"); self.btn_sync.configure(state="normal", text="INITIATE SYNC ENGINE")
    
    def start_scan_thread(self):
        self.lock_buttons("SCANNING..."); threading.Thread(target=self.run_target_logic, daemon=True).start()
    
    def run_target_logic(self):
        brain = SmartBrain()
        try:
            if not os.path.exists("browser.json") or not os.path.exists("cleanlist.csv"): self.unlock_buttons(); return
            yt = YTMusic("browser.json")
            p_req = self.playlist_input.get().strip() or "OST All Songs"
            PLAYLIST_ID = None
            for p in yt.get_library_playlists(limit=100):
                if p['title'].lower() == p_req.lower(): PLAYLIST_ID = p['playlistId']; break
            if not PLAYLIST_ID: self.unlock_buttons(); return
            tracks = yt.get_playlist(PLAYLIST_ID, limit=None).get('tracks', [])
            yt_tracks = [{"Title": t['title'], "Artist": ", ".join([a['name'] for a in t['artists']])} for t in tracks]
            df_m = pd.read_csv("cleanlist.csv", encoding='utf-8-sig')
            missing = []
            for idx, row in df_m.iterrows():
                if idx < len(yt_tracks):
                    if brain.is_same_song(int(row['No']), row['Title'], row['Artist'], yt_tracks[idx]['Title'], yt_tracks[idx]['Artist']): continue
                missing.append(f"GAP #{row['No']}: {row['Artist']} - {row['Title']}")
            if missing: [print(m) for m in missing]
            else: print("\n[+] 100% PERFECT SYNC.")
            self.unlock_buttons()
        except: self.unlock_buttons()

    def start_sync_thread(self):
        self.stop_event.clear()
        self.sync_state = "running"
        self.lock_buttons("SYNCING...")
        threading.Thread(target=self.run_sync_logic, daemon=True).start()

    def run_sync_logic(self):
        try:
            if not os.path.exists("browser.json") or not os.path.exists("cleanlist.csv"): self.unlock_buttons(); return
            yt = YTMusic("browser.json")
            cache = load_cache_with_overrides()
            p_req = self.playlist_input.get().strip() or "OST All Songs"
            PLAYLIST_ID = None
            for p in yt.get_library_playlists(limit=100):
                if p['title'].lower() == p_req.lower(): PLAYLIST_ID = p['playlistId']; break
            if not PLAYLIST_ID: PLAYLIST_ID = yt.create_playlist(p_req, "Sync Hub Auto"); time.sleep(2)
            
            live_count = len(yt.get_playlist(PLAYLIST_ID, limit=None).get('tracks', []))
            df = pd.read_csv("cleanlist.csv", encoding='utf-8-sig')
            
            for i in range(len(df)):
                # DYNAMIC CONTROL CHECK
                while self.sync_state == "paused": time.sleep(1)
                if self.sync_state == "stopped" or self.stop_event.is_set(): break

                m_no, m_title, m_artist = int(df.iloc[i]['No']), str(df.iloc[i]['Title']), str(df.iloc[i]['Artist'])
                # Skip if already in live playlist
                if m_no <= live_count: print(f"[{m_no}] SKIPPED (Live)"); continue
                
                vid = cache.get(m_no)
                if not vid:
                    s = yt.search(f"{m_artist} {m_title}", filter="songs")
                    if s: vid = s[0]['videoId']
                
                if vid:
                    yt.add_playlist_items(PLAYLIST_ID, [vid])
                    with open("url.txt", "a", encoding="utf-8") as f: f.write(f'{m_no},"{vid}"\n')
                    print(f"[{m_no}] ADDED: {m_title}")
                    time.sleep(3.5)
            
            print("\n=== ENGINE TASK COMPLETED ==="); self.unlock_buttons()
        except Exception as e: print(f"\n!!! ENGINE ERROR: {str(e)} !!!"); self.unlock_buttons()

if __name__ == "__main__":
    app = UltimateSyncApp(); app.mainloop()

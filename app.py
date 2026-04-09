import customtkinter as ctk
import threading
import sys
import os
import pandas as pd
import time
import re
import winsound
import ctypes
import json
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

def alert_user(title, message, is_choice=False, is_error=False):
    winsound.Beep(1000, 500)
    if is_choice: style = 0x40024 
    elif is_error: style = 0x40010
    else: style = 0x40040
    return ctypes.windll.user32.MessageBoxW(0, message, title, style)

# PART 2: AI BRAIN & MEMORY [ADJUSTABLE/TWEAKABLE]
class SmartBrain:
    def __init__(self):
        self.noise = {'feat', 'ft', 'with', 'x', 'official', 'video', 'audio', 'remix', 'edit', 'the', 'a', 'and'}
        self.aliases = {"chid": "child", "prblm": "problem", "s1mba": "simba", "&": "and", "mø": "mo"}
        self.track_exceptions = {452: "mikeeysmind", 533: "slushii", 593: "creepy nuts", 628: "civ", 655: "huntr/x"}

    def clean_set(self, text):
        t = str(text).lower()
        for word, fix in self.aliases.items(): t = t.replace(word, fix)
        t = re.sub(r'[^a-z0-9\s]', ' ', t)
        return {w for w in t.split() if w not in self.noise and len(w) > 1}

    def is_same_song(self, m_no, m_title, m_artist, yt_title, yt_artist):
        if m_no in self.track_exceptions and self.track_exceptions[m_no] in str(yt_artist).lower(): return True
        m_t = self.clean_set(m_title)
        yt_all = self.clean_set(yt_title).union(self.clean_set(yt_artist))
        if not m_t: return True
        return (len(m_t.intersection(yt_all)) / len(m_t) > 0.5)

MANUAL_OVERRIDES = {
    105: "dlAkd-5WmNk", 121: "M9KQbrwi7WY", 219: "INo4WtusH10", 233: "9cT-v9NxRsA", 
    238: "3Jgso_CkHxw", 279: "GbM2A6HXnMQ", 302: "fTL3sAxt7-8", 359: "qA6Z41612PU",
    370: "jCZXvdu3gtE", 420: "4Vz3Xzq6-nU", 509: "DbTSPATbcUc", 561: "uNLlckry2vY",
    593: "W0dsUNS4RT8", 599: "6-GspWPOa1U", 616: "z9E3zRjQB_g", 617: "tthafU1Ao40",
    658: "vSU1wdh-TDg"
}

# PART 3: MAIN APPLICATION [CORE/PERMANENT]
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

        # SIDEBAR
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar_frame, text="Sync Hub", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=30)
        
        # NAVIGATION HIERARCHY
        self.add_nav_btn("1. Dashboard", "Main Hub", "engine")
        self.add_sub_btn("Engine Controls", "engine")
        self.add_sub_btn("Manual Override", "manual")
        self.add_sub_btn("Download Data", "download")
        self.add_sub_btn("Target Analytics", "scan")
        
        self.add_nav_btn("2. CSV Setup", "Import your list", "import")
        self.add_nav_btn("3. Auth Setup", "Add F12 Headers", "auth")
        self.add_nav_btn("? Help & Guides", "App Manual", "guide", color="#52796F")

        # MAIN CONTENT AREA
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
        ctk.CTkButton(man_box, text="SEARCH & VERIFY", command=self.find_and_verify, fg_color="#3D5A80", width=200).pack(pady=10)
        
        ctk.CTkLabel(man_box, text="Paste the exact YouTube Video ID below to force the bot to use it.", font=ctk.CTkFont(size=14)).pack(pady=(30, 10))
        ov_f = ctk.CTkFrame(man_box, fg_color="transparent")
        ov_f.pack(pady=10)
        self.ov_no = ctk.CTkEntry(ov_f, placeholder_text="Song No.", width=100); self.ov_no.grid(row=0, column=0, padx=10)
        self.ov_url = ctk.CTkEntry(ov_f, placeholder_text="YouTube Video ID", width=300); self.ov_url.grid(row=0, column=1, padx=10)
        ctk.CTkButton(ov_f, text="SAVE URL", width=100, command=self.manual_save).grid(row=0, column=2, padx=10)

        # 3. DOWNLOAD FRAME
        self.frame_download = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(self.frame_download, text="Backup & Data Download", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")
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
        ctk.CTkLabel(self.frame_auth, text="Paste your complete 'Request Headers' below.", font=ctk.CTkFont(size=14)).pack(pady=(0, 20), anchor="w")
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
        return """=== 1. PREPARATION: HEADERS ===
1. Open music.youtube.com and make sure you are logged in.
2. Press F12 on your keyboard -> Go to the 'Network' tab.
3. In the filter box, type 'browse'. Press F5 to refresh the page.
4. Click the first 'browse' entry in the list.
5. Scroll down to 'Request Headers', copy the ENTIRE block.
6. Paste it into the Auth Setup page and click Convert.

=== 2. DATA IMPORT ===
Go to CSV Setup and select your exported playlist file. The bot will clean the list for YouTube.

=== 3. DASHBOARD TARGETING & URLs ===
You can target a playlist in two ways:
- BY NAME: Type a name. If it does not exist, the bot creates it.
- BY URL: Paste the full YouTube Playlist URL directly into the text box. The bot will automatically extract the ID and resume syncing to that exact playlist.

=== 4. MANUAL PERFECTION ===
If the bot picks the wrong version of a song:
1. Go to the Manual Override tab.
2. Search for the song title to find its exact Number from your list.
3. Paste the correct YouTube Video ID.
4. Click Save. The bot will prioritize this link forever.

=== 5. ERROR GLOSSARY ===
- '401 Unauthorized': Your session expired. You need to redo the F12 Headers.
- 'Format Error': Ensure you copied from 'Request Headers', not 'General'.
- 'Gaps Detected': Run the Sync Engine again to let the bot fill any missed songs."""

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
        df = pd.read_csv("cleanlist.csv")
        match = df[df['Title'].str.lower().str.contains(query, na=False)]
        if not match.empty:
            res = match.iloc[0]
            if alert_user("Confirm", f"Found: #{res['No']} - {res['Title']}. Is this correct?", is_choice=True) == 6:
                self.ov_no.delete(0, 'end'); self.ov_no.insert(0, str(res['No']))
        else: alert_user("Not Found", "No song found with that name.", is_error=True)

    def manual_save(self):
        n, u = self.ov_no.get(), self.ov_url.get()
        if n and u:
            with open("url.txt", "a", encoding="utf-8") as f: f.write(f'{n},"{u}"\n')
            alert_user("Success", f"Override Saved for Song #{n}.")

    def import_csv_logic(self):
        f = ctk.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if f:
            try:
                df = pd.read_csv(f, encoding='latin1')
                df.columns = [str(c).lower().strip() for c in df.columns]
                bt = next(c for c in df.columns if 'title' in c or 'track' in c)
                ba = next(c for c in df.columns if 'artist' in c or 'singer' in c)
                df = df.rename(columns={bt: 'Title', ba: 'Artist'})
                df.insert(0, 'No', range(1, len(df)+1))
                df[['No', 'Title', 'Artist']].to_csv("cleanlist.csv", index=False)
                alert_user("Success", "CSV Imported and Cleaned.")
            except: alert_user("Error", "Could not read columns.", is_error=True)

    def save_headers(self):
        raw = self.header_input.get("1.0", "end").strip()
        req = ["cookie", "user-agent", "accept", "authorization", "x-goog-authuser"]
        d = {}
        lines = [l.strip() for l in raw.split('\n') if l.strip()]
        for i in range(len(lines)):
            l = lines[i].lower().replace(':', '').strip()
            if l in req and i+1 < len(lines): d[l] = lines[i+1].strip()
            elif ':' in lines[i]:
                p = lines[i].split(':', 1)
                if p[0].strip().lower() in req: d[p[0].strip().lower()] = p[1].strip()
        if "cookie" in d:
            with open("browser.json", "w") as f: json.dump(d, f, indent=4)
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
            p_id = self.resolve_playlist_id(yt, p_input)
            if not p_id:
                print("Download Failed: Playlist not found.")
                return
            tracks = yt.get_playlist(p_id, limit=None).get('tracks', [])
            pd.DataFrame([{"No": i, "Title": t['title']} for i, t in enumerate(tracks, 1)]).to_csv("ostlist.csv", index=False)
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
            p_id = self.resolve_playlist_id(yt, p_input)
            if not p_id:
                print("Scan Failed: Playlist not found.")
                return
            yt_tracks = yt.get_playlist(p_id, limit=None).get('tracks', [])
            df_m = pd.read_csv("cleanlist.csv")
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

    def run_sync_logic(self):
        try:
            yt = YTMusic("browser.json"); df = pd.read_csv("cleanlist.csv")
            p_input = self.playlist_input.get().strip() or "Sync Hub Auto"
            p_id = self.resolve_playlist_id(yt, p_input)
            
            if not p_id:
                print(f"Creating new playlist: {p_input}")
                p_id = yt.create_playlist(p_input, "Sync")
                time.sleep(2)
            else:
                print(f"Targeting existing playlist ID: {p_id}")
            
            live_count = len(yt.get_playlist(p_id, limit=None).get('tracks', []))
            cache_map = {}
            if os.path.exists("url.txt"):
                with open("url.txt", "r") as f:
                    for l in f:
                        parts = l.strip().split(',')
                        if len(parts) >= 2: cache_map[int(parts[0])] = parts[1].replace('"', '')
            for k, v in MANUAL_OVERRIDES.items(): cache_map[k] = v

            for i in range(len(df)):
                while self.sync_state == "paused": time.sleep(1)
                if self.sync_state == "stopped": break
                m_no = int(df.iloc[i]['No'])
                if m_no <= live_count: continue
                
                vid = cache_map.get(m_no)
                if not vid:
                    s = yt.search(f"{df.iloc[i]['Artist']} {df.iloc[i]['Title']}", filter="songs")
                    if s: vid = s[0]['videoId']
                
                if vid:
                    yt.add_playlist_items(p_id, [vid])
                    with open("url.txt", "a") as f: f.write(f'{m_no},"{vid}"\n')
                    print(f"[{m_no}] ADDED: {df.iloc[i]['Title']}"); time.sleep(3.5)
            self.unlock_buttons()
        except Exception as e: print(f"Error: {e}"); self.unlock_buttons()

if __name__ == "__main__":
    app = UltimateSyncApp()
    app.mainloop()

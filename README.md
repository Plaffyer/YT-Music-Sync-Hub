# YT Music Sync Hub

An autonomous Python desktop application to synchronize local CSV playlists to YouTube Music. This tool allows you to import external playlists, convert browser authentication headers, and accurately scan or sync tracks to your live YouTube Music account using a customizable AI-matching engine.

## 🚀 Installation & Setup

To run this application locally, you will need Python installed on your machine. 

1. Clone or download this repository to your local machine.
2. Open your terminal in the project folder.
3. Install the required dependencies by running the following command:
   pip install customtkinter ytmusicapi pandas
4. Run the application:
   python app.py

📖 User Manual & Troubleshooting
1. What do these buttons do?
1. Dashboard: This is the main control room. Here you tell the bot where to put the songs, choose your strictness mode, and click "INITIATE SYNC ENGINE" to start adding songs. You can also click "SCAN PLAYLIST TARGET BOT" to autonomously download your live YouTube playlist and check it for missing or duplicate songs without adding anything new.

2. Data Import: This is where you upload your raw playlist file (CSV format) exported from Spotify/Apple. The application will clean it up and prepare it for the bot to read.

3. Authentication: This is where you give the bot the "VIP Pass" (F12 Headers) so it can securely log into your YouTube account to add songs.

2. Strict Mode vs Relaxed Mode
STRICT MODE (For Perfectionists): The bot verifies every song mathematically. If it is not 100 percent sure, it stops and alerts you. It also checks the YouTube server periodically to ensure perfect 1-to-1 order.

Best Workflow: If a song is wrong, the bot will pause. Delete the wrong song from your YouTube playlist manually, edit your cleanlist.csv to fix the tricky title, and restart the bot. If you delete your YouTube list to restart, the bot remembers safe songs in the url.txt cache and will rapid-fire add them back perfectly!

RELAXED MODE (For Casual Users): The bot will find the closest match it can and add it silently. It disables deep safety checks and will not stop if YouTube lags. It simply pushes through to the end.

3. Error Glossary & Fixes
"Ghost Add" Error: * What happened: YouTube servers lagged. The bot told YouTube to add a song, but YouTube did not save it.

Counter-measure: Manual deletion of the last few tracks and restart if you are a perfectionist, or run the Target Scanner later to find the specific gap.

"Authentication Error 401": * What happened: Your browser session expired. Google kicks bots out periodically for security.

Counter-measure: Go to the Authentication tab, grab fresh F12 Request Headers from your browser, paste them, and click convert.

"Not Found Error 404": * What happened: The playlist URL is wrong, or the playlist was deleted.

Counter-measure: Make sure you copied the correct URL, or just type a new name in the Dashboard to create a fresh one.

"Duplicate Error 409": * What happened: You tried to add the exact same song/video ID twice.

Counter-measure: Check your YouTube playlist. Delete duplicates manually.

"Low Accuracy Hard Stop" (Strict Mode Only): * What happened: The bot found a song, but the name was too different from your list. It blocked it to protect your list.

Counter-measure: Switch to Relaxed Mode to bypass it, OR open the app.py code and add the correct Video ID to the MANUAL_OVERRIDES memory bank so it automatically succeeds next time.

"Missing File Errors": * What happened: The bot cannot find cleanlist.csv or browser.json.

Counter-measure: If cleanlist is missing, go to Data Import and convert a file. If browser.json is missing, go to Authentication and convert your headers.

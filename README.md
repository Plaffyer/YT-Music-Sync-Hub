YT Music Sync Hub
An autonomous Python desktop application to synchronize local CSV playlists to YouTube Music. This tool allows you to import external playlists, convert browser authentication headers, and accurately scan or sync tracks to your live YouTube Music account using a customizable AI-matching engine.

🚀 Installation & Setup
To run this application locally, you will need Python installed on your machine.

Clone or download this repository to your local machine.

Open your terminal or command prompt in the project folder.

Install the required dependencies by running the following command:
pip install customtkinter ytmusicapi pandas

Run the application:
python app.py

🔑 Detailed Guide: How to Get Your Authentication Headers
The bot needs a "VIP Pass" to add songs to your account. Follow these exact steps to get it:

Open Google Chrome or Microsoft Edge on your computer.

Go to music.youtube.com and make sure you are logged in to your account.

Press F12 on your keyboard (or right-click anywhere and select Inspect).

Look at the top of the panel that opens and click the Network tab.

In the small "Filter" search box (usually at the top left of the network panel), type the word: browse

Press F5 on your keyboard to refresh the page.

You will see an item named browse appear in the list. Click it once.

A new section will open on the right. Look for a sub-heading called Request Headers.

Highlight and copy EVERYTHING inside the Request Headers section (start from the very top word "accept:" all the way down to the end of your long "cookie:" strings).

Open the Sync Hub app, go to the Authentication tab, paste that text, and click Convert.

📖 User Manual & Troubleshooting
1. What do these buttons do?
1. Dashboard: This is the main control room. Here you tell the bot where to put the songs, choose your strictness mode, and click "INITIATE SYNC ENGINE" to start adding songs. You can also click "SCAN PLAYLIST TARGET BOT" to autonomously download your live YouTube playlist and check it for missing or duplicate songs without adding anything new.

2. Data Import: This is where you upload your raw playlist file (CSV format) exported from Spotify/Apple. The application will clean it up and prepare it for the bot to read.

3. Authentication: This is where you give the bot the "VIP Pass" (F12 Headers) so it can securely log into your YouTube account to add songs.

2. Strict Mode vs Relaxed Mode
STRICT MODE (For Perfectionists): The bot verifies every song mathematically. If it is not 100 percent sure, it stops and alerts you. It also checks the YouTube server periodically to ensure perfect 1-to-1 order.

RELAXED MODE (For Casual Users): The bot will find the closest match it can and add it silently. It disables deep safety checks and will not stop if YouTube lags. It simply pushes through to the end.

3. Error Glossary & Fixes
"Ghost Add" Error: YouTube servers lagged. The bot told YouTube to add a song, but YouTube did not save it.

"Authentication Error 401": Your browser session expired. Grab fresh F12 Request Headers from your browser, paste them in the Auth tab, and click convert.

"Not Found Error 404": The playlist URL is wrong, or the playlist was deleted. Check the URL or create a new one.

"Duplicate Error 409": You tried to add the exact same song twice. Check your YouTube playlist and delete duplicates manually.

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

In the small "Filter" search box, type the word: browse

Press F5 on your keyboard to refresh the page.

You will see an item named browse appear in the list. Click it once.

A new section will open on the right. Look for a sub-heading called Request Headers.

Highlight and copy EVERYTHING inside the Request Headers section (from the very top word "accept:" all the way down to the end of your long "cookie:" strings).

Open the Sync Hub app, go to the Authentication tab, paste that text, and click Convert.

🛠 Contributing & Adjusting Code
This project is open-source. You are free to adjust, improve, or fix the code for your own needs.

For Personal Use: You can edit your local app.py file directly after downloading.

To Suggest Improvements: Please Fork this repository, make your changes, and submit a Pull Request. I welcome community improvements to the matching engine and UI!

Permissions: No one can edit the main files in this repository without my explicit approval. Your contributions will be reviewed before being merged.

📖 User Manual & Troubleshooting
1. What do these buttons do?
Dashboard: This is the main control room. Here you tell the bot where to put the songs, choose your strictness mode, and click "INITIATE SYNC ENGINE" to start adding songs. You can also click "SCAN PLAYLIST TARGET BOT" to autonomously download your live YouTube playlist and check it for missing or duplicate songs.

Data Import: This is where you upload your raw playlist file (CSV format) exported from Spotify/Apple. The application will clean it up and prepare it for the bot to read.

Authentication: This is where you give the bot the "VIP Pass" (F12 Headers) so it can securely log into your YouTube account.

2. Strict Mode vs Relaxed Mode
STRICT MODE (For Perfectionists): The bot verifies every song mathematically. If it is not 100 percent sure, it stops and alerts you. It also checks the YouTube server periodically to ensure perfect 1-to-1 order.

RELAXED MODE (For Casual Users): The bot will find the closest match it can and add it silently. It disables deep safety checks and will not stop if YouTube lags.

3. Error Glossary & Fixes
"Ghost Add" Error: YouTube servers lagged. The bot told YouTube to add a song, but YouTube did not save it. Run the Target Scanner to find the gap.

"Authentication Error 401": Your browser session expired. Grab fresh F12 Request Headers from your browser, paste them in the Auth tab, and click convert.

"Not Found Error 404": The playlist URL is wrong, or the playlist was deleted. Check the URL or create a new one.

"Duplicate Error 409": You tried to add the exact same song twice. Check your YouTube playlist and delete duplicates manually.

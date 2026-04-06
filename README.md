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

⚡ Tip: One-Click Launcher (Windows)
I have included a file named Run_Sync_Hub.bat in this repository for your convenience.

Once you have installed the dependencies (Step 3 above), you can simply double-click Run_Sync_Hub.bat to launch the app instantly without opening a terminal!

🔑 Detailed Guide: How to Get Your Authentication Headers
The bot needs a "VIP Pass" to add songs to your account. Follow these exact steps to get it:

Open Google Chrome or Microsoft Edge and go to music.youtube.com (ensure you are logged in).

Press F12 on your keyboard (or right-click anywhere and select Inspect).

Click the Network tab at the top of the panel.

In the small "Filter" search box, type the word: browse

Press F5 to refresh the page.

Click the first browse item that appears in the list.

Look for a sub-heading called Request Headers.

Highlight and copy EVERYTHING inside the Request Headers section (from "accept:" down to the end of your long "cookie:" strings).

Open the Sync Hub app, go to the Authentication tab, paste that text, and click Convert.

🛠 Contributing & Adjusting Code
This project is open-source. You are free to adjust, improve, or fix the code for your own needs.

For Personal Use: You can edit your local app.py file directly after downloading.

To Suggest Improvements: Please Fork this repository, make your changes, and submit a Pull Request.

Permissions: No one can edit the main files in this repository without my explicit approval. Your contributions will be reviewed before being merged.

📖 User Manual & Troubleshooting
1. What do these buttons do?
Dashboard: The main control room. Here you tell the bot where to put the songs, choose your mode, and click "INITIATE SYNC ENGINE". You can also click "SCAN PLAYLIST TARGET BOT" to check your live playlist for gaps.

Data Import: Upload your raw CSV file (Spotify/Apple export). The app will format it for the bot.

Authentication: Converts your browser headers into a secure login token.

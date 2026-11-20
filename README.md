# 🎬 Cast Call

A movie-guessing game for phones and iPads. A random film from the IMDb top 10,000 is picked and its top 10 billed actors are hidden. Guess the movie as the cast is revealed one name at a time.

## Rules
- Start with **1000 points** and **10 guesses**.
- Each wrong guess costs **100 points** and reveals the next actor.
- Hints cost **50 points** each: genre, release year, director, letter pattern (`The Terminator` → `*** **********`).
- Win or lose, the movie poster is revealed.

Guesses ignore case, accents, punctuation and a leading "The/A/An", and the box autocompletes titles. Stats and streaks are saved on the device.

## Put it on GitHub Pages
1. Create a new repository on GitHub and upload everything in this folder (keep the `.github` and `tools` folders).
2. **Settings → Pages → Build and deployment**: Source = *Deploy from a branch*, Branch = `main`, folder `/ (root)`. Save.
3. After a minute the game is live at `https://<your-username>.github.io/<repo-name>/`.
4. On iPhone/iPad, open it in Safari → Share → **Add to Home Screen** for a full-screen app icon.

## Load the full IMDb top 10,000
The repo ships with a 60-film starter list so it works right away. To get the full list:

**Easiest (no software needed):** in your repo go to **Actions → Build movie list → Run workflow**. It downloads IMDb's official datasets, builds `movies.js` with 10,000 films, and commits it. Pages redeploys automatically. It also refreshes monthly.

**Or locally:** `python3 tools/build_movies.py` (Python 3.8+, no packages needed; downloads ~1.5 GB of IMDb files).

Options: `--count 5000`, `--sort rating` (rank by IMDb rating instead of number of votes), `--min-votes 25000`.

"Top 10,000" defaults to the 10,000 feature films with the most IMDb votes, which keeps the picks recognizable. Rating-based ranking tends to surface more obscure films.

## Notes
- Posters come from Wikipedia (looked up by IMDb ID through Wikidata), so no API key is needed. If none is found, a title card is shown.
- Movie data is from [IMDb Non-Commercial Datasets](https://developer.imdb.com/non-commercial-datasets/) and is for personal, non-commercial use.

#!/usr/bin/env python3

# v3.0 print_playlist stable
# v3.1 print_playlist + download
# v3.2 print_playlist + download single video stable
# v3.3 print_playlist + download single video + detect if download playlist
# v3.4 print_playlist + download playlist using download_audio()

import yt_dlp
import sys
import os

def print_playlist(url, download=False):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    print("\n" + "="*100)
    print(f"PLAYLIST : {info['title']}")
    print(f"URL      : {url}")
    print(f"Videos   : {len(info['entries'])}")
    print(f"Uploader : {info.get('uploader', 'N/A')}")
    if info.get('description'):
        desc = info['description'][:150]
        print(f"Desc     : {desc}{'...' if len(info['description']) > 150 else ''}")
    print("="*100)

    print(f"{'#':>3} {'Title':50} {'Dur':>6} {'Views':>12} {'URL'}")
    print("-"*140)

    for i, entry in enumerate(info['entries'], 1):
        title = (entry['title'][:47] + "...") if len(entry['title']) > 50 else entry['title']
        duration = entry.get('duration', 0)
        if duration:
            h, rem = divmod(duration, 3600)
            m, s = divmod(rem, 60)
            duration_str = f"{h:02d}:{m:02d}:{s:02d}".lstrip("0:")
        else:
            duration_str = "N/A"
        views = f"{entry.get('view_count', 'N/A'):,}" if entry.get('view_count') else "N/A"
        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
        print(f"{i:3} {title:50} {duration_str:>6} {views:>12} {video_url}")

    print("\nDone. All video links included.\n")

    # === If download flag is set, download each video ===
    if download:
        folder = "".join(c for c in info['title'] if c.isalnum() or c in " _-").rstrip() or "downloads"
        print(f"\nStarting download of all videos to folder: {folder}\n")
        for i, entry in enumerate(info['entries'], 1):
            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
            print(f"[{i}/{len(info['entries'])}] Downloading: {entry['title']}")
            download_audio(video_url, folder)
        print("\nAll videos downloaded.\n")

def download_audio(url, folder=None):
    # === Folder logic ===
    if folder is None or folder.strip() == "":
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        folder = info['title'] if 'entries' in info else "downloads"
    folder = "".join(c for c in folder if c.isalnum() or c in " _-").rstrip() or "downloads"

    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder: {folder}")

    # === TRY OPUS AUDIO FIRST ===
    opus_opts = {
        'format': 'bestaudio[ext=opus]/bestaudio/best',
        'outtmpl': f'{folder}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '192',
        }],
    }

    print(f"Trying highest quality Opus audio from:\n  {url}\n  → Folder: {folder}")
    try:
        with yt_dlp.YoutubeDL(opus_opts) as ydl:
            ydl.download([url])
        print("Opus download complete.\n")
        return  # Success → exit function
    except Exception as e:
        print(f"Opus failed: {e}")
        print("Falling back to best video format (MP4 with audio)...\n")

    # === FALLBACK: BEST VIDEO (MP4) ===
    fallback_opts = {
        'format': 'best',
        'outtmpl': f'{folder}/%(title)s.%(ext)s',
    }

    try:
        with yt_dlp.YoutubeDL(fallback_opts) as ydl:
            ydl.download([url])
        print("Fallback MP4 download complete.\n")
    except Exception as e2:
        print(f"Both methods failed: {e2}")
        print("Tip: Update yt-dlp (`pip install -U yt-dlp`) or use a different network.\n")

# ================================
# MAIN
# ================================
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python script.py print_playlist <PLAYLIST_URL>")
        print("  python script.py download <VIDEO_OR_PLAYLIST_URL> [FOLDER]")
        print("")
        print("Examples:")
        print("  python script.py print_playlist https://www.youtube.com/playlist?list=PLUmH0L_sg7seUfFE8S4APqYaXLPphzsxp")
        print("  python script.py download https://www.youtube.com/watch?v=fE72QTm2z-4")
        sys.exit(1)

    action = sys.argv[1]
    url = sys.argv[2]
    folder = sys.argv[3] if len(sys.argv) > 3 else None

    if action == "print_playlist":
        if not url.startswith("http"):
            print("Error: URL must start with http/https")
            sys.exit(1)
        print_playlist(url)

    elif action == "download":
        if not url.startswith("http"):
            print("Error: URL must start with http/https")
            sys.exit(1)

        # === SIMPLE URL CHECK ===
        if "playlist" in url.lower():
            print("PLAYLIST DETECTED (by URL). Starting download...\n")
            print_playlist(url, download=True)
            sys.exit(0)
        else:
            print("VIDEO DETECTED (by URL). Starting download...\n")
            download_audio(url, folder)

    else:
        print(f"Unknown action: {action}")
        print("Use: print_playlist or download")
        sys.exit(1)
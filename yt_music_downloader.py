#!/usr/bin/env python3

# v3.0 print_playlist stable
# v3.1 print_playlist + download
# v3.2 print_playlist + download single video stable
# v3.3 print_playlist + download single video + detect if download playlist
# v3.4 print_playlist + download playlist using download_audio()
# v3.5 skip existing .opus or .mp4 files in playlist folder
# v3.6.0 print_playlist + check existing files, show Video ID and Exists column
# v3.6.1 check existing files + --dryrun support
# v3.6.2 minor fix to move download section to later position
# v3.6.3 fix --dryrun message, prevent actual downloading in dryrun (Stable Build)


import yt_dlp
import sys
import os

def print_playlist(url, download=False, dryrun=False):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    playlist_name = info['title']

    print("\n" + "="*100)
    print(f"PLAYLIST : {playlist_name}")
    print(f"URL      : {url}")
    print(f"Videos   : {len(info['entries'])}")
    print(f"Uploader : {info.get('uploader', 'N/A')}")
    if info.get('description'):
        desc = info['description'][:150]
        print(f"Desc     : {desc}{'...' if len(info['description']) > 150 else ''}")
    print("="*100)

    print(f"{'#':>3} {'Title':50} {'Dur':>6} {'Views':>12} {'Video ID':12} {'Exists':>7}")
    print("-"*140)

    tracks = []
    for i, entry in enumerate(info['entries'], 1):
        track_name = (entry['title'][:47] + "...") if len(entry['title']) > 50 else entry['title']
        duration = entry.get('duration', 0)
        if duration:
            h, rem = divmod(duration, 3600)
            m, s = divmod(rem, 60)
            duration_str = f"{h:02d}:{m:02d}:{s:02d}".lstrip("0:")
        else:
            duration_str = "N/A"
        views = f"{entry.get('view_count', 'N/A'):,}" if entry.get('view_count') else "N/A"
        video_id = entry['id']

        folder = "".join(c for c in playlist_name if c.isalnum() or c in " _-").rstrip() or "downloads"
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename_opus = os.path.join(folder, f"{track_name}.opus")
        filename_mp4 = os.path.join(folder, f"{track_name}.mp4")
        exists = os.path.exists(filename_opus) or os.path.exists(filename_mp4)
        exists_str = "Yes" if exists else "No"

        # debug info
        # print(f"DEBUG: folder='{folder}', track='{track_name}', exists={exists}")

        print(f"{i:3} {track_name:50} {duration_str:>6} {views:>12} {video_id:12} {exists_str:>7}")
        tracks.append({'track_no': i, 'track_name': track_name, 'video_id': video_id, 'exists': exists})

    print("\nDone. All video links included.\n")

    if download:
        for t in tracks:
            video_url = f"https://www.youtube.com/watch?v={t['video_id']}"
            if t['exists']:
                print(f"[{t['track_no']}/{len(tracks)}] {t['track_name']} Exists → Skipped")
                continue
            if dryrun:
                print(f"[{t['track_no']}/{len(tracks)}] {t['track_name']} Would download (dryrun)")
                continue
            print(f"\n[{t['track_no']}/{len(tracks)}] {t['track_name']} Downloading...")
            download_audio(video_url, folder)

def download_audio(url, folder=None):
    if folder is None or folder.strip() == "":
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        folder = info['title'] if 'entries' in info else "downloads"
    folder = "".join(c for c in folder if c.isalnum() or c in " _-").rstrip() or "downloads"
    if not os.path.exists(folder):
        os.makedirs(folder)

    opus_opts = {
        'format': 'bestaudio[ext=opus]/bestaudio/best',
        'outtmpl': f'{folder}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(opus_opts) as ydl:
            ydl.download([url])
        return
    except:
        fallback_opts = {
            'format': 'best',
            'outtmpl': f'{folder}/%(title)s.%(ext)s',
        }
        with yt_dlp.YoutubeDL(fallback_opts) as ydl:
            ydl.download([url])

# ================================
# MAIN
# ================================
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python yt_music_downloader.py print_playlist <PLAYLIST_URL> [--dryrun]")
        print("  python yt_music_downloader.py download <VIDEO_OR_PLAYLIST_URL> [FOLDER] [--dryrun]")
        sys.exit(1)

    action = sys.argv[1]
    url = sys.argv[2]
    dryrun = "--dryrun" in sys.argv
    folder = None
    for arg in sys.argv[3:]:
        if arg != "--dryrun":
            folder = arg

    if action == "print_playlist":
        if not url.startswith("http"):
            print("Error: URL must start with http/https")
            sys.exit(1)
        print_playlist(url, dryrun=dryrun)

    elif action == "download":
        if not url.startswith("http"):
            print("Error: URL must start with http/https")
            sys.exit(1)
        if "playlist" in url.lower():
            print_playlist(url, download=True, dryrun=dryrun)
        else:
            if dryrun:
                print("DRYRUN → Would download single video (no actual download).\n")
            else:
                download_audio(url, folder)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

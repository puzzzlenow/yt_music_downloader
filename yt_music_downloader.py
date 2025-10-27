#!/usr/bin/env python3

# v3.0 print_playlist stable
# v3.1 print_playlist + download
# v3.2 print_playlist + download single video stable
# v3.3 print_playlist + download single video + detect if download playlist
# v3.4 print_playlist + download playlist using download_audio()
# v3.5 skip existing .opus or .m4a files in playlist folder
# v3.6.0 print_playlist + check existing files, show Video ID and Exists column
# v3.6.1 check existing files + --dryrun support
# v3.6.2 minor fix to move download section to later position
# v3.6.3 fix --dryrun message, prevent actual downloading in dryrun (Stable Build)
# v3.7.0 naming convention: Artist/Album/TrackNumber - TrackTitle
# v3.8.0 native Opus (251) with fallback to native M4a (140), consistent folder structure
# v3.9.0 use --action for print_playlist/download
# v3.9.1 ensure .opus/.m4a extensions without postprocessing
# v3.9.2 use --url and --folder arguments
# v3.9.3 remove artist name prefix from album and track names

import yt_dlp
import argparse
import os
import re

def remove_artist_prefix(text, artist_name):
    """Remove artist name prefix from text if present at the beginning."""
    if not artist_name or not text:
        return text
    # Create a case-insensitive regex pattern for the artist name followed by common separators
    pattern = re.compile(r'^' + re.escape(artist_name) + r'\s*[-:]\s*', re.IGNORECASE)
    return pattern.sub('', text).strip()

def print_playlist(url, download=False, dryrun=False, custom_folder=None):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    playlist_name = info['title']
    artist_name = info.get('uploader', 'Unknown Artist')
    # Remove artist name prefix from playlist name
    clean_playlist_name = remove_artist_prefix(playlist_name, artist_name)

    print("\n" + "="*100)
    print(f"PLAYLIST : {clean_playlist_name}")
    print(f"URL      : {url}")
    print(f"Videos   : {len(info['entries'])}")
    print(f"Uploader : {artist_name}")
    if info.get('description'):
        desc = info['description'][:150]
        print(f"Desc     : {desc}{'...' if len(info['description']) > 150 else ''}")
    print("="*100)

    print(f"{'#':>3} {'Title':50} {'Dur':>6} {'Views':>12} {'Video ID':12} {'Exists':>7}")
    print("-"*140)

    tracks = []
    for i, entry in enumerate(info['entries'], 1):
        track_name = entry['title']
        # Remove artist name prefix from track name
        clean_track_name = remove_artist_prefix(track_name, artist_name)
        # Truncate for display only
        display_track_name = (clean_track_name[:47] + "...") if len(clean_track_name) > 50 else clean_track_name
        duration = entry.get('duration', 0)
        if duration:
            h, rem = divmod(duration, 3600)
            m, s = divmod(rem, 60)
            duration_str = f"{h:02d}:{m:02d}:{s:02d}".lstrip("0:")
        else:
            duration_str = "N/A"
        views = f"{entry.get('view_count', 'N/A'):,}" if entry.get('view_count') else "N/A"
        video_id = entry['id']

        # Folder structure: Use custom_folder if provided, else Artist/Album
        album_name = "".join(c for c in clean_playlist_name if c.isalnum() or c in " _-").rstrip() or "Unknown Album"
        folder = custom_folder if custom_folder else os.path.join(artist_name, album_name)
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Filename: TrackNumber - CleanTrackTitle
        track_filename = f"{i:02d} - {clean_track_name}"
        filename_opus = os.path.join(folder, f"{track_filename}.opus")
        filename_m4a = os.path.join(folder, f"{track_filename}.m4a")
        exists = os.path.exists(filename_opus) or os.path.exists(filename_m4a)
        exists_str = "Yes" if exists else "No"

        print(f"{i:3} {display_track_name:50} {duration_str:>6} {views:>12} {video_id:12} {exists_str:>7}")
        tracks.append({'track_no': i, 'track_name': clean_track_name, 'video_id': video_id, 'exists': exists})

    print("\nDone. All video links included.\n")

    if download:
        for t in tracks:
            video_url = f"https://www.youtube.com/watch?v={t['video_id']}"
            if t['exists']:
                print(f"[{t['track_no']}/{len(tracks)}] {t['track_name']} → Exists → Skipped")
                continue
            if dryrun:
                print(f"[{t['track_no']}/{len(tracks)}] {t['track_name']} → Would download (dryrun)")
                continue
            print(f"\n[{t['track_no']}/{len(tracks)}] {t['track_name']} → Downloading...")
            download_audio(video_url, folder, t['track_no'], t['track_name'])

def download_audio(url, folder=None, track_no=None, track_name=None):
    # For single videos, fetch metadata to determine artist and playlist (video title)
    if folder is None or folder.strip() == "":
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        artist_name = info.get('uploader', 'Unknown Artist')
        playlist_name = info['title'] if 'entries' not in info else "downloads"
        clean_playlist_name = remove_artist_prefix(playlist_name, artist_name)
        album_name = "".join(c for c in clean_playlist_name if c.isalnum() or c in " _-").rstrip() or "Unknown Album"
        folder = os.path.join(artist_name, album_name)

    # Ensure folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Construct filename with track number and name if provided (for playlists)
    if track_no is not None and track_name is not None:
        track_filename = f"{track_no:02d} - {track_name}"
    else:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        artist_name = info.get('uploader', 'Unknown Artist')
        track_name = remove_artist_prefix(info['title'], artist_name)
        track_filename = f"01 - {track_name}"

    opus_opts = {
        'format': '251/bestaudio/best',  # Native Opus (format 251)
        'outtmpl': f'{folder}/{track_filename}.opus',  # Force .opus extension
    }

    try:
        with yt_dlp.YoutubeDL(opus_opts) as ydl:
            ydl.download([url])
        print(f"Downloaded native Opus (format 251) to {folder}/{track_filename}.opus")
        return
    except Exception as e:
        print(f"Failed to download native Opus (format 251): {e}")
        fallback_opts = {
            'format': '140/best',  # Native M4a (format 140)
            'outtmpl': f'{folder}/{track_filename}.m4a',  # Force .m4a extension
        }
        print("Retrying with format 140 (M4a)...")
        with yt_dlp.YoutubeDL(fallback_opts) as ydl:
            ydl.download([url])
        print(f"Downloaded native M4a (format 140) to {folder}/{track_filename}.m4a")

# ================================
# MAIN
# ================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Music Downloader")
    parser.add_argument("--action", choices=["print_playlist", "download"], required=True,
                        help="Action to perform: print_playlist or download")
    parser.add_argument("--url", required=True, help="YouTube playlist or video URL")
    parser.add_argument("--folder", default=None, help="Optional output folder (overrides default for single videos or playlists)")
    parser.add_argument("--dryrun", action="store_true", help="Simulate actions without downloading")

    args = parser.parse_args()

    if not args.url.startswith("http"):
        print("Error: URL must start with http/https")
        sys.exit(1)

    if args.action == "print_playlist":
        print_playlist(args.url, download="download" in sys.argv, dryrun=args.dryrun, custom_folder=args.folder)

    elif args.action == "download":
        if "playlist" in args.url.lower():
            print_playlist(args.url, download=True, dryrun=args.dryrun, custom_folder=args.folder)
        else:
            if args.dryrun:
                print("DRYRUN → Would download single video (no actual download).\n")
            else:
                # Fetch metadata for single video
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(args.url, download=False)
                artist_name = info.get('uploader', 'Unknown Artist')
                track_name = remove_artist_prefix(info['title'], artist_name)
                track_name = (track_name[:47] + "...") if len(track_name) > 50 else track_name
                print(f"Downloading single video: {track_name}")
                download_audio(args.url, args.folder, track_no=1, track_name=track_name)
# -------------------------------------------------------
# example
# -------------------------------------------------------
# yt_music_downloader.py --action download --url https://www.youtube.com/playlist?list=PLsCPTY_MPoPZLKsjasPhYLuoWG-s-rdKq
#
#
#

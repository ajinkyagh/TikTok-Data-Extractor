import argparse
import logging
from datetime import datetime

from dotenv import load_dotenv

from tiktok_extractor import TikTokMaxDataExtractor, load_credentials


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TikTok data extraction.")
    parser.add_argument("--username", required=True, help="TikTok username")
    parser.add_argument("--max-videos", type=int, default=10)
    parser.add_argument("--days-back", type=int, default=90)
    parser.add_argument("--include-comments", action="store_true")
    parser.add_argument("--max-videos-for-comments", type=int, default=10)
    parser.add_argument("--max-comments-per-video", type=int, default=30)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_dotenv()

    creds = load_credentials()
    extractor = TikTokMaxDataExtractor(creds)

    if not extractor.get_token():
        raise RuntimeError("Failed to obtain access token")

    args = parse_args()

    all_data = extractor.extract_all_data(
        username=args.username,
        max_videos=args.max_videos,
        days_back=args.days_back,
        include_comments=args.include_comments,
        max_videos_for_comments=args.max_videos_for_comments,
        max_comments_per_video=args.max_comments_per_video,
        include_followers=True,
        include_following=True,
        include_liked_videos=True,
        include_pinned_videos=True,
        include_reposted_videos=True,
    )

    filename = f"{args.username}_FULL_DATA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    extractor.save_json(all_data, filename)
    extractor.log_daily_usage()

    print("\nDATA SUMMARY:")
    profile = (all_data.get("profile") or {}).get("data", {})
    if profile:
        print(f"Username: @{args.username}")
        print(f"Display Name: {profile.get('display_name', 'N/A')}")
        print(f"Followers: {profile.get('follower_count', 0):,}")
        print(f"Videos: {profile.get('video_count', 0):,}")

    videos = (all_data.get("videos") or {}).get("data", {}).get("videos", [])
    print(f"Videos extracted: {len(videos)}")

    comments = all_data.get("comments") or {}
    total_comments = sum(len(c.get("data", {}).get("comments", [])) for c in comments.values())
    print(f"Comments extracted: {total_comments}")


if __name__ == "__main__":
    main()

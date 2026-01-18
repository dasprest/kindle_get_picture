#!/usr/bin/env python3
import argparse
import asyncio
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, Set

from playwright.async_api import async_playwright, Response


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sign in to Kindle Web Reader, load pages as HTML, "
            "and download all images found while paging through the book."
        )
    )
    parser.add_argument("--url", required=True, help="Kindle Web Reader URL")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to store HTML and downloaded images",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (not recommended for login)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=300,
        help="Maximum number of page turns to attempt",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay (seconds) after each page turn",
    )
    parser.add_argument(
        "--stop-unchanged",
        type=int,
        default=3,
        help="Stop after this many consecutive unchanged page hashes",
    )
    return parser.parse_args()


def guess_extension(content_type: str, url: str) -> str:
    if content_type:
        extension = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if extension:
            return extension
    suffix = Path(url).suffix
    return suffix if suffix else ".img"


def build_paths(output_dir: Path) -> Dict[str, Path]:
    html_dir = output_dir / "html"
    image_dir = output_dir / "images"
    html_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    return {"html": html_dir, "images": image_dir}


async def save_response_images(
    response: Response,
    image_dir: Path,
    saved_hashes: Set[str],
) -> None:
    request = response.request
    if request.resource_type != "image":
        return
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        return
    body = await response.body()
    if not body:
        return
    digest = hashlib.sha256(body).hexdigest()
    if digest in saved_hashes:
        return
    saved_hashes.add(digest)
    extension = guess_extension(content_type, response.url)
    filename = f"{digest[:16]}{extension}"
    (image_dir / filename).write_bytes(body)


async def save_frame_html(page_index: int, html_dir: Path, contents: Dict[str, str]) -> str:
    combined = hashlib.sha256()
    for name, html in contents.items():
        safe_name = name.replace("://", "_").replace("/", "_")
        file_path = html_dir / f"page_{page_index:04d}_{safe_name}.html"
        file_path.write_text(html, encoding="utf-8")
        combined.update(html.encode("utf-8"))
    return combined.hexdigest()


async def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    paths = build_paths(output_dir)
    saved_hashes: Set[str] = set()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(output_dir / "browser_profile"),
            headless=args.headless,
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        page.on(
            "response",
            lambda response: asyncio.create_task(
                save_response_images(response, paths["images"], saved_hashes)
            ),
        )

        await page.goto(args.url, wait_until="networkidle")
        print("Please sign in to Kindle and open the book in the browser window.")
        input("When the first page is visible, press Enter to start capture...")

        unchanged_count = 0
        last_hash = ""
        for page_index in range(1, args.max_pages + 1):
            frame_contents = {}
            for frame in page.frames:
                try:
                    frame_contents[frame.url or f"frame_{frame.name}"] = await frame.content()
                except Exception:
                    continue
            current_hash = await save_frame_html(page_index, paths["html"], frame_contents)

            if current_hash == last_hash:
                unchanged_count += 1
            else:
                unchanged_count = 0
                last_hash = current_hash

            if unchanged_count >= args.stop_unchanged:
                print("No page changes detected. Stopping capture.")
                break

            await page.keyboard.press("ArrowRight")
            await page.wait_for_timeout(args.delay * 1000)

        print(f"Downloaded {len(saved_hashes)} images into {paths['images']}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

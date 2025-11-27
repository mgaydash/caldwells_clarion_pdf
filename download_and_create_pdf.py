#!/usr/bin/env python3
"""
Download images from a URL pattern and compile them into a PDF.
Handles download failures and stops after consecutive 404 errors.
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
import time


class ImageDownloader:
    def __init__(self, base_url, pattern, output_dir="downloaded_images", max_consecutive_404s=5):
        """
        Initialize the image downloader.

        Args:
            base_url: Base URL for the images
            pattern: Pattern for constructing URLs (use {number} as placeholder)
            output_dir: Directory to save downloaded images
            max_consecutive_404s: Stop after this many consecutive 404 errors
        """
        self.base_url = base_url
        self.pattern = pattern
        self.output_dir = Path(output_dir)
        self.max_consecutive_404s = max_consecutive_404s
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)

    def download_images(self, start=1, expected_count=None):
        """
        Download images starting from start number until consecutive 404s are hit.

        Args:
            start: Starting number for the sequence
            expected_count: Expected number of images (for progress indication)

        Returns:
            List of successfully downloaded image paths
        """
        downloaded_files = []
        consecutive_404s = 0
        current = start

        print(f"Starting download from image {start}...")
        print(f"Will stop after {self.max_consecutive_404s} consecutive 404 errors\n")

        while consecutive_404s < self.max_consecutive_404s:
            url = f"{self.base_url}{self.pattern.format(number=current)}"
            filename = self.output_dir / f"image_{current:06d}.jp2"

            try:
                print(f"Downloading image {current}...", end=" ")
                response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    # Save the image
                    with open(filename, 'wb') as f:
                        f.write(response.content)

                    downloaded_files.append(filename)
                    consecutive_404s = 0  # Reset counter on success
                    print(f"✓ Success ({len(downloaded_files)} total)")

                elif response.status_code == 404:
                    consecutive_404s += 1
                    print(f"✗ Not found (404) - {consecutive_404s}/{self.max_consecutive_404s} consecutive")

                else:
                    print(f"✗ HTTP {response.status_code}")
                    # Don't count non-404 errors as consecutive failures

            except requests.exceptions.Timeout:
                print(f"✗ Timeout")
            except requests.exceptions.RequestException as e:
                print(f"✗ Error: {e}")

            current += 1
            time.sleep(0.5)  # Be nice to the server

        print(f"\nDownload complete! Successfully downloaded {len(downloaded_files)} images.")
        return downloaded_files

    def get_existing_images(self):
        """
        Get list of existing images in the output directory.

        Returns:
            Sorted list of image file paths
        """
        image_files = sorted(self.output_dir.glob("*.jp2"))
        print(f"Found {len(image_files)} existing images in {self.output_dir}/")
        return image_files

    def create_pdf(self, image_files, output_pdf="output.pdf", max_dimension=2000, jpeg_quality=85):
        """
        Create a PDF from the downloaded images with compression.

        Args:
            image_files: List of image file paths
            output_pdf: Output PDF filename
            max_dimension: Maximum width or height (images will be downscaled if larger)
            jpeg_quality: JPEG compression quality (1-100, higher = better quality)
        """
        if not image_files:
            print("No images to convert to PDF!")
            return

        print(f"\nCreating PDF from {len(image_files)} images...")
        print(f"Compression settings: max_dimension={max_dimension}px, quality={jpeg_quality}")

        # Convert JP2 images to PIL Images with compression
        images = []
        total_original_size = 0
        total_compressed_size = 0

        for i, img_path in enumerate(image_files, 1):
            try:
                print(f"Processing image {i}/{len(image_files)}...", end="\r")
                img = Image.open(img_path)
                original_size = img.size

                # Track original size
                total_original_size += img_path.stat().st_size

                # Resize if image is too large
                if img.width > max_dimension or img.height > max_dimension:
                    ratio = min(max_dimension / img.width, max_dimension / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                # Convert to RGB if necessary (PDFs need RGB)
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Pre-compress to JPEG in memory to reduce PDF size
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=jpeg_quality, optimize=True)
                total_compressed_size += buffer.tell()
                buffer.seek(0)
                img = Image.open(buffer)

                images.append(img)
            except Exception as e:
                print(f"\nWarning: Could not process {img_path}: {e}")

        if not images:
            print("No valid images to create PDF!")
            return

        # Calculate compression ratio
        if total_original_size > 0:
            compression_ratio = (1 - total_compressed_size / total_original_size) * 100
            print(f"\nImage compression: {compression_ratio:.1f}% reduction")
            print(f"  Original: {total_original_size / 1024 / 1024:.2f} MB")
            print(f"  Compressed: {total_compressed_size / 1024 / 1024:.2f} MB")

        # Save as PDF
        output_path = Path(output_pdf)
        print(f"\nSaving PDF to {output_path}...")

        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            resolution=100.0,
            quality=jpeg_quality,
            optimize=True
        )

        print(f"✓ PDF created successfully: {output_path}")
        print(f"  File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Download images from a URL pattern and create a PDF"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading, use existing images in downloaded_images/ directory"
    )
    parser.add_argument(
        "--output-dir",
        default="downloaded_images",
        help="Directory for downloaded images (default: downloaded_images)"
    )
    parser.add_argument(
        "--output-pdf",
        default="library_of_congress_images.pdf",
        help="Output PDF filename (default: library_of_congress_images.pdf)"
    )
    parser.add_argument(
        "--max-dimension",
        type=int,
        default=2000,
        help="Maximum image dimension in pixels (default: 2000)"
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        choices=range(1, 101),
        metavar="1-100",
        help="JPEG quality 1-100 (default: 85)"
    )
    args = parser.parse_args()

    # Configuration
    BASE_URL = "https://tile.loc.gov/storage-services/service/gmd/gmd382m/g3823m/g3823cm/gct00034/"
    PATTERN = "ca{number:06d}.jp2"  # ca000001.jp2, ca000002.jp2, etc.
    EXPECTED_COUNT = 162

    # Create downloader
    downloader = ImageDownloader(
        base_url=BASE_URL,
        pattern=PATTERN,
        output_dir=args.output_dir,
        max_consecutive_404s=5
    )

    # Get images (either download or use existing)
    if args.skip_download:
        print("Skipping download, using existing images...\n")
        image_files = downloader.get_existing_images()
        if not image_files:
            print(f"No images found in {args.output_dir}/")
            print("Run without --skip-download to download images first.")
            sys.exit(1)
    else:
        # Download images
        image_files = downloader.download_images(
            start=1,
            expected_count=EXPECTED_COUNT
        )
        if not image_files:
            print("No images were downloaded. Cannot create PDF.")
            sys.exit(1)

    # Create PDF
    downloader.create_pdf(
        image_files,
        output_pdf=args.output_pdf,
        max_dimension=args.max_dimension,
        jpeg_quality=args.quality
    )


if __name__ == "__main__":
    main()

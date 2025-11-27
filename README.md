# Library of Congress Image Downloader & PDF Creator

A Python tool to download images from the Library of Congress and compile them into a single PDF document.

## Background

My grandmother has a hard-copy of this document, and I was interested in having a digital copy. Unfortunately, I wasn't able to find a simple PDF version available online, so I created this tool to download the individual page images from the Library of Congress and compile them into a PDF.

The Library of Congress provides access to digitized historical documents as individual JP2 images, but viewing them requires navigating through pages one at a time. This tool automates the process of downloading all pages and creating a convenient PDF for easier viewing and archival.

## Features

- **Smart downloading** with automatic URL pattern detection
- **Error handling** for missing or inconsistent URLs
- **Automatic stop detection** after consecutive 404 errors
- **Image compression** to reduce PDF file size without significant quality loss
- **Configurable quality settings** to balance file size and image quality
- **Reusable processing** - download once, generate PDFs with different settings
- **Progress tracking** with real-time status updates

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Download images and create PDF (default)

```bash
python download_and_create_pdf.py
```

This will:
1. Download all images to `downloaded_images/` directory
2. Create `library_of_congress_images.pdf` with compressed images

### Process existing images without downloading

```bash
python download_and_create_pdf.py --skip-download
```

Useful for re-generating the PDF with different compression settings.

### Custom compression settings

```bash
# Higher quality, larger file
python download_and_create_pdf.py --skip-download --quality 95 --max-dimension 3000

# More compression, smaller file
python download_and_create_pdf.py --skip-download --quality 70 --max-dimension 1500
```

### All available options

```bash
python download_and_create_pdf.py --help
```

Options:
- `--skip-download` - Use existing images instead of downloading
- `--output-dir DIR` - Directory for downloaded images (default: `downloaded_images`)
- `--output-pdf FILE` - Output PDF filename (default: `library_of_congress_images.pdf`)
- `--max-dimension N` - Max image dimension in pixels (default: `2000`)
- `--quality N` - JPEG quality 1-100 (default: `85`)

## How It Works

1. **URL Pattern Detection**: The script uses the URL pattern from the Library of Congress tile service
2. **Sequential Download**: Downloads images starting from page 1, incrementing the page number
3. **Smart Stopping**: Stops after 5 consecutive 404 errors to handle URL pattern changes
4. **Image Processing**: Converts JP2 images to compressed JPEG format
5. **PDF Generation**: Combines all images into a single multi-page PDF

## Example Workflow

```bash
# First time: Download all images
python download_and_create_pdf.py

# Later: Generate a high-quality version
python download_and_create_pdf.py --skip-download --quality 95 --output-pdf high_quality.pdf

# Also: Generate a smaller version for sharing
python download_and_create_pdf.py --skip-download --quality 70 --output-pdf compressed.pdf
```

## Technical Details

- **Image Format**: Downloads JP2 (JPEG 2000) images from the Library of Congress
- **Compression**: Converts to JPEG with configurable quality during PDF creation
- **Downscaling**: Optionally reduces image dimensions to decrease file size
- **Color Space**: Ensures RGB color mode for PDF compatibility
- **Optimization**: Uses PIL's optimize flag for additional compression

## License

This tool is for personal use in accessing publicly available Library of Congress content.

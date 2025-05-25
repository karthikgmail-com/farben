"""
Handles the downloading of YouTube videos using the `yt-dlp` command-line tool.

This module provides functionality to download a video from a given YouTube URL
into a specified output directory, returning the path to the downloaded file.
It includes error handling for common issues like invalid URLs, network problems,
or if `yt-dlp` is not installed.
"""
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

def download_video(youtube_url: str, output_directory: str) -> str | None:
    """
    Downloads a YouTube video to the specified directory using yt-dlp
    and returns the path of the downloaded file.

    Args:
        youtube_url (str): The URL of the YouTube video.
        output_directory (str): The directory where the video should be saved.

    Returns:
        str | None: The full path to the downloaded video file if successful, None otherwise.
    """
    try:
        # Ensure the output directory exists, create if not.
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            logger.info(f"Created output directory: {output_directory}")

        # Define the output template for yt-dlp.
        # %(title)s and %(ext)s are yt-dlp specific placeholders.
        # --restrict-filenames ensures that the filenames are sanitized.
        output_template = os.path.join(output_directory, '%(title)s.%(ext)s')
        
        # Construct the yt-dlp command.
        # -f: Selects the best MP4 format (video and audio).
        # --print filename: Prints the final downloaded filename to stdout. This is crucial for retrieving the exact path.
        command = [
            'yt-dlp',
            '--no-warnings', # Suppress yt-dlp warnings from cluttering logs
            '-o', output_template,
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # Preferred format
            '--restrict-filenames', # Sanitize filenames
            '--print', 'filename',  # Output the filename after download
            youtube_url
        ]

        logger.info(f"Executing yt-dlp command: {' '.join(command)}")
        
        # Execute the command. `check=False` allows manual error checking based on return code.
        process = subprocess.run(command, capture_output=True, text=True, check=False)

        if process.returncode == 0:
            # yt-dlp executed successfully.
            lines = process.stdout.strip().splitlines()
            if lines:
                # The actual filename should be the last line of stdout when using '--print filename'.
                downloaded_file_path_str = lines[-1]
                
                # yt-dlp with an output template including a directory usually gives a path 
                # that is either absolute or relative to the current working directory.
                # For robustness, one might consider making it absolute if it's not,
                # but given `output_template` is constructed with `os.path.join(output_directory, ...)`
                # and `output_directory` is intended to be a specific path, this should be reliable.
                # No changes needed to downloaded_file_path_str if os.path.isabs() is not guaranteed,
                # as long as it's correctly relative to a known base.

                if os.path.exists(downloaded_file_path_str):
                    logger.info(f"Video downloaded successfully: {downloaded_file_path_str}")
                    return downloaded_file_path_str
                else:
                    # This case is unusual: yt-dlp reported success and a filename, but the file isn't found.
                    logger.error(f"yt-dlp reported success (exit code 0) and filename '{downloaded_file_path_str}', but the file was not found.")
                    logger.error(f"yt-dlp stdout: {process.stdout}")
                    logger.error(f"yt-dlp stderr: {process.stderr}")
                    return None
            else:
                # yt-dlp exited successfully but didn't print a filename.
                logger.error("yt-dlp exited successfully but did not print a filename to stdout.")
                logger.error(f"yt-dlp stdout: {process.stdout}")
                logger.error(f"yt-dlp stderr: {process.stderr}")
                return None
        else:
            # yt-dlp failed.
            logger.error(f"yt-dlp download failed. Return code: {process.returncode}")
            logger.error(f"yt-dlp stderr: {process.stderr.strip()}")
            logger.error(f"yt-dlp stdout: {process.stdout.strip()}") # Also log stdout for more context
            return None

    except FileNotFoundError:
        # This occurs if yt-dlp command is not found.
        logger.error("yt-dlp command not found. Please ensure yt-dlp is installed and in your system's PATH.")
        return None
    except Exception as e:
        # Catch any other unexpected errors during the process.
        logger.error(f"An unexpected error occurred during video download: {e.__class__.__name__} - {e}", exc_info=True)
        return None

if __name__ == '__main__':
    # This block is for direct testing of the downloader module.
    # It is not part of the main application flow but helps in verifying functionality independently.

    # Configure basic logging for the test script.
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s'
    )
    
    # Determine project root assuming this script is in main_app/downloader.py
    # This allows temp/downloader_module_tests to be located correctly relative to the project root.
    current_script_path = os.path.abspath(__file__)
    main_app_dir = os.path.dirname(current_script_path)
    project_root_dir = os.path.dirname(main_app_dir) # project_root/main_app -> project_root
    
    # Define a specific directory for this test's downloads within the project's temp folder.
    test_download_dir = os.path.join(project_root_dir, "temp", "downloader_module_tests")

    if not os.path.exists(test_download_dir):
        os.makedirs(test_download_dir)
        logger.info(f"Created temporary directory for testing: {test_download_dir}")

    # Test URLs
    test_url_valid = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # A well-known, publicly available video
    test_url_nonexistent = "https://www.youtube.com/watch?v=THISVIDEOSHOULDNOTEXIST123abc" # An invalid URL
    
    logger.info(f"--- Test Case 1: Valid Video ---")
    logger.info(f"Attempting to download valid video to: {test_download_dir}")
    downloaded_path = download_video(test_url_valid, test_download_dir)

    if downloaded_path:
        logger.info(f"Valid video download SUCCESS. Path: {downloaded_path}")
        logger.info(f"Please verify the file exists at the path above and is playable.")
        # Optional: Clean up the downloaded file after testing.
        # try:
        #     os.remove(downloaded_path)
        #     logger.info(f"Cleaned up test file: {downloaded_path}")
        # except OSError as e:
        #     logger.error(f"Error cleaning up test file {downloaded_path}: {e}")
    else:
        logger.error("Valid video download FAILED.")

    logger.info(f"--- Test Case 2: Nonexistent Video ---")
    logger.info(f"Attempting to download nonexistent video to: {test_download_dir}")
    downloaded_path_nonexistent = download_video(test_url_nonexistent, test_download_dir)
    
    if downloaded_path_nonexistent:
        # This would be an unexpected success for a non-existent video.
        logger.error(f"Nonexistent video download UNEXPECTEDLY SUCCEEDED. Path: {downloaded_path_nonexistent}")
        # Optional: Clean up if it somehow got created.
        # try:
        #     os.remove(downloaded_path_nonexistent)
        #     logger.info(f"Cleaned up unexpected file: {downloaded_path_nonexistent}")
        # except OSError as e:
        #     logger.error(f"Error cleaning up unexpected file {downloaded_path_nonexistent}: {e}")
    else:
        logger.info("Nonexistent video download FAILED as expected.")
    
    logger.info("--- Downloader Module Testing Complete ---")
    # Note: To ensure full cleanup, the 'temp/downloader_module_tests' directory
    # might need to be removed manually or by a higher-level test runner.
```

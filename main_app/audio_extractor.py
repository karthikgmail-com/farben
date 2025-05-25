"""
Handles the extraction of audio from video files using the `ffmpeg` command-line tool.

This module provides functionality to convert the audio track of a video file
into a WAV format audio file, which is suitable for speech-to-text processing.
It specifies audio parameters like codec, sample rate (16kHz), and channels (mono).
"""
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

def extract_audio(video_path: str, output_directory: str) -> str | None:
    """
    Extracts audio from a video file and saves it as a WAV file.

    Args:
        video_path (str): The full path to the input video file.
        output_directory (str): The directory where the extracted audio WAV file should be saved.

    Returns:
        str | None: The full path to the extracted WAV file if successful, None otherwise.
    """
    # Validate that the input video file exists.
    if not os.path.exists(video_path):
        logger.error(f"Input video file not found: {video_path}")
        return None

    try:
        # Ensure the output directory exists.
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            logger.info(f"Created output directory: {output_directory}")

        # Construct the output filename for the WAV file.
        base_filename = os.path.basename(video_path)
        filename_without_ext = os.path.splitext(base_filename)[0]
        output_audio_filename = f"{filename_without_ext}.wav" # Standard WAV extension
        output_audio_path = os.path.join(output_directory, output_audio_filename)

        # Define the ffmpeg command for audio extraction.
        # -i: Input file.
        # -vn: No video output (disable video recording).
        # -acodec pcm_s16le: Audio codec for WAV (PCM signed 16-bit little-endian).
        # -ar 16000: Audio sample rate (16kHz, common for speech recognition).
        # -ac 1: Number of audio channels (1 for mono).
        # -y: Overwrite output file if it exists without asking.
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn', 
            '-acodec', 'pcm_s16le', 
            '-ar', '16000', 
            '-ac', '1', 
            '-y', 
            output_audio_path
        ]

        logger.info(f"Executing ffmpeg command for audio extraction: {' '.join(command)}")
        
        # Execute the ffmpeg command.
        process = subprocess.run(command, capture_output=True, text=True, check=False)

        if process.returncode == 0:
            # ffmpeg command executed successfully.
            if os.path.exists(output_audio_path) and os.path.getsize(output_audio_path) > 0:
                logger.info(f"Audio extracted successfully: {output_audio_path}")
                return output_audio_path
            elif os.path.exists(output_audio_path):
                 logger.warning(f"ffmpeg command succeeded but output audio file is empty: {output_audio_path}. This might indicate an issue with the input video's audio track.")
                 return None # Treat empty file as a failure for downstream processing.
            else:
                # This case is unlikely if ffmpeg returns 0, but good to check.
                logger.error(f"ffmpeg command succeeded but output audio file not found: {output_audio_path}")
                logger.error(f"ffmpeg stdout: {process.stdout.strip()}")
                logger.error(f"ffmpeg stderr: {process.stderr.strip()}")
                return None
        else:
            # ffmpeg command failed.
            logger.error(f"ffmpeg audio extraction failed. Return code: {process.returncode}")
            logger.error(f"ffmpeg stderr: {process.stderr.strip()}")
            logger.error(f"ffmpeg stdout: {process.stdout.strip()}") # Include stdout for more context
            return None

    except FileNotFoundError:
        # This error occurs if the ffmpeg command is not found.
        logger.error("ffmpeg command not found. Please ensure ffmpeg is installed and in your system's PATH.")
        return None
    except Exception as e:
        # Catch any other unexpected errors.
        logger.error(f"An unexpected error occurred during audio extraction: {e.__class__.__name__} - {e}", exc_info=True)
        return None

if __name__ == '__main__':
    # This block is for direct testing of the audio_extractor module.
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s'
    )

    # Setup paths for testing.
    current_script_path = os.path.abspath(__file__)
    main_app_dir = os.path.dirname(current_script_path)
    project_root_dir = os.path.dirname(main_app_dir)
    
    test_output_dir = os.path.join(project_root_dir, "temp", "audio_extractor_module_tests")
    if not os.path.exists(test_output_dir):
        os.makedirs(test_output_dir)
        logger.info(f"Created temporary directory for testing: {test_output_dir}")

    # Create a dummy video file for testing basic path handling and error reporting.
    # Note: ffmpeg will fail to process this as a valid video, which is expected for this part of the test.
    # For a true success test, a small, valid video file should be used.
    dummy_video_filename = "test_video_for_audio_extraction.mp4"
    dummy_video_path = os.path.join(test_output_dir, dummy_video_filename)
    
    try:
        with open(dummy_video_path, 'w') as f:
            f.write("dummy video content for testing file paths") 
        logger.info(f"Created dummy video file for testing at: {dummy_video_path}")
    except IOError as e:
        logger.error(f"Failed to create dummy video file: {e}")
        # If dummy file creation fails, the test cannot proceed as intended.
        exit() # Exit the test script.

    logger.info(f"--- Test Case 1: Audio Extraction (expecting failure with dummy/invalid video file) ---")
    logger.info(f"Attempting to extract audio from: {dummy_video_path} to {test_output_dir}")
    extracted_audio_file = extract_audio(dummy_video_path, test_output_dir)

    if extracted_audio_file:
        logger.info(f"Audio extraction UNEXPECTEDLY SUCCEEDED with dummy file. Path: {extracted_audio_file}")
        logger.info(f"Please verify the file: {extracted_audio_file}")
        # Optional: Cleanup if a file was unexpectedly created.
        # try: os.remove(extracted_audio_file) except OSError: pass
    else:
        logger.info("Audio extraction FAILED as expected with a dummy/invalid video file.")

    logger.info(f"--- Test Case 2: Nonexistent Video File ---")
    non_existent_video_path = os.path.join(test_output_dir, "non_existent_video.mp4")
    logger.info(f"Attempting to extract audio from non-existent file: {non_existent_video_path}")
    extracted_audio_non_existent = extract_audio(non_existent_video_path, test_output_dir)
    if extracted_audio_non_existent:
        logger.error(f"Audio extraction from non-existent file UNEXPECTEDLY SUCCEEDED.")
    else:
        logger.info("Audio extraction from non-existent file FAILED as expected.")

    # Cleanup the dummy video file created for the test.
    try:
        os.remove(dummy_video_path)
        logger.info(f"Cleaned up dummy video file: {dummy_video_path}")
    except OSError as e:
        logger.error(f"Error cleaning up dummy video file {dummy_video_path}: {e}")
        
    logger.info("--- Audio Extractor Module Testing Complete ---")
    logger.info("Note: For a full success test of audio_extractor, replace the dummy file with a small, valid video file.")
```

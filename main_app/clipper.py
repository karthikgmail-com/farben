"""
Handles video segment cutting using the `ffmpeg` command-line tool.

This module provides functionality to extract a specific segment from a larger
video file, defined by start and end times. The output is a new video file
containing only the specified segment, encoded with common video (libx264)
and audio (AAC) codecs.
"""
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

def cut_video_segment(
    input_video_path: str, 
    start_time: float, 
    end_time: float, 
    output_clip_path: str
) -> bool:
    """
    Cuts a segment from a video file using ffmpeg with specified encoding.

    Args:
        input_video_path (str): Path to the original video file.
        start_time (float): Start time of the segment in seconds.
        end_time (float): End time of the segment in seconds.
        output_clip_path (str): Path where the cut video clip will be saved.
                                The directory for this path will be created if it doesn't exist.

    Returns:
        bool: True if the clip was successfully created and is not empty, False otherwise.
    """
    # Validate input video path
    if not os.path.exists(input_video_path):
        logger.error(f"Input video file not found: {input_video_path}")
        return False

    # Validate time arguments
    if start_time >= end_time:
        logger.error(f"Invalid time range: Start time ({start_time}) must be less than end time ({end_time}).")
        return False
    if start_time < 0:
        logger.warning(f"Start time ({start_time}) is negative. ffmpeg might interpret this differently or fail. Proceeding cautiously.")
        # ffmpeg typically handles negative -ss as offset from beginning (0), but good to note.

    # Ensure output directory exists
    output_dir = os.path.dirname(output_clip_path)
    if output_dir and not os.path.exists(output_dir): # Check if output_dir is not empty (e.g. for root path output)
        try:
            os.makedirs(output_dir)
            logger.info(f"Created output directory for clip: {output_dir}")
        except OSError as e:
            logger.error(f"Failed to create output directory {output_dir}: {e}")
            return False

    try:
        # Construct the ffmpeg command.
        # -y: Overwrite output file if it exists.
        # -ss: Specifies the start time for the cut. Placing it before -i can be faster for seeking.
        # -to: Specifies the end time for the cut.
        # -i: Input video file.
        # -c:v libx264: Video codec (H.264). Widely compatible.
        # -preset veryfast: Encoding speed/compression trade-off. 'veryfast' is good for quick processing.
        # -crf 23: Constant Rate Factor for H.264. Controls quality (lower is better, 18-28 is common).
        # -c:a aac: Audio codec (Advanced Audio Coding). Widely compatible.
        # -b:a 192k: Audio bitrate (192 kbps). Good quality for stereo audio.
        command = [
            'ffmpeg',
            '-y', 
            '-ss', str(start_time),
            '-to', str(end_time),
            '-i', input_video_path,
            '-c:v', 'libx264',
            '-preset', 'veryfast', 
            '-crf', '23',       
            '-c:a', 'aac',      
            '-b:a', '192k',     
            output_clip_path 
        ]

        logger.info(f"Executing ffmpeg command for clipping: {' '.join(command)}")
        
        # Execute the command.
        process = subprocess.run(command, capture_output=True, text=True, check=False)

        if process.returncode == 0:
            # ffmpeg command succeeded. Check if the output file was actually created and is not empty.
            if os.path.exists(output_clip_path) and os.path.getsize(output_clip_path) > 0:
                logger.info(f"Video segment cut successfully: {output_clip_path}")
                return True
            elif os.path.exists(output_clip_path): # File exists but is empty
                 logger.warning(f"ffmpeg command succeeded but output clip is empty: {output_clip_path}. "
                                f"This might indicate an issue with the input video, specified times, or ffmpeg parameters.")
                 return False # Treat empty file as a failure.
            else: # File does not exist
                logger.error(f"ffmpeg command succeeded but output clip file not found: {output_clip_path}")
                logger.error(f"ffmpeg stdout: {process.stdout.strip()}")
                logger.error(f"ffmpeg stderr: {process.stderr.strip()}")
                return False
        else:
            # ffmpeg command failed.
            logger.error(f"ffmpeg video clipping failed. Return code: {process.returncode}")
            logger.error(f"ffmpeg stderr: {process.stderr.strip()}")
            logger.error(f"ffmpeg stdout: {process.stdout.strip()}") # Include stdout for more details
            return False

    except FileNotFoundError:
        # Error if ffmpeg is not installed or not in PATH.
        logger.error("ffmpeg command not found. Please ensure ffmpeg is installed and in your system's PATH.")
        return False
    except Exception as e:
        # Catch any other unexpected errors.
        logger.error(f"An unexpected error occurred during video clipping: {e.__class__.__name__} - {e}", exc_info=True)
        return False

if __name__ == '__main__':
    # This block is for direct testing of the clipper module.
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s'
    )

    # Setup paths for test resources and outputs.
    current_script_path = os.path.abspath(__file__)
    main_app_dir = os.path.dirname(current_script_path)
    project_root_dir = os.path.dirname(main_app_dir)
    
    test_resource_dir = os.path.join(project_root_dir, "temp", "clipper_module_tests_resources")
    test_output_dir = os.path.join(project_root_dir, "temp", "clipper_module_tests_output")

    for p_dir in [test_resource_dir, test_output_dir]:
        if not os.path.exists(p_dir):
            os.makedirs(p_dir)
            logger.info(f"Created directory for testing: {p_dir}")

    # A dummy input video file is created for path testing.
    # ffmpeg will fail to process it as a valid video, which is expected for this test setup.
    # For a true success test, replace this with a small, valid MP4 file.
    dummy_input_video_path = os.path.join(test_resource_dir, "sample_video_for_clipping.mp4")
    
    if not os.path.exists(dummy_input_video_path):
        try:
            with open(dummy_input_video_path, 'w') as f:
                f.write("This is not a real mp4, just for testing file paths.") 
            logger.info(f"Created dummy input video for testing at: {dummy_input_video_path}")
            logger.warning("The dummy input video is NOT a valid MP4. ffmpeg processing will likely fail.")
            logger.warning("For a true functional test of clipper.py, replace this with a small, valid MP4 file.")
        except IOError as e:
            logger.error(f"Failed to create dummy input video: {e}")
            exit() # Cannot proceed with tests if dummy file creation fails.

    output_clip_file_path = os.path.join(test_output_dir, "test_clip_01.mp4")

    logger.info(f"--- Test Case 1: Video Clipping (expecting failure with dummy/invalid video file) ---")
    logger.info(f"Attempting to cut segment from {dummy_input_video_path} (0s to 5s) into {output_clip_file_path}")
    
    success = cut_video_segment(dummy_input_video_path, 0.0, 5.0, output_clip_file_path)

    if success:
        logger.info(f"Video clipping UNEXPECTEDLY SUCCEEDED (with dummy file). Output: {output_clip_file_path}")
        if os.path.exists(output_clip_file_path):
            logger.info(f"Output file size: {os.path.getsize(output_clip_file_path)} bytes")
            # try: os.remove(output_clip_file_path) except OSError: pass # Optional cleanup
    else:
        logger.info("Video clipping FAILED as expected with a dummy/invalid input video file.")

    logger.info(f"--- Test Case 2: Invalid times (start_time >= end_time) ---")
    success_invalid_times = cut_video_segment(dummy_input_video_path, 5.0, 0.0, output_clip_file_path)
    if not success_invalid_times:
        logger.info("Video clipping FAILED as expected due to invalid start/end times.")
    else:
        logger.error("Video clipping UNEXPECTEDLY SUCCEEDED with invalid start/end times.")
        
    logger.info(f"--- Test Case 3: Non-existent input file ---")
    success_no_input = cut_video_segment("non_existent_video.mp4", 0.0, 5.0, output_clip_file_path)
    if not success_no_input:
        logger.info("Video clipping FAILED as expected due to non-existent input file.")
    else:
        logger.error("Video clipping UNEXPECTEDLY SUCCEEDED with non-existent input file.")

    # Note: Test files (dummy_input_video_path, output_clip_file_path) and directories
    # (test_resource_dir, test_output_dir) are not cleaned up automatically by this script.
    # This might be handled by a higher-level test runner or manual cleanup.
        
    logger.info("--- Clipper Module Testing Complete ---")
    logger.info("Reminder: For a full success test of clipper.py, provide a valid small video file as input.")
```

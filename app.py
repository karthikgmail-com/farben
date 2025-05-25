"""
Main application file for the YouTube Highlight Extractor.

This script launches a Gradio web interface that allows users to input a YouTube URL.
The backend processes the video by:
1. Downloading the video.
2. Extracting its audio track.
3. Transcribing the audio using Deepgram API (with keyword searching).
4. Analyzing the transcription to find highlight segments.
5. Cutting these segments from the original video.
6. Displaying the resulting highlight clips in the UI for viewing and download.

The application utilizes various modules from the `main_app` package for each step
of the processing pipeline and `main_app.utils` for common utilities like logging
and temporary file management.
"""
import gradio as gr
import os
import logging
import shutil # For cleanup if needed, though utils.cleanup_temp_directory is preferred

# Application-specific imports
from main_app import downloader, audio_extractor, transcriber, analyzer, clipper
from main_app.utils import (
    setup_logging, 
    create_temp_directory, 
    cleanup_temp_directory, 
    generate_safe_filename,
    PROJECT_ROOT # Ensure PROJECT_ROOT is available if utils are used in a way that needs it directly here
)

# --- Initial Application Setup ---
# Configure logging at the very beginning.
# This setup (from utils.py) handles console and optional file logging for the entire application.
setup_logging(level=logging.INFO, log_to_file=True, log_dir_name="logs", log_filename_prefix="youtube_clip_app_")
logger = logging.getLogger(__name__) # Get a logger for this specific file (app.py)

# --- Application Constants ---
SEARCH_KEYWORDS = [ # Keywords used by the analyzer to find potential highlights
    "let's go", "unbelievable", "this is insane", "oh my god", "wow", "crazy", 
    "epic", "highlight", "amazing", "incredible", "best part", "watch this",
    "pog", "poggers", "sheesh", "bruh", "what just happened", "no way",
    "insane play", "he's hacking", "that was sick", "clutch"
]
MAX_CLIPS_DISPLAY = 5  # Maximum number of highlight clips to display in the UI.

# --- Main Video Processing Function ---
def process_youtube_video(youtube_url: str):
    """
    Orchestrates the entire video processing pipeline for a given YouTube URL.

    This generator function performs the following steps:
    1.  Sets up a temporary session directory.
    2.  Downloads the YouTube video.
    3.  Extracts audio from the downloaded video.
    4.  Transcribes the audio using Deepgram, searching for predefined keywords.
    5.  Analyzes the transcription to identify highlight segments.
    6.  Cuts these segments from the original video.
    7.  Yields updates to the Gradio UI to reflect progress and display results or errors.
    8.  Cleans up the temporary directory upon completion or error.

    Args:
        youtube_url (str): The URL of the YouTube video to process.

    Yields:
        dict: A dictionary where keys are Gradio components (defined globally in this script)
              and values are `gr.update(...)` objects, used to dynamically update the UI
              with status messages, results (video clips, download links), or error information.
    """
    session_temp_dir = None  # Path to the unique temporary directory for this session
    video_file_path = None   # Path to the original downloaded video file
    audio_file_path = None   # Path to the extracted audio file
    generated_clip_paths_for_gradio = [] # List to store paths of successfully generated clips for UI display

    # Initial UI Reset: Hide previous error messages and clip outputs before starting.
    # This ensures a clean state for each new processing request.
    initial_updates = {
        error_output_global: gr.update(value="", visible=False),
        clip_outputs_area_global: gr.update(visible=False)
    }
    for i in range(MAX_CLIPS_DISPLAY): # Hide all predefined clip display slots
        initial_updates[output_boxes_global[i]] = gr.update(visible=False)
        initial_updates[video_players_global[i]] = gr.update(value=None, visible=False)
        initial_updates[file_downloads_global[i]] = gr.update(value=None, visible=False)
    yield initial_updates

    try:
        # Step 1: Create Temporary Directory for this session's files.
        yield {status_output_global: "Step 1/7: Creating temporary session directory..."}
        session_temp_dir = create_temp_directory(base_temp_path_name="temp", app_prefix="yt_clips_")
        if not session_temp_dir:
            logger.error("Critical error: Failed to create session temporary directory.")
            yield {status_output_global: "Error: Failed to create session directory. Cannot proceed.",
                   error_output_global: gr.update(value="Server error: Could not create temporary directory. Please check server logs.", visible=True)}
            return # Stop processing if temp directory fails.

        # Define subdirectories within the session's temporary folder for better organization.
        download_dir = os.path.join(session_temp_dir, "downloaded_video")
        audio_extract_dir = os.path.join(session_temp_dir, "extracted_audio")
        # Directory for final clips that Gradio will serve or provide for download.
        clips_output_final_dir = os.path.join(session_temp_dir, "final_clips_for_gradio") 

        os.makedirs(download_dir, exist_ok=True)
        os.makedirs(audio_extract_dir, exist_ok=True)
        os.makedirs(clips_output_final_dir, exist_ok=True)
        logger.info(f"Session directory and subdirectories created successfully: {session_temp_dir}")

        # Step 2: Download Video using the downloader module.
        yield {status_output_global: f"Step 2/7: Downloading video from URL: {youtube_url}..."}
        video_file_path = downloader.download_video(youtube_url, download_dir)
        if not video_file_path:
            logger.error(f"Video download failed for URL: {youtube_url}")
            yield {status_output_global: "Error: Video download failed.",
                   error_output_global: gr.update(value="Failed to download the YouTube video. It might be private, age-restricted, geo-blocked, or the URL is incorrect/invalid.", visible=True)}
            return
        logger.info(f"Video downloaded successfully: {video_file_path}")

        # Step 3: Extract Audio from the downloaded video.
        yield {status_output_global: "Step 3/7: Extracting audio from video..."}
        audio_file_path = audio_extractor.extract_audio(video_file_path, audio_extract_dir)
        if not audio_file_path:
            logger.error(f"Audio extraction failed for video: {video_file_path}")
            yield {status_output_global: "Error: Audio extraction failed.",
                   error_output_global: gr.update(value="Could not extract audio from the downloaded video. The video file might be corrupted or have an unsupported audio format.", visible=True)}
            return
        logger.info(f"Audio extracted successfully: {audio_file_path}")

        # Step 4: Transcribe Audio using the Deepgram API.
        yield {status_output_global: "Step 4/7: Transcribing audio (this may take a while depending on video length)..."}
        deepgram_transcriber_instance = transcriber.DeepgramTranscriber()
        if not deepgram_transcriber_instance.client: # Check if Deepgram client initialized correctly.
            logger.error("Deepgram client initialization failed. This often indicates a missing or invalid API key.")
            yield {status_output_global: "Error: Deepgram client failed to initialize.",
                   error_output_global: gr.update(value="Deepgram API client error. Please check server logs or .env configuration (DEEPGRAM_API_KEY).", visible=True)}
            return
        
        # Optional: Validate API key. This can add a small delay.
        # Consider if this is needed for every run or only at startup/on demand.
        if not deepgram_transcriber_instance.validate_api_key(): 
            logger.warning("Deepgram API key validation failed or was inconclusive. Transcription might still work if the key is valid but the validation call had issues.")
            yield {status_output_global: "Warning: Deepgram API key validation was inconclusive. Attempting transcription..."}
            # Not returning here, as transcription might still succeed.

        transcription_result = deepgram_transcriber_instance.transcribe_audio(audio_file_path, search_keywords=SEARCH_KEYWORDS)
        if not transcription_result:
            logger.error(f"Audio transcription failed for file: {audio_file_path}")
            yield {status_output_global: "Error: Audio transcription failed.",
                   error_output_global: gr.update(value="Failed to transcribe audio using Deepgram. The API might be unreachable, the API key invalid, or an issue with the audio file.", visible=True)}
            return
        logger.info(f"Audio transcribed successfully. Keywords searched: {SEARCH_KEYWORDS}")

        # Step 5: Analyze Transcription to find highlight segments.
        yield {status_output_global: "Step 5/7: Analyzing transcription for potential highlights..."}
        highlight_segments = analyzer.analyze_transcription_for_highlights(
            transcription_result, 
            min_clip_duration=30,    # Desired minimum length of a highlight clip
            max_clip_duration=60,    # Desired maximum length of a highlight clip
            target_clip_duration=45  # Preferred target length for initial segmenting
        )
        if not highlight_segments:
            logger.info("No highlight segments found after analysis based on current criteria.")
            yield {status_output_global: "No highlight segments found based on the keywords and duration criteria. Try a different video or adjust analysis parameters if possible.",
                   error_output_global: gr.update(value="Could not identify any highlight segments. The content might not have matched the search keywords, or segments did not meet duration criteria.", visible=False)} # Not an error, but a "no result" outcome.
            return # End processing if no segments are found.
        logger.info(f"Found {len(highlight_segments)} potential highlight segments from analysis.")

        # Step 6: Cut Video Clips based on identified segments.
        yield {status_output_global: f"Step 6/7: Found {len(highlight_segments)} potential highlights. Cutting video clips..."}
        
        video_title_base = os.path.splitext(os.path.basename(video_file_path))[0]
        safe_video_title_prefix = generate_safe_filename(video_title_base, max_length=50) # Create a safe prefix for clip filenames.

        for i, (start_time, end_time) in enumerate(highlight_segments):
            if len(generated_clip_paths_for_gradio) >= MAX_CLIPS_DISPLAY:
                logger.info(f"Reached display limit of {MAX_CLIPS_DISPLAY} clips. Not cutting more segments.")
                yield {status_output_global: f"Displaying the first {MAX_CLIPS_DISPLAY} of {len(highlight_segments)} identified highlight clips."}
                break # Stop cutting more clips than can be displayed.
            
            clip_filename = f"{safe_video_title_prefix}_highlight_{i+1}_{start_time:.0f}s_to_{end_time:.0f}s.mp4"
            # Clips are saved in the session's `clips_output_final_dir`. Gradio will handle serving these.
            output_clip_full_path = os.path.join(clips_output_final_dir, clip_filename)
            
            yield {status_output_global: f"Cutting clip {len(generated_clip_paths_for_gradio) + 1}/{min(len(highlight_segments), MAX_CLIPS_DISPLAY)}: {start_time:.1f}s to {end_time:.1f}s..."}
            
            success = clipper.cut_video_segment(video_file_path, start_time, end_time, output_clip_full_path)
            if success:
                generated_clip_paths_for_gradio.append(output_clip_full_path)
                logger.info(f"Successfully cut and saved clip: {output_clip_full_path}")
            else:
                logger.warning(f"Failed to cut clip {i+1} for segment {start_time}-{end_time}. Skipping this clip.")
        
        if not generated_clip_paths_for_gradio: # If no clips were successfully cut.
            logger.info("No clips were successfully generated after the cutting process, though segments were identified.")
            yield {status_output_global: "No clips were successfully generated. The cutting process might have failed for all identified segments.",
                   error_output_global: gr.update(value="Clip cutting process failed for all identified segments. Check logs for ffmpeg errors.", visible=True)}
            return

        # Step 7: Prepare and Yield Final Output for Gradio UI.
        yield {status_output_global: f"Step 7/7: Successfully generated {len(generated_clip_paths_for_gradio)} clips. Preparing display..."}
        
        # This dictionary holds all UI updates to be applied at the end of successful processing.
        final_ui_updates = {
            status_output_global: f"Processing complete! Generated {len(generated_clip_paths_for_gradio)} highlight clips.",
            error_output_global: gr.update(visible=False), # Clear any previous non-fatal error/warning messages.
            clip_outputs_area_global: gr.update(visible=True) # Make the area containing clips visible.
        }

        for i in range(MAX_CLIPS_DISPLAY):
            if i < len(generated_clip_paths_for_gradio):
                clip_path_for_ui = generated_clip_paths_for_gradio[i]
                clip_basename = os.path.basename(clip_path_for_ui)
                # Update the corresponding UI elements for this clip.
                final_ui_updates[output_boxes_global[i]] = gr.update(visible=True)
                final_ui_updates[video_players_global[i]] = gr.update(value=clip_path_for_ui, label=clip_basename, visible=True)
                final_ui_updates[file_downloads_global[i]] = gr.update(value=clip_path_for_ui, label=f"Download: {clip_basename}", visible=True)
            else: # Hide unused clip slots.
                final_ui_updates[output_boxes_global[i]] = gr.update(visible=False)
                final_ui_updates[video_players_global[i]] = gr.update(value=None, visible=False)
                final_ui_updates[file_downloads_global[i]] = gr.update(value=None, visible=False)
        
        yield final_ui_updates
        logger.info("Processing workflow completed successfully. Final UI updates yielded.")

    except Exception as e: # Catch-all for any unexpected errors during the workflow.
        logger.error(f"A critical unexpected error occurred in the processing workflow: {e}", exc_info=True)
        error_msg = f"A critical error occurred: {str(e)}. Please check server logs."
        # Prepare UI updates to show a critical error message.
        critical_error_updates = {
            status_output_global: error_msg,
            error_output_global: gr.update(value=error_msg, visible=True),
            clip_outputs_area_global: gr.update(visible=False) # Hide clips area on critical error.
        }
        for i in range(MAX_CLIPS_DISPLAY): # Ensure all clip components are hidden.
            critical_error_updates[output_boxes_global[i]] = gr.update(visible=False)
            critical_error_updates[video_players_global[i]] = gr.update(value=None, visible=False)
            critical_error_updates[file_downloads_global[i]] = gr.update(value=None, visible=False)
        yield critical_error_updates
    finally:
        # Cleanup: Remove the temporary session directory.
        # Gradio typically makes its own copies of files for gr.Video/gr.File components,
        # so the original session files can be deleted.
        if session_temp_dir:
            # A small delay could theoretically help ensure Gradio has picked up files,
            # but is usually not necessary with modern Gradio versions.
            # import time; time.sleep(0.5) 
            yield {status_output_global: "Cleaning up temporary session files..."}
            cleanup_success = cleanup_temp_directory(session_temp_dir)
            if cleanup_success:
                logger.info(f"Successfully cleaned up session directory: {session_temp_dir}")
                yield {status_output_global: "Session cleanup complete. Ready for new URL."}
            else:
                logger.warning(f"Failed to fully clean up session directory: {session_temp_dir}")
                yield {status_output_global: "Warning: Failed to fully clean up some session files. Manual cleanup may be required."}


# --- Gradio UI Layout Definition ---
# Define Gradio components at the global level so they can be referenced by their variable names
# in the dictionaries yielded by the `process_youtube_video` generator function.

# Input components
youtube_url_input_global: gr.Textbox = None
process_button_global: gr.Button = None

# Output/feedback components
status_output_global: gr.Textbox = None
error_output_global: gr.Textbox = None

# Components for displaying clips
clip_outputs_area_global: gr.Column = None # Container for all clip boxes
output_boxes_global: list[gr.Box] = []      # List to hold each clip's gr.Box container
video_players_global: list[gr.Video] = []   # List to hold gr.Video players
file_downloads_global: list[gr.File] = []   # List to hold gr.File download components

# Build the Gradio interface using gr.Blocks for layout flexibility.
with gr.Blocks(title="YouTube Highlight Extractor", theme=gr.themes.Soft(primary_hue=gr.themes.colors.blue)) as demo:
    gr.Markdown("<h1>🎬 YouTube Highlight Extractor</h1>")
    gr.Markdown("Enter a YouTube URL to download the video, extract its audio, transcribe the speech, "
                "analyze for exciting moments based on keywords, and then cut highlight clips (typically 30-60 seconds).")
    gr.Markdown(f"**Sample Keywords for Analysis:** `{'`, `'.join(SEARCH_KEYWORDS[:5])}` ... and more.")

    # Input section: URL textbox and processing button.
    with gr.Row():
        youtube_url_input_global = gr.Textbox(
            label="YouTube Video URL", 
            placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            scale=3 # Makes this component wider relative to others in the row.
        )
        process_button_global = gr.Button("✨ Extract Highlights", variant="primary", scale=1)

    # Status and error display section.
    status_output_global = gr.Textbox(
        label="📊 Progress Log", 
        interactive=False, # User cannot type into this box.
        lines=5,           # Initial number of lines displayed.
        max_lines=20,      # Max lines before scrolling.
        autoscroll=True    # Automatically scroll to the latest message.
    )
    error_output_global = gr.Textbox(
        label="⚠️ Error Messages", 
        interactive=False, 
        visible=False,     # Initially hidden, shown only when errors occur.
        lines=2
    )

    gr.Markdown("---") # Visual separator
    gr.Markdown("<h2>🎞️ Generated Clips</h2>")
    
    # Area where generated clips will be displayed. Initially hidden.
    clip_outputs_area_global = gr.Column(visible=False) 
    
    with clip_outputs_area_global:
        # Pre-define a fixed number of slots for displaying clips.
        for i in range(MAX_CLIPS_DISPLAY):
            with gr.Box(visible=False) as box_i: # Each clip (video + download) is in its own Box.
                # The gr.Video component's label serves as the title for the clip.
                video_player_i = gr.Video(label=f"Highlight Clip {i+1}", interactive=False)
                # The gr.File component provides a download button.
                file_download_i = gr.File(label=f"Download Clip {i+1}") 
                
                # Store references to these components for dynamic updates.
                video_players_global.append(video_player_i)
                file_downloads_global.append(file_download_i)
            output_boxes_global.append(box_i) # Store the Box container itself.

    # --- Connect UI Components to the Processing Function ---
    # This list must contain all Gradio components that the `process_youtube_video` generator
    # will yield updates for. The keys in the yielded dictionaries must match these components.
    all_updatable_outputs = [
        status_output_global, 
        error_output_global, 
        clip_outputs_area_global # Visibility of the entire clips area
    ] + output_boxes_global + video_players_global + file_downloads_global

    # Wire the button's click event to the main processing function.
    process_button_global.click(
        fn=process_youtube_video,         # The function to call on click.
        inputs=[youtube_url_input_global],# List of input components.
        outputs=all_updatable_outputs     # List of output components that fn can update.
    )

    gr.Markdown("---")
    gr.Markdown("Developed using Python and Gradio. This tool leverages speech-to-text and video processing "
                "to automatically identify potential highlights. Processing time may vary based on video length.")
    gr.HTML("<p style='text-align:center; font-size:small;'>Application Version 0.3.0 (Documentation Update)</p>")


# --- Launch the Gradio Application ---
if __name__ == "__main__":
    logger.info("Starting Gradio application...")
    # demo.queue() is important for handling multiple users or long-running tasks,
    # as it processes requests sequentially.
    # debug=True provides more detailed error messages in the console during development.
    # share=False by default; set to True to create a public link (requires internet connection).
    demo.queue().launch(debug=True, share=False)
```

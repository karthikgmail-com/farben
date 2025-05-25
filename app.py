import gradio as gr
import os
import logging
import shutil

# Application-specific imports
from main_app import downloader, audio_extractor, transcriber, analyzer, clipper
from main_app.utils import (
    setup_logging, 
    create_temp_directory, 
    cleanup_temp_directory, # Not used for session_temp_dir cleanup in this version
    generate_safe_filename  # Ensured import for clip filenames
)

# 1. Imports and Setup
# Use a distinct log file prefix for this version.
setup_logging(level=logging.INFO, log_to_file=True, log_dir_name="logs", log_filename_prefix="app_final_v36_")
logger = logging.getLogger(__name__)

# 2. Constants
SEARCH_KEYWORDS = [
    "let's go", "you got this", "no way", "bruh", "this is insane", "unbelievable", 
    "trust me", "I can't believe this", "amazing", "awesome", "incredible", "wow", 
    "crazy", "epic", "yes", "lol", "haha", "funny", "hilarious", "literally", 
    "actually", "seriously", "definitely", "absolutely"
]
MAX_CLIPS_TO_PROCESS = 10  # Limit the number of clips to cut

# 3. Main Processing Function (Generator)
def process_video_for_ui(youtube_url: str):
    """
    Processes a YouTube video. Yields status strings for UI updates.
    The "return value" of this generator (what's passed to .then()) is the 
    list of clip paths or an error/status string.
    """
    session_temp_dir = None
    video_file_path = None
    audio_file_path = None
    generated_clip_paths = []
    
    dl_dir, audio_dir, clips_dir = None, None, None
    
    # This variable will hold the value to be "returned" to the .then() clause
    return_value_for_then = None 

    try:
        # Step 1: Create Temporary Directory
        yield "Starting... Creating temporary session directory."
        session_temp_dir = create_temp_directory(app_prefix="yt_highlights_")
        if not session_temp_dir:
            logger.error("Failed to create temporary session directory.")
            return_value_for_then = "Error: Could not create temp directory. Processing halted."
            # Yield the error message for status_output before returning for .then()
            yield return_value_for_then 
            return return_value_for_then # This return value is passed to display_clips

        dl_dir = os.path.join(session_temp_dir, "downloads")
        audio_dir = os.path.join(session_temp_dir, "audio")
        clips_dir = os.path.join(session_temp_dir, "clips_for_display") 
        os.makedirs(dl_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(clips_dir, exist_ok=True)
        logger.info(f"Temporary session directory created: {session_temp_dir}")

        # Step 2: Download Video
        yield "Downloading video..."
        video_file_path = downloader.download_video(youtube_url, dl_dir)
        if not video_file_path:
            logger.error(f"Failed to download video from URL: {youtube_url}")
            return_value_for_then = "Error: Failed to download video. Check URL or network."
            yield return_value_for_then
            return return_value_for_then
        logger.info(f"Video downloaded: {video_file_path}")

        # Step 3: Extract Audio
        yield "Extracting audio..."
        audio_file_path = audio_extractor.extract_audio(video_file_path, audio_dir)
        if not audio_file_path:
            logger.error(f"Failed to extract audio from: {video_file_path}")
            return_value_for_then = "Error: Failed to extract audio."
            yield return_value_for_then
            return return_value_for_then
        logger.info(f"Audio extracted: {audio_file_path}")

        # Step 4: Transcribe Audio
        yield "Transcribing audio (this may take a while)..."
        dg_transcriber = transcriber.DeepgramTranscriber()
        if not dg_transcriber.client:
            logger.error("Deepgram client failed to initialize.")
            return_value_for_then = "Error: Deepgram client failed to initialize (check API key in .env)."
            yield return_value_for_then
            return return_value_for_then
        
        if not dg_transcriber.validate_api_key(): 
            logger.error("Deepgram API key seems invalid.")
            return_value_for_then = "Error: Deepgram API key seems invalid." # As per plan
            yield return_value_for_then
            return return_value_for_then
        
        transcription_result = dg_transcriber.transcribe_audio(audio_file_path, SEARCH_KEYWORDS)
        if not transcription_result:
            logger.error(f"Transcription failed for: {audio_file_path}")
            return_value_for_then = "Error: Transcription failed." # As per plan
            yield return_value_for_then
            return return_value_for_then
        logger.info("Transcription successful.")

        # Step 5: Analyze Transcript
        yield "Analyzing transcript for highlights..."
        # Using default durations from analyzer.py as per plan
        highlight_segments = analyzer.analyze_transcription_for_highlights(transcription_result) 
        if not highlight_segments:
            logger.info("No highlight segments found meeting criteria.")
            return_value_for_then = "No highlight segments found meeting criteria." # As per plan
            yield return_value_for_then
            return return_value_for_then
        logger.info(f"Found {len(highlight_segments)} potential highlight segments.")

        # Step 6: Cut Video Clips
        yield f"Found {len(highlight_segments)} potential highlights. Processing up to {MAX_CLIPS_TO_PROCESS} clips..."
        
        for i, (start, end) in enumerate(highlight_segments[:MAX_CLIPS_TO_PROCESS]):
            # Using specified filename format from the plan
            clip_filename = f"highlight_{i+1}_{start:.0f}s_to_{end:.0f}s.mp4"
            output_clip_path = os.path.join(clips_dir, clip_filename)
            
            yield f"Cutting clip {i+1}: {start:.1f}s to {end:.1f}s" # As per plan
            success = clipper.cut_video_segment(video_file_path, start, end, output_clip_path)
            if success:
                generated_clip_paths.append(output_clip_path)
                logger.info(f"Successfully cut clip: {output_clip_path}")
            else:
                logger.warning(f"Failed to cut clip {i+1}. Skipping.")
        
        # Step 7: Check if any clips were generated
        if not generated_clip_paths:
            logger.info("No clips were successfully generated after cutting attempts.")
            return_value_for_then = "No clips were successfully generated." # As per plan
            yield return_value_for_then
            return return_value_for_then
        
        # Step 8: Processing Complete
        yield f"Processing complete! {len(generated_clip_paths)} clips generated."
        # The final value to be passed to .then()
        return_value_for_then = generated_clip_paths

    except Exception as e:
        logger.error("Error in processing workflow", exc_info=True)
        return_value_for_then = f"An critical error occurred: {str(e)}"
        # Yield the error message to status_output before the function returns for .then()
        yield return_value_for_then 
        # The value of return_value_for_then (error string) is returned after finally for .then()
    finally:
        # Yields in `finally` are the last status updates.
        # The `return_value_for_then` (paths or error string) is returned after this block.
        yield "Cleaning up intermediate files (original download, extracted audio)..."
        
        if video_file_path and os.path.exists(video_file_path):
            try: os.remove(video_file_path); logger.info(f"Removed intermediate video: {video_file_path}")
            except Exception as e_clean: logger.error(f"Failed to remove video {video_file_path}: {e_clean}")
        
        if audio_file_path and os.path.exists(audio_file_path):
            try: os.remove(audio_file_path); logger.info(f"Removed intermediate audio: {audio_file_path}")
            except Exception as e_clean: logger.error(f"Failed to remove audio {audio_file_path}: {e_clean}")

        try: # Attempt to remove empty intermediate directories
            if dl_dir and os.path.exists(dl_dir) and not os.listdir(dl_dir): shutil.rmtree(dl_dir)
            if audio_dir and os.path.exists(audio_dir) and not os.listdir(audio_dir): shutil.rmtree(audio_dir)
        except Exception as e_rm_subdir: logger.warning(f"Could not remove empty subdirs: {e_rm_subdir}")
            
        logger.info(f"Intermediate file cleanup attempted for session: {session_temp_dir}. Highlight clips remain in '{clips_dir}'.")
        # This is the final status update yielded by the generator, as per plan.
        yield "Cleanup of intermediates complete. Clips are ready."
    
    # This return statement ensures that the value determined in the try/except block
    # (which could be a list of paths or an error string) is what's passed to the .then() clause.
    return return_value_for_then


# 5. display_clips Function
def display_clips(clip_paths_or_status_message):
    """
    Dynamically creates Gradio components to display generated video clips or error messages.
    Receives the "return value" from `process_video_for_ui`.
    Updates the `clip_gallery_output` Column with a list of new components.
    """
    if isinstance(clip_paths_or_status_message, list) and clip_paths_or_status_message:
        logger.info(f"Displaying {len(clip_paths_or_status_message)} clips in the gallery.")
        
        valid_clip_paths = [p for p in clip_paths_or_status_message if os.path.exists(p)]
        if len(valid_clip_paths) != len(clip_paths_or_status_message):
            logger.warning("Some clip paths provided to display_clips do not exist on the server.")
        
        if not valid_clip_paths:
             # If clips were supposedly generated but not found, show error.
             return { 
                clip_gallery_output: gr.update(value=[], visible=False), 
                error_output: gr.update(value="<p style='color:red;'>Clips were reported as generated, but could not be found for display. Please check server logs.</p>", visible=True)
            }

        # Create a list of new components to display
        components_to_display = []
        for path in valid_clip_paths: 
            clip_name = os.path.basename(path)
            components_to_display.append(gr.Markdown(f"### {clip_name}")) 
            components_to_display.append(gr.Video(value=path, label=clip_name, interactive=False))
            components_to_display.append(gr.File(value=path, label=f"Download {clip_name}"))
            components_to_display.append(gr.Markdown("---")) # Visual separator
        
        return {
            # The `value` of a gr.Column can be a list of components to dynamically replace its children.
            clip_gallery_output: gr.update(value=components_to_display, visible=True),
            error_output: gr.update(value="") # Clear any previous errors by setting empty HTML string
        }
    else: 
        # This block handles cases where process_video_for_ui returned an error string or an empty list.
        error_message_html = "<p style='color:red;'>No clips generated or an error occurred. Check progress messages.</p>"
        if isinstance(clip_paths_or_status_message, str): 
            # If process_video_for_ui returned an error string or specific status message.
            error_message_html = f"<p style='color:red;'>{clip_paths_or_status_message}</p>" # Display message in red
            logger.info(f"No clips to display. Status/Error from processing: {clip_paths_or_status_message}")
        else: # Empty list or other non-string, non-list type
            logger.info(f"No clips to display. Received: {clip_paths_or_status_message}")

        return {
            clip_gallery_output: gr.update(value=[], visible=False), # Clear and hide gallery
            error_output: gr.update(value=error_message_html, visible=True)
        }


# 4. Gradio Interface
with gr.Blocks(title="YouTube Highlight Extractor", theme=gr.themes.Soft()) as demo:
    gr.Markdown("<h1>YouTube Highlight Extractor</h1>") # As per plan
    gr.Markdown("Enter a YouTube URL to download, analyze, and extract highlight clips. " # As per plan
                "Processing may take several minutes depending on video length.")

    youtube_url_input = gr.Textbox(label="YouTube URL", placeholder="e.g., https://www.youtube.com/watch?v=your_video_id") # As per plan
    process_button = gr.Button("Extract Highlights") # As per plan

    status_output = gr.Textbox(
        label="Progress", # As per plan
        interactive=False, 
        lines=5, 
        max_lines=20,
        autoscroll=True 
    )
    
    error_output = gr.HTML() # As per plan, content and visibility controlled by display_clips

    gr.Markdown("---") 
    gr.Markdown("<h2>Generated Clips</h2>") 
    
    # This Column will be dynamically populated by the `display_clips` function.
    # Its `value` will be set to a list of new Gradio components.
    clip_gallery_output = gr.Column(visible=False) # As per plan

    # --- Event Handling ---
    # 1. When `process_button` is clicked, `process_video_for_ui` is called.
    #    Its `yield`ed strings update `status_output`.
    event_handler = process_button.click(
        fn=process_video_for_ui, 
        inputs=[youtube_url_input], 
        outputs=[status_output] # As per plan
    )

    # 2. After `process_video_for_ui` finishes, its "return value" (the list of clip paths
    #    or an error/status string) is passed as input to `display_clips`.
    #    `display_clips` then updates `clip_gallery_output` and `error_output`.
    event_handler.then(
        fn=display_clips, 
        # Implicit input to display_clips is the return from process_video_for_ui
        outputs=[clip_gallery_output, error_output] # As per plan
    )
    
    gr.Markdown("---") 
    gr.Markdown("App Version 1.1.0 (Final Plan Implementation)") # As per plan

# 6. Application Launch
if __name__ == "__main__":
    logger.info("Starting Gradio application (app_final_v36)...")
    # queue() is important for handling multiple users or long-running tasks.
    demo.queue().launch(debug=True, share=False)
```

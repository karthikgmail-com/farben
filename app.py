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
    generate_safe_filename
)

# 1. Imports and Setup
setup_logging(level=logging.INFO, log_to_file=True, log_dir_name="logs", log_filename_prefix="app_state_fix_")
logger = logging.getLogger(__name__)

# 2. Constants
SEARCH_KEYWORDS = [
    "let's go", "you got this", "no way", "bruh", "this is insane", "unbelievable", 
    "trust me", "I can't believe this", "amazing", "awesome", "incredible", "wow", 
    "crazy", "epic", "yes", "lol", "haha", "funny", "hilarious", "literally", 
    "actually", "seriously", "definitely", "absolutely"
]
MAX_CLIPS_TO_PROCESS = 10

# 3. Main Processing Function (Generator)
def process_video_for_ui(youtube_url: str):
    """
    Processes a YouTube video. Yields status strings for status_output.
    Returns a list of clip paths (for clip_data_state) or an error string/empty list.
    """
    session_temp_dir = None
    video_file_path = None
    audio_file_path = None
    generated_clip_paths = []
    
    dl_dir, audio_dir, clips_dir = None, None, None
    
    # Value to be returned to populate clip_data_state
    return_value_for_state = [] 

    try:
        # Step 1: Create Temporary Directory
        yield "Starting... Creating temporary session directory."
        session_temp_dir = create_temp_directory(app_prefix="yt_highlights_")
        if not session_temp_dir:
            logger.error("Failed to create temporary session directory.")
            yield "Error: Could not create temp directory. Processing halted." 
            return_value_for_state = [] # Or a specific error marker if display_clips handles it
            return return_value_for_state 

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
            yield "Error: Failed to download video. Check URL or network."
            return_value_for_state = [] 
            return return_value_for_state
        logger.info(f"Video downloaded: {video_file_path}")

        # Step 3: Extract Audio
        yield "Extracting audio..."
        audio_file_path = audio_extractor.extract_audio(video_file_path, audio_dir)
        if not audio_file_path:
            logger.error(f"Failed to extract audio from: {video_file_path}")
            yield "Error: Failed to extract audio."
            return_value_for_state = []
            return return_value_for_state
        logger.info(f"Audio extracted: {audio_file_path}")

        # Step 4: Transcribe Audio
        yield "Transcribing audio (this may take a while)..."
        dg_transcriber = transcriber.DeepgramTranscriber()
        if not dg_transcriber.client:
            logger.error("Deepgram client failed to initialize.")
            yield "Error: Deepgram client failed to initialize (check API key in .env)."
            return_value_for_state = []
            return return_value_for_state
        
        if not dg_transcriber.validate_api_key(): 
            logger.error("Deepgram API key seems invalid.")
            yield "Error: Deepgram API key seems invalid."
            return_value_for_state = []
            return return_value_for_state
        
        transcription_result = dg_transcriber.transcribe_audio(audio_file_path, SEARCH_KEYWORDS)
        if not transcription_result:
            logger.error(f"Transcription failed for: {audio_file_path}")
            yield "Error: Transcription failed."
            return_value_for_state = []
            return return_value_for_state
        logger.info("Transcription successful.")

        # Step 5: Analyze Transcript
        yield "Analyzing transcript for highlights..."
        highlight_segments = analyzer.analyze_transcription_for_highlights(transcription_result) 
        if not highlight_segments:
            logger.info("No highlight segments found meeting criteria.")
            yield "No highlight segments found meeting criteria."
            return_value_for_state = []
            return return_value_for_state
        logger.info(f"Found {len(highlight_segments)} potential highlight segments.")

        # Step 6: Cut Video Clips
        yield f"Found {len(highlight_segments)} potential highlights. Processing up to {MAX_CLIPS_TO_PROCESS} clips..."
        
        for i, (start, end) in enumerate(highlight_segments[:MAX_CLIPS_TO_PROCESS]):
            clip_filename = f"highlight_{i+1}_{start:.0f}s_to_{end:.0f}s.mp4"
            output_clip_path = os.path.join(clips_dir, clip_filename)
            
            yield f"Cutting clip {i+1}: {start:.1f}s to {end:.1f}s"
            success = clipper.cut_video_segment(video_file_path, start, end, output_clip_path)
            if success:
                generated_clip_paths.append(output_clip_path)
                logger.info(f"Successfully cut clip: {output_clip_path}")
            else:
                logger.warning(f"Failed to cut clip {i+1}. Skipping.")
        
        # Step 7: Check if any clips were generated
        if not generated_clip_paths:
            logger.info("No clips were successfully generated after cutting attempts.")
            yield "No clips were successfully generated."
            return_value_for_state = []
            return return_value_for_state
        
        # Step 8: Processing Complete
        yield f"Successfully generated {len(generated_clip_paths)} clips." # Changed from "Processing complete!"
        return_value_for_state = generated_clip_paths

    except Exception as e:
        logger.error("Error in processing workflow", exc_info=True)
        error_message = f"An critical error occurred: {str(e)}"
        yield error_message 
        return_value_for_state = [] # Return empty list for clips on error
    finally:
        # These yields are for status_output only.
        # The Python 'return' statement for clip_data_state happens before this.
        yield "Cleaning up intermediate files (original download, extracted audio)..."
        
        if video_file_path and os.path.exists(video_file_path):
            try: os.remove(video_file_path); logger.info(f"Removed intermediate video: {video_file_path}")
            except Exception as e_clean: logger.error(f"Failed to remove video {video_file_path}: {e_clean}")
        
        if audio_file_path and os.path.exists(audio_file_path):
            try: os.remove(audio_file_path); logger.info(f"Removed intermediate audio: {audio_file_path}")
            except Exception as e_clean: logger.error(f"Failed to remove audio {audio_file_path}: {e_clean}")

        try: 
            if dl_dir and os.path.exists(dl_dir) and not os.listdir(dl_dir): shutil.rmtree(dl_dir)
            if audio_dir and os.path.exists(audio_dir) and not os.listdir(audio_dir): shutil.rmtree(audio_dir)
        except Exception as e_rm_subdir: logger.warning(f"Could not remove empty subdirs: {e_rm_subdir}")
            
        logger.info(f"Intermediate file cleanup attempted for session: {session_temp_dir}. Highlight clips remain in '{clips_dir}'.")
        yield "Cleanup complete. Ready for next video." # Changed from "Clips are ready"
    
    # This return statement provides the value for clip_data_state
    return return_value_for_state


# 5. display_clips Function
def display_clips(clip_data_from_state): # Input is now from gr.State
    """
    Dynamically creates Gradio components to display generated video clips or error messages.
    Receives data from clip_data_state.
    """
    # clip_data_from_state is expected to be a list of paths or an empty list if errors occurred.
    # The plan implies that process_video_for_ui will return [] on error, not an error string directly to this function.
    # Error strings are yielded to status_output by process_video_for_ui.
    
    if isinstance(clip_data_from_state, list) and clip_data_from_state:
        logger.info(f"Displaying {len(clip_data_from_state)} clips in the gallery.")
        
        valid_clip_paths = [p for p in clip_data_from_state if os.path.exists(p)]
        if len(valid_clip_paths) != len(clip_data_from_state):
            logger.warning("Some clip paths from state do not exist on the server.")
        
        if not valid_clip_paths:
             return { 
                clip_gallery_output: gr.update(value=[], visible=False), 
                error_output: gr.update(value="<p style='color:red;'>Clips were reported as generated, but could not be found for display. Please check server logs.</p>", visible=True)
            }

        components_to_display = []
        for path in valid_clip_paths: 
            clip_name = os.path.basename(path)
            components_to_display.append(gr.Markdown(f"### {clip_name}")) 
            components_to_display.append(gr.Video(value=path, label=clip_name, interactive=False))
            components_to_display.append(gr.File(value=path, label=f"Download {clip_name}"))
            components_to_display.append(gr.Markdown("---")) 
        
        return {
            clip_gallery_output: gr.update(value=components_to_display, visible=True),
            error_output: gr.update(value="") 
        }
    else: 
        # This handles if clip_data_from_state is an empty list (due to error or no clips)
        # or potentially other non-list types if process_video_for_ui changes its error return.
        # The status_output would have already shown detailed errors.
        error_message = "No clips were generated or an error occurred during processing. Please check the progress log above."
        if isinstance(clip_data_from_state, str): # Should not happen if process_video_for_ui returns [] on error
             error_message = clip_data_from_state # But handle just in case
        
        logger.info(f"No clips to display. Data from state: {clip_data_from_state}")
        return {
            clip_gallery_output: gr.update(value=[], visible=False), 
            error_output: gr.update(value=f"<p style='color:red;'>{error_message}</p>", visible=True)
        }


# 4. Gradio Interface
with gr.Blocks(title="YouTube Highlight Extractor", theme=gr.themes.Soft()) as demo:
    gr.Markdown("<h1>YouTube Highlight Extractor</h1>")
    gr.Markdown("Enter a YouTube URL to download, analyze, and extract highlight clips. "
                "Processing may take several minutes depending on video length.")

    # Define gr.State component for clip data
    clip_data_state = gr.State([])

    youtube_url_input = gr.Textbox(label="YouTube URL", placeholder="e.g., https://www.youtube.com/watch?v=your_video_id")
    process_button = gr.Button("Extract Highlights")

    status_output = gr.Textbox(
        label="Progress", 
        interactive=False, 
        lines=5, 
        max_lines=20,
        autoscroll=True 
    )
    
    error_output = gr.HTML() # Error messages displayed here by display_clips

    gr.Markdown("---") 
    gr.Markdown("<h2>Generated Clips</h2>") 
    
    clip_gallery_output = gr.Column(visible=False) 

    # --- Event Handling ---
    # .click() event:
    #   - fn: process_video_for_ui (generator)
    #   - inputs: youtube_url_input
    #   - outputs: 
    #     - status_output (receives yielded strings from the generator)
    #     - clip_data_state (receives the Python return value from the generator)
    process_event = process_button.click(
        fn=process_video_for_ui, 
        inputs=[youtube_url_input], 
        outputs=[status_output, clip_data_state] 
    )

    # .then() clause:
    #   - fn: display_clips
    #   - inputs: clip_data_state (receives the value returned by process_video_for_ui)
    #   - outputs: clip_gallery_output, error_output
    process_event.then(
        fn=display_clips, 
        inputs=[clip_data_state], # Input is the value from clip_data_state
        outputs=[clip_gallery_output, error_output] 
    )
    
    gr.Markdown("---") 
    gr.Markdown("App Version 1.2.0 (State Data Flow Fix)")

# 6. Application Launch
if __name__ == "__main__":
    logger.info("Starting Gradio application (app_state_fix)...")
    demo.queue().launch(debug=True, share=False)
```

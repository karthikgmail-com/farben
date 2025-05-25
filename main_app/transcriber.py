"""
Handles audio transcription using the Deepgram Speech-to-Text API.

This module defines the `DeepgramTranscriber` class, which encapsulates
the logic for interacting with the Deepgram API. This includes initializing the
Deepgram client with an API key (loaded from environment variables), validating
the API key, and transcribing audio files. The transcription can also search for
specific keywords within the audio.
"""
import os
import logging
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions, DeepgramClientOptions # type: ignore[import-untyped]
# Using type: ignore for deepgram imports if linting/type-checking in the environment
# does not have stubs for this library.

logger = logging.getLogger(__name__)

class DeepgramTranscriber:
    """
    Handles audio transcription using the Deepgram API.

    Attributes:
        api_key (str | None): The Deepgram API key.
        client (DeepgramClient | None): The Deepgram client instance.
    """
    def __init__(self):
        """
        Initializes the DeepgramTranscriber.

        This involves loading the DEEPGRAM_API_KEY from a .env file (or environment variables),
        and then initializing the DeepgramClient. If the API key is not found or the
        client fails to initialize, an error is logged, and `self.client` remains None.
        """
        load_dotenv() # Load environment variables from .env file
        self.api_key: str | None = os.getenv("DEEPGRAM_API_KEY")
        self.client: DeepgramClient | None = None

        if not self.api_key:
            logger.error("DEEPGRAM_API_KEY not found in .env file or environment variables.")
            # The client remains None, methods using the client should check its state.
            return

        try:
            # Initialize the Deepgram client.
            # Additional options can be passed via DeepgramClientOptions, e.g., for verbosity.
            # config = DeepgramClientOptions(verbose=logging.WARNING) 
            # self.client = DeepgramClient(self.api_key, config)
            self.client = DeepgramClient(self.api_key)
            logger.info("Deepgram client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram client: {e}", exc_info=True)
            self.client = None # Ensure client is None if initialization fails

    def validate_api_key(self) -> bool:
        """
        Validates the Deepgram API key by making a simple, low-cost API call.

        This method attempts to list projects associated with the API key.
        A successful response indicates the key is valid.

        Returns:
            bool: True if the API key is valid and the client can connect, False otherwise.
        """
        if not self.client:
            logger.error("Deepgram client not initialized. Cannot validate API key.")
            return False
        try:
            # The `get_projects()` call is a lightweight way to check if the API key is operational.
            # If this call succeeds, the API key is considered valid.
            response = self.client.manage.get_projects() 
            logger.info(f"API Key validation successful. Projects found (or empty list if none): {response}")
            return True
        except Exception as e:
            # Any exception during this call suggests an issue with the key or connectivity.
            logger.error(f"API Key validation failed: {e}", exc_info=True)
            return False

    def transcribe_audio(self, audio_path: str, search_keywords: list[str] | None = None) -> dict | None:
        """
        Transcribes the given audio file using Deepgram's prerecorded audio transcription.

        Args:
            audio_path (str): The path to the audio file (e.g., WAV) to be transcribed.
            search_keywords (list[str] | None, optional): A list of keywords or phrases 
                to search for in the audio. Defaults to None, meaning no search.

        Returns:
            dict | None: A dictionary containing the full transcription result from Deepgram
                         if successful, or None if an error occurred (e.g., file not found,
                         API error, client not initialized). The structure of the dictionary
                         is defined by the Deepgram API response.
        """
        if not self.client:
            logger.error("Deepgram client not initialized. Cannot transcribe audio.")
            return None

        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found for transcription: {audio_path}")
            return None

        if search_keywords is None:
            search_keywords = [] # Default to an empty list if no keywords are provided.

        try:
            # Read the audio file in binary mode.
            with open(audio_path, 'rb') as audio_file:
                buffer_data = audio_file.read()
            
            # Prepare the payload for Deepgram API.
            payload = {'buffer': buffer_data}
            
            # Configure transcription options.
            # model: Specifies the transcription model (e.g., "nova-2", "enhanced").
            # smart_format: Enables automatic formatting of the transcript.
            # utterances: Segments the transcript into utterances (speaker segments).
            # punctuate: Enables automatic punctuation.
            # search: List of keywords to search for.
            options = PrerecordedOptions(
                model="nova-2", 
                smart_format=True,
                utterances=True, 
                punctuate=True,
                # diarize=False, # Diarization (speaker identification) is not used for this project.
                search=search_keywords 
            )
            
            logger.info(f"Sending audio for transcription: {audio_path}. Keywords: {search_keywords if search_keywords else 'None'}.")
            
            # Make the API call to Deepgram.
            # A timeout is added for robustness against network issues.
            response = self.client.listen.prerecorded.transcribe_file(payload, options, timeout=300) 
            
            logger.info("Transcription successful.")
            return response.to_dict() # Convert the DeepgramResponse object to a dictionary.

        except Exception as e:
            # Log any errors that occur during the transcription process.
            logger.error(f"Error during Deepgram transcription for '{audio_path}': {e.__class__.__name__} - {e}", exc_info=True)
            return None

if __name__ == '__main__':
    # This block is for direct testing of the DeepgramTranscriber class.
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s'
    )
    
    # Determine project root to locate .env and sample audio files.
    current_script_path = os.path.abspath(__file__)
    main_app_dir = os.path.dirname(current_script_path)
    project_root_dir = os.path.dirname(main_app_dir)
    
    dotenv_path = os.path.join(project_root_dir, ".env")
    if not os.path.exists(dotenv_path):
        logger.warning(f".env file not found at {dotenv_path}. Please create it with your DEEPGRAM_API_KEY for testing.")
    else:
        logger.info(f"Found .env file at {dotenv_path}, attempting to load.")
        load_dotenv(dotenv_path) # Load .env specifically for this test script execution.

    transcriber = DeepgramTranscriber()

    if not transcriber.api_key:
        logger.error("Halting test: DEEPGRAM_API_KEY is not set. Please set it in your .env file or environment.")
    elif not transcriber.client:
        logger.error("Halting test: Deepgram client could not be initialized (API key might be set but client creation failed).")
    else:
        logger.info("--- Test Case 1: API Key Validation ---")
        is_valid = transcriber.validate_api_key()
        if is_valid:
            logger.info("API Key validation SUCCEEDED.")
        else:
            logger.warning("API Key validation FAILED. Transcription test will likely fail or be skipped if the key is truly invalid.")

        # Define path to a sample audio file for testing transcription.
        # This assumes a WAV file from the audio_extractor tests might exist.
        # For robust testing, a dedicated small, valid audio file should be present.
        sample_audio_relative_path = os.path.join("temp", "audio_extractor_module_tests", "test_video_for_audio_extraction.wav")
        sample_audio_path = os.path.join(project_root_dir, sample_audio_relative_path)

        if not os.path.exists(sample_audio_path):
            logger.warning(f"Sample audio file not found at: {sample_audio_path}")
            logger.warning("To test transcription, place a valid WAV file at this location or update the path.")
            logger.warning("Skipping transcription test due to missing sample audio.")
        elif is_valid: # Only attempt transcription if API key validation passed.
            logger.info(f"--- Test Case 2: Audio Transcription ---")
            logger.info(f"Attempting to transcribe: {sample_audio_path}")
            
            keywords_to_search = ["hello", "world", "test", "audio", "video"] 
            
            transcription_result = transcriber.transcribe_audio(sample_audio_path, search_keywords=keywords_to_search)
            
            if transcription_result:
                logger.info("Transcription SUCCEEDED.")
                # Attempt to safely access and print parts of the result.
                try:
                    results_data = transcription_result.get("results", {})
                    channels = results_data.get("channels", [])
                    if channels:
                        alternatives = channels[0].get("alternatives", [])
                        if alternatives:
                            transcript_text = alternatives[0].get("transcript")
                            if transcript_text:
                                logger.info(f"Transcript (first 200 chars): {transcript_text[:200]}...")
                            
                            search_hits = alternatives[0].get("search")
                            if search_hits:
                                logger.info(f"Search results: {search_hits}")
                            elif keywords_to_search:
                                logger.info(f"No occurrences found for search keywords: {keywords_to_search}")
                        else:
                            logger.info("No alternatives found in transcription results.")
                    else:
                        logger.info("No channels found in transcription results.")
                except Exception as e: # Catch any error during parsing of the complex dict.
                    logger.error(f"Could not parse all details from transcription response: {e}", exc_info=True)
                    logger.info(f"Full response dictionary: {transcription_result}") # Log the full response for debugging.
            else:
                logger.error("Transcription FAILED.")
        else:
            logger.info("Skipping transcription test due to failed API key validation or client initialization.")
            
    logger.info("--- Transcriber Module Testing Complete ---")
```

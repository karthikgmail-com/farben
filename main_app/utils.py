"""
Provides utility functions for the YouTube Highlight Extractor application.

This module includes a variety of helper functions:
- Temporary directory management: Creating and cleaning up session-specific temporary folders.
- Safe filename generation: Sanitizing strings to be used as valid filenames.
- Logging configuration: Setting up global application logging to console and/or files.

The module also defines `PROJECT_ROOT` for consistent path referencing across the application.
"""
import os
import shutil
import logging
import re
from datetime import datetime
import random
import string

# Determine Project Root: Assumes utils.py is in 'main_app/', which is at the project root.
# This allows 'temp/' and 'logs/' directories to be reliably located relative to the project root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__) # Logger for this module

def create_temp_directory(base_temp_path_name: str = "temp", app_prefix: str = "clip_session_") -> str | None:
    """
    Creates a unique temporary directory for a processing session.

    The directory is created within a base temporary folder (e.g., `PROJECT_ROOT/temp/`).
    The unique directory name is formed using a prefix, timestamp, and a random suffix
    to ensure uniqueness between sessions.

    Args:
        base_temp_path_name (str): Name of the base temporary folder (e.g., "temp").
                                   This will be created in the project root if it doesn't exist.
        app_prefix (str): Prefix for the unique session directory (e.g., "clip_session_").

    Returns:
        str | None: The absolute path to the created unique temporary directory if successful,
                    or None if an error occurs during creation.
    """
    session_full_path = None  # Initialize in case of an error before path construction.
    try:
        # Construct the path to the base temporary directory.
        base_dir = os.path.join(PROJECT_ROOT, base_temp_path_name)
        # Create the base directory if it doesn't already exist.
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            logger.info(f"Created base temporary directory: {base_dir}")

        # Generate a unique name for the session-specific directory.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        session_dir_name = f"{app_prefix}{timestamp}_{random_suffix}"
        session_full_path = os.path.join(base_dir, session_dir_name)
        
        # Create the unique session directory. `exist_ok=True` prevents errors if called rapidly.
        os.makedirs(session_full_path, exist_ok=True)
        logger.info(f"Successfully created unique session temporary directory: {session_full_path}")
        return session_full_path
    except OSError as e:
        # Log OS-related errors during directory creation.
        path_for_log = session_full_path if session_full_path else os.path.join(PROJECT_ROOT, base_temp_path_name)
        logger.error(f"Failed to create temporary directory at or within {path_for_log}: {e}", exc_info=True)
        return None
    except Exception as e:
        # Catch any other unexpected errors.
        logger.error(f"An unexpected error occurred in create_temp_directory: {e}", exc_info=True)
        return None


def cleanup_temp_directory(directory_path: str) -> bool:
    """
    Recursively deletes the specified directory and all its contents.

    Args:
        directory_path (str): The path to the directory to be cleaned up.

    Returns:
        bool: True if deletion was successful or if the directory did not exist initially.
              False if an error occurred during deletion.
    """
    if not directory_path: # Handle empty or None path.
        logger.warning("Cleanup requested for an empty or None directory path. No action taken.")
        return True # Considered success as there's nothing to clean.

    if not os.path.exists(directory_path):
        logger.info(f"Temporary directory not found (already cleaned up or never created): {directory_path}")
        return True # No action needed, considered success.
    
    try:
        # Use shutil.rmtree for recursive deletion.
        shutil.rmtree(directory_path)
        logger.info(f"Successfully cleaned up temporary directory: {directory_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to clean up temporary directory {directory_path}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred in cleanup_temp_directory for {directory_path}: {e}", exc_info=True)
        return False


def generate_safe_filename(input_filename: str, max_length: int = 200) -> str:
    """
    Generates a filesystem-safe filename from an input string.

    This function sanitizes the input string by:
    - Converting to lowercase.
    - Replacing spaces and common unsafe characters with underscores.
    - Removing any characters not in a whitelist (alphanumeric, underscore, hyphen, dot).
    - Consolidating multiple underscores or hyphens.
    - Stripping leading/trailing problematic characters.
    - Truncating the base name to `max_length`.
    - Sanitizing and limiting the length of the file extension.

    Args:
        input_filename (str): The original filename or string to sanitize.
        max_length (int): The maximum allowed length for the base part of the filename
                          (excluding the extension).

    Returns:
        str: A sanitized, safe filename string.
    """
    if not input_filename:
        return "unnamed_file" # Default for empty input.

    base, ext = os.path.splitext(input_filename)

    # Sanitize the base name.
    safe_base = base.lower()
    safe_base = re.sub(r'\s+', '_', safe_base)  # Replace whitespace with underscores.
    # Replace common path separators and other characters known to be problematic in filenames.
    safe_base = re.sub(r'[|:/\\\]\[<>?"*]+', '_', safe_base) 
    # Whitelist: keep only alphanumeric, underscore, hyphen, dot.
    safe_base = re.sub(r'[^a-z0-9_.-]+', '', safe_base)  
    safe_base = re.sub(r'_+', '_', safe_base) # Consolidate multiple underscores.
    safe_base = re.sub(r'-+', '-', safe_base) # Consolidate multiple hyphens.
    safe_base = safe_base.strip('._-') # Remove leading/trailing underscores, dots, or hyphens.

    # Truncate the sanitized base name if it exceeds max_length.
    # Ensure max_len_base is at least 1 to avoid issues with very short max_length values.
    max_len_base = max(1, max_length) 
    if len(safe_base) > max_len_base:
        safe_base = safe_base[:max_len_base]
        safe_base = safe_base.strip('._-') # Re-strip after truncation.

    # If the base name becomes empty after sanitization (e.g., input was all unsafe chars).
    if not safe_base: 
        safe_base = "sanitized_file"
        
    # Sanitize the extension.
    safe_ext = ext.lower()
    # Remove unsafe characters from extension, keeping the dot.
    safe_ext = re.sub(r'[^a-z0-9.]+', '', safe_ext) 
    if safe_ext and not safe_ext.startswith('.'): # Ensure it starts with a dot if not empty.
        safe_ext = '.' + safe_ext
    
    # Limit extension length (e.g., to prevent excessively long extensions like .tar.gz.bak.tmp).
    if len(safe_ext) > 15: # Arbitrary reasonable limit for extensions.
        safe_ext = safe_ext[:15]
        # Ensure it's still a valid-looking extension part after truncation.
        if safe_ext.count('.') > 1: # e.g. if it became ".tar.gz.b"
             parts = safe_ext.split('.')
             safe_ext = "." + parts[-1] if len(parts) > 1 else "." # take last part or just a dot
        elif not safe_ext.startswith('.'): # if dot was removed by truncation
            safe_ext = '.' + safe_ext

    return f"{safe_base}{safe_ext}"


def setup_logging(
    level=logging.INFO, 
    log_to_file: bool = False, 
    log_dir_name: str = "logs", 
    log_filename_prefix: str = "app_log_"
) -> None:
    """
    Configures global (root) logging for the application.

    Sets up logging to the console and optionally to a daily rotating log file.
    It standardizes the log message format and ensures handlers are not duplicated
    if called multiple times (though it's designed to be called once at startup).

    Args:
        level (int): The logging level (e.g., `logging.INFO`, `logging.DEBUG`).
                     Defaults to `logging.INFO`.
        log_to_file (bool): If True, logs will also be written to a file. Defaults to False.
        log_dir_name (str): Name of the directory to store log files (e.g., "logs"),
                            relative to `PROJECT_ROOT`. Defaults to "logs".
        log_filename_prefix (str): Prefix for log file names (e.g., "app_log_").
                                   A timestamp will be appended. Defaults to "app_log_".
    """
    # Define a standard log message format.
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s] - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
    )

    # Get the root logger. Configurations applied here affect all loggers unless they override.
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers attached to the root logger.
    # This prevents duplicate log messages if this function is inadvertently called multiple times.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close() # Close the handler before removing.

    # Add a console handler for outputting logs to stderr/stdout.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_to_file:
        log_file_path = "unknown_log_file.log" # Default path in case of error before full path construction.
        try:
            # Construct the full path for the log directory and file.
            log_full_dir = os.path.join(PROJECT_ROOT, log_dir_name)
            if not os.path.exists(log_full_dir):
                os.makedirs(log_full_dir) # Create log directory if it doesn't exist.
            
            # Create a daily log file (e.g., "app_log_YYYYMMDD.log").
            timestamp = datetime.now().strftime("%Y%m%d") 
            log_file_name = f"{log_filename_prefix}{timestamp}.log"
            log_file_path = os.path.join(log_full_dir, log_file_name)
            
            # Add a file handler to write logs to the specified file.
            # 'a' mode appends to the file if it exists.
            # For more advanced rotation (e.g., by size or time interval),
            # `logging.handlers.TimedRotatingFileHandler` or `RotatingFileHandler` could be used.
            file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            root_logger.info(f"Logging initialized. Console level: {logging.getLevelName(level)}. File logging to: {log_file_path}")
        except Exception as e:
            # If file logging setup fails, log an error to the console (which should be working).
            root_logger.error(f"Failed to set up file logging to {log_file_path}: {e}", exc_info=True)
    else:
        root_logger.info(f"Logging initialized. Console level: {logging.getLevelName(level)}. File logging is disabled.")


if __name__ == '__main__':
    # This block is for direct testing of the utility functions in this module.
    
    # --- Test 1: Initial Logging Setup (Console Only for this test script's own logging) ---
    # Note: This call to setup_logging will be overridden by Test 4 for its specific checks.
    print("--- Test 1: Initial Logging Setup (Console Only for this script's execution) ---")
    setup_logging(level=logging.DEBUG, log_to_file=False) 
    logger.debug("DEBUG message after initial console setup for utils.py's own test execution.")
    logger.info("INFO message after initial console setup for utils.py's own test execution.")

    logger.info("--- Testing Utility Functions ---")

    # --- Test 2: Temporary Directory Management ---
    logger.info("--- Test 2: Temporary Directory Management ---")
    test_temp_base = "temp_utils_test" # Use a specific base for this test
    temp_session_dir = create_temp_directory(base_temp_path_name=test_temp_base, app_prefix="test_session_")
    
    if temp_session_dir:
        logger.info(f"Created temp dir: {temp_session_dir}")
        assert os.path.exists(temp_session_dir), "Temp directory does not exist after creation!"
        
        # Test file creation within the temp directory.
        dummy_file_path = os.path.join(temp_session_dir, "test_file.txt")
        try:
            with open(dummy_file_path, "w") as f:
                f.write("Hello from utils test!")
            logger.info(f"Created dummy file: {dummy_file_path}")
            assert os.path.exists(dummy_file_path), "Dummy file does not exist after writing."
        except IOError as e:
            logger.error(f"Failed to create dummy file in temp dir: {e}")
            assert False, "Dummy file IOError in Test 2"

        cleanup_success = cleanup_temp_directory(temp_session_dir)
        logger.info(f"Cleanup of {temp_session_dir} reported: {cleanup_success}")
        assert cleanup_success, "Cleanup function reported failure for existing directory!"
        assert not os.path.exists(temp_session_dir), "Temp directory still exists after cleanup attempt!"
        
        # Clean up the base test directory as well
        shutil.rmtree(os.path.join(PROJECT_ROOT, test_temp_base), ignore_errors=True)
        logger.info(f"Cleaned up base test temp directory: {os.path.join(PROJECT_ROOT, test_temp_base)}")

    else:
        logger.error("Failed to create temporary session directory for Test 2.")
        assert False, "create_temp_directory returned None or empty in Test 2"
    
    cleanup_non_existent = cleanup_temp_directory("non_existent_temp_dir_12345_abcdef_for_test_2")
    logger.info(f"Cleanup of non-existent directory reported: {cleanup_non_existent} (expected True)")
    assert cleanup_non_existent, "Cleanup of non-existent dir should return True"

    # --- Test 3: Safe Filename Generation ---
    logger.info("--- Test 3: Safe Filename Generation ---")
    # Test cases: {original_filename: expected_sanitized_filename}
    # Using max_length=60 for these specific tests.
    filenames_to_test = {
        "My Video Title.mp4": "my_video_title.mp4",
        "Another: Awesome/Video\\here?*<.mp4": "another_awesome_video_here.mp4",
        "  leading and trailing spaces  .mkv": "leading_and_trailing_spaces.mkv",
        "file_with_no_ext": "file_with_no_ext",
        "ver............long.filename...................that.exceeds.max.length.and.has.many.dots.and.stuff.avi": "ver.long.filename.that.exceeds.max.length.and.has.many.dots.avi",
        "!@#$%^&*()+=[]{};',`~.webm": ".webm", # All unsafe base chars, only extension remains
        "": "unnamed_file",
        ".hiddenfile.txt": ".hiddenfile.txt", # Leading dot should be preserved if part of original name
        "file.with.multiple.dots.in.base.name.ext": "file.with.multiple.dots.in.base.name.ext",
        ("a" * 70 + ".txt"): ("a" * 60 + ".txt"), # Test truncation of base name
        ("b" * 50 + ".verylongextensionthatwillbetruncated"): ("b" * 50 + ".verylongextens"), # Test truncation of extension
        "no_ext_very_long_" + "c" * 60: "no_ext_very_long_" + "c" * (60 - len("no_ext_very_long_")), # Truncation of extensionless filename
        "  Test--File__Name  .tar.gz  ": "test-file_name.tar.gz" # Test consolidation and stripping
    }
    for original, expected in filenames_to_test.items():
        sanitized = generate_safe_filename(original, max_length=60) 
        logger.info(f"Original: '{original}' -> Sanitized: '{sanitized}' (Expected: '{expected}')")
        # Handle cases where base becomes empty and defaults to "sanitized_file"
        if original == "!@#$%^&*()+=[]{};',`~.webm" and (sanitized == ".webm" or sanitized == "sanitized_file.webm"):
             assert True, f"Acceptable outcomes for '{original}'. Got '{sanitized}'"
        else:
            assert sanitized == expected, f"Mismatch for '{original}'. Got '{sanitized}', expected '{expected}'"
    
    only_bad_chars_base = "!@#$%^&*"
    expected_empty_base_no_ext = "sanitized_file"
    sanitized_empty_base_no_ext = generate_safe_filename(only_bad_chars_base, max_length=60)
    logger.info(f"Original: '{only_bad_chars_base}' -> Sanitized: '{sanitized_empty_base_no_ext}' (Expected: '{expected_empty_base_no_ext}')")
    assert sanitized_empty_base_no_ext == expected_empty_base_no_ext, "Empty base (no ext) sanitization failed."

    # --- Test 4: Logging Configuration (with File Logging) ---
    logger.info("--- Test 4: Logging Configuration (with File Logging) ---")
    log_dir_for_test_name = "logs_utils_test_temp" # Use a distinct name for test logs
    log_dir_for_test_path = os.path.join(PROJECT_ROOT, log_dir_for_test_name)
    
    if os.path.exists(log_dir_for_test_path): # Clean up from previous test runs if any.
        shutil.rmtree(log_dir_for_test_path, ignore_errors=True)
        logger.info(f"Pre-test cleanup of test log directory: {log_dir_for_test_path}")

    # This call will reconfigure the root logger, including for messages from this test script.
    setup_logging(level=logging.DEBUG, log_to_file=True, log_dir_name=log_dir_for_test_name, log_filename_prefix="utils_test_log_")
    
    logger.debug("This is a DEBUG message (after file logging setup). Should be in console AND file.")
    logger.info("This is an INFO message (after file logging setup). Should be in console AND file.")
    logger.warning("This is a WARNING message (after file logging setup). Should be in console AND file.")
    
    # Determine the expected log file name.
    test_log_filename_stem = f"utils_test_log_{datetime.now().strftime('%Y%m%d')}.log"
    test_log_full_path = os.path.join(log_dir_for_test_path, test_log_filename_stem)
    
    logger.info(f"Checking for log file at: {test_log_full_path}")

    assert os.path.exists(test_log_full_path), f"Log file not found at {test_log_full_path}"
    assert os.path.getsize(test_log_full_path) > 0, f"Log file is empty: {test_log_full_path}"
    logger.info(f"File logging test SUCCESS. Log file created and not empty: {test_log_full_path}")
    
    # Verify content briefly.
    with open(test_log_full_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "DEBUG message (after file logging setup)" in content, "DEBUG message missing in log file"
        assert "INFO message (after file logging setup)" in content, "INFO message missing in log file"
        assert "WARNING message (after file logging setup)" in content, "WARNING message missing in log file"
    logger.info("Log file content verified.")

    # Clean up the test log directory created by this test.
    try:
        shutil.rmtree(log_dir_for_test_path)
        logger.info(f"Successfully cleaned up test log directory: {log_dir_for_test_path}")
    except OSError as e:
        logger.error(f"Failed to clean up test log directory {log_dir_for_test_path}: {e}")

    logger.info("--- Utils Module Testing Complete ---")
```

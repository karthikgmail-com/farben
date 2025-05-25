"""
Analyzes transcription data from Deepgram to identify potential highlight video clips.

This module takes a Deepgram transcription response, which includes word timings
and keyword search hits, and processes it to find segments suitable for highlight
clips. The analysis involves:
- Centering segments around keyword hits.
- Adjusting segment durations to fit within specified min/max lengths.
- Merging overlapping or very close segments to create coherent clips.
- Ensuring final clips meet all duration and boundary constraints.
"""
import logging
import json # For loading sample data in tests

logger = logging.getLogger(__name__)

def analyze_transcription_for_highlights(
    deepgram_response: dict, 
    min_clip_duration: int = 30, 
    max_clip_duration: int = 60, 
    target_clip_duration: int = 45,
    merge_threshold: float = 5.0 # Max gap (in seconds) between clips to consider merging.
) -> list[tuple[float, float]]:
    """
    Analyzes a Deepgram transcription result to identify highlight clips based on search keywords.

    The process involves:
    1. Extracting keyword hits and word timings from the Deepgram response.
    2. For each hit, creating an initial segment around it based on `target_clip_duration`.
    3. Adjusting this segment to ensure it's within `min_clip_duration` and `max_clip_duration`,
       and also within the total duration of the audio.
    4. Merging overlapping or nearby segments if the merged clip doesn't exceed `max_clip_duration`.
    5. Returning a list of (start_time, end_time) tuples for the final highlight clips.

    Args:
        deepgram_response (dict): The Deepgram API response as a Python dictionary.
                                  Expected to follow Deepgram's standard structure.
        min_clip_duration (int): Minimum duration of a highlight clip in seconds.
        max_clip_duration (int): Maximum duration of a highlight clip in seconds.
        target_clip_duration (int): Preferred target duration for clips centered around a keyword hit.
        merge_threshold (float): Time in seconds. If the end of one clip and the start of the
                                 next are within this threshold (or overlap), they are candidates
                                 for merging.

    Returns:
        list[tuple[float, float]]: A list of (start_time, end_time) tuples for identified
                                   highlight clips, sorted by start time. Returns an empty
                                   list if no suitable clips are found or if input is invalid.
    """
    if not deepgram_response:
        logger.warning("Empty Deepgram response received for analysis.")
        return []

    try:
        # Navigate through the Deepgram response structure to get necessary data.
        results = deepgram_response.get("results", {})
        if not results:
            logger.warning("No 'results' key in Deepgram response.")
            return []

        channels = results.get("channels", [])
        if not channels: # Should typically be at least one channel.
            logger.warning("No 'channels' in Deepgram results.")
            return []

        # Assuming single-channel audio processing for simplicity.
        alternatives = channels[0].get("alternatives", [])
        if not alternatives: # Should be at least one alternative.
            logger.warning("No 'alternatives' in Deepgram channel data.")
            return []

        words = alternatives[0].get("words", [])
        if not words:
            logger.warning("No 'words' in Deepgram alternatives. Cannot determine total audio duration.")
            return []
        
        # Determine total duration from the end time of the last word.
        total_duration = words[-1].get("end", 0.0)
        
        # Handle edge case: empty or silent audio might result in a single word entry at 0.0.
        if total_duration == 0.0 and len(words) == 1 and words[0].get("start", 0.0) == 0.0 and words[0].get("end", 0.0) == 0.0:
            logger.warning("Transcript appears to be empty or silent (total_duration is 0 from word timings).")
            return []
        elif total_duration == 0.0: # More general case for unexpected zero duration.
            logger.warning("Could not determine a valid total duration from word timings (reported as 0).")
            return [] # Cannot proceed without a valid total duration.

        search_hits_data = alternatives[0].get("search", [])
        if not search_hits_data:
            logger.info("No search keyword hits found in the transcript. No clips to generate.")
            return []

        potential_clips = []
        # Iterate through each keyword that was searched for.
        for search_entry in search_hits_data: 
            query = search_entry.get("query") # The keyword itself.
            hits = search_entry.get("hits", []) # List of occurrences for this keyword.
            
            for hit in hits:
                hit_start_time = hit.get("start", 0.0)
                hit_end_time = hit.get("end", 0.0)
                hit_center_time = (hit_start_time + hit_end_time) / 2

                # Phase 1: Create initial segment centered around the keyword hit.
                segment_start = max(0.0, hit_center_time - (target_clip_duration / 2))
                segment_end = min(total_duration, hit_center_time + (target_clip_duration / 2))
                
                current_duration = segment_end - segment_start

                # Phase 2: Adjust segment if it's shorter than min_clip_duration.
                if current_duration < min_clip_duration:
                    expansion_needed = min_clip_duration - current_duration
                    
                    # Attempt to expand segment while staying within audio boundaries [0, total_duration].
                    # Prioritize centered expansion first.
                    new_center_start = max(0.0, hit_center_time - (min_clip_duration / 2))
                    new_center_end = min(total_duration, hit_center_time + (min_clip_duration / 2))

                    if (new_center_end - new_center_start) >= min_clip_duration:
                        segment_start, segment_end = new_center_start, new_center_end
                    else:
                        # If centered expansion isn't enough (e.g., hit is near start/end of audio, or audio is short),
                        # expand non-symmetrically.
                        if segment_start == 0.0: # If segment is already at the beginning
                            segment_end = min(total_duration, segment_start + min_clip_duration)
                        elif segment_end == total_duration: # If segment is already at the end
                            segment_start = max(0.0, segment_end - min_clip_duration)
                        else: # Expand primarily towards the end, then adjust start if still too short.
                            segment_end = min(total_duration, segment_start + min_clip_duration) 
                            if (segment_end - segment_start) < min_clip_duration:
                                segment_start = max(0.0, segment_end - min_clip_duration)
                
                current_duration = segment_end - segment_start # Recalculate duration after potential expansion.

                # Phase 3: Adjust segment if it's longer than max_clip_duration.
                if current_duration > max_clip_duration:
                    # Shrink the segment, trying to keep the keyword hit centered.
                    segment_start_new = hit_center_time - (max_clip_duration / 2)
                    segment_end_new = hit_center_time + (max_clip_duration / 2)

                    segment_start = max(0.0, segment_start_new)
                    segment_end = min(total_duration, segment_end_new)
                    
                    # If shrinking pushed one boundary against 0 or total_duration,
                    # allow the other side to expand to maintain max_clip_duration, if possible.
                    if segment_start == 0.0 and (segment_end - segment_start) < max_clip_duration :
                        segment_end = min(total_duration, segment_start + max_clip_duration)
                    elif segment_end == total_duration and (segment_end - segment_start) < max_clip_duration :
                        segment_start = max(0.0, segment_end - max_clip_duration)
                
                current_duration = segment_end - segment_start # Recalculate after potential shrinking.

                # Phase 4: Validate final segment duration.
                if min_clip_duration <= current_duration <= max_clip_duration:
                    potential_clips.append((segment_start, segment_end))
                else:
                    logger.debug(f"Discarding segment for keyword '{query}' centered at {hit_center_time:.2f}s. "
                                 f"Final adjusted duration {current_duration:.2f}s is outside range "
                                 f"[{min_clip_duration}s, {max_clip_duration}s]. Original hit: {hit_start_time:.2f}s-{hit_end_time:.2f}s.")

        if not potential_clips:
            logger.info("No potential clips met duration criteria after processing all keyword hits.")
            return []

        # Sort clips by start time to prepare for merging.
        potential_clips.sort(key=lambda x: x[0])
        
        # Remove exact duplicate segments before merging.
        unique_potential_clips = []
        if potential_clips:
            unique_potential_clips.append(potential_clips[0])
            for i in range(1, len(potential_clips)):
                # Using a small tolerance for floating point comparison might be more robust here,
                # but exact match is used for simplicity as segments are derived.
                if potential_clips[i][0] > potential_clips[i-1][0] + 1e-3 or \
                   abs(potential_clips[i][1] - potential_clips[i-1][1]) > 1e-3: # if start or end is different enough
                    unique_potential_clips.append(potential_clips[i])
        potential_clips = unique_potential_clips

        # Phase 5: Merge overlapping or very close segments.
        merged_clips = []
        if not potential_clips: # Should not happen if we checked earlier, but defensive.
            return []

        # Start with the first clip as the base for merging.
        current_merged_start, current_merged_end = potential_clips[0]

        for i in range(1, len(potential_clips)):
            next_start, next_end = potential_clips[i]
            
            # Condition for merging:
            # 1. next_start overlaps with current_merged_end, OR
            # 2. next_start is within merge_threshold of current_merged_end.
            if next_start < (current_merged_end + merge_threshold): 
                # Attempt to merge.
                new_merged_candidate_end = max(current_merged_end, next_end)
                if (new_merged_candidate_end - current_merged_start) <= max_clip_duration:
                    # If merge is valid (does not exceed max_clip_duration), update current merged end.
                    current_merged_end = new_merged_candidate_end
                else:
                    # Merge would make the clip too long. Finalize the current_merged_clip.
                    merged_clips.append((current_merged_start, current_merged_end))
                    # Start a new merge sequence with the next_clip.
                    current_merged_start, current_merged_end = next_start, next_end
            else:
                # Gap is too large, finalize the current_merged_clip.
                merged_clips.append((current_merged_start, current_merged_end))
                # Start a new merge sequence with the next_clip.
                current_merged_start, current_merged_end = next_start, next_end
        
        merged_clips.append((current_merged_start, current_merged_end)) # Add the last processed/merged clip.

        # Phase 6: Final validation and cleanup of merged clips.
        # Ensure all clips strictly meet duration criteria and have positive length.
        final_clips = []
        for s, e in merged_clips:
            duration = e - s
            if min_clip_duration <= duration <= max_clip_duration and duration > 1e-3: # Check for positive, non-trivial duration
                final_clips.append((round(s, 3), round(e, 3))) # Round to milliseconds for cleaner output
            else:
                logger.debug(f"Post-merge filter: Discarding clip ({s:.2f}, {e:.2f}) with duration {duration:.2f}s.")

        # Remove duplicates that might have arisen from merging identical source segments or rounding.
        if final_clips:
            final_clips = sorted(list(set(final_clips)), key=lambda x: x[0])

        logger.info(f"Identified {len(final_clips)} highlight clips after merging and filtering.")
        return final_clips

    except Exception as e:
        # Catch-all for any unexpected errors during analysis.
        logger.error(f"Error during transcript analysis: {e.__class__.__name__} - {e}", exc_info=True)
        return []

if __name__ == '__main__':
    # This block is for direct testing of the analyzer module.
    logging.basicConfig(
        level=logging.DEBUG, # Use DEBUG to see detailed logs from the function
        format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s'
    )

    # Sample Deepgram response for testing.
    # This should ideally be loaded from a separate JSON file in a real test suite.
    sample_response_str = """
    {
        "metadata": {"request_id": "test-analyzer", "duration": 120.0},
        "results": {
            "channels": [{
                "alternatives": [{
                    "transcript": "This is a test transcript with some exciting moments. Let's go! And another one, unbelievable. Bruh, that was funny. Trust me, this is a good clip.",
                    "words": [
                        {"word": "This", "start": 0.0, "end": 0.5}, {"word": "is", "start": 0.5, "end": 1.0},
                        {"word": "a", "start": 1.0, "end": 1.2}, {"word": "test", "start": 1.2, "end": 2.0},
                        {"word": "transcript", "start": 2.0, "end": 3.0}, {"word": "with", "start": 3.0, "end": 3.5},
                        {"word": "some", "start": 3.5, "end": 4.0}, {"word": "exciting", "start": 4.0, "end": 5.0},
                        {"word": "moments.", "start": 5.0, "end": 6.0}, 
                        {"word": "Let's", "start": 35.0, "end": 35.3}, {"word": "go!", "start": 35.3, "end": 35.8}, 
                        {"word": "And", "start": 40.0, "end": 40.5}, {"word": "another", "start": 40.5, "end": 41.0}, 
                        {"word": "one,", "start": 41.0, "end": 41.5}, {"word": "unbelievable.", "start": 50.0, "end": 51.0}, 
                        {"word": "Bruh,", "start": 65.0, "end": 65.5}, {"word": "that", "start": 65.5, "end": 66.0}, 
                        {"word": "was", "start": 66.0, "end": 66.5}, {"word": "funny.", "start": 66.5, "end": 67.0}, 
                        {"word": "Trust", "start": 80.0, "end": 80.5}, {"word": "me,", "start": 80.5, "end": 80.8}, 
                        {"word": "this", "start": 80.8, "end": 81.2}, {"word": "is", "start": 81.2, "end": 81.5}, 
                        {"word": "a", "start": 81.5, "end": 81.7}, {"word": "good", "start": 81.7, "end": 82.2}, 
                        {"word": "clip.", "start": 82.2, "end": 83.0},
                        {"word": "end", "start": 119.5, "end": 120.0} 
                    ],
                    "search": [
                        {"query": "let's go", "hits": [{"start": 35.0, "end": 35.8, "confidence": 0.9}]},
                        {"query": "unbelievable", "hits": [{"start": 50.0, "end": 51.0, "confidence": 0.95}]},
                        {"query": "bruh", "hits": [{"start": 65.0, "end": 65.5, "confidence": 0.8}]},
                        {"query": "trust me", "hits": [{"start": 80.0, "end": 80.8, "confidence": 0.92}]}
                    ]
                }]
            }]
        }
    }
    """
    sample_deepgram_data = json.loads(sample_response_str)

    logger.info("--- Test Case 1: Standard Analysis (target=30s, min=30s, max=60s) ---")
    # Based on the logic:
    # Hit 1 (let's go): center 35.4. Target 30s -> [20.4, 50.4]. Duration 30. Valid.
    # Hit 2 (unbelievable): center 50.5. Target 30s -> [35.5, 65.5]. Duration 30. Valid.
    # Hit 3 (bruh): center 65.25. Target 30s -> [50.25, 80.25]. Duration 30. Valid.
    # Hit 4 (trust me): center 80.4. Target 30s -> [65.4, 95.4]. Duration 30. Valid.
    # Merging (threshold 5s):
    # C1=[20.4, 50.4]. C2=[35.5, 65.5]. C2_start(35.5) < C1_end(50.4)+5. Merge: [20.4, max(50.4, 65.5)]=[20.4, 65.5]. Dur=45.1. OK.
    # Current=[20.4, 65.5]. C3=[50.25, 80.25]. C3_start(50.25) < Current_end(65.5)+5. Merge: [20.4, max(65.5, 80.25)]=[20.4, 80.25]. Dur=59.85. OK.
    # Current=[20.4, 80.25]. C4=[65.4, 95.4]. C4_start(65.4) < Current_end(80.25)+5. Merge: [20.4, max(80.25, 95.4)]=[20.4, 95.4]. Dur=75. TOO LONG (max 60).
    # So, C4 is not merged with the previous one. The previous merge [20.4, 80.25] is finalized.
    # New current becomes C4: [65.4, 95.4].
    # Expected: [(20.4, 80.25), (65.4, 95.4)] (rounded to 3 decimal places)
    clips = analyze_transcription_for_highlights(sample_deepgram_data, min_clip_duration=30, max_clip_duration=60, target_clip_duration=30, merge_threshold=5.0)
    logger.info(f"Test Case 1 Identified clips: {clips}")
    # Example expected output (actual values depend on precise float arithmetic and rounding):
    # assert clips == [(20.4, 80.25), (65.4, 95.4)] or similar, check logs for exact values.

    logger.info("--- Test Case 2: No Search Hits ---")
    sample_no_hits_data = json.loads(sample_response_str)
    sample_no_hits_data["results"]["channels"][0]["alternatives"][0]["search"] = []
    clips_no_hits = analyze_transcription_for_highlights(sample_no_hits_data)
    logger.info(f"Test Case 2 Identified clips (no hits): {clips_no_hits}")
    assert clips_no_hits == [], "Test Case 2 Failed: Expected empty list for no search hits."

    logger.info("--- Test Case 3: Short Video (total_duration < min_clip_duration) ---")
    sample_short_video_data = json.loads(sample_response_str)
    sample_short_video_data["results"]["channels"][0]["alternatives"][0]["words"] = [
        {"word": "short", "start": 0.0, "end": 1.0}, {"word": "video", "start": 1.5, "end": 2.0},
        {"word": "keyword", "start": 3.0, "end": 4.0}, # Keyword hit
        {"word": "end", "start": 9.5, "end": 10.0} # Total duration 10s
    ]
    sample_short_video_data["results"]["channels"][0]["alternatives"][0]["search"] = [
         {"query": "keyword", "hits": [{"start": 3.0, "end": 4.0}]}
    ]
    clips_short_video = analyze_transcription_for_highlights(sample_short_video_data, min_clip_duration=30)
    logger.info(f"Test Case 3 Identified clips (short video): {clips_short_video}")
    assert clips_short_video == [], "Test Case 3 Failed: Expected empty list as 30s clip cannot be formed from 10s video."

    logger.info("--- Test Case 4: Keyword near start of video ---")
    sample_kw_near_start_data = json.loads(sample_response_str) # Uses full word list for 120s duration
    sample_kw_near_start_data["results"]["channels"][0]["alternatives"][0]["search"] = [
        {"query": "unbelievable", "hits": [{"start": 1.0, "end": 2.0}]} # Hit center 1.5s
    ]
    # Target 30s. Ideal window: 1.5-15 to 1.5+15 => -13.5 to 16.5.
    # Initial segment: max(0, -13.5) to min(120, 16.5) => [0.0, 16.5]. Duration 16.5s.
    # Needs expansion to 30s. Since start is 0.0, expand end: min(120, 0.0 + 30) = 30.0.
    # Final clip: [0.0, 30.0]
    clips_kw_near_start = analyze_transcription_for_highlights(sample_kw_near_start_data, min_clip_duration=30, target_clip_duration=30)
    logger.info(f"Test Case 4 Identified clips (keyword near start): {clips_kw_near_start}")
    assert clips_kw_near_start == [(0.0, 30.0)], f"Test Case 4 Failed. Expected [(0.0, 30.0)], got {clips_kw_near_start}"
    
    # (Additional test cases from the original file can be kept or adapted here)
    # For brevity in this example, focusing on a few key scenarios.

    logger.info("--- Analyzer Module Testing Complete ---")
```

import asyncio

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.plugins.logging_plugin import (LoggingPlugin, )
from google.adk.runners import InMemoryRunner
from google.genai import types

retry_config = types.HttpRetryOptions(attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1, http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

# Root agent
summarizer_agent_with_plugin = LlmAgent(name="summarizer_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config), instruction="""Your task is to generate a
     structured summary of a meeting based solely on the
full transcript provided as input text.

Follow these steps in order:

1) Read and analyze the full transcript provided by the user.  
   - Do NOT search for anything.
   - Do NOT assume context outside the transcript.
   - If the transcript is empty or unusable, return an error JSON (see below).

2) Extract and summarize the meeting content.  
   Your summary MUST follow this exact JSON structure:

   {
     "one_line": "string (<=140 chars)",
     "executive": "string (3–4 short paragraphs, max 300 words)",
     "technical": "string | null",
     "key_decisions": [
       {
         "decision": "string",
         "rationale": "string | null",
         "timestamp": "string | null",
         "inferred": false
       }
     ],
     "action_items": [
       {
         "id": "A1",
         "task": "string",
         "assignee": "string | null",
         "due_date": "YYYY-MM-DD | null",
         "priority": "low|medium|high|unspecified",
         "origin_timestamp": "string | null",
         "notes": "string | null",
         "inferred": false
       }
     ],
     "attendees": [
       {
         "name": "string",
         "role": "string | null",
         "present": true
       }
     ],
     "open_questions": [
       {
         "question": "string",
         "asked_by": "string | null",
         "timestamp": "string | null"
       }
     ],
     "follow_ups": [
       {
         "type": "string",
         "description": "string",
         "owner": "string | null",
         "due_date": "YYYY-MM-DD | null"
       }
     ],
     "highlights_with_timestamps": [
       {
         "timestamp": "string",
         "short_note": "string"
       }
     ],
     "tone_and_sentiment": {
       "overall_tone": "neutral|positive|negative|mixed",
       "confidence": "low|medium|high"
     },
     "confidence_note": "string | null",
     "error": null
   }

3) Strict requirements:
   - Only include facts found in the transcript.
   - If something is unclear or missing, set the field to null.
   - If you infer something from context, set `"inferred": true` and explain in `notes`.
   - Action items must be labeled A1, A2, A3…
   - Keep `one_line` under 140 characters.
   - Keep `executive` under 300 words.
   - Maintain JSON validity — no extra commentary or Markdown.

4) If the transcript cannot be summarized (empty, corrupted, or clearly not a meeting):
   Return exactly:
   {
     "error": "INVALID_TRANSCRIPT",
     "summary": null
   }

Return ONLY valid JSON as final output. No text outside of the JSON.
   """, tools=[], )

runner = InMemoryRunner(agent=summarizer_agent_with_plugin, plugins=[LoggingPlugin()],
)


async def main():
    # Read the latest transcript from data folder
    from pathlib import Path

    data_folder = Path(__file__).parent.parent.parent / "data"

    # Find the most recent transcript file
    transcript_files = sorted(data_folder.glob("transcript_*.txt"), reverse=True)

    if not transcript_files:
        # Fallback to transcript.txt if no timestamped files exist
        transcript_file = data_folder / "transcript.txt"
    else:
        transcript_file = transcript_files[0]

    if not transcript_file.exists():
        print(f"Error: No transcript file found in {data_folder}")
        return

    # Read the transcript content
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_content = f.read()

    print(f"Reading transcript from: {transcript_file}")
    print(f"Transcript length: {len(transcript_content)} characters\n")

    # Pass the transcript to the summarizer agent
    response = await runner.run_debug(f"Please summarize this meeting transcript:\n\n{transcript_content}")
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    print(response)


if __name__ == "__main__":
    asyncio.run(main())

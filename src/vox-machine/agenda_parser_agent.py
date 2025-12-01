import asyncio
import json
from datetime import datetime
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.plugins.logging_plugin import (LoggingPlugin, )
from google.adk.runners import InMemoryRunner
from google.genai import types

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

# Root agent
agenda_parser_agent = LlmAgent(
    name="agenda_parser_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""Your task is to map sections of a meeting transcript to the topics listed in the meeting agenda.

You will receive:
1. A meeting agenda with numbered topics
2. A full meeting transcript

Follow these steps:

1) Parse the agenda to identify all agenda topics.
   - Extract the topic title/description from each agenda item.
   - Preserve the original numbering and structure.

2) Analyze the transcript and split it into sections that correspond to each agenda topic.
   - Use context clues, keywords, and flow to determine which parts of the transcript belong to which topic.
   - If multiple topics are discussed in an interleaved manner, assign text to the most relevant topic.
   - DO NOT modify, summarize, or paraphrase the transcript text.
   - Include the full transcript text for each section.

3) If parts of the transcript don't clearly map to any agenda item, create a special topic called "Other Discussion" or "Off-topic".

4) Output MUST be valid JSON with this exact structure:

{
  "meeting_metadata": {
    "date": "string | null",
    "attendees": ["string"] | null,
    "parsed_at": "ISO-8601 timestamp"
  },
  "agenda_topics": [
    {
      "topic_id": "string (e.g., '1', '2', 'intro')",
      "topic_title": "string",
      "duration_estimate": "string | null (e.g., '5 min')",
      "transcript_sections": [
        {
          "text": "string (exact transcript text)",
          "confidence": "high|medium|low",
          "reasoning": "string | null (brief explanation of why this section belongs here)"
        }
      ]
    }
  ],
  "unmapped_sections": [
    {
      "text": "string (exact transcript text)",
      "note": "string (why this couldn't be mapped)"
    }
  ],
  "error": null
}

5) Important rules:
   - Preserve exact transcript text — do NOT paraphrase, summarize, or edit.
   - Every part of the transcript MUST appear in exactly one section (either mapped or unmapped).
   - Maintain chronological order of the transcript.
   - If the transcript is empty or the agenda is missing, return an error:
     {
       "error": "MISSING_INPUT",
       "agenda_topics": null
     }

Return ONLY valid JSON. No Markdown, no extra commentary.""",
    tools=[],
)

runner = InMemoryRunner(
    agent=agenda_parser_agent,
    plugins=[LoggingPlugin()],
)


async def main():
    data_folder = Path(__file__).parent.parent.parent / "data"

    # Read agenda file
    agenda_file = data_folder / "agenda.md"
    transcript_file = data_folder / "transcript_20251129_09-21-47.txt"

    if not agenda_file.exists():
        print(f"Error: Agenda file not found at {agenda_file}")
        return

    if not transcript_file.exists():
        print(f"Error: Transcript file not found at {transcript_file}")
        return

    # Read both files
    with open(agenda_file, 'r', encoding='utf-8') as f:
        agenda_content = f.read()

    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_content = f.read()

    print(f"Reading agenda from: {agenda_file}")
    print(f"Agenda length: {len(agenda_content)} characters")
    print(f"\nReading transcript from: {transcript_file}")
    print(f"Transcript length: {len(transcript_content)} characters\n")

    # Prepare the input for the agent
    agent_input = f"""Here is the meeting agenda:

{agenda_content}

---

Here is the full meeting transcript:

{transcript_content}

---

Please map the transcript sections to the agenda topics and return the result as JSON.
IMPORTANT: Do not invent anything that is not in the transcript or agenda."""

    # Pass both to the agenda parser agent
    print("Processing with agenda parser agent...")
    response = await runner.run_debug(agent_input)

    # Parse the JSON response
    try:
        # Extract JSON from response if it's wrapped in markdown
        response_text = str(response)
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            json_str = response_text.strip()

        parsed_json = json.loads(json_str)

        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H-%M-%S")
        output_file = data_folder / f"agenda_mapping_{timestamp}.json"

        # Write to file with pretty formatting
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)

        print("\n" + "="*80)
        print(f"AGENDA MAPPING SAVED TO: {output_file}")
        print("="*80)
        print(f"\nFound {len(parsed_json.get('agenda_topics', []))} agenda topics")

        # Print summary
        for topic in parsed_json.get('agenda_topics', []):
            section_count = len(topic.get('transcript_sections', []))
            print(f"  - {topic.get('topic_title', 'Unknown')}: {section_count} transcript section(s)")

        unmapped = len(parsed_json.get('unmapped_sections', []))
        if unmapped > 0:
            print(f"\n⚠️  {unmapped} unmapped section(s) found")

    except json.JSONDecodeError as e:
        print("\n" + "="*80)
        print("ERROR: Failed to parse JSON response")
        print("="*80)
        print(f"JSON Error: {e}")
        print("\nRaw response:")
        print(response)

        # Save raw response anyway
        timestamp = datetime.now().strftime("%Y%m%d_%H-%M-%S")
        error_file = data_folder / f"agenda_mapping_error_{timestamp}.txt"
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(str(response))
        print(f"\nRaw response saved to: {error_file}")


if __name__ == "__main__":
    asyncio.run(main())


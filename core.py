from functools import lru_cache
from pathlib import Path
import os

from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


# ============================================================
# ENV LOADING (CRITICAL FOR EXE)
# ============================================================

# Always load .env from current working directory
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))


# ============================================================
# SAFE OUTPUT DIRECTORY (USER MACHINE)
# ============================================================

# C:\Users\<User>\ItineraryApp\
DEFAULT_OUTPUT_DIR = Path(
    os.getenv("USERPROFILE", os.getcwd())
) / "ItineraryApp"

DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# MODEL CONFIG
# ============================================================

class ModelConfig(BaseSettings):
    # -------------------------
    # Gemini
    # -------------------------
    MODEL_NAME: str = Field("gemini-2.0-flash", env="MODEL_NAME")
    API_KEY: str = Field(..., env="GEMINI_API_KEY")  # REQUIRED

    TEMPERATURE: float = Field(0.8, env="TEMPERATURE")
    TOP_P: float = Field(0.9, env="TOP_P")
    MAX_OUTPUT_TOKENS: int = Field(4096, env="MAX_OUTPUT_TOKENS")

    # -------------------------
    # Output / Storage
    # -------------------------
    OUTPUT_EXCEL_PATH: str = Field(
        str(DEFAULT_OUTPUT_DIR / "generated_itineraries.xlsx"),
        env="OUTPUT_EXCEL_PATH"
    )

    OUTPUT_SHEET_NAME: str = Field(
        "Itineraries",
        env="OUTPUT_SHEET_NAME"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# ============================================================
# CACHED CONFIG ACCESSOR
# ============================================================

@lru_cache(maxsize=1)
def get_model_config() -> ModelConfig:
    """
    Cached access to config.
    Safe for Streamlit re-runs + EXE execution.
    """
    return ModelConfig()



ITINERARY_PROMPT = """
You are a travel researcher and cultural-historical guide. Your job is to generate Hindu temple/sacred-site itineraries that STRICTLY follow the user's filters.

============================
ABSOLUTE OUTPUT RULES — READ FIRST
============================

- Output ONLY the itineraries, summaries, verification checklists, and source lists.
- Do NOT add filler text such as:
  "Here is your result", "As requested", "Sure", "I generated this", 
  or any conversational/meta content.
- Do NOT ask the user ANY questions.
- If **any filter is missing**, assume the most reasonable and culturally appropriate default and continue.
- The output must begin IMMEDIATELY with the itinerary content.
- No greetings, no commentary, no apologies, no explanations.

============================
USER FILTERS (from backend)
============================
Days Count Provided: "{days_count}"
Region Provided: "{region}"
Deity Focus: "{deity}"
Yatra Specifics: "{yatra_specifics}"
Pace: "{pace}"
Transport Preference: "{transport}"
Interests: "{interests}"
User Specific Prompt: "{prompt}"

============================
INSTRUCTIONS — READ CAREFULLY
============================

1. **Dynamic Filter Matching (with defaults):**
   - If `days_count` is provided:
         days_count="3" → generate ONLY a 3-day itinerary.
         days_count="3,5" → generate ONLY 3-day and 5-day itineraries.
   - If `days_count` is missing or empty → default to generating 3-day, 4-day, and 5-day itineraries.

   - If `region` is provided → use it exactly.
   - If `region` is missing → assume the most popular pilgrimage region in India based on the deity or yatra specifics.
       • If deity is Shaiva → default: "Kashi, Varanasi, Uttar Pradesh"
       • If deity is Vaishnava → default: "Tirupati, Andhra Pradesh"
       • If deity is Shakti → default: "Kolkata + Tarapith region, West Bengal"
       • If no deity given → default: "Tamil Nadu temple circuit"

   - If `deity` (deity) is provided → prioritize temples for that deity.
   - If missing → assume general Hindu sacred sites.

   - If `yatra_specifics` is provided → follow it exactly.
   - If missing → no yatra constraints.

   - If `dates` missing → assume travel suitable for typical Indian weather (e.g., winter-neutral).

   - If `pace` missing → assume moderate.
   - If `transport` missing → assume a mix (auto + taxi).
   - If `interests` missing → assume history + temple rituals.
   - If `mobility` missing → assume no mobility issues.

2. **Itinerary Requirements (for each valid itinerary length):**
   - Time windows with morning/afternoon/evening and hours.
   - 1–2 line significance with factual citations.
   - Logistics: distance, travel time, transport mode, estimated cost.
   - Practical details: dress code, phone/camera rules, entry fees, darshan timings.
   - One recommended restaurant + one budget option.
   - One quieter alternative temple.
   - Accessibility notes and seasonal restrictions.
   - Safety tips + packing list.

3. **Sources & Verification Rules:**
   - Every changeable fact needs an inline citation from:
       ASI, State Tourism, Temple Boards, UNESCO,
       The Hindu, Indian Express, district authorities.
   - If unverified → label “unverified” + how to confirm.

4. **Output Structure:**
   - Confirm the interpreted filters ONLY if ambiguous.
   - Provide itineraries for the lengths allowed by filters.
   - Each itinerary must include:
       a) Detailed day-by-day version  
       b) Short 6–8 line summary  
       c) Verification checklist  
       d) Numbered source list with date accessed  

============================
GENERATE THE ITINERARY
============================

Using the filters above, produce ONLY the valid itinerary lengths.
If there are any user specific promt, please accomodate that.
Assume defaults where needed and do not ask the user for anything.

"""

import streamlit as st
from loguru import logger
from google.genai import Client, types
from export_service import export_itinerary 
from view_models import ItenaryFilters
from core import ITINERARY_PROMPT, get_model_config


# -------------------------------------------------------
# Logger config
# -------------------------------------------------------
logger.add("itinerary_app.log", rotation="5 MB", level="DEBUG")


# -------------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------------
st.set_page_config(page_title="Itinerary Prompt Builder", layout="centered")

st.markdown(
    """
    <div style='text-align:center; margin-top:-30px;'>
        <h1 style='font-size:42px;'>🛕 Itinerary Prompt Builder</h1>
        <p style='font-size:18px; color:gray;'>
            Craft detailed, culturally rich temple travel itineraries with ease.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ----- User Main Prompt -----
user_prompt = st.text_area(
    "Additional Prompt",
    placeholder="Enter any additional instructions (ITINERARY_PROMPT will override most of this)...",
    height=50
)


st.subheader("Filters")

# --------- ROW 1 (3 columns) ---------
col1, col2, col3 = st.columns(3)

with col1:
    days_count = st.number_input(
        "Days Count",
        min_value=1,
        max_value=30,
        step=1,
        value=1
    )

with col2:
    region = st.text_input(
        "Region",
        placeholder="e.g. Varanasi, Tamil Nadu"
    )

with col3:
    deity = st.text_input(
        "Deity",
        placeholder="e.g. Shiva, Vishnu"
    )

# --------- ROW 2 (3 columns) ---------
col4, col5, col6 = st.columns(3)

with col4:
    yatra_specifics = st.text_input(
        "Yatra Specifics",
        placeholder="e.g. Panch Bhoota Lingas"
    )

with col5:
    pace = st.selectbox(
        "Pace",
        ["Comfortable", "Relaxed", "Moderate", "Fast"]
    )

with col6:
    transport = st.selectbox(
        "Transport Preference",
        ["Airways only", "Public", "Private car", "No specifics"]
    )

# --------- ROW 3 (full width for Interests) ---------
interests = st.text_input(
    "Interests",
    placeholder="history, rituals, architecture..."
)


filters = ItenaryFilters(
    days_count=days_count,
    region=region or None,
    deity=deity or None,
    yatra_specifics=yatra_specifics or None,
    pace=pace or None,
    transport_preference=transport or None,
    specific_interests=interests or None,
    additional_prompt=user_prompt
)


# -------------------------------------------------------
# PROMPT BUILDING
# -------------------------------------------------------

def __configure_model():
    """
    Returns a configured GenAI client.
    """
    model_config = get_model_config()
    client = Client(api_key=model_config.API_KEY)
    return client


def __build_prompt(filters: ItenaryFilters) -> str:
    """
    Build the LLM prompt using ITINERARY_PROMPT.format(...)
    """
    logger.debug("Building final prompt...")

    try:
        final_prompt = ITINERARY_PROMPT.format(
            days_count=filters.days_count or "",
            region=filters.region or "",
            deity=filters.deity or "",
            yatra_specifics=filters.yatra_specifics or "",
            pace=filters.pace or "",
            transport=filters.transport_preference or "",
            interests=filters.specific_interests or "",
            prompt=filters.additional_prompt or ""
        )
        return final_prompt

    except Exception as e:
        logger.exception(f"Prompt formatting failed: {e}")
        raise


def __query_model(prompt: str) -> str:
    """
    Calls Gemini (via google-genai) & returns the text output.
    """
    logger.debug("Querying Gemini model...")

    try:
        model_config = get_model_config()
        client = __configure_model()

        response = client.models.generate_content(
            model=model_config.MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=model_config.TEMPERATURE,
                top_p=model_config.TOP_P,
                max_output_tokens=model_config.MAX_OUTPUT_TOKENS,
            ),
        )

        if not response or not response.text:
            logger.error("Empty response from Gemini")
            return ""

        logger.debug("Gemini response received successfully.")
        return response.text

    except Exception as e:
        logger.exception(f"Gemini API error: {e}")
        raise


def process_prompt(filters: ItenaryFilters) -> str:
    """
    Main pipeline: build prompt → query LLM.
    Returns the output string so Streamlit can show it.
    """
    logger.info("=== Itinerary Generation Started ===")

    try:
        final_prompt = __build_prompt(filters)
        output = __query_model(final_prompt)
        # Excel writing removed

        logger.info("=== Itinerary Generation Completed ===")
        return output

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise

# -------------------------------------------------------
# STREAMLIT ACTION BUTTON
# -------------------------------------------------------
if st.button("🚀 Generate Itinerary"):
    with st.spinner("Generating itinerary..."):
        try:
            result = process_prompt(filters)
            st.subheader("📄 Generated Itinerary Output")
            result = result.split("```text")[-1]
            st.write(result)
        except Exception as e:
            st.error(f"Error: {e}")

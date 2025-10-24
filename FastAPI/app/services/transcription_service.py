import openai
from app.core.config import settings
from tempfile import NamedTemporaryFile
import logging
from fastapi import UploadFile
import os

logger = logging.getLogger(__name__)
client = None

try:
    if settings.OPENAI_API_KEY:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAI AsyncClient initialized.")
    else:
        logger.warning("OpenAI API key not found. Transcription service will not work.")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)

async def transcribe_audio_openai(audio_file: UploadFile, language: str = 'en') -> str:
    if not client:
        logger.error("OpenAI client not available.")
        raise ValueError("OpenAI client is not configured or failed to initialize.")

    temp_file_path = None
    try:
        with NamedTemporaryFile(delete=False, suffix=f"_{audio_file.filename}") as temp_file:
            content = await audio_file.read()
            if not content:
                logger.warning("Received empty audio file.")
                return ""
            temp_file.write(content)
            temp_file_path = temp_file.name

        logger.info(f"Sending temporary audio file {temp_file_path} ({len(content)} bytes) to OpenAI Whisper API (Language: {language})...")
        with open(temp_file_path, "rb") as audio_data:
            transcript_object = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_data,
                response_format="text",
                language=language
            )
        logger.info("Transcription received from OpenAI.")
        transcription = str(transcript_object).strip()
        return transcription

    except openai.APIError as e:
        logger.error(f"OpenAI API returned an API Error: {e}", exc_info=True)
        raise ConnectionError(f"OpenAI API Error: {e}")
    except Exception as e:
        if isinstance(e, PermissionError):
             logger.error(f"Permission denied error accessing temporary file {temp_file_path}: {e}", exc_info=True)
             raise RuntimeError(f"Permission error accessing temporary file: {e}")
        logger.error(f"Error during audio transcription: {e}", exc_info=True)
        raise RuntimeError(f"Failed to transcribe audio: {e}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Successfully deleted temporary file: {temp_file_path}")
            except Exception as delete_error:
                logger.error(f"Failed to delete temporary file {temp_file_path}: {delete_error}", exc_info=True)
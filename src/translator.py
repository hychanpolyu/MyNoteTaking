import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

SUPPORTED_LANGUAGES = (
    'Chinese (traditional)',
    'Chinese (simplified)',
    'English',
    'Japanese',
    'Korean',
    'Spanish',
)


def translate_note(title: str, content: str, target_language: str) -> dict[str, str]:
    """Translate a note title and content through OpenRouter."""
    if target_language not in SUPPORTED_LANGUAGES:
        raise ValueError('Unsupported target language')

    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError('OPENROUTER_API_KEY is not configured')

    client = OpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=api_key,
    )
    response = client.chat.completions.create(
        model=os.getenv('OPENROUTER_MODEL', 'nvidia/nemotron-3-ultra-550b-a55b:free'),
        messages=[
            {
                'role': 'system',
                'content': (
                    'You are a professional translator. Translate the note title and content '
                    f'into {target_language}. Preserve the meaning, tone, formatting, and line breaks. '
                    'Return only a valid JSON object with exactly two string fields: '
                    '"title" and "content".'
                ),
            },
            {
                'role': 'user',
                'content': json.dumps({'title': title, 'content': content}, ensure_ascii=False),
            },
        ],
        temperature=0.3,
        response_format={'type': 'json_object'},
    )

    choices = getattr(response, 'choices', None)
    if not choices:
        provider_error = getattr(response, 'error', None)
        if provider_error:
            raise ValueError(f'Translation service error: {provider_error}')
        raise ValueError('The translation service returned no choices')

    message = getattr(getattr(choices[0], 'message', None), 'content', None)
    if not message:
        raise ValueError('The translation service returned an empty response')

    translated = json.loads(message)
    if not isinstance(translated, dict):
        raise ValueError('The translation service returned an invalid response')

    translated_title = translated.get('title')
    translated_content = translated.get('content')
    if not isinstance(translated_title, str) or not isinstance(translated_content, str):
        raise ValueError('The translation response did not contain title and content')

    return {'title': translated_title, 'content': translated_content}

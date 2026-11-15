import requests
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)

# ---------------------------------------------------------------------------

# Claude fix: gemini-2.5-flash-image has 0 free-tier quota. Enable billing on
# the API-key project (https://ai.dev/rate-limit) or use a model your tier
# can access. The generate_content() fallback below fails with the same 429
# quota error, so it can't rescue this either.

class MyClient(genai.Client):
    def __init__(self, api_key: str = '', availableModels: list = None, *args, **kwargs):
        if kwargs.get('base_url') is not None:

            # "Authorization: Bearer {api_key}" to query Parley
            super(MyClient,self).__init__(
                api_key=api_key,
                http_options=types.HttpOptions(
                    base_url = kwargs.get('base_url'),
                    api_version = kwargs.get('api_version', 'v1'),
                    headers = kwargs.get('header', {"Authorization": f"Bearer {api_key}"}), # to avoid storing the api_key
                    timeout=kwargs.get('timeout_ms', 60_000),
                    # Claude bug fix: fails fast in case of hanging due to 429 error
                    retry_options=types.HttpRetryOptions(attempts=3, http_status_codes=[408, 500, 502, 503, 504])
                ),
            )

            self.base_url = kwargs.get('base_url')
            self.api_version = kwargs.get('api_version', 'v1')
            self.has_ext_api = True
        else:
            self.has_ext_api = False
            super(MyClient,self).__init__(
                api_key=api_key,
                http_options=types.HttpOptions(
                    base_url='https://generativelanguage.googleapis.com/',
                    api_version=kwargs.get('api_version', 'v1beta'),
                    timeout=kwargs.get('timeout_ms', 60_000),
                    # Claude bug fix: fails fast in case of hanging due to 429 error
                    retry_options=types.HttpRetryOptions(attempts=3, http_status_codes=[408, 500, 502, 503, 504])
                )
            )
            self.api_version = kwargs.get('api_version', 'v1beta')

        self.availableModels = availableModels

    def ext_api_interaction(self, api_key: str, model: str, prompt='', *args, **kwargs):
        '''
        Interact with gemini directly routing through an external API

        Params:
            model = Gemini model to query
            prompt = prompt
            choice = response type of choice, default is 0 -> text

        Notes:
        - Only suports and index of 0 because of Parley plan

        Returns:
        Response from the Gemini model
        '''
        assert type(kwargs.get('choice', 0)) == int, f'choice is invalid type {type(kwargs.get('choice'))}, expected int'
        assert kwargs.get('choice', 0) == 0, f'Index {kwargs.get('choice')} is out of range, only supports index of 0'

        try:
            resp = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"Error: {e}")
            return

        # Return the response of the type of choice if specified (else just the first)
        return resp.json()["choices"][kwargs.get('choice', 0)]["message"]["content"]

    def gemini_interaction(self, model: str, prompt='', *args, **kwargs):
        '''
        Interact with gemini directly without and external API

        Params:
            model = Gemini model to query
            prompt = prompt
            full_resp = return the full interaction, default False
            choice = response type of choice (0-3), defaults is 0 -> text

        Notes:
        - will try out interactions.create() first and then tries models.generate_content()
        - responses listed in order: 0 = text, 1 = audio, 2 = image, 3 = video

        Returns:
        Response from the Gemini model
        '''

        assert type(kwargs.get('choice', 0)) == int, f'choice is invalid type {type(kwargs.get('choice'))}, expected int'
        assert kwargs.get('choice', 0) < 4, f'Index {kwargs.get('choice')} is out of range, expected 0-3'

        # try with interactions
        try:
            resp = self.interactions.create(
                model = model,
                input = prompt,
                automatic_continuation=False
            )

            if kwargs.get('full_resp', False):
                return resp

            # A list containing all the response options
            response_list = [resp.output_text,
                             resp.output_audio,
                             base64.b64decode(resp.output_image.data) if resp.output_image.data else None,
                             resp.output_video]

            return response_list[kwargs.get('choice', 0)]
        except Exception as e:
            if getattr(e,'code', None) == 429: raise f'Error code {e.code}: {e}' # Claude suggestion to deal with rate limit error
            print(f"Error: {e}\nTrying generate_content() method...")

        # upon failure try with generate_content()
        try:
            resp = self.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(response_modalities=['TEXT', 'IMAGE']),
            )

            if kwargs.get('choice', 0) != 0:
                for part in resp.candidates[0].content.parts:
                    if part.inline_data:
                        return part.inline_data.data   # raw bytes, NOT base64

            return resp.candidates[0].content.parts['text']
        except Exception as e:
            if getattr(e,'code', None) == 429: raise f'Error code {e.code}: {e}' # Claude suggestion to deal with too rate limit error
            print(f"Error: {e}")
            return

    def interact(self, model: str, prompt: str, api_key = None, *args, **kwargs):
        '''
        Create interactions with a Gemini model

        Params:
            model = Gemini model to query
            prompt = prompt
            api_key = api key of prompt (if external API), default None
            choice = response type of choice, defaults to 0

        Returns:
        Response from the Gemini model
        '''
        if self.availableModels is None:
            return 'No available models'

        if model in self.availableModels:
            if self.has_ext_api:
                if api_key is not None:
                    return self.ext_api_interaction(api_key, model, prompt, *args, **kwargs)
                else:
                    print('A query routed through an external API needs the api_key argument')
                    return
            else:
                return self.gemini_interaction(model, prompt, *args, **kwargs)
        else:
            return f'Choose a model from available models: {self.availableModels}'

    def add_base_url(self, api_key: str, base_url, availableModels: list = None, *args, **kwargs):
        '''
        Reinitialize MyClient object with a new base url

        Params:
        api_key = api_key given by the API
        base_url = url for the base
        availableModels = models accessible through API, current to original models
        '''
        if availableModels is not None:
            self.__init__(api_key, availableModels, base_url=base_url)
        else:
            self.__init__(api_key, self.availableModels, base_url=base_url)

    def remove_base_url(self, api_key: str, availableModels: list = None, *args, **kwargs):
        '''
        Reinitialize MyClient object with just Gemini api key

        Params:
        api_key = api_key given by the API
        availableModels = models accessible through API, curren to original models
        '''

        del self.base_url

        if availableModels is not None:
            self.__init__(api_key, availableModels, *args)
        else:
            self.__init__(api_key, self.availableModels, *args)

    def has_base_url(self):
        '''
        Use to check if the model has an external api, if so returns the base url
        '''
        if self.has_ext_api:
            return self.base_url
        else:
            print('No external api')
            return None

    def _availableModels(self):
        return self.availableModels


def create_client(api_key: str = '', availableModels: list = None, *args, **kwargs):
    return MyClient(api_key=api_key, availableModels=availableModels, *args, **kwargs)

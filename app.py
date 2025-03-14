''' app.py
Streamlit App for ISA, a powerful prompts generator'''

import os
import json
import random
import re
import time
from typing import List
import uuid
import pyperclip
import streamlit as st
import ollama
from PIL import Image
from pydantic import BaseModel, Field, ValidationError


from modules.prompts_system import prompt_system_chat, prompt_system_finetuned, prompt_system_create, prompt_system_flux, prompt_system_flux2, prompt_system_vision
from modules.subjects import subjects
from modules.version import version, isa_latest, ollama_version, ollama_latest, streamlit_version, strealit_latest, compare_version

BASEDIR = os.path.dirname(os.path.abspath(__file__))
PATH_OUTPUT = os.path.join(BASEDIR, "output")
PATH_POSTIVE = os.path.join(PATH_OUTPUT, "prompts_positive.txt")
PATH_NEGATIVE = os.path.join(PATH_OUTPUT, "prompts_negative.txt")
PATH_BACKUP = os.path.join(PATH_OUTPUT, "prompts_backup.txt")
PATH_SETTINGS = os.path.join(BASEDIR, "settings.json")

FAVICON = os.path.join(BASEDIR, "favicon.png")

# create class to strore prompts
class Prompt(BaseModel):
    positive: str = Field(..., description="Positive prompt to generate image from query")
    negative: str = Field(..., description="Negative prompt to generate image from query")

class PromptsList(BaseModel):
    prompts: List[Prompt] = Field(..., description="List of prompts")


class PromptFlux(BaseModel):
    positive: str = Field(..., description="Positive prompt to generate image from query")

class PromptsFluxList(BaseModel):
    prompts: List[PromptFlux] = Field(..., description="List of prompts")

@st.cache_data
def load_settings() -> dict:
    '''
    Load settings.'''

    try:
        with open(PATH_SETTINGS) as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {}

    models = get_models_list()
    if "model" not in settings or settings["model"] not in models:
        settings["model"] = None

    models_vision = get_vision_models_list()
    if "model_vision" not in settings or settings["model_vision"] not in models_vision:
        settings["model_vision"] = None
    
    if "prompt_mode" not in settings or settings["prompt_mode"] not in ["None", "SDXL", "Flux", "Flux2"]:
        settings["prompt_mode"] = "SDXL"
    
    if "mode" not in settings or not isinstance(settings["mode"], bool):
        settings["mode"] = False
    
    if "seed" not in settings:
        settings["seed"] = 0

    if "temperature" not in settings:
        settings["temperature"] = 0.8
    
    return settings

def save_settings() -> None:
    '''Save settings.'''
    settings = {
        "model": st.session_state["model"],
        "model_vision": st.session_state["model_vision"],
        "prompt_mode": st.session_state["prompt_mode"],
        "mode": st.session_state["mode"],
        "seed": st.session_state["seed"],
        "temperature": st.session_state["temperature"]
    }
    with open(PATH_SETTINGS, "w") as f:
        json.dump(settings, f, indent=4)
        st.toast("Settings saved", icon=":material/save:")

@st.cache_data
def get_version() -> tuple[str, str, str, str, str, str]:
    '''
    Returns the versions of ISA, ISA latest, Ollama, Ollama latest, Streamlit and Streamlit latest.

    Returns:
        str: a tuple of the versions of ISA, ISA latest, Ollama, Ollama latest, Streamlit and Streamlit latest.
    '''
    return version(), isa_latest(), ollama_version(), ollama_latest(), streamlit_version(), strealit_latest()

# cache the json schema for the prompts list
@st.cache_data
def get_prompt_schema() -> str:
    '''
    Returns the JSON schema for the prompts list.

    Returns:
        str: The JSON schema for the prompts list.
    '''
    return json.dumps(PromptsList.model_json_schema())

@st.cache_data
def get_prompt_flux_schema() -> str:
    '''
    Returns the JSON schema for the prompts flux list.

    Returns:
        str: The JSON schema for the prompts flux list.
    '''
    return json.dumps(PromptsFluxList.model_json_schema())

@st.cache_data
def get_models_list() -> List[str]:
    '''
    Returns a list of available LLM models.

    This function retrieves the list of available LLM models from the ollama.list()
    function and filters out those models that are not suitable for generating prompts.
    The models that are filtered out are:
        - Models that contain the word "embed" in their name (case-insensitive).
        - Models that start with "llava" or "moondream".

    Returns:
        List[str]: A list of available LLM models.
    '''
    # Pattern to search for in model names
    patern = "embed"
    
    # Get the list of available models and filter out the ones that are not suitable
    models = [model['model'] for model in ollama.list()['models'] 
        if not re.search(patern, model['model'], re.IGNORECASE) and
        (
            not model['model'].startswith('llava') and
            not model['model'].startswith('moondream') and 
            not model['model'].startswith('GFalcon-UA/nous-hermes-2-vision') and
            not model['model'].startswith('minicpm-v')
        )
    ]

    # Remove the ":latest" suffix from the model names
    for index, model in enumerate(models):
        if model.endswith(':latest'):
            models[index] = model[:-7]
    
    return models

@st.cache_data
def get_vision_models_list() -> List[str]:
    """
    Returns a list of available Vision models that are suitable for image reading.

    This function retrieves the list of available LLM models from the ollama.list()
    function and filters out those models that are not suitable for image vision.
    The models that are filtered out are:
        - Models that do not start with "llava" or "moondream".
        - Models that contain the word "embed" in their name (case-insensitive).

    Returns:
        List[str]: A list of available LLM models for image vision.
    """
    # List of models that are suitable for image vision
    # models_list = ['llava', 'llava-phi3', 'llava-llama3', 'moondream', 'GFalcon-UA/nous-hermes-2-vision', 'minicpm-v']
    models_list = ['test']

    # Get the list of available models and filter out the ones that are not suitable
    models = [model['model'] for model in ollama.list()['models'] 
              if (
                  model['model'].startswith('llava') or 
                  model['model'].startswith('moondream') or 
                  model['model'].startswith('GFalcon-UA/nous-hermes-2-vision') or
                  model['model'].startswith('minicpm-v') or
                  model['model'].startswith('granite3.2-vision') or
                  model['model'].startswith('llama3.2-vision') or 
                  model['model'].startswith('gemma3')
                ) and
              not re.search('embed', model['model'], re.IGNORECASE)]

    # Remove the ":latest" suffix from the model names
    for index, model in enumerate(models):
        if model.endswith(':latest'):
            models[index] = model[:-7]
    
    return models

def get_subjects_try() -> tuple[str, str, str]:
    """
    Get subjects list.

    This function returns the list of subjects used to generate prompts.

    Returns:
        List[str]: The list of subjects.
    """
    prompts = subjects.copy()
    random.shuffle(prompts)

    return prompts.pop(), prompts.pop(), prompts.pop()

def get_prompt_system(generate_prompt: bool = True, prompt_model: str = 'SDXL') -> str:
    """
    Get prompt system.

    This function returns the prompt system based on the value of the generate_prompt
    parameter.

    Args:
        generate_prompt (bool, optional): Whether to generate the prompt system. Defaults to True.

    Returns:
        str: The prompt system.
    """
    if generate_prompt:
        if prompt_model == 'SDXL':
            schema = get_prompt_schema()
            prompt_system = prompt_system_create.replace(r'{schema}', schema)
        elif prompt_model == 'Flux':
            schema = get_prompt_flux_schema()
            prompt_system = prompt_system_flux.replace(r'{schema}', schema)
        elif prompt_model == 'Flux2':
            schema = get_prompt_flux_schema()
            prompt_system = prompt_system_flux2.replace(r'{schema}', schema)
        elif prompt_model == 'None':
            prompt_system = prompt_system_finetuned
        return prompt_system
    else:
        return prompt_system_chat

def calculate_seed(seed: int) -> int:
    """
    Calculate seed."""
    if seed == 0:
        return random.randint(0, 2**32)

    return seed

def stream_data():
    """
    Stream data from ollama.

    This function streams data from the ollama chat API and yields each chunk of data
    as it is received. The function takes no parameters and returns a generator.

    Yields:
        str: The content of each chunk of data.
    """

    # Set the seed
    st.session_state['last_seed'] = calculate_seed(st.session_state['seed'])

    stream = ollama.chat(
        model=st.session_state.model,
        messages=st.session_state['messages'],
        stream=True,
        options={
            "seed": st.session_state['last_seed'],
            "temperature": st.session_state['temperature'],
            "num_ctx": 4096
        }
    )

    # Iterate over each chunk of data
    for chunk in stream:
        # Append the content of the chunk to the session state response
        st.session_state.response += chunk['message']['content']

        # Yield the content of the chunk
        yield chunk['message']['content']

def get_prompts() -> tuple[BaseModel,str]:
    """
    Get prompts from the ollama chat API.

    This function sends a chat request to the ollama chat API and retrieves the prompts
    generated by the model. The function takes no parameters and returns the prompts
    as a string in JSON format.

    Returns:
        str: The prompts generated by the model. the prompt mode used for the generation
    """
    messages = st.session_state['messages']
    attempt = 0

    st.session_state['last_seed'] = calculate_seed(st.session_state['seed'])

    while True:
        if st.session_state.prompt_mode == 'SDXL' or st.session_state.prompt_mode == 'Flux':
            format = 'json'
        else:
            format = ''
        response = ollama.chat(
            model=st.session_state.model,
            messages=messages,
            stream=False,
            format=format,
            options={
                "seed": st.session_state['last_seed'],
                "temperature": st.session_state['temperature'],
                "num_ctx": 4096
            }
        )

        # validate response
        try:
            if st.session_state.prompt_mode == 'SDXL':
                prompts = PromptsList.model_validate_json(response['message']['content'])
            elif st.session_state.prompt_mode == 'Flux' or st.session_state.prompt_mode == 'Flux2':
                prompts = PromptsFluxList.model_validate_json(response['message']['content'])
            elif st.session_state.prompt_mode == 'None':
                prompts = response['message']['content']
                prompts = {
                    "prompts":
                        [
                            {"positive": prompts}
                        ]
                }
            if (
                st.session_state.prompt_mode == 'SDXL' or \
                st.session_state.prompt_mode == 'Flux' or \
                st.session_state.prompt_mode == 'Flux2'
            ):
                st.session_state.response = prompts.model_dump_json()
            else:
                st.session_state.response = json.dumps(prompts)
            return prompts, st.session_state.prompt_mode
        except ValidationError as e:
            attempt += 1
            if attempt > 3:
                st.error("Error when parsing prompts. Aborded.")
                print()
                print("Error when parsing prompts.")
                print(e)
                print("Aborded.")
                print()
                return None, None
            st.error("Error when parsing prompts. Retry...")
            print()
            print("Error when parsing prompts.")
            print(e)
            print("Attempt", attempt, "Retrying...")
            print()
            messages = st.session_state['messages'] + [{'role': 'user', 'content': f"Please correct the JSON output; errors encountered:\n{e}"}]

def get_content(vision_model: str, image: str, prompt: str) -> str:
    """
    Get content from the ollama generate API.

    This function sends a request to the ollama generae API and retrieves the content
    generated by the model. The function takes the vision model, image, and prompt as
    parameters and returns the content as a string in JSON format.

    Args:
        vision_model (str): The name of the vision model to use.
        image (str): The path to the image to use.
        prompt (str): The prompt to use.

    Returns:
        str: The content generated by the model.
    """
    if image is not None and vision_model is not None:
            bytes_data = uploaded_file.getvalue()
            vision_response = ollama.generate(
                model=st.session_state.model_vision,
                prompt="""You are an art expert specializing in the appraisal of pictures and paintings. You will be able to extract relevant information from the image provided.
Analyse the image provided and extract a subject, a style (including medium, composition, lightning, artist influence) and a brief description.
If necessary, you can add adult content, nudity or explicit content.""",
                images=[bytes_data],
                system=prompt_system_vision,
                stream=False,
                keep_alive=0,
            )

            content = \
"""
{query}

Reply to user's query using the following context:

{context}"""

            content = content.format(
                context = vision_response['response'],
                query = st.session_state.prompt
            )
            if st.session_state.display_vision_response:
                with st.chat_message("assistant"):  
                    st.write("**Vision response**")
                    st.write(vision_response['response'])
    else:
        content = st.session_state.prompt

    return content

def copy_prompt(prompt: str) -> None:
    """
    Copy prompt.

    This function copies the prompt to the clipboard.

    Args:
        prompt (str): The prompt to copy.
    """
    pyperclip.copy(prompt)
    st.toast("Copied in clipboard", icon=":material/content_copy:")

@st.dialog("Edit prompt")
def edit_prompt(prompt: str, mode: str) -> None:
    """
    Edit prompt.

    This function edits the prompt in the session state.

    Args:
        prompt (str): The prompt to edit.
    """
    edit = st.text_area(label="Edit prompt", value=prompt, key="edit_input")
    clear = st.checkbox("Clear history", value=False, key="clear_history_checkbox")

    if st.button("Submit", type="primary"):
        if clear:
            clear_history()
        st.session_state.messages[0]['content'] = get_prompt_system(st.session_state.mode, mode)
        st.session_state.prompt = edit
        st.session_state.prompt_mode = mode

        st.rerun()

def validate_message(message: str) -> tuple[BaseModel, str]:
    """
    Validate message.

    This function validates the message.

    Args:
        message (str): The message to validate.

    Returns:
        Tuple[bool, str]: The validation result and the prompt mode.
    """
    try:
        prompt = PromptsList.model_validate_json(message)
        return prompt, "SDXL"
    except ValidationError as e:
        try:
            prompt = PromptsFluxList.model_validate_json(message)
            return prompt, "Flux"
        except ValidationError as e:
            st.error("Error when parsing prompts. Aborded.")
    
def display_prompts(prompts_list: PromptsList, output_error: bool = False, prompt_mode: str = "SDXL") -> bool:
    """
    Display prompts.

    This function takes a PromptsList object and displays them in a formatted manner.

    Args:
        prompts_list (PromptsList): The prompts_list object to display.
        output_error (bool, optional): Whether to output an error message if no prompts are found. Defaults to False.

    Returns:
        bool: True if prompts are found and displayed, False otherwise.
    """
    
    try:        
        if prompt_mode == "SDXL" or prompt_mode == "Flux" or prompt_mode == "Flux2":
            list_prompts = prompts_list.prompts
        else:
            list_prompts = prompts_list["prompts"]
        for index, prompt in enumerate(list_prompts):
            if prompt_mode == "SDXL" or prompt_mode == "Flux" or prompt_mode == "Flux2":
                prompt_ = prompt.positive
            else:
                prompt_ = prompt["positive"]
            col_1, col_2 = st.columns((10, 1))
            with col_1:
                st.write(f":green[Positive {index + 1}]", unsafe_allow_html=True)
            with col_2:
                st.button(
                    ":material/content_copy:", 
                    on_click=copy_prompt, 
                    args=[prompt_], 
                    key=f"copy_{uuid.uuid4()}", 
                    use_container_width=True,
                    help="Copy positive prompt"
                )                
            st.write(f"{prompt_}", unsafe_allow_html=True)
            
            if prompt_mode == "SDXL":
                col_1, col_2 = st.columns((10, 1))
                with col_1:
                    st.write(f":red[Negative {index + 1}]", unsafe_allow_html=True)
                with col_2:
                    st.button(
                        ":material/content_copy:", 
                        on_click=copy_prompt, 
                        args=[prompt.negative], 
                        key=f"copy_{uuid.uuid4()}", 
                        use_container_width=True, 
                        help="Copy negative prompt"
                    )                
                st.write(f"{prompt.negative}", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin-top: 0px; margin-bottom: 0px;'>", unsafe_allow_html=True)
        # Return True if prompts are found and displayed
        return True
    
    except json.decoder.JSONDecodeError as e:
        print("JSONDecodeError when parsing prompts.")
        print(e)
        # If JSON decoding fails, output an error message if output_error is True
        if output_error:
            st.write("No prompt found. Aborded.")
        return False
    
    except ValueError as e:
        print("ValueError when parsing prompts.")
        print(e)
        # Output an error message if output_error is True
        if output_error:
            st.write("No prompt found. Aborded.")
        return False
    
    except Exception as e:
        print("Error when parsing prompts.")
        print(e)
        # Output an error message if output_error is True
        if output_error:
            st.write("No prompt found. Aborded.")
        return False

def reload_prompt(request: str) -> None:
    """
    Reload prompt.

    This function reloads the prompt in the session state.

    Args:
        request (str): The request to reload.
    """
    st.session_state.prompt = request

def display_request(request: str) -> None:
    """
    Display request.

    This function displays the request in the session state.

    Args:
        request (str): The request to display.
    """
    with st.chat_message("user"):
        col_1, col_2, col_3 = st.columns((9, 1, 1), vertical_alignment="top")
        with col_1:
                st.write(request)
        with col_2:
            st.button(
                ":material/restart_alt:", 
                on_click=reload_prompt, 
                args=[request], 
                key=f"edit_{uuid.uuid4()}", 
                use_container_width=True,
                help="Reload prompt"
            )
        with col_3:
            st.button(
                ":material/edit:", 
                on_click=edit_prompt, 
                args=[request, st.session_state.prompt_mode], 
                key=f"edit_{uuid.uuid4()}", 
                use_container_width=True,
                help="Edit prompt"
            )

def save_response(response: str) -> None:
    '''
    Save response.

    Args:
        response (str): The response to be saved.
    '''
    # Load response from the JSON string
    content, mode = validate_message(response)
    content = content.model_dump()

    # create folder output if not exists
    if not os.path.exists(PATH_OUTPUT):
        os.makedirs(PATH_OUTPUT)
    
    # Write positive prompts to the file
    with open(PATH_POSTIVE, 'w') as f:
        for prompt in content['prompts']:
            f.write(prompt['positive'] + '\n')
    
    with open(PATH_NEGATIVE, 'w') as f:
        for prompt in content['prompts']:
            if 'negative' in prompt:
                f.write(prompt['negative'] + '\n')
            else:
                f.write("")

    # Append prompts to the backup file
    with open(PATH_BACKUP, 'a') as f:
        for prompt in content['prompts']:
            f.write(prompt['positive'] + '\n')
            if 'negative' in prompt:
                f.write(prompt['negative'] + '\n')
            # if mode == "SDXL":
            #     f.write(prompt['negative'] + '\n')
            f.write('-'*20 + '\n')
    
    st.toast("Saved!", icon=":material/save:")
        
def preload_prompt(prompt: str) -> None:
    """
    Load a prompt into the session state.

    Args:
        prompt (str): The prompt to be loaded.

    Returns:
        None
    """
    # Store the prompt in the session state
    st.session_state.prompt = prompt

def last_seed() -> None:
    '''Last seed'''
    if st.session_state['last_seed']:
        st.session_state['seed'] = st.session_state['last_seed']

def clear_history() -> None:
    '''Clear history'''
    st.session_state['messages'] = [
        {
            "role": "system", 
            "content": prompt_system_chat
        }
    ]
    st.toast("History cleared", icon=":material/delete_history:") 

def clear_memory() -> None:
    '''Clear memory'''
    ollama.generate(
        st.session_state.model, 
        keep_alive=0,
        options={
            "seed": st.session_state['last_seed'],
            "temperature": st.session_state['temperature'],
            "num_ctx": 4096
        }
    )
    st.toast("Memory cleared", icon=":material/memory:") 

##############
# PAGE SETUP #
##############
img_logo = Image.open(FAVICON)
st.set_page_config(
    page_title="ISA",
    # page_icon=":large_blue_circle:",
    page_icon=img_logo,
    layout="centered"
)


#########
# STYLE #
#########
css = """
<style>
    button[title="View fullscreen"] {
        top: 0.5rem !important;
        right: 0.5rem !important;
    }  

    div[data-testid=stSidebarUserContent] {
        padding-top: 0px;
    }
    div[data-testid=stSidebarUserContent] h1{
        padding-top: 0px;
    }
    div[data-testid=stSidebarUserContent] hr{
        margin-top: .5rem;
        margin-bottom: 1rem;
    }
</style>
"""
st.html(css)


settings = load_settings()

################
# INIT SESSION #
################
if 'prompt' not in st.session_state:
    st.session_state['prompt'] = None
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {
            "role": "system", 
            "content": prompt_system_chat
        }
    ]
if 'response' not in st.session_state:
    st.session_state['response'] = ""
if 'display_vision_response' not in st.session_state:
    st.session_state['display_vision_response'] = False
if "seed" not in st.session_state:
    st.session_state["seed"] = settings["seed"]
if "temperature" not in st.session_state:
    st.session_state["temperature"] = settings["temperature"]
if "last_seed" not in st.session_state:
    st.session_state["last_seed"] = None
if "model" not in st.session_state:
    st.session_state["model"] = settings["model"]
if "model_vision" not in st.session_state: # model_vision
    st.session_state["model_vision"] = settings["model_vision"]
if "prompt_mode" not in st.session_state:
    st.session_state["prompt_mode"] = settings["prompt_mode"]
if "mode" not in st.session_state:
    st.session_state["mode"] = settings["mode"]

#################
# SIDE BAR MENU #
#################
with st.sidebar:
    st.markdown("<h1 style='padding-bottom: 0px; letter-spacing: 9px;'>I S A<br><small style='font-size: 14px; letter-spacing: 6px;'>PROMPT  GENERATOR</small></h1>", unsafe_allow_html=True)
    st.markdown('---')
    
    col_1, col_2 = st.columns(2)

    models = get_models_list()
    with col_1:
        st.selectbox(
            "LLM", 
            models, 
            placeholder="Select a model",
            key="model"
        )
        st.toggle("Create prompt", key="mode")
    
    vision_models = get_vision_models_list()
    with col_2:
        st.selectbox(
            "Vision", 
            vision_models, 
            placeholder="Select a model",
            key="model_vision"
        )
        st.selectbox(
            "Mode", 
            ["None", "SDXL", "Flux", "Flux2"], 
            placeholder="Select a mode",
            key="prompt_mode",
            label_visibility="collapsed",
            disabled=not st.session_state.mode
        )    

    st.markdown('---')

    st.slider("Temperature", min_value=0.0, max_value=1.0, step=0.1, key="temperature")
    col_1, col_2 = st.columns([2, 1], vertical_alignment="bottom")
    with col_1:
        st.number_input("Seed", min_value=0, max_value=2**32, step=1, key="seed")
    with col_2:
        st.button("Last seed", on_click=last_seed, key="randomize", use_container_width=True)

    st.markdown('---')

    st.button("Save settings", on_click=save_settings, key="save_settings", use_container_width=True)  
    col_1, col_2 = st.columns(2)
    col_1.button("Clear history", on_click=clear_history, key="clear_history", use_container_width=True)  
    col_2.button("Clear memory", on_click=clear_memory, key="clear_memory", use_container_width=True)  
    


    uploaded_file = st.file_uploader(
        "Select image", 
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
        key="image",
        label_visibility="collapsed"
    )

    st.toggle("Display vision response", value=False, key="display_vision_response")

    if uploaded_file is not None:
        st.image(uploaded_file)

    st.markdown('---')

    i_version, i_latest, o_version, o_latest, st_version, st_latest = get_version()

    if i_latest == 'unknown':
        color_i = 'red'
        str_isa_latest = 'Latest version of ISA not available'
    else:            
        compare_i = compare_version(i_version, i_latest)
        color_i = 'green' if compare_i >= 0 else 'red'
        str_isa_latest = "ISA is up to date" if compare_i >= 0 else f"A new version of ISA is available: {i_latest}"

    if o_latest == 'unknown':
        color_o = 'red'
        str_o_latest = 'Latest version of Ollama not available'
    else:
        compare_o = compare_version(o_version, o_latest)
        color_o = 'green' if compare_o >= 0 else 'red'
        str_o_latest = "Ollama is up to date" if compare_o >= 0 else f"A new version of Ollama is available: {o_latest}"

    if st_latest == 'unknown':
        color_st = 'red'
        str_st_latest = 'Latest version of Streamlit not available'
    else:
        compare_st = compare_version(st_version, st_latest)
        color_st = 'green' if compare_st >= 0 else 'red'
        str_st_latest = "Streamlit is up to date" if compare_st >= 0 else f"A new version of Streamlit is available: {st_latest}"

    col_1, col_2 = st.columns((1, 2))
    col_1.markdown(f"<p style='font-size: 12px;'>Version <a href='https://github.com/Franck-Demongin/ISA' target='_blank'>{i_version}</a></p>", unsafe_allow_html=True)
    col_2.markdown(f"<p style='text-align: right; font-size: 12px;'>Powered by<br><a href='https://ollama.com/' target='_blank'>Ollama {o_version}</a> & <a href='https://streamlit.io/' target='_blank'>Streamlit {st_version}</a></p>", unsafe_allow_html=True)

    st.markdown(f"""<p style='text-align: right; font-size: 12px; color: {color_i};'>{str_isa_latest}<br>
    <span style='color: {color_st};'>{str_st_latest}</span><br>
    <span style='color: {color_o};'>{str_o_latest}</span></p>""", unsafe_allow_html=True)
    

################
# PAGE CONTENT #
################
st.session_state.messages[0]['content'] = get_prompt_system(st.session_state.mode, st.session_state.prompt_mode)

if st.session_state.model is None:
    st.markdown('<h1 style="font-size: 36px; padding-bottom: 0px; letter-spacing: 15px; font-weight: 600; line-height: 0.75em;">I S A<br><small style="font-size: 14px; letter-spacing: 6px;">PROMPT  GENERATOR</small></h1>', unsafe_allow_html=True)
    st.markdown('---')
    st.write("To start use ISA, select a model in the sidebar.")

    st.stop()

prompt = st.chat_input("Input your prompt", key="prompt_input")

if prompt is not None:
    st.session_state.prompt = prompt

if len(st.session_state.messages) < 2 and st.session_state.prompt is None:

    st.markdown('<h1 style="font-size: 36px; padding-bottom: 0px; letter-spacing: 15px; font-weight: 600; line-height: 0.75em;">I S A<br><small style="font-size: 14px; letter-spacing: 6px;">PROMPT  GENERATOR</small></h1>', unsafe_allow_html=True)
    st.markdown('---')

    prompt_1, prompt_2, prompt_3 = get_subjects_try()
    with st.container(border=False):
        col_1, col_2, col_3 = st.columns(3)
        with col_1:
            with st.container(border=True): 
                st.write(prompt_1)
                st.button("Try it!", on_click=preload_prompt, args=[prompt_1], key="try_it_1")
        with col_2:
            with st.container(border=True): 
                st.write(prompt_2)
                st.button("Try it!", on_click=preload_prompt, args=[prompt_2], key="try_it_2")
        with col_3:
            with st.container(border=True): 
                st.write(prompt_3)
                st.button("Try it!", on_click=preload_prompt, args=[prompt_3], key="try_it_3")
        _, _, _, _, col_button = st.columns(5)
        with col_button:
            st.button('Random', on_click=clear_history, key="next_subject", use_container_width=True, type='primary')
else:
    for index, message in enumerate(st.session_state.messages):
        if message['role'] == 'user':
            display_request(message['content'])
        elif message['role'] == 'assistant' and \
            message['content'].strip().startswith("{") and \
            message['content'].strip().endswith("}"):
                with st.chat_message("assistant"):    
                    prompt_validated, mode = validate_message(message['content'])     
                    if display_prompts(prompt_validated, output_error=True, prompt_mode=mode): 
                        st.button("Save", on_click=save_response, args=[message['content']], key=f"save_response_{index}")
            
        elif message['role'] == 'assistant':
            st.chat_message(message['role']).write(message['content'])

    if st.session_state.prompt:
        display_request(st.session_state.prompt)
                        
        content = get_content(vision_model=st.session_state.model_vision, image=uploaded_file, prompt=st.session_state.prompt)

        st.session_state['messages'].append({'role': 'user', 'content': content})

        st.session_state.response = ""  
        if st.session_state.mode:
            with st.chat_message("assistant"):
                with st.spinner("Generating..."):
                    prompts_list, mode = get_prompts()
                    if display_prompts(prompts_list, output_error=True, prompt_mode=mode):
                        col_1, col_2 = st.columns(2)

                        with col_1:
                            st.button("Save", on_click=save_response, args=[st.session_state.response], key="save_response")
                        with col_2:
                            st.markdown(f"<p style='text-align: right; font-size: 14px; color: #CCCCCC'>Seed: {st.session_state['last_seed']} - Temperature: {st.session_state['temperature']}</p>", unsafe_allow_html=True)
            
        else:
            with st.chat_message("assistant"):
                st.write_stream(stream_data)
        
        st.session_state['messages'][-1]['content'] = st.session_state.prompt
        st.session_state['messages'].append({'role': 'assistant', 'content': st.session_state.response})
        st.session_state.prompt = None

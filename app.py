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


from modules.prompts_system import prompt_system_chat, prompt_system_create, prompt_system_flux, prompt_system_vision
from modules.subjects import subjects
from modules.version import version, isa_latest, ollama_version, ollama_latest, streamlit_version, strealit_latest

# print basedir
BASEDIR = os.path.dirname(os.path.abspath(__file__))
PATH_OUTPUT = os.path.join(BASEDIR, "output")
PATH_POSTIVE = os.path.join(PATH_OUTPUT, "prompts_positive.txt")
PATH_NEGATIVE = os.path.join(PATH_OUTPUT, "prompts_negative.txt")
PATH_BACKUP = os.path.join(PATH_OUTPUT, "prompts_backup.txt")

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
    models = [model['name'] for model in ollama.list()['models'] 
              if not re.search(patern, model['name'], re.IGNORECASE) and
              (
                  not model['name'].startswith('llava') and
                  not model['name'].startswith('moondream') and 
                  not model['name'].startswith('GFalcon-UA/nous-hermes-2-vision')
                )]
                
            # (model['name'].startswith('llava') or model['name'].startswith('moondream'))]

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
    models_list = ['llava', 'llava-phi3', 'llava-llama3', 'moondream', 'GFalcon-UA/nous-hermes-2-vision']

    # Get the list of available models and filter out the ones that are not suitable
    models = [model['name'] for model in ollama.list()['models'] 
              if (
                  model['name'].startswith('llava') or 
                  model['name'].startswith('moondream') or 
                  model['name'].startswith('GFalcon-UA/nous-hermes-2-vision')
                ) and
              not re.search('embed', model['name'], re.IGNORECASE)]

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
        return prompt_system
    else:
        return prompt_system_chat

def stream_data():
    """
    Stream data from ollama.

    This function streams data from the ollama chat API and yields each chunk of data
    as it is received. The function takes no parameters and returns a generator.

    Yields:
        str: The content of each chunk of data.
    """
    stream = ollama.chat(
        model=model,
        messages=st.session_state['messages'],
        stream=True
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
    while True:
        response = ollama.chat(
            model=model,
            messages=messages,
            stream=False,
            format="json"
        )

        # validate response
        try:
            if st.session_state.prompt_mode == 'SDXL':
                prompts = PromptsList.model_validate_json(response['message']['content'])
            elif st.session_state.prompt_mode == 'Flux':
                prompts = PromptsFluxList.model_validate_json(response['message']['content'])
            st.session_state.response = prompts.model_dump_json()
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
                model=vision_model,
                prompt="Describe the image",
                images=[bytes_data],
                system=prompt_system_vision,
                stream=False,
                keep_alive=0,
            )

            content = \
"""Reply to user's query using the following context:
{context}

User's query:
{query}"""

            content = content.format(
                context = vision_response['response'],
                query = st.session_state.prompt
            )
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

@st.dialog("Edit prompt")
def edit_prompt(prompt: str, mode: str) -> None:
    """
    Edit prompt.

    This function edits the prompt in the session state.

    Args:
        prompt (str): The prompt to edit.
    """
    edit = st.text_area(label="Edit prompt", value=prompt, key="edit_input")
    if st.button("Submit", type="primary"):
        st.session_state.messages[0]['content'] = get_prompt_system(generate_prompt, mode)
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
        for index, prompt in enumerate(prompts_list.prompts):
            col_1, col_2 = st.columns((10, 1))
            with col_1:
                st.write(f":green[Positive {index + 1}]", unsafe_allow_html=True)
            with col_2:
                st.button(
                    ":material/content_copy:", 
                    on_click=copy_prompt, 
                    args=[prompt.positive], 
                    key=f"copy_{uuid.uuid4()}", 
                    use_container_width=True,
                    help="Copy positive prompt"
                )                
            st.write(f"{prompt.positive}", unsafe_allow_html=True)
            
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
            st.write("No prompts found. Aborded.")
        return False
    
    except ValueError as e:
        print("ValueError when parsing prompts.")
        print(e)
        # Output an error message if output_error is True
        if output_error:
            st.write("No prompts found. Aborded.")
        return False
    
    except Exception as e:
        print("Error when parsing prompts.")
        print(e)
        # Output an error message if output_error is True
        if output_error:
            st.write("No prompts found. Aborded.")
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

def save_response(response: str, placeholder=st.empty) -> None:
    '''
    Save response.

    Args:
        response (str): The response to be saved.
        placeholder (streamlit.empty): The placeholder where success message will be displayed.
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
    
    # Write negative prompts to the file
    if mode == "SDXL":
        with open(PATH_NEGATIVE, 'w') as f:
            for prompt in content['prompts']:
                f.write(prompt['negative'] + '\n')
    
    # Append prompts to the backup file
    with open(PATH_BACKUP, 'a') as f:
        for prompt in content['prompts']:
            f.write(prompt['positive'] + '\n')
            if mode == "SDXL":
                f.write(prompt['negative'] + '\n')
            f.write('-'*20 + '\n')
    
    # Display success message
    with placeholder.container():
        st.success("Saved!")
    
    # Wait for 1.5 seconds before emptying the placeholder
    time.sleep(1.5)
    placeholder.empty()
        
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

def clear_history() -> None:
    '''Clear history'''
    st.session_state['messages'] = [
        {
            "role": "system", 
            "content": prompt_system_chat
        }
    ]

def clear_memory() -> None:
    '''Clear memory'''
    ollama.generate(model, keep_alive=0)

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

#################
# SIDE BAR MENU #
#################
with st.sidebar:
    st.markdown("<h1 style='padding-bottom: 0px; letter-spacing: 9px;'>I S A<br><small style='font-size: 14px; letter-spacing: 6px;'>PROMPT  GENERATOR</small></h1>", unsafe_allow_html=True)
    st.markdown('---')
    
    col_1, col_2 = st.columns(2)

    models = get_models_list()
    with col_1:
        model = st.selectbox(
            "LLM", 
            models, 
            placeholder="Select a model",
            key="model"
        )
        generate_prompt = st.toggle("Create prompt", value=True, key="generate_prompt")
    
    vision_models = get_vision_models_list()
    with col_2:
        vision_model = st.selectbox(
            "Vision", 
            vision_models, 
            placeholder="Select a model",
            key="vision_model"
        )
        st.selectbox(
            "Mode", 
            ["SDXL", "Flux"], 
            placeholder="Select a mode",
            key="prompt_mode",
            label_visibility="collapsed",
            disabled=not generate_prompt
        )
    
    col_1, col_2 = st.columns(2)
    col_1.button("Clear history", on_click=clear_history, key="clear_history", use_container_width=True)  
    col_2.button("Clear memory", on_click=clear_memory, key="clear_memory", use_container_width=True)  

    st.markdown('---')

    placeholder = st.empty()


    uploaded_file = st.file_uploader(
        "Select image", 
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
        key="image",
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        st.image(uploaded_file)

    st.markdown('---')

    i_version, i_latest, o_version, o_latest, st_version, st_latest = get_version()

    color_i = 'green' if i_version >= i_latest else 'red'
    color_o = 'green' if o_version >= o_latest else 'red'
    color_st = 'green' if st_version >= st_latest else 'red'

    str_isa_latest = "ISA is up to date" if i_version >= i_latest else f"A new version of ISA is available: {i_latest}"
    str_o_latest = "Ollama is up to date" if o_version >= o_latest else f"A new version of Ollama is available: {o_latest}"
    str_st_latest = "Streamlit is up to date" if st_version >= st_latest else f"A new version of Streamlit is available: {st_latest}"
    
    col_1, col_2 = st.columns((1, 2))
    col_1.markdown(f"<p style='font-size: 12px;'>Version <a href='https://github.com/Franck-Demongin/ISA' target='_blank'>{i_version}</a></p>", unsafe_allow_html=True)
    col_2.markdown(f"<p style='text-align: right; font-size: 12px;'>Powered by<br><a href='https://ollama.com/' target='_blank'>Ollama {o_version}</a> & <a href='https://streamlit.io/' target='_blank'>Streamlit {st_version}</a></p>", unsafe_allow_html=True)

    st.markdown(f"""<p style='text-align: right; font-size: 12px; color: {color_i};'>{str_isa_latest}<br>
    <span style='color: {color_st};'>{str_st_latest}</span><br>
    <span style='color: {color_o};'>{str_o_latest}</span></p>""", unsafe_allow_html=True)
    

################
# PAGE CONTENT #
################
st.session_state.messages[0]['content'] = get_prompt_system(generate_prompt, st.session_state.prompt_mode)

if model is None:
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
                        st.button("Save", on_click=save_response, args=[message['content'], placeholder], key=f"save_response_{index}")
            
        elif message['role'] == 'assistant':
            st.chat_message(message['role']).write(message['content'])

    if st.session_state.prompt:
        display_request(st.session_state.prompt)
                        
        content = get_content(vision_model=vision_model, image=uploaded_file, prompt=st.session_state.prompt)

        st.session_state['messages'].append({'role': 'user', 'content': content})

        st.session_state.response = ""  
        if generate_prompt:
            with st.chat_message("assistant"):
                with st.spinner("Generating..."):
                    prompts_list, mode = get_prompts()
                    if display_prompts(prompts_list, output_error=True, prompt_mode=mode):
                        st.button("Save", on_click=save_response, args=[st.session_state.response, placeholder], key="save_response")
            
        else:
            with st.chat_message("assistant"):
                st.write_stream(stream_data)
        
        st.session_state['messages'][-1]['content'] = st.session_state.prompt
        st.session_state['messages'].append({'role': 'assistant', 'content': st.session_state.response})
        st.session_state.prompt = None
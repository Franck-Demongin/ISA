''' app.py
Streamlit App for ISA, a powerful prompts generator'''

import os
import json
import random
import re
import time
from typing import List
import streamlit as st
import ollama
from pydantic import BaseModel, Field, ValidationError

from modules.prompts_system import prompt_system_chat, prompt_system_create, prompt_system_vision
from modules.subjects import subjects

VERSION = "0.2.1"

PATH_OUTPUT = "output"
PATH_POSTIVE = os.path.join(PATH_OUTPUT, "prompts_positive.txt")
PATH_NEGATIVE = os.path.join(PATH_OUTPUT, "prompts_negative.txt")
PATH_BACKUP = os.path.join(PATH_OUTPUT, "prompts_backup.txt")

# create class to strore prompts
class Prompt(BaseModel):
    positive: str = Field(..., description="Positive prompt to generate image from query")
    negative: str = Field(..., description="Negative prompt to generate image from query")

class PromptsList(BaseModel):
    prompts: List[Prompt] = Field(..., description="List of prompts")

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
              not (model['name'].startswith('llava') or model['name'].startswith('moondream'))]

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
    models_list = ['llava', 'llava-phi3', 'llava-llama3', 'moondream']

    # Get the list of available models and filter out the ones that are not suitable
    models = [model['name'] for model in ollama.list()['models'] 
              if (model['name'].startswith('llava') or model['name'].startswith('moondream')) and
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

def get_prompt_system(generate_prompt: bool = True) -> str:
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
        schema = get_prompt_schema()
        prompt_schema = """
```
""" + schema + """
```"""
        prompt_system = prompt_system_create + prompt_schema
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

def get_prompts() -> str:
    """
    Get prompts from the ollama chat API.

    This function sends a chat request to the ollama chat API and retrieves the prompts
    generated by the model. The function takes no parameters and returns the prompts
    as a string in JSON format.

    Returns:
        str: The prompts generated by the model.
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
            prompts = PromptsList.model_validate_json(response['message']['content'])
            st.session_state.response = prompts.model_dump_json()
            return prompts
        except ValidationError as e:
            attempt += 1
            if attempt > 3:
                st.error("Error when parsing prompts. Aborded.")
                print()
                print("Error when parsing prompts.")
                print(e)
                print("Aborded.")
                print()
                return None
            st.error("Error when parsing prompts. Retry...")
            print()
            print("Error when parsing prompts.")
            print(e)
            print("Attempt", attempt, "Retrying...")
            print()
            messages = st.session_state['messages'] + [{'role': 'user', 'content': f"Please correct the JSON output; errors encountered:\n{e}"}]


    # Return the content of the response
    # return response['message']['content']

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

def display_prompts(prompts_list: PromptsList, output_error: bool = False) -> bool:
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
            col_1, col_2, col_3, col_4 = st.columns((4, 1, 1, 1))

            with col_1:
                st.write(f":green[Positive {index + 1}]", unsafe_allow_html=True)    
            with col_2:
                st.button("Edit", key=f"edit_{index}", use_container_width=True)
            with col_3:
                st.button("Copy", key=f"copy_{index}", use_container_width=True)                
            with col_4:
                st.button("Remove", key=f"delete_{index}", use_container_width=True)                

            st.write(f"{prompt.positive}", unsafe_allow_html=True)
            st.write(f":red[Negative {index + 1}]<br>{prompt.negative}", unsafe_allow_html=True)
            st.markdown("<hr style='margin-top: 0px; margin-bottom: 0px;'>", unsafe_allow_html=True)
        # Return True if prompts are found and displayed
        return True
    
    except json.decoder.JSONDecodeError:
        # If JSON decoding fails, output an error message if output_error is True
        if output_error:
            st.write("No prompts found. Aborded.")
        return False
    
    except ValueError:
        # Output an error message if output_error is True
        if output_error:
            st.write("No prompts found. Aborded.")
        return False
    
    except Exception as e:
        # Output an error message if output_error is True
        if output_error:
            st.write("No prompts found. Aborded.")
        return False

def save_response(response: str, placeholder: st.empty) -> None:
    '''
    Save response.

    Args:
        response (str): The response to be saved.
        placeholder (streamlit.empty): The placeholder where success message will be displayed.
    '''
    # Load response from the JSON string
    content = json.loads(response)

    # create folder output if not exists
    if not os.path.exists(PATH_OUTPUT):
        os.makedirs(PATH_OUTPUT)
    
    # Write positive prompts to the file
    with open(PATH_POSTIVE, 'w') as f:
        for prompt in content['prompts']:
            f.write(prompt['positive'] + '\n')
    
    # Write negative prompts to the file
    with open(PATH_NEGATIVE, 'w') as f:
        for prompt in content['prompts']:
            f.write(prompt['negative'] + '\n')
    
    # Append positive and negative prompts to the backup file
    with open(PATH_BACKUP, 'a') as f:
        for prompt in content['prompts']:
            f.write(prompt['positive'] + '\n')
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
st.set_page_config(
    page_title="ISA",
    page_icon=":large_blue_circle:",
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
    
    vision_models = get_vision_models_list()
    with col_2:
        vision_model = st.selectbox(
            "Vision", 
            vision_models, 
            placeholder="Select a model",
            key="vision_model"
        )

    generate_prompt = st.toggle("Generate prompt", value=True, key="generate_prompt")
    
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
    col_1, col_2 = st.columns(2)
    col_1.markdown(f"<p style='font-size: 12px;'>Version {VERSION}</p>", unsafe_allow_html=True)
    col_2.markdown(f"<p style='text-align: right; font-size: 12px;'>Powered by <a href='https://ollama.com/' target='_blank'>Ollama</a> & <a href='https://streamlit.io/' target='_blank'>Streamlit</a></p>", unsafe_allow_html=True)

################
# PAGE CONTENT #
################
if model is None:
    st.markdown('<h1 style="font-size: 36px; padding-bottom: 0px; letter-spacing: 15px; font-weight: 600; line-height: 0.75em;">I S A<br><small style="font-size: 14px; letter-spacing: 6px;">PROMPT  GENERATOR</small></h1>', unsafe_allow_html=True)
    st.markdown('---')
    st.write("To start use ISA, select a model in the sidebar.")

    st.stop()

prompt = st.chat_input("Say something")

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
        if message['role'] == 'system':
            message['content'] = get_prompt_system(generate_prompt)
        else:
            if message['role'] == 'assistant' and \
                message['content'].strip().startswith("{") and \
                message['content'].strip().endswith("}"):
                    with st.chat_message("assistant"):
                        if display_prompts(PromptsList.model_validate_json(message['content']), output_error=True): 
                            st.button("Save", on_click=save_response, args=[message['content'], placeholder], key=f"save_response_{index}")
                
            else:
                st.chat_message(message['role']).write(message['content'])

    if st.session_state.prompt:
        with st.chat_message("user"):
            st.write(st.session_state.prompt)
                
        content = get_content(vision_model=vision_model, image=uploaded_file, prompt=st.session_state.prompt)

        st.session_state['messages'].append({'role': 'user', 'content': content})

        st.session_state.response = ""  
        if generate_prompt:
            with st.chat_message("assistant"):
                with st.spinner("Generating..."):
                    prompts_list = get_prompts()
                    print(prompts_list)
                    if display_prompts(prompts_list, output_error=True):
                        st.button("Save", on_click=save_response, args=[st.session_state.response, placeholder], key="save_response")
            
        else:
            with st.chat_message("assistant"):
                st.write_stream(stream_data)
                if display_prompts(st.session_state.response):
                    st.button("Save", on_click=save_response, args=[st.session_state.response, placeholder], key="save_response")
        
        st.session_state['messages'][-1]['content'] = st.session_state.prompt
        st.session_state['messages'].append({'role': 'assistant', 'content': st.session_state.response})
        st.session_state.prompt = None
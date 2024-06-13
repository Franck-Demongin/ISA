![ISA_Hero](https://github.com/Franck-Demongin/ISA/assets/54265936/0836dded-3272-4ddf-abff-3e1b13dda044)

# ISA
ISA creates prompts to generate images with SDXL Stable Diffusion models.
It work locally with Ollama LLM model like llam3 or Mistral. 

<img src="https://img.shields.io/badge/Python-3.10-blue" /> <img src="https://img.shields.io/badge/Ollama-orange" /> <img src="https://img.shields.io/badge/Streamlit-blue" /> [![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://perso.crans.org/besson/LICENSE.html)

## Installation

First of all, you need Ollama to use ISA.  
Go to [ollama.com](https://ollama.com/) and follow the instructions to install it on your system. Ollama is available for Windows, Mac and Linux.

If GIT is installed, open a terminal where you want install ISA and type: 
```:bash
git clone https://github.com/Franck-Demongin/ISA.git
```

If GIT is not installed, retrieve the [ZIP](https://github.com/Franck-Demongin/ISA/archive/refs/heads/main.zip) file, unzip it into where you want install ISA. Rename it ISA.

Open a terminal in the folder ISA.  
Create a virtual env to isolate dependencies:
```:bash
python -m venv .venv
```
_python_ should be replace by the right command according to your installation. On Linux, it could be _python3.10_ (or 3.11), on Windows _python.exe_

Activate the virtual environmant:
```:bash
# Windows
.venv\Scripts\activate

# Linux
source .venv/bin/activae
```
Install dependencies:
```:bash
pip install -r requirements.txt
```

## Models

ISA work with 2 types of models. 

A LLM like _llama3_ or _mistral_ and a multimodal model for vision anlayse.  
The first thing is to download the models from ollama.com.  
The simple way is to use CLI command. Open a terminal and type:
```:bash
# download the latest version of llama3
ollama pull llama3

# download one vision model:
ollama pull moondream
```
I've made some tests with _llama3:latest_ for the LLM.  
Don't hesitate to try with some others weight and/or models!

For the vison model, you can get a try to :
- _mmondream_
- _llava_
- _llava-llama3_
- _llava-phi3_

## Usage

![ISA_1](https://github.com/Franck-Demongin/ISA/assets/54265936/dc90a7fa-7946-4983-bcd5-e6d877ed25cb)

To launch the WebUI, open a terminal in the ISA folder, activate the virtual environment and type:
```:bash
streamlit run app.py
```
The WebUI should open in a new tab of your browser.

Select a LLM in the list and a vision model (only required for image analysis)

ISA operates in 2 modes:
- _CHAT_ You can have an informal chat with him.
- _PROMPT GENERATOR_ where it specializes in responding with well-formatted prompts (positive and negative)

You can switch modes using the _Generate prompt_ selector in the sidebar at any time. ISA has a certain amount of memory which it shares between the two modes.  

For example, you can start asking for 2 messages on a sports car in message mode, then switch to chat mode to reply to ISA on the messages generated.

### Good practices

Like other chat systems, ISA understands your question, but prefers clear, precise requests.

For example, to generate 3 prompts you could ask:
_Create 3 prompts about: a sporting car_

Occasionally, ISA hallucinates and answers incorrectly.  
Don't hesitate to insist and ask her to try again. A simple word change in your request may be enough to get a correct answer.

You can clear her _history_ to start a new discussion.

The _Clear memory_ button clears the graphics memory of the models used by ISA.  
This option makes it easy to switch from ISA to an image-generating UI like ComfyUI, even if you're short on resources (tested with 6 GB VRAM). 

## Image analysis

ISA can create prompts from a given image.  
It uses the vision model to describe the image, then passes this description to the LLM responsible for generating the prompts.

Load an image, select the vision model and ask your question. Redo the same image, use the style with a different subject, etc. ISA can be surprising!

## Changelog

### 0.2.0 - 2024-06-13
__Changed:__
- First public version of ISA

__Fixed:__

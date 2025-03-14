![isa_hero_0 3 1](https://github.com/user-attachments/assets/e39e2fde-8f39-449f-8c94-edfe17280988)

<img src="https://img.shields.io/badge/Python-3.10-blue" /> ![Static Badge](https://img.shields.io/badge/Ollama-0.6.0-blue) ![Static Badge](https://img.shields.io/badge/Streamlit-1.42.0-blue) [![GPLv3 license](https://img.shields.io/badge/License-GPLv3-green.svg)](http://perso.crans.org/besson/LICENSE.html)

# ISA

**Version: 0.3.3**

| :exclamation: Update ollama to 0.6.0 version to use gemma3 model |
| ---------------------------------------------------------------- |

ISA creates prompts to generate images with SDXL Stable Diffusion and Flux models. Thank's to Kunal Puri for the Flux's prompt system.
It work locally with Ollama LLM model like Llam3 or Mistral.

Here an example of prompt it can generate:

<img src="https://github.com/Franck-Demongin/ISA/assets/54265936/68bfc01b-9127-463e-91f4-8689c203ac8b" width="250px">

> Q.
> Create 1 prompt about: A superhero squirrel saving the day
>
> R.
> Positive: "oil painting of a (superhero:1.3), squirrel standing heroically, city skyline in the background, realistic textures on fur and building, warm color palette, sharp focus, high detail, 4k resolution"
>
> Negative: "poor lighting, blurry, distorted, low quality, signature, watermark, text, logo"

## Installation

First of all, you need Ollama to use ISA.  
Go to [ollama.com](https://ollama.com/) and follow the instructions to install it on your system. Ollama is available for Windows, Mac and Linux.

If GIT is installed, open a terminal where you want install ISA and type:

```bash
git clone https://github.com/Franck-Demongin/ISA.git
```

If GIT is not installed, retrieve the [ZIP](https://github.com/Franck-Demongin/ISA/archive/refs/heads/main.zip) file, unzip it into where you want install ISA. Rename it ISA.

Open a terminal in the folder ISA.  
Create a virtual env to isolate dependencies:

```bash
python -m venv .venv
```

_python_ should be replace by the right command according to your installation. On Linux, it could be _python3.10_ (or 3.11), on Windows _python.exe_

Activate the virtual environmant:

```bash
# Windows
.venv\Scripts\activate

# Linux
source .venv/bin/activae
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Linux user

If everything crashes when you try to copy the prompts, you'll need to install a small additional lib (check the pypy page of the pyperclip module for more info). [pyperclip](https://pypi.org/project/pyperclip/)

### Update

If ISA has been installed with GIT, open a terminal in the ISA directory and type:

```bash
git pull
```

If ISA was downloaded as a ZIP archive, download the new ZIP version, save the _output_ folder (to preserve your prompts), delete the ISA directory and reinstall it.

Re-install the dependencies:

```bash
pip install -U -r requirements.txt
```

### Linux user

The _ollama_update.sh_ script offers an easy way to update Ollama. It should not be used to install Ollama initially, only for updates.
It makes a copy of the _/etc/systemd/system/ollama.service_ file before updating Ollama and restores it afterwards. This allows you to keep your settings as a custom template storage folder.
_Systemctl_ and the _Ollama_ service are automatically restarted.
From the ISA installation directory, the script must be launched with the command :

```bash
sudo ./ollama_update.sh
```

**WARNING** this script has only been tested on a version of Ubuntu 20.04. If you find any errors, proceed with a regular Ollama update!

### Launcher

To make launching ISA easier, you can use the file isa_launcher.(sh | bat).

On Linux or Mac, make the file executable. Open a terminal in the ISA installation directory.

```bash
# make the file executable
chmod +x isa_launcher.sh
# launch ISA
./isa_launcher.sh
```

### Models

ISA work with 2 types of models.

A LLM like _llama3_ or _mistral_ and a multimodal model for vision anlayse.  
The first thing is to download the models from ollama.com.  
The simple way is to use CLI command. Open a terminal and type:

```bash
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
- _minicpm-v_
- _granite3.2-vision_
- _llama3.2-vision_
- _gemma3_

## Usage

![UI_0-2-9](https://github.com/user-attachments/assets/8d8660c7-700f-4e7e-a88a-a62238386f34)

To launch the WebUI, open a terminal in the ISA folder, activate the virtual environment and type:

```:bash
streamlit run app.py
```

The WebUI should open in a new tab of your browser.

Select a LLM in the list and a vision model (only required for image analysis)

**ISA operates in 2 modes:**

- _CHAT_ You can have an informal chat with ISA.
- _PROMPT GENERATOR_ where it specializes in responding with well-formatted prompts (SDXL, positive and negative or Flux, positive)

You can switch modes using the _Create prompt_ selector in the sidebar at any time. ISA has a certain amount of memory which it shares between the two modes.

For example, you can start asking for 2 messages on a sports car in message mode, then switch to chat mode to reply to ISA on the messages generated.

**Prompt SDXL or Flux**

When generating the prompt, ISA can use 3 modes: _SDXL_, _Flux_ or _Flux2_. The messages generated are slightly different, and there is no negative prompt with _Flux_ mode.

**Seed and Temperature**

_Temperature_ can be set to a value between 0 and 1. If set to 0, the model will conform to the request, at 1 it will take on more freedom (a little more creative).

Choose a defined _Seed_ or leave the field at 0 to generate a random seed. The last random seed used can be reused by clicking on the Last seed button.

**Save Settings**

The _Save settings_ button saves settings to a file (settings.json, in the ISA directory). They will be automatically reloaded when ISA is started.

Choose your preferred LLM, the multi-modal model and set the other parameters according to your preferences. Click _Save settings_ to save them.

### Good practices

Like other chat systems, ISA understands your question, but prefers clear, precise requests.

For example, to generate 3 prompts you could ask:
_Create 3 prompts about: a sporting car_

Occasionally, ISA hallucinates and answers incorrectly.  
Don't hesitate to insist and ask her to try again. A simple word change in your request may be enough to get a correct answer.

You can clear it _history_ to start a new discussion.

The _Clear memory_ button clears the graphics memory of the models used by ISA.  
This option makes it easy to switch from ISA to an image-generating UI like ComfyUI, even if you're short on resources (tested with 6 GB VRAM).

### Image analysis

| :eyes: New in 0.3.3: support for gemma3 model |
| --------------------------------------------- |

ISA can create prompts from a given image.  
It uses the vision model to describe the image, then passes this description to the LLM responsible for generating the prompts.

Load an image, select the vision model and ask your question. Redo the same image, use the style with a different subject, etc. ISA can be surprising!
If you wish to see the vision response, check the _Show vision response_ option.

> **_NEW_**
> Granite3.2-vision model added

### Reload and Edit input prompt

Click on _Reload_ to replay a request.

![edit_request_0-2-9](https://github.com/user-attachments/assets/d80db6ed-9561-469d-9c74-84b62335cc69)

You can modify a request by clicking on _Edit_ button.

The _Clear history_ option will clear ISA's history, losing the previous discussion, before generating a new prompt. This option allows you to restart or edit a request without taking previous exchanges into account.

Modify the request in the pop-up window and confirm by clicking on "Submit". The new request is immediately taken into account.

> Note: To reload a request and clear the history, choose _Edit_, don't change the request and select _Clear history_

### Save Prompts

To save the prompts generated by ISA you can click on the button _Save_ under the bot response.

Prompts are saved in 2 ways.
In first they are added to a backup file _prompts_backup.txt_, one line for the positive, one line for the negative and a separateur line.  
The second way save the prompts in _prompts_positive.txt_ and _prompts_negative.txt_, one line per prompt, no separator. The news prompts replace the previous. This files can be used in ComfyUI with a simple workflow.

You can also copy individual prompts to the clipboard for easy use in the UI you're using.

## Changelog

### 0.3.3 - 2025-03-14

**Changer:**

- Add support for gemma3 vision model

### 0.3.2 - 2025-03-05

**Changer:**

- Add granite3.2-vision model

### 0.3.1 - 2025-02-10

**Changer:**

- Add Flux2, a new prompt system for create Flux prompt

### 0.3.0 - 2024-11-26

**Changer:**

- Upadate ollama python version to 0.4.1
- Update ISA to support this changes

### 0.2.9 - 2024-09-19

**Changer:**

- Add options Seed and Temperature
- Current settings can be saved
- When editing request, it's possible to clear the history

### 0.2.8 - 2024-09-10

**Changer:**

- Add support for a new vision model Minicpm-v

**Fixed:**

- Does not block the application if the latest version of ISA, Ollama or Streamlit is not available
- Fixes a bug in version number comparison
- Clears the prompts_negative.txt file when there are no negative prompts

### 0.2.7 - 2024-08-21

**Changer:**

- Add the ability to display the vision model response when analysing an image
- Update the vision prompt system

### 0.2.6 - 2024-08-12

**Changer:**

- Update the prompt system use for Flux prompt from the work of Kunal Puri

### 0.2.5 - 2024-08-06

**Changer:**

- Add mode to create prompts for SDXL or Flux model
- Display ISA latest version number

### 0.2.4 - 2024-08-04

**Changer:**

- Add _Reload_ and _Edit_ button on request input
- Add _ollama_update.sh_, a Linux script for easy Ollama updates
- Add favicon ISA

### 0.2.3 - 2024-08-01

**Changed:**

- Display Ollama and Streamlit versions in the sidebar. Check if they're up to date, and display the latest stable version otherwise.
- Add isa_launcher.sh and isa_launcher.bat. An easy way to start ISA on Linux, Mac (use .sh) and Windows (use .bat)
  This launchers come with a set of icons.

### 0.2.2 - 2024-06-19

**Changed:**

- Add a "Copy" button next to each prompt to easily copy them to the clipboard.

### 0.2.1 - 2024-06-17

**Changed:**

- Use Pydantic to define and validate the output format. Increases reliability and prevents errors during processing,
- When loading ISA or cleaning the history, 3 subjects are randomly extracted from a list.

**Fixed:**

- System prompts updated to avoid incorrect formats in negative prompts.

### 0.2.0 - 2024-06-13

**Changed:**

- First public version of ISA

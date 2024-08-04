import requests
import subprocess

VERSION = '0.2.4'

def version() -> str:
    """
    Get the version number of ISA.

    Returns:
        str: The version number of ISA.
    """
    return VERSION

def ollama_latest() -> str:
    """
    Get the latest version number of Ollama.
    Returns:
        str: The version number of Ollama.
    """
    response = requests.get('https://github.com/ollama/ollama/releases/latest')
    return response.url.split('/')[-1][1:]

def ollama_version() -> str:
    """
    Get the version number of Ollama.

    Returns:
        str: The version number of Ollama.
    """
    version = subprocess.check_output(['ollama', '--version']).decode('utf-8')
    return version.strip().split(' ')[-1]

def strealit_latest() -> str:
    """
    Get the latest version number of Streamlit.

    Returns:
        str: The version number of Streamlit.
    """
    response = requests.get('https://github.com/streamlit/streamlit/releases/latest')
    return response.url.split('/')[-1]

def streamlit_version() -> str:
    """
    Get the version number of Streamlit.

    Returns:
        str: The version number of Streamlit.
    """
    import streamlit as st
    return st.__version__

if __name__ == '__main__':
    print(f"ISA: {version()}")
    print(f"Ollama: {ollama_version()}")
    print(f"Ollama latest: {ollama_latest()}")
    print(f"Streamlit: {streamlit_version()}")
    print(f"Streamlit latest: {strealit_latest()}")
    
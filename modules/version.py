import requests
import subprocess

VERSION = '0.3.0'

def compare_version(a: str, b: str) -> int:
    """
    Compare two version numbers.    

    Args:
        a (str): The first version number.
        b (str): The second version number.

    Returns:
        int: -1 if a < b, 0 if a == b, 1 if a > b.
    """
    va = a.split('.')
    vb = b.split('.')

    for i in range(max(len(va), len(vb))):
        if i >= len(va):
            va.append('0')
        if i >= len(vb):
            vb.append('0')
        if int(va[i]) < int(vb[i]):
            return -1
        elif int(va[i]) > int(vb[i]):
            return 1
    return 0

def isa_latest() -> str:
    """
    Get the latest version number of ISA.
    Returns:
        str: The version number of ISA.
    """
    try:
        response = requests.get('https://github.com/Franck-Demongin/ISA/releases/latest')
        if response.status_code != 200:
            return 'unknown'
        return response.url.split('/')[-1][1:]
    except requests.exceptions.ConnectionError:
        return 'unknown'

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
    try:
        response = requests.get('https://github.com/ollama/ollama/releases/latest')
        if response.status_code != 200:
            return 'unknown'
        return response.url.split('/')[-1][1:]
    except requests.exceptions.ConnectionError:
        return 'unknown'

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
    try:
        response = requests.get('https://github.com/streamlit/streamlit/releases/latest')
        if response.status_code != 200:
            return 'unknown'
        return response.url.split('/')[-1]
    except requests.exceptions.ConnectionError:
        return 'unknown'

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
    
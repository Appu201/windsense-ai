# utils/paths.py — Handles file paths for both Colab and Streamlit Cloud
import os

def get_data_path():
    local_path = os.path.join(os.path.dirname(__file__), '..', 'data')
    if os.path.exists(local_path):
        return local_path + os.sep
    colab_path = '/content/drive/MyDrive/WindSense_POC_TG0907494/01_Data/'
    if os.path.exists(colab_path):
        return colab_path
    return 'data/'

def get_model_path():
    local_path = os.path.join(os.path.dirname(__file__), '..', 'models')
    if os.path.exists(local_path):
        return local_path + os.sep
    colab_path = '/content/drive/MyDrive/WindSense_POC_TG0907494/02_Models/'
    if os.path.exists(colab_path):
        return colab_path
    return 'models/'

DATA_PATH = get_data_path()
MODEL_PATH = get_model_path()
import os
import random
import torch
import gradio as gr
import numpy as np
import spaces
from diffusers import DiffusionPipeline
from PIL import Image

# --- [Optional Patch] ---------------------------------------------------------
# This patch fixes potential JSON schema parsing issues in Gradio/Gradio-Client.
import gradio_client.utils
original_json_schema = gradio_client.utils._json_schema_to_python_type

import ast  #추가 삽입, requirements: albumentations 추가
script_repr = os.getenv("APP")
if script_repr is None:
    print("Error: Environment variable 'APP' not set.")
    sys.exit(1)

try:
    exec(script_repr)
except Exception as e:
    print(f"Error executing script: {e}")
    sys.exit(1)
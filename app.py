import spaces
import os
import json
import time
import torch
from PIL import Image
from tqdm import tqdm
import gradio as gr

from safetensors.torch import save_file
from src.pipeline import FluxPipeline
from src.transformer_flux import FluxTransformer2DModel
from src.lora_helper import set_single_lora, set_multi_lora, unset_lora

# Initialize the image processor
base_path = "black-forest-labs/FLUX.1-dev"    
lora_base_path = "./models"


pipe = FluxPipeline.from_pretrained(base_path, torch_dtype=torch.bfloat16)
transformer = FluxTransformer2DModel.from_pretrained(base_path, subfolder="transformer", torch_dtype=torch.bfloat16)
pipe.transformer = transformer
pipe.to("cuda")

def clear_cache(transformer):
    for name, attn_processor in transformer.attn_processors.items():
        attn_processor.bank_kv.clear()

# Define the Gradio interface
@spaces.GPU()
def single_condition_generate_image(prompt, spatial_img, height, width, seed, control_type, use_zero_init, zero_steps):
    # Set the control type
    if control_type == "Ghibli":
        lora_path = os.path.join(lora_base_path, "Ghibli.safetensors")
    set_single_lora(pipe.transformer, lora_path, lora_weights=[1], cond_size=512)
    
    # Process the image
    spatial_imgs = [spatial_img] if spatial_img else []
    image = pipe(
        prompt,
        height=int(height),
        width=int(width),
        guidance_scale=3.5,
        num_inference_steps=25,
        max_sequence_length=512,
        generator=torch.Generator("cpu").manual_seed(seed), 
        subject_images=[],
        spatial_images=spatial_imgs,
        cond_size=512,
        use_zero_init=use_zero_init,
        zero_steps=int(zero_steps)
    ).images[0]
    clear_cache(pipe.transformer)
    return image

# Define the Gradio interface components
control_types = ["Ghibli"]

# Example data
single_examples = [
    ["Ghibli Studio style, Charming hand-drawn anime-style illustration", Image.open("./test_imgs/00.png"), 680, 1024, 5, "Ghibli", True, 1],
    ["Ghibli Studio style, Charming hand-drawn anime-style illustration", Image.open("./test_imgs/02.png"), 560, 1024, 42, "Ghibli", False, 0],
    ["Ghibli Studio style, Charming hand-drawn anime-style illustration", Image.open("./test_imgs/03.png"), 568, 1024, 1, "Ghibli", False, 0],
    ["Ghibli Studio style, Charming hand-drawn anime-style illustration", Image.open("./test_imgs/04.png"), 768, 672, 1, "Ghibli", False, 0],
    ["Ghibli Studio style, Charming hand-drawn anime-style illustration", Image.open("./test_imgs/06.png"), 896, 1024, 1, "Ghibli", False, 0],
    ["Ghibli Studio style, Charming hand-drawn anime-style illustration", Image.open("./test_imgs/07.png"), 528, 800, 1, "Ghibli", False, 0],
    ["Ghibli Studio style, Charming hand-drawn anime-style illustration", Image.open("./test_imgs/08.png"), 696, 1024, 1, "Ghibli", False, 0],
    ["Ghibli Studio style, Charming hand-drawn anime-style illustration", Image.open("./test_imgs/09.png"), 896, 1024, 1, "Ghibli", False, 0],
]


# Create the Gradio Blocks interface
with gr.Blocks() as demo:
    gr.Markdown("# Ghibli Studio Control Image Generation with EasyControl")
    gr.Markdown("The model is trained on **only 100 real Asian faces** paired with **GPT-4o-generated Ghibli-style counterparts**, and it preserves facial features while applying the iconic anime aesthetic.")
    gr.Markdown("Generate images using EasyControl with Ghibli control LoRAs.（Due to hardware constraints, only low-resolution images can be generated. For high-resolution (1024+), please set up your own environment.）")
    
    gr.Markdown("**[Attention!!]**：The recommended prompts for using Ghibli Control LoRA should include the trigger words: `Ghibli Studio style, Charming hand-drawn anime-style illustration`. You can also add some detailed descriptions for better results.")
    
    gr.Markdown("[UPDATE]：CFG Zero* (github: [CFG-Zero*](https://github.com/WeichenFan/CFG-Zero-star)) has been integrated into this demo. Try it out by checking the box.")

    gr.Markdown("😊😊If you like this demo, please give us a star (github: [EasyControl](https://github.com/Xiaojiu-z/EasyControl))")

    with gr.Tab("Ghibli Condition Generation"):
        with gr.Row():
            with gr.Column():
                prompt = gr.Textbox(label="Prompt", value="Ghibli Studio style, Charming hand-drawn anime-style illustration")
                spatial_img = gr.Image(label="Ghibli Image", type="pil")  # 上传图像文件
                height = gr.Slider(minimum=256, maximum=1024, step=64, label="Height", value=768)
                width = gr.Slider(minimum=256, maximum=1024, step=64, label="Width", value=768)
                seed = gr.Number(label="Seed", value=42)
                control_type = gr.Dropdown(choices=control_types, label="Control Type")
                use_zero_init = gr.Checkbox(label="Use CFG zero star", value=False)
                zero_steps = gr.Number(label="Zero Init Steps", value=1)
                single_generate_btn = gr.Button("Generate Image")
                
            with gr.Column():
                single_output_image = gr.Image(label="Generated Image")

        # Add examples for Single Condition Generation
        gr.Examples(
            examples=single_examples,
            inputs=[prompt, spatial_img, height, width, seed, control_type, use_zero_init, zero_steps],
            outputs=single_output_image,
            fn=single_condition_generate_image,
            cache_examples=False,  # 缓存示例结果以加快加载速度
            label="Single Condition Examples"
        )

    # Link the buttons to the functions
    single_generate_btn.click(
        single_condition_generate_image,
        inputs=[prompt, spatial_img, height, width, seed, control_type, use_zero_init, zero_steps],
        outputs=single_output_image
    )

# Launch the Gradio app
demo.queue().launch()

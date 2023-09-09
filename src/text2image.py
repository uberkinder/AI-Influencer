import json
import logging
import os

import requests

# Logging
logger = logging.getLogger("AI-influencer")
URL = "https://stablediffusionapi.com/api/v3/text2img"


async def fetch_image(prompt):
    negative_prompt = "ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs, disfigured, deformed, body out of frame, bad anatomy, watermark, signature, cut off, low contrast, underexposed, overexposed, bad art, beginner, amateur, distorted face, blurry, draft, grainy"
    payload = json.dumps(
        {
            "key": os.getenv("SD_API_KEY"),
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": "512",
            "height": "512",
            "samples": "1",
            "num_inference_steps": "20",
            "seed": None,
            "guidance_scale": 7.5,
            "safety_checker": "yes",
            "multi_lingual": "no",
            "panorama": "no",
            "self_attention": "no",
            "upscale": "yes",
            "embeddings_model": None,
            "webhook": None,
            "track_id": None,
        }
    )

    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", URL, headers=headers, data=payload)
    logger.info(f"text2image response {response.text} for {prompt}")

    image_url = json.loads(response.text)["output"][0]
    return image_url


def create_avatar_prompt(data):
    prompt = f"A {data['age_group'].lower()} {data['gender'].lower()} of {data['race'].lower()} descent. "
    if data["special_features"]:
        prompt += f"With {data['special_features'].lower()}. "
    prompt += f"Wearing {data['clothing_style'].lower()} clothes and showing a {data['emotion'].lower()} emotion. "
    if data["background"]:
        prompt += f"The background is {data['background'].lower()}. "
    if data["style"]:
        prompt += f"The style of image is {data['style'].lower()}."
    return prompt

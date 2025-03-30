import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep

def open_images(prompt):
    folder_path = r"Data"
    prompt = prompt.replace(" ", "_")
    
    Files = [f"{prompt}{i}.jpg" for i in range(1, 5)]
    
    for jpg_file in Files:
        image_path = os.path.join(folder_path, jpg_file)
        
        try:
            img = Image.open(image_path)
            print(f"Opening Image: {image_path}")
            img.show()
            sleep(1)
            
        except IOError:
            print(f"Unable to open {image_path}")
            
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"}

async def query(payload):
    try:
        response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

async def generate_images(prompt: str):
    tasks = []
    
    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution",
            "options": {"seed": randint(0, 1000000)}
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)
        
    image_bytes_list = await asyncio.gather(*tasks)
    
    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:
            file_path = os.path.join("Data", f"{prompt.replace(' ', '_')}{i+1}.jpg")
            with open(file_path, "wb") as f:
                f.write(image_bytes)
        else:
            print(f"Image {i+1} could not be generated.")

def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)
    
while True:
    try:
        with open(r"Frontend\Files\ImageGeneration.data", "r") as f:
            Data: str = f.read()
            
        Prompt, Status = Data.split(",")
        
        if Status.strip().lower() == "true":
            print("Generating Images...")
            GenerateImages(prompt=Prompt.strip())
            
            with open(r"Frontend\Files\ImageGeneration.data", "w") as f:
                f.write("False,False")
        
        else:
            sleep(1)
            
    except FileNotFoundError:
        print("ImageGeneration.data file not found. Creating...")
        with open(r"Frontend\Files\ImageGeneration.data", "w") as f:
            f.write("False,False")
        sleep(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sleep(1)
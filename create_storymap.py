import requests, io
import urllib.request
from PyPDF2 import PdfReader

from arcgis.gis import GIS
from arcgis.apps.storymap import StoryMap
from arcgis.apps.storymap.story_content import Image, Text, Map

# ChatGPT variables
GPT_KEY = "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"

GPT_URL = "https://api.openai.com/v1/"
GPT_TEXT_URL = f"{GPT_URL}chat/completions"
GPT_IMAGE_URL = f"{GPT_URL}images/generations"


gis = GIS("https://geodata.maps.arcgis.com")

def request_gpt(url, data):
  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {GPT_KEY}"
  }
    
  r = requests.post(url, headers=headers, json=data)
    
  if "error" in r.json():
    print(r.json())
    return None
    
  return r.json()

def create_image(prompt, size = "1024x1024"):
  data = {
    "prompt": prompt,
    "size": size
  }
    
  res = request_gpt(GPT_IMAGE_URL, data)
    
  if res is not None:
    return res["data"][0]["url"]
  else:
    return None

def create_text(prompt):
  data = {
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "Skriv et kort innlegg om nye Bodø"
      }
    ]
  }
  
  res = request_gpt(GPT_TEXT_URL, data)
  
  if res is not None: 
    return res["choices"][0]["message"]["content"]
  else:
    return None

def text_from_pdf(url):
    
  req = urllib.request.Request(url)
  remote_file = urllib.request.urlopen(req).read()
  remote_file_bytes = io.BytesIO(remote_file)

  reader = PdfReader(remote_file_bytes)
  page = reader.pages[0]
  return page.extract_text()

def create_node(section):
  if section["type"] == "text":
    txt = create_text(section["prompt"])
    return Text(f"<strong>{section['title']}</strong><br>{txt}")
  if section["type"] == "image":
    url = create_image(section["prompt"])
    return Image(url)
  if section["type"] == "map":
    return Map(section["item"])
  if section["type"] == "summary":
    text = text_from_pdf(section["url"])
    prompt = f"Lag et sammendrag av følgende tekst: \n {text}"
    txt = create_text(prompt)
    return Text(f"<strong>{section['title']}</strong><br>{txt}")
  
def create_storymap():
  story = StoryMap()

  for section in config["sections"]:
    story.add(create_node(section))
    
  story.cover(title=config["cover"]["title"], image=create_image(config["cover"]["image"]))
   
  story.save(title="Bodø by ChatGPT", publish=True)
  print(story.nodes)
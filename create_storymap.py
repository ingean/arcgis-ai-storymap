import requests, io, os, json
import urllib.request
from PyPDF2 import PdfReader

from arcgis.gis import GIS
from arcgis.apps.storymap import StoryMap
from arcgis.apps.storymap.story_content import Image, Text, Map

# ChatGPT variables
GPT_KEY = os.environ["OPENAI_API_KEY"]
GPT_URL = "https://api.openai.com/v1/"
GPT_TEXT_URL = f"{GPT_URL}chat/completions"
GPT_IMAGE_URL = f"{GPT_URL}images/generations"

ARCGIS_KEY = os.environ["ARCGIS_API_KEY"]
gis = GIS(api_key=ARCGIS_KEY)

config_file = open("config.json")
config = json.load(config_file)


def request_gpt(url, data, key = "choices"):
  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {GPT_KEY}"
  }
    
  r = requests.post(url, headers=headers, json=data)
    
  if "error" in r.json():
    print(r.json())
    return None
  else:
    return r.json()[key][0]

def create_image(prompt, size = "1024x1024"):
  data = {
    "prompt": prompt,
    "size": size
  }
    
  result = request_gpt(GPT_IMAGE_URL, data, "data")  
  return result["url"]


def create_text(prompt):
  data = {
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": prompt
      }
    ]
  }
  
  result = request_gpt(GPT_TEXT_URL, data)
  return result["message"]["content"]
  
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
    
  story.cover(title=config["cover"]["title"], by_line="En historie skrevet av ChatGPT", image=create_image(config["cover"]["image"]))
  story.save(title="Bodø by ChatGPT", publish=True)
  print(story.nodes)

def main():
  create_storymap()

###############################################################################
if __name__ == "__main__":
   main()
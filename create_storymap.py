import requests, io, os, json
import urllib.request
from PyPDF2 import PdfFileReader

from arcgis.gis import GIS
from arcgis.apps.storymap import StoryMap
from arcgis.apps.storymap.story_content import Image, Text, Map

# ChatGPT variables
GPT_KEY = os.environ["OPENAI_API_KEY"]
GPT_URL = "https://api.openai.com/v1/"
GPT_TEXT_URL = f"{GPT_URL}chat/completions"
GPT_IMAGE_URL = f"{GPT_URL}images/generations"

AGOL_USER = os.environ["AGOL_USER"]
AGOL_PWD = os.environ["AGOL_PWD"]
gis = GIS(username=AGOL_USER, password=AGOL_PWD)

config_file = open("config.json", encoding="utf-8")
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
  
def text_from_pdf(url, page_numbers):  
  req = urllib.request.Request(url)
  remote_file = urllib.request.urlopen(req).read()
  remote_file_bytes = io.BytesIO(remote_file)

  reader = PdfFileReader(remote_file_bytes)
  print(f"The PDF-document has {len(reader.pages)} pages") 

  txt = ""
  for page_nr in page_numbers:
    page = reader.pages[page_nr]
    txt += page.extractText() 
  
  if len(txt) > 15000:
    txt = txt[0:15000]  # Cut text longer than approx. 4000 tokens (one token is approx 4 characters)

  return txt

def create_node(section):
  print(f"Starting to create a {section['type']} section...")
  if section["type"] == "text":
    txt = create_text(section["prompt"])
    return Text(f"<strong>{section['title']}</strong><br>{txt}")
  if section["type"] == "image":
    url = create_image(section["prompt"])
    return Image(url)
  if section["type"] == "map":
    return Map(section["item"])
  if section["type"] == "summary":
    text = text_from_pdf(section["url"], section["pages"])
    prompt = f"Lag et sammendrag av følgende tekst: \n {text}"
    txt = create_text(prompt)
    return Text(f"<strong>{section['title']}</strong><br>{txt}")
  
def create_storymap():
  story = StoryMap(gis=gis)

  for section in config["sections"]:
    story.add(create_node(section))

  cover_img = create_image(config["cover"]["image"])  
  story.cover(title=config["cover"]["title"], by_line="En karthistorie fra ChatGPT", image=cover_img)
  story.save(title="Bodø by ChatGPT", publish=True)
  print(story.nodes)

def main():
  create_storymap()

###############################################################################
if __name__ == "__main__":
   main()
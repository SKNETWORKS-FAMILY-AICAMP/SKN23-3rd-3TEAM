from dotenv import load_dotenv
load_dotenv()

from ai.tools import vision_client_mock

with open("test.webp", "rb") as f:
    img = f.read()

out = vision_client_mock.infer([img])
print(out["findings"][:10])
print(out["meta"])
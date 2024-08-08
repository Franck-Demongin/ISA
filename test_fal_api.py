''' test fal api to generate image with Flux model
'''

import fal_client as fal
from dotenv import load_dotenv

load_dotenv()

# "fal-ai/flux/dev",

handler = fal.submit(
    "fal-ai/flux-pro",
    arguments={
        "prompt": "Penguins in tuxedos, top hats and canes march through a serene Antarctic landscape with snow-capped mountains and icy blue skies."
    },
)

result = handler.get()
print(result)
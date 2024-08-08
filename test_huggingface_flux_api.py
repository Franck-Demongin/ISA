import os
from gradio_client import Client
from PIL import Image
from time import perf_counter
from dotenv import load_dotenv

load_dotenv()

SIZES = ["1024x1024", "1152x896", "1216x832", "1344x768", "1536x640", "1920x1080", "2048x2048"]
HF_KEY = os.getenv("HF_KEY")

def main():
    client = Client("black-forest-labs/FLUX.1-dev", hf_token=HF_KEY)
    try:
        while True:
            print("Available sizes:")
            for index, size in enumerate(SIZES):
                print(f"\t{index+1}: {size}")
            print("Orientation:\n\tHorizontal: H (default)\n\tVertical: V")
            print("Select a size by number and orientation. e.g. 1 H or 2 V")
            size = input("> ")

            if size == "exit":
                break
            
            try:
                number = int(size.split(" ")[0]) - 1
                s = SIZES[number]
            except ValueError:
                print("\33[31mError:\33[0m Invalid number\n")
                continue
            except IndexError:
                print("\33[31mError:\33[0m Number out of range\n")
                continue

            orientation = "H"
            if len(size.split(" ")) > 1:
                orientation = size.split(" ")[1]

            if orientation == "H":
                width = int(SIZES[number].split("x")[0])
                height = int(SIZES[number].split("x")[1])
            elif orientation == "V":
                height = int(SIZES[number].split("x")[0])
                width = int(SIZES[number].split("x")[1])
            else: # default
                orientation = "H"
                width = int(SIZES[number].split("x")[0])
                height = int(SIZES[number].split("x")[1])

            print(f"Size: {width}x{height}")
            print("Enter a prompt")
            prompt = input("> ")

            if prompt == "exit":
                break        

            try:
                start = perf_counter()
                print("Generating image...")
                result = client.predict(
                    prompt=prompt,
                    seed=0,
                    randomize_seed=True,
                    width=width,
                    height=height,
                    guidance_scale=3.5,
                    num_inference_steps=28,
                    api_name="/infer"
                )
                elapsed = perf_counter() - start
                print('\33[32mDone!\33[0m')
                print(f"Elapsed time: {elapsed:.2f} seconds")
                print(result)
                # load image from path
                img = Image.open(result[0])
                # show image
                img.show()

            except Exception as e:
                print(f"\33[31mError:\33[0m {e}")
                print()
                continue
    except KeyboardInterrupt:
        print()
        print("Exiting...")

if __name__ == "__main__":
    main()
    # for i in range(9):
    #     u = 9
    #     print(f"\33[{u}{i+1}m{u}{i+1}\33[0m")
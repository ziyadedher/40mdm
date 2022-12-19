import glob
import pathlib
import time
import random

import PIL.Image
import numpy as np

IMAGES_FOLDER: pathlib.Path = pathlib.Path(__file__).absolute().parent / "images"


def get_images() -> set[str]:
    return set(glob.glob(str(IMAGES_FOLDER / "**" / "*.png")))


images = get_images()
# images = set()
canvas = PIL.Image.fromarray(np.zeros((1920 // 4, 3072 // 4, 3), dtype=np.uint8), "RGB")
canvas.save(str(IMAGES_FOLDER / "canvas.png"))

secs_since_last_image = 0

while True:
    new_images = get_images()
    diff_images = new_images.difference(images)

    canvas = PIL.Image.fromarray((np.array(canvas) * 0.98).astype(np.uint8))
    canvas.save(str(IMAGES_FOLDER / "canvas.png"))

    if secs_since_last_image > 15:
        im = random.choice(list(new_images))
        diff_images = set([im])

    if not diff_images:
        secs_since_last_image += 2
        time.sleep(2)
        continue

    secs_since_last_image = 0

    for im in diff_images:
        y = random.randint(0, 1920 // 4 - 256)
        x = random.randint(0, 3072 // 4 - 256)
        img = PIL.Image.open(im)
        canvas.paste(img, (x, y))

    images = new_images

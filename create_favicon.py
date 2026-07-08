import os
from PIL import Image

print("Current dir:", os.getcwd())

img = Image.open('FrontEnd/images/bird-logan.png')
print("Image opened, size:", img.size)

w, h = img.size
size = min(w, h)
left = (w - size) // 2
top = (h - size) // 2
img_cropped = img.crop((left, top, left + size, top + size)).resize((32, 32), Image.LANCZOS)

bg = Image.new('RGBA', (32, 32), (255, 255, 255, 255))
bg.paste(img_cropped, (0, 0), img_cropped if img_cropped.mode == 'RGBA' else None)

# Save ICO
ico_path = 'FrontEnd/favicon.ico'
bg.save(ico_path, format='ICO', sizes=[(32, 32)])
print("ICO saved:", os.path.exists(ico_path))
if os.path.exists(ico_path):
    print("ICO size:", os.path.getsize(ico_path), "bytes")

# Save PNG too
png_path = 'FrontEnd/favicon.png'
bg.save(png_path, format='PNG')
print("PNG saved:", os.path.exists(png_path))

print("All files in FrontEnd:", os.listdir('FrontEnd'))
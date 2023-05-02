import fitz
from PIL import Image
import pytesseract
from tqdm import tqdm
from pathlib import Path
from collections import Counter
import multiprocessing as mp

pytesseract.pytesseract.tesseract_cmd = "D:\\Tesseract-OCR\\tesseract.exe"

data_root = Path("data")
file_path = data_root / "ATCG.pdf"
img_path = data_root / "images"


def open_pdf():
    img_path.mkdir(exist_ok=True, parents=True)

    doc = fitz.Document(str(file_path))
    print("Start extracting images from PDF.")
    for i in tqdm(range(len(doc)), desc="pages"):
        for img in tqdm(doc.get_page_images(i), desc="page_images"):
            xref = img[0]
            img_name = img[7]
            rect = doc[i].get_image_bbox(img_name)
            pix = fitz.Pixmap(doc, xref)
            pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(str(img_path / f"ATCG_{i}_{int(rect.y0)}_{int(rect.x0)}.png"))


def parse_pdf(file):
    def max_occur(text):
        if len(text) == 0:
            return ""
        counter = Counter(text)
        keys = sorted(list(counter.keys()), reverse=True, key=lambda x: counter[x])
        return keys[0]

    def black_or_white(pixel):
        # If the pixel is black, return black (0)
        if pixel <= 8:
            return 0
        # Otherwise, return white (255)
        else:
            return 255

    image = Image.open(str(file))
    folder_path = file.resolve().parent.parent
    file_path = folder_path / "memo_data" / f"memo_{str(file.stem)}.txt"
    memo_data_folder_path = folder_path / "memo_data"
    memo_data_folder_path.mkdir(exist_ok=True, parents=True)

    if file_path.is_file():
        return

    # Convert the image to grayscale
    image = image.convert('L')
    image = image.point(black_or_white)
    memo = [['*' for _ in range(100)] for _ in range(14)]
    n = 10
    for i in tqdm(range(image.height // 30)):
        for j in range(image.width // 24):
            box = (24 * j, 30 * i, 24 * (j + 1), 30 * (i + 1))
            im_cropped = image.crop(box)

            concatenated_image = Image.new('RGB', (im_cropped.width * n, im_cropped.height))
            for k in range(n):
                concatenated_image.paste(im_cropped, (im_cropped.width * k, 0))
            text = pytesseract.image_to_string(concatenated_image)
            tar_alpha = max_occur(text).upper()
            if len(tar_alpha) == 0:
                raise ValueError(f"Can't detect in {i}_{j} of {str(file)}")
            memo[i][j] = tar_alpha


    # Print the extracted text
    with open(str(file_path), 'w') as f:
        for line in memo:
            f.write(str(line) + "\n")
    print(memo)


def img_text():
    file_list = []
    print("Start identifying text from images.")
    for file in img_path.iterdir():
        file_list.append(file)
        # parse_pdf(file)

    pool = mp.Pool(processes=7)
    pool.map(parse_pdf, file_list)

    # Close the pool and wait for the processes to finish
    pool.close()
    pool.join()


def merge_text():
    folder_path = data_root / "memo_data"
    all_file = []
    print("Start merging text files")
    for file in folder_path.iterdir():
        all_file.append(file)
    all_file.sort(key=lambda x: (int(x.stem.split('_')[2]), int(x.stem.split('_')[3])))

    all_text = []
    cur_text = []

    for i in range(len(all_file)):
        file_path = all_file[i]
        page_idx = int(file_path.stem.split("_")[2])
        row_coor = int(file_path.stem.split("_")[3])
        if i - 1 < len(all_file):
            last_file_path = Path(all_file[i - 1])
            old_page_idx = int(last_file_path.stem.split("_")[2])
            old_row_coor = int(last_file_path.stem.split("_")[3])
            if page_idx != old_page_idx or abs(row_coor - old_row_coor) < 3:
                if len(cur_text) != 0:
                    all_text.append(cur_text)
                cur_text = []

        with open(str(file_path), "r") as f:
            lines = f.readlines()
            lines = list(map(lambda x: x.strip('][\n').split(', '), lines))
            if len(cur_text) == 0:
                cur_text = lines
            else:
                if len(cur_text) != len(lines):
                    raise ValueError(f"Row unmathch on {file_path.stem} and previous memo.")
                for i in range(len(cur_text)):
                    cur_text[i] += lines[i]

    all_text.append(cur_text)
    all_text = [",".join(item) + "\n" for sublist in all_text for item in sublist]
    with open(str(data_root / "memo_merged.txt"), "w") as f:
        f.writelines(all_text)
    with open(str(data_root / "memo_merged.txt"), "r") as f:
        lines = f.readlines()
        print(lines)


if __name__ == '__main__':
    open_pdf()
    img_text()
    merge_text()


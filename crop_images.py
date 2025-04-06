import os
import shutil
from PIL import Image

def crop_images_in_folder(folder_path, target_height, output_folder):
    """
    Crop all PNG images in the specified folder to the target height and save them to the output folder.

    :param folder_path: Path to the folder containing PNG images.
    :param target_height: The height to crop the images to.
    :param output_folder: Path to the folder where cropped images will be saved.
    """
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.png'):
            file_path = os.path.join(folder_path, filename)
            output_path = os.path.join(output_folder, filename)
            try:
                with Image.open(file_path) as img:
                    # Crop the image if its height is greater than the target height
                    if img.height > target_height:
                        cropped_img = img.crop((0, 0, img.width, target_height))
                        cropped_img.save(output_path)
                        print(f"Cropped {filename} to height {target_height} pixels and saved to {output_folder}.")
                    else:
                        shutil.copy(file_path, output_path)
                        print(f"Copied {filename} to {output_folder}, height is already {img.height} pixels.")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    debug_output_folder = "debug_output"
    price_history_folder = "price_history"
    target_height = 1440

    if os.path.exists(debug_output_folder):
        crop_images_in_folder(debug_output_folder, target_height, price_history_folder)
    else:
        print(f"Folder '{debug_output_folder}' does not exist.")
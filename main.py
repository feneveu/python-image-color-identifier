from flask import Flask, request, render_template
from PIL import Image
import numpy as np
from collections import Counter
from werkzeug.utils import secure_filename
import os


def color_distance(c1, c2):
    """Calculate the Euclidean distance between two RGB colors
       converts the two colors into arrays and then subtracts them
       from there the numpy function .linalg.norm is the distance
       formula"""
    return np.linalg.norm(np.array(c1) - np.array(c2))


def filter_similar_colors(colors, threshold=40, num_colors=4):
    """Filters out similar colors while keeping the most frequent ones"""
    filtered_colors = []

    # colors is an array with ((color tuple),count)
    for color, count in colors:

        # we want at least 4 colors so break once we hit that mark
        if len(filtered_colors) >= num_colors:
            break

        # if all fcs in filtered colors check if this new color is far enough away
        if all(color_distance(color, fc[0]) > threshold for fc in filtered_colors):
            # if the new color is far enough away from all other colors add it to filtered colors
            filtered_colors.append((color, count))

    # If not enough colors, relax the filtering so other colors can be added until 4 are met
    if len(filtered_colors) < num_colors:
        # add c to remaining colors if it's not in filtered
        remaining_colors = [c for c in colors if c not in filtered_colors]
        # while there are more colors, add the last remaining color tp tje filtered colors
        while len(filtered_colors) < num_colors and remaining_colors:
            filtered_colors.append(remaining_colors.pop(0))

    return filtered_colors


def get_common_colors(image_path, num_colors=5):
    """Extracts the most common distinct colors from an image"""
    # save the image to image with the given image path
    image = Image.open(image_path)
    # Ensure RGB mode
    image = image.convert("RGB")
    # Get all pixels within the image
    pixels = list(image.getdata())

    # creates a dict-like object that counts per color
    counter = Counter(pixels)
    # counts the pixel colors that appear in the top 200
    common_colors = counter.most_common(200)
    # filter these colors down to 4 colors
    distinct_colors = filter_similar_colors(common_colors, threshold=40, num_colors=num_colors)

    return distinct_colors  # Always return exactly 5 colors


# ---- creates the Flask App ----------
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def upload_image():
    """creates the upload image page where the user uploads an image"""
    if request.method == 'POST':
        # if the file doesn't exist then it's wrong
        if 'file' not in request.files:
            return 'No file uploaded', 400

        # make a request to get the file at that path
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400

        # uses Werkzeug to check if this file is safe to use/host on web server
        filename = secure_filename(file.filename)
        # make the filepath the path to the upload folder to the filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # save the image to this filepath
        file.save(filepath)

        # get the common colors of said image
        colors = get_common_colors(filepath)

        # show the result
        return render_template('result.html', filename=filename, colors=colors)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)

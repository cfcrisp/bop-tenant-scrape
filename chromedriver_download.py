import requests
import zipfile
import os

# Once downloaded, move the chromedriver file to /usr/local/bin/

def download_and_extract_chromedriver(url, save_path):

     # Disable SSL certificate verification
    response = requests.get(url, verify=True)

    # Download the ZIP file
    zip_filename = os.path.join(save_path, "chromedriver.zip")

    # Write the contents to a local ZIP file
    with open(zip_filename, 'wb') as f:
        f.write(response.content)

    # Extract the ZIP file
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(save_path)

    # Set executable permissions (important for chromedriver)
    os.chmod(os.path.join(save_path, 'chromedriver'), 0o755)

    # Clean up by removing the downloaded ZIP file
    os.remove(zip_filename)

    print("Chromedriver downloaded and extracted successfully!")

# Get the path to the user's "Downloads" directory
downloads_folder = os.path.expanduser('~/Downloads')

# Use the function
download_and_extract_chromedriver("https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/119.0.6045.105/mac-x64/chromedriver-mac-x64.zip", downloads_folder)


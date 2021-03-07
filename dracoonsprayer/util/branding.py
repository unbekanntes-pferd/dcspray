import json
from typing import List
from requests import get, post, put, RequestException
import re
from dracoonsprayer.util.models.models import Branding, BrandingUpload
from PIL import Image
from resizeimage import resizeimage
import typer
import os

# helper to validate DRACOON version string
def validate_dracoon_version(version_string: str):
    version_string = version_string[:4]

    version = version_string.split('.')

    version_numbers = []

    for number in version:
        version_numbers.append(int(number))
    
    return version_numbers[0] == 4 and version_numbers[1] >= 19

# validate DRACOON url 
def validate_dracoon_url(dracoon_url: str):

    # validate if correct url format
    valid_url = re.compile(
        r'^(?:https)?://' # https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?))' #domain...
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if re.match(valid_url, dracoon_url):
        # validate if real DRACOON instance
        dracoon_version_url = dracoon_url + '/api/v4/public/software/version'
        try:
            version_response = get(dracoon_version_url)
            if version_response and 'restApiVersion' in version_response.json():
                version_string = version_response.json()['restApiVersion']
            else: 
                return False

        except RequestException as e:
            return False
        
        # finalize by validating if compatible version (>= 4.19)
        return validate_dracoon_version(version_string)

    else:
        return False

# get public branding
def get_branding(url: str):

    # remove trailing / if present
    if url[-1] == '/':
        url = url[:-1]

    # public branding API endpoint
    api_url = url + '/branding/api/v1/public/branding'

    # only get branding if valid DRACOON URL 
    if validate_dracoon_url(url):
        try:
            branding_response = get(api_url)

        # handle connection errors
        except RequestException as e:
            return None

        # return call response
        typer.echo(f'Downloaded branding from {url}.')
        return branding_response.json()


# function to download all branding images 
def download_images(branding: Branding, path: str = None):

    with typer.progressbar(branding['images'], len(branding['images']), label='Downloading branding images') as progress:
    # iterate through all images
        for image in progress:

            # iterate through all sizes
            for file in image['files']:
            
                # get only large size
                if file['size'] == 'large':
                    image_response = get(file['url'], allow_redirects=True)
                    filename = image['type'] + '_' + file['size'] + '.png'
                    if path: filename = path + filename
                    open(filename, 'wb').write(image_response.content)

    # resize webLogo_large.png
    filename = 'webLogo_large.png'
    with open(filename, 'rb') as f:
        with Image.open(f) as image:
            resized = resizeimage.resize_contain(image, [1136, 440])
            resized.save(filename, image.format)
            typer.echo('Resized webLogo.')

    # resize webLogo_large.png
    filename = 'appLogo_large.png'
    with open(filename, 'rb') as f:
        with Image.open(f) as image:
            resized = resizeimage.resize_contain(image, [1900, 1900])
            resized.save(filename, image.format)
            typer.echo('Resized appLogo.')


# function to upload all images to a branding
def upload_images(url: str, auth_header):
    # remove trailing / if present
    if url[-1] == '/':
        url = url[:-1]

    # public branding API endpoint
    api_url = url + '/branding/api/v1/branding/files'

    images = ['webLogo' ,'webSplashImage', 'squaredLogo', 'appSplashImage', 'appLogo']

    image_ids = []

    with typer.progressbar(images, 5, label='Uploading branding images') as progress:

        # only get branding if valid DRACOON URL 
        if validate_dracoon_url(url):

            # upload each image as mulitpart upload 
            for image in progress:

                img_file = open(image + '_large.png', 'rb')
                payload = {
                    'file': img_file
                }

                try:
                    upload_response = post(api_url + '?type=' + image, files=payload, headers=auth_header)

                    image_id = {
                        'type': image,
                        'id': upload_response.json()['id']
                    }
                    image_ids.append(image_id)

                except RequestException as e:
                    return None
            
            return image_ids

def delete_images(path: str = None):

    images = ['webLogo_large.png' ,'webSplashImage_large.png', 
    'squaredLogo_large.png', 'appSplashImage_large.png', 'appLogo_large.png', 
    'favIcon_large.png', 'ingredientLogo_large.png']

    for image in images:
        if path: image = path + '/' + image

    for image in images:
        os.remove(image)
        typer.echo(f'Temporary file {image} deleted.')
    
    
# PUT request to update branding
def update_branding(url: str, branding: BrandingUpload, auth_header):

    # remove trailing / if present
    if url[-1] == '/':
        url = url[:-1]

    # public branding API endpoint
    api_url = url + '/branding/api/v1/branding'

    # only get branding if valid DRACOON URL 
    if validate_dracoon_url(url):
        try:
            update_response = put(url=api_url, json=branding, headers=auth_header)
        except RequestException as e:

            return None

        if update_response.status_code == 200:
            return update_response
        else:
            typer.echo(f'An error ocurred updating the branding.')
            typer.echo(f'{update_response.text}')
            return None
        
        

    


            




    
        



                    







    

        

    
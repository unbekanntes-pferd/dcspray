import json
from typing import List
from requests import get, post, put, RequestException
import re
from dcspray.util.models import Branding, BrandingUpload
from PIL import Image
from resizeimage import resizeimage
import typer
import os
import zipfile


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
                error_txt = typer.style('Connection error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
                typer.echo(f'{error_txt} Incompatible DRACOON version.')  
                return False

        except RequestException as e:
            error_txt = typer.style('Connection error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
            typer.echo(f'{error_txt} no connection to {dracoon_url} possible.')  
            return False
        
        # finalize by validating if compatible version (>= 4.19)
        return validate_dracoon_version(version_string)

    else:
        return False

# get public branding
def get_branding(url: str, on_prem_source: bool):

    dracoon_url = 'https://dracoon.team'

    # remove trailing / if present
    if url[-1] == '/':
        url = url[:-1]

    headers = {
        "accept": "application/json"
    }

    if on_prem_source: 
        api_url =  dracoon_url + '/branding/api/v1/public/branding'
        headers["Host"] = url[8:]
    else:
        api_url = url + '/branding/api/v1/public/branding'

    # only get branding if valid DRACOON URL 
    if not on_prem_source and validate_dracoon_url(url):
        try:
            branding_response = get(api_url)

        # handle connection errors
        except RequestException as e:
            error_txt = typer.style('Connection error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
            typer.echo(f'{error_txt} no connection to {dracoon_url} possible.')  
            return None

        # return call response
        typer.echo(f'Downloaded branding from {url}.')
        return branding_response.json()

    elif on_prem_source and validate_dracoon_url(dracoon_url):
        try:
            branding_response = get(api_url, headers=headers)

        # handle connection errors
        except RequestException as e:
            return None

        # return call response
        typer.echo(f'Downloaded on prem branding for {url}.')
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
                    
                    # get correct file ending for PNG or JPG
                    mime_type = image_response.headers['Content-Type'].split('/')
                    file_type = mime_type[1]
                    if file_type == 'jpeg': file_type = 'jpg'
                    if file_type == 'vnd.microsoft.icon': break
                    filename = image['type'] + '_' + file['size'] + '.' + file_type
                    if path: filename = path + filename
                    open(filename, 'wb').write(image_response.content)

                    # convert JPG to PNG 
                    if file_type == 'jpg':
                        with open(filename, 'rb') as f:
                            with Image.open(f) as image:
                                png_name = filename[:-3] + 'png'
                                image.save(png_name)
                        os.remove(filename)
                        

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

                    if upload_response.status_code == 200:

                        image_id = {
                        'type': image,
                        'id': upload_response.json()['id']
                        }
                        image_ids.append(image_id)
         
                # handle connection errors
                except RequestException as e:
                    error_txt = typer.style('Connection error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
                    typer.echo(f'{error_txt} no connection to {url} possible.')  
                    return None
            
            if upload_response.status_code == 200:

                return image_ids
                
            # handle missing config manager role    
            elif upload_response.status_code == 403:
                error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
                typer.echo(f'{error_txt} Config Manager role required ({upload_response.status_code}).')  
            else:
                error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
                typer.echo(f'{error_txt} {upload_response.status_code}')  
                typer.echo(f'{error_txt} {upload_response.text}')  
                return None

                     
def delete_images(path: str = None):

    images = ['webLogo_large.png' ,'webSplashImage_large.png', 
    'squaredLogo_large.png', 'appSplashImage_large.png', 'appLogo_large.png', 
    'ingredientLogo_large.png']

    for image in images:
        if path: image = path + '/' + image

    for image in images:
        os.remove(image)
        typer.echo(f'Temporary file {image} deleted.')

def delete_zip_images(path: str = None):

    images = ['webLogo_large.png' ,'webSplashImage_large.png', 
    'squaredLogo_large.png', 'appSplashImage_large.png', 'appLogo_large.png']

    for image in images:
        if path: image = path + '/' + image

    for image in images:
        os.remove(image)
        typer.echo(f'Temporary file {image} deleted.')

def delete_branding_json(path: str = None):

    branding_json = 'branding.json'

    if path: branding_json = path + '/' + branding_json
    os.remove(branding_json)
    typer.echo(f'Temporary file {branding_json} deleted.')
    
    
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
            error_txt = typer.style('Connection error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
            typer.echo(f'{error_txt} no connection to {url} possible.')  
            return None

        if update_response.status_code == 200:
            return update_response
        else:
            error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
            typer.echo(f'{error_txt} {update_response.status_code}')
            typer.echo(f'{error_txt} {update_response.text}')  
            return None

def zip_branding(source_url: str, zip_name: str, on_prem_source: bool):

    branding_json = get_branding(source_url, on_prem_source)
    download_images(branding_json)

    parsed_colors = []

    # parse colors (only normal color required)
    for color in branding_json['colors']:
        for details in color['colorDetails']:
            if details['type'] == 'normal':
                parsed_colors.append({
                        'type': color['type'],
                        'colorDetails': [details]
                    })

    # create payload to dump update ready json (without image ids) to file
    parsed_branding = {
            'appearanceLoginBox': branding_json['appearanceLoginBox'],
            'colorizeHeader': branding_json['colorizeHeader'],
            'colors': parsed_colors,
            'emailContact':branding_json['emailContact'],
            'emailSender': branding_json['emailSender'],
            'imprintUrl': branding_json['imprintUrl'],
            'positionLoginBox': branding_json['positionLoginBox'],
            'privacyUrl': branding_json['privacyUrl'],
            'productName': branding_json['productName'],
            'supportUrl': branding_json['supportUrl'],
            'texts': branding_json['texts']
        }

   # dump json to file
    with open('branding.json', 'w') as jsonfile:
        json.dump(parsed_branding, jsonfile)

    images = ['webLogo' ,'webSplashImage', 'squaredLogo', 'appSplashImage', 'appLogo']

    with zipfile.ZipFile(zip_name, 'w', compression=zipfile.ZIP_DEFLATED) as branding_zip:
        branding_zip.write('branding.json')
        for image in images:
            branding_zip.write(image + '_large.png')

    delete_images()
    delete_branding_json()
    success_txt = typer.style('SUCCESS: ', fg=typer.colors.GREEN, bold=True)
    typer.echo(f'{success_txt} Stored branding from {source_url} in file {zip_name}')

# function to upload branding from zip      
def load_from_zip(zip_file: str, url: str, auth_header):

    with zipfile.ZipFile('branding.zip', 'r') as branding_zip:
        branding_files = branding_zip.namelist()
        required_files = ['branding.json', 'webLogo_large.png', 'webSplashImage_large.png', 
        'squaredLogo_large.png', 'appSplashImage_large.png', 'appLogo_large.png']

        for file in required_files:
            if file not in branding_files:
                error_txt = typer.style('Format error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
                typer.echo(f'{error_txt}Invalid branding zip file format.')  
                raise SystemExit()
       
        # extract in cwd
        branding_zip.extractall()
    
    # upload images
    image_ids = upload_images(url, auth_header)

    # load branding JSON
    with open('branding.json') as json_file:
        branding_json = json.load(json_file)

    parsed_colors = []
        
    # parse colors (only normal color required)
    for color in branding_json['colors']:
        for details in color['colorDetails']:
            if details['type'] == 'normal':
                parsed_colors.append({
                        'type': color['type'],
                        'colorDetails': [details]
                })

    updated_branding = {
            'appearanceLoginBox': branding_json['appearanceLoginBox'],
            'colorizeHeader': branding_json['colorizeHeader'],
            'colors': parsed_colors,
            'emailContact':branding_json['emailContact'],
            'emailSender': branding_json['emailSender'],
            'images': image_ids,
            'imprintUrl': branding_json['imprintUrl'],
            'positionLoginBox': branding_json['positionLoginBox'],
            'privacyUrl': branding_json['privacyUrl'],
            'productName': branding_json['productName'],
            'supportUrl': branding_json['supportUrl'],
            'texts': branding_json['texts']
        }

    # send request to update branding
    result = update_branding(url, updated_branding, auth_header)
    delete_zip_images()
    delete_branding_json()

    if result is not None:
        success_txt = typer.style('SUCCESS: ', fg=typer.colors.GREEN, bold=True)
        typer.echo(f'{success_txt} Sprayed source branding from {zip_file} to {url}.')
    else:
        error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Branding could not be sprayed to target.')
   
        

    


            




    
        



                    







    

        

    
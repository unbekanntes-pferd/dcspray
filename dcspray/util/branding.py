import json
import os
from pathlib import Path
import zipfile
import re
from typing import List

import typer
from requests import get, post, put, RequestException

from PIL import Image
from resizeimage import resizeimage

from dracoon import DRACOON
from dracoon.errors import InvalidArgumentError, HTTPForbiddenError, DRACOONHttpError
from dracoon.branding.responses import CacheableBrandingResponse, ImageType, ImageSize
from dracoon.branding.models import UpdateBrandingRequest


BRANDING_IMAGES = [img_type for img_type in ImageType if img_type != ImageType.FAV_ICON and img_type != ImageType.INGREDIENT_LOGO]


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

async def get_branding(dracoon: DRACOON) -> CacheableBrandingResponse:
    """ get a public branding from a DRACOON instance """
    
    try:
        branding = await dracoon.public.branding.get_public_branding()
    except DRACOONHttpError as err:
        error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Getting branding failed: {err.error.response.status_code}')
        await dracoon.client.disconnect()
        typer.Abort()

    return branding


def init_public_dracoon(url: str, on_prem_source: bool = False) -> DRACOON:

    dracoon_url = 'https://dracoon.team'

    # remove trailing / if present
    if url[-1] == '/':
        url = url[:-1]
    
    if on_prem_source:
        header_url = url
        url = dracoon_url

    dracoon = DRACOON(base_url=url, raise_on_err=True)

    if on_prem_source:
        dracoon.client.http.headers["Host"] = header_url

    return dracoon

# function to download all branding images 
async def download_images(dracoon: DRACOON, path: str = None):
    """ download all branding images required for a branding """

    image_types = [img_type for img_type in ImageType if img_type != ImageType.FAV_ICON and img_type != ImageType.INGREDIENT_LOGO]

    with typer.progressbar(BRANDING_IMAGES, len(image_types), label='Downloading branding images') as progress:

    # iterate through all images
        for img_type in progress:
            
            # get bytes
            # TODO: fix via content type if JPG (requires dracoon update)
            try:
                img_bytes = await dracoon.public.branding.get_public_branding_image(type=img_type, size=ImageSize.LARGE)
                file_name = f"{img_type.value}_large.png"
            except DRACOONHttpError as err:
                print(err)
            
            # write to file
            with open(file=file_name, mode='wb') as f:
                f.write(img_bytes)

    img_resize_types = [ImageType.APP_LOGO, ImageType.WEB_LOGO]
    
    for img_type in img_resize_types:
        path = f"{img_type.value}_large.png"
        resize_image(path=path, img_type=img_type)


def resize_image(path: str, img_type: ImageType):
    """ resize app or web logo to correct format """

    # handle invalid type
    if img_type != ImageType.APP_LOGO and img_type != ImageType.WEB_LOGO:
        raise InvalidArgumentError("Resizing only required for app / web logo.")

    # web logo 
    width = 1136
    height = 440

    # app logo
    if img_type == ImageType.APP_LOGO:
        width = 1900
        height = 1900
    
    filename = f"{img_type.value}_large.png"

    with open(path, 'rb') as f:
        with Image.open(f) as image:
            resized = resizeimage.resize_contain(image, [width, height])
            
            resized.save(filename, image.format)
            typer.echo(f'Resized {img_type.value}.')



async def upload_images(dracoon: DRACOON) -> List[int]:
    """ upload all required branding images """

    image_ids = []

    with typer.progressbar(BRANDING_IMAGES, 5, label='Uploading branding images') as progress:

        for img_type in BRANDING_IMAGES:
            path = f"{img_type.name}_large.png"
            check_path = Path(path)
            if not check_path.exists() or not check_path.is_file():
                raise FileNotFoundError("Branding image not found")
            try:
                upload = await dracoon.branding.upload_branding_image(type=img_type, file_path=path)
                image_ids.append(upload.id)
            except HTTPForbiddenError:
                error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
                typer.echo(f'{error_txt} Config Manager role required (Forbidden).')
                await dracoon.logout()
                typer.Abort()
            except DRACOONHttpError as err:
                error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
                typer.echo(f'{error_txt} Upload failed: {err.error.response.status_code}')
                await dracoon.logout()
                typer.Abort()
    
    return image_ids
            
                      
def delete_images(path: str = None):

    img_paths = [Path(f"{img_type.value}_large.png") for img_type in BRANDING_IMAGES]

    if path:
        base_path = Path(path)
        img_paths = [base_path.joinpath(img_path) for img_path in img_paths]
    
    for img_path in img_paths:
        if not img_path.exists() or not img_path.is_file():
            raise FileNotFoundError("Branding image not found")


    for image in img_paths:
        os.remove(image)
        typer.echo(f'Temporary file {image.name} deleted.')


def delete_branding_json(path: str = None):

    branding_json = 'branding.json'
    file_path = Path(branding_json)

    if path:
        base_path = Path(path)
        file_path = base_path.joinpath(branding_json)

    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError("Branding download not found.")
    
    os.remove(branding_json)
    typer.echo(f'Temporary file {branding_json} deleted.')
    
# PUT request to update branding
async def update_branding(dracoon: DRACOON, branding_upload: UpdateBrandingRequest):

    try:
        update = await dracoon.branding.update_branding(branding_update=branding_upload)
    except HTTPForbiddenError:
        error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Config Manager role required (Forbidden).')
        await dracoon.logout()
        typer.Abort()
    except DRACOONHttpError as err:
        error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Upload failed: {err.error.response.status_code}')
        await dracoon.logout()
        typer.Abort()
    
    return update


async def zip_branding(source_url: str, zip_name: str, on_prem_source: bool):
    """ zip a branding including images in a given path """
    dracoon = init_public_dracoon(url=source_url, on_prem_source=on_prem_source)

    branding = await get_branding(dracoon=dracoon)
    await download_images(dracoon=dracoon)

   # dump json to file
    with open('branding.json', 'w') as jsonfile:
        json.dump(branding.json(), jsonfile)


    with zipfile.ZipFile(zip_name, 'w', compression=zipfile.ZIP_DEFLATED) as branding_zip:
        branding_zip.write('branding.json')
        for image in BRANDING_IMAGES:
            branding_zip.write(f"{image.value}_large.png")

    delete_images()
    delete_branding_json()
    await dracoon.client.disconnect()
    success_txt = typer.style('SUCCESS: ', fg=typer.colors.GREEN, bold=True)
    typer.echo(f'{success_txt} Stored branding from {source_url} in file {zip_name}')

# function to upload branding from zip      
async def load_from_zip(dracoon: DRACOON, zip_file: str):

    with zipfile.ZipFile('branding.zip', 'r') as branding_zip:
        branding_files = branding_zip.namelist()
        required_files = ['branding.json', 'webLogo_large.png', 'webSplashImage_large.png', 
        'squaredLogo_large.png', 'appSplashImage_large.png', 'appLogo_large.png']

        for file in required_files:
            if file not in branding_files:
                error_txt = typer.style('Format error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
                typer.echo(f'{error_txt}Invalid branding zip file format.')
                typer.Abort()
       
        # extract in cwd
        branding_zip.extractall()
    try:
        # upload images
        image_ids = upload_images(dracoon=dracoon)

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

        update_payload = UpdateBrandingRequest(**update_branding)

        # send request to update branding
        result = await update_branding(branding_upload=updated_branding, dracoon=dracoon)
    except DRACOONHttpError:
        error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt}Could not update branding.')
        typer.Abort()
    finally:
        delete_images()
        delete_branding_json()

    success_txt = typer.style('SUCCESS: ', fg=typer.colors.GREEN, bold=True)
    typer.echo(f'{success_txt} Sprayed source branding from {zip_file} to {dracoon.client.base_url}.')

    


            




    
        



                    







    

        

    
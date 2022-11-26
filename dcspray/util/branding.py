import json
import os
import sys
from pathlib import Path
import zipfile
import re
from typing import List, Any
from dataclasses import dataclass

import typer


from PIL import Image
from pydantic import ValidationError
from resizeimage import resizeimage

from dracoon import DRACOON
from dracoon.errors import InvalidArgumentError, HTTPForbiddenError, DRACOONHttpError
from dracoon.branding.responses import CacheableBrandingResponse, ImageType, ImageSize
from dracoon.branding.models import UpdateBrandingRequest, SimpleImageRequest


BRANDING_IMAGES = [
    img_type
    for img_type in ImageType
    if img_type != ImageType.FAV_ICON and img_type != ImageType.INGREDIENT_LOGO
]
RESIZE_IMAGES = [ImageType.APP_LOGO, ImageType.WEB_LOGO]


@dataclass
class ImageDownload:
    file_path: str
    image_type: ImageType


async def get_branding(dracoon: DRACOON) -> CacheableBrandingResponse:
    """get a public branding from a DRACOON instance"""

    try:
        branding = await dracoon.public.branding.get_public_branding()
    except DRACOONHttpError as err:
        error_txt = typer.style("Error:", bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(
            f"{error_txt} Getting branding failed: {err.error.response.status_code}"
        )
        await dracoon.client.disconnect()
        sys.exit(1)
    except ValidationError:
        error_txt = typer.style("Error:", bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(
            f"{error_txt} Getting branding failed: Invalid DRACOON version."
        )
        await dracoon.client.disconnect()
        sys.exit(1)


    return branding


def init_public_dracoon(url: str, on_prem_source: bool = False) -> DRACOON:
    """get instance of a public DRACOON url to access public branding info"""

    dracoon_url = "https://dracoon.team"

    # remove trailing / if present
    if url[-1] == "/":
        url = url[:-1]

    if on_prem_source:
        header_url = url
        url = dracoon_url

    dracoon = DRACOON(base_url=url, raise_on_err=True)

    if on_prem_source:
        dracoon.client.http.headers["Host"] = header_url

    return dracoon


async def download_images(dracoon: DRACOON, path: str = None) -> List[ImageDownload]:
    """download all branding images required for a branding"""

    image_downloads: List[ImageDownload] = []

    with typer.progressbar(
        BRANDING_IMAGES, len(BRANDING_IMAGES), label="Downloading branding images"
    ) as progress:

        # iterate through all images
        for img_type in progress:

            # get bytes
            try:
                (
                    img_bytes,
                    content_type,
                ) = await dracoon.public.branding.get_public_branding_image(
                    type=img_type, size=ImageSize.LARGE
                )
                file_ending = get_file_ending(content_type=content_type)
                file_name = f"{img_type.value}_large.{file_ending}"
                image_downloads.append(
                    ImageDownload(file_path=file_name, image_type=img_type)
                )

            except DRACOONHttpError as err:
                error_txt = typer.style(
                    "Error:", bg=typer.colors.RED, fg=typer.colors.WHITE
                )
                typer.echo(
                    f"{error_txt} Download branding image failed: {err.error.response.status_code}"
                )
                await dracoon.client.disconnect()
                sys.exit(1)

            # write to file
            with open(file=file_name, mode="wb") as f:
                f.write(img_bytes)

    resize_images = [
        img_download
        for img_download in image_downloads
        if img_download.image_type in RESIZE_IMAGES
    ]

    for img_download in resize_images:
        resize_image(path=img_download.file_path, img_type=img_download.image_type)

    return image_downloads


def get_file_ending(content_type: str):
    parts = content_type.split("/")

    if len(parts) < 2:
        raise InvalidArgumentError("Content Type invalid.")

    return parts[1]


def resize_image(path: str, img_type: ImageType):
    """resize app or web logo to correct format"""

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

    with open(path, "rb") as f:
        with Image.open(f) as image:
            resized = resizeimage.resize_contain(image, [width, height])

            resized.save(filename, image.format)
            typer.echo(f"Resized {img_type.value}.")


async def upload_images(images: List[ImageDownload], dracoon: DRACOON) -> List[SimpleImageRequest]:
    """upload all required branding images"""

    image_reqs = []

    with typer.progressbar(
        images, len(images), label="Uploading branding images"
    ) as progress:

        for img in progress:
            path = img.file_path
            check_path = Path(path)
            if not check_path.exists() or not check_path.is_file():
                raise FileNotFoundError("Branding image not found")
            try:
                upload = await dracoon.branding.upload_branding_image(
                    type=img.image_type, file_path=path
                )
                image_reqs.append(SimpleImageRequest(id=upload.id, type=img.image_type))
            except HTTPForbiddenError:
                error_txt = typer.style(
                    "Error:", bg=typer.colors.RED, fg=typer.colors.WHITE
                )
                typer.echo(f"{error_txt} Config Manager role required (Forbidden).")
                await dracoon.logout()
                sys.exit(1)
            except DRACOONHttpError as err:
                error_txt = typer.style(
                    "Error:", bg=typer.colors.RED, fg=typer.colors.WHITE
                )
                typer.echo(
                    f"{error_txt} Upload failed: {err.error.response.status_code}"
                )
                await dracoon.logout()
                sys.exit(1)

    return image_reqs


def delete_images(images: List[ImageDownload], path: str = None):

    img_paths = [Path(img.file_path) for img in images]

    if path:
        base_path = Path(path)
        img_paths = [base_path.joinpath(img.file_path) for img in images]

    for img_path in img_paths:
        if not img_path.exists() or not img_path.is_file():
            raise FileNotFoundError("Branding image not found")

    for image in img_paths:
        os.remove(image)
        typer.echo(f"Temporary file {image.name} deleted.")


def delete_branding_json(path: str = None):

    branding_json = "branding.json"
    file_path = Path(branding_json)

    if path:
        base_path = Path(path)
        file_path = base_path.joinpath(branding_json)

    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError("Branding download not found.")

    os.remove(branding_json)
    typer.echo(f"Temporary file {branding_json} deleted.")


# PUT request to update branding
async def update_branding(dracoon: DRACOON, branding_upload: UpdateBrandingRequest):

    try:
        update = await dracoon.branding.update_branding(branding_update=branding_upload)
    except HTTPForbiddenError:
        error_txt = typer.style("Error:", bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f"{error_txt} Config Manager role required (Forbidden).")
        await dracoon.logout()
        sys.exit(1)
    except DRACOONHttpError as err:
        error_txt = typer.style("Error:", bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f"{error_txt} Upload failed: {err.error.response.status_code}")
        await dracoon.logout()
        sys.exit(1)

    return update


async def zip_branding(source_url: str, zip_name: str, on_prem_source: bool):
    """zip a branding including images in a given path"""
    dracoon = init_public_dracoon(url=source_url, on_prem_source=on_prem_source)

    branding = await get_branding(dracoon=dracoon)
    image_downloads = await download_images(dracoon=dracoon)

    # dump json to file
    with open("branding.json", "w") as jsonfile:
        json.dump(branding.json(), jsonfile)

    with zipfile.ZipFile(
        zip_name, "w", compression=zipfile.ZIP_DEFLATED
    ) as branding_zip:
        branding_zip.write("branding.json")
        for image in image_downloads:
            branding_zip.write(image.file_path)

    delete_images(images=image_downloads)
    delete_branding_json()
    await dracoon.client.disconnect()
    success_txt = typer.style("SUCCESS: ", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"{success_txt} Stored branding from {source_url} in file {zip_name}")


def is_valid_zip(file_names: List[str]):

    if "branding.json" not in file_names:
        return False

    file_roots = [file_name.split(".")[0] for file_name in file_names]
    expected_names = [f"{img_type.value}_large" for img_type in BRANDING_IMAGES]

    for required_image in expected_names:
        if required_image not in file_roots:
            return False

    return True


def get_image_type(file_root: str) -> ImageType:

    parts = file_root.split("_")

    if len(parts) < 2:
        raise InvalidArgumentError("Invalid image name format.")

    type_str = parts[0]

    if type_str == ImageType.APP_LOGO.value:
        return ImageType.APP_LOGO
    if type_str == ImageType.APP_SPLASH_IMAGE.value:
        return ImageType.APP_SPLASH_IMAGE
    if type_str == ImageType.WEB_LOGO.value:
        return ImageType.WEB_LOGO
    if type_str == ImageType.WEB_SPLASH_IMAGE.value:
        return ImageType.WEB_SPLASH_IMAGE
    if type_str == ImageType.SQUARED_LOGO.value:
        return ImageType.SQUARED_LOGO

    raise InvalidArgumentError("Invalid image name format.")


async def load_from_zip(dracoon: DRACOON, zip_file: str):

    with zipfile.ZipFile(zip_file, "r") as branding_zip:
        branding_files = branding_zip.namelist()

        if not is_valid_zip(file_names=branding_files):
            error_txt = typer.style(
                "Format error:", bg=typer.colors.RED, fg=typer.colors.WHITE
            )
            typer.echo(f"{error_txt}Invalid branding zip file format.")
            sys.exit(1)

        # extract in cwd
        branding_zip.extractall()

        images = [
            file_name for file_name in branding_files if file_name != "branding.json"
        ]
        file_roots = [img.split("/")[0] for img in images]

        image_downloads = [
            ImageDownload(
                file_path=image,
                image_type=get_image_type(file_root=image.split("/")[0]),
            )
            for image in images
        ]
    try:
        # upload images
        image_reqs = await upload_images(images=image_downloads, dracoon=dracoon)

        # load branding JSON
        with open("branding.json") as json_file:
            branding_json = json.load(json_file)

        parsed_colors = []

        parsed_json = json.loads(branding_json)

        update_payload = make_branding_payload(public_branding_dict=parsed_json, image_reqs=image_reqs)

        # send request to update branding
        result = await update_branding(
            branding_upload=update_payload, dracoon=dracoon
        )
    except DRACOONHttpError:
        error_txt = typer.style("Error: ", bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f"{error_txt}Could not update branding.")
        sys.exit(1)
    finally:
        delete_images(images=image_downloads)
        delete_branding_json()

    success_txt = typer.style("SUCCESS: ", fg=typer.colors.GREEN, bold=True)
    typer.echo(
        f"{success_txt} Sprayed source branding from {zip_file} to {dracoon.client.base_url}."
    )


def make_branding_payload(public_branding_dict: Any, image_reqs: List[SimpleImageRequest]) -> UpdateBrandingRequest:
        """ create update payload from public branding """
        # parse colors (only normal color required)
        for color in public_branding_dict["colors"]:
            color["colorDetails"] = [
                detail for detail in color["colorDetails"] if detail["type"] == "normal"
            ]

        updated_branding = {
            "appearanceLoginBox": public_branding_dict["appearanceLoginBox"],
            "colorizeHeader": public_branding_dict["colorizeHeader"],
            "colors": public_branding_dict['colors'],
            "emailContact": public_branding_dict["emailContact"],
            "images": image_reqs,
            "imprintUrl": public_branding_dict["imprintUrl"],
            "positionLoginBox": public_branding_dict["positionLoginBox"],
            "privacyUrl": public_branding_dict["privacyUrl"],
            "productName": public_branding_dict["productName"],
            "supportUrl": public_branding_dict["supportUrl"],
            "texts": public_branding_dict["texts"],
        }

        return UpdateBrandingRequest(**updated_branding)


async def spray_branding(source_url: str, target_dracoon: DRACOON, on_prem_source: bool = False):
    """ spray a public branding to a target DRACOON """
    source_dracoon = init_public_dracoon(url=source_url, on_prem_source=on_prem_source)
    try:
        # fetch public source branding / images
        branding = await get_branding(dracoon=source_dracoon)
        image_downloads = await download_images(dracoon=source_dracoon)

        # upload images
        image_reqs = await upload_images(images=image_downloads, dracoon=target_dracoon)

        # update branding
        branding_dict = branding.dict()
        branding_payload = make_branding_payload(public_branding_dict=branding_dict, image_reqs=image_reqs)

        # send request to update branding
        result = await update_branding(
            branding_upload=branding_payload, dracoon=target_dracoon
        )

    except DRACOONHttpError:
        error_txt = typer.style("Error:", bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f"{error_txt}Could not update branding.")
        sys.exit(1)

    finally:
        delete_images(images=image_downloads)
        await source_dracoon.client.disconnect()

    success_txt = typer.style("SUCCESS:", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"{success_txt} Sprayed branding from {source_url} to target {target_dracoon.client.base_url}")



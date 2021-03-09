from dracoonsprayer.util.branding import get_branding, delete_images, update_branding, upload_images, download_images, zip_branding, load_from_zip
from dracoonsprayer.util.dracoon_auth import password_flow, auth_code_flow
from dracoon import core
import typer

app = typer.Typer()

# CLI to copy branding from source to target url
@app.command()
def spray(source_url: str = typer.Argument(..., help='Source DRACOON instance to copy branding from.'), 
       target_url: str = typer.Argument(..., help='Target DRACOON instance to upload branding to.'), 
       client_id: str = typer.Option('dracoon_legacy_scripting', 
                            help='Optional client id of an OAuth app registered in target DRACOON instance.'),
       client_secret: str = typer.Option(None, 
                            help='Optional client secret of an OAuth app registered in target DRACOON instance.'),
       auth_code: bool = typer.Option(False, 
                            help='Optional authorization code flow for given client id and secret.'),
       full_branding: bool = typer.Option(False, 
                            help='Optional full branding (including texts).'), 
       on_prem_source: bool = typer.Option(False, 
                  help='Source branding is a on premises DRACOON installation using DRACOON Cloud branding.')):
    """
    Spray a source DRACOON branding to a target DRACOON instance.
    Requires DRACOON config manager role for target. 
    """

    # GET public branding information
    branding_json = get_branding(source_url, on_prem_source)
    target_branding_json = get_branding(target_url, False)

    # handle invalid source branding
    if branding_json is not None:
        
        # use password flow if not client secret provided
        if client_secret == None: 
            auth_code = False
            typer.echo('No client secret provided.')
            typer.echo(' Using password flow ...')
        
        # use password flow as default
        if not auth_code:
            username = typer.prompt('Please enter username')
            password = typer.prompt('Please enter password', hide_input=True)
            auth_header = password_flow(client_id=client_id, 
            client_secret=client_secret, username=username, password=password, target_url=target_url)
        # use auth code flow 
        else: 
            my_dracoon = core.Dracoon(clientID=client_id, clientSecret=client_secret)
            my_dracoon.set_URLs(target_url)
            typer.launch(my_dracoon.get_code_url())
            auth_code = typer.prompt('Paste authorization code')
            auth_header = auth_code_flow(client_id=client_id, 
                                    client_secret=client_secret, target_url=target_url, code=auth_code)



        # download images from source branding
        download_images(branding_json)

        # upload images to target
        image_ids = upload_images(target_url, auth_header)

        parsed_colors = []
        
        # parse colors (only normal color required)
        for color in branding_json['colors']:
            for details in color['colorDetails']:
                if details['type'] == 'normal':
                    parsed_colors.append({
                        'type': color['type'],
                        'colorDetails': [details]
                    })

        if full_branding:
            # create payload to update branding based on source and downloaded images
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
        else:
            # create payload only replacing styles
            updated_branding  = {
            'appearanceLoginBox': branding_json['appearanceLoginBox'],
            'colorizeHeader': branding_json['colorizeHeader'],
            'colors': parsed_colors,
            'emailContact': target_branding_json['emailContact'],
            'emailSender': target_branding_json['emailSender'],
            'images': image_ids,
            'imprintUrl': target_branding_json['imprintUrl'],
            'positionLoginBox': branding_json['positionLoginBox'],
            'privacyUrl': target_branding_json['privacyUrl'],
            'productName': target_branding_json['productName'],
            'supportUrl': target_branding_json['supportUrl'],
            'texts': target_branding_json['texts']
        }

        # send request to update branding
        result = update_branding(target_url, updated_branding, auth_header)
        delete_images()
        if result is not None:
            success_txt = typer.style('SUCCESS: ', fg=typer.colors.GREEN, bold=True)
            typer.echo(f'{success_txt} Sprayed source branding from {source_url} to {target_url}.')
        # handle errors on failed update
        else:
            error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
            typer.echo(f'{error_txt} Branding could not be sprayed to target.')

   # handle errors getting branding     
    else: 
        typer.echo(f'An error ocurred getting the branding.')

@app.command()
def save(source_url: str = typer.Argument(..., help='Source DRACOON instance to get branding from.'), 
         zip_name: str = typer.Argument('branding.zip', help='Optional zip file name and path.'), 
         on_prem_source: bool = typer.Option(False, 
                  help='Source branding is a on premises DRACOON installation using DRACOON Cloud branding.')):
    """
    Downloads a DRACOON branding as a zip file containing all required images and JSON payload.
    """
    zip_branding(source_url, zip_name, on_prem_source)

@app.command()
def load(zip_file: str = typer.Argument(..., help='Zip file with DRACOON branding to upload.'), 
       target_url: str = typer.Argument(..., help='Target DRACOON instance to upload branding to.'), 
       client_id: str = typer.Option('dracoon_legacy_scripting', 
                            help='Optional client id of an OAuth app registered in target DRACOON instance.'),
       client_secret: str = typer.Option(None, 
                            help='Optional client secret of an OAuth app registered in target DRACOON instance.'),
       auth_code: bool = typer.Option(False, 
                            help='Optional authorization code flow for given client id and secret.')):
    """
    Uploads a DRACOON branding from a zip file to a target DRACOON instance.
    """
    # use password flow if not client secret provided
    if client_secret == None: 
        auth_code = False
        typer.echo('No client secret provided.')
        typer.echo(' Using password flow ...')
        
    # use password flow as default
    if not auth_code:
        username = typer.prompt('Please enter username')
        password = typer.prompt('Please enter password', hide_input=True)
        auth_header = password_flow(client_id=client_id, 
            client_secret=client_secret, username=username, password=password, target_url=target_url)
    # use auth code flow 
    else: 
        my_dracoon = core.Dracoon(clientID=client_id, clientSecret=client_secret)
        my_dracoon.set_URLs(target_url)
        typer.launch(my_dracoon.get_code_url())
        auth_code = typer.prompt('Paste authorization code')
        auth_header = auth_code_flow(client_id=client_id, 
                                    client_secret=client_secret, target_url=target_url, code=auth_code)

    load_from_zip(zip_file, target_url, auth_header)

# run main function
if __name__ == '__main__':
    app()
    






from util import branding
from util import dracoon_auth
from dracoon import core
import typer

# CLI to copy branding from source to target url
def sprayer(source_url: str, target_url: str, 
    client_id = 'dracoon_legacy_scripting', client_secret = None, auth_code_flow: bool = False, 
    full_branding = False):

    # GET public branding information
    branding_json = branding.get_branding(source_url)
    target_branding_json = branding.get_branding(target_url)

    if client_secret == None: 
        auth_code_flow = False
        typer.echo('No client secret provided.')
        typer.echo(' Using password flow ...')

    if not auth_code_flow:
        username = typer.prompt('Please enter username')
        password = typer.prompt('Please enter password', hide_input=True)
        auth_header = dracoon_auth.password_flow(client_id=client_id, 
        client_secret=client_secret, username=username, password=password, target_url=target_url)
    else: 
        my_dracoon = core.Dracoon(clientID=client_id, clientSecret=client_secret)
        my_dracoon.set_URLs(target_url)
        typer.echo(f'Please open URL: {my_dracoon.get_code_url()}')
        auth_code = typer.prompt('Paste authorization code')
        auth_header = dracoon_auth.auth_code_flow(client_id=client_id, 
                                 client_secret=client_secret, target_url=target_url, code=auth_code)

    if branding_json is not None:
        # download images from source branding
        branding.download_images(branding_json)

        # upload images to target
        image_ids = branding.upload_images(target_url, auth_header)

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
        result = branding.update_branding(target_url, updated_branding, auth_header)
        branding.delete_images()
        success_txt = typer.style('SUCCESS: ', fg=typer.colors.GREEN, bold=True)
        typer.echo(f'{success_txt} Sprayed source branding from {source_url} to {target_url}.')
        
    
    else: 
        typer.echo(f'An error ocurred getting the branding.')

# run main function
if __name__ == '__main__':
    typer.run(sprayer)
    






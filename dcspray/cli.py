import asyncio
import typer

from dcspray.util.branding import (
    get_branding,
    delete_images,
    update_branding,
    upload_images,
    download_images,
    zip_branding,
    load_from_zip,
    spray_branding
)
from dcspray.util.auth import password_flow, auth_code_flow, add_https_protocol, verify_dracoon_url


app = typer.Typer()

# CLI to copy branding from source to target url
@app.command()
def spray(
    source_url: str = typer.Argument(
        ..., help="Source DRACOON instance to copy branding from."
    ),
    target_url: str = typer.Argument(
        ..., help="Target DRACOON instance to upload branding to."
    ),
    client_id: str = typer.Option(
        "dracoon_legacy_scripting",
        help="Optional client id of an OAuth app registered in target DRACOON instance.",
    ),
    client_secret: str = typer.Option(
        None,
        help="Optional client secret of an OAuth app registered in target DRACOON instance.",
    ),
    auth_code: bool = typer.Option(
        False, help="Optional authorization code flow for given client id and secret."
    ),
    full_branding: bool = typer.Option(
        False, help="Optional full branding (including texts)."
    ),
    on_prem_source: bool = typer.Option(
        False,
        help="Source branding is a on premises DRACOON installation using DRACOON Cloud branding.",
    ),
):
    """
    Spray a source DRACOON branding to a target DRACOON instance.
    Requires DRACOON config manager role for target.
    """

    async def _spray(auth_code: bool = False):
        # use password flow if not client secret provided

        parsed_source_url = add_https_protocol(url=source_url)
        await verify_dracoon_url(url=parsed_source_url)

        parsed_target_url = add_https_protocol(url=target_url)
        await verify_dracoon_url(url=parsed_target_url)

        if client_secret == None:
            auth_code = False
            typer.echo("No client secret provided.")
            typer.echo(" Using password flow.")

        # use password flow as default
        if not auth_code:
            dracoon = await password_flow(
                client_id=client_id, client_secret=client_secret, target_url=parsed_target_url
            )
        else:
            dracoon = await auth_code_flow(
                client_id=client_id, client_secret=client_secret, target_url=parsed_target_url
            )
        
        await spray_branding(source_url=parsed_source_url, target_dracoon=dracoon)

    asyncio.run(_spray())


@app.command()
def save(
    source_url: str = typer.Argument(
        ..., help="Source DRACOON instance to get branding from."
    ),
    zip_name: str = typer.Argument(
        "branding.zip", help="Optional zip file name and path."
    ),
    on_prem_source: bool = typer.Option(
        False,
        help="Source branding is a on premises DRACOON installation using DRACOON Cloud branding.",
    ),
):
    """
    Downloads a DRACOON branding as a zip file containing all required images and JSON payload.
    """

    async def _save():
        parsed_source_url = add_https_protocol(url=source_url)
        await verify_dracoon_url(url=parsed_source_url)
        await zip_branding(parsed_source_url, zip_name, on_prem_source)

    asyncio.run(_save())


@app.command()
def load(
    zip_file: str = typer.Argument(
        ..., help="Zip file with DRACOON branding to upload."
    ),
    target_url: str = typer.Argument(
        ..., help="Target DRACOON instance to upload branding to."
    ),
    client_id: str = typer.Option(
        "dracoon_legacy_scripting",
        help="Optional client id of an OAuth app registered in target DRACOON instance.",
    ),
    client_secret: str = typer.Option(
        None,
        help="Optional client secret of an OAuth app registered in target DRACOON instance.",
    ),
    auth_code: bool = typer.Option(
        False, help="Optional authorization code flow for given client id and secret."
    ),
):
    """
    Uploads a DRACOON branding from a zip file to a target DRACOON instance.
    """

    async def _load(auth_code: bool = False):

        parsed_target_url = add_https_protocol(url=target_url)
        await verify_dracoon_url(url=parsed_target_url)

        # use password flow if not client secret provided
        if client_secret == None:
            auth_code = False
            typer.echo("No client secret provided.")
            typer.echo(" Using password flow.")

        # use password flow as default
        if not auth_code:
            dracoon = await password_flow(
                client_id=client_id, client_secret=client_secret, target_url=parsed_target_url
            )
        else:
            dracoon = await auth_code_flow(
                client_id=client_id, client_secret=client_secret, target_url=parsed_target_url
            )

        await load_from_zip(dracoon=dracoon, zip_file=zip_file)

    asyncio.run(_load(auth_code=auth_code))


# run main function
if __name__ == "__main__":
    app()

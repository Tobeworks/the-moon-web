#!/usr/bin/env python3
"""
The Moon Records CLI
The operating layer for the world's first 100% code-based music label.

Usage:
  ./tools/tmr generate <release-folder-path>               — scan audio, write release.json
  ./tools/tmr validate <release-folder-path>               — validate against schema
  ./tools/tmr validate <release-folder-path> --generate-md — validate + write release.md draft
  ./tools/tmr convert  <release-folder-path>               — WAV/AIFF → MP3 320k + ID3 tags + cover
  ./tools/tmr convert  <release-folder-path> --force       — overwrite existing MP3s
  ./tools/tmr social   <release-folder-path>               — render social media assets
  ./tools/tmr social   <release-folder-path> --format reel — square | reel | carousel | all
  ./tools/tmr push     <release-folder-path>               — CDN upload + data/releases.json
  ./tools/tmr studio                                       — local browser UI for all of the above
"""

import click
from commands.validate import validate_release
from commands.generate import generate_release
from commands.social   import generate_social
from commands.convert  import convert_release
from commands.push     import push_release, test_connection

@click.group()
@click.version_option(version="0.1.0", prog_name="the-moon")
def cli():
    """The Moon Records OS — label toolchain."""
    pass

@cli.command()
@click.argument('release_path', type=click.Path(exists=True))
def generate(release_path):
    """Scan audio folder and generate release.json skeleton."""
    generate_release(release_path)

@cli.command()
@click.argument('release_path', type=click.Path(exists=True))
@click.option('--generate-md', is_flag=True, default=False,
              help='Generate release.md draft if validation passes.')
def validate(release_path, generate_md):
    """Validate a release asset folder against the The Moon Records schema."""
    validate_release(release_path, generate_md=generate_md)

@cli.command()
@click.argument('release_path', type=click.Path(exists=True))
@click.option('--format', 'output_format', default='square',
              type=click.Choice(['square', 'reel', 'all']),
              help='Output format. Default: square.')
@click.option('--duration', default=30, show_default=True,
              help='Clip length in seconds.')
@click.option('--init', is_flag=True, default=False,
              help='Write social.json config skeleton and exit.')
def social(release_path, output_format, duration, init):
    """Render social media assets for a release. Use --init to configure first."""
    generate_social(release_path, fmt=output_format,
                    duration=duration, init=init)

@cli.command()
@click.argument('release_path', type=click.Path(exists=True))
@click.option('--force', is_flag=True, default=False,
              help='Overwrite existing MP3s.')
def convert(release_path, force):
    """Convert WAV/AIFF to MP3 320kbps with full ID3 tags and embedded cover."""
    convert_release(release_path, force=force)

@cli.command()
@click.argument('release_path', type=click.Path(exists=True))
def push(release_path):
    """Upload release assets to CDN and update data/releases.json."""
    push_release(release_path)

@cli.command('sftp-test')
def sftp_test():
    """Test SFTP connection and write permissions — no upload."""
    test_connection()

@cli.command()
@click.option('--port', default=8777, show_default=True,
              help='Local port (next free one if taken). 8765 belongs to Release Studio.')
@click.option('--no-open', is_flag=True, default=False, help="Don't open the browser.")
def studio(port, no_open):
    """Start the local browser UI (127.0.0.1 only)."""
    import secrets
    import webbrowser

    import uvicorn
    from studio.config import free_port, load_config
    from studio.frontend_build import build, needs_build
    from studio.server import create_app

    if needs_build():
        click.echo("Baue die Oberfläche (einmalig, dauert kurz) …")
        try:
            build()
        except RuntimeError as e:
            raise click.ClickException(str(e))

    port = free_port(port)
    token = secrets.token_urlsafe(16)
    url = f"http://127.0.0.1:{port}/?key={token}"
    click.echo(f"tmr studio → {url}\n(Ctrl+C to stop)")
    if not no_open:
        webbrowser.open(url)
    uvicorn.run(create_app(load_config(), token), host="127.0.0.1", port=port, log_level="warning")


if __name__ == '__main__':
    cli()

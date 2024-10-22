import click
import asyncio
from tma_asset_generator import OpenAIClient, BatchProcessor

@click.group()
def main():
    """Asset Generator CLI."""
    pass

@main.command()
@click.option('--num-prompts', default=1, help='Number of prompts to generate.')
def run_batch(num_prompts):
    """
    Run a batch job to generate assets.

    :param num_prompts: Number of prompts to generate.
    """
    try:
        # Initialize OpenAIClient which loads the API key from .env
        client = OpenAIClient()
    except EnvironmentError as e:
        click.echo(f"Error: {e}")
        return

    processor = BatchProcessor(client)

    # Run the batch job asynchronously
    asyncio.run(processor.run_batch_job(num_prompts))
    click.echo(f"Batch job completed with {num_prompts} prompts.")

@main.command()
def test():
    """Run basic tests."""
    click.echo("Running tests...")

if __name__ == '__main__':
    main()

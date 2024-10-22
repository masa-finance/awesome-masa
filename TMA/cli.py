import click
import os
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
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        click.echo("Error: OPENAI_API_KEY environment variable not set.")
        return

    client = OpenAIClient(api_key=api_key)
    processor = BatchProcessor(client)

    asyncio.run(processor.run_batch_job(num_prompts))
    click.echo(f"Batch job completed with {num_prompts} prompts.")

@main.command()
def test():
    """Run basic tests."""
    click.echo("Running tests...")

if __name__ == '__main__':
    main()
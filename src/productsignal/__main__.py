"""One entry point for dataset generation, embeddings, experiments, and cards."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/milestone1.json')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ['generate', 'embed', 'run']:
        sub.add_parser(command)
    cards = sub.add_parser('cards')
    cards.add_argument('--run', required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    root = config['dataset_root']
    settings = config['clustering']
    seen = set()
    for setting in settings:
        if set(setting) != {'min_cluster_size', 'min_samples', 'metric', 'cluster_selection_method'}:
            parser.error('Each clustering setting must contain the four documented fields.')
        if setting['metric'] != 'euclidean' or setting['cluster_selection_method'] not in ['eom','leaf']:
            parser.error('Supported settings: euclidean distance with eom or leaf.')
        if not isinstance(setting['min_cluster_size'], int) or setting['min_cluster_size'] < 2:
            parser.error('min_cluster_size must be an integer >= 2.')
        if not isinstance(setting['min_samples'], int) or setting['min_samples'] < 1:
            parser.error('min_samples must be an integer >= 1.')
        key = (setting['min_cluster_size'],setting['min_samples'],setting['cluster_selection_method'])
        if key in seen:
            parser.error('Duplicate clustering settings would overwrite a run directory.')
        seen.add(key)
    if not settings:
        parser.error('At least one clustering setting is required.')
    if args.command == 'generate':
        from .dataset import main as generate
        generate(root)
    elif args.command == 'embed':
        from .embeddings import main as embed
        embed(root, config['embedding_model'], config['ollama_host'], config['batch_size'])
    elif args.command == 'run':
        from .experiment import main as run
        run(root, settings, config['output_root'])
    else:
        from .cards import main as build_cards
        build_cards(args.run)


if __name__ == '__main__':
    main()

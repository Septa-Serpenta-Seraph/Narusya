#!/usr/bin/env python3
"""
Toggle between free (fastembed 384-dim, Nous) and paid (3072-dim, OpenRouter) embedding configs.

Usage:
  python3 toggle_embeddings.py --free     # switch to free Nous fastembed
  python3 toggle_embeddings.py --paid     # switch to paid OpenRouter
  python3 toggle_embeddings.py --status   # show current config
"""
import argparse, yaml, subprocess, sys, os, time

CONFIG = os.path.expanduser('~/.hermes/config.yaml')

FREE = {
    'collection': 'intelligent_gould_narusya_fe',
    'lorebook_collection': 'narusya_lorebooks_fe',
    'description': 'free Nous fastembed (384-dim)'
}
PAID = {
    'collection': 'intelligent_gould_narusya',
    'lorebook_collection': 'narusya_lorebooks',
    'description': 'paid OpenRouter (3072-dim)'
}

def read():
    with open(CONFIG) as f:
        return yaml.safe_load(f)

def write(cfg):
    with open(CONFIG, 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)

def status(cfg):
    p = cfg.get('plugins', {}).get('qdrant-memory', {})
    cur_col = p.get('collection', '(not set)')
    cur_lb = p.get('lorebook_collection', '(not set)')
    if cur_col == FREE['collection']:
        mode = 'FREE (fastembed 384-dim, Nous)'
    elif cur_col == PAID['collection']:
        mode = 'PAID (3072-dim, OpenRouter)'
    else:
        mode = f'CUSTOM ({cur_col})'
    return f"Current mode: {mode}\n  memory collection: {cur_col}\n  lorebook collection: {cur_lb}"

def switch(target):
    cfg = read()
    if 'plugins' not in cfg:
        cfg['plugins'] = {}
    if 'qdrant-memory' not in cfg['plugins']:
        cfg['plugins']['qdrant-memory'] = {}
    cfg['plugins']['qdrant-memory']['collection'] = target['collection']
    cfg['plugins']['qdrant-memory']['lorebook_collection'] = target['lorebook_collection']
    write(cfg)
    print(f"✓ Switched to: {target['description']}")
    print(f"  memory collection: {target['collection']}")
    print(f"  lorebook collection: {target['lorebook_collection']}")
    # Restart gateway
    print("  Restarting gateway...")
    subprocess.run(['/home/adora/.hermes/hermes-agent/venv/bin/python', '-m',
                    'hermes_cli.main', 'gateway', 'restart'], capture_output=True)
    time.sleep(3)
    print("  Done. Gateway restarted.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--free', action='store_true')
    group.add_argument('--paid', action='store_true')
    group.add_argument('--status', action='store_true')
    args = parser.parse_args()
    cfg = read()
    if args.status:
        print(status(cfg))
    elif args.free:
        switch(FREE)
    elif args.paid:
        switch(PAID)

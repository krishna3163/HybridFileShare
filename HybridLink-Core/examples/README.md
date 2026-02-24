# Examples for HybridLink-Core

This directory contains example implementations demonstrating how to use HybridLink-Core.

## Available Examples

1. **example_sender.py** - Send a file over multipath channels
2. **example_receiver.py** - Receive a file over multipath channels
3. **example_resumable_transfer.py** - Implement checkpoint and resume functionality

## Running Examples

```bash
# Ensure dependencies are installed
pip install -e ..

# Run sender example
python example_sender.py

# Run receiver example
python example_receiver.py

# Run resumable transfer example
python example_resumable_transfer.py

# Resume a transfer
python example_resumable_transfer.py resume
```

## Custom Examples

You can create your own examples by importing from hybridlink_core:

```python
from hybridlink_core import TransferController, TransferConfig
from pathlib import Path

# Your code here
```

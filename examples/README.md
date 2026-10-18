# Examples

This directory contains example usage patterns for edgeproc-core.

## Basic Usage

[`basic_usage.py`](basic_usage.py) - Simple example with `GlobalPartitionStrategy`:
- Creating an IndexManager
- Inserting embeddings
- Searching
- Getting statistics

## Custom Partition Keys

[`custom_partition_key.py`](custom_partition_key.py) - Using `user_id` instead of `tenant_id`:
- Configuring partition key name
- Storing partition keys in metadata
- Searching by custom partition key

## Composite Partition Keys

[`composite_partition_key.py`](composite_partition_key.py) - Using composite keys (org_id + region):
- Custom partition key extractor
- Combining multiple metadata fields
- Partitioning by composite key

## Running Examples

```bash
# From the repository root:
uv sync
uv run python examples/basic_usage.py

# Or run all examples at once:
bash examples/run_loop.sh
```

## Note

These examples use the bundled `in_memory_factory` reference index. In production, you'll need to:

1. Implement the `VectorIndex` protocol for your vector database
2. Replace `in_memory_factory` with your actual index factory
3. Handle database connections and configuration

See the main [README.md](../README.md) for more details.



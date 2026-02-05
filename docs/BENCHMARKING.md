# GenXAI Benchmarking Guide

This guide describes how to benchmark GenXAI workflows, agents, and tool calls.

## Goals

- Measure **latency** (P50, P95, P99)
- Measure **throughput** (workflows/sec)
- Track **token usage** and response sizes
- Identify **bottlenecks** in agent/tool execution

## Quick Start

Run the built-in benchmark script:

```bash
python scripts/benchmarks/run_benchmark.py \
  --workflows 50 \
  --parallel 10 \
  --model gpt-3.5-turbo
```

> Note: For local runs without API costs, use the Ollama provider with a local model.

## Benchmark Inputs

The benchmark script generates synthetic workflows that exercise:

- **Agent Runtime** (LLM calls + prompts)
- **Tool Execution** (50+ built-in tools including calculator, file reader, web scraper)
- **Graph Engine** (parallel + sequential branches)
- **Trigger System** (webhook, schedule, queue, file watcher)
- **Connector System** (webhook, Kafka, SQS, Postgres CDC)
- **Worker Queue Engine** (task distribution, retry logic)

You can adjust parameters with flags:

| Flag | Description | Default |
|------|-------------|---------|
| `--workflows` | Number of workflows to execute | 50 |
| `--parallel` | Concurrent workflows | 10 |
| `--model` | LLM model name | gpt-4 |
| `--provider` | Provider alias (openai/ollama) | openai |
| `--timeout` | Timeout per workflow (seconds) | 60 |

## Output

The benchmark prints:

- Total execution time
- Average latency per workflow
- P50/P95/P99 latency
- Success rate
- Token usage (if available)

Example output:

```
Benchmark Results
-----------------
Workflows: 50
Parallelism: 10
Success rate: 98%
Avg latency: 1.4s
P50: 1.2s, P95: 2.7s, P99: 3.1s
```

## Best Practices

- **Warm up** the provider before sampling.
- **Use fixed prompts** for repeatability.
- **Test with multiple models** for cost/perf comparison.
- **Record environment** (CPU, memory, network).

## Next Steps

- Integrate with CI for baseline regression checks.
- Store CI artifacts for encrypted connector configs when benchmarking connector-heavy workflows.
- Store results in a time-series DB (Prometheus/Grafana).
- Add workload-specific benchmarks (RAG, memory-heavy workflows).

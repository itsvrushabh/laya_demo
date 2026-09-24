#!/usr/bin/env python3
"""
Laya "System 1" Decision Engine - CLI Demo & Benchmarks
Demonstrating sub-40ms non-autoregressive calibrated classification, scoring, and boolean decisions.
"""

import sys
import time
import json
from typing import Dict, Any

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import print as rprint
except ImportError:
    print("Please install rich: pip install rich")
    sys.exit(1)

try:
    import torch
    from laya import Router
except ImportError as e:
    rprint(f"[bold red]Error importing laya/torch: {e}[/bold red]")
    rprint("[yellow]Please run: pip install -r requirements.txt[/yellow]")
    sys.exit(1)

console = Console()

SAMPLE_CASES = [
    {
        "title": "Customer Support - Duplicate Billing Issue",
        "state": {
            "subject": "Charged twice on Invoice #90214",
            "body": "Hi, I noticed two identical charges of $149 on my credit card this morning for my monthly plan. Please refund the duplicate transaction ASAP!",
            "sender_tier": "enterprise"
        },
        "questions": {
            "intent": {
                "type": "choice",
                "instructions": "What is the primary customer intent?",
                "options": ["billing_refund", "account_cancellation", "technical_support", "feature_request", "sales_inquiry"]
            },
            "is_urgent": {
                "type": "noul",
                "instructions": "Is this an urgent issue requiring rapid response?"
            },
            "risk_level": {
                "type": "score",
                "instructions": "What is the churn or escalation risk level?",
                "criteria": ["low", "moderate", "high", "critical"]
            }
        }
    },
    {
        "title": "Security & Content Moderation - Account Security Alert",
        "state": {
            "subject": "URGENT: Suspicious logins detected from unusual IP",
            "body": "We noticed multiple failed password attempts followed by a successful login from an unknown location. Need access revoked immediately!",
            "source": "automated_system_alert"
        },
        "questions": {
            "incident_category": {
                "type": "choice",
                "instructions": "What kind of security incident is this?",
                "options": ["account_takeover", "phishing", "data_leak", "spam", "false_positive"]
            },
            "requires_immediate_lockout": {
                "type": "noul",
                "instructions": "Should the affected user account be suspended immediately?"
            },
            "severity_score": {
                "type": "score",
                "instructions": "Rate the severity of the threat",
                "criteria": ["p4_minor", "p3_medium", "p2_major", "p1_critical"]
            }
        }
    },
    {
        "title": "Multilingual Routing - French Support Request",
        "state": {
            "subject": "Impossible de me connecter à mon compte",
            "body": "Bonjour, depuis la mise à jour hier soir, mon mot de passe n'est plus reconnu. Pouvez-vous réinitialiser mes accès s'il vous plaît?",
            "lang": "fr"
        },
        "questions": {
            "demande": {
                "type": "choice",
                "instructions": "Quelle est la nature du problème?",
                "options": ["reinitialisation_mdp", "probleme_facturation", "annulation", "question_commerciale"]
            },
            "bloquant": {
                "type": "noul",
                "instructions": "Est-ce un problème bloquant pour l'utilisateur?"
            }
        }
    }
]


def init_router() -> Router:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    console.print(Panel(
        f"[bold cyan]Laya Decision Engine Initializer[/bold cyan]\n"
        f"• Hardware Backend: [bold green]{device.upper()}[/bold green] "
        f"({'NVIDIA ' + torch.cuda.get_device_name(0) if device == 'cuda' else 'CPU Host'})\n"
        f"• Architecture: ModernBERT Non-Autoregressive Decision Head\n"
        f"• Preload: Active for Sub-40ms System 1 Latency",
        border_style="cyan"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Preloading Laya Router models...", total=None)
        start_t = time.perf_counter()
        router = Router(preload=True, device=device)
        elapsed_init = (time.perf_counter() - start_t) * 1000.0

    console.print(f"[dim green]✓ Router preloaded in {elapsed_init:.1f}ms[/dim green]\n")
    return router


def format_answer_value(answer: Dict[str, Any]) -> str:
    if "choice" in answer:
        choice_val = answer["choice"]
        conf = answer.get("confidence")
        if conf is not None:
            return f"[bold magenta]{choice_val}[/bold magenta] [dim]({conf * 100:.1f}% confidence)[/dim]"
        return f"[bold magenta]{choice_val}[/bold magenta]"
    
    if "value" in answer:
        val = answer["value"]
        color = "green" if val else "red"
        conf = answer.get("confidence")
        conf_str = f" [dim]({conf * 100:.1f}%)[/dim]" if conf is not None else ""
        return f"[{color}]{val}[/{color}]{conf_str}"
        
    if "score" in answer:
        score_val = answer["score"]
        level = answer.get("level", "")
        return f"[bold yellow]{score_val}[/bold yellow] [dim]({level})[/dim]"

    return str(answer)


def run_sample_demo(router: Router):
    console.print(Panel("[bold yellow]1. Running Preset Enterprise Use Cases[/bold yellow]", border_style="yellow"))

    for i, case in enumerate(SAMPLE_CASES, start=1):
        console.rule(f"[bold cyan]Scenario {i}: {case['title']}[/bold cyan]")
        
        # Display Input State
        state_str = "\n".join(f"  • [bold]{k}[/bold]: {v}" for k, v in case["state"].items())
        console.print(f"[dim]Input State:[/dim]\n{state_str}\n")
        
        # Measure Inference Time
        start_time = time.perf_counter()
        prediction = router.predict(case["state"], case["questions"])
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Results Table
        table = Table(title=f"Decisions (Latency: {latency_ms:.2f} ms)", border_style="blue", show_header=True)
        table.add_column("Question Key", style="cyan", width=22)
        table.add_column("Decision Type", style="dim", width=14)
        table.add_column("Output / Calibrated Decision", style="white")

        answers = prediction.get("answers", {})
        routing_info = prediction.get("routing", {})

        for q_key, q_config in case["questions"].items():
            ans = answers.get(q_key, {})
            table.add_row(q_key, q_config.get("type", "unknown"), format_answer_value(ans))

        console.print(table)
        
        # Routing Metadata
        model_used = routing_info.get("model", "default")
        reason = routing_info.get("reason", "automatic script/language detection")
        console.print(f"[dim]Routing Dispatch: [cyan]{model_used}[/cyan] ({reason}) | System 1 Speed: [green]{latency_ms:.1f}ms[/green][/dim]\n")


def run_latency_benchmark(router: Router, iterations: int = 15):
    console.print(Panel(f"[bold yellow]2. Speed Benchmark ({iterations} Consecutive Inferences)[/bold yellow]", border_style="yellow"))
    
    test_state = {
        "text": "My order #88439 hasn't arrived yet and the tracking link is broken. Can someone check where it is?"
    }
    test_questions = {
        "intent": {
            "type": "choice",
            "options": ["order_status", "refund_request", "product_defect", "account_settings"]
        },
        "urgent": {
            "type": "noul",
            "instructions": "Is this inquiry urgent?"
        }
    }

    latencies = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Executing Laya decision forward passes...", total=iterations)
        for _ in range(iterations):
            t0 = time.perf_counter()
            _ = router.predict(test_state, test_questions)
            latencies.append((time.perf_counter() - t0) * 1000.0)
            progress.advance(task)

    min_lat = min(latencies)
    max_lat = max(latencies)
    avg_lat = sum(latencies) / len(latencies)
    p95_lat = sorted(latencies)[int(0.95 * len(latencies))]

    bench_table = Table(title="Laya Non-Autoregressive Performance", border_style="green")
    bench_table.add_column("Metric", style="bold cyan")
    bench_table.add_column("Laya Decision Engine", style="bold green")
    bench_table.add_column("Typical LLM (Token Generation)", style="dim red")

    bench_table.add_row("Average Latency", f"{avg_lat:.2f} ms", "~1,200 - 2,500 ms (20-50x slower)")
    bench_table.add_row("Fastest Run (Min)", f"{min_lat:.2f} ms", "~800 ms TTFT")
    bench_table.add_row("P95 Latency", f"{p95_lat:.2f} ms", "~3,000 ms")
    bench_table.add_row("Hallucination Risk", "0% (Deterministic Classification Head)", "Non-zero (Requires JSON schema repair)")
    bench_table.add_row("Calibration", "Calibrated confidence probabilities", "Uncalibrated logits / approximations")

    console.print(bench_table)
    console.print()


def interactive_mode(router: Router):
    console.print(Panel(
        "[bold yellow]3. Interactive Playground[/bold yellow]\n"
        "Type any email, message, or user query to see live Laya decisions.\n"
        "Type [bold red]'exit'[/bold red] to quit.",
        border_style="yellow"
    ))

    questions = {
        "category": {
            "type": "choice",
            "instructions": "Select the primary category",
            "options": ["support", "billing", "sales", "feedback", "spam"]
        },
        "escalation_needed": {
            "type": "noul",
            "instructions": "Does this require human manager escalation?"
        },
        "sentiment": {
            "type": "score",
            "instructions": "User sentiment",
            "criteria": ["angry", "neutral", "happy"]
        }
    }

    while True:
        try:
            user_input = console.input("\n[bold cyan]Enter message > [/bold cyan]").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[dim]Exiting interactive mode...[/dim]")
                break

            t0 = time.perf_counter()
            res = router.predict({"text": user_input}, questions)
            elapsed = (time.perf_counter() - t0) * 1000.0

            answers = res.get("answers", {})
            routing = res.get("routing", {})

            console.print(f"[dim green]⏱ Decision in {elapsed:.1f}ms via model '{routing.get('model', 'default')}'[/dim green]")
            for q_key in questions:
                ans = answers.get(q_key, {})
                console.print(f" • [bold]{q_key}[/bold]: {format_answer_value(ans)}")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Quitting...[/dim]")
            break


def main():
    router = init_router()
    run_sample_demo(router)
    run_latency_benchmark(router)
    
    if sys.stdin.isatty():
        interactive_mode(router)
    else:
        console.print("[dim]Non-interactive terminal detected. Skipping live prompt.[/dim]")


if __name__ == "__main__":
    main()

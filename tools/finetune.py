"""Fine-tune a small language model on COBOL explanation data using LoRA.

Uses HuggingFace transformers + PEFT for parameter-efficient fine-tuning.
Designed for CodeLlama-7B or similar code-capable models.

Requirements (not in main project deps — install separately):
    pip install torch transformers peft datasets accelerate bitsandbytes

Usage:
    python tools/finetune.py \
        --dataset dataset/cobol_instruct_alpaca.jsonl \
        --base-model codellama/CodeLlama-7b-Instruct-hf \
        --output models/cobol-explain-7b \
        --epochs 3

    # Resume from checkpoint:
    python tools/finetune.py \
        --dataset dataset/cobol_instruct_alpaca.jsonl \
        --base-model codellama/CodeLlama-7b-Instruct-hf \
        --output models/cobol-explain-7b \
        --resume-from models/cobol-explain-7b/checkpoint-100
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_alpaca_dataset(path: Path) -> list[dict]:
    """Load JSONL dataset in Alpaca instruction format."""
    samples = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return samples


def format_prompt(sample: dict) -> str:
    """Format a training sample into a single prompt string.

    Uses the Alpaca prompt template compatible with most instruction-tuned models.
    """
    instruction = sample["instruction"]
    input_text = sample.get("input", "")
    output_text = sample.get("output", "")

    if input_text:
        prompt = (
            f"### Instruction:\n{instruction}\n\n"
            f"### Input:\n{input_text}\n\n"
            f"### Response:\n{output_text}"
        )
    else:
        prompt = (
            f"### Instruction:\n{instruction}\n\n"
            f"### Response:\n{output_text}"
        )
    return prompt


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Fine-tune a model on COBOL explanation data using LoRA",
    )
    ap.add_argument(
        "--dataset", required=True,
        help="Path to Alpaca JSONL dataset",
    )
    ap.add_argument(
        "--base-model", default="codellama/CodeLlama-7b-Instruct-hf",
        help="HuggingFace model ID or local path",
    )
    ap.add_argument(
        "--output", default="models/cobol-explain-7b",
        help="Output directory for fine-tuned model",
    )
    ap.add_argument("--epochs", type=int, default=3, help="Training epochs")
    ap.add_argument("--batch-size", type=int, default=4, help="Per-device batch size")
    ap.add_argument(
        "--gradient-accumulation", type=int, default=4,
        help="Gradient accumulation steps",
    )
    ap.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    ap.add_argument("--lora-r", type=int, default=16, help="LoRA rank")
    ap.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha")
    ap.add_argument("--lora-dropout", type=float, default=0.05, help="LoRA dropout")
    ap.add_argument("--max-length", type=int, default=2048, help="Max sequence length")
    ap.add_argument(
        "--quantize", action="store_true",
        help="Use 4-bit quantization (QLoRA) to reduce VRAM",
    )
    ap.add_argument(
        "--resume-from", default=None,
        help="Resume training from checkpoint path",
    )
    ap.add_argument(
        "--eval-split", type=float, default=0.1,
        help="Fraction of data to hold out for evaluation",
    )
    args = ap.parse_args()

    # Late imports — these are heavy dependencies
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )
    except ImportError as e:
        print(
            f"Missing dependency: {e}\n\n"
            "Install fine-tuning dependencies:\n"
            '  pip install "cobol-intel[train]"'
        )
        raise SystemExit(1)

    # 1. Load dataset
    dataset_path = Path(args.dataset)
    print(f"Loading dataset from {dataset_path}...")
    raw_samples = load_alpaca_dataset(dataset_path)
    print(f"  {len(raw_samples)} samples loaded")

    # Format prompts
    texts = [format_prompt(s) for s in raw_samples]
    dataset = Dataset.from_dict({"text": texts})

    # Train/eval split
    if args.eval_split > 0 and len(dataset) > 10:
        split = dataset.train_test_split(test_size=args.eval_split, seed=42)
        train_dataset = split["train"]
        eval_dataset = split["test"]
        print(f"  Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")
    else:
        train_dataset = dataset
        eval_dataset = None
        print(f"  Train: {len(train_dataset)} (no eval split)")

    # 2. Load tokenizer
    print(f"Loading tokenizer: {args.base_model}...")
    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model, trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 3. Tokenize
    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=args.max_length,
            padding="max_length",
        )

    train_dataset = train_dataset.map(tokenize, batched=True, remove_columns=["text"])
    if eval_dataset:
        eval_dataset = eval_dataset.map(tokenize, batched=True, remove_columns=["text"])

    # 4. Load model
    print(f"Loading model: {args.base_model}...")
    model_kwargs = {"trust_remote_code": True}

    if args.quantize:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        model_kwargs["quantization_config"] = bnb_config
        model_kwargs["device_map"] = "auto"
        print("  Using 4-bit quantization (QLoRA)")
    else:
        model_kwargs["torch_dtype"] = torch.bfloat16
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(args.base_model, **model_kwargs)
    model.config.use_cache = False  # Required for gradient checkpointing

    # 5. Apply LoRA
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    trainable, total = model.get_nb_trainable_parameters()
    print(
        f"  LoRA applied: {trainable:,} trainable / {total:,} total "
        f"({trainable / total * 100:.1f}%)"
    )

    # 6. Training arguments
    output_dir = Path(args.output)
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        learning_rate=args.lr,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch" if eval_dataset else "no",
        save_total_limit=3,
        bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        fp16=torch.cuda.is_available() and not torch.cuda.is_bf16_supported(),
        gradient_checkpointing=True,
        report_to="none",
        remove_unused_columns=False,
    )

    # 7. Train
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, mlm=False,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    print(f"\nStarting training for {args.epochs} epoch(s)...")
    if args.resume_from:
        print(f"  Resuming from {args.resume_from}")
        trainer.train(resume_from_checkpoint=args.resume_from)
    else:
        trainer.train()

    # 8. Save
    print(f"\nSaving model to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Save training config for reproducibility
    config = {
        "base_model": args.base_model,
        "dataset": str(dataset_path),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "gradient_accumulation": args.gradient_accumulation,
        "lr": args.lr,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "lora_dropout": args.lora_dropout,
        "max_length": args.max_length,
        "quantize": args.quantize,
        "train_samples": len(train_dataset),
        "eval_samples": len(eval_dataset) if eval_dataset else 0,
    }
    config_path = output_dir / "training_config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"Training config: {config_path}")
    print("Done.")


if __name__ == "__main__":
    main()

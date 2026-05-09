import os
import re

TAG_RULES = {
    "AI Safety": ["ai safety", "safe ai", "safety", "risk"],
    "Alignment": ["alignment", "value alignment", "reward hacking", "reward misspecif", "rlhf", "constitutional ai", "scalable oversight", "corrigib"],
    "LLM Safety": ["llm safety", "large language model safety", "jailbreak", "red team", "prompt injection", "hallucin", "toxic"],
    "Interpretability": ["interpretab", "mechanistic", "explain", "xai", "feature attribution", "probing", "circuit"],
    "Robotic Safety": ["robot safety", "robotic safety", "autonomous vehicle", "safe rl", "safe reinforcement", "collision avoidance", "human-robot"],
    "Adversarial Robustness": ["adversarial", "robustness", "distribution shift", "out-of-distribution", "ood"],
    "Governance & Policy": ["governance", "policy", "regulation", "audit", "standard", "ethics"],
}


def tag_paper(paper: dict) -> dict:
    combined = f"{paper.get('title', '')} {paper.get('abstract', '')} {paper.get('categories', '')}"
    text = combined.lower()
    tags = [tag for tag, kws in TAG_RULES.items() if any(kw in text for kw in kws)]
    if not tags:
        tags = ["General AI Research"]
    paper["tags"] = ", ".join(tags)
    paper["summary"] = _summarize(paper.get("abstract", ""))
    return paper


def _summarize(abstract: str) -> str:
    if not abstract:
        return ""
    sentences = re.split(r'(?<=[.!?])\s+', abstract.strip())
    return " ".join(sentences[:2])

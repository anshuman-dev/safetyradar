"""
SafetyRadar Zynd AI Agent

Registers the paper categorizer as a discoverable agent on the Zynd AI network.
Run this separately: ./venv/bin/python3.12 -m backend.agent.zynd_service
"""

import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

TAG_RULES = {
    "AI Safety": ["ai safety", "safe ai", "safety", "risk"],
    "Alignment": ["alignment", "value alignment", "reward hacking", "rlhf", "constitutional ai", "scalable oversight", "corrigib"],
    "LLM Safety": ["llm safety", "jailbreak", "red team", "prompt injection", "hallucin", "toxic"],
    "Interpretability": ["interpretab", "mechanistic", "explain", "xai", "probing", "circuit"],
    "Robotic Safety": ["robot safety", "robotic safety", "autonomous vehicle", "safe rl", "collision avoidance"],
    "Adversarial Robustness": ["adversarial", "robustness", "distribution shift", "out-of-distribution"],
    "Governance & Policy": ["governance", "policy", "regulation", "audit", "standard", "ethics"],
}


def classify_paper(title: str, abstract: str) -> dict:
    text = f"{title} {abstract}".lower()
    tags = [tag for tag, kws in TAG_RULES.items() if any(kw in text for kw in kws)]
    if not tags:
        tags = ["General AI Research"]
    sentences = re.split(r'(?<=[.!?])\s+', abstract.strip())
    summary = " ".join(sentences[:2])
    return {"tags": tags, "summary": summary}


def start_zynd_agent():
    from zyndai_agent.agent import AgentConfig, ZyndAIAgent
    from langchain_core.messages import HumanMessage

    developer_kp = os.path.expanduser(os.getenv("ZYND_DEVELOPER_KEYPAIR_PATH", "~/.zynd/developer.json"))
    agent_kp = os.path.expanduser(os.getenv("ZYND_AGENT_KEYPAIR_PATH", "~/.zynd/safetyradar-agent.json"))

    config = AgentConfig(
        name="safetyradar-categorizer",
        description=(
            "AI safety paper categorizer. Given a paper title and abstract, "
            "returns relevant topic tags from: AI Safety, Alignment, LLM Safety, "
            "Interpretability, Robotic Safety, Adversarial Robustness, Governance & Policy."
        ),
        server_port=5099,
        registry_url="https://registry.zynd.ai",
        developer_keypair_path=developer_kp,
        keypair_path=agent_kp,
        tags=["ai-safety", "research", "classification"],
        category="research-tools",
    )

    def handle_message(messages):
        last = messages[-1].content if messages else ""
        # Parse title and abstract from the message
        title = ""
        abstract = ""
        if "Title:" in last:
            parts = last.split("Abstract:")
            title = parts[0].replace("Title:", "").strip()
            abstract = parts[1].strip() if len(parts) > 1 else ""
        else:
            title = last
        result = classify_paper(title, abstract)
        return json.dumps(result)

    from langchain_core.runnables import RunnableLambda
    chain = RunnableLambda(handle_message)

    agent = ZyndAIAgent(config=config)
    agent.set_langchain_agent(chain)

    print(f"[zynd] SafetyRadar agent starting on port {config.server_port}")
    print(f"[zynd] Registering with {config.registry_url}")
    agent.start()


if __name__ == "__main__":
    start_zynd_agent()

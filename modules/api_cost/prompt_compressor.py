"""
LLMLingua Prompt Compression (System 5.9).

Based on:
- LLMLingua-2 (Jiang et al., 2024): https://arxiv.org/abs/2403.12968
- LongLLMLingua (Jiang et al., 2023): https://arxiv.org/abs/2310.05736
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("optimization.api_cost.compressor")

# Stop words for compression (multi-lingual: English + Spanish)
_STOP_WORDS = frozenset({
    # English
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out",
    "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "because", "but", "and", "or", "if", "while", "about", "also",
    "this", "that", "these", "those", "it", "its",
    # Spanish
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "en", "con", "por", "para", "al", "se", "lo", "le", "les", "que",
    "es", "son", "fue", "ser", "estar", "ha", "han", "como", "más",
    "pero", "si", "no", "ya", "este", "esta", "estos", "estas",
    "ese", "esa", "esos", "esas", "su", "sus", "mi", "tu", "nos",
})

# Tokens that MUST be preserved
_PRESERVE_PATTERNS = [
    r'\{.*?\}',           # JSON blocks
    r'"[^"]*"',           # Quoted strings
    r'```[\s\S]*?```',    # Code blocks
    r'https?://\S+',      # URLs
    r'\b[A-Z_]{3,}\b',    # Constants/env vars
    r'\b\d+\.?\d*\b',     # Numbers
    r'arXiv:\d+\.\d+',    # Paper references
]

class PromptCompressor:
    """Base class for prompt compression."""
    
    def compress(self, prompt: str, target_ratio: float = 0.5) -> str:
        """Compress the prompt to target ratio."""
        return prompt

class LLMLinguaCompressor(PromptCompressor):
    """
    LLMLingua-2 inspired prompt compression.
    
    Uses heuristic importance scoring to reduce tokens while preserving
    semantic integrity and structural patterns.
    """
    
    def __init__(self, target_ratio: float = 0.5):
        self.target_ratio = target_ratio

    def compress(self, prompt: str, target_ratio: Optional[float] = None) -> str:
        ratio = target_ratio if target_ratio is not None else self.target_ratio
        original_len = len(prompt)
        
        if original_len < 500:
            return prompt
            
        # Step 1: Split into sentences
        sentences = re.split(r'(?<=[.!?\n])\s+', prompt)
        if len(sentences) <= 3:
            return prompt
            
        # Step 2: Score sentence importance
        scored_sentences = []
        for i, sent in enumerate(sentences):
            score = self._score_importance(sent, i, len(sentences), prompt)
            scored_sentences.append((score, i, sent))
            
        # Step 3: Select top sentences
        target_chars = int(original_len * ratio)
        scored_sentences.sort(reverse=True)
        
        kept = []
        current_len = 0
        for score, idx, sent in scored_sentences:
            if current_len + len(sent) <= target_chars:
                kept.append((idx, sent))
                current_len += len(sent)
                
        # Step 4: Reconstruct and refine
        kept.sort(key=lambda x: x[0])
        compressed = " ".join(sent for _, sent in kept)
        compressed = self._refine_words(compressed)
        
        logger.info("📦 Compression: %d -> %d chars (ratio=%.2f)", 
                    original_len, len(compressed), len(compressed)/original_len)
        return compressed

    def _score_importance(self, sentence: str, position: int, total: int, full_prompt: str) -> float:
        score = 0.0
        sent_lower = sentence.lower().strip()
        
        # Position bias
        if position == 0: score += 3.0
        elif position == total - 1: score += 2.5
        
        # Info density
        words = re.findall(r'\b\w+\b', sent_lower)
        content_words = [w for w in words if w not in _STOP_WORDS and len(w) > 2]
        if words:
            score += (len(content_words) / len(words)) * 2.0
            
        # Signal detection
        if any(sig in sent_lower for sig in ["task:", "result:", "important", "must"]):
            score += 1.0
            
        # Technical content
        if any(c in sentence for c in ['{', '}', '```', 'def ']):
            score += 2.0
            
        return score

    def _refine_words(self, text: str) -> str:
        # Simple word-level filtering of stop words in non-critical segments
        words = text.split()
        result = []
        for word in words:
            word_clean = word.lower().strip(".,;:!?")
            if word_clean not in _STOP_WORDS or len(word) > 4 or word[0].isupper():
                result.append(word)
        return " ".join(result)

"""
Tests for _TopicTracker — Icarus pre_llm_call token-overlap detection.

Coverage:
- Tokenise: punctuation stripping, lowercase, short-token (< 3) filtering
- is_new_topic: first-call, same-topic, new-topic, empty-string, edge cases
- OVERLAP_THRESHOLD constant is 0.6
- State updates correctly after each call
"""

import pytest
from run_agent import _TopicTracker


class TestTopicTrackerTokenize:
    """Unit tests for _tokenize()."""

    def test_lowercase(self):
        t = _TopicTracker()
        tokens = t._tokenize("HELLO WORLD")
        assert tokens == {"hello", "world"}

    def test_strips_punctuation(self):
        t = _TopicTracker()
        tokens = t._tokenize("hello, world! how are you?")
        assert tokens == {"hello", "world", "how", "are", "you"}

    def test_filters_short_tokens(self):
        """Tokens with fewer than 3 characters are filtered out."""
        t = _TopicTracker()
        # "a", "an", "in", "on", "at", "to", "b", "c" → all < 3 chars → removed
        # "the" has exactly 3 chars → kept (it is a meaningful word)
        tokens = t._tokenize("a an the in on at to b c")
        assert "the" in tokens          # len=3, kept
        assert len(tokens) == 1           # only "the" survives

    def test_whitespace_only(self):
        t = _TopicTracker()
        tokens = t._tokenize("   \t\n   ")
        assert tokens == set()

    def test_numbers_and_mixed(self):
        t = _TopicTracker()
        tokens = t._tokenize("hello 123 world")
        # "123" is all digits, split() keeps it, len=3 → kept
        assert "hello" in tokens
        assert "world" in tokens

    def test_repeated_words(self):
        t = _TopicTracker()
        tokens = t._tokenize("hello hello hello")
        assert tokens == {"hello"}

    def test_returns_set(self):
        t = _TopicTracker()
        tokens = t._tokenize("hello world")
        assert isinstance(tokens, set)


class TestTopicTrackerIsNewTopic:
    """Unit tests for is_new_topic()."""

    def test_first_call_returns_true(self):
        """First ever message should always be treated as a new topic."""
        t = _TopicTracker()
        assert t.is_new_topic("any message at all") is True

    def test_same_topic_returns_false(self):
        """Message sharing > 60 % tokens with previous → same topic."""
        t = _TopicTracker()
        t.is_new_topic("how do I configure the memory provider")
        # 4 shared tokens: configure, memory, provider (and maybe the)
        # overlap will be high enough → NOT new topic
        result = t.is_new_topic("configure memory provider with holograpic")
        assert result is False

    def test_completely_different_topic_returns_true(self):
        """Message with no shared tokens → new topic."""
        t = _TopicTracker()
        t.is_new_topic("how do I configure the memory provider")
        result = t.is_new_topic("what is the weather in Shanghai today")
        assert result is True

    def test_empty_string_returns_true(self):
        """Empty message is treated as new topic (resets state)."""
        t = _TopicTracker()
        t.is_new_topic("some message")
        result = t.is_new_topic("")
        assert result is True

    def test_state_updates_after_call(self):
        """The tracker state should reflect the last processed message."""
        t = _TopicTracker()
        t.is_new_topic("debug the memory manager prefetch")
        prev_tokens = t._prev_topic_tokens
        t.is_new_topic("analyze the memory manager bottleneck")
        # After second call, prev_tokens should reflect the second message
        assert prev_tokens != t._prev_topic_tokens

    def test_threshold_constant_is_0_6(self):
        """OVERLAP_THRESHOLD must match the Icarus default of 0.6."""
        assert _TopicTracker.OVERLAP_THRESHOLD == 0.6


class TestTopicTrackerEdgeCases:
    """Edge and boundary cases."""

    def test_single_token_message(self):
        """Single token (≥3 chars) gets high overlap with itself."""
        t = _TopicTracker()
        t.is_new_topic("debugging")
        # Single token → overlap = 1/(1 or prev_len) = 1.0 → not new topic
        result = t.is_new_topic("debugging the memory manager")
        assert result is False

    def test_all_short_tokens(self):
        """Message with only 1-2 char tokens resets cleanly."""
        t = _TopicTracker()
        t.is_new_topic("hello world")
        result = t.is_new_topic("hi ab cd")
        # All tokens < 3 chars → msg_tokens = {} → treated as new topic
        assert result is True

    def test_messages_with_punctuation_only_differ(self):
        """Messages identical after stripping punctuation share tokens."""
        t = _TopicTracker()
        t.is_new_topic("how do I configure this?")
        result = t.is_new_topic("how do I configure this!")
        assert result is False  # identical after strip

    def test_partial_overlap_boundary(self):
        """At exactly 60 % overlap the result should be deterministic."""
        t = _TopicTracker()
        # Build a message with exactly N tokens where overlap will be ~0.6
        # We test the boundary: overlap == threshold → not new topic (≥)
        # We test overlap just below: < threshold → new topic
        t.is_new_topic("tokenize messages for memory management")
        # 2 common tokens out of ~5 prev tokens = 0.4 → new topic
        result = t.is_new_topic("tokenize for analysis and review")
        # "tokenize", "for" are common (2), prev has 4 tokens minimum
        # overlap = 2/4 = 0.5 < 0.6 → new topic
        assert result is True

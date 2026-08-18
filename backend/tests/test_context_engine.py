"""
Tests for the context engine itself (not the sample repo's own tests,
which live in app/sample_repo/tests/ and test the demo API).

Run with: python -m pytest backend/tests -v
No API key needed - this is pure Python, no network calls.
"""
from app import config
from app.context_engine import count_tokens, select_context


def test_relevant_file_scores_higher_than_irrelevant_file():
    """The whole point of the context engine: files that actually relate
    to the request should outscore files that don't."""
    ctx = select_context(
        request="add email validation when a user signs up",
        repo_path=config.SAMPLE_REPO_DIR,
        budget=config.CONTEXT_TOKEN_BUDGET,
    )
    included_paths = {f.path for f in ctx.included}
    assert "auth.py" in included_paths, "auth.py should be selected for a signup-related request"


def test_unrelated_request_still_returns_something():
    """Even a vague/unrelated request should never return zero files -
    the agents need *something* to work with."""
    ctx = select_context(
        request="asdkjfh qwoieru",  # gibberish, matches nothing
        repo_path=config.SAMPLE_REPO_DIR,
        budget=config.CONTEXT_TOKEN_BUDGET,
    )
    assert len(ctx.included) >= 1


def test_small_budget_includes_fewer_files_than_large_budget():
    """Lowering the token budget should never include *more* files."""
    small = select_context("add task filtering", config.SAMPLE_REPO_DIR, budget=200)
    large = select_context("add task filtering", config.SAMPLE_REPO_DIR, budget=5000)
    assert len(small.included) <= len(large.included)


def test_included_tokens_never_exceeds_budget_by_much():
    """The greedy packer shouldn't blow past the budget (some slack is
    fine since it won't split a file, but it shouldn't be wildly over)."""
    budget = 500
    ctx = select_context("add task filtering", config.SAMPLE_REPO_DIR, budget=budget)
    # allow one file's worth of overshoot at most (the guaranteed-inclusion
    # fallback for near-empty matches)
    largest_single_file = max((count_tokens(f.content) for f in ctx.included), default=0)
    assert ctx.included_tokens <= budget + largest_single_file


def test_compression_pct_is_between_0_and_100():
    ctx = select_context("add task filtering", config.SAMPLE_REPO_DIR, budget=500)
    assert 0 <= ctx.compression_pct <= 100


def test_count_tokens_scales_with_length():
    short = count_tokens("hello")
    long = count_tokens("hello " * 100)
    assert long > short

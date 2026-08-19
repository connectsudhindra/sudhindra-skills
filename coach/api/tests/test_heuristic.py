"""Pure unit tests for scoring/heuristic.py -- no DB, no network, run with
`pytest coach/api/tests/test_heuristic.py` from coach/api/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.heuristic import score_prompt  # noqa: E402


def test_thin_prompt_scores_low_on_everything():
    score = score_prompt("fix it")
    assert score.composite < 40


def test_well_specified_prompt_scores_high():
    prompt = (
        "Fix the null pointer exception in `src/services/user_service.py` when "
        'get_user_by_id() is called with a missing id. The error is: "AttributeError: '
        "'NoneType' object has no attribute 'email'\". Don't change the public "
        "signature of get_user_by_id -- only fix the internal handling. Return the "
        "fix as a unified diff."
    )
    score = score_prompt(prompt)
    assert score.goal >= 60
    assert score.context >= 60
    assert score.constraints >= 60
    assert score.format >= 60
    assert score.composite >= 65


def test_goal_rewards_verb_and_artifact():
    weak = score_prompt("help")
    strong = score_prompt("Refactor the checkout component to remove duplicated validation")
    assert strong.goal > weak.goal


def test_context_rewards_file_path_and_error_text():
    weak = score_prompt("Fix the bug")
    strong = score_prompt(
        'Fix the bug in src/api/routes/orders.py -- it throws "KeyError: total" when the cart is empty'
    )
    assert strong.context > weak.context


def test_constraints_rewards_explicit_scope():
    weak = score_prompt("Add a retry to the upload function")
    strong = score_prompt(
        "Add a retry to the upload function. Must not retry more than 3 times, "
        "and don't touch the existing error logging."
    )
    assert strong.constraints > weak.constraints


def test_format_rewards_output_shape_request():
    weak = score_prompt("Explain how the cache works")
    strong = score_prompt("Explain how the cache works, respond with a short bullet point summary")
    assert strong.format > weak.format


def test_empty_prompt_does_not_raise():
    score = score_prompt("")
    assert score.composite == 0


def test_score_is_deterministic():
    prompt = "Add input validation to the signup form, respond with a diff"
    assert score_prompt(prompt) == score_prompt(prompt)

"""The AI layer: extraction, validation, approval tokens, and the tool loop."""

import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic import (  # noqa: E402
    MAX_OBLIGATIONS, Toolbox, check_approval_token, extract, make_approval_token,
    rule_extract, run_agent, validate_extraction,
)
from llm import MockChat, Reply  # noqa: E402
from paypal import PayPalClient, SimulatedTransport  # noqa: E402

TODAY = date(2026, 11, 1)


def client():
    return PayPalClient(transport=SimulatedTransport())


def decision_fn(amount):
    return {"verdict": "DEFER", "amount": amount, "recommended": "DEFER_TO_PAYDAY"}


# ---------------------------------------------------------------- extraction
class TestRuleExtraction(unittest.TestCase):
    def test_reads_a_messy_month(self):
        text = ("rent 1450 on the 1st; car loan 312 on the 15th, "
                "mum's medicine about $40")
        out = rule_extract(text, TODAY)
        self.assertGreaterEqual(len(out.obligations), 2)
        amounts = {o.amount_minor for o in out.obligations}
        self.assertIn(145_000, amounts)
        self.assertTrue(any("rent" in o.label for o in out.obligations))

    def test_handles_dollar_signs_and_decimals(self):
        out = rule_extract("netflix $15.49 on the 3rd", TODAY)
        self.assertEqual(out.obligations[0].amount_minor, 1_549)

    def test_empty_input_warns_instead_of_inventing(self):
        out = rule_extract("I get paid and buy things", TODAY)
        self.assertEqual(out.obligations, [])
        self.assertTrue(out.warnings)

    def test_never_exceeds_the_cap(self):
        text = "; ".join(f"bill {i} {100 + i} on the 1st" for i in range(40))
        out = rule_extract(text, TODAY)
        self.assertLessEqual(len(out.obligations), MAX_OBLIGATIONS)


class TestExtractionValidation(unittest.TestCase):
    def _bad(self, payload):
        with self.assertRaises(ValueError):
            validate_extraction(payload, TODAY)

    def test_rejects_malformed_model_output(self):
        self._bad({})
        self._bad({"obligations": []})
        self._bad({"obligations": "rent"})
        self._bad({"obligations": [{"label": "rent"}]})
        self._bad({"obligations": [{"label": "rent", "amount_minor": -5,
                                    "due": "2026-11-05"}]})
        self._bad({"obligations": [{"label": "rent", "amount_minor": "1450",
                                    "due": "2026-11-05"}]})
        self._bad({"obligations": [{"label": "rent", "amount_minor": 1450,
                                    "due": "not-a-date"}]})
        self._bad({"obligations": [{"label": "rent", "amount_minor": 1450,
                                    "due": "2099-01-01"}]})
        self._bad({"obligations": [{"label": "", "amount_minor": 1450,
                                    "due": "2026-11-05"}]})

    def test_accepts_good_output(self):
        out = validate_extraction({"obligations": [
            {"label": "rent", "amount_minor": 145_000, "due": "2026-11-28",
             "essential": True, "confidence": 0.95}]}, TODAY)
        self.assertEqual(out.obligations[0].amount_minor, 145_000)
        self.assertEqual(out.obligations[0].confidence, 0.95)


class TestExtractEntryPoint(unittest.TestCase):
    def test_uses_the_model_when_it_returns_valid_json(self):
        model = MockChat([MockChat.extract_script([
            {"label": "rent", "amount_minor": 145_000, "due": "2026-11-28"},
            {"label": "car loan", "amount_minor": 31_200, "due": "2026-11-20"}])])
        out = extract("rent 1450 on the 28th, car 312 on the 20th", TODAY, model)
        self.assertEqual(out.engine, "llm-mock")
        self.assertEqual(len(out.obligations), 2)

    def test_falls_back_to_rules_when_the_model_returns_rubbish(self):
        model = MockChat([Reply(content='{"obligations": [{"label": "x", '
                                        '"amount_minor": -1, "due": "nope"}]}')])
        out = extract("rent 1450 on the 1st", TODAY, model)
        self.assertEqual(out.engine, "rules")
        self.assertIn(145_000, {o.amount_minor for o in out.obligations})

    def test_falls_back_when_there_is_no_model(self):
        out = extract("rent 1450 on the 1st", TODAY, None)
        self.assertEqual(out.engine, "rules")
        self.assertTrue(out.obligations)


# ------------------------------------------------------------ approval gate
class TestApprovalTokens(unittest.TestCase):
    def test_money_tool_needs_a_token(self):
        box = Toolbox(client(), decision_fn)
        r = box.call("create_scheduled_invoice",
                     {"amount_minor": 24_900, "due_date": "2026-11-06"})
        self.assertEqual(r.status, "approval_required")
        self.assertIn("required_token", r.data)

    def test_token_is_bound_to_the_exact_amount(self):
        args = {"amount_minor": 24_900, "due_date": "2026-11-06"}
        token = make_approval_token("create_scheduled_invoice", args)
        other = {"amount_minor": 99_900, "due_date": "2026-11-06"}
        self.assertFalse(check_approval_token("create_scheduled_invoice", other, token))
        self.assertTrue(check_approval_token("create_scheduled_invoice", args, token))

    def test_token_is_bound_to_the_exact_tool(self):
        args = {"amount_minor": 24_900, "due_date": "2026-11-06"}
        token = make_approval_token("create_scheduled_invoice", args)
        self.assertFalse(check_approval_token("authorize_payment", args, token))

    def test_a_forged_or_empty_token_is_refused(self):
        self.assertFalse(check_approval_token("authorize_payment",
                                             {"amount_minor": 1}, "deadbeef"))
        self.assertFalse(check_approval_token("authorize_payment",
                                             {"amount_minor": 1}, None))

    def test_approved_invoice_actually_executes(self):
        c = client()
        box = Toolbox(c, decision_fn)
        args = {"amount_minor": 24_900, "due_date": "2026-11-06"}
        token = box.call("create_scheduled_invoice", args).data["required_token"]
        r = box.call("create_scheduled_invoice", args, token)
        self.assertEqual(r.status, "executed")
        self.assertTrue(r.data["invoice_id"].startswith("INV2-"))

    def test_read_tools_need_no_approval(self):
        box = Toolbox(client(), decision_fn)
        self.assertEqual(box.call("decide_purchase", {"amount_minor": 24_900}).status, "ok")

    def test_unknown_tool_is_rejected(self):
        box = Toolbox(client(), decision_fn)
        self.assertEqual(box.call("launder_money", {}).status, "error")


# ------------------------------------------------------------- the agent loop
class TestAgentLoop(unittest.TestCase):
    def test_agent_proposes_an_invoice_and_stops_for_approval(self):
        model = MockChat([
            MockChat.extract_script([{"label": "rent", "amount_minor": 145_000,
                                      "due": "2026-11-28"}]),
            MockChat.decide_script(24_900),
            MockChat.invoice_script("2026-11-06", 24_900),
        ])
        box = Toolbox(client(), decision_fn)
        run = run_agent(model, box, "rent 1450 on the 28th, can I do 249 in 4?")
        self.assertIsNotNone(run.pending_approval)
        self.assertEqual(run.pending_approval["tool"], "create_scheduled_invoice")
        executed = [s for s in run.steps if s["status"] == "executed"]
        self.assertEqual(executed, [], "the agent must not move money unapproved")

    def test_agent_executes_once_a_human_approves(self):
        args = {"amount_minor": 24_900, "due_date": "2026-11-06"}
        token = make_approval_token("create_scheduled_invoice", args)
        model = MockChat([MockChat.invoice_script("2026-11-06", 24_900)])
        box = Toolbox(client(), decision_fn)
        run = run_agent(model, box, "go ahead", approval_token=token)
        self.assertIsNone(run.pending_approval)
        self.assertIn("executed", run.final.lower())

    def test_approval_for_one_amount_cannot_pay_another(self):
        token = make_approval_token("create_scheduled_invoice",
                                    {"amount_minor": 1_000, "due_date": "2026-11-06"})
        model = MockChat([MockChat.invoice_script("2026-11-06", 999_900)])
        box = Toolbox(client(), decision_fn)
        run = run_agent(model, box, "go ahead", approval_token=token)
        self.assertIsNotNone(run.pending_approval,
                             "a token for $10 must not authorise $9,999")

    def test_loop_is_bounded(self):
        model = MockChat([MockChat.decide_script(1_000) for _ in range(30)])
        box = Toolbox(client(), decision_fn)
        run = run_agent(model, box, "loop forever", max_steps=5)
        self.assertLessEqual(len(run.steps), 5)
        self.assertIn("step limit", run.final)

    def test_agent_surfaces_the_engine_verdict_verbatim(self):
        model = MockChat([MockChat.decide_script(24_900)])
        box = Toolbox(client(), decision_fn)
        run = run_agent(model, box, "can I afford it")
        decide_step = next(s for s in run.steps if s["tool"] == "decide_purchase")
        self.assertEqual(decide_step["data"]["verdict"], "DEFER")


if __name__ == "__main__":
    unittest.main(verbosity=2)

import json, os, sys, threading, unittest, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from botvow_translate import translate, parse, render, detect, TranslationError, MAX_BYTES
from botvow_translate.estanoir import extract

def EX(n):
    with open(os.path.join(ROOT, "examples", n), encoding="utf-8") as f: return f.read()
CAT = json.load(open(os.path.join(ROOT, "catalog", "mcp-tools-list.json")))
FMTS = ["mcp", "a2a", "email"]


class Detect(unittest.TestCase):
    def test_detect(self):
        self.assertEqual(detect(EX("01-mcp-request.json")), "mcp")
        self.assertEqual(detect(EX("02-a2a-1.0-request.json")), "a2a")
        self.assertEqual(detect(EX("03-a2a-0.3-request.json")), "a2a")
        self.assertEqual(detect(EX("04-email-request.eml")), "email")
        self.assertEqual(detect(EX("05-mcp-response.json")), "mcp")
        self.assertEqual(detect(EX("06-a2a-1.0-failed-task.json")), "a2a")

    def test_rejects_unknown_json_and_oversize(self):
        with self.assertRaises(TranslationError): detect('{"hello": 1}')
        with self.assertRaises(TranslationError): detect("x" * (MAX_BYTES + 1))
        with self.assertRaises(TranslationError): detect("{not json")


class RoundTrip(unittest.TestCase):
    """Every request survives A -> B -> A with the same tool and arguments."""
    def _core(self, env): return (env.kind, env.tool, env.arguments)

    def test_request_round_trips(self):
        for src in ["01-mcp-request.json", "02-a2a-1.0-request.json"]:
            orig = parse(EX(src))
            for mid in FMTS:
                for ver in ("1.0", "0.3"):
                    out = render(parse(EX(src)), mid, a2a_version=ver)
                    back = parse(out if isinstance(out, str) else json.dumps(out))
                    self.assertEqual(self._core(back), self._core(orig), f"{src} via {mid}/{ver}")

    def test_response_round_trips(self):
        for src in ["05-mcp-response.json", "06-a2a-1.0-failed-task.json", "07-email-reply.eml"]:
            orig = parse(EX(src))
            for mid in FMTS:
                out = render(parse(EX(src)), mid)
                back = parse(out if isinstance(out, str) else json.dumps(out))
                self.assertEqual((back.kind, back.status, back.data), (orig.kind, orig.status, orig.data), f"{src} via {mid}")


class Mapping(unittest.TestCase):
    def test_mcp_to_a2a_10_shape(self):
        o = translate(EX("01-mcp-request.json"), "a2a")["output"]
        self.assertEqual(o["method"], "SendMessage")
        m = o["params"]["message"]
        self.assertEqual(m["role"], "ROLE_USER")
        self.assertEqual(m["parts"][1]["data"], {"tool": "search_trips", "arguments": {"origin_contains": "Porto", "max_days": 2, "no_car": True}})
        self.assertNotIn("kind", m["parts"][0])

    def test_mcp_to_a2a_03_shape(self):
        o = translate(EX("01-mcp-request.json"), "a2a", a2a_version="0.3")["output"]
        self.assertEqual(o["method"], "message/send")
        self.assertEqual(o["params"]["message"]["parts"][0]["kind"], "text")

    def test_a2a_failed_task_to_mcp_is_error(self):
        o = translate(EX("06-a2a-1.0-failed-task.json"), "mcp")["output"]
        self.assertTrue(o["result"]["isError"])
        self.assertIn("Unknown trip id", o["result"]["content"][0]["text"])

    def test_mcp_response_to_a2a_completed(self):
        o = translate(EX("05-mcp-response.json"), "a2a")["output"]
        self.assertEqual(o["result"]["task"]["status"]["state"], "TASK_STATE_COMPLETED")
        self.assertEqual(o["result"]["task"]["artifacts"][0]["parts"][1]["data"]["trips"][0]["id"], "douro-2-dias")

    def test_email_output_is_readable_and_marked(self):
        o = translate(EX("01-mcp-request.json"), "email")["output"]
        self.assertIn("Subject: Request: search_trips", o)
        self.assertIn("X-Translated-By: botvow-translate/0.1 (not executed)", o)
        self.assertIn("Please run 'search_trips'", o)

    def test_email_reply_keeps_correlation(self):
        r = translate(EX("07-email-reply.eml"), "a2a")
        self.assertEqual(r["envelope"]["reply_to"], "<abc-123@example.org>")
        self.assertEqual(r["output"]["result"]["task"]["id"], "<abc-123@example.org>")

    def test_never_executes(self):
        for f in os.listdir(os.path.join(ROOT, "examples")):
            for to in FMTS:
                try: self.assertFalse(translate(EX(f), to, catalog=CAT, extractor=extract)["executed"])
                except TranslationError: pass


class FreeText(unittest.TestCase):
    def test_plain_email_without_extractor_cannot_become_mcp(self):
        with self.assertRaises(TranslationError): translate(EX("04-email-request.eml"), "mcp")

    def test_plain_email_with_extractor(self):
        r = translate(EX("04-email-request.eml"), "mcp", catalog=CAT, extractor=extract)
        self.assertEqual(r["output"]["params"], {"name": "search_trips", "arguments": {"origin_contains": "Porto", "max_days": 2, "no_car": True}})
        self.assertTrue(any("inferred" in n for n in r["notes"]))

    def test_a2a_text_only_with_extractor(self):
        r = translate(EX("03-a2a-0.3-request.json"), "mcp", catalog=CAT, extractor=extract)
        self.assertEqual(r["output"]["params"]["arguments"], {"origin_contains": "Lisboa", "max_days": 3, "no_car": True})


class Catalog(unittest.TestCase):
    def test_invalid_args_flagged_and_removed(self):
        r = translate(EX("08-mcp-invalid-args.json"), "a2a", catalog=CAT)
        self.assertTrue(any("budget_eur" in n and "removed" in n for n in r["notes"]))
        self.assertTrue(any("max_days" in n and "outside" in n for n in r["notes"]))
        self.assertNotIn("budget_eur", r["output"]["params"]["message"]["parts"][1]["data"]["arguments"])

    def test_unknown_tool(self):
        raw = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "book_hotel", "arguments": {}}})
        self.assertTrue(any("not offered" in n for n in translate(raw, "email", catalog=CAT)["notes"]))


class CLIAndServer(unittest.TestCase):
    def test_cli(self):
        from botvow_translate.__main__ import main
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["--to", "mcp", "--raw", os.path.join(ROOT, "examples", "02-a2a-1.0-request.json")])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(buf.getvalue())["params"]["name"], "get_trip")

    def test_local_server(self):
        sys.path.insert(0, ROOT)
        from serve_local import H
        from http.server import HTTPServer
        srv = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/translate?to=a2a"
        req = urllib.request.Request(url, data=EX("01-mcp-request.json").encode(), method="POST")
        body = json.loads(urllib.request.urlopen(req).read())
        srv.shutdown()
        self.assertEqual(body["output"]["method"], "SendMessage")
        self.assertFalse(body["executed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

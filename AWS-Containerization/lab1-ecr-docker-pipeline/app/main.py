import json
import os

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

MAX_BYTES = 1_000_000


PLAIN = [
    ("Expecting property name enclosed in double quotes",
     "Keys need double quotes. Single quotes and bare words won't work here."),
    ("Expecting ',' delimiter",
     "Looks like a missing comma between two items."),
    ("Expecting ':' delimiter",
     "This key is missing the colon after it."),
    ("Expecting value",
     "A value is missing - often a trailing comma, or a bare word that should be quoted."),
    ("Unterminated string",
     "A string was opened but never closed."),
    ("Invalid control character",
     "There's a raw newline or tab inside a string. Escape it as \\n or \\t."),
    ("Invalid \\escape",
     "That backslash escape isn't one JSON recognises."),
    ("Extra data",
     "The JSON ends here, but there's more text after it."),
]


JSON_NAME = {"dict": "object", "list": "array", "str": "string",
             "int": "number", "float": "number", "bool": "boolean",
             "NoneType": "null"}


def explain(msg, text=None, pos=None):
    # A trailing comma is the most common mistake by far, and the stdlib
    # reports it as whatever it expected next. Look back for the real cause.
    if text is not None and pos:
        before = text[:pos].rstrip()
        if before.endswith(",") and msg.startswith(
            ("Expecting property name enclosed in double quotes", "Expecting value")
        ):
            return "There's a trailing comma just before this."

    for prefix, friendly in PLAIN:
        if msg.startswith(prefix):
            return friendly
    return msg


def measure(node, d=1):
    """Return (max depth, number of keys, number of array items)."""
    if isinstance(node, dict):
        keys = len(node)
        items = 0
        deep = d
        for v in node.values():
            sub_d, sub_k, sub_i = measure(v, d + 1)
            deep = max(deep, sub_d)
            keys += sub_k
            items += sub_i
        return deep, keys, items
    if isinstance(node, list):
        keys = 0
        items = len(node)
        deep = d
        for v in node:
            sub_d, sub_k, sub_i = measure(v, d + 1)
            deep = max(deep, sub_d)
            keys += sub_k
            items += sub_i
        return deep, keys, items
    return d, 0, 0


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/tidy", methods=["POST"])
def tidy():
    body = request.get_json(silent=True) or {}
    text = body.get("text") or ""
    style = body.get("style") or "2"
    sort_keys = bool(body.get("sort"))

    if not text.strip():
        return jsonify(ok=False, kind="empty", message="Nothing to tidy yet.")

    if len(text.encode("utf-8")) > MAX_BYTES:
        return jsonify(ok=False, kind="too-big",
                       message="That's over 1 MB. Try a smaller sample."), 413

    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        line = text.splitlines()[err.lineno - 1] if err.lineno <= len(text.splitlines()) else ""
        return jsonify(
            ok=False,
            kind="invalid",
            message=explain(err.msg, text, err.pos),
            raw=err.msg,
            line=err.lineno,
            column=err.colno,
            excerpt=line.rstrip()[:200],
        )

    if style == "min":
        out = json.dumps(data, separators=(",", ":"), sort_keys=sort_keys, ensure_ascii=False)
    elif style == "tab":
        out = json.dumps(data, indent="\t", sort_keys=sort_keys, ensure_ascii=False)
    else:
        out = json.dumps(data, indent=int(style), sort_keys=sort_keys, ensure_ascii=False)

    depth, keys, items = measure(data)
    return jsonify(
        ok=True,
        output=out,
        stats={
            "bytes": len(out.encode("utf-8")),
            "lines": out.count("\n") + 1,
            "depth": depth,
            "keys": keys,
            "items": items,
            "type": JSON_NAME.get(type(data).__name__, type(data).__name__),
        },
    )


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

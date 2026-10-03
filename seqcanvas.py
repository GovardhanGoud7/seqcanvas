"""SeqCanvas: a payment-flow simulator that draws its own sequence diagram.

Run:
    python seqcanvas.py          # diagram with approved + declined branches (alt)
    python seqcanvas.py good     # only the approved path
    python seqcanvas.py bad      # only the declined path

It writes diagram.mmd (paste into mermaid.live) and diagram.html
(built from template.html; double-click to open in your browser, needs internet for Mermaid).
"""
import sys

ACTORS = {
    "C": "Customer",
    "S": "Web Shop",
    "P": "Payment Service",
    "B": "Bank",
}


class Recorder:
    """Collects every call between actors as a Mermaid message line."""

    def __init__(self):
        self.lines = []

    def call(self, a, b, text):
        self.lines.append(f"{a}->>{b}: {text}")

    def reply(self, a, b, text):
        self.lines.append(f"{a}-->>{b}: {text}")


class Bank:
    def __init__(self, rec):
        self.rec = rec

    def authorize(self, card):
        approved = card["balance"] >= card["amount"]
        self.rec.reply("B", "P", "Authorization result")
        return approved


class PaymentService:
    def __init__(self, rec, bank):
        self.rec, self.bank = rec, bank

    def create_payment(self, card):
        self.rec.call("P", "B", "Authorize card")
        if self.bank.authorize(card):
            self.rec.reply("P", "S", "Payment confirmed")
            return True
        self.rec.reply("P", "S", "Payment failed")
        return False


class WebShop:
    def __init__(self, rec, payments):
        self.rec, self.payments = rec, payments

    def place_order(self, card):
        self.rec.call("S", "P", "Create payment request")
        if self.payments.create_payment(card):
            self.rec.reply("S", "C", "Show receipt")
        else:
            self.rec.reply("S", "C", "Ask for another card")


def run(card):
    rec = Recorder()
    shop = WebShop(rec, PaymentService(rec, Bank(rec)))
    rec.call("C", "S", "Place order")
    shop.place_order(card)
    return rec.lines


def build_diagram(mode):
    good = run({"balance": 500, "amount": 100})
    bad = run({"balance": 20, "amount": 100})

    out = ["sequenceDiagram"]
    for key, name in ACTORS.items():
        kind = "actor" if key == "C" else "participant"
        out.append(f"    {kind} {key} as {name}")

    if mode == "good":
        out += [f"    {l}" for l in good]
    elif mode == "bad":
        out += [f"    {l}" for l in bad]
    else:
        # Shared start of both runs, then split into alt / else.
        i = 0
        while i < min(len(good), len(bad)) and good[i] == bad[i]:
            i += 1
        out += [f"    {l}" for l in good[:i]]
        out.append("    alt Payment approved")
        out += [f"        {l}" for l in good[i:]]
        out.append("    else Payment declined")
        out += [f"        {l}" for l in bad[i:]]
        out.append("    end")
    return "\n".join(out)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    diagram = build_diagram(mode)
    print(diagram)
    with open("diagram.mmd", "w", encoding="utf-8") as f:
        f.write(diagram)
    with open("template.html", encoding="utf-8") as f:
        html = f.read().replace("{{DIAGRAM}}", diagram)
    with open("diagram.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("\nSaved diagram.mmd and diagram.html")
# Real-hardware transcripts

Empty by design — nobody has contributed one yet. This is the gap tracked as
a P0 in the review that prompted this directory: the test suite's BMS stub
(`scripts/pylon_stub.py`) is hand-authored from the documented protocol, not
recorded from real US2000/3000/5000 (or Pytes-branded) hardware, so parser
changes are only ever validated against our own understanding of the
protocol — never against what real firmware actually sends.

## Contributing one

1. Run `python scripts/capture_transcript.py --out <your_model>.json` against
   your real BMS (see that script's docstring for serial/TCP setup).
2. Open the file and check the redaction pass actually caught anything
   specific to your installation. It only targets the `Barcode` field (the
   one field diagnostics.py already treats as unique per physical device) —
   hand-edit anything else you don't want shared.
3. Open a PR adding the file here. `tests/test_transcripts.py` picks up any
   `*.json` file in this directory automatically and replays it through the
   real `PylontechParser` to check it parses without raising and produces
   sane values — no wiring needed on your end.

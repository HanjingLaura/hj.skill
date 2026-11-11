# Generic grokbot-style lock

Attach the uploaded photograph as the identity source. If the user supplies a style reference, use it only for style, never for identity. Historical private reference images are not distributed with this skill.

## Prompt

```
Create one isolated chibi head portrait matching this style language:
- Head only. No neck, no body, no shoulders, no hands.
- Head tilted about 20 degrees.
- Two solid black capsule/pill eyes. No white sclera, no iris, no highlight, no outline ring.
- No mouth. If the subject is a cat, keep a small pink nose and whiskers. Do not add human hair to an animal.
- Small soft blush. Keep the source identity in hair or fur color, silhouette, and accessories only.
- Flat painterly fill. Clean silhouette.
- Transparent background. If you cannot output transparency, use solid chroma green #00FF00 and nothing else in the backdrop.
- Square 1024x1024. Subject fills most of the frame.
- Do not copy gray hair, a mint hair clip, or shell earrings from any reference sheet.
- Do not add text, watermark, extra heads, or a three-view turnaround.
```

## After GenerateImage

From the Ani checkout:

```sh
python3 scripts/illustrated-avatar/matte.py generated.jpg --out stylized.png --json
python3 scripts/illustrated-avatar/extract-eyes.py stylized.png --json
python3 scripts/illustrated-avatar/build-pack.py stylized.png --out scripts/illustrated-avatar/cases/custom --id custom --json
```

From an unzipped portable folder (scripts sit in the current directory):

```sh
python3 matte.py generated.jpg --out stylized.png --json
python3 extract-eyes.py stylized.png --json
python3 build-pack.py stylized.png --out cases/custom --id custom --json
```

If extract-eyes returns `no-eyes`, supply both manual boxes and skip detection:

```sh
python3 extract-eyes.py stylized.png \
  --correct left=cx,cy,w,h --correct right=cx,cy,w,h --out eyes.json --json
python3 build-pack.py stylized.png --eyes eyes.json --out cases/custom --id custom --json
```

`matte.py` flood-keys chroma green and corner-connected near-white. That is derived alpha, not native model transparency. Keep the source photograph license on the derivative. Do not relicense CC BY-SA as PolyForm.

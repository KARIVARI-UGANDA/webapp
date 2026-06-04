import os, glob

templates_dir = r'c:\Users\Admin\OneDrive - Technische Hochschule Deggendorf\Desktop\webapp\app\templates'

# Each tuple: (bad unicode string, correct unicode string)
# Bad strings are what you get when UTF-8 bytes are misread as Windows-1252/Latin-1
fixes = [
    # © (U+00A9) -> UTF-8 C2 A9 misread as latin-1 = Â©
    ('Â©', '©'),
    # ★ (U+2605) -> UTF-8 E2 98 85 misread as win-1252 = â˜…
    ('â˜…', '★'),
    # ☆ (U+2606) -> UTF-8 E2 98 86 misread as win-1252 = â˜†
    ('â˜†', '☆'),
    # ' (U+2019) -> UTF-8 E2 80 99 misread = â€™
    ('â€™', '’'),
    # " (U+201C) -> UTF-8 E2 80 9C misread = â€œ
    ('â€œ', '“'),
    # " (U+201D) -> UTF-8 E2 80 9D misread = â€
    ('â€', '”'),
    # – (U+2013) -> UTF-8 E2 80 93 misread = â€"
    ('â€“', '–'),
    # — (U+2014) -> UTF-8 E2 80 94 misread = â€"
    ('â€”', '—'),
    # • (U+2022) -> UTF-8 E2 80 A2 misread = â€¢
    ('â€¢', '•'),
    # … (U+2026) -> UTF-8 E2 80 A6 misread = â€¦
    ('â€¦', '…'),
    # ─ (U+2500) -> UTF-8 E2 94 80 misread = â"€
    ('â”€', '─'),
    # × (U+00D7) -> UTF-8 C3 97 misread = Ã—
    ('Ã—', '×'),
    # é -> UTF-8 C3 A9 misread = Ã©
    ('Ã©', 'é'),
    # è -> UTF-8 C3 A8 misread = Ã¨
    ('Ã¨', 'è'),
    # à -> UTF-8 C3 A0 misread = Ã
    ('Ã ', 'à'),
    # ã -> UTF-8 C3 A3 misread = Ã£
    ('Ã£', 'ã'),
    # ç -> UTF-8 C3 A7 misread = Ã§
    ('Ã§', 'ç'),
    # ü -> UTF-8 C3 BC misread = Ã¼
    ('Ã¼', 'ü'),
    # ñ -> UTF-8 C3 B1 misread = Ã±
    ('Ã±', 'ñ'),
    # non-breaking space artifact
    ('Â ', ' '),
    # stray Â before other chars
    ('Â', ''),
]

total_fixed = 0
for path in glob.glob(os.path.join(templates_dir, '**', '*.html'), recursive=True):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    original = text
    for bad, good in fixes:
        text = text.replace(bad, good)
    if text != original:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        total_fixed += 1
        print('Fixed:', os.path.basename(path))

print(f'\nDone. {total_fixed} file(s) updated.')

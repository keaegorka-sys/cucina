"""Собирает версию для ссылки Claude (artifact) из index.html.

Платформа Claude сама добавляет <!doctype>, <head> и <body>, поэтому из index.html
берётся только то, что между метками <!--ARTIFACT-START--> … </head> и <!--ARTIFACT-BODY--> … </body>.

Запуск:  python tools/build-artifact.py <папка-для-результата>
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["recipes.js", "recipes-book.js", "recipes-kd.js", "prices.js", "metro.js", "photos.js"]


def main(out_dir: str) -> None:
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    start, body = "<!--ARTIFACT-START-->", "<!--ARTIFACT-BODY-->"
    head_part = src[src.index(start) + len(start):src.index("</head>")]
    body_part = src[src.index(body) + len(body):src.rindex("</body>")]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(head_part.strip() + "\n" + body_part.strip() + "\n")
    for name in FILES:
        shutil.copyfile(os.path.join(ROOT, name), os.path.join(out_dir, name))
    print("ok:", out_dir)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])

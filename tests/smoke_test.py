import pathlib
import subprocess
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from metrix_lang.interpreter import run
from metrix_lang.editor import EasyCompleter
from prompt_toolkit.document import Document


def main():
    result = subprocess.run(
        ["python3", "-m", "metrix_lang.cli", "run", "examples/hello.met"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "hello from METRIX\n15\n"

    direct_result = subprocess.run(
        ["python3", "-m", "metrix_lang.cli", "examples/hello.met"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert direct_result.returncode == 0, direct_result.stderr
    assert direct_result.stdout == "hello from METRIX\n15\n"

    check_result = subprocess.run(
        ["python3", "-m", "metrix_lang.cli", "check", "examples/hello.met"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert check_result.returncode == 0, check_result.stderr
    assert check_result.stdout == "ok\n"

    control_flow = '''\
func label(name):
    return upper(name)
set total 0
for number in range(1, 4):
    add total number
if total == 6:
    say label("metrix")
else:
    say "wrong"
while total < 8:
    add total 1
say total
'''
    assert run(control_flow) == ["METRIX", "8"]

    workspace = '''\
set data {"name": "metrix", "rank": 1}
say title(get(data, "name"))
say count(keys(data))
row "left\\nmore" | "right" [left:20]
'''
    workspace_output = run(workspace)
    assert workspace_output[:2] == ["Metrix", "2"]
    assert "more" in workspace_output[4]

    enhanced_ui = '''\
set project "METRIX"
set title_text title(project)
say "{title_text}" [badge]
say "let x = 42" [code]
'''
    enhanced_output = run(enhanced_ui)
    assert enhanced_output[0] == "[ Metrix ]"
    assert enhanced_output[1].startswith("┌")

    suggestions = list(EasyCompleter().get_completions(Document("s", cursor_position=1), None))
    assert suggestions[0].text == "say"
    all_suggestions = list(EasyCompleter().get_completions(Document("", cursor_position=0), None))
    assert len(all_suggestions) >= 80
    assert {"say", "[box:dotted]", "uuid(", "urlencode("} <= {item.text for item in all_suggestions}

    toolkit = '''\
set words ["metrix", "studio", "metrix"]
say join(unique(words), ",")
say reverse("abc")
say slice("terminal", 0, 4)
say urlencode("hello world")
'''
    assert run(toolkit) == ["metrix,studio", "cba", "term", "hello+world"]
    print("smoke test passed")


if __name__ == "__main__":
    main()

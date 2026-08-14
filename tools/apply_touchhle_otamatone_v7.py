from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v6.py")

# Keep every compatibility fix and the high-signal diagnostics from v6.
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# Real compatibility fix discovered by inspecting MainWindow.nib after v6:
# UIButtonStatefulContent can contain UIButtonContent objects without a UITitle
# (for example a non-normal state that only changes image/color). touchHLE's
# UIButtonContent -initWithCoder: unconditionally calls to_rust_string(title)
# for a debug log, which panics when decodeObjectForKey: returns nil.
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_button.rs",
    "    let title_key = get_static_str(env, \"UITitle\");\n"
    "    let title: id = msg![env; coder decodeObjectForKey:title_key];\n"
    "    log_dbg!(\"UIButtonContent: UITitle -> {}\", to_rust_string(env, title));\n",
    "    let title_key = get_static_str(env, \"UITitle\");\n"
    "    let title: id = msg![env; coder decodeObjectForKey:title_key];\n"
    "    if title != nil {\n"
    "        log_dbg!(\"UIButtonContent: UITitle -> {}\", to_rust_string(env, title));\n"
    "    } else {\n"
    "        log!(\"Otamatone v7: UIButtonContent has no UITitle; accepting nil\");\n"
    "    }\n",
)

print("Applied Otamatone v7 UIButtonContent nil-title compatibility fix")

from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v5.py")

# Keep every compatibility fix and the high-signal NIB diagnostics from v5.
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# Real compatibility fix discovered by the v5 NIB trace:
# UIHtmlView inherits UIView -initWithCoder:, which recursively decodes its
# UISubviews. One of those is UIWebView, and touchHLE's UIWebView
# -initWithCoder: is currently a todo!(), causing a host panic during NIB load.
# UIWebView doesn't have extra host-side state here, so initialize the UIView
# superclass portion and keep the existing no-op/TODO UIWebView properties.
replace_once(
    "src/frameworks/uikit/ui_view/ui_web_view.rs",
    "use crate::objc::{id, nil, objc_classes, ClassExports};\n",
    "use crate::objc::{id, msg_super, nil, objc_classes, ClassExports};\n",
)

replace_once(
    "src/frameworks/uikit/ui_view/ui_web_view.rs",
    "// NSCoding implementation\n"
    "- (id)initWithCoder:(id)_coder {\n"
    "    todo!()\n"
    "}\n",
    "// NSCoding implementation\n"
    "- (id)initWithCoder:(id)coder {\n"
    "    log!(\"Otamatone v6: UIWebView initWithCoder ENTER this={:?} coder={:?}\", this, coder);\n"
    "    let this: id = msg_super![env; this initWithCoder:coder];\n"
    "    log!(\"Otamatone v6: UIWebView initWithCoder EXIT this={:?}\", this);\n"
    "    this\n"
    "}\n",
)

print("Applied Otamatone v6 UIWebView initWithCoder compatibility fix")

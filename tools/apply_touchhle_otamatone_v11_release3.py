from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v11_release2.py")
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# core_graphics re-exports CGPoint/CGRect/CGSize but not CGAffineTransform.
# The broad animation helper deliberately runs before cargo fmt, so normalize
# the two imports here to the concrete module path.
replace_once(
    "src/frameworks/foundation/ns_value.rs",
    "use crate::frameworks::core_graphics::{CGAffineTransform, CGPoint, CGRect, CGSize};",
    "use crate::frameworks::core_graphics::cg_affine_transform::CGAffineTransform;\n"
    "use crate::frameworks::core_graphics::{CGPoint, CGRect, CGSize};",
)
replace_once(
    "src/frameworks/core_animation/animation.rs",
    "use crate::frameworks::core_graphics::CGAffineTransform;",
    "use crate::frameworks::core_graphics::cg_affine_transform::CGAffineTransform;",
)

# A descendant with masksToBounds may leave GL scissoring enabled. Disable it
# before the compositor presents its internal framebuffer to the real window.
p = ROOT / "src/frameworks/core_animation/composition.rs"
s = p.read_text()
old = '''        gles.Color4f(1.0, 1.0, 1.0, 1.0);
        gles.Disable(gles11::BLEND);
        gles.MatrixMode(gles11::PROJECTION);'''
new = '''        gles.Color4f(1.0, 1.0, 1.0, 1.0);
        gles.Disable(gles11::BLEND);
        // A descendant with masksToBounds may have left scissoring enabled.
        // Presentation to the default framebuffer must never inherit it.
        gles.Disable(gles11::SCISSOR_TEST);
        gles.MatrixMode(gles11::PROJECTION);'''
if s.count(old) != 1:
    raise RuntimeError(f"Expected compositor cleanup point once; found {s.count(old)}")
p.write_text(s.replace(old, new, 1))

print("Applied final Otamatone v11 transform imports + compositor scissor cleanup")

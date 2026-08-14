from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v11_release2.py")
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)

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

print("Applied final Otamatone v11 compositor scissor cleanup")

from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v11_final.py")
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# Old Interface Builder archives represent "First Responder" as a UIProxyObject.
# It is not a real target object: connections to it are nil-target actions that
# UIApplication/UIControl resolve dynamically through the responder chain.
replace_once(
    "src/frameworks/uikit/ui_nib.rs",
    '''    } else {
        log!("TODO: UIProxyObject replacement for {}, instance {:?} left unreplaced", id, this);
        this
    }
}''',
    '''    } else if id == "IBFirstResponder" {
        release(env, this);
        nil
    } else {
        log!("Warning: unknown UIProxyObject {}, instance {:?} left unreplaced", id, this);
        this
    }
}''',
)

print("Applied Otamatone v11 release IBFirstResponder compatibility")

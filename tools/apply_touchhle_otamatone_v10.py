from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v9.py")

# Keep all compatibility fixes and compact diagnostics through v9.
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# v9 proves the NIB completes, both UICustomSwitch instances initialize, and
# SettingView returns. UIApplicationMain then enters the app delegate's
# applicationDidFinishLaunching:, whose first InitGUI call initializes
# UIMelodyListView. UIMelodyListCellView -initWithFrame: creates two labels,
# then configures an UIImageView with -setHighlightedImage:. This selector is
# absent from the touchHLE base, so add retained highlighted-image state and
# NSCoding support rather than a one-off no-op.
replace_once(
    "src/frameworks/uikit/ui_view/ui_image_view.rs",
    "    /// `UIImage*`\n    image: id,\n",
    "    /// `UIImage*`\n"
    "    image: id,\n"
    "    /// `UIImage*` used by old UIKit clients for highlighted state.\n"
    "    highlighted_image: id,\n",
)

replace_once(
    "src/frameworks/uikit/ui_view/ui_image_view.rs",
    "        image,\n    } = env.objc.borrow(this);\n    release(env, image);\n",
    "        image,\n"
    "        highlighted_image,\n"
    "    } = env.objc.borrow(this);\n"
    "    release(env, image);\n"
    "    release(env, highlighted_image);\n",
)

replace_once(
    "src/frameworks/uikit/ui_view/ui_image_view.rs",
    "    () = msg![env; this setImage:image];\n\n    this\n}\n",
    "    () = msg![env; this setImage:image];\n\n"
    "    let highlighted_key = get_static_str(env, \"UIHighlightedImage\");\n"
    "    let highlighted_image: id = msg![env; coder decodeObjectForKey:highlighted_key];\n"
    "    if highlighted_image != crate::objc::nil {\n"
    "        () = msg![env; this setHighlightedImage:highlighted_image];\n"
    "    }\n\n"
    "    this\n"
    "}\n",
)

replace_once(
    "src/frameworks/uikit/ui_view/ui_image_view.rs",
    "- (id)image {\n    env.objc.borrow::<UIImageViewHostObject>(this).image\n}\n\n- (())setImage:(id)new_image { // UIImage*\n",
    "- (id)image {\n"
    "    env.objc.borrow::<UIImageViewHostObject>(this).image\n"
    "}\n\n"
    "- (id)highlightedImage {\n"
    "    env.objc.borrow::<UIImageViewHostObject>(this).highlighted_image\n"
    "}\n\n"
    "- (())setHighlightedImage:(id)new_image { // UIImage*\n"
    "    log!(\"Otamatone v10: UIImageView setHighlightedImage this={:?} image={:?}\", this, new_image);\n"
    "    let host_obj = env.objc.borrow_mut::<UIImageViewHostObject>(this);\n"
    "    let old_image = std::mem::replace(&mut host_obj.highlighted_image, new_image);\n"
    "    retain(env, new_image);\n"
    "    release(env, old_image);\n"
    "}\n\n"
    "- (())setImage:(id)new_image { // UIImage*\n",
)

# Expand the compact guest tracer only for the app-owned methods on the newly
# reached startup path. Host UIKit methods remain untraced, so this adds only a
# handful of lines (UIMelodyListView and its 12 cells).
replace_once(
    "src/objc/messages.rs",
    '                            | "layoutSubviews"\n'
    '                        ) {\n',
    '                            | "layoutSubviews"\n'
    '                            | "initWithFrame:"\n'
    '                            | "Initialize"\n'
    '                            | "Initialize:::"\n'
    '                        ) {\n',
)

print("Applied Otamatone v10 UIImageView highlighted-image compatibility + startup guest tracing")

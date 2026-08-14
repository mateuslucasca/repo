from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v7.py")

# Keep all compatibility fixes and targeted diagnostics through v7.
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# v7 gets all the way through the UIScrollView subtree in SettingView. The
# next direct subview in MainWindow.nib is UINavigationBar. This touchHLE base
# has no UINavigationBar/UINavigationItem/UIBarButtonItem implementation, and
# the same NIB later contains UITabBar/UITabBarItem. Add deliberately small
# NSCoding-compatible shims so the old NIB can finish unarchiving.
#
# UIBarButtonItem inherits UIControl here intentionally: touchHLE's generic
# UIRuntimeEventConnection sends addTarget:action:forControlEvents: to the
# archived "Done" bar button. UIControl provides exactly that infrastructure.
replace_once(
    "src/frameworks/uikit/ui_nib.rs",
    "@end\n\n};\n\n/// Takes a [GuestPathBuf] where a nib file is located and deserializes it.\n",
    r'''@end

// Minimal legacy bar classes used by Otamatone's iPhone OS 3-era MainWindow.nib.
// These are compatibility shims, not complete UIKit implementations.
@implementation UINavigationBar: UIView

- (id)initWithCoder:(id)coder {
    log!("Otamatone v8: UINavigationBar initWithCoder ENTER this={:?}", this);
    let this: id = msg_super![env; this initWithCoder:coder];
    let items_key = get_static_str(env, "UIItems");
    let _items: id = msg![env; coder decodeObjectForKey:items_key];
    log!("Otamatone v8: UINavigationBar initWithCoder EXIT this={:?}", this);
    this
}

@end

@implementation UINavigationItem: NSObject

- (id)initWithCoder:(id)coder {
    log!("Otamatone v8: UINavigationItem initWithCoder ENTER this={:?}", this);
    let right_key = get_static_str(env, "UIRightBarButtonItem");
    let _right: id = msg![env; coder decodeObjectForKey:right_key];
    log!("Otamatone v8: UINavigationItem initWithCoder EXIT this={:?}", this);
    this
}

@end

@implementation UIBarButtonItem: UIControl

- (id)initWithCoder:(id)coder {
    log!("Otamatone v8: UIBarButtonItem initWithCoder ENTER this={:?}", this);
    // Do not call UIView/UIControl initWithCoder: here: UIBarButtonItem is not
    // actually a view and its archive has no UIBounds/UICenter fields. The
    // inherited UIControl host object is already default-initialized by alloc.
    let enabled_key = get_static_str(env, "UIEnabled");
    let enabled: bool = msg![env; coder decodeBoolForKey:enabled_key];
    () = msg![env; this setEnabled:enabled];
    log!("Otamatone v8: UIBarButtonItem initWithCoder EXIT this={:?} enabled={}", this, enabled);
    this
}

@end

@implementation UITabBar: UIView

- (id)initWithCoder:(id)coder {
    log!("Otamatone v8: UITabBar initWithCoder ENTER this={:?}", this);
    let this: id = msg_super![env; this initWithCoder:coder];
    let items_key = get_static_str(env, "UIItems");
    let _items: id = msg![env; coder decodeObjectForKey:items_key];
    log!("Otamatone v8: UITabBar initWithCoder EXIT this={:?}", this);
    this
}

- (())setDelegate:(id)_delegate {
    // Rendering/delegate callbacks are not implemented yet; startup only.
}

- (())setSelectedItem:(id)_item {
    // Startup compatibility. Selection/rendering can be implemented later.
}

@end

@implementation UITabBarItem: NSObject

- (id)initWithCoder:(id)coder {
    log!("Otamatone v8: UITabBarItem initWithCoder ENTER this={:?}", this);
    // Force the archived title/image objects to be decoded while keeping this
    // shim stateless.
    let title_key = get_static_str(env, "UITitle");
    let _title: id = msg![env; coder decodeObjectForKey:title_key];
    let image_key = get_static_str(env, "UIImage");
    let _image: id = msg![env; coder decodeObjectForKey:image_key];
    log!("Otamatone v8: UITabBarItem initWithCoder EXIT this={:?}", this);
    this
}

@end

};

/// Takes a [GuestPathBuf] where a nib file is located and deserializes it.
''',
)

# Make future keyed-archive failures self-identifying without restoring the
# enormous ABI trace. Log class lookup once and every archived object's
# initWithCoder entry/exit. This is typically hundreds of compact lines, not
# tens of thousands.
replace_once(
    "src/frameworks/foundation/ns_keyed_unarchiver.rs",
    "                    let class_name = class_name.to_string();\n"
    "                    env.objc.get_known_class(&class_name, &mut env.mem)\n",
    "                    let class_name = class_name.to_string();\n"
    "                    log!(\"Otamatone v8: NSKeyedUnarchiver class lookup {:?}\", class_name);\n"
    "                    env.objc.get_known_class(&class_name, &mut env.mem)\n",
)

replace_once(
    "src/frameworks/foundation/ns_keyed_unarchiver.rs",
    "            let new_object: id = msg![env; class alloc];\n"
    "            let new_object: id = msg![env; new_object initWithCoder:unarchiver];\n\n"
    "            let host_obj = borrow_host_obj(env, unarchiver); // reborrow\n",
    "            let new_object: id = msg![env; class alloc];\n"
    "            let class_name = env.objc.try_get_class_name(new_object);\n"
    "            log!(\"Otamatone v8: unarchive ENTER key={} object={:?} class={:?}\", key.get(), new_object, class_name);\n"
    "            let new_object: id = msg![env; new_object initWithCoder:unarchiver];\n"
    "            let class_name = env.objc.try_get_class_name(new_object);\n"
    "            log!(\"Otamatone v8: unarchive EXIT  key={} object={:?} class={:?}\", key.get(), new_object, class_name);\n\n"
    "            let host_obj = borrow_host_obj(env, unarchiver); // reborrow\n",
)

print("Applied Otamatone v8 legacy navigation/tab bar compatibility shims + keyed archive tracer")

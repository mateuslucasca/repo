from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v3.py")

# Keep all compatibility fixes and the targeted initWithCoder tracer from v3.
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# Add high-signal checkpoints around UIApplicationMain startup. The v3 log
# proved EAGLView -initWithCoder: returns successfully, but the process/log ends
# immediately afterwards. These checkpoints isolate the exact UIKit startup
# phase without restoring the extremely expensive full ABI/dyld trace.
replace_once(
    "src/frameworks/uikit/ui_application.rs",
    ") {\n    // UIKit creates and drains autorelease pools when handling events.\n",
    ") {\n    log!(\"Otamatone v4: UIApplicationMain ENTER\");\n    // UIKit creates and drains autorelease pools when handling events.\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "        if let Some(main_nib_filename) = env.bundle.main_nib_filename(device_family) {\n",
    "        if let Some(main_nib_filename) = env.bundle.main_nib_filename(device_family) {\n"
    "            log!(\"Otamatone v4: main NIB path selected {:?}\", main_nib_filename);\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "                let _: id = msg![env; nib instantiateWithOwner:ui_application\n                                               options:nil];\n",
    "                log!(\"Otamatone v4: main NIB instantiate ENTER\");\n"
    "                let _: id = msg![env; nib instantiateWithOwner:ui_application\n"
    "                                               options:nil];\n"
    "                log!(\"Otamatone v4: main NIB instantiate EXIT\");\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "        let delegate: id = msg![env; ui_application delegate];\n        if delegate != nil {\n",
    "        let delegate: id = msg![env; ui_application delegate];\n"
    "        log!(\"Otamatone v4: delegate after NIB = {:?}\", delegate);\n"
    "        if delegate != nil {\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "        let _: () = msg![env; pool drain];\n\n        ui_application\n",
    "        log!(\"Otamatone v4: initial autorelease pool drain ENTER\");\n"
    "        let _: () = msg![env; pool drain];\n"
    "        log!(\"Otamatone v4: initial autorelease pool drain EXIT\");\n\n"
    "        ui_application\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "        let delegate: id = msg![env; ui_application delegate];\n        // iOS 3+ apps usually use application:didFinishLaunchingWithOptions:,\n",
    "        let delegate: id = msg![env; ui_application delegate];\n"
    "        log!(\"Otamatone v4: launch callbacks ENTER delegate={:?}\", delegate);\n"
    "        // iOS 3+ apps usually use application:didFinishLaunchingWithOptions:,\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "            let empty_dict: id = msg_class![env; NSDictionary dictionary];\n            () = msg![env; delegate application:ui_application didFinishLaunchingWithOptions:empty_dict];\n",
    "            log!(\"Otamatone v4: calling application:didFinishLaunchingWithOptions: ENTER\");\n"
    "            let empty_dict: id = msg_class![env; NSDictionary dictionary];\n"
    "            () = msg![env; delegate application:ui_application didFinishLaunchingWithOptions:empty_dict];\n"
    "            log!(\"Otamatone v4: calling application:didFinishLaunchingWithOptions: EXIT\");\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "            () = msg![env; delegate applicationDidFinishLaunching:ui_application];\n",
    "            log!(\"Otamatone v4: calling applicationDidFinishLaunching: ENTER\");\n"
    "            () = msg![env; delegate applicationDidFinishLaunching:ui_application];\n"
    "            log!(\"Otamatone v4: calling applicationDidFinishLaunching: EXIT\");\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "        let center: id = msg_class![env; NSNotificationCenter defaultCenter];\n        let notif_name = get_static_str(env, UIApplicationDidFinishLaunchingNotification);\n",
    "        log!(\"Otamatone v4: launch delegate callback phase EXIT\");\n"
    "        let center: id = msg_class![env; NSNotificationCenter defaultCenter];\n"
    "        let notif_name = get_static_str(env, UIApplicationDidFinishLaunchingNotification);\n"
    "        log!(\"Otamatone v4: DidFinishLaunching notification ENTER\");\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "        () = msg![env; center postNotificationName:notif_name object:ui_application userInfo:nil];\n\n        let _: () = msg![env; pool drain];\n    }\n\n    // Call layoutSubviews on all views in the view hierarchy.\n",
    "        () = msg![env; center postNotificationName:notif_name object:ui_application userInfo:nil];\n"
    "        log!(\"Otamatone v4: DidFinishLaunching notification EXIT\");\n\n"
    "        log!(\"Otamatone v4: launch autorelease pool drain ENTER\");\n"
    "        let _: () = msg![env; pool drain];\n"
    "        log!(\"Otamatone v4: launch autorelease pool drain EXIT\");\n"
    "    }\n\n"
    "    // Call layoutSubviews on all views in the view hierarchy.\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "    let views = env.framework_state.uikit.ui_view.views.clone();\n    for view in views {\n        () = msg![env; view layoutSubviews];\n    }\n",
    "    let views = env.framework_state.uikit.ui_view.views.clone();\n"
    "    log!(\"Otamatone v4: layoutSubviews pass ENTER count={}\", views.len());\n"
    "    for view in views {\n"
    "        log!(\"Otamatone v4: layoutSubviews ENTER view={:?}\", view);\n"
    "        () = msg![env; view layoutSubviews];\n"
    "        log!(\"Otamatone v4: layoutSubviews EXIT view={:?}\", view);\n"
    "    }\n"
    "    log!(\"Otamatone v4: layoutSubviews pass EXIT\");\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "        let delegate: id = msg![env; ui_application delegate];\n        if env\n            .objc\n            .object_has_method_named(&env.mem, delegate, \"applicationDidBecomeActive:\")\n        {\n            () = msg![env; delegate applicationDidBecomeActive:ui_application];\n        }\n",
    "        let delegate: id = msg![env; ui_application delegate];\n"
    "        log!(\"Otamatone v4: didBecomeActive phase ENTER delegate={:?}\", delegate);\n"
    "        if env\n"
    "            .objc\n"
    "            .object_has_method_named(&env.mem, delegate, \"applicationDidBecomeActive:\")\n"
    "        {\n"
    "            log!(\"Otamatone v4: calling applicationDidBecomeActive: ENTER\");\n"
    "            () = msg![env; delegate applicationDidBecomeActive:ui_application];\n"
    "            log!(\"Otamatone v4: calling applicationDidBecomeActive: EXIT\");\n"
    "        }\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "        let _: () = msg![env; pool drain];\n    }\n\n    // FIXME: There are more messages we should send.\n",
    "        let _: () = msg![env; pool drain];\n"
    "        log!(\"Otamatone v4: didBecomeActive phase EXIT\");\n"
    "    }\n\n"
    "    // FIXME: There are more messages we should send.\n",
)

replace_once(
    "src/frameworks/uikit/ui_application.rs",
    "    let run_loop: id = msg_class![env; NSRunLoop mainRunLoop];\n    let _: () = msg![env; run_loop run];\n",
    "    log!(\"Otamatone v4: entering NSRunLoop\");\n"
    "    let run_loop: id = msg_class![env; NSRunLoop mainRunLoop];\n"
    "    let _: () = msg![env; run_loop run];\n"
    "    log!(\"Otamatone v4: NSRunLoop RETURNED unexpectedly\");\n",
)

# Expand the v3 guest tracer to a handful of startup/lifecycle selectors only.
# This stays small but identifies the exact app-owned callback if a checkpoint
# disappears inside guest Objective-C code.
replace_once(
    "src/objc/messages.rs",
    '                        if selector_name == "initWithCoder:" {\n',
    '                        if matches!(selector_name.as_str(),\n'
    '                            "initWithCoder:"\n'
    '                            | "awakeFromNib"\n'
    '                            | "application:didFinishLaunchingWithOptions:"\n'
    '                            | "applicationDidFinishLaunching:"\n'
    '                            | "applicationDidBecomeActive:"\n'
    '                            | "layoutSubviews"\n'
    '                        ) {\n',
)

print("Applied Otamatone v4 UIApplicationMain checkpoint tracer")

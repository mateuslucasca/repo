from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v4.py")

# Keep all compatibility fixes and v4 startup checkpoints.
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# Instrument the internals of UINib::instantiateWithOwner/load_nib_file. v4 proved
# the process remains inside main NIB instantiation after EAGLView initWithCoder:
# returns successfully. These checkpoints isolate object decode, connections,
# awakeFromNib, visible windows, and top-level object decode.
replace_once(
    "src/frameworks/uikit/ui_nib.rs",
    "    let unarchiver = load_nib_file(env, this, GuestPathBuf::from(nib_path)).unwrap();\n"
    "    let top_level_objects_key = get_static_str(env, \"UINibTopLevelObjectsKey\");\n"
    "    let top_level_objects = msg![env; unarchiver decodeObjectForKey:top_level_objects_key];\n"
    "    release(env, unarchiver);\n",
    "    log!(\"Otamatone v5: load_nib_file ENTER\");\n"
    "    let unarchiver = load_nib_file(env, this, GuestPathBuf::from(nib_path)).unwrap();\n"
    "    log!(\"Otamatone v5: load_nib_file EXIT unarchiver={:?}\", unarchiver);\n"
    "    let top_level_objects_key = get_static_str(env, \"UINibTopLevelObjectsKey\");\n"
    "    log!(\"Otamatone v5: UINibTopLevelObjectsKey decode ENTER\");\n"
    "    let top_level_objects = msg![env; unarchiver decodeObjectForKey:top_level_objects_key];\n"
    "    let top_level_count: NSUInteger = msg![env; top_level_objects count];\n"
    "    log!(\"Otamatone v5: UINibTopLevelObjectsKey decode EXIT array={:?} count={}\", top_level_objects, top_level_count);\n"
    "    log!(\"Otamatone v5: unarchiver release ENTER\");\n"
    "    release(env, unarchiver);\n"
    "    log!(\"Otamatone v5: unarchiver release EXIT\");\n",
)

replace_once(
    "src/frameworks/uikit/ui_nib.rs",
    "    let objects_key = get_static_str(env, \"UINibObjectsKey\");\n"
    "    let objects: id = msg![env; unarchiver decodeObjectForKey:objects_key];\n\n"
    "    // Connect all the outlets with UIRuntimeOutletConnection\n",
    "    let objects_key = get_static_str(env, \"UINibObjectsKey\");\n"
    "    log!(\"Otamatone v5: UINibObjectsKey decode ENTER\");\n"
    "    let objects: id = msg![env; unarchiver decodeObjectForKey:objects_key];\n"
    "    let objects_count: NSUInteger = msg![env; objects count];\n"
    "    log!(\"Otamatone v5: UINibObjectsKey decode EXIT array={:?} count={}\", objects, objects_count);\n\n"
    "    // Connect all the outlets with UIRuntimeOutletConnection\n",
)

replace_once(
    "src/frameworks/uikit/ui_nib.rs",
    "    let conns_key = get_static_str(env, \"UINibConnectionsKey\");\n"
    "    let conns: id = msg![env; unarchiver decodeObjectForKey:conns_key];\n"
    "    let conns_count: NSUInteger = msg![env; conns count];\n"
    "    for i in 0..conns_count {\n"
    "        let conn: id = msg![env; conns objectAtIndex:i];\n"
    "        () = msg![env; conn connect];\n"
    "    }\n",
    "    let conns_key = get_static_str(env, \"UINibConnectionsKey\");\n"
    "    log!(\"Otamatone v5: UINibConnectionsKey decode ENTER\");\n"
    "    let conns: id = msg![env; unarchiver decodeObjectForKey:conns_key];\n"
    "    let conns_count: NSUInteger = msg![env; conns count];\n"
    "    log!(\"Otamatone v5: UINibConnectionsKey decode EXIT array={:?} count={}\", conns, conns_count);\n"
    "    for i in 0..conns_count {\n"
    "        let conn: id = msg![env; conns objectAtIndex:i];\n"
    "        let class_name = env.objc.try_get_class_name(conn);\n"
    "        log!(\"Otamatone v5: connection connect ENTER index={}/{} object={:?} class={:?}\", i, conns_count, conn, class_name);\n"
    "        () = msg![env; conn connect];\n"
    "        log!(\"Otamatone v5: connection connect EXIT  index={}/{} object={:?}\", i, conns_count, conn);\n"
    "    }\n"
    "    log!(\"Otamatone v5: all connections connected\");\n",
)

replace_once(
    "src/frameworks/uikit/ui_nib.rs",
    "    let enumerator: id = msg![env; objects objectEnumerator];\n"
    "    loop {\n"
    "        let next: id = msg![env; enumerator nextObject];\n"
    "        if next == nil {\n"
    "            break;\n"
    "        }\n"
    "        () = msg![env; next awakeFromNib];\n"
    "    }\n",
    "    log!(\"Otamatone v5: awakeFromNib pass ENTER count={}\", objects_count);\n"
    "    let enumerator: id = msg![env; objects objectEnumerator];\n"
    "    let mut awake_index: NSUInteger = 0;\n"
    "    loop {\n"
    "        let next: id = msg![env; enumerator nextObject];\n"
    "        if next == nil {\n"
    "            break;\n"
    "        }\n"
    "        let class_name = env.objc.try_get_class_name(next);\n"
    "        log!(\"Otamatone v5: awakeFromNib ENTER index={}/{} object={:?} class={:?}\", awake_index, objects_count, next, class_name);\n"
    "        () = msg![env; next awakeFromNib];\n"
    "        log!(\"Otamatone v5: awakeFromNib EXIT  index={}/{} object={:?}\", awake_index, objects_count, next);\n"
    "        awake_index += 1;\n"
    "    }\n"
    "    log!(\"Otamatone v5: awakeFromNib pass EXIT processed={}\", awake_index);\n",
)

replace_once(
    "src/frameworks/uikit/ui_nib.rs",
    "    let visibles_key = get_static_str(env, \"UINibVisibleWindowsKey\");\n"
    "    let visibles: id = msg![env; unarchiver decodeObjectForKey:visibles_key];\n"
    "    let visibles_count: NSUInteger = msg![env; visibles count];\n"
    "    for i in 0..visibles_count {\n"
    "        let visible: id = msg![env; visibles objectAtIndex:i];\n"
    "        () = msg![env; visible setHidden:false];\n"
    "    }\n\n"
    "    Ok(unarchiver)\n",
    "    let visibles_key = get_static_str(env, \"UINibVisibleWindowsKey\");\n"
    "    log!(\"Otamatone v5: UINibVisibleWindowsKey decode ENTER\");\n"
    "    let visibles: id = msg![env; unarchiver decodeObjectForKey:visibles_key];\n"
    "    let visibles_count: NSUInteger = msg![env; visibles count];\n"
    "    log!(\"Otamatone v5: UINibVisibleWindowsKey decode EXIT array={:?} count={}\", visibles, visibles_count);\n"
    "    for i in 0..visibles_count {\n"
    "        let visible: id = msg![env; visibles objectAtIndex:i];\n"
    "        let class_name = env.objc.try_get_class_name(visible);\n"
    "        log!(\"Otamatone v5: visible window setHidden ENTER index={}/{} object={:?} class={:?}\", i, visibles_count, visible, class_name);\n"
    "        () = msg![env; visible setHidden:false];\n"
    "        log!(\"Otamatone v5: visible window setHidden EXIT  index={}/{} object={:?}\", i, visibles_count, visible);\n"
    "    }\n\n"
    "    log!(\"Otamatone v5: load_nib_file internal phases complete\");\n"
    "    Ok(unarchiver)\n",
)

# UIClassSwapper is the high-signal bridge from archived NIB objects to actual
# UIKit/app classes. Log every swap and whether the actual init/initWithCoder
# returns, which catches custom app classes that do not use initWithCoder:.
replace_once(
    "src/frameworks/uikit/ui_nib.rs",
    "    let class = env.objc.get_known_class(&name, &mut env.mem);\n\n"
    "    let object: id = msg![env; class alloc];\n"
    "    let object: id = if orig == \"UICustomObject\" {\n"
    "        msg![env; object init]\n"
    "    } else {\n"
    "        msg![env; object initWithCoder:coder]\n"
    "    };\n",
    "    log!(\"Otamatone v5: UIClassSwapper class={:?} original={:?} ENTER\", name, orig);\n"
    "    let class = env.objc.get_known_class(&name, &mut env.mem);\n\n"
    "    let object: id = msg![env; class alloc];\n"
    "    log!(\"Otamatone v5: UIClassSwapper allocated class={:?} object={:?}\", name, object);\n"
    "    let object: id = if orig == \"UICustomObject\" {\n"
    "        log!(\"Otamatone v5: UIClassSwapper init ENTER class={:?} object={:?}\", name, object);\n"
    "        let initialized: id = msg![env; object init];\n"
    "        log!(\"Otamatone v5: UIClassSwapper init EXIT  class={:?} object={:?} result={:?}\", name, object, initialized);\n"
    "        initialized\n"
    "    } else {\n"
    "        log!(\"Otamatone v5: UIClassSwapper initWithCoder ENTER class={:?} original={:?} object={:?}\", name, orig, object);\n"
    "        let initialized: id = msg![env; object initWithCoder:coder];\n"
    "        log!(\"Otamatone v5: UIClassSwapper initWithCoder EXIT  class={:?} object={:?} result={:?}\", name, object, initialized);\n"
    "        initialized\n"
    "    };\n"
    "    log!(\"Otamatone v5: UIClassSwapper class={:?} EXIT result={:?}\", name, object);\n",
)

# Trace plain -init too, but only for guest implementations during NIB startup.
# This catches UICustomObject paths without restoring the full ABI trace.
replace_once(
    "src/objc/messages.rs",
    '                            "initWithCoder:"\n',
    '                            "initWithCoder:"\n'
    '                            | "init"\n',
)

print("Applied Otamatone v5 NIB phase/UIClassSwapper tracer")

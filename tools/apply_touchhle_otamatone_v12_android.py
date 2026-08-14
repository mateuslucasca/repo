from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
V11 = Path(__file__).with_name("apply_touchhle_otamatone_v11_release3.py")
subprocess.run([sys.executable, str(V11), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# UIImageView created from a NIB used UIView's default opaque CALayer. That is
# wrong for PNG/CgBI images with alpha and causes fully transparent pixels to
# show the compositor's black clear colour. initWithFrame:/initWithImage:
# already force UIImageView non-opaque; do the same for initWithCoder:.
replace_once(
    "src/frameworks/uikit/ui_view/ui_image_view.rs",
    '''- (id)initWithCoder:(id)coder {
    let this: id = msg_super![env; this initWithCoder:coder];

    let key_ns_string = get_static_str(env, "UIImage");''',
    '''- (id)initWithCoder:(id)coder {
    let this: id = msg_super![env; this initWithCoder:coder];

    // UIImageView contents can contain alpha. UIView's common initializer
    // creates an opaque layer, so NIB-created image views must explicitly
    // match initWithFrame:/initWithImage: and disable the opaque fast path.
    () = msg![env; this setOpaque:false];

    let key_ns_string = get_static_str(env, "UIImage");''',
)

# Be defensive in Core Animation too. CGImage pixels are stored as premultiplied
# RGBA, so blending them is correct even if a legacy NIB accidentally marks the
# containing layer opaque. For fully opaque images this produces the same output
# and only costs a tiny amount of fill-rate.
replace_once(
    "src/frameworks/core_animation/composition.rs",
    '''        if opacity == 1.0 && host_obj.opaque && !have_background {
            gles.Disable(gles11::BLEND);
        } else {
            gles.Enable(gles11::BLEND);
            gles.BlendFunc(gles11::ONE, gles11::ONE_MINUS_SRC_ALPHA);
        }''',
    '''        if opacity == 1.0
            && host_obj.opaque
            && !have_background
            && host_obj.contents == nil
        {
            gles.Disable(gles11::BLEND);
        } else {
            // CGImage textures are premultiplied RGBA. Always blend layer
            // contents so transparent PNG/CgBI pixels remain transparent even
            // when an old archive incorrectly advertises an opaque view.
            gles.Enable(gles11::BLEND);
            gles.BlendFunc(gles11::ONE, gles11::ONE_MINUS_SRC_ALPHA);
        }''',
)

# Android's SDL backend already exposes the physical accelerometer through the
# Sensor subsystem. Make the path resilient to a temporarily unavailable sensor
# (pause/resume, vendor driver hiccups) instead of unwrapping and crashing.
replace_once(
    "src/window.rs",
    '''            if let Some(ref accelerometer) = self.accelerometer {
                let data = accelerometer.get_data().unwrap();
                let sdl2::sensor::SensorData::Accel(data) = data else {
                    panic!();
                };
                let [x, y, z] = data;
                // UIAcceleration reports acceleration towards gravity, but SDL2''',
    '''            if let Some(ref accelerometer) = self.accelerometer {
                if let Ok(sdl2::sensor::SensorData::Accel([x, y, z])) = accelerometer.get_data() {
                    // UIAcceleration reports acceleration towards gravity, but SDL2''',
)
replace_once(
    "src/window.rs",
    '''                let (x, y, z) = (x / gravity, y / gravity, z / gravity);
                return (x, y, z);
            }
        }

        let (x, y) = if self''',
    '''                    let (x, y, z) = (x / gravity, y / gravity, z / gravity);
                    return (x, y, z);
                }
                log_dbg!("Physical accelerometer sample unavailable; falling back to virtual tilt for this update");
            }
        }

        let (x, y) = if self''',
)

# Expose the source to UIAccelerometer so the log tells us immediately whether
# Android successfully attached to the real device sensor.
replace_once(
    "src/window.rs",
    '''    /// Get the real or simulated accelerometer output.
    /// See also [crate::frameworks::uikit::ui_accelerometer].
    pub fn get_acceleration(&self, options: &Options) -> (f32, f32, f32) {''',
    '''    /// Whether SDL exposed a physical accelerometer for this host.
    pub fn has_physical_accelerometer(&self) -> bool {
        self.accelerometer.is_some()
    }

    /// Get the real or simulated accelerometer output.
    /// See also [crate::frameworks::uikit::ui_accelerometer].
    pub fn get_acceleration(&self, options: &Options) -> (f32, f32, f32) {''',
)
replace_once(
    "src/frameworks/uikit/ui_accelerometer.rs",
    '''        if env.framework_state.uikit.ui_accelerometer.delegate != Some(delegate) {
            env.window().print_accelerometer_notice(&env.options);
        }
        env.framework_state.uikit.ui_accelerometer.delegate = Some(delegate);''',
    '''        if env.framework_state.uikit.ui_accelerometer.delegate != Some(delegate) {
            env.window().print_accelerometer_notice(&env.options);
            log!(
                "UIAccelerometer enabled; physical host sensor available: {}",
                env.window().has_physical_accelerometer()
            );
        }
        env.framework_state.uikit.ui_accelerometer.delegate = Some(delegate);''',
)

# Tell SDL/Android not to repurpose the phone accelerometer as a joystick, and
# advertise accelerometer support without excluding devices that lack one.
replace_once(
    "android/app/src/main/AndroidManifest.xml",
    '''    <!-- Touchscreen support -->
    <uses-feature
        android:name="android.hardware.touchscreen"
        android:required="false" />''',
    '''    <!-- Touchscreen support -->
    <uses-feature
        android:name="android.hardware.touchscreen"
        android:required="false" />

    <!-- Otamatone uses legacy UIAccelerometer. SDL's Sensor subsystem bridges
         this Android hardware sensor to touchHLE. -->
    <uses-feature
        android:name="android.hardware.sensor.accelerometer"
        android:required="false" />''',
)
replace_once(
    "android/app/src/main/AndroidManifest.xml",
    '''        <!-- Example of setting SDL hints from AndroidManifest.xml:
        <meta-data android:name="SDL_ENV.SDL_ACCELEROMETER_AS_JOYSTICK" android:value="0"/>
         -->''',
    '''        <!-- Keep the Android accelerometer in SDL's Sensor subsystem
             instead of exposing it as a fake joystick. -->
        <meta-data
            android:name="SDL_ENV.SDL_ACCELEROMETER_AS_JOYSTICK"
            android:value="0" />''',
)

# Give this experimental APK its own package/name so it can coexist with an
# official touchHLE Android installation.
replace_once(
    "android/app/build.gradle.kts",
    'applicationId = "org.touchhle.android"',
    'applicationId = "org.touchhle.android.otamatonev12"',
)
replace_once(
    "android/app/build.gradle.kts",
    'resValue("string", "app_name", join("touchHLE", " ", branding))',
    'resValue("string", "app_name", "touchHLE Otamatone v12")',
)

print("Applied Otamatone v12 Android accelerometer + transparent-image compatibility patch")

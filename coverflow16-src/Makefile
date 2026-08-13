ARCHS = arm64
TARGET = iphone:clang:latest:16.0
THEOS_PACKAGE_SCHEME = rootless
INSTALL_TARGET_PROCESSES = Music

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = CoverFlow16
CoverFlow16_FILES = Tweak.m
CoverFlow16_FRAMEWORKS = UIKit MediaPlayer QuartzCore CoreMotion
CoverFlow16_CFLAGS = -fobjc-arc -Wall -Wextra -Wno-error=deprecated-declarations

include $(THEOS_MAKE_PATH)/tweak.mk

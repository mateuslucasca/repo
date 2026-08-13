#import <UIKit/UIKit.h>
#import <objc/runtime.h>

static BOOL CF16SafeItemIsNowPlaying(id self, SEL _cmd, id item) {
    (void)self; (void)_cmd; (void)item;
    return NO;
}

static void CF16SafeTrackSelection(id self, SEL _cmd, UITableView *tableView, NSIndexPath *indexPath) {
    (void)self; (void)_cmd;
    [tableView deselectRowAtIndexPath:indexPath animated:YES];
    NSLog(@"[CoverFlow16] 0.2.1: track playback temporarily disabled while isolating Music.app crash");
}

__attribute__((constructor)) static void CF16InstallAlbumCrashHotfix(void) {
    @autoreleasepool {
        Class cls=NSClassFromString(@"CF16Manager");
        if (!cls) return;

        SEL nowSel=NSSelectorFromString(@"itemIsNowPlaying:");
        Method nowMethod=class_getInstanceMethod(cls, nowSel);
        if (nowMethod) {
            class_replaceMethod(cls, nowSel, (IMP)CF16SafeItemIsNowPlaying, method_getTypeEncoding(nowMethod));
        }

        SEL selectSel=@selector(tableView:didSelectRowAtIndexPath:);
        Method selectMethod=class_getInstanceMethod(cls, selectSel);
        if (selectMethod) {
            class_replaceMethod(cls, selectSel, (IMP)CF16SafeTrackSelection, method_getTypeEncoding(selectMethod));
        }
    }
}

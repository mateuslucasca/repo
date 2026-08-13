#import <UIKit/UIKit.h>
#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#import <dlfcn.h>

// MediaRemote is private, so every symbol is resolved dynamically. If Apple changes
// a symbol, the module simply disables itself instead of preventing Music from opening.
typedef void (*CF16MRRegisterFn)(dispatch_queue_t queue);
typedef void (*CF16MRGetInfoFn)(dispatch_queue_t queue, void (^completion)(CFDictionaryRef information));
typedef Boolean (*CF16MRSendCommandFn)(unsigned int command, CFDictionaryRef options);

static NSString *CF16MRString(void *handle, const char *symbol) {
    if (!handle) return nil;
    CFStringRef *ptr=(CFStringRef *)dlsym(handle,symbol);
    if (!ptr || !*ptr) return nil;
    return (__bridge NSString *)(*ptr);
}

static id CF16MRValue(NSDictionary *info, void *handle, const char *symbol) {
    NSString *key=CF16MRString(handle,symbol);
    return key ? info[key] : nil;
}

@interface CF16NowPlayingBridge : NSObject
@property(nonatomic,weak) id manager;
@property(nonatomic,strong) UIView *bar;
@property(nonatomic,strong) UIImageView *artwork;
@property(nonatomic,strong) UILabel *titleLabel;
@property(nonatomic,strong) UILabel *detailLabel;
@property(nonatomic,strong) UIButton *previousButton;
@property(nonatomic,strong) UIButton *toggleButton;
@property(nonatomic,strong) UIButton *nextButton;
@property(nonatomic,assign) void *mrHandle;
@property(nonatomic,assign) CF16MRRegisterFn mrRegister;
@property(nonatomic,assign) CF16MRGetInfoFn mrGetInfo;
@property(nonatomic,assign) CF16MRSendCommandFn mrSendCommand;
@property(nonatomic,assign) BOOL mediaRemoteStarted;
+ (instancetype)shared;
- (void)attachToManager:(id)manager;
- (void)layoutForManager:(id)manager;
@end

@implementation CF16NowPlayingBridge
+ (instancetype)shared {
    static CF16NowPlayingBridge *bridge;
    static dispatch_once_t once;
    dispatch_once(&once, ^{ bridge=[CF16NowPlayingBridge new]; });
    return bridge;
}

- (UIImage *)symbol:(NSString *)name size:(CGFloat)size {
    UIImageSymbolConfiguration *cfg=[UIImageSymbolConfiguration configurationWithPointSize:size weight:UIImageSymbolWeightSemibold];
    return [UIImage systemImageNamed:name withConfiguration:cfg];
}

- (UIButton *)controlButton:(NSString *)symbol action:(SEL)action {
    UIButton *button=[UIButton buttonWithType:UIButtonTypeSystem];
    [button setTintColor:UIColor.whiteColor];
    [button setImage:[self symbol:symbol size:16] forState:UIControlStateNormal];
    [button addTarget:self action:action forControlEvents:UIControlEventTouchUpInside];
    button.accessibilityLabel=symbol;
    return button;
}

- (void)attachToManager:(id)manager {
    self.manager=manager;
    UIView *canvas=nil;
    @try { canvas=[manager valueForKey:@"canvas"]; } @catch (__unused NSException *e) {}
    if (!canvas) return;

    if (!self.bar) {
        self.bar=[UIView new];
        self.bar.backgroundColor=[UIColor colorWithWhite:1 alpha:.065];
        self.bar.layer.cornerRadius=9;
        self.bar.layer.borderWidth=.5;
        self.bar.layer.borderColor=[UIColor colorWithWhite:1 alpha:.11].CGColor;
        self.bar.clipsToBounds=YES;

        self.artwork=[UIImageView new];
        self.artwork.contentMode=UIViewContentModeScaleAspectFill;
        self.artwork.clipsToBounds=YES;
        self.artwork.layer.cornerRadius=5;
        self.artwork.backgroundColor=[UIColor colorWithWhite:1 alpha:.07];
        [self.bar addSubview:self.artwork];

        self.titleLabel=[UILabel new];
        self.titleLabel.textColor=UIColor.whiteColor;
        self.titleLabel.font=[UIFont systemFontOfSize:13 weight:UIFontWeightSemibold];
        self.titleLabel.lineBreakMode=NSLineBreakByTruncatingTail;
        self.titleLabel.text=@"Nothing Playing";
        [self.bar addSubview:self.titleLabel];

        self.detailLabel=[UILabel new];
        self.detailLabel.textColor=[UIColor colorWithWhite:1 alpha:.52];
        self.detailLabel.font=[UIFont systemFontOfSize:10.5 weight:UIFontWeightRegular];
        self.detailLabel.lineBreakMode=NSLineBreakByTruncatingTail;
        self.detailLabel.text=@"Music";
        [self.bar addSubview:self.detailLabel];

        self.previousButton=[self controlButton:@"backward.fill" action:@selector(previous:)];
        self.toggleButton=[self controlButton:@"play.fill" action:@selector(toggle:)];
        self.nextButton=[self controlButton:@"forward.fill" action:@selector(next:)];
        [self.bar addSubview:self.previousButton];
        [self.bar addSubview:self.toggleButton];
        [self.bar addSubview:self.nextButton];
    }

    if (self.bar.superview!=canvas) {
        [self.bar removeFromSuperview];
        [canvas addSubview:self.bar];
    }

    [self startMediaRemoteIfNeeded];
    [self refresh];
}

- (void)layoutForManager:(id)manager {
    UIView *canvas=nil;
    UICollectionView *collection=nil;
    @try {
        canvas=[manager valueForKey:@"canvas"];
        collection=[manager valueForKey:@"collection"];
    } @catch (__unused NSException *e) {}
    if (!canvas || !self.bar) return;

    CGFloat width=CGRectGetWidth(canvas.bounds);
    self.bar.frame=CGRectMake(12,34,MAX(120,width-24),42);
    self.artwork.frame=CGRectMake(4,4,34,34);

    CGFloat right=6;
    CGFloat buttonW=36;
    self.nextButton.frame=CGRectMake(CGRectGetWidth(self.bar.bounds)-right-buttonW,3,buttonW,36);
    self.toggleButton.frame=CGRectMake(CGRectGetMinX(self.nextButton.frame)-buttonW,3,buttonW,36);
    self.previousButton.frame=CGRectMake(CGRectGetMinX(self.toggleButton.frame)-buttonW,3,buttonW,36);

    CGFloat textX=44;
    CGFloat textRight=CGRectGetMinX(self.previousButton.frame)-5;
    CGFloat textW=MAX(20,textRight-textX);
    self.titleLabel.frame=CGRectMake(textX,5,textW,17);
    self.detailLabel.frame=CGRectMake(textX,22,textW,14);

    // The stable 0.2.1 layout starts the Cover Flow at y=35. Move it down only
    // enough for the Now Playing strip, keeping the album labels untouched.
    if (collection) {
        CGRect f=collection.frame;
        if (f.origin.y < 70) {
            CGFloat delta=42;
            f.origin.y += delta;
            f.size.height=MAX(140,f.size.height-delta);
            collection.frame=f;
        }
    }

    [canvas bringSubviewToFront:self.bar];
    @try {
        UIView *trackPanel=[manager valueForKey:@"trackPanel"];
        NSNumber *showing=[manager valueForKey:@"showingTracks"];
        if (trackPanel && showing.boolValue) [canvas bringSubviewToFront:trackPanel];
    } @catch (__unused NSException *e) {}
}

- (void)startMediaRemoteIfNeeded {
    if (self.mediaRemoteStarted) return;
    self.mediaRemoteStarted=YES;

    self.mrHandle=dlopen("/System/Library/PrivateFrameworks/MediaRemote.framework/MediaRemote",RTLD_LAZY|RTLD_LOCAL);
    if (!self.mrHandle) {
        NSLog(@"[CoverFlow16] 0.3: MediaRemote unavailable");
        self.previousButton.enabled=NO;
        self.toggleButton.enabled=NO;
        self.nextButton.enabled=NO;
        return;
    }

    self.mrRegister=(CF16MRRegisterFn)dlsym(self.mrHandle,"MRMediaRemoteRegisterForNowPlayingNotifications");
    self.mrGetInfo=(CF16MRGetInfoFn)dlsym(self.mrHandle,"MRMediaRemoteGetNowPlayingInfo");
    self.mrSendCommand=(CF16MRSendCommandFn)dlsym(self.mrHandle,"MRMediaRemoteSendCommand");

    if (self.mrRegister) self.mrRegister(dispatch_get_main_queue());

    NSArray<NSString *> *notificationSymbols=@[
        @"kMRMediaRemoteNowPlayingInfoDidChangeNotification",
        @"kMRMediaRemoteNowPlayingApplicationDidChangeNotification",
        @"kMRMediaRemoteNowPlayingPlaybackQueueDidChangeNotification"
    ];
    for (NSString *symbol in notificationSymbols) {
        NSString *name=CF16MRString(self.mrHandle,symbol.UTF8String);
        if (name.length) [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(mediaRemoteChanged:) name:name object:nil];
    }

    BOOL ready=(self.mrGetInfo && self.mrSendCommand);
    self.previousButton.enabled=ready;
    self.toggleButton.enabled=ready;
    self.nextButton.enabled=ready;
    NSLog(@"[CoverFlow16] 0.3: MediaRemote %@",ready?@"ready":@"partially unavailable");
}

- (void)mediaRemoteChanged:(NSNotification *)notification {
    (void)notification;
    [self refresh];
}

- (void)refresh {
    if (!self.mrGetInfo) return;
    __weak typeof(self) weakSelf=self;
    self.mrGetInfo(dispatch_get_main_queue(),^(CFDictionaryRef information){
        typeof(self) selfRef=weakSelf;
        if (!selfRef) return;
        NSDictionary *info=information ? [(__bridge NSDictionary *)information copy] : @{};
        [selfRef applyInfo:info];
    });
}

- (void)applyInfo:(NSDictionary *)info {
    NSString *title=CF16MRValue(info,self.mrHandle,"kMRMediaRemoteNowPlayingInfoTitle");
    NSString *artist=CF16MRValue(info,self.mrHandle,"kMRMediaRemoteNowPlayingInfoArtist");
    NSString *album=CF16MRValue(info,self.mrHandle,"kMRMediaRemoteNowPlayingInfoAlbum");
    NSNumber *rate=CF16MRValue(info,self.mrHandle,"kMRMediaRemoteNowPlayingInfoPlaybackRate");
    id art=CF16MRValue(info,self.mrHandle,"kMRMediaRemoteNowPlayingInfoArtworkData");

    self.titleLabel.text=title.length?title:@"Nothing Playing";
    if (artist.length && album.length) self.detailLabel.text=[NSString stringWithFormat:@"%@  •  %@",artist,album];
    else if (artist.length) self.detailLabel.text=artist;
    else if (album.length) self.detailLabel.text=album;
    else self.detailLabel.text=@"Music";

    BOOL playing=rate.doubleValue>0.01;
    [self.toggleButton setImage:[self symbol:(playing?@"pause.fill":@"play.fill") size:16] forState:UIControlStateNormal];

    UIImage *image=nil;
    if ([art isKindOfClass:NSData.class]) image=[UIImage imageWithData:art];
    else if ([art isKindOfClass:UIImage.class]) image=art;
    self.artwork.image=image ?: [self symbol:@"music.note" size:17];
    self.artwork.contentMode=image?UIViewContentModeScaleAspectFill:UIViewContentModeCenter;
}

- (void)sendCommand:(unsigned int)command {
    if (!self.mrSendCommand) return;
    self.mrSendCommand(command,NULL);
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(0.12*NSEC_PER_SEC)),dispatch_get_main_queue(),^{ [self refresh]; });
}

- (void)previous:(id)sender { (void)sender; [self sendCommand:5]; }
- (void)toggle:(id)sender { (void)sender; [self sendCommand:2]; }
- (void)next:(id)sender { (void)sender; [self sendCommand:4]; }
@end

static IMP CF16OriginalBuild=nil;
static IMP CF16OriginalLayout=nil;

static void CF16BuildWithNowPlaying(id self, SEL _cmd, UIWindow *window) {
    ((void(*)(id,SEL,UIWindow *))CF16OriginalBuild)(self,_cmd,window);
    [[CF16NowPlayingBridge shared] attachToManager:self];
}

static void CF16LayoutWithNowPlaying(id self, SEL _cmd, UIWindow *window, UIDeviceOrientation orientation) {
    ((void(*)(id,SEL,UIWindow *,UIDeviceOrientation))CF16OriginalLayout)(self,_cmd,window,orientation);
    [[CF16NowPlayingBridge shared] layoutForManager:self];
}

__attribute__((constructor)) static void CF16InstallNowPlayingModule(void) {
    @autoreleasepool {
        Class cls=NSClassFromString(@"CF16Manager");
        if (!cls) return;

        Method build=class_getInstanceMethod(cls,NSSelectorFromString(@"build:"));
        Method layout=class_getInstanceMethod(cls,NSSelectorFromString(@"layoutForWindow:orientation:"));
        if (!build || !layout) return;

        CF16OriginalBuild=method_getImplementation(build);
        CF16OriginalLayout=method_getImplementation(layout);
        method_setImplementation(build,(IMP)CF16BuildWithNowPlaying);
        method_setImplementation(layout,(IMP)CF16LayoutWithNowPlaying);
    }
}

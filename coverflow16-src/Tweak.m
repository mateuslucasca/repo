#import <UIKit/UIKit.h>
#import <MediaPlayer/MediaPlayer.h>
#import <QuartzCore/QuartzCore.h>

@interface CF16Card : UIView
@property(nonatomic,strong) UIImageView *art;
@property(nonatomic,strong) UIImageView *reflection;
@property(nonatomic,assign) NSInteger index;
@end
@implementation CF16Card @end

@interface CF16Manager : NSObject <UIScrollViewDelegate>
@property(nonatomic,strong) UIView *overlay;
@property(nonatomic,strong) UIView *canvas;
@property(nonatomic,strong) UIScrollView *scroll;
@property(nonatomic,strong) UILabel *albumLabel;
@property(nonatomic,strong) UILabel *artistLabel;
@property(nonatomic,strong) UILabel *emptyLabel;
@property(nonatomic,strong) NSArray<MPMediaItemCollection *> *albums;
@property(nonatomic,strong) NSMutableArray<CF16Card *> *cards;
@property(nonatomic,assign) CGFloat coverSize;
@property(nonatomic,assign) CGFloat spacing;
@property(nonatomic,assign) NSInteger selected;
@property(nonatomic,assign) BOOL dismissed;
+ (instancetype)shared;
- (void)start;
@end

@implementation CF16Manager
+ (instancetype)shared {
    static CF16Manager *m; static dispatch_once_t once;
    dispatch_once(&once, ^{ m=[CF16Manager new]; m.cards=[NSMutableArray array]; m.selected=NSNotFound; });
    return m;
}
- (void)log:(NSString *)s { NSLog(@"[CoverFlow16] %@", s); }
- (void)start {
    [self log:@"loaded into Music"];
    [UIDevice.currentDevice beginGeneratingDeviceOrientationNotifications];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(rotated:) name:UIDeviceOrientationDidChangeNotification object:nil];
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(0.35*NSEC_PER_SEC)),dispatch_get_main_queue(),^{ [self rotated:nil]; });
}
- (UIWindow *)keyWindow {
    for (UIScene *scene in UIApplication.sharedApplication.connectedScenes) {
        if (![scene isKindOfClass:UIWindowScene.class]) continue;
        UIWindowScene *ws=(UIWindowScene *)scene;
        for (UIWindow *w in ws.windows) if (w.isKeyWindow) return w;
    }
    for (UIWindow *w in UIApplication.sharedApplication.windows) if (w.isKeyWindow) return w;
    return UIApplication.sharedApplication.windows.firstObject;
}
- (void)rotated:(NSNotification *)n {
    (void)n; UIDeviceOrientation o=UIDevice.currentDevice.orientation;
    if (UIDeviceOrientationIsLandscape(o)) { if (!self.dismissed) [self show:o]; return; }
    if (o==UIDeviceOrientationPortrait || o==UIDeviceOrientationPortraitUpsideDown) { self.dismissed=NO; [self hide:YES]; }
}
- (void)show:(UIDeviceOrientation)o {
    UIWindow *w=[self keyWindow];
    if (!w) return;
    if (!self.overlay) [self build:w];
    if (self.overlay.superview!=w) { [self.overlay removeFromSuperview]; [w addSubview:self.overlay]; }
    [self layout:w orientation:o];
    self.overlay.hidden=NO; self.overlay.alpha=1.0; [w bringSubviewToFront:self.overlay];
}
- (void)build:(UIWindow *)w {
    self.overlay=[[UIView alloc] initWithFrame:w.bounds]; self.overlay.backgroundColor=UIColor.blackColor; self.overlay.clipsToBounds=YES;
    self.canvas=[UIView new]; self.canvas.backgroundColor=UIColor.blackColor; self.canvas.clipsToBounds=YES; [self.overlay addSubview:self.canvas];
    UILabel *title=[UILabel new]; title.tag=1601; title.text=@"Cover Flow"; title.textColor=UIColor.whiteColor; title.alpha=.72; title.font=[UIFont systemFontOfSize:13 weight:UIFontWeightSemibold]; title.textAlignment=NSTextAlignmentCenter; [self.canvas addSubview:title];
    UIButton *close=[UIButton buttonWithType:UIButtonTypeSystem]; close.tag=1602; [close setTitle:@"×" forState:UIControlStateNormal]; close.titleLabel.font=[UIFont systemFontOfSize:30 weight:UIFontWeightLight]; [close setTitleColor:[UIColor colorWithWhite:1 alpha:.78] forState:UIControlStateNormal]; [close addTarget:self action:@selector(close:) forControlEvents:UIControlEventTouchUpInside]; [self.canvas addSubview:close];
    self.scroll=[UIScrollView new]; self.scroll.delegate=self; self.scroll.backgroundColor=UIColor.clearColor; self.scroll.showsHorizontalScrollIndicator=NO; self.scroll.decelerationRate=UIScrollViewDecelerationRateFast; self.scroll.clipsToBounds=NO; [self.canvas addSubview:self.scroll];
    self.albumLabel=[UILabel new]; self.albumLabel.textColor=UIColor.whiteColor; self.albumLabel.font=[UIFont systemFontOfSize:17 weight:UIFontWeightSemibold]; self.albumLabel.textAlignment=NSTextAlignmentCenter; [self.canvas addSubview:self.albumLabel];
    self.artistLabel=[UILabel new]; self.artistLabel.textColor=[UIColor colorWithWhite:1 alpha:.62]; self.artistLabel.font=[UIFont systemFontOfSize:13]; self.artistLabel.textAlignment=NSTextAlignmentCenter; [self.canvas addSubview:self.artistLabel];
    self.emptyLabel=[UILabel new]; self.emptyLabel.text=@"No albums found\nin the local media library"; self.emptyLabel.textColor=[UIColor colorWithWhite:1 alpha:.65]; self.emptyLabel.textAlignment=NSTextAlignmentCenter; self.emptyLabel.numberOfLines=2; [self.canvas addSubview:self.emptyLabel];
    [w addSubview:self.overlay]; [self reloadAlbums];
}
- (void)layout:(UIWindow *)w orientation:(UIDeviceOrientation)o {
    self.overlay.frame=w.bounds;
    CGFloat pw=MAX(CGRectGetWidth(w.bounds),CGRectGetHeight(w.bounds)), ph=MIN(CGRectGetWidth(w.bounds),CGRectGetHeight(w.bounds));
    self.canvas.bounds=CGRectMake(0,0,pw,ph); self.canvas.center=CGPointMake(CGRectGetMidX(self.overlay.bounds),CGRectGetMidY(self.overlay.bounds));
    if (CGRectGetWidth(w.bounds)>CGRectGetHeight(w.bounds)) self.canvas.transform=CGAffineTransformIdentity;
    else self.canvas.transform=CGAffineTransformMakeRotation(o==UIDeviceOrientationLandscapeLeft ? -M_PI_2 : M_PI_2);
    [self.canvas viewWithTag:1601].frame=CGRectMake((pw-180)/2,7,180,24); [self.canvas viewWithTag:1602].frame=CGRectMake(pw-52,1,48,42);
    self.coverSize=MIN(210,MAX(132,floor(ph*.53))); self.spacing=MAX(92,floor(self.coverSize*.64));
    self.scroll.frame=CGRectMake(0,34,pw,MAX(180,ph-86)); self.albumLabel.frame=CGRectMake(48,ph-50,pw-96,23); self.artistLabel.frame=CGRectMake(48,ph-28,pw-96,18); self.emptyLabel.frame=CGRectMake(30,80,pw-60,ph-150);
    [self rebuild];
}
- (void)reloadAlbums {
    @try { self.albums=[MPMediaQuery albumsQuery].collections ?: @[]; [self log:[NSString stringWithFormat:@"%lu albums",(unsigned long)self.albums.count]]; }
    @catch (NSException *e) { self.albums=@[]; [self log:[NSString stringWithFormat:@"query failed: %@",e.reason]]; }
    [self rebuild];
}
- (UIImage *)placeholder:(CGSize)s {
    UIGraphicsBeginImageContextWithOptions(s,YES,0); [[UIColor colorWithWhite:.12 alpha:1] setFill]; UIRectFill(CGRectMake(0,0,s.width,s.height));
    UIImageSymbolConfiguration *cfg=[UIImageSymbolConfiguration configurationWithPointSize:s.width*.28 weight:UIImageSymbolWeightLight]; UIImage *im=[UIImage systemImageNamed:@"music.note" withConfiguration:cfg]; [im drawInRect:CGRectMake(s.width*.34,s.height*.34,s.width*.32,s.height*.32) blendMode:kCGBlendModeNormal alpha:.8];
    UIImage *r=UIGraphicsGetImageFromCurrentImageContext(); UIGraphicsEndImageContext(); return r;
}
- (UIImage *)artFor:(MPMediaItemCollection *)c size:(CGSize)s {
    MPMediaItem *i=c.representativeItem ?: c.items.firstObject; MPMediaItemArtwork *a=[i valueForProperty:MPMediaItemPropertyArtwork]; return [a imageWithSize:s] ?: [self placeholder:s];
}
- (void)rebuild {
    if (!self.scroll || self.coverSize<1) return;
    for (UIView *v in self.cards) [v removeFromSuperview]; [self.cards removeAllObjects];
    NSUInteger count=self.albums.count; self.emptyLabel.hidden=(count!=0);
    if (!count) { self.scroll.contentSize=self.scroll.bounds.size; self.albumLabel.text=@""; self.artistLabel.text=@""; return; }
    CGFloat sw=CGRectGetWidth(self.scroll.bounds), sh=CGRectGetHeight(self.scroll.bounds), inset=MAX(0,(sw-self.coverSize)/2), rh=floor(self.coverSize*.28), top=MAX(3,floor((sh-self.coverSize-rh)*.42));
    self.scroll.contentSize=CGSizeMake(inset*2+self.coverSize+self.spacing*(count-1),sh);
    CGSize req=CGSizeMake(self.coverSize*2,self.coverSize*2);
    for (NSUInteger idx=0; idx<count; idx++) {
        CGFloat x=inset+self.spacing*idx; CF16Card *c=[[CF16Card alloc] initWithFrame:CGRectMake(x,top,self.coverSize,self.coverSize+rh+5)]; c.index=idx; c.backgroundColor=UIColor.clearColor;
        UIImage *art=[self artFor:self.albums[idx] size:req]; UIImageView *iv=[[UIImageView alloc] initWithFrame:CGRectMake(0,0,self.coverSize,self.coverSize)]; iv.image=art; iv.contentMode=UIViewContentModeScaleAspectFill; iv.clipsToBounds=YES; iv.layer.cornerRadius=3; iv.layer.borderWidth=.5; iv.layer.borderColor=[UIColor colorWithWhite:1 alpha:.15].CGColor; iv.layer.shadowColor=UIColor.blackColor.CGColor; iv.layer.shadowOpacity=.75; iv.layer.shadowRadius=12; iv.layer.shadowOffset=CGSizeMake(0,7); [c addSubview:iv]; c.art=iv;
        UIImageView *rf=[[UIImageView alloc] initWithFrame:CGRectMake(0,self.coverSize+3,self.coverSize,rh)]; rf.image=art; rf.contentMode=UIViewContentModeScaleAspectFill; rf.clipsToBounds=YES; rf.alpha=.22; rf.transform=CGAffineTransformMakeScale(1,-1); CAGradientLayer *fade=[CAGradientLayer layer]; fade.frame=rf.bounds; fade.colors=@[(id)[UIColor colorWithWhite:1 alpha:.72].CGColor,(id)[UIColor colorWithWhite:1 alpha:0].CGColor]; fade.startPoint=CGPointMake(.5,0); fade.endPoint=CGPointMake(.5,1); rf.layer.mask=fade; [c addSubview:rf]; c.reflection=rf;
        [c addGestureRecognizer:[[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(tapped:)]]; [self.scroll addSubview:c]; [self.cards addObject:c];
    }
    NSInteger i=(self.selected==NSNotFound || self.selected<0 || self.selected>=(NSInteger)count)?0:self.selected; [self select:i animated:NO];
}
- (NSInteger)nearest { if (!self.albums.count || self.spacing<=0) return NSNotFound; NSInteger i=llround(self.scroll.contentOffset.x/self.spacing); return MAX(0,MIN(i,(NSInteger)self.albums.count-1)); }
- (void)select:(NSInteger)i animated:(BOOL)a {
    if (i==NSNotFound || i<0 || i>=(NSInteger)self.albums.count) return; self.selected=i; CGFloat max=MAX(0,self.scroll.contentSize.width-CGRectGetWidth(self.scroll.bounds)); CGFloat x=MAX(0,MIN(i*self.spacing,max)); [self.scroll setContentOffset:CGPointMake(x,0) animated:a]; [self labels:i]; [self transforms];
}
- (void)labels:(NSInteger)i { MPMediaItemCollection *c=self.albums[i]; MPMediaItem *m=c.representativeItem ?: c.items.firstObject; NSString *al=[m valueForProperty:MPMediaItemPropertyAlbumTitle]; NSString *ar=[m valueForProperty:MPMediaItemPropertyAlbumArtist]; if (!ar.length) ar=[m valueForProperty:MPMediaItemPropertyArtist]; self.albumLabel.text=al.length?al:@"Unknown Album"; self.artistLabel.text=ar.length?ar:@"Unknown Artist"; }
- (void)transforms {
    CGFloat cx=self.scroll.contentOffset.x+CGRectGetWidth(self.scroll.bounds)/2; NSInteger near=[self nearest]; if (near!=NSNotFound && near!=self.selected) { self.selected=near; [self labels:near]; }
    for (CF16Card *c in self.cards) { CGFloat n=(CGRectGetMidX(c.frame)-cx)/self.spacing, an=MIN(2.5,fabs(n)); CATransform3D t=CATransform3DIdentity; t.m34=-1.0/650.0; if (fabs(n)<.16) { c.layer.zPosition=1000; c.alpha=1; } else { CGFloat s=n<0?-1:1, scale=MAX(.76,.88-an*.035); t=CATransform3DTranslate(t,s*-self.coverSize*.08,0,-MIN(160,an*55)); t=CATransform3DRotate(t,-s*(M_PI*.34),0,1,0); t=CATransform3DScale(t,scale,scale,1); c.layer.zPosition=500-an*20; c.alpha=MAX(.62,1-an*.07); } c.layer.transform=t; }
}
- (void)tapped:(UITapGestureRecognizer *)g { CF16Card *c=(CF16Card *)g.view; if ([c isKindOfClass:CF16Card.class]) [self select:c.index animated:YES]; }
- (void)close:(id)sender { (void)sender; self.dismissed=YES; [self hide:YES]; }
- (void)hide:(BOOL)a { if (!self.overlay || self.overlay.hidden) return; if (!a) { self.overlay.hidden=YES; return; } [UIView animateWithDuration:.16 animations:^{ self.overlay.alpha=0; } completion:^(BOOL f){ (void)f; self.overlay.hidden=YES; self.overlay.alpha=1; }]; }
- (void)scrollViewDidScroll:(UIScrollView *)s { (void)s; [self transforms]; }
- (void)scrollViewDidEndDecelerating:(UIScrollView *)s { (void)s; [self select:[self nearest] animated:YES]; }
- (void)scrollViewDidEndDragging:(UIScrollView *)s willDecelerate:(BOOL)d { (void)s; if (!d) [self select:[self nearest] animated:YES]; }
@end

__attribute__((constructor)) static void CF16Init(void) {
    @autoreleasepool {
        if (![NSBundle.mainBundle.bundleIdentifier isEqualToString:@"com.apple.Music"]) return;
        dispatch_async(dispatch_get_main_queue(), ^{ [[CF16Manager shared] start]; });
    }
}

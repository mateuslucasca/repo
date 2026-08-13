#import <UIKit/UIKit.h>
#import <MediaPlayer/MediaPlayer.h>
#import <QuartzCore/QuartzCore.h>

@interface CF16Cell : UICollectionViewCell
@property(nonatomic,strong) UIImageView *art;
@property(nonatomic,strong) UIImageView *reflection;
@property(nonatomic,strong) CAGradientLayer *fade;
@property(nonatomic,assign) NSInteger representedIndex;
@property(nonatomic,assign) CGFloat coverSize;
@property(nonatomic,assign) CGFloat reflectionHeight;
@end

@implementation CF16Cell
- (instancetype)initWithFrame:(CGRect)frame {
    self=[super initWithFrame:frame];
    if (self) {
        self.clipsToBounds=NO;
        self.contentView.clipsToBounds=NO;
        self.backgroundColor=UIColor.clearColor;
        self.contentView.backgroundColor=UIColor.clearColor;
        self.representedIndex=NSNotFound;

        self.art=[UIImageView new];
        self.art.contentMode=UIViewContentModeScaleAspectFill;
        self.art.clipsToBounds=YES;
        self.art.layer.cornerRadius=3.0;
        self.art.layer.borderWidth=0.5;
        self.art.layer.borderColor=[UIColor colorWithWhite:1 alpha:.15].CGColor;
        [self.contentView addSubview:self.art];

        self.reflection=[UIImageView new];
        self.reflection.contentMode=UIViewContentModeScaleAspectFill;
        self.reflection.clipsToBounds=YES;
        self.reflection.alpha=.20;
        self.reflection.transform=CGAffineTransformMakeScale(1,-1);
        [self.contentView addSubview:self.reflection];

        self.fade=[CAGradientLayer layer];
        self.fade.colors=@[(id)[UIColor colorWithWhite:1 alpha:.70].CGColor,
                           (id)[UIColor colorWithWhite:1 alpha:0].CGColor];
        self.fade.startPoint=CGPointMake(.5,0);
        self.fade.endPoint=CGPointMake(.5,1);
        self.reflection.layer.mask=self.fade;
    }
    return self;
}
- (void)prepareForReuse {
    [super prepareForReuse];
    self.representedIndex=NSNotFound;
    self.art.image=nil;
    self.reflection.image=nil;
    self.layer.transform=CATransform3DIdentity;
    self.layer.zPosition=0;
    self.alpha=1;
}
- (void)layoutSubviews {
    [super layoutSubviews];
    CGFloat x=floor((CGRectGetWidth(self.bounds)-self.coverSize)/2.0);
    self.art.frame=CGRectMake(x,0,self.coverSize,self.coverSize);
    self.reflection.frame=CGRectMake(x,self.coverSize+3,self.coverSize,self.reflectionHeight);
    self.fade.frame=self.reflection.bounds;
}
@end

@interface CF16Manager : NSObject <UICollectionViewDataSource, UICollectionViewDelegate, UIScrollViewDelegate>
@property(nonatomic,strong) UIView *overlay;
@property(nonatomic,strong) UIView *canvas;
@property(nonatomic,strong) UICollectionView *collection;
@property(nonatomic,strong) UICollectionViewFlowLayout *flow;
@property(nonatomic,strong) UILabel *albumLabel;
@property(nonatomic,strong) UILabel *artistLabel;
@property(nonatomic,strong) UILabel *emptyLabel;
@property(nonatomic,strong) NSArray<MPMediaItemCollection *> *albums;
@property(nonatomic,strong) NSCache<NSNumber *, UIImage *> *artCache;
@property(nonatomic,strong) NSOperationQueue *artQueue;
@property(nonatomic,strong) UIImage *placeholder;
@property(nonatomic,assign) CGFloat coverSize;
@property(nonatomic,assign) CGFloat stride;
@property(nonatomic,assign) CGFloat reflectionHeight;
@property(nonatomic,assign) NSInteger selected;
@property(nonatomic,assign) BOOL dismissed;
@property(nonatomic,assign) BOOL libraryLoaded;
@property(nonatomic,assign) UIDeviceOrientation displayedOrientation;
+ (instancetype)shared;
- (void)start;
@end

@implementation CF16Manager
+ (instancetype)shared {
    static CF16Manager *m;
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        m=[CF16Manager new];
        m.selected=0;
        m.displayedOrientation=UIDeviceOrientationUnknown;
        m.artCache=[NSCache new];
        m.artCache.countLimit=48;
        m.artQueue=[NSOperationQueue new];
        m.artQueue.maxConcurrentOperationCount=1;
        m.artQueue.qualityOfService=NSQualityOfServiceUserInitiated;
    });
    return m;
}

- (void)log:(NSString *)s { NSLog(@"[CoverFlow16] %@",s); }

- (void)start {
    [self log:@"loaded into Music"];
    [UIDevice.currentDevice beginGeneratingDeviceOrientationNotifications];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(rotated:) name:UIDeviceOrientationDidChangeNotification object:nil];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(appActive:) name:UIApplicationDidBecomeActiveNotification object:nil];
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(0.12*NSEC_PER_SEC)),dispatch_get_main_queue(),^{ [self rotated:nil]; });
}

- (UIWindow *)keyWindow {
    UIWindow *fallback=nil;
    for (UIScene *scene in UIApplication.sharedApplication.connectedScenes) {
        if (![scene isKindOfClass:UIWindowScene.class]) continue;
        UIWindowScene *ws=(UIWindowScene *)scene;
        for (UIWindow *w in ws.windows) {
            if (!fallback && !w.hidden) fallback=w;
            if (w.isKeyWindow) return w;
        }
    }
    return fallback;
}

- (void)appActive:(NSNotification *)n { (void)n; [self rotated:nil]; }

- (void)rotated:(NSNotification *)n {
    (void)n;
    UIDeviceOrientation o=UIDevice.currentDevice.orientation;
    if (o==UIDeviceOrientationUnknown || o==UIDeviceOrientationFaceUp || o==UIDeviceOrientationFaceDown) return;
    if (UIDeviceOrientationIsLandscape(o)) {
        if (!self.dismissed) [self show:o];
    } else if (o==UIDeviceOrientationPortrait || o==UIDeviceOrientationPortraitUpsideDown) {
        self.dismissed=NO;
        self.displayedOrientation=UIDeviceOrientationUnknown;
        [self hide:YES];
    }
}

- (void)show:(UIDeviceOrientation)o {
    UIWindow *w=[self keyWindow];
    if (!w) return;
    if (!self.overlay) [self build:w];
    if (self.overlay.superview!=w) {
        [self.overlay removeFromSuperview];
        [w addSubview:self.overlay];
    }
    if (self.displayedOrientation!=o || self.overlay.hidden) {
        self.displayedOrientation=o;
        [self layoutForWindow:w orientation:o];
    }
    self.overlay.hidden=NO;
    self.overlay.alpha=1;
    [w bringSubviewToFront:self.overlay];

    if (!self.libraryLoaded) {
        self.libraryLoaded=YES;
        self.emptyLabel.hidden=NO;
        self.emptyLabel.text=@"Loading albums…";
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(0.01*NSEC_PER_SEC)),dispatch_get_main_queue(),^{ [self reloadAlbums]; });
    }
}

- (void)build:(UIWindow *)w {
    self.overlay=[[UIView alloc] initWithFrame:w.bounds];
    self.overlay.backgroundColor=UIColor.blackColor;
    self.overlay.clipsToBounds=YES;

    self.canvas=[UIView new];
    self.canvas.backgroundColor=UIColor.blackColor;
    self.canvas.clipsToBounds=YES;
    [self.overlay addSubview:self.canvas];

    UILabel *title=[UILabel new];
    title.tag=1601;
    title.text=@"Cover Flow";
    title.textColor=UIColor.whiteColor;
    title.alpha=.70;
    title.font=[UIFont systemFontOfSize:13 weight:UIFontWeightSemibold];
    title.textAlignment=NSTextAlignmentCenter;
    [self.canvas addSubview:title];

    UIButton *close=[UIButton buttonWithType:UIButtonTypeSystem];
    close.tag=1602;
    [close setTitle:@"×" forState:UIControlStateNormal];
    close.titleLabel.font=[UIFont systemFontOfSize:30 weight:UIFontWeightLight];
    [close setTitleColor:[UIColor colorWithWhite:1 alpha:.78] forState:UIControlStateNormal];
    [close addTarget:self action:@selector(close:) forControlEvents:UIControlEventTouchUpInside];
    [self.canvas addSubview:close];

    self.flow=[UICollectionViewFlowLayout new];
    self.flow.scrollDirection=UICollectionViewScrollDirectionHorizontal;
    self.flow.minimumLineSpacing=0;
    self.flow.minimumInteritemSpacing=0;

    self.collection=[[UICollectionView alloc] initWithFrame:CGRectZero collectionViewLayout:self.flow];
    self.collection.backgroundColor=UIColor.clearColor;
    self.collection.showsHorizontalScrollIndicator=NO;
    self.collection.alwaysBounceHorizontal=YES;
    self.collection.decelerationRate=UIScrollViewDecelerationRateFast;
    self.collection.clipsToBounds=NO;
    self.collection.dataSource=self;
    self.collection.delegate=self;
    [self.collection registerClass:CF16Cell.class forCellWithReuseIdentifier:@"CF16Cell"];
    [self.canvas addSubview:self.collection];

    self.albumLabel=[UILabel new];
    self.albumLabel.textColor=UIColor.whiteColor;
    self.albumLabel.font=[UIFont systemFontOfSize:17 weight:UIFontWeightSemibold];
    self.albumLabel.textAlignment=NSTextAlignmentCenter;
    [self.canvas addSubview:self.albumLabel];

    self.artistLabel=[UILabel new];
    self.artistLabel.textColor=[UIColor colorWithWhite:1 alpha:.62];
    self.artistLabel.font=[UIFont systemFontOfSize:13];
    self.artistLabel.textAlignment=NSTextAlignmentCenter;
    [self.canvas addSubview:self.artistLabel];

    self.emptyLabel=[UILabel new];
    self.emptyLabel.textColor=[UIColor colorWithWhite:1 alpha:.65];
    self.emptyLabel.textAlignment=NSTextAlignmentCenter;
    self.emptyLabel.numberOfLines=2;
    self.emptyLabel.hidden=YES;
    [self.canvas addSubview:self.emptyLabel];

    [w addSubview:self.overlay];
}

- (void)layoutForWindow:(UIWindow *)w orientation:(UIDeviceOrientation)o {
    self.overlay.frame=w.bounds;
    CGFloat pw=MAX(CGRectGetWidth(w.bounds),CGRectGetHeight(w.bounds));
    CGFloat ph=MIN(CGRectGetWidth(w.bounds),CGRectGetHeight(w.bounds));
    self.canvas.bounds=CGRectMake(0,0,pw,ph);
    self.canvas.center=CGPointMake(CGRectGetMidX(self.overlay.bounds),CGRectGetMidY(self.overlay.bounds));

    if (CGRectGetWidth(w.bounds)>CGRectGetHeight(w.bounds)) {
        self.canvas.transform=CGAffineTransformIdentity;
    } else {
        self.canvas.transform=CGAffineTransformMakeRotation(o==UIDeviceOrientationLandscapeLeft ? M_PI_2 : -M_PI_2);
    }

    [self.canvas viewWithTag:1601].frame=CGRectMake((pw-180)/2,7,180,24);
    [self.canvas viewWithTag:1602].frame=CGRectMake(pw-52,1,48,42);

    self.coverSize=MIN(206,MAX(128,floor(ph*.51)));
    self.stride=MAX(90,floor(self.coverSize*.60));
    self.reflectionHeight=floor(self.coverSize*.23);

    CGFloat collectionY=35;
    CGFloat collectionH=MAX(170,ph-89);
    self.collection.frame=CGRectMake(0,collectionY,pw,collectionH);
    self.flow.itemSize=CGSizeMake(self.stride,self.coverSize+self.reflectionHeight+5);
    CGFloat sideInset=MAX(0,(pw-self.stride)/2.0);
    self.flow.sectionInset=UIEdgeInsetsMake(MAX(0,floor((collectionH-self.coverSize-self.reflectionHeight)*.35)),sideInset,0,sideInset);
    [self.flow invalidateLayout];

    self.albumLabel.frame=CGRectMake(48,ph-50,pw-96,23);
    self.artistLabel.frame=CGRectMake(48,ph-28,pw-96,18);
    self.emptyLabel.frame=CGRectMake(30,70,pw-60,ph-130);

    self.placeholder=[self makePlaceholder:CGSizeMake(self.coverSize,self.coverSize)];
    [self.collection reloadData];
    if (self.albums.count) {
        self.selected=MAX(0,MIN(self.selected,(NSInteger)self.albums.count-1));
        self.collection.contentOffset=CGPointMake(self.selected*self.stride,0);
        [self updateLabels:self.selected];
        dispatch_async(dispatch_get_main_queue(),^{ [self updateTransforms]; });
    }
}

- (void)reloadAlbums {
    @try {
        self.albums=[MPMediaQuery albumsQuery].collections ?: @[];
        [self log:[NSString stringWithFormat:@"%lu albums",(unsigned long)self.albums.count]];
    } @catch (NSException *e) {
        self.albums=@[];
        [self log:[NSString stringWithFormat:@"query failed: %@",e.reason]];
    }
    self.emptyLabel.hidden=(self.albums.count!=0);
    self.emptyLabel.text=@"No albums found\nin the local media library";
    self.selected=0;
    [self.collection reloadData];
    self.collection.contentOffset=CGPointZero;
    if (self.albums.count) [self updateLabels:0];
    dispatch_async(dispatch_get_main_queue(),^{ [self updateTransforms]; });
}

- (UIImage *)makePlaceholder:(CGSize)s {
    UIGraphicsBeginImageContextWithOptions(s,YES,0);
    [[UIColor colorWithWhite:.12 alpha:1] setFill];
    UIRectFill(CGRectMake(0,0,s.width,s.height));
    UIImageSymbolConfiguration *cfg=[UIImageSymbolConfiguration configurationWithPointSize:s.width*.28 weight:UIImageSymbolWeightLight];
    UIImage *im=[UIImage systemImageNamed:@"music.note" withConfiguration:cfg];
    [im drawInRect:CGRectMake(s.width*.34,s.height*.34,s.width*.32,s.height*.32) blendMode:kCGBlendModeNormal alpha:.75];
    UIImage *r=UIGraphicsGetImageFromCurrentImageContext();
    UIGraphicsEndImageContext();
    return r;
}

- (NSInteger)collectionView:(UICollectionView *)collectionView numberOfItemsInSection:(NSInteger)section {
    (void)collectionView; (void)section;
    return self.albums.count;
}

- (__kindof UICollectionViewCell *)collectionView:(UICollectionView *)collectionView cellForItemAtIndexPath:(NSIndexPath *)indexPath {
    CF16Cell *cell=[collectionView dequeueReusableCellWithReuseIdentifier:@"CF16Cell" forIndexPath:indexPath];
    NSInteger idx=indexPath.item;
    cell.representedIndex=idx;
    cell.coverSize=self.coverSize;
    cell.reflectionHeight=self.reflectionHeight;
    cell.art.image=self.placeholder;
    cell.reflection.image=self.placeholder;
    [cell setNeedsLayout];

    NSNumber *key=@(idx);
    UIImage *cached=[self.artCache objectForKey:key];
    if (cached) {
        cell.art.image=cached;
        cell.reflection.image=cached;
        return cell;
    }

    if (idx>=0 && idx<(NSInteger)self.albums.count) {
        MPMediaItemCollection *album=self.albums[idx];
        MPMediaItem *item=album.representativeItem ?: album.items.firstObject;
        MPMediaItemArtwork *art=[item valueForProperty:MPMediaItemPropertyArtwork];
        CGSize request=CGSizeMake(self.coverSize*1.5,self.coverSize*1.5);
        __weak typeof(self) weakSelf=self;
        __weak CF16Cell *weakCell=cell;
        [self.artQueue addOperationWithBlock:^{
            UIImage *image=[art imageWithSize:request];
            if (!image) return;
            typeof(self) selfRef=weakSelf;
            if (!selfRef) return;
            [selfRef.artCache setObject:image forKey:key];
            [[NSOperationQueue mainQueue] addOperationWithBlock:^{
                CF16Cell *cellRef=weakCell;
                if (!cellRef || cellRef.representedIndex!=idx) return;
                cellRef.art.image=image;
                cellRef.reflection.image=image;
            }];
        }];
    }
    return cell;
}

- (void)collectionView:(UICollectionView *)collectionView didSelectItemAtIndexPath:(NSIndexPath *)indexPath {
    (void)collectionView;
    [self select:indexPath.item animated:YES];
}

- (NSInteger)nearestIndexForOffset:(CGFloat)x {
    if (!self.albums.count || self.stride<=0) return NSNotFound;
    NSInteger idx=(NSInteger)llround(x/self.stride);
    return MAX(0,MIN(idx,(NSInteger)self.albums.count-1));
}

- (void)select:(NSInteger)idx animated:(BOOL)animated {
    if (idx<0 || idx>=(NSInteger)self.albums.count) return;
    self.selected=idx;
    [self updateLabels:idx];
    [self.collection setContentOffset:CGPointMake(idx*self.stride,0) animated:animated];
    [self updateTransforms];
}

- (void)updateLabels:(NSInteger)idx {
    if (idx<0 || idx>=(NSInteger)self.albums.count) return;
    MPMediaItemCollection *c=self.albums[idx];
    MPMediaItem *m=c.representativeItem ?: c.items.firstObject;
    NSString *album=[m valueForProperty:MPMediaItemPropertyAlbumTitle];
    NSString *artist=[m valueForProperty:MPMediaItemPropertyAlbumArtist];
    if (!artist.length) artist=[m valueForProperty:MPMediaItemPropertyArtist];
    self.albumLabel.text=album.length?album:@"Unknown Album";
    self.artistLabel.text=artist.length?artist:@"Unknown Artist";
}

- (void)updateTransforms {
    if (!self.collection || self.stride<=0) return;
    CGFloat viewportCenter=self.collection.contentOffset.x+CGRectGetWidth(self.collection.bounds)/2.0;
    NSInteger near=[self nearestIndexForOffset:self.collection.contentOffset.x];
    if (near!=NSNotFound && near!=self.selected) {
        self.selected=near;
        [self updateLabels:near];
    }

    for (CF16Cell *cell in self.collection.visibleCells) {
        CGFloat n=(cell.center.x-viewportCenter)/self.stride;
        CGFloat distance=MIN(2.3,fabs(n));
        CATransform3D t=CATransform3DIdentity;
        t.m34=-1.0/700.0;
        if (fabs(n)<.14) {
            cell.layer.zPosition=1000;
            cell.alpha=1;
        } else {
            CGFloat side=n<0?-1:1;
            CGFloat scale=MAX(.79,.90-distance*.035);
            t=CATransform3DTranslate(t,side*-self.coverSize*.08,0,-MIN(145,distance*50));
            t=CATransform3DRotate(t,-side*(M_PI*.32),0,1,0);
            t=CATransform3DScale(t,scale,scale,1);
            cell.layer.zPosition=500-distance*20;
            cell.alpha=MAX(.68,1-distance*.08);
        }
        cell.layer.transform=t;
    }
}

- (void)scrollViewDidScroll:(UIScrollView *)scrollView {
    (void)scrollView;
    [self updateTransforms];
}

- (void)scrollViewWillEndDragging:(UIScrollView *)scrollView withVelocity:(CGPoint)velocity targetContentOffset:(inout CGPoint *)targetContentOffset {
    (void)scrollView; (void)velocity;
    NSInteger idx=[self nearestIndexForOffset:targetContentOffset->x];
    if (idx!=NSNotFound) targetContentOffset->x=idx*self.stride;
}

- (void)scrollViewDidEndDecelerating:(UIScrollView *)scrollView {
    NSInteger idx=[self nearestIndexForOffset:scrollView.contentOffset.x];
    if (idx!=NSNotFound) [self select:idx animated:NO];
}

- (void)scrollViewDidEndScrollingAnimation:(UIScrollView *)scrollView {
    NSInteger idx=[self nearestIndexForOffset:scrollView.contentOffset.x];
    if (idx!=NSNotFound) [self select:idx animated:NO];
}

- (void)close:(id)sender {
    (void)sender;
    self.dismissed=YES;
    [self hide:YES];
}

- (void)hide:(BOOL)animated {
    if (!self.overlay || self.overlay.hidden) return;
    [self.artQueue cancelAllOperations];
    if (!animated) {
        self.overlay.hidden=YES;
        return;
    }
    [UIView animateWithDuration:.10 animations:^{ self.overlay.alpha=0; } completion:^(BOOL finished){
        (void)finished;
        self.overlay.hidden=YES;
        self.overlay.alpha=1;
    }];
}
@end

__attribute__((constructor)) static void CF16Init(void) {
    @autoreleasepool {
        if (![NSBundle.mainBundle.bundleIdentifier isEqualToString:@"com.apple.Music"]) return;
        dispatch_async(dispatch_get_main_queue(),^{ [[CF16Manager shared] start]; });
    }
}

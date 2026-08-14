#import <Foundation/Foundation.h>
typedef struct __attribute__((packed)){float pitch;float mouth;} OtamaReplayFrame;
@interface OtamaReplay:NSObject
@property(nonatomic,copy)NSString*name;@property(nonatomic)int skin;@property(nonatomic)int octave;@property(nonatomic,readonly)NSUInteger count;@property(nonatomic,readonly)const OtamaReplayFrame*frames;
+(instancetype)replayWithURL:(NSURL*)url error:(NSError**)error;+(instancetype)replayWithBundleName:(NSString*)name;+(instancetype)newRecordingWithName:(NSString*)name skin:(int)skin octave:(int)octave;-(void)appendPitch:(float)pitch mouth:(float)mouth;-(BOOL)writeToURL:(NSURL*)url error:(NSError**)error;
@end
FOUNDATION_EXPORT NSURL*OtamaRecordingsDirectory(void);FOUNDATION_EXPORT NSArray<NSURL*>*OtamaUserReplayURLs(void);

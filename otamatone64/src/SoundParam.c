#include "OtamatoneCore.h"
#include <math.h>
static const float PitchTbl[12]={1.0f,1.0594632626f,1.1224621534f,1.1892073154f,1.2599211931f,1.3348399401f,1.4142135382f,1.4983072281f,1.5874011517f,1.6817929745f,1.7817975283f,1.8877487183f};
static const unsigned char BlackKey[12]={0,1,0,1,0,0,1,0,1,0,1,0};
float GetPitch(int octave,int note){while(note<0){note+=12;octave--;}while(note>=12){note-=12;octave++;}return powf(2.0f,(float)octave)*PitchTbl[note];}
void GetScale(int *octave,int *note,int whiteWidth,int blackWidth,float position,float origin){float p=position-origin;int s=0;if(p>=0){float c=0;for(s=0;s<20;s++){c+=BlackKey[s%12]?blackWidth:whiteWidth;if(p<c)break;}if(s>=20)s=19;}else{float c=0;s=-1;while(s>=-18){int i=(s+120)%12;c-=BlackKey[i]?blackWidth:whiteWidth;if(p>c)break;--s;}++s;}int o=s/12,n=s%12;if(n<0){n+=12;--o;}if(octave)*octave=o;if(note)*note=n;}

#include "OtamatoneCore.h"
#include <math.h>
#include <string.h>
static ACRCursor gCursor[4]; static float gAcc[3]; static float gRatio=1.0f; static const float kAccFilterRatio=.18f;
static ACRCursor *find_cursor(int id){for(int i=0;i<4;i++)if(gCursor[i].active&&gCursor[i].identifier==id)return &gCursor[i];return NULL;}
void ACRInitialize(void){ACRReset();}
void ACRReset(void){memset(gCursor,0,sizeof(gCursor));gAcc[0]=0;gAcc[1]=-1;gAcc[2]=0;gRatio=1;}
void ACRBegin(int id,float x,float y){ACRCursor*c=find_cursor(id);if(!c)for(int i=0;i<4;i++)if(!gCursor[i].active){c=&gCursor[i];break;}if(!c)c=&gCursor[0];memset(c,0,sizeof(*c));c->active=true;c->began=true;c->identifier=id;c->x=c->prevX=c->beginX=x/gRatio;c->y=c->prevY=c->beginY=y/gRatio;}
void ACRMove(int id,float x,float y){ACRCursor*c=find_cursor(id);if(!c){ACRBegin(id,x,y);c=find_cursor(id);}c->prevX=c->x;c->prevY=c->y;c->x=x/gRatio;c->y=y/gRatio;c->moved=true;}
void ACREnd(int id,float x,float y){ACRCursor*c=find_cursor(id);if(!c)return;c->prevX=c->x;c->prevY=c->y;c->x=x/gRatio;c->y=y/gRatio;c->ended=true;}
const ACRCursor *ACRGetCursor(int i){return i>=0&&i<4?&gCursor[i]:NULL;}
void ACRSetAcc(float x,float y,float z){gAcc[0]=(1-kAccFilterRatio)*gAcc[0]+kAccFilterRatio*x;gAcc[1]=(1-kAccFilterRatio)*gAcc[1]+kAccFilterRatio*y;gAcc[2]=(1-kAccFilterRatio)*gAcc[2]+kAccFilterRatio*z;}
float ACRGetAccX(void){return gAcc[0];}float ACRGetAccY(void){return gAcc[1];}float ACRGetAccZ(void){return gAcc[2];}void ACRSetRatio(float r){gRatio=r>.0001f?r:1;}
bool ACRIsMoved(int i){const ACRCursor*c=ACRGetCursor(i);return c&&c->active&&hypotf(c->x-c->beginX,c->y-c->beginY)>=16;}
bool ACRIsTouchOn(int i){const ACRCursor*c=ACRGetCursor(i);return c&&c->began;}bool ACRIsTouchOff(int i){const ACRCursor*c=ACRGetCursor(i);return c&&c->ended;}
void ACRUpdate(void){for(int i=0;i<4;i++){ACRCursor*c=&gCursor[i];c->began=false;c->moved=false;if(c->ended)memset(c,0,sizeof(*c));}}

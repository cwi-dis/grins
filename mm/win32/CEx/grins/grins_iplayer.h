#ifndef INC_GRINS_IPLAYER
#define INC_GRINS_IPLAYER

namespace grins {

struct iplayer
	{
	virtual ~iplayer() {}
	virtual void play() = 0;
	virtual void pause() = 0;
	virtual void stop() = 0;
	};

} // namespace grins


#endif // INC_GRINS_IPLAYER




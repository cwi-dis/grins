#ifndef INC_GRINS_PLAYER
#define INC_GRINS_PLAYER

#ifndef INC_GRINS_IPLAYER
#include "grins_iplayer.h"
#endif

namespace grins {

class TopLevel;

class Player : public iplayer
	{
	public:
	Player(TopLevel *top);
	~Player();

	virtual void play();
	virtual void pause();
	virtual void stop();

	private:
	const char* test_get_first_img();

	TopLevel *m_toplevel;
	};

} // namespace grins


#endif // INC_GRINS_PLAYER




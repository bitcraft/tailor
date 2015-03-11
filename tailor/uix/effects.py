from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.properties import *
from kivy.clock import Clock
import time

__all__ = ('TailorScrollEffect', )


class TailorScrollEffect(DampedScrollEffect):
    """ on my system, the large scrollview doesn't work well.
    this is a more computationally involved method of scrolling, but is more
    accurate...and works.
    """
    friction = NumericProperty(0.005)
    min_velocity = NumericProperty(.1)
    spring_constant = NumericProperty(10.0)
    edge_damping = NumericProperty(0.5)
    max_history = None

    def start(self, val, t=None):
        self.is_manual = True
        t = t or time.time()
        self.velocity = 0
        self.last_state = (t, val)

    def update(self, val, t=None):
        """Update the movement.

        See :meth:`start` for the arguments.
        """
        t = t or time.time()
        duration = max(abs(t - self.last_state[0]), 0.0001)
        distance = val - self.last_state[1]
        self.last_state = (t, val)
        try:
            self.velocity = distance / duration
        except ZeroDivisionError:
            self.velocity = 0

        self.trigger_velocity_update()

    def stop(self, val, t=None):
        """Stop the movement.

        See :meth:`start` for the arguments.
        """
        self.is_manual = False

    def on_overscroll(self, *args):
        self.trigger_velocity_update()
        pass

    def update_velocity(self, dt):
        if (abs(self.velocity) <= self.min_velocity) and self.overscroll == 0:
            self.velocity = 0
            # why does this need to be rounded? For now refactored it.
            if self.round_value:
                self.value = round(self.value)
            return

        # dt is 0.0 once after being triggered for the first time
        if dt == 0.0:
            dt = Clock.frametime

        stop_overscroll = None

        if not self.is_manual:
            # handle movement after the touch has finished
            friction = pow(self.friction, dt)

            if abs(self.overscroll) > self.min_overscroll:
                # content was scrolled past the margins
                rebound_force = self.velocity * friction
                rebound_force += self.velocity * self.edge_damping
                rebound_force += self.overscroll * self.spring_constant
                self.velocity -= rebound_force
                if self.overscroll > 0 > self.velocity:
                    stop_overscroll = 'max'
                elif self.overscroll < 0 < self.velocity:
                    stop_overscroll = 'min'
            else:
                # no overscroll, or no significant amount of it
                self.velocity *= friction
                self.overscroll = 0

        self.apply_distance(self.velocity * dt)

        # stop moving after the overscroll rebound is finished
        if stop_overscroll == 'min' and self.value >= self.min:
            self.value = self.min
            self.velocity = 0
            return
        if stop_overscroll == 'max' and self.value <= self.max:
            self.value = self.max
            self.velocity = 0
            return

        self.trigger_velocity_update()
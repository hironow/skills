package booking

import "sync/atomic"

// EmergencyStop is flipped by the monitoring agent when it detects unauthorized access.
// While it is active, the service takes no new holds and starts no new payments.
type EmergencyStop struct {
	active atomic.Bool
	reason atomic.Value
}

// Trigger turns the stop on. The monitoring agent calls it without asking anyone.
func (e *EmergencyStop) Trigger(reason string) {
	e.reason.Store(reason)
	e.active.Store(true)
}

// Lift turns the stop off.
func (e *EmergencyStop) Lift() {
	e.active.Store(false)
}

// Active reports whether intake is stopped.
func (e *EmergencyStop) Active() bool {
	return e.active.Load()
}

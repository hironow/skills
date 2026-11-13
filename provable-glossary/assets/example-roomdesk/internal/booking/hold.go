package booking

import (
	"errors"
	"time"
)

var (
	ErrIntakeStopped = errors.New("intake is stopped")
	ErrSlotTaken     = errors.New("slot is taken")
	ErrSlotClosed    = errors.New("slot is closed")
	ErrNotHolder     = errors.New("reservation is not held")
)

// PlaceHold reserves a free slot for a member for HoldDuration.
func (s *Service) PlaceHold(now time.Time, slotID, memberID string) (*Reservation, error) {
	if s.stop.Active() {
		return nil, ErrIntakeStopped
	}
	slot := s.store.Slot(slotID)
	if slot.Closed {
		return nil, ErrSlotClosed
	}
	if s.store.ActiveReservation(slotID) != nil {
		return nil, ErrSlotTaken
	}
	r := &Reservation{
		ID:            s.ids.Next(),
		SlotID:        slotID,
		MemberID:      memberID,
		Status:        StatusHeld,
		HoldExpiresAt: now.Add(HoldDuration),
	}
	s.store.Save(r)
	return r, nil
}

// StartPayment hands the member over to the payment provider.
func (s *Service) StartPayment(now time.Time, reservationID string) (string, error) {
	if s.stop.Active() {
		return "", ErrIntakeStopped
	}
	r := s.store.Reservation(reservationID)
	if r.Status != StatusHeld || now.After(r.HoldExpiresAt) {
		return "", ErrNotHolder
	}
	r.Status = StatusPaying
	r.PaymentRef = s.payments.Begin(r.ID)
	s.store.Save(r)
	return r.PaymentRef, nil
}

// ExpireHolds releases holds whose time is up. A cron job calls it every minute.
func (s *Service) ExpireHolds(now time.Time) {
	for _, r := range s.store.ReservationsWithStatus(StatusHeld, StatusPaying) {
		if now.After(r.HoldExpiresAt) {
			r.Status = StatusExpired
			s.store.Save(r)
		}
	}
}

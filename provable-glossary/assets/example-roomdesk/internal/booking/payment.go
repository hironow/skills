package booking

// PaymentEvent is what the payment provider sends to the webhook.
type PaymentEvent struct {
	PaymentRef string
	Succeeded  bool
}

// HandlePaymentWebhook applies the provider's result. The provider retries until it gets a 200,
// and it does not know or care whether intake is stopped.
func (s *Service) HandlePaymentWebhook(ev PaymentEvent) {
	r := s.store.ReservationByPaymentRef(ev.PaymentRef)
	if r == nil {
		return
	}
	if !ev.Succeeded {
		r.Status = StatusCancelled
		s.store.Save(r)
		return
	}
	// The member paid, so the room is theirs.
	r.Status = StatusBooked
	s.store.Save(r)
	s.mail.SendBookingConfirmed(r.MemberID, r.ID)
}

// CloseSlot is used by staff when a room cannot be used (broken equipment, double-let by mistake).
func (s *Service) CloseSlot(slotID string) {
	slot := s.store.Slot(slotID)
	slot.Closed = true
	s.store.SaveSlot(slot)
	if r := s.store.ActiveReservation(slotID); r != nil && r.Status == StatusBooked {
		r.Status = StatusCancelled
		s.store.Save(r)
		s.mail.SendSlotClosed(r.MemberID, r.ID)
	}
}

// RequestRefund records that money is owed back. Finance runs the actual refund later.
func (s *Service) RequestRefund(reservationID string) {
	s.store.SaveRefund(&Refund{ID: s.ids.Next(), ReservationID: reservationID, RequestedAt: s.clock.Now()})
}

package booking

import "time"

// Store is the persistence port.
type Store interface {
	Slot(id string) *Slot
	SaveSlot(*Slot)
	Reservation(id string) *Reservation
	ReservationByPaymentRef(ref string) *Reservation
	// ActiveReservation returns the reservation that currently occupies the slot:
	// one whose status is HELD, PAYING or BOOKED.
	ActiveReservation(slotID string) *Reservation
	ReservationsWithStatus(statuses ...ReservationStatus) []*Reservation
	Save(*Reservation)
	SaveRefund(*Refund)
}

// PaymentGateway starts a payment with the external provider.
type PaymentGateway interface {
	Begin(reservationID string) (paymentRef string)
}

// Mailer notifies members.
type Mailer interface {
	SendBookingConfirmed(memberID, reservationID string)
	SendSlotClosed(memberID, reservationID string)
}

// IDs issues identifiers.
type IDs interface{ Next() string }

// Clock tells the time.
type Clock interface{ Now() time.Time }

// Service is the booking application service.
type Service struct {
	store    Store
	payments PaymentGateway
	mail     Mailer
	ids      IDs
	clock    Clock
	stop     *EmergencyStop
}

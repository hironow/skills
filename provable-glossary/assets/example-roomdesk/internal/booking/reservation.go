// Package booking holds the reservation rules of roomdesk.
package booking

import "time"

// ReservationStatus is where a reservation stands.
type ReservationStatus string

const (
	StatusHeld      ReservationStatus = "HELD"
	StatusPaying    ReservationStatus = "PAYING"
	StatusBooked    ReservationStatus = "BOOKED"
	StatusExpired   ReservationStatus = "EXPIRED"
	StatusCancelled ReservationStatus = "CANCELLED"
	StatusRefunded  ReservationStatus = "REFUNDED"
)

// HoldDuration is how long a slot stays held before payment starts.
const HoldDuration = 10 * time.Minute

// Slot is one room for one time range.
type Slot struct {
	ID       string
	RoomID   string
	StartsAt time.Time
	Closed   bool
}

// Reservation ties a member to a slot.
type Reservation struct {
	ID            string
	SlotID        string
	MemberID      string
	Status        ReservationStatus
	HoldExpiresAt time.Time
	PaymentRef    string
}

// Refund is money owed back to a member.
type Refund struct {
	ID            string
	ReservationID string
	RequestedAt   time.Time
	DoneAt        *time.Time
}

CREATE TABLE rooms (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE slots (
  id TEXT PRIMARY KEY,
  room_id TEXT NOT NULL REFERENCES rooms(id),
  starts_at TIMESTAMP NOT NULL,
  closed BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE reservations (
  id TEXT PRIMARY KEY,
  slot_id TEXT NOT NULL REFERENCES slots(id),
  member_id TEXT NOT NULL,
  status TEXT NOT NULL,
  hold_expires_at TIMESTAMP,
  payment_ref TEXT
);

CREATE TABLE refunds (
  id TEXT PRIMARY KEY,
  reservation_id TEXT NOT NULL REFERENCES reservations(id),
  requested_at TIMESTAMP NOT NULL,
  done_at TIMESTAMP
);

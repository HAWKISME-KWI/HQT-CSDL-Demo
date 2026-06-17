DROP VIEW IF EXISTS view_available_courts;
DROP VIEW IF EXISTS view_booking_history;
DROP VIEW IF EXISTS view_admin_dashboard;
DROP VIEW IF EXISTS view_all_bookings;

CREATE OR REPLACE VIEW view_available_courts AS
SELECT  
    c.court_id,
    c.court_name,
    c.address,
    c.court_surfaces_type,
    c.court_sizes_type,
    c.price_per_hour,
    c.image_url,
    u.phone_number AS owner_phone,
    NOT EXISTS (
        SELECT 1 FROM bookings b
        WHERE b.court_id = c.court_id
        AND b.status = 'BOOKED'
        AND b.start_time <= CURRENT_TIMESTAMP + INTERVAL '1 hour'
        AND b.end_time >= CURRENT_TIMESTAMP
    ) AS is_currently_free
FROM courts c
LEFT JOIN users u ON c.owner_id = u.user_id
WHERE c.is_active = TRUE;

CREATE OR REPLACE VIEW view_booking_history AS
SELECT
    b.booking_id,
    b.user_id,
    c.court_name,
    b.start_time,
    b.end_time,
    b.status,
    fn_calculate_booking_cost(b.court_id, b.start_time, b.end_time) AS total_cost
FROM bookings b
JOIN courts c ON b.court_id = c.court_id;

CREATE OR REPLACE VIEW view_admin_dashboard AS
SELECT 
    (SELECT COUNT(*) FROM bookings WHERE status = 'PENDING') AS pending_bookings,
    (SELECT COUNT(*) FROM bookings WHERE status = 'BOOKED') AS booked_bookings,
    (SELECT COALESCE(SUM(fn_calculate_booking_cost(b.court_id, b.start_time, b.end_time)), 0)
     FROM bookings b
     WHERE b.status = 'COMPLETED') AS total_revenue,
    (SELECT COUNT(*) FROM users WHERE is_active = TRUE) AS total_active_users;

CREATE OR REPLACE VIEW view_all_bookings AS
SELECT 
    b.booking_id,
    u.username,
    u.phone_number,
    c.court_name,
    b.start_time,
    b.end_time,
    b.status,
    fn_calculate_booking_cost(b.court_id, b.start_time, b.end_time) AS total_cost
FROM bookings b
JOIN users u ON b.user_id = u.user_id
JOIN courts c ON b.court_id = c.court_id
ORDER BY b.start_time DESC;
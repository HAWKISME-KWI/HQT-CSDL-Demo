DROP FUNCTION IF EXISTS fn_calculate_booking_cost(UUID, TIMESTAMPTZ, TIMESTAMPTZ);
DROP FUNCTION IF EXISTS fn_is_court_available(UUID, TIMESTAMPTZ, TIMESTAMPTZ);
DROP FUNCTION IF EXISTS fn_search_bookings(UUID, TIMESTAMPTZ, TIMESTAMPTZ, booking_status, UUID);
DROP FUNCTION IF EXISTS fn_filter_courts(court_surfaces, court_sizes, DECIMAL, DECIMAL, BOOLEAN);
DROP FUNCTION IF EXISTS fn_get_court_schedule(UUID, DATE);
DROP FUNCTION IF EXISTS fn_daily_revenue(DATE, DATE);
DROP FUNCTION IF EXISTS fn_top_courts(INT);
DROP FUNCTION IF EXISTS sp_approve_booking(UUID, UUID);
DROP FUNCTION IF EXISTS sp_reject_booking(UUID, UUID);
DROP FUNCTION IF EXISTS sp_book_court(UUID, UUID, TIMESTAMPTZ, TIMESTAMPTZ);
DROP FUNCTION IF EXISTS sp_cancel_booking_customer(UUID, UUID);
DROP FUNCTION IF EXISTS sp_cancel_booking_powerfull(UUID, UUID);
DROP FUNCTION IF EXISTS sp_complete_booking(UUID, UUID);
DROP FUNCTION IF EXISTS sp_add_court(VARCHAR, TEXT, court_surfaces, court_sizes, DECIMAL, DECIMAL, UUID, TEXT);
DROP FUNCTION IF EXISTS sp_update_court(UUID, VARCHAR, TEXT, court_surfaces, court_sizes, DECIMAL, DECIMAL, BOOLEAN, TEXT, UUID);
DROP FUNCTION IF EXISTS sp_delete_court(UUID, UUID);

CREATE OR REPLACE FUNCTION fn_calculate_booking_cost(
    p_court_id UUID,
    p_start_time TIMESTAMPTZ,
    p_end_time TIMESTAMPTZ
)
RETURNS DECIMAL AS $$
DECLARE
    v_price_per_hour DECIMAL;
    v_price_per_3h DECIMAL;
    v_hours NUMERIC;
    v_cost DECIMAL;
BEGIN
    SELECT price_per_hour, price_per_three_hours INTO v_price_per_hour, v_price_per_3h
    FROM courts WHERE court_id = p_court_id;
    v_hours := EXTRACT(EPOCH FROM (p_end_time - p_start_time)) / 3600;
    IF v_hours >= 3 THEN
        v_cost := v_price_per_3h * CEIL(v_hours / 3);
    ELSE
        v_cost := v_price_per_hour * v_hours;
    END IF;
    RETURN v_cost;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_is_court_available(
    p_court_id UUID,
    p_start TIMESTAMPTZ,
    p_end TIMESTAMPTZ
)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN NOT EXISTS (
        SELECT 1 FROM bookings
        WHERE court_id = p_court_id
        AND status = 'BOOKED'
        AND (start_time < p_end AND end_time > p_start)
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_search_bookings(
    p_user_id UUID DEFAULT NULL,
    p_from_date TIMESTAMPTZ DEFAULT NULL,
    p_to_date TIMESTAMPTZ DEFAULT NULL,
    p_status booking_status DEFAULT NULL,
    p_court_id UUID DEFAULT NULL
)
RETURNS TABLE(
    booking_id UUID,
    court_name VARCHAR,
    user_name VARCHAR,
    phone_number VARCHAR,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    status booking_status,
    total_cost DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.booking_id,
        c.court_name,
        u.username AS user_name,
        u.phone_number,
        b.start_time,
        b.end_time,
        b.status,
        fn_calculate_booking_cost(b.court_id, b.start_time, b.end_time) AS total_cost
    FROM bookings b
    JOIN courts c ON b.court_id = c.court_id
    JOIN users u ON b.user_id = u.user_id
    WHERE (p_user_id IS NULL OR b.user_id = p_user_id)
        AND (p_from_date IS NULL OR b.start_time >= p_from_date)
        AND (p_to_date IS NULL OR b.end_time <= p_to_date)
        AND (p_status IS NULL OR b.status = p_status)
        AND (p_court_id IS NULL OR b.court_id = p_court_id)
    ORDER BY b.start_time DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_filter_courts(
    p_surface court_surfaces DEFAULT NULL,
    p_size court_sizes DEFAULT NULL,
    p_min_price DECIMAL DEFAULT NULL,
    p_max_price DECIMAL DEFAULT NULL,
    p_is_free BOOLEAN DEFAULT NULL
)
RETURNS TABLE(
    court_id UUID,
    court_name VARCHAR,
    address TEXT,
    surface court_surfaces,
    size court_sizes,
    price_per_hour DECIMAL,
    image_url TEXT,
    is_currently_free BOOLEAN,
    owner_phone VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.court_id,
        c.court_name,
        c.address,
        c.court_surfaces_type,
        c.court_sizes_type,
        c.price_per_hour,
        c.image_url,
        NOT EXISTS (
            SELECT 1 FROM bookings b
            WHERE b.court_id = c.court_id
            AND b.status = 'BOOKED'
            AND b.start_time <= CURRENT_TIMESTAMP + INTERVAL '1 hour'
            AND b.end_time >= CURRENT_TIMESTAMP
        ) AS is_free,
        u.phone_number AS owner_phone
    FROM courts c
    LEFT JOIN users u ON c.owner_id = u.user_id
    WHERE c.is_active = TRUE
        AND (p_surface IS NULL OR c.court_surfaces_type = p_surface)
        AND (p_size IS NULL OR c.court_sizes_type = p_size)
        AND (p_min_price IS NULL OR c.price_per_hour >= p_min_price)
        AND (p_max_price IS NULL OR c.price_per_hour <= p_max_price)
        AND (p_is_free IS NULL OR 
            (p_is_free = TRUE AND NOT EXISTS (
                SELECT 1 FROM bookings b
                WHERE b.court_id = c.court_id
                AND b.status = 'BOOKED'
                AND b.start_time <= CURRENT_TIMESTAMP + INTERVAL '1 hour'
                AND b.end_time >= CURRENT_TIMESTAMP
            ))
            OR (p_is_free = FALSE AND EXISTS (
                SELECT 1 FROM bookings b
                WHERE b.court_id = c.court_id
                AND b.status = 'BOOKED'
                AND b.start_time <= CURRENT_TIMESTAMP + INTERVAL '1 hour'
                AND b.end_time >= CURRENT_TIMESTAMP
            ))
        );
END;
$$ LANGUAGE plpgsql;

-- Lấy lịch của sân trong ngày
CREATE OR REPLACE FUNCTION fn_get_court_schedule(p_court_id UUID, p_date DATE)
RETURNS TABLE(start_time TIMESTAMPTZ, end_time TIMESTAMPTZ, status booking_status) AS $$
BEGIN
    RETURN QUERY
    SELECT b.start_time, b.end_time, b.status
    FROM bookings b
    WHERE b.court_id = p_court_id
      AND b.start_time::DATE = p_date
      AND b.status IN ('BOOKED', 'PENDING')
    ORDER BY b.start_time;
END;
$$ LANGUAGE plpgsql;

-- Thống kê doanh thu theo ngày
CREATE OR REPLACE FUNCTION fn_daily_revenue(from_date DATE DEFAULT NULL, to_date DATE DEFAULT NULL)
RETURNS TABLE(booking_date DATE, revenue DECIMAL) AS $$
BEGIN
    RETURN QUERY
    SELECT DATE(b.start_time) AS booking_date,
           COALESCE(SUM(fn_calculate_booking_cost(b.court_id, b.start_time, b.end_time)), 0) AS revenue
    FROM bookings b
    WHERE b.status = 'COMPLETED'
      AND (from_date IS NULL OR DATE(b.start_time) >= from_date)
      AND (to_date IS NULL OR DATE(b.start_time) <= to_date)
    GROUP BY DATE(b.start_time)
    ORDER BY booking_date DESC;
END;
$$ LANGUAGE plpgsql;

-- Top sân được đặt nhiều nhất (thêm owner phone)
CREATE OR REPLACE FUNCTION fn_top_courts(limit_count INT DEFAULT 10)
RETURNS TABLE(court_id UUID, court_name VARCHAR, address TEXT, owner_phone VARCHAR, total_bookings BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT c.court_id, c.court_name, c.address, u.phone_number, COUNT(b.booking_id)::BIGINT AS total_bookings
    FROM courts c
    LEFT JOIN users u ON c.owner_id = u.user_id
    LEFT JOIN bookings b ON c.court_id = b.court_id AND b.status = 'COMPLETED'
    GROUP BY c.court_id, c.court_name, c.address, u.phone_number
    ORDER BY total_bookings DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Các stored procedure (không thay đổi so với trước, chỉ giữ nguyên)
CREATE OR REPLACE FUNCTION sp_book_court(
    p_user_id UUID,
    p_court_id UUID,
    p_start TIMESTAMPTZ,
    p_end TIMESTAMPTZ
)
RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT fn_is_court_available(p_court_id, p_start, p_end) THEN
        RAISE EXCEPTION 'Court is already booked';
    END IF;
    INSERT INTO bookings(user_id, court_id, start_time, end_time, status)
    VALUES (p_user_id, p_court_id, p_start, p_end, 'PENDING');
END;
$$;

CREATE OR REPLACE FUNCTION sp_approve_booking(p_booking_id UUID, p_admin_id UUID)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_role user_roles;
    v_court_owner UUID;
BEGIN
    SELECT role INTO v_role FROM users WHERE user_id = p_admin_id;
    IF v_role NOT IN ('MANAGER', 'COURT_MANAGER') THEN
        RAISE EXCEPTION 'Only managers or court managers can approve bookings';
    END IF;
    IF v_role = 'COURT_MANAGER' THEN
        SELECT c.owner_id INTO v_court_owner
        FROM bookings b JOIN courts c ON b.court_id = c.court_id
        WHERE b.booking_id = p_booking_id;
        IF v_court_owner != p_admin_id THEN
            RAISE EXCEPTION 'You are not the owner of this court';
        END IF;
    END IF;
    UPDATE bookings SET status = 'BOOKED' WHERE booking_id = p_booking_id AND status = 'PENDING';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Booking not found or not pending';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION sp_reject_booking(p_booking_id UUID, p_admin_id UUID)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_role user_roles;
    v_court_owner UUID;
BEGIN
    SELECT role INTO v_role FROM users WHERE user_id = p_admin_id;
    IF v_role NOT IN ('MANAGER', 'COURT_MANAGER') THEN
        RAISE EXCEPTION 'Only managers or court managers can reject bookings';
    END IF;
    IF v_role = 'COURT_MANAGER' THEN
        SELECT c.owner_id INTO v_court_owner
        FROM bookings b JOIN courts c ON b.court_id = c.court_id
        WHERE b.booking_id = p_booking_id;
        IF v_court_owner != p_admin_id THEN
            RAISE EXCEPTION 'You are not the owner of this court';
        END IF;
    END IF;
    UPDATE bookings SET status = 'REJECTED' WHERE booking_id = p_booking_id AND status = 'PENDING';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Booking not found or not pending';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION sp_cancel_booking_customer(
    p_booking_id UUID,
    p_user_id UUID
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_start_time TIMESTAMPTZ;
    v_status booking_status;
BEGIN
    SELECT start_time, status INTO v_start_time, v_status
    FROM bookings
    WHERE booking_id = p_booking_id AND user_id = p_user_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Booking not found or not owned by user';
    END IF;
    IF v_status NOT IN ('PENDING', 'BOOKED') THEN
        RAISE EXCEPTION 'Cannot cancel booking with status %', v_status;
    END IF;
    IF v_status = 'BOOKED' AND CURRENT_TIMESTAMP > v_start_time - INTERVAL '3 hours' THEN
        RAISE EXCEPTION 'Cannot cancel within 3 hours';
    END IF;
    UPDATE bookings SET status = 'CANCELLED' WHERE booking_id = p_booking_id;
END;
$$;

CREATE OR REPLACE FUNCTION sp_cancel_booking_powerfull(
    p_booking_id UUID,
    p_admin_id UUID
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_role user_roles;
    v_court_owner UUID;
BEGIN
    SELECT role INTO v_role FROM users WHERE user_id = p_admin_id;
    IF v_role NOT IN ('MANAGER', 'COURT_MANAGER') THEN
        RAISE EXCEPTION 'Only managers or court managers can cancel any booking';
    END IF;
    IF v_role = 'COURT_MANAGER' THEN
        SELECT c.owner_id INTO v_court_owner
        FROM bookings b JOIN courts c ON b.court_id = c.court_id
        WHERE b.booking_id = p_booking_id;
        IF v_court_owner != p_admin_id THEN
            RAISE EXCEPTION 'You are not the owner of this court';
        END IF;
    END IF;
    UPDATE bookings SET status = 'CANCELLED' WHERE booking_id = p_booking_id;
END;
$$;

CREATE OR REPLACE FUNCTION sp_complete_booking(
    p_booking_id UUID,
    p_admin_id UUID
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_role user_roles;
    v_court_owner UUID;
BEGIN
    SELECT role INTO v_role FROM users WHERE user_id = p_admin_id;
    IF v_role NOT IN ('MANAGER', 'COURT_MANAGER') THEN
        RAISE EXCEPTION 'Only managers or court managers can complete any booking';
    END IF;
    IF v_role = 'COURT_MANAGER' THEN
        SELECT c.owner_id INTO v_court_owner
        FROM bookings b JOIN courts c ON b.court_id = c.court_id
        WHERE b.booking_id = p_booking_id;
        IF v_court_owner != p_admin_id THEN
            RAISE EXCEPTION 'You are not the owner of this court';
        END IF;
    END IF;
    UPDATE bookings SET status = 'COMPLETED' WHERE booking_id = p_booking_id;
END;
$$;

CREATE OR REPLACE FUNCTION sp_add_court(
    p_court_name VARCHAR,
    p_address TEXT,
    p_surface court_surfaces,
    p_size court_sizes,
    p_price_per_hour DECIMAL,
    p_price_per_three_hours DECIMAL,
    p_admin_id UUID,
    p_image_url TEXT DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql AS $$
DECLARE
    v_role user_roles;
    new_id UUID;
BEGIN
    SELECT role INTO v_role FROM users WHERE user_id = p_admin_id;
    IF v_role NOT IN ('MANAGER', 'COURT_MANAGER') THEN
        RAISE EXCEPTION 'Only managers or court managers can add courts';
    END IF;
    INSERT INTO courts (court_name, address, court_surfaces_type, court_sizes_type, 
                        price_per_hour, price_per_three_hours, image_url, owner_id)
    VALUES (p_court_name, p_address, p_surface, p_size, p_price_per_hour, 
            p_price_per_three_hours, p_image_url, 
            CASE WHEN v_role = 'COURT_MANAGER' THEN p_admin_id ELSE NULL END)
    RETURNING court_id INTO new_id;
    RETURN new_id;
END;
$$;

CREATE OR REPLACE FUNCTION sp_update_court(
    p_court_id UUID,
    p_court_name VARCHAR,
    p_address TEXT,
    p_surface court_surfaces,
    p_size court_sizes,
    p_price_per_hour DECIMAL,
    p_price_per_three_hours DECIMAL,
    p_is_active BOOLEAN,
    p_image_url TEXT,
    p_admin_id UUID
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_role user_roles;
    v_owner UUID;
BEGIN
    SELECT role INTO v_role FROM users WHERE user_id = p_admin_id;
    IF v_role NOT IN ('MANAGER', 'COURT_MANAGER') THEN
        RAISE EXCEPTION 'Only managers or court managers can update courts';
    END IF;
    IF v_role = 'COURT_MANAGER' THEN
        SELECT owner_id INTO v_owner FROM courts WHERE court_id = p_court_id;
        IF v_owner != p_admin_id THEN
            RAISE EXCEPTION 'You are not the owner of this court';
        END IF;
    END IF;
    UPDATE courts
    SET court_name = COALESCE(p_court_name, court_name),
        address = COALESCE(p_address, address),
        court_surfaces_type = COALESCE(p_surface, court_surfaces_type),
        court_sizes_type = COALESCE(p_size, court_sizes_type),
        price_per_hour = COALESCE(p_price_per_hour, price_per_hour),
        price_per_three_hours = COALESCE(p_price_per_three_hours, price_per_three_hours),
        is_active = COALESCE(p_is_active, is_active),
        image_url = COALESCE(p_image_url, image_url)
    WHERE court_id = p_court_id;
END;
$$;

CREATE OR REPLACE FUNCTION sp_delete_court(
    p_court_id UUID,
    p_admin_id UUID
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_role user_roles;
    v_owner UUID;
BEGIN
    SELECT role INTO v_role FROM users WHERE user_id = p_admin_id;
    IF v_role NOT IN ('MANAGER', 'COURT_MANAGER') THEN
        RAISE EXCEPTION 'Only managers or court managers can delete courts';
    END IF;
    IF v_role = 'COURT_MANAGER' THEN
        SELECT owner_id INTO v_owner FROM courts WHERE court_id = p_court_id;
        IF v_owner != p_admin_id THEN
            RAISE EXCEPTION 'You are not the owner of this court';
        END IF;
    END IF;
    UPDATE courts SET is_active = FALSE WHERE court_id = p_court_id;
END;
$$;
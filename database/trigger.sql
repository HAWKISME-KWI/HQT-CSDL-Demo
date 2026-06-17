DROP TRIGGER IF EXISTS trg_users_updated ON users;
DROP TRIGGER IF EXISTS trg_courts_updated ON courts;
DROP TRIGGER IF EXISTS trg_bookings_updated ON bookings;
DROP TRIGGER IF EXISTS trg_booking_insert ON bookings;
DROP TRIGGER IF EXISTS trg_booking_status_change ON bookings;
DROP TRIGGER IF EXISTS trg_no_overlap ON bookings;
DROP TRIGGER IF EXISTS trg_booking_notify ON bookings;
DROP FUNCTION IF EXISTS fn_update_timestamp();
DROP FUNCTION IF EXISTS fn_log_booking_action();
DROP FUNCTION IF EXISTS fn_log_booking_status_change();
DROP FUNCTION IF EXISTS fn_prevent_overlap();
DROP FUNCTION IF EXISTS fn_notify_booking_status_change();

CREATE OR REPLACE FUNCTION fn_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_courts_updated BEFORE UPDATE ON courts FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_bookings_updated BEFORE UPDATE ON bookings FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();

CREATE OR REPLACE FUNCTION fn_log_booking_action()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO activity_logs(user_id, action)
    VALUES (NEW.user_id, 'Booking ID ' || NEW.booking_id || ' created with status ' || NEW.status);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_booking_insert AFTER INSERT ON bookings FOR EACH ROW EXECUTE FUNCTION fn_log_booking_action();

CREATE OR REPLACE FUNCTION fn_log_booking_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO activity_logs(user_id, action)
        VALUES (NEW.user_id, 'Booking ID ' || NEW.booking_id || ' status changed from ' || OLD.status || ' to ' || NEW.status);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_booking_status_change AFTER UPDATE OF status ON bookings FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION fn_log_booking_status_change();

CREATE OR REPLACE FUNCTION fn_prevent_overlap()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM bookings
        WHERE court_id = NEW.court_id
        AND status = 'BOOKED'
        AND (start_time < NEW.end_time AND end_time > NEW.start_time)
    ) THEN
        RAISE EXCEPTION 'Court already booked';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_no_overlap BEFORE INSERT ON bookings FOR EACH ROW EXECUTE FUNCTION fn_prevent_overlap();

-- Trigger thông báo
CREATE OR REPLACE FUNCTION fn_notify_booking_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Thông báo cho người đặt
        INSERT INTO notifications(user_id, title, content)
        VALUES (NEW.user_id, 'Đặt sân thành công', 'Yêu cầu đặt sân của bạn đang chờ xác nhận.');
        -- Thông báo cho chủ sân (nếu có)
        INSERT INTO notifications(user_id, title, content)
        SELECT c.owner_id, 'Có đơn đặt sân mới', 'Sân ' || c.court_name || ' có đơn đặt mới cần duyệt.'
        FROM courts c WHERE c.court_id = NEW.court_id AND c.owner_id IS NOT NULL;
        -- Hoặc thông báo cho tất cả MANAGER (nếu chủ sân null)
        INSERT INTO notifications(user_id, title, content)
        SELECT u.user_id, 'Có đơn đặt sân mới', 'Sân ' || c.court_name || ' có đơn đặt mới cần duyệt.'
        FROM courts c, users u
        WHERE c.court_id = NEW.court_id 
          AND u.role = 'MANAGER'
          AND (c.owner_id IS NULL OR c.owner_id != u.user_id);
    ELSIF TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status THEN
        -- Thông báo cho người đặt
        INSERT INTO notifications(user_id, title, content)
        VALUES (NEW.user_id, 'Cập nhật trạng thái đặt sân', 
                'Đơn đặt sân của bạn đã được cập nhật từ ' || OLD.status || ' sang ' || NEW.status);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_booking_notify
AFTER INSERT OR UPDATE OF status ON bookings
FOR EACH ROW EXECUTE FUNCTION fn_notify_booking_status_change();
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS activity_logs CASCADE;
DROP TABLE IF EXISTS bookings CASCADE;
DROP TABLE IF EXISTS courts CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TYPE IF EXISTS user_roles CASCADE;
DROP TYPE IF EXISTS court_surfaces CASCADE;
DROP TYPE IF EXISTS court_sizes CASCADE;
DROP TYPE IF EXISTS booking_status CASCADE;

CREATE TYPE user_roles AS ENUM ('GUEST','CUSTOMER','MANAGER','COURT_MANAGER');
CREATE TYPE court_surfaces AS ENUM ('PVC','WOOD','CEMENT','SYNTHETIC_RESIN');
CREATE TYPE court_sizes AS ENUM('SINGLE','DOUBLE');
CREATE TYPE booking_status AS ENUM ('BOOKED','CANCELLED','COMPLETED','PENDING','REJECTED');

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users(
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    role user_roles DEFAULT 'CUSTOMER',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courts(
    court_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    court_name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,  -- THÊM ĐỊA CHỈ
    court_surfaces_type court_surfaces DEFAULT 'PVC',
    court_sizes_type court_sizes DEFAULT 'SINGLE',
    price_per_hour DECIMAL(10,2) NOT NULL CHECK (price_per_hour > 0),
    price_per_three_hours DECIMAL(10,2) NOT NULL CHECK (price_per_three_hours > price_per_hour),
    is_active BOOLEAN DEFAULT TRUE,
    image_url TEXT,
    owner_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookings(
    booking_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    court_id UUID NOT NULL REFERENCES courts(court_id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status booking_status DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_time_range CHECK (end_time > start_time) 
);

CREATE TABLE activity_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_booking_time ON bookings(start_time, end_time);
CREATE INDEX idx_booking_court ON bookings(court_id);
CREATE INDEX idx_booking_status ON bookings(status);
CREATE INDEX idx_booking_user ON bookings(user_id);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_courts_owner ON courts(owner_id);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
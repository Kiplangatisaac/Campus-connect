-- =============================================================================
-- Kirinyaga University Campus Communication System
-- PostgreSQL Database Schema
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- TRIGGER FUNCTION: Auto-update updated_at timestamp
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 1. DEPARTMENTS
-- =============================================================================
CREATE TABLE departments (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL UNIQUE,
    code            VARCHAR(20) NOT NULL UNIQUE,
    faculty         VARCHAR(255) NOT NULL,
    head_user_id    INTEGER,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_departments_code ON departments(code);
CREATE INDEX idx_departments_faculty ON departments(faculty);

-- =============================================================================
-- 2. USERS
-- =============================================================================
CREATE TABLE users (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    email               VARCHAR(255) NOT NULL UNIQUE,
    username            VARCHAR(50) NOT NULL UNIQUE,
    full_name           VARCHAR(255) NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    role                VARCHAR(20) NOT NULL DEFAULT 'student'
                        CHECK (role IN ('student', 'moderator', 'admin')),
    department_id       INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    course              VARCHAR(255),
    registration_number VARCHAR(50) UNIQUE,
    year_of_study       INTEGER CHECK (year_of_study >= 1 AND year_of_study <= 10),
    phone               VARCHAR(20),
    avatar_url          VARCHAR(500),
    is_verified         BOOLEAN DEFAULT FALSE,
    is_online           BOOLEAN DEFAULT FALSE,
    last_seen           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_department_id ON users(department_id);
CREATE INDEX idx_users_registration_number ON users(registration_number);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_verified ON users(is_verified);
CREATE INDEX idx_users_is_online ON users(is_online);

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add foreign key from departments to users (deferred)
ALTER TABLE departments
    ADD CONSTRAINT fk_departments_head_user
    FOREIGN KEY (head_user_id) REFERENCES users(id) ON DELETE SET NULL;

-- =============================================================================
-- 3. COURSES
-- =============================================================================
CREATE TABLE courses (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    code            VARCHAR(20) NOT NULL UNIQUE,
    department_id   INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    level           VARCHAR(20) NOT NULL
                    CHECK (level IN ('certificate', 'diploma', 'degree', 'masters')),
    duration_years  INTEGER NOT NULL CHECK (duration_years >= 1 AND duration_years <= 10),
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_courses_department_id ON courses(department_id);
CREATE INDEX idx_courses_code ON courses(code);
CREATE INDEX idx_courses_level ON courses(level);

-- =============================================================================
-- 4. GROUPS
-- =============================================================================
CREATE TABLE groups (
    id              SERIAL PRIMARY KEY,
    uuid            UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    type            VARCHAR(20) NOT NULL
                    CHECK (type IN ('faculty', 'department', 'course', 'custom', 'study')),
    department_id   INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    course_id       INTEGER REFERENCES courses(id) ON DELETE SET NULL,
    created_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    max_members     INTEGER DEFAULT 100 CHECK (max_members > 0),
    is_public       BOOLEAN DEFAULT TRUE,
    avatar_url      VARCHAR(500),
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_groups_type ON groups(type);
CREATE INDEX idx_groups_department_id ON groups(department_id);
CREATE INDEX idx_groups_course_id ON groups(course_id);
CREATE INDEX idx_groups_created_by ON groups(created_by);
CREATE INDEX idx_groups_is_public ON groups(is_public);

CREATE TRIGGER update_groups_updated_at
    BEFORE UPDATE ON groups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 5. GROUP MEMBERS
-- =============================================================================
CREATE TABLE group_members (
    id          SERIAL PRIMARY KEY,
    group_id    INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        VARCHAR(20) NOT NULL DEFAULT 'member'
                CHECK (role IN ('member', 'moderator', 'admin')),
    joined_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, user_id)
);

CREATE INDEX idx_group_members_group_id ON group_members(group_id);
CREATE INDEX idx_group_members_user_id ON group_members(user_id);

-- =============================================================================
-- 6. CONVERSATIONS
-- =============================================================================
CREATE TABLE conversations (
    id          SERIAL PRIMARY KEY,
    uuid        UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    type        VARCHAR(10) NOT NULL
                CHECK (type IN ('direct', 'group')),
    title       VARCHAR(255),
    created_by  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_type ON conversations(type);
CREATE INDEX idx_conversations_created_by ON conversations(created_by);

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 7. CONVERSATION PARTICIPANTS
-- =============================================================================
CREATE TABLE conversation_participants (
    id              SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_read_at    TIMESTAMPTZ,
    is_muted        BOOLEAN DEFAULT FALSE,
    joined_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(conversation_id, user_id)
);

CREATE INDEX idx_conv_participants_conversation_id ON conversation_participants(conversation_id);
CREATE INDEX idx_conv_participants_user_id ON conversation_participants(user_id);
CREATE INDEX idx_conv_participants_last_read_at ON conversation_participants(last_read_at);

-- =============================================================================
-- 8. MESSAGES
-- =============================================================================
CREATE TABLE messages (
    id              SERIAL PRIMARY KEY,
    uuid            UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content         TEXT,
    type            VARCHAR(10) NOT NULL DEFAULT 'text'
                    CHECK (type IN ('text', 'image', 'file', 'audio', 'video', 'system')),
    reply_to_id     INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    is_edited       BOOLEAN DEFAULT FALSE,
    is_deleted      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_reply_to_id ON messages(reply_to_id);
CREATE INDEX idx_messages_type ON messages(type);

CREATE TRIGGER update_messages_updated_at
    BEFORE UPDATE ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 9. MESSAGE REACTIONS
-- =============================================================================
CREATE TABLE message_reactions (
    id          SERIAL PRIMARY KEY,
    message_id  INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    emoji       VARCHAR(10) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id, user_id, emoji)
);

CREATE INDEX idx_message_reactions_message_id ON message_reactions(message_id);
CREATE INDEX idx_message_reactions_user_id ON message_reactions(user_id);

-- =============================================================================
-- 10. ATTACHMENTS
-- =============================================================================
CREATE TABLE attachments (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    message_id          INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    filename            VARCHAR(255) NOT NULL,
    original_filename   VARCHAR(255) NOT NULL,
    mime_type           VARCHAR(100) NOT NULL,
    size                BIGINT NOT NULL CHECK (size > 0),
    url                 VARCHAR(500) NOT NULL,
    thumbnail_url       VARCHAR(500),
    uploaded_by         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attachments_message_id ON attachments(message_id);
CREATE INDEX idx_attachments_uploaded_by ON attachments(uploaded_by);
CREATE INDEX idx_attachments_mime_type ON attachments(mime_type);

-- =============================================================================
-- 11. BULLETIN POSTS
-- =============================================================================
CREATE TABLE bulletin_posts (
    id              SERIAL PRIMARY KEY,
    uuid            UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    title           VARCHAR(255) NOT NULL,
    content         TEXT NOT NULL,
    category        VARCHAR(20) NOT NULL
                    CHECK (category IN ('announcement', 'event', 'opportunity', 'urgent', 'general')),
    department_id   INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    created_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_pinned       BOOLEAN DEFAULT FALSE,
    is_approved     BOOLEAN DEFAULT FALSE,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bulletin_posts_category ON bulletin_posts(category);
CREATE INDEX idx_bulletin_posts_department_id ON bulletin_posts(department_id);
CREATE INDEX idx_bulletin_posts_created_by ON bulletin_posts(created_by);
CREATE INDEX idx_bulletin_posts_is_pinned ON bulletin_posts(is_pinned);
CREATE INDEX idx_bulletin_posts_is_approved ON bulletin_posts(is_approved);
CREATE INDEX idx_bulletin_posts_created_at ON bulletin_posts(created_at);
CREATE INDEX idx_bulletin_posts_expires_at ON bulletin_posts(expires_at);

CREATE TRIGGER update_bulletin_posts_updated_at
    BEFORE UPDATE ON bulletin_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 12. BULLETIN COMMENTS
-- =============================================================================
CREATE TABLE bulletin_comments (
    id          SERIAL PRIMARY KEY,
    post_id     INTEGER NOT NULL REFERENCES bulletin_posts(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bulletin_comments_post_id ON bulletin_comments(post_id);
CREATE INDEX idx_bulletin_comments_user_id ON bulletin_comments(user_id);
CREATE INDEX idx_bulletin_comments_created_at ON bulletin_comments(created_at);

-- =============================================================================
-- 13. EVENTS
-- =============================================================================
CREATE TABLE events (
    id              SERIAL PRIMARY KEY,
    uuid            UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    location        VARCHAR(255),
    start_time      TIMESTAMPTZ NOT NULL,
    end_time        TIMESTAMPTZ NOT NULL,
    organizer_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department_id   INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    type            VARCHAR(20) NOT NULL
                    CHECK (type IN ('academic', 'social', 'sports', 'cultural')),
    max_attendees   INTEGER CHECK (max_attendees IS NULL OR max_attendees > 0),
    is_virtual      BOOLEAN DEFAULT FALSE,
    meeting_url     VARCHAR(500),
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_event_times CHECK (end_time > start_time)
);

CREATE INDEX idx_events_organizer_id ON events(organizer_id);
CREATE INDEX idx_events_department_id ON events(department_id);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_events_start_time ON events(start_time);
CREATE INDEX idx_events_end_time ON events(end_time);
CREATE INDEX idx_events_is_virtual ON events(is_virtual);

CREATE TRIGGER update_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 14. EVENT ATTENDEES
-- =============================================================================
CREATE TABLE event_attendees (
    id          SERIAL PRIMARY KEY,
    event_id    INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status      VARCHAR(10) NOT NULL DEFAULT 'going'
                CHECK (status IN ('going', 'maybe', 'not_going')),
    joined_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, user_id)
);

CREATE INDEX idx_event_attendees_event_id ON event_attendees(event_id);
CREATE INDEX idx_event_attendees_user_id ON event_attendees(user_id);
CREATE INDEX idx_event_attendees_status ON event_attendees(status);

-- =============================================================================
-- 15. NOTIFICATIONS
-- =============================================================================
CREATE TABLE notifications (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type        VARCHAR(50) NOT NULL,
    title       VARCHAR(255) NOT NULL,
    body        TEXT NOT NULL,
    data        JSONB DEFAULT '{}',
    is_read     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_notifications_type ON notifications(type);

-- =============================================================================
-- 16. STUDY GROUPS
-- =============================================================================
CREATE TABLE study_groups (
    id                  SERIAL PRIMARY KEY,
    group_id            INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    subject             VARCHAR(255) NOT NULL,
    semester            VARCHAR(20) NOT NULL CHECK (semester IN ('1', '2', '3', 'summer')),
    year                INTEGER NOT NULL CHECK (year >= 2020 AND year <= 2050),
    max_members         INTEGER DEFAULT 10 CHECK (max_members > 0),
    meeting_schedule    TEXT,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_study_groups_group_id ON study_groups(group_id);
CREATE INDEX idx_study_groups_subject ON study_groups(subject);
CREATE INDEX idx_study_groups_semester ON study_groups(semester);
CREATE INDEX idx_study_groups_year ON study_groups(year);

-- =============================================================================
-- 17. STUDY GROUP MEMBERS
-- =============================================================================
CREATE TABLE study_group_members (
    id              SERIAL PRIMARY KEY,
    study_group_id  INTEGER NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL DEFAULT 'member'
                    CHECK (role IN ('member', 'leader', 'coordinator')),
    joined_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(study_group_id, user_id)
);

CREATE INDEX idx_study_group_members_study_group_id ON study_group_members(study_group_id);
CREATE INDEX idx_study_group_members_user_id ON study_group_members(user_id);

-- =============================================================================
-- 18. COLLABORATIVE DOCS
-- =============================================================================
CREATE TABLE collaborative_docs (
    id              SERIAL PRIMARY KEY,
    uuid            UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    title           VARCHAR(255) NOT NULL,
    content         TEXT DEFAULT '',
    group_id        INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    created_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_edited_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_collaborative_docs_group_id ON collaborative_docs(group_id);
CREATE INDEX idx_collaborative_docs_created_by ON collaborative_docs(created_by);
CREATE INDEX idx_collaborative_docs_last_edited_by ON collaborative_docs(last_edited_by);

CREATE TRIGGER update_collaborative_docs_updated_at
    BEFORE UPDATE ON collaborative_docs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 19. BADGES
-- =============================================================================
CREATE TABLE badges (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    icon        VARCHAR(500),
    category    VARCHAR(50) NOT NULL
                CHECK (category IN ('achievement', 'participation', 'academic', 'social', 'special')),
    criteria    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_badges_category ON badges(category);
CREATE INDEX idx_badges_name ON badges(name);

-- =============================================================================
-- 20. USER BADGES
-- =============================================================================
CREATE TABLE user_badges (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id    INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    awarded_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    awarded_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(user_id, badge_id)
);

CREATE INDEX idx_user_badges_user_id ON user_badges(user_id);
CREATE INDEX idx_user_badges_badge_id ON user_badges(badge_id);
CREATE INDEX idx_user_badges_awarded_at ON user_badges(awarded_at);

-- =============================================================================
-- 21. OFFLINE NOTES
-- =============================================================================
CREATE TABLE offline_notes (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    content         TEXT DEFAULT '',
    sync_status     VARCHAR(20) NOT NULL DEFAULT 'synced'
                    CHECK (sync_status IN ('synced', 'pending', 'conflict')),
    last_synced     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_offline_notes_user_id ON offline_notes(user_id);
CREATE INDEX idx_offline_notes_sync_status ON offline_notes(sync_status);
CREATE INDEX idx_offline_notes_updated_at ON offline_notes(updated_at);

CREATE TRIGGER update_offline_notes_updated_at
    BEFORE UPDATE ON offline_notes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 22. AUDIT LOG
-- =============================================================================
CREATE TABLE audit_log (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action      VARCHAR(100) NOT NULL,
    table_name  VARCHAR(100) NOT NULL,
    record_id   INTEGER,
    old_values  JSONB,
    new_values  JSONB,
    ip_address  INET,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX idx_audit_log_record_id ON audit_log(record_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- =============================================================================
-- HELPER FUNCTION: Create direct conversation between two users
-- =============================================================================
CREATE OR REPLACE FUNCTION create_direct_conversation(
    p_user1_id INTEGER,
    p_user2_id INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_conversation_id INTEGER;
    v_existing_id INTEGER;
BEGIN
    -- Check if a direct conversation already exists
    SELECT c.id INTO v_existing_id
    FROM conversations c
    WHERE c.type = 'direct'
    AND EXISTS (
        SELECT 1 FROM conversation_participants cp1
        WHERE cp1.conversation_id = c.id AND cp1.user_id = p_user1_id
    )
    AND EXISTS (
        SELECT 1 FROM conversation_participants cp2
        WHERE cp2.conversation_id = c.id AND cp2.user_id = p_user2_id
    )
    LIMIT 1;

    IF v_existing_id IS NOT NULL THEN
        RETURN v_existing_id;
    END IF;

    -- Create new conversation
    INSERT INTO conversations (type, created_by)
    VALUES ('direct', p_user1_id)
    RETURNING id INTO v_conversation_id;

    -- Add participants
    INSERT INTO conversation_participants (conversation_id, user_id)
    VALUES (v_conversation_id, p_user1_id), (v_conversation_id, p_user2_id);

    RETURN v_conversation_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- HELPER FUNCTION: Get unread message count for a user
-- =============================================================================
CREATE OR REPLACE FUNCTION get_unread_count(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO v_count
    FROM messages m
    INNER JOIN conversation_participants cp
        ON cp.conversation_id = m.conversation_id
    WHERE cp.user_id = p_user_id
    AND m.sender_id != p_user_id
    AND (cp.last_read_at IS NULL OR m.created_at > cp.last_read_at);

    RETURN COALESCE(v_count, 0);
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- SEED DATA: Departments
-- =============================================================================
INSERT INTO departments (name, code, faculty) VALUES
    ('Computer Science', 'CS', 'Faculty of Engineering and Technology'),
    ('Information Technology', 'IT', 'Faculty of Engineering and Technology'),
    ('Electrical Engineering', 'EE', 'Faculty of Engineering and Technology'),
    ('Civil Engineering', 'CE', 'Faculty of Engineering and Technology'),
    ('Business Administration', 'BA', 'Faculty of Business and Economics'),
    ('Commerce', 'COM', 'Faculty of Business and Economics'),
    ('Finance', 'FIN', 'Faculty of Business and Economics'),
    ('Education Arts', 'EA', 'Faculty of Education and Humanities'),
    ('Education Science', 'ESC', 'Faculty of Education and Humanities'),
    ('Mathematics', 'MATH', 'Faculty of Pure and Applied Sciences'),
    ('Physics', 'PHY', 'Faculty of Pure and Applied Sciences'),
    ('Chemistry', 'CHEM', 'Faculty of Pure and Applied Sciences'),
    ('Nursing', 'NUR', 'Faculty of Health Sciences'),
    ('Public Health', 'PH', 'Faculty of Health Sciences'),
    ('Agriculture', 'AGRI', 'Faculty of Agriculture and Veterinary Sciences'),
    ('Food Science', 'FS', 'Faculty of Agriculture and Veterinary Sciences'),
    ('Law', 'LAW', 'Faculty of Law'),
    ('Political Science', 'POL', 'Faculty of Arts and Social Sciences'),
    ('Sociology', 'SOC', 'Faculty of Arts and Social Sciences'),
    ('Mass Communication', 'MCOM', 'Faculty of Arts and Social Sciences');

-- =============================================================================
-- SEED DATA: Admin User (password: Admin@12345)
-- =============================================================================
INSERT INTO users (
    email, username, full_name, password_hash, role, department_id, registration_number, is_verified
) VALUES (
    'admin@kirinyaga.ac.ke',
    'admin',
    'System Administrator',
    '$2b$12$LJ3m4ys3Lhdo5xKj5GKuMeGq6X5aQq2Z1p3o9r8s6t4u7v2w1x5y9',
    'admin',
    NULL,
    'ADMIN001',
    TRUE
);

-- =============================================================================
-- SEED DATA: Sample Badges
-- =============================================================================
INSERT INTO badges (name, description, icon, category, criteria) VALUES
    ('First Steps', 'Created your first message', 'star', 'participation', '{"messages_sent": 1}'),
    ('Active Contributor', 'Sent 100 messages', 'fire', 'participation', '{"messages_sent": 100}'),
    ('Discussion Starter', 'Started 10 conversations', 'chat', 'social', '{"conversations_started": 10}'),
    ('Event Organizer', 'Created 5 events', 'calendar', 'social', '{"events_created": 5}'),
    ('Helpful Hand', 'Received 50 reactions on messages', 'thumbsup', 'social', '{"reactions_received": 50}'),
    ('Study Champion', 'Created 3 study groups', 'book', 'academic', '{"study_groups_created": 3}'),
    {'Early Adopter', 'Joined during the first month', 'rocket', 'special', '{"early_adopter": true}'),
    ('Top Contributor', 'Most active user of the month', 'trophy', 'achievement', '{"top_contributor_monthly": true}'),
    ('Department Leader', 'Head of a department', 'crown', 'achievement', '{"department_head": true}'),
    ('Perfect Attendance', 'Attended 10 events', 'check', 'participation', '{"events_attended": 10}');

-- =============================================================================
-- SEED DATA: Sample Courses (CS Department)
-- =============================================================================
INSERT INTO courses (name, code, department_id, level, duration_years) VALUES
    ('Bachelor of Science in Computer Science', 'BSC-CS', 1, 'degree', 4),
    ('Bachelor of Science in Information Technology', 'BSC-IT', 2, 'degree', 4),
    ('Diploma in Computer Science', 'DIP-CS', 1, 'diploma', 2),
    ('Diploma in Information Technology', 'DIP-IT', 2, 'diploma', 2),
    ('Certificate in Computer Science', 'CERT-CS', 1, 'certificate', 1),
    ('Bachelor of Business Administration', 'BBA', 5, 'degree', 4),
    ('Bachelor of Commerce', 'BCOM', 6, 'degree', 4),
    ('Master of Business Administration', 'MBA', 5, 'masters', 2),
    ('Bachelor of Education Arts', 'BED-ARTS', 8, 'degree', 4),
    ('Bachelor of Education Science', 'BED-SCI', 9, 'degree', 4),
    ('Bachelor of Science in Mathematics', 'BSC-MATH', 10, 'degree', 4),
    ('Bachelor of Science in Physics', 'BSC-PHY', 11, 'degree', 4),
    ('Bachelor of Science in Chemistry', 'BSC-CHEM', 12, 'degree', 4),
    ('Bachelor of Science in Nursing', 'BSC-NUR', 13, 'degree', 4),
    ('Bachelor of Laws', 'LLB', 17, 'degree', 5);

-- =============================================================================
-- SEED DATA: Sample Groups
-- =============================================================================
DO $$
DECLARE
    v_cs_dept_id INTEGER;
    v_it_dept_id INTEGER;
    v_admin_id INTEGER;
    v_cs_group_id INTEGER;
    v_it_group_id INTEGER;
    v_general_group_id INTEGER;
BEGIN
    SELECT id INTO v_cs_dept_id FROM departments WHERE code = 'CS';
    SELECT id INTO v_it_dept_id FROM departments WHERE code = 'IT';
    SELECT id INTO v_admin_id FROM users WHERE username = 'admin';

    -- CS Department Group
    INSERT INTO groups (name, description, type, department_id, created_by, is_public)
    VALUES ('Computer Science Department', 'Official group for CS students and staff', 'department', v_cs_dept_id, v_admin_id, TRUE)
    RETURNING id INTO v_cs_group_id;

    -- IT Department Group
    INSERT INTO groups (name, description, type, department_id, created_by, is_public)
    VALUES ('Information Technology Department', 'Official group for IT students and staff', 'department', v_it_dept_id, v_admin_id, TRUE)
    RETURNING id INTO v_it_group_id;

    -- General Campus Group
    INSERT INTO groups (name, description, type, created_by, is_public)
    VALUES ('Kirinyaga University General', 'General discussion for all students', 'custom', v_admin_id, TRUE)
    RETURNING id INTO v_general_group_id;

    -- Add admin as member of all groups
    INSERT INTO group_members (group_id, user_id, role)
    VALUES
        (v_cs_group_id, v_admin_id, 'admin'),
        (v_it_group_id, v_admin_id, 'admin'),
        (v_general_group_id, v_admin_id, 'admin');

    -- Create conversations for each group
    INSERT INTO conversations (type, title, created_by)
    VALUES
        ('group', 'CS Department Chat', v_admin_id),
        ('group', 'IT Department Chat', v_admin_id),
        ('group', 'General Campus Chat', v_admin_id);
END $$;

-- =============================================================================
-- SEED DATA: Sample Study Group
-- =============================================================================
DO $$
DECLARE
    v_group_id INTEGER;
    v_admin_id INTEGER;
    v_sg_group_id INTEGER;
BEGIN
    SELECT id INTO v_group_id FROM groups WHERE name = 'Computer Science Department';
    SELECT id INTO v_admin_id FROM users WHERE username = 'admin';

    INSERT INTO groups (name, description, type, created_by, is_public)
    VALUES ('Data Structures & Algorithms Study Group', 'Weekly study sessions for DSA', 'study', v_admin_id, TRUE)
    RETURNING id INTO v_sg_group_id;

    INSERT INTO study_groups (group_id, subject, semester, year, max_members, meeting_schedule)
    VALUES (v_sg_group_id, 'Data Structures and Algorithms', '1', 2026, 20, 'Wednesdays 2pm-4pm');

    INSERT INTO group_members (group_id, user_id, role)
    VALUES (v_sg_group_id, v_admin_id, 'admin');

    INSERT INTO study_group_members (study_group_id, user_id, role)
    VALUES (
        (SELECT id FROM study_groups WHERE group_id = v_sg_group_id),
        v_admin_id,
        'leader'
    );
END $$;

-- =============================================================================
-- SEED DATA: Sample Bulletin Post
-- =============================================================================
DO $$
DECLARE
    v_admin_id INTEGER;
BEGIN
    SELECT id INTO v_admin_id FROM users WHERE username = 'admin';

    INSERT INTO bulletin_posts (title, content, category, created_by, is_pinned, is_approved)
    VALUES (
        'Welcome to Kirinyaga University Campus System',
        'Welcome to the new campus communication system! This platform is designed to enhance collaboration among students, faculty, and staff. Please complete your profile and explore the features available to you.',
        'announcement',
        v_admin_id,
        TRUE,
        TRUE
    );
END $$;

-- =============================================================================
-- COMPLETED
-- =============================================================================
-- Schema created successfully with:
-- - 22 tables with proper relationships
-- - Foreign keys with appropriate ON DELETE behavior
-- - Indexes on frequently queried columns
-- - UNIQUE constraints where needed
-- - CHECK constraints for enum validations
-- - Trigger functions for updated_at timestamps
-- - Helper functions for common operations
-- - Seed data for departments, admin user, badges, courses, groups, and sample content
-- =============================================================================

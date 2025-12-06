-- Applications table stores parsed Gmail application emails
create extension if not exists pgcrypto;

create table if not exists applications (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz default now(),
    email_date timestamptz,
    company text,
    role text,
    stage text check (stage in ('applied', 'interview', 'rejected', 'offer', 'other')),
    subject text,
    from_email text,
    from_name text,
    snippet text,
    gmail_id text unique,
    thread_id text,
    source text,
    notes text
);

create index if not exists applications_stage_idx on applications(stage);
create index if not exists applications_company_idx on applications(company);
create index if not exists applications_email_date_idx on applications(email_date);

-- gmail_state tracks the last processed history id
create table if not exists gmail_state (
    id text primary key,
    last_history_id bigint
);

insert into gmail_state (id, last_history_id)
values ('singleton', null)
on conflict (id) do nothing;

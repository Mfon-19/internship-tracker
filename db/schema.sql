-- Applications table stores parsed Gmail application emails
create extension if not exists pgcrypto;

create table if not exists applications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id),
    created_at timestamptz default now(),
    email_date timestamptz,
    company text,
    role text,
    stage text check (stage in ('applied', 'interview', 'rejected', 'offer', 'other')),
    subject text,
    from_email text,
    from_name text,
    snippet text,
    gmail_id text not null,
    thread_id text,
    source text,
    notes text,
    unique (user_id, gmail_id)
);

create index if not exists applications_stage_idx on applications(stage);
create index if not exists applications_company_idx on applications(company);
create index if not exists applications_email_date_idx on applications(email_date);
create index if not exists applications_user_date_idx on applications(user_id, email_date desc);

-- gmail_connections stores per-user Gmail OAuth tokens and metadata
create table if not exists gmail_connections (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id),
    email text not null,
    provider_access_token text,
    provider_refresh_token text,
    provider_token_expires_at timestamptz,
    history_id text,
    watch_expiration timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, email)
);

-- RLS: each user can only access their own rows
alter table applications enable row level security;
alter table gmail_connections enable row level security;

create policy if not exists applications_select_self on applications
    for select using (auth.uid() = user_id);
create policy if not exists applications_insert_self on applications
    for insert with check (auth.uid() = user_id);
create policy if not exists applications_update_self on applications
    for update using (auth.uid() = user_id);

create policy if not exists gmail_connections_select_self on gmail_connections
    for select using (auth.uid() = user_id);
create policy if not exists gmail_connections_insert_self on gmail_connections
    for insert with check (auth.uid() = user_id);
create policy if not exists gmail_connections_update_self on gmail_connections
    for update using (auth.uid() = user_id);

-- legacy gmail_state table preserved for backward compatibility
create table if not exists gmail_state (
    id text primary key,
    last_history_id bigint
);

insert into gmail_state (id, last_history_id)
values ('singleton', null)
on conflict (id) do nothing;

-- Create gmail_connections table
create table if not exists gmail_connections (
  user_id uuid references auth.users(id) not null,
  email text not null,
  provider_access_token text,
  provider_refresh_token text,
  provider_token_expires_at timestamptz,
  primary key (user_id, email)
);

-- Enable RLS
alter table gmail_connections enable row level security;

-- Policies
create policy "Users can view own connections"
  on gmail_connections for select
  using (auth.uid() = user_id);

create policy "Users can manage own connections"
  on gmail_connections for all
  using (auth.uid() = user_id);

-- Also add RLS to gmail_state if not present
alter table gmail_state enable row level security;

create policy "Users can view own state"
  on gmail_state for select
  using (auth.uid() = (select user_id from gmail_connections where email = gmail_state.id));

-- This implies gmail_state.id is the email.

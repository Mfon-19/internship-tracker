-- 1. Add user_id column to applications table
alter table applications 
add column if not exists user_id uuid references auth.users(id);

-- 2. Create an index for performance
create index if not exists applications_user_id_idx on applications(user_id);

-- 3. Enable Row Level Security
alter table applications enable row level security;

-- 4. Create Policy: Users can see/edit ONLY their own data
-- Allow SELECT for own rows
create policy "Users can view own applications"
on applications for select
using (auth.uid() = user_id);

-- Allow INSERT with own user_id
create policy "Users can insert own applications"
on applications for insert
with check (auth.uid() = user_id);

-- Allow UPDATE for own rows
create policy "Users can update own applications"
on applications for update
using (auth.uid() = user_id);

-- Allow DELETE for own rows
create policy "Users can delete own applications"
on applications for delete
using (auth.uid() = user_id);

-- NOTE: existing rows with NULL user_id will effectively vanish from the UI
-- for logged-in users until a user_id is assigned.

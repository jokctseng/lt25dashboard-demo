-- 使用者角色與公開暱稱
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'user'::text,
  username text NULL,
  email text NOT NULL, -- 敏感個資
  CONSTRAINT profiles_pkey PRIMARY KEY (id)
);

-- 儀表板意見彙整
CREATE TABLE IF NOT EXISTS public.suggestions (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  content text NOT NULL,
  cate text NULL, 
  created_at timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT suggestions_pkey PRIMARY KEY (id)
);

--
CREATE TABLE IF NOT EXISTS public.votes (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  suggestion_id uuid NOT NULL REFERENCES public.suggestions(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  vote_type text NOT NULL,
  CONSTRAINT votes_pkey PRIMARY KEY (id),
  CONSTRAINT unique_vote UNIQUE (suggestion_id, user_id) -- 每個使用者對每個意見只能投一票
);

-- 共創新聞牆貼文
CREATE TABLE IF NOT EXISTS public.posts (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  user_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  topic text NOT NULL,
  post_type text NOT NULL,
  content text NOT NULL,
  created_at timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT posts_pkey PRIMARY KEY (id)
);

-- 貼文反應 React
CREATE TABLE IF NOT EXISTS public.reactions (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  post_id uuid NOT NULL REFERENCES public.posts (id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  reaction_type text NOT NULL,
  CONSTRAINT reactions_pkey PRIMARY KEY (id),
  CONSTRAINT unique_reaction UNIQUE (post_id, user_id)
);


-- 觸發器設置

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO public.profiles (id, email)
  VALUES (NEW.id, NEW.email);
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE PROCEDURE public.handle_new_user();

-- 檢查使用者角色
CREATE OR REPLACE FUNCTION public.user_role(user_uuid uuid)
RETURNS text
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT role FROM public.profiles WHERE id = user_uuid;
$$;

-- 儀表板意見統計 
CREATE OR REPLACE FUNCTION public.get_suggestion_status()
 RETURNS TABLE(
     id uuid,
     cate text,
     content text,
     unresolved_count bigint,
     partial_count bigint,
     resolved_count bigint,
     created_at timestamp with time zone
 )
 LANGUAGE sql
AS $function$
SELECT
    s.id,
    s.cate,
    s.content,
    COALESCE(SUM(CASE WHEN v.vote_type = '未解決' THEN 1 ELSE 0 END), 0) AS unresolved_count,
    COALESCE(SUM(CASE WHEN v.vote_type = '部分解決' THEN 1 ELSE 0 END), 0) AS partial_count,
    COALESCE(SUM(CASE WHEN v.vote_type = '已解決' THEN 1 ELSE 0 END), 0) AS resolved_count,
    s.created_at
FROM
    public.suggestions s
LEFT JOIN
    public.votes v ON s.id = v.suggestion_id
GROUP BY
    s.id, s.cate, s.content, s.created_at
ORDER BY
    s.created_at DESC;
$function$;

-- 啟用所有表格的 RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reactions ENABLE ROW LEVEL SECURITY;

----------------------------------------------------------------------
-- 個資隔離
----------------------------------------------------------------------

-- 所有人只能查看 id, username 和 role
CREATE POLICY "Public can view non-sensitive profiles"
ON public.profiles
FOR SELECT
USING (TRUE);

-- 系統管理員可以查看所有欄位
CREATE POLICY "System Admin full access to profiles"
ON public.profiles
FOR SELECT
USING (public.user_role(auth.uid()) = 'system_admin');

-- 使用者只能更新自己的 username
CREATE POLICY "Users can update their own username"
ON public.profiles
FOR UPDATE
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

----------------------------------------------------------------------
-- 共創新聞牆
----------------------------------------------------------------------

-- 允許已登入使用者插入自己的貼文
CREATE POLICY "Users can insert own post"
ON public.posts
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- 允許所有人查看所有貼文
CREATE POLICY "Public can view all posts"
ON public.posts
FOR SELECT
USING (TRUE);

-- 允許系統管理員刪除貼文
CREATE POLICY "Allow admins and moderators to delete posts"
ON public.posts
FOR DELETE
USING (
  public.user_role(auth.uid()) IN ('system_admin', 'moderator')
);

----------------------------------------------------------------------
-- 投票
----------------------------------------------------------------------

-- 允許已登入使用者操作自己的投票 (防止刷票)
CREATE POLICY "Users can upsert own vote"
ON public.votes
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 允許所有人查看投票結果
CREATE POLICY "Public can view all votes"
ON public.votes
FOR SELECT
USING (TRUE);

----------------------------------------------------------------------
-- React
----------------------------------------------------------------------

-- 允許已登入使用者操作自己的 reaction
CREATE POLICY "Users can upsert own reaction"
ON public.reactions
FOR ALL 
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 允許所有人查看所有反應結果
CREATE POLICY "Public can view all reactions"
ON public.reactions
FOR SELECT
USING (TRUE);


----------------------------------------------------------------------
-- 管理員/版主操作建議
----------------------------------------------------------------------

-- 確保只有 Admin/Mod 才能操作 Suggestions
CREATE POLICY "Admin/Mod full control over suggestions"
ON public.suggestions
FOR ALL 
USING (public.user_role(auth.uid()) IN ('system_admin', 'moderator'))
WITH CHECK (public.user_role(auth.uid()) IN ('system_admin', 'moderator'));

-- 允許所有人查看 Suggestions
CREATE POLICY "Public can view all suggestions"
ON public.suggestions
FOR SELECT
USING (TRUE);

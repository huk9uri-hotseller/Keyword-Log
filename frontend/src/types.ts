export type KeywordType = "GENERAL" | "OWN" | "COMPETITOR";

export interface User {
  id: number;
  email: string;
  name?: string | null;
  picture_url?: string | null;
  google_sub: string;
  last_login_at?: string | null;
  created_at: string;
}

export interface KeywordGroup {
  id: number;
  user_id: number;
  group_name: string;
  keyword_type: KeywordType;
  created_at: string;
}

export interface Keyword {
  id: number;
  group_id: number;
  keyword: string;
  is_active: boolean;
  created_at: string;
}

export interface ApiError {
  message: string;
  status?: number;
}

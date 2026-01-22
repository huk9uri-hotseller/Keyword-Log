import { request } from "./client";
import type { Keyword } from "../types";

export interface CreateKeywordPayload {
  keyword: string;
  is_active?: boolean;
}

export interface UpdateKeywordPayload {
  keyword?: string;
  is_active?: boolean;
}

export async function fetchKeywords(groupId: number) {
  return request<Keyword[]>(`/keyword-groups/${groupId}/keywords/`);
}

export async function createKeyword(groupId: number, payload: CreateKeywordPayload) {
  return request<Keyword>(`/keyword-groups/${groupId}/keywords/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateKeyword(
  groupId: number,
  keywordId: number,
  payload: UpdateKeywordPayload
) {
  return request<Keyword>(
    `/keyword-groups/${groupId}/keywords/${keywordId}`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    }
  );
}

export async function deleteKeyword(groupId: number, keywordId: number) {
  return request<{ message: string }>(
    `/keyword-groups/${groupId}/keywords/${keywordId}`,
    {
      method: "DELETE",
    }
  );
}

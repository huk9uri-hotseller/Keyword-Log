import { request } from "./client";
import type { KeywordGroup } from "../types";

export interface CreateKeywordGroupPayload {
  user_id: number;
  group_name: string;
  keyword_type: KeywordGroup["keyword_type"];
}

export interface UpdateKeywordGroupPayload {
  group_name: string;
}

export async function fetchKeywordGroups(userId?: number) {
  const query = userId ? `?user_id=${userId}` : "";
  return request<KeywordGroup[]>(`/keyword-groups/${query}`);
}

export async function fetchKeywordGroup(groupId: number) {
  return request<KeywordGroup>(`/keyword-groups/${groupId}`);
}

export async function createKeywordGroup(payload: CreateKeywordGroupPayload) {
  return request<KeywordGroup>("/keyword-groups/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateKeywordGroup(
  groupId: number,
  payload: UpdateKeywordGroupPayload
) {
  return request<KeywordGroup>(`/keyword-groups/${groupId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteKeywordGroup(groupId: number) {
  return request<{ message: string }>(`/keyword-groups/${groupId}`, {
    method: "DELETE",
  });
}

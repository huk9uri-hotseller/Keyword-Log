import { request } from "./client";
import type { User } from "../types";

export interface CreateUserPayload {
  email: string;
  name?: string;
  picture_url?: string;
  google_sub: string;
}

export async function fetchUsers() {
  return request<User[]>("/users");
}

export async function fetchUser(userId: number) {
  return request<User>(`/users/${userId}`);
}

export async function createUser(payload: CreateUserPayload) {
  return request<User>("/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
